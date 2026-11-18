"""Synthetic end-to-end handoff tests; never contains user story bytes."""
import tempfile
import hashlib
import unittest
from pathlib import Path

from worldroot.ledger import WorldrootStore, GateError, ConflictError
from worldroot.narrative import Choice
from worldroot.episode_pipeline import EpisodeDraft, EpisodeClosure
from worldroot.episode_handoff import EpisodeHandoff, AuthorSelection
from worldroot.drive_bridge import GoogleDriveSynchronizer
from worldroot.private_github import PrivateGitHubArchive


CHOICES=[
    Choice(1,'Synthetic road A','Gain one view; risk another'),
    Choice(2,'Synthetic road B','Gain history; risk time'),
    Choice(3,'Synthetic road C','Gain detail; risk hesitation'),
    Choice(4,'SPECIAL: Synthetic surprise','Gain emotion; uncertain effects',is_special=True),
    Choice(5,'Free action','',is_free=True),
]
PROSE=('LIVRO SINTÉTICO — CAPÍTULO 2 · PARTE I\n'
       'Uma cena de teste que não contém acontecimentos do universo real.\n'
       'PERSONAGEM A — Este texto é apenas uma experiência de qualidade.\n')
FULL=PROSE+'\n'+''.join(f'{c.number} — {c.title}\n{c.description}\n' for c in CHOICES)
META={'day':10,'book':'Livro Sintético','chapter':15,'part':'II','hour':'20h42',
      'location':'Local fictício','choice':'4','canon_status':'RASCUNHO'}
EV={'event_id':'SYNTHETIC-EVT-001','event_type':'ACONTECIMENTO','body':'SYNTHETIC ONLY',
    'visibility':'PRIVADO_PERSONAGEM','canon_status':'PENDENTE_APROVACAO'}


class MemoryDrive:
    def __init__(self):self.files={};self.uploads=0;self.fail=False
    def find(self,folder,delivery):
        return [a.copy() for a,b in self.files.values() if a['appProperties']['worldroot_delivery']==delivery and folder in a['parents']]
    def create(self,folder,name,delivery,sha,body):
        self.uploads+=1
        metadata={'id':str(self.uploads),'name':name,'size':str(len(body)),
                  'md5Checksum':hashlib.md5(body).hexdigest(),'version':'1',
                  'parents':[folder],'mimeType':'text/plain',
                  'appProperties':{'worldroot_delivery':delivery,'worldroot_sha256':sha}}
        self.files[str(self.uploads)]=(metadata,body);return metadata.copy()
    def info(self,file_id):return self.files[file_id][0].copy()
    def download(self,file_id):
        if self.fail:raise OSError('synthetic outage')
        return self.files[file_id][1]

class MemoryGitHub:
    def __init__(self,private=True):self.private=private;self.files={};self.uploads=0;self.repo="synthetic/private";self.branch="story-archive"
    def metadata(self):return {'private':self.private,'visibility':'private' if self.private else 'public','permissions':{'push':True}}
    def get(self,path):
        if path not in self.files:return None
        return {'bytes':self.files[path],'sha':'synthetic'}
    def create(self,path,body):
        if path in self.files:raise GateError('synthetic conflict')
        self.files[path]=body;self.uploads+=1
        return 'synthetic-commit'

class SyntheticCommitter:
    def __init__(self,fail=False):self.fail=fail;self.count=0
    def commit_previous(self,draft,choice,events,head):
        self.count+=1
        if self.fail:raise OSError('synthetic dependency outage')
        return {'episode_id':draft.delivery_id,
                'verified_drive':True,'verified_github_private':True,
                'verified_base':True,'verified_atlas':True,'verified_head':True,
                'new_head':{'episode_id':draft.delivery_id,'release':'r7-test+episode'}}

class HandoffTest(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.store=WorldrootStore(t.name)
        self.store.baseline(release='r7-synthetic-D09',day=9,book='Livro Sintético',chapter=15,
                            part='I',hour='23h06',location='Synthetic',
                            debts=['This is not a real narrative'],approved_by_author=True)
        self.closure=EpisodeClosure(self.store)
        self.flow=EpisodeHandoff(self.closure)
        self.disk_drive=MemoryDrive()
        self.drive=GoogleDriveSynchronizer(self.disk_drive,'test-folder',allow_synthetic_test_transport=True)
        self.fake_github=MemoryGitHub()
        self.github=PrivateGitHubArchive(self.fake_github,allow_fake_for_tests=True)
        self.draft=EpisodeDraft('SYNTHETIC-EP-10',PROSE,FULL,META,CHOICES,[EV])
        self.selection=AuthorSelection(self.draft.delivery_id,4)
        self.canon_events=[{**EV,'canon_status':'NARRADO'}]
    def local(self):return self.flow.stage_after_options(self.draft)
    def remote(self):return self.flow.stage_after_options(self.draft,drive_sync=self.drive,github_private=self.github)
    def close(self,committer=None,selection=None,events=None, **extra):
        return self.flow.on_next_choice(self.draft,selection or self.selection,
                 reviewed_events=events if events is not None else self.canon_events,
                 expected_head={'release':'r7-synthetic-D09','day':9},
                 trusted_committer=committer or SyntheticCommitter(),allow_test_committer=True,**extra)
    def test_local_draft_does_not_change_head(self):
        x=self.local();self.assertEqual(x['status'],'RASCUNHO_LOCAL')
        self.assertEqual(self.store.status()['head']['day'],9)
        with self.assertRaises(GateError):self.close()
    def test_private_repo_required_before_upload(self):
        self.fake_github.private=False
        with self.assertRaises(GateError):self.remote()
        self.assertEqual(self.fake_github.uploads,0)
        self.assertEqual(self.store.status()['head']['day'],9)
        self.assertIsNotNone(self.flow.status(self.draft.delivery_id)['drive_receipt'])
    def test_retry_after_visibility_change(self):
        self.fake_github.private=False
        with self.assertRaises(GateError):self.remote()
        self.fake_github.private=True
        r=self.remote();self.assertEqual(r['status'],'RASCUNHO_ARQUIVADO')
        self.assertEqual(self.disk_drive.uploads,1)
        self.assertEqual(self.fake_github.uploads,6)
    def test_successful_stage_only_not_canon(self):
        r=self.remote()
        self.assertEqual(r['status'],'RASCUNHO_ARQUIVADO')
        self.assertEqual(self.store.status()['head']['day'],9)
        self.assertEqual(self.store.receipt(self.draft.delivery_id)['state'],'CONFIRMADO')
        self.assertEqual(self.store.receipt(self.draft.delivery_id)['metadata']['canon_status'],'RASCUNHO')
    def test_restore_exact_draft_from_private_github(self):
        self.remote()
        recovered=self.github.recover_draft(self.draft.delivery_id)
        self.assertEqual(recovered.full_text,self.draft.full_text)
        self.assertEqual(recovered.prose,self.draft.prose)
        self.assertEqual(len(recovered.choices),5)

    def test_corrupt_archived_json_detected_on_recovery(self):
        self.remote()
        path=f'episodes/{self.draft.delivery_id}/draft/episode_draft.json'
        self.fake_github.files[path]=b'CORRUPTED'
        with self.assertRaises(GateError):self.github.recover_draft(self.draft.delivery_id)

    def test_do_not_reset_closing_intent_on_stage_retry(self):
        self.remote()
        publisher=SyntheticCommitter(fail=True)
        with self.assertRaises(OSError):self.close(publisher)
        before=self.flow.status(self.draft.delivery_id)
        self.remote()
        after=self.flow.status(self.draft.delivery_id)
        self.assertEqual(before['status'],after['status'])
        self.assertEqual(after['status'],'FALHA_FECHAMENTO')

    def test_stage_idempotent_no_duplicate_files(self):
        self.remote();self.remote()
        self.assertEqual(self.disk_drive.uploads,1)
        self.assertEqual(self.fake_github.uploads,6)
    def test_changed_episode_rejected(self):
        self.local()
        changed=EpisodeDraft(self.draft.delivery_id,PROSE,FULL+'CORRUPTION',META,CHOICES,[EV])
        with self.assertRaises(ConflictError):self.flow.stage_after_options(changed)
    def test_tampered_github_repo_public_on_next_file(self):
        self.fake_github.private=False
        self.local()
        with self.assertRaises(GateError):self.github.stage_package(self.draft.delivery_id,self.store.private/'episode_packages'/self.draft.delivery_id)
    def test_close_success_after_selection(self):
        self.remote();x=self.close()
        self.assertTrue(x['next_generation_allowed'])
        self.assertEqual(self.flow.status(self.draft.delivery_id)['status'],'FECHADO')
    def test_selection_same_replay_idempotent(self):
        self.remote();publisher=SyntheticCommitter();self.close(publisher)
        again=self.close(publisher)
        self.assertTrue(again['idempotent_replay'])
        self.assertEqual(publisher.count,1)
    def test_no_new_generation_after_commit_failure(self):
        self.remote();publisher=SyntheticCommitter(fail=True)
        with self.assertRaises(OSError):self.close(publisher)
        self.assertEqual(self.flow.status(self.draft.delivery_id)['status'],'FALHA_FECHAMENTO')
        publisher.fail=False
        result=self.close(publisher)
        self.assertTrue(result['next_generation_allowed'])
        self.assertEqual(publisher.count,2)
    def test_different_choice_after_failed_commit_rejected(self):
        self.remote()
        with self.assertRaises(OSError):self.close(SyntheticCommitter(fail=True))
        with self.assertRaises(ConflictError):self.close(selection=AuthorSelection(self.draft.delivery_id,2))
    def test_different_choice_after_closed_rejected(self):
        self.remote();self.close()
        with self.assertRaises(ConflictError):self.close(selection=AuthorSelection(self.draft.delivery_id,2))
    def test_free_choice_requires_text(self):
        self.remote()
        with self.assertRaises(GateError):self.close(selection=AuthorSelection(self.draft.delivery_id,5))
    def test_invalid_choice(self):
        self.remote()
        with self.assertRaises(ValueError):self.close(selection=AuthorSelection(self.draft.delivery_id,6))
    def test_model_cannot_approve(self):
        self.remote()
        with self.assertRaises(GateError):self.close(selection=AuthorSelection(self.draft.delivery_id,4,author_source='AI_GENERATED'))
    def test_event_review_mandatory(self):
        self.remote()
        with self.assertRaises(GateError):self.close(events=[EV])
        with self.assertRaises(GateError):self.close(events=[])
    def test_result_cannot_be_fake_dict_missing_proofs(self):
        self.remote()
        class BadPublisher:
            def commit_previous(self,*a):return {'verified_drive':True}
        with self.assertRaises(GateError):self.close(BadPublisher())
        self.assertEqual(self.flow.status(self.draft.delivery_id)['status'],'FALHA_FECHAMENTO')
    def test_forged_publisher_not_allowed_in_production(self):
        self.remote()
        with self.assertRaises(GateError):self.flow.on_next_choice(
            self.draft,self.selection,reviewed_events=self.canon_events,
            expected_head={'release':'r7-synthetic-D09','day':9},
            trusted_committer=SyntheticCommitter(),allow_test_committer=False)
    def test_different_source_sha_blocks_advance(self):
        self.remote()
        m=EpisodeDraft(self.draft.delivery_id,PROSE,FULL+'x',META,CHOICES,[EV])
        with self.assertRaises(ConflictError):self.flow.on_next_choice(m,self.selection,
            reviewed_events=self.canon_events,expected_head={'release':'r7-synthetic-D09','day':9},
            trusted_committer=SyntheticCommitter(),allow_test_committer=True)
    def test_integrity(self):self.assertEqual(self.store.status()['db_integrity'],'ok')

if __name__=='__main__':unittest.main()

class IntegratedSyntheticPublicationTest(HandoffTest):
    """End-to-end simulation with independent fake APIs, no network/real story."""
    def test_private_archive_drive_sheets_head_and_next_episode_gate(self):
        from worldroot.episode_pipeline import EpisodePublicationCoordinator, VerifiedArtifactPublisher
        from worldroot.episode_handoff import (PrivateCanonicalGitHubPublisher, VerifiedCanonCommitter)
        from worldroot.drive_bridge import GoogleDocsHeadPublisher
        from worldroot.sheets_index import GoogleSheetsEpisodeIndex
        from test_ledger import FakeDoc
        from test_sheets_index import FakeSheetsAPI
        self.remote()
        d=FakeDoc();b=FakeSheetsAPI();a=FakeSheetsAPI()
        saga=EpisodePublicationCoordinator(self.closure,
            drive_sync=self.drive,
            artifact_sync=VerifiedArtifactPublisher(self.disk_drive,'test-folder'),
            github=PrivateCanonicalGitHubPublisher(self.github,self.store.private),
            base_index=GoogleSheetsEpisodeIndex(b,'SHEET-BASE'),
            atlas_index=GoogleSheetsEpisodeIndex(a,'SHEET-ATLAS'),
            head_publisher=GoogleDocsHeadPublisher(d,'fake-doc'))
        committer=VerifiedCanonCommitter(saga,expected_head_revision='v1')
        result=self.flow.on_next_choice(self.draft,self.selection,
            reviewed_events=self.canon_events,
            expected_head={'release':'r7-synthetic-D09','day':9},
            trusted_committer=committer)
        self.assertTrue(result['next_generation_allowed'])
        self.assertEqual(self.store.status()['head']['day'],10)
        self.assertEqual(self.store.status()['head']['part'],'II')
        self.assertIn('SYNTHETIC-EP-10-CLOSED',d.body)
        self.assertEqual(b.appends,1)
        self.assertEqual(a.appends,1)
        self.assertEqual(self.fake_github.uploads,12) # 6 draft + 6 canon
        self.assertEqual(self.disk_drive.uploads,7)  # 1 draft + 1 canonical + 5 sidecars
        retry=self.flow.on_next_choice(self.draft,self.selection,
            reviewed_events=self.canon_events,
            expected_head={'release':'r7-synthetic-D09','day':9},
            trusted_committer=committer)
        self.assertTrue(retry['idempotent_replay'])
        self.assertEqual(b.appends,1)
        self.assertEqual(a.appends,1)
        self.assertEqual(self.store.status()['head']['day'],10)
