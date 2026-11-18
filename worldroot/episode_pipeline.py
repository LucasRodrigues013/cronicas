"""WORLDROOT: fail-closed episode closure, layered on the existing r7 ledger.

Private canonical story bytes live in Google Drive; the public GitHub repository
receives only opaque technical receipts. This module does not watch ChatGPT turns.
An authenticated runtime must explicitly call stage() and publish().
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .ledger import WorldrootStore, GateError, ConflictError, IDENTIFIER, digest
from .drive_bridge import GoogleDriveSynchronizer
from .narrative import Choice, validate_interface


def json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def atomic_immutable(path: Path, body: bytes) -> None:
    """Retry-safe and never silently overwrite bytes from a previous chapter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != body:
            raise ConflictError(f'Existing artifact changed: {path.name}')
        return
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent, prefix='.worldroot_', delete=False) as fp:
            tmp = Path(fp.name)
            fp.write(body)
            fp.flush()
            os.fsync(fp.fileno())
        # Only one trusted worker may own a runtime directory. Concurrent writers must
        # use an external job queue / lock; os.replace alone is not compare-and-swap.
        if path.exists():
            if path.read_bytes() != body:
                raise ConflictError(f'Concurrent artifact conflict: {path.name}')
        else:
            os.replace(tmp, path)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


@dataclass(frozen=True)
class EpisodeDraft:
    delivery_id: str
    prose: str
    full_text: str  # EXACT final user-visible chapter + all options, including whitespace
    metadata: dict
    choices: list[Choice]
    events: list[dict]
    book_closed: bool = False
    editorial_visibility: str = 'PRIVADO'

    @classmethod
    def from_dict(cls, payload: dict) -> 'EpisodeDraft':
        choices = [Choice(**entry) for entry in payload['choices']]
        return cls(payload['delivery_id'], payload['prose'], payload['full_text'],
                   payload['metadata'], choices, payload.get('events', []),
                   payload.get('book_closed', False), payload.get('editorial_visibility', 'PRIVADO'))

    def validate(self) -> dict:
        if not IDENTIFIER.fullmatch(self.delivery_id):
            raise ValueError('Stable ASCII episode/delivery ID required')
        if self.editorial_visibility != 'PRIVADO':
            raise GateError('Unreviewed narrative must remain private')
        if not isinstance(self.full_text, str) or not self.full_text.startswith(self.prose):
            raise GateError('full_text must contain the UNMODIFIED prose as its exact prefix')
        if not self.prose.strip() or len(self.prose) < 50:
            raise GateError('Refuse to archive an empty/truncated scene')
        for choice in self.choices:
            if choice.title not in self.full_text:
                raise GateError(f'Choice {choice.number} not present in the literal rendered text')
        result = validate_interface(prose=self.prose, book_closed=self.book_closed,
                                    chapter=self.metadata.get('chapter', 0),
                                    part=self.metadata.get('part', ''),
                                    choices=self.choices, actual_save_receipt=None)
        if not result['ok']:
            raise GateError('Narrative/interface preflight: ' + '; '.join(result['errors']))
        if self.metadata.get('canon_status') not in ('NARRADO','RASCUNHO','SIMULADO'):
            raise GateError('Must distinguish NARRADO, RASCUNHO and SIMULADO')
        # A model must never grant itself approval to edit a remote canonical HEAD.
        if self.metadata.get('approval') == 'AUTO_FROM_MODEL':
            raise GateError('Author approval cannot originate from the generated model output')
        return result

    def public_marker(self, sha: str, bytes_count: int) -> dict:
        """No character names, day, places, plot, Drive URLs or private metadata."""
        return {'format':'worldroot-private-episode-receipt-v1','sha256':sha,
                'bytes':bytes_count, 'story_content_in_github':False}


class EpisodeClosure:
    """Stage immutable local/Drive artifacts. No implicit canon promotion."""
    def __init__(self, store: WorldrootStore):
        self.store = store

    def stage(self, draft: EpisodeDraft) -> dict:
        preflight=draft.validate()
        r=self.store.prepare(draft.delivery_id,draft.full_text,draft.metadata,draft.events)
        if r['state']=='PREPARADO': self.store.validate(draft.delivery_id)
        r=self.store.receipt(draft.delivery_id)
        if r['state']=='VALIDADO': self.store.write_literal(draft.delivery_id,draft.full_text)
        r=self.store.receipt(draft.delivery_id)
        if r['state']=='GRAVADO': self.store.verify_local(draft.delivery_id)
        r=self.store.receipt(draft.delivery_id)
        if r['state'] not in ('CONFERIDO','CONFIRMADO'):
            raise GateError('Local archive was not independently verified')

        folder=self.store.private/'episode_packages'/draft.delivery_id
        files={
          'narrativa_integral.md': draft.full_text.encode('utf-8'),
          'opcoes.json': json_bytes([vars(c) for c in draft.choices]),
          'eventos_e_consequencias.json': json_bytes(draft.events),
          'checkpoint_candidato.json': json_bytes(draft.metadata),
          # Recover EXACT original prose/choices after chat truncation: no
          # reconstruction from a summary or heuristic text splitting.
          'episode_draft.json': json_bytes({
              'delivery_id':draft.delivery_id,
              'prose':draft.prose,'full_text':draft.full_text,
              'metadata':draft.metadata,'choices':[vars(c) for c in draft.choices],
              'events':draft.events,'book_closed':draft.book_closed,
              'editorial_visibility':draft.editorial_visibility}),
        }
        manifest={
          'schema':'worldroot-episode-package-v1',
          'delivery_id':draft.delivery_id,
          'canon_status':draft.metadata['canon_status'],
          'original_readback_sha256':r['sha256'],
          'artifacts':{n:{'sha256':digest(b),'bytes':len(b)} for n,b in files.items()},
          'external_saving':'PENDENTE_ATE_READBACK',
          'github_full_story':False,
        }
        files['manifesto_imutavel.json']=json_bytes(manifest)
        for name,data in files.items():atomic_immutable(folder/name,data)
        # User-facing receipt MUST NOT claim that HEAD / GitHub / Drive are updated.
        return {'id':draft.delivery_id,'state':r['state'], 'sha256':r['sha256'],
                'full_text_bytes':r['bytes'], 'package_dir':str(folder),
                'archive_count':len(files), 'preflight_notices':preflight['notices'],
                'external_saved':bool(r['external']),'canon_promoted':False}

    def verify_package(self, delivery_id: str) -> dict:
        folder=self.store.private/'episode_packages'/delivery_id
        manifest=json.loads((folder/'manifesto_imutavel.json').read_text(encoding='utf-8'))
        for name,meta in manifest['artifacts'].items():
            b=(folder/name).read_bytes()
            if digest(b)!=meta['sha256'] or len(b)!=meta['bytes']:
                raise GateError('Package artifact hash failed: '+name)
        literal=(folder/'narrativa_integral.md').read_bytes()
        r=self.store.receipt(delivery_id)
        if digest(literal)!=r['sha256']:
            raise GateError('Episode package differs from local ledger literal')
        return manifest


class VerifiedArtifactPublisher:
    """Upload/check sidecar JSON with the same authenticated transport API.

    Every item is a separate idempotent Drive blob bound to a unique synthetic
    delivery_id. The main chapter is saved with GoogleDriveSynchronizer.
    """
    def __init__(self, transport, folder_id: str):
        self.transport=transport
        self.folder_id=folder_id

    def sync_file(self, artifact_id: str, filename: str, contents: bytes):
        if not IDENTIFIER.fullmatch(artifact_id):
            raise ValueError('Invalid artifact ID')
        sha=digest(contents)
        existing=self.transport.find(self.folder_id,artifact_id)
        if len(existing)>1:raise ConflictError('Duplicate remote sidecars')
        # Existing Drive adapter always uploads text/plain, including UTF-8 JSON,
        # and retains the exact bytes without converting to a native Google Doc.
        name=artifact_id+'-'+sha[:16]+'.txt'
        remote=existing[0] if existing else self.transport.create(
            self.folder_id,name,artifact_id,sha,contents)
        meta=self.transport.info(remote['id'])
        props=meta.get('appProperties') or {}
        if (meta.get('name')!=name or meta.get('id')!=remote['id'] or
                self.folder_id not in meta.get('parents',[]) or
                props.get('worldroot_delivery')!=artifact_id or
                props.get('worldroot_sha256')!=sha or
                str(meta.get('size'))!=str(len(contents)) or
                not meta.get('version')):
            raise GateError('Artifact Drive provenance mismatch')
        downloaded=self.transport.download(remote['id'])
        if downloaded!=contents or digest(downloaded)!=sha:
            raise GateError('Sidecar Drive readback mismatch')
        return {'artifact_id':artifact_id,'file_id':meta['id'],
                'sha256':sha,'bytes':len(contents),'remote_version':str(meta['version']),
                'verification':'google_drive_get_media'}


class PublicGitHubReceipt:
    """Pluggable GitHub publisher: public repo receives only anonymized hashes.

    The actual GitHub API client is supplied by the trusted executor. No tokens
    or private Drive URLs are ever placed in this JSON payload.
    """
    def __init__(self, client):
        self.client=client

    def publish(self, episode: EpisodeDraft) -> dict:
        payload=episode.public_marker(digest(episode.full_text.encode('utf-8')),
                                      len(episode.full_text.encode('utf-8')))
        fname=hashlib.sha256(episode.delivery_id.encode()).hexdigest()[:32]+'.json'
        path='receipts/'+fname
        body=json_bytes(payload)
        # client.put_unique must use GitHub API create/update with SHA checking
        # and then GET the file back to verify exact bytes.
        result=self.client.put_unique(path,body)
        if self.client.read(path)!=body:
            raise GateError('GitHub readback failed for sanitized receipt')
        return {'path':path,'blob_sha256':digest(body),
                'commit':result.get('commit'),'verification':'github_readback'}


class EpisodePublicationCoordinator:
    """Explicit multi-service saga: HEAD is always updated last.

    All external publishers are injected and must be authenticated/trusted.
    This class cannot run itself when ChatGPT finishes displaying a message.
    """
    def __init__(self, closure: EpisodeClosure, *, drive_sync,
                 artifact_sync: VerifiedArtifactPublisher, github: PublicGitHubReceipt,
                 base_index, atlas_index, head_publisher):
        self.closure=closure
        self.drive_sync=drive_sync
        self.artifact_sync=artifact_sync
        self.github=github
        self.base_index=base_index
        self.atlas_index=atlas_index
        self.head_publisher=head_publisher

    def publish(self,draft: EpisodeDraft,*, author_approved: bool,
                expected_head_revision: str,expected_head_release: str,expected_head_day: int) -> dict:
        if not author_approved:
            raise GateError('An author choice or author-approved standing policy must be verified by the host')
        if draft.metadata.get('canon_status')!='NARRADO':
            raise GateError('Simulations and drafts cannot be canonicalized')
        if not draft.events or any(x.get('canon_status')!='NARRADO' for x in draft.events):
            raise GateError('Events require author-reviewed narrative state')
        store=self.closure.store
        local=self.closure.stage(draft)
        manifest=self.closure.verify_package(draft.delivery_id)
        self.drive_sync.sync(store,draft.delivery_id)
        store.confirm(draft.delivery_id)
        folder=Path(local['package_dir'])
        sidecars={}
        for n in ['manifesto_imutavel.json','opcoes.json','eventos_e_consequencias.json','checkpoint_candidato.json','episode_draft.json']:
            artifact_id=draft.delivery_id+'-'+hashlib.sha256(n.encode()).hexdigest()[:12]
            sidecars[n]=self.artifact_sync.sync_file(artifact_id,n,(folder/n).read_bytes())
        github=self.github.publish(draft)
        base=self.base_index.record(draft.delivery_id,manifest,sidecars)
        atlas=self.atlas_index.record(draft.delivery_id,manifest,sidecars)
        if not base.get('verified') or not atlas.get('verified'):
            raise GateError('Base and Atlas must both be read back before HEAD')
        # Existing GoogleDocsHeadPublisher validates revision and writes the marker.
        head=self.head_publisher.publish(store,draft.delivery_id,
            expected_revision=expected_head_revision,
            expected_local_release=expected_head_release,
            prerequisites_verified=True, author_approved=True)
        promoted=store.promote(draft.delivery_id, author_approved=True,
            expected_head_day=expected_head_day,expected_head_release=expected_head_release)
        return {'status':'CANONICO','head':promoted,'drive':store.receipt(draft.delivery_id)['external'],
                'sidecars':sidecars,'github':github,'base':base,'atlas':atlas,
                'head_document':head.get('remote_head'), 'local_stage':local['state']}
