"""Two-phase narrative handoff: archive completed options; commit on next choice.

The r7 HEAD never moves when choices are merely displayed. A new installment
cannot be authorized until the previously displayed episode has been remotely
archived, its events reviewed and its HEAD update independently verified.

This is an explicitly called workflow. It is NOT a background ChatGPT hook.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Protocol

from .ledger import GateError, ConflictError, digest, encoded, utcnow
from .episode_pipeline import EpisodeClosure, EpisodeDraft


@dataclass(frozen=True)
class AuthorSelection:
    episode_id: str
    option: int
    free_text: str = ''
    author_source: str = 'USER_MESSAGE'

    def validate(self):
        if self.option not in (1,2,3,4,5) or isinstance(self.option,bool):
            raise ValueError('Selection must be an integer from 1 to 5')
        if self.option==5 and not self.free_text.strip():
            raise GateError('Free-action choice must include the author instruction')
        if self.author_source!='USER_MESSAGE':
            raise GateError('A generated answer cannot authorize its own closure')


class CanonicalCommitter(Protocol):
    def commit_previous(self, draft: EpisodeDraft, selection: AuthorSelection,
                        reviewed_events: list[dict], expected_head: dict) -> dict: ...


class EpisodeHandoff:
    def __init__(self, closure: EpisodeClosure):
        self.closure=closure
        self.store=closure.store
        c=self.store._connection()
        try:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS episode_handoff (
                episode_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN
                   ('RASCUNHO_LOCAL','RASCUNHO_ARQUIVADO','FECHANDO','FALHA_FECHAMENTO','FECHADO')),
                github_receipt_json TEXT,
                drive_receipt_json TEXT,
                selected_json TEXT,
                closed_receipt_json TEXT,
                last_error TEXT,
                updated_at TEXT NOT NULL
            );
            ''')
            c.commit()
        finally:c.close()

    def _entry(self,episode_id: str):
        c=self.store._connection()
        try:
            row=c.execute('SELECT * FROM episode_handoff WHERE episode_id=?',(episode_id,)).fetchone()
            return dict(row) if row else None
        finally:c.close()

    def _update(self,episode_id: str, status: str, *, github=None, drive=None,
                selection=None, closed=None, error=None):
        c=self.store._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT * FROM episode_handoff WHERE episode_id=?',(episode_id,)).fetchone()
            if not row:raise KeyError(episode_id)
            # Never roll back a closed episode to a draft.
            if row['status']=='FECHADO' and status!='FECHADO':
                raise GateError('Cannot reopen a canonical episode')
            fields={'status':status,'updated_at':utcnow(),'last_error':error}
            if github is not None:fields['github_receipt_json']=encoded(github)
            if drive is not None:fields['drive_receipt_json']=encoded(drive)
            if selection is not None:fields['selected_json']=encoded(selection)
            if closed is not None:fields['closed_receipt_json']=encoded(closed)
            sql='UPDATE episode_handoff SET '+','.join(k+'=?' for k in fields)+' WHERE episode_id=?'
            c.execute(sql,(*fields.values(),episode_id))
            c.commit()
        except Exception:c.rollback();raise
        finally:c.close()
        return self.status(episode_id)

    def status(self,episode_id):
        row=self._entry(episode_id)
        if row is None:raise KeyError(episode_id)
        for col in ('github_receipt_json','drive_receipt_json','selected_json','closed_receipt_json'):
            if row[col]:row[col[:-5]]=json.loads(row[col])
        return row

    def stage_after_options(self, draft: EpisodeDraft, *, drive_sync=None,
                            github_private=None, artifacts=None) -> dict:
        """Idempotent post-render staging. HEAD remains at the PREVIOUS episode.

        Both authenticated destinations are necessary before next choice may
        close this installment. Missing credentials leave RASCUNHO_LOCAL.
        """
        if draft.metadata.get('canon_status')!='RASCUNHO':
            raise GateError('A generated episode must be RASCUNHO until the next author choice')
        local=self.closure.stage(draft)
        manifest=self.closure.verify_package(draft.delivery_id)
        c=self.store._connection()
        try:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute('SELECT * FROM episode_handoff WHERE episode_id=?',(draft.delivery_id,)).fetchone()
            if r and r['sha256']!=local['sha256']:
                raise ConflictError('Immutable draft ID reused for a different narrative')
            if not r:
                c.execute('INSERT INTO episode_handoff(episode_id,sha256,status,updated_at) VALUES (?,?,?,?)',
                          (draft.delivery_id,local['sha256'],'RASCUNHO_LOCAL',utcnow()))
            c.commit()
        except Exception:c.rollback();raise
        finally:c.close()
        already=self.status(draft.delivery_id)
        if already['status'] in ('FECHADO','FECHANDO','FALHA_FECHAMENTO'):return already
        if drive_sync is not None:
            from .drive_bridge import GoogleDriveSynchronizer
            if not isinstance(drive_sync, GoogleDriveSynchronizer):
                raise GateError('Use the authenticated Google Drive synchronizer')
        if github_private is not None:
            from .private_github import PrivateGitHubArchive
            if not isinstance(github_private,PrivateGitHubArchive):
                raise GateError('Use the private-only GitHub archiver')
        # Check destinations independently, and preserve successful receipts if
        # the other side fails; subsequent calls are idempotent retries.
        if drive_sync is not None and not already.get('drive_receipt_json'):
            verified=drive_sync.sync(self.store,draft.delivery_id)
            self.store.confirm(draft.delivery_id)
            # A draft is REMOTELY SAVED but it is NOT CANONIZED.
            receipt=self.store.receipt(draft.delivery_id)['external']
            if not receipt or receipt.get('sha256')!=local['sha256']:
                raise GateError('Drive draft readback missing')
            self._update(draft.delivery_id,'RASCUNHO_LOCAL',drive=receipt)
        already=self.status(draft.delivery_id)
        if github_private is not None and not already.get('github_receipt_json'):
            archive=github_private.stage_package(draft.delivery_id,local['package_dir'])
            if archive['narrativa_integral.md']['sha256']!=local['sha256']:
                raise GateError('GitHub archive differs from literal')
            self._update(draft.delivery_id,'RASCUNHO_LOCAL',github=archive)
        result=self.status(draft.delivery_id)
        if result.get('drive_receipt_json') and result.get('github_receipt_json'):
            gh=result['github_receipt']
            if any(not isinstance(v,dict) or v.get('verification')!='github_private_contents_readback' for v in gh.values()):
                raise GateError('Unverified GitHub archive item')
            return self._update(draft.delivery_id,'RASCUNHO_ARQUIVADO')
        return result

    def on_next_choice(self, draft: EpisodeDraft, choice: AuthorSelection, *,
                       reviewed_events: list[dict], expected_head: dict,
                       trusted_committer: CanonicalCommitter, allow_test_committer=False) -> dict:
        """Close the previous episode FIRST; only then authorize next creation.

        The committer must guarantee Drive/GitHub/Base/Atlas/HEAD readbacks.
        It should be run inside a trusted orchestration environment with
        verified author instruction, not called from generated prose itself.
        """
        choice.validate()
        if choice.episode_id!=draft.delivery_id:raise GateError('Choice refers to a different episode')
        r=self.status(draft.delivery_id)
        if r['sha256']!=digest(draft.full_text.encode('utf-8')):
            raise ConflictError('Choice draft content differs from archived text')
        if r['status']=='FECHADO':
            if r.get('selected') != vars(choice):
                raise ConflictError('This episode has already been closed with another choice')
            return {'previous_status':'FECHADO','next_generation_allowed':True,
                    'head':r.get('closed'),'idempotent_replay':True}
        if r['status'] not in ('RASCUNHO_ARQUIVADO','FECHANDO','FALHA_FECHAMENTO'):
            raise GateError('Cannot start new episode: previous draft not archived in both services')
        if not expected_head or not expected_head.get('release') or expected_head.get('day') is None:
            raise GateError('A verified expected HEAD release/day is required')
        if not reviewed_events or any(e.get('canon_status')!='NARRADO' or not e.get('event_id') for e in reviewed_events):
            raise GateError('All selected prior-episode events require stable IDs and NARRADO review')
        if not allow_test_committer and not isinstance(trusted_committer,VerifiedCanonCommitter):
            raise GateError('Real canonical committer required; generated receipts are not evidence')
        prior_selection=r.get('selected')
        if prior_selection and prior_selection!=vars(choice):
            raise ConflictError('An earlier, different author choice is already being processed')
        # Commit intent BEFORE calling external systems. On retry, the same
        # selection is enforced and the committer must resume idempotently.
        self._update(draft.delivery_id,'FECHANDO',selection=vars(choice))
        try:
            receipt=trusted_committer.commit_previous(draft,choice,reviewed_events,expected_head)
            # The trusted caller is responsible for actual external evidence.
            # A bare response from the model is NOT a valid committer.
            needed={'verified_drive','verified_github_private','verified_base','verified_atlas','verified_head'}
            if not isinstance(receipt,dict) or any(receipt.get(k) is not True for k in needed):
                raise GateError('Closure prerequisites not independently verified')
            if receipt.get('episode_id')!=draft.delivery_id:
                raise GateError('Canonical closure receipt has wrong episode ID')
            current=receipt.get('new_head') or {}
            if current.get('episode_id')!=draft.delivery_id or not current.get('release'):
                raise GateError('HEAD did not advance to the episode being closed')
            self._update(draft.delivery_id,'FECHADO',closed=receipt)
            return {'previous_status':'FECHADO','next_generation_allowed':True,
                    'head':receipt,'idempotent_replay':False,
                    'new_episode_status':'PODE_CRIAR_RASCUNHO'}
        except Exception as exc:
            self._update(draft.delivery_id,'FALHA_FECHAMENTO',error=str(exc)[:400])
            raise

class PrivateCanonicalGitHubPublisher:
    """Adapter for EpisodePublicationCoordinator's GitHub publisher contract."""
    def __init__(self, archive, package_root):
        self.archive=archive
        self.package_root=package_root

    def publish(self, canonical_draft):
        p=self.package_root/'episode_packages'/canonical_draft.delivery_id
        receipts=self.archive.stage_package(canonical_draft.delivery_id,p)
        for artifact in receipts.values():
            if artifact.get('verification')!='github_private_contents_readback':
                raise GateError('Private GitHub archive was not independently verified')
        return {'verification':'github_private_contents_readback',
                'artifacts':receipts,'path':f'episodes/{canonical_draft.delivery_id}/draft/',
                'commit':receipts['manifesto_imutavel.json'].get('commit')}


class VerifiedCanonCommitter:
    """Delegates verified publication to the existing guarded saga coordinator.

    `coordinator` is EpisodePublicationCoordinator configured with an authenticated
    Drive sync, private GitHub publisher, readback-capable Base/Atlas indices and
    guarded Docs HEAD publisher. Its `publish()` checks these dependencies first.
    """
    def __init__(self, coordinator, *, expected_head_revision: str):
        self.coordinator=coordinator
        self.expected_head_revision=expected_head_revision

    def commit_previous(self, draft, selection, reviewed_events, expected_head):
        from .semantic_gate import require_reviewed_event_evidence
        require_reviewed_event_evidence(draft, reviewed_events)
        if not self.expected_head_revision:
            raise GateError('Remote HEAD revision must be supplied by authenticated Docs read')
        source_metadata=dict(draft.metadata)
        source_metadata['canon_status']='NARRADO'
        source_metadata['source_episode_id']=draft.delivery_id
        source_metadata['next_author_choice']=vars(selection)
        # The original draft remains immutable. The closing event stream owns new
        # stable IDs to avoid collisions with the earlier staging records.
        derived=[]
        for event in reviewed_events:
            item=dict(event)
            old_id=item['event_id']
            item['event_id']=old_id+'-CLOSED'
            item['draft_event_id']=old_id
            item['canon_status']='NARRADO'
            derived.append(item)
        closing=EpisodeDraft(delivery_id=draft.delivery_id+'-CLOSED',
            prose=draft.prose,full_text=draft.full_text,
            metadata=source_metadata,choices=draft.choices,
            events=derived,book_closed=draft.book_closed,
            editorial_visibility='PRIVADO')
        r=self.coordinator.publish(closing,author_approved=True,
            expected_head_revision=self.expected_head_revision,
            expected_head_release=expected_head['release'],
            expected_head_day=expected_head['day'])
        head=r.get('head') or {}
        drive=r.get('drive') or {}
        gh=r.get('github') or {}
        base=r.get('base') or {}
        atlas=r.get('atlas') or {}
        head_doc=r.get('head_document') or {}
        if r.get('status')!='CANONICO' or head.get('delivery_id')!=closing.delivery_id:
            raise GateError('Canonical publication did not finish')
        return {
            'episode_id':draft.delivery_id,
            'canonical_delivery_id':closing.delivery_id,
            'verified_drive':drive.get('verification')=='google_drive_get_media',
            'verified_github_private':gh.get('verification')=='github_private_contents_readback',
            'verified_base':base.get('verified') is True,
            'verified_atlas':atlas.get('verified') is True,
            'verified_head':head_doc.get('verification')=='required_revision_id_readback',
            'new_head':{'release':head.get('release'),'episode_id':draft.delivery_id,
                        'canonical_delivery_id':closing.delivery_id,
                        'day':head.get('day'),'hour':head.get('hour')},
            'source_sha256':digest(draft.full_text.encode('utf-8')),
            'author_selection':vars(selection),
        }
