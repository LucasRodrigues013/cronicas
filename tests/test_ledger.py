import hashlib
import tempfile
import unittest
from pathlib import Path
from worldroot.ledger import WorldrootStore, ConflictError, GateError, InvalidStateError
from worldroot.drive_bridge import GoogleDriveSynchronizer, GoogleDocsHeadPublisher

META={'day':10,'book':'Livro Sintético','chapter':1,'part':'II','hour':'09h00','location':'cidade fictícia','choice':'4'}
EVENT={'event_id':'EVT-SYN-01','event_type':'DECISAO','body':'synthetic test only',
       'visibility':'PRIVADO_PERSONAGEM','canon_status':'NARRADO'}
BODY='Original fictício imutável.\n'.encode()

class FakeDrive:
    def __init__(self):self.files={};self.upload_count=0;self.fail_download=False;self.tamper=False
    def find(self,folder_id,delivery_id):
        return [m.copy() for m,b in self.files.values() if m['appProperties']['worldroot_delivery']==delivery_id and folder_id in m['parents']]
    def create(self,folder_id,filename,delivery_id,sha256,body):
        self.upload_count+=1
        key='fake-drive-'+str(self.upload_count)
        meta={'id':key,'name':filename,'size':str(len(body)),
              'md5Checksum':hashlib.md5(body).hexdigest(),'version':'1','parents':[folder_id],
              'mimeType':'text/plain','appProperties':{'worldroot_delivery':delivery_id,'worldroot_sha256':sha256}}
        self.files[key]=(meta,body)
        return meta.copy()
    def info(self,file_id):return self.files[file_id][0].copy()
    def download(self,file_id):
        if self.fail_download:raise RuntimeError('Synthetic network failure')
        return self.files[file_id][1]+(b'tampered' if self.tamper else b'')

class FakeDoc:
    def __init__(self):self.rev='v1';self.body='Original synthetic HEAD.\n';self.fail_revision=False
    def documents(self):return self
    def get(self,documentId,fields):
        class Request:
            def __init__(self,fn):self.fn=fn
            def execute(self):return self.fn()
        return Request(lambda:{'documentId':documentId,'revisionId':self.rev,
          'body':{'content':[{'paragraph':{'elements':[{'textRun':{'content':self.body}}]}}]}})
    def batchUpdate(self,documentId,body):
        class Request:
            def __init__(self,fn):self.fn=fn
            def execute(self):return self.fn()
        def work():
            if body['writeControl']['requiredRevisionId']!=self.rev:
                raise RuntimeError('Synthetic concurrent write / 409')
            self.body=body['requests'][0]['insertText']['text']+self.body
            self.rev='v2'
            return {'documentId':documentId,'writeControl':{'requiredRevisionId':'v2'}}
        return Request(work)

class LedgerTest(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.store=WorldrootStore(t.name)
        self.drive=FakeDrive();self.sync=GoogleDriveSynchronizer(self.drive,'synthetic-folder',allow_synthetic_test_transport=True)
        self.doc=FakeDoc();self.publisher=GoogleDocsHeadPublisher(self.doc,'fake-doc')
        self.store.baseline(release='r7-synthetic',day=9,book=META['book'],chapter=1,part='I',
            hour='23h06',location='Synthetic',debts=['unfinished semantic reconciliation'],approved_by_author=True)
    def prepare(self,id='SYNTH-DEL-10',events=None,text=None,meta=None):
        return self.store.prepare(id,text if text is not None else BODY.decode(),
                                  meta if meta is not None else META,[EVENT] if events is None else events)
    def local(self,id='SYNTH-DEL-10',events=None,text=None,meta=None):
        self.prepare(id,events,text,meta);self.store.validate(id)
        self.store.write_literal(id,text if text is not None else BODY.decode())
        return self.store.verify_local(id)
    def confirmed(self,id='SYNTH-DEL-10',events=None,text=None,meta=None):
        self.local(id,events,text,meta);self.sync.sync(self.store,id)
        return self.store.confirm(id)
    def head(self,id='SYNTH-DEL-10'):
        return self.publisher.publish(self.store,id,expected_revision='v1',
            expected_local_release='r7-synthetic',prerequisites_verified=True,author_approved=True)
    def test_fake_transport_not_accepted_by_default(self):
        with self.assertRaises(GateError):GoogleDriveSynchronizer(self.drive,'synthetic-folder')
    def test_integrity(self):self.assertEqual(self.store.status()['db_integrity'],'ok')
    def test_author_approval_required(self):
        with self.assertRaises(GateError):self.store.baseline(release='bad',day=1,book='x',chapter=1,part='I',hour='09h00',location='x',debts=['debt'],approved_by_author=False)
    def test_baseline_idempotent(self):
        self.assertEqual(self.store.baseline(release='r7-synthetic',day=9,book=META['book'],chapter=1,part='I',hour='23h06',location='Synthetic',debts=['unfinished semantic reconciliation'],approved_by_author=True)['release'],'r7-synthetic')
    def test_prepared_idempotent(self):self.assertEqual(self.prepare(),self.prepare())
    def test_conflict_on_changed_text(self):
        self.prepare()
        with self.assertRaises(ConflictError):self.prepare(text='other')
    def test_missing_metadata(self):
        with self.assertRaises(ValueError):self.prepare(meta={k:v for k,v in META.items() if k!='choice'})
    def test_bad_time(self):
        for hour in ['29h92','24h00','12h60','noon','9h00']:
            with self.subTest(hour=hour),self.assertRaises(ValueError):self.prepare(meta={**META,'hour':hour})
    def test_legal_time(self):
        self.assertEqual(self.prepare(meta={**META,'hour':'23h59'})['state'],'PREPARADO')
    def test_no_write_before_validation(self):
        self.prepare()
        with self.assertRaises(InvalidStateError):self.store.write_literal('SYNTH-DEL-10',BODY.decode())
    def test_digest_protects_write(self):
        self.prepare();self.store.validate('SYNTH-DEL-10')
        with self.assertRaises(ConflictError):self.store.write_literal('SYNTH-DEL-10','changed')
    def test_local_only_cannot_confirm(self):
        self.local()
        with self.assertRaises(GateError):self.store.confirm('SYNTH-DEL-10')
    def test_forged_external_readback_rejected(self):
        self.local()
        with self.assertRaises(GateError):self.store.record_external_readback('SYNTH-DEL-10',provider='google_drive',locator='FAKE',returned_bytes=BODY)
        with self.assertRaises(GateError):self.store.confirm('SYNTH-DEL-10')
    def test_verified_remote_confirm(self):
        self.assertEqual(self.confirmed()['state'],'CONFIRMADO')
        self.assertEqual(self.store.status()['event_count'],1)
    def test_drive_idempotent(self):
        self.confirmed();self.sync.sync(self.store,'SYNTH-DEL-10');self.store.confirm('SYNTH-DEL-10')
        self.assertEqual(self.drive.upload_count,1)
        self.assertEqual(self.store.status()['event_count'],1)
    def test_remote_modified_contents_fail(self):
        self.local();self.drive.tamper=True
        with self.assertRaises(GateError):self.sync.sync(self.store,'SYNTH-DEL-10')
        self.assertIsNone(self.store.receipt('SYNTH-DEL-10')['external'])
    def test_remote_modified_metadata_fail(self):
        self.local();self.drive.create('synthetic-folder','SYNTH-DEL-10-'+self.store.receipt('SYNTH-DEL-10')['sha256'][:16]+'.txt','SYNTH-DEL-10',self.store.receipt('SYNTH-DEL-10')['sha256'],BODY)
        next(iter(self.drive.files.values()))[0]['parents']=['wrong-folder']
        # The file no longer appears in expected folder; adapter creates a new correct file.
        self.sync.sync(self.store,'SYNTH-DEL-10');self.assertEqual(self.drive.upload_count,2)
    def test_no_network_no_confirm_and_retry(self):
        self.local();self.drive.fail_download=True
        with self.assertRaises(RuntimeError):self.sync.sync(self.store,'SYNTH-DEL-10')
        self.assertEqual(self.drive.upload_count,1)
        self.drive.fail_download=False
        self.sync.sync(self.store,'SYNTH-DEL-10')
        self.assertEqual(self.drive.upload_count,1)
        self.assertEqual(self.store.confirm('SYNTH-DEL-10')['state'],'CONFIRMADO')
    def test_duplicate_remote_rejected(self):
        self.local();r=self.store.receipt('SYNTH-DEL-10')
        n='SYNTH-DEL-10-'+r['sha256'][:16]+'.txt'
        self.drive.create('synthetic-folder',n,'SYNTH-DEL-10',r['sha256'],BODY)
        self.drive.create('synthetic-folder',n,'SYNTH-DEL-10',r['sha256'],BODY)
        with self.assertRaises(ConflictError):self.sync.sync(self.store,'SYNTH-DEL-10')
    def test_canon_requires_head_receipt(self):
        self.confirmed()
        with self.assertRaises(GateError):self.store.promote('SYNTH-DEL-10',author_approved=True,expected_head_day=9,expected_head_release='r7-synthetic')
    def test_head_requires_prerequisites(self):
        self.confirmed()
        with self.assertRaises(GateError):self.publisher.publish(self.store,'SYNTH-DEL-10',expected_revision='v1',expected_local_release='r7-synthetic',prerequisites_verified=False,author_approved=True)
    def test_head_stale_remote_revision_fails(self):
        self.confirmed();self.doc.rev='v3'
        with self.assertRaises(ConflictError):self.head()
        self.assertIsNone(self.store.receipt('SYNTH-DEL-10')['remote_head'])
    def test_head_rejects_unapproved(self):
        self.confirmed()
        with self.assertRaises(GateError):self.publisher.publish(self.store,'SYNTH-DEL-10',expected_revision='v1',expected_local_release='r7-synthetic',prerequisites_verified=True)

    def test_head_readback_success(self):
        self.confirmed();r=self.head()
        self.assertEqual(r['remote_head']['new_revision'],'v2')
    def test_canon_requires_explicit_author(self):
        self.confirmed();self.head()
        with self.assertRaises(GateError):self.store.promote('SYNTH-DEL-10',author_approved=False,expected_head_day=9,expected_head_release='r7-synthetic')
    def test_canon_requires_head_release_match(self):
        self.confirmed();self.head()
        with self.assertRaises(GateError):self.store.promote('SYNTH-DEL-10',author_approved=True,expected_head_day=9,expected_head_release='wrong')
    def test_canon_requires_reviewed_events(self):
        self.confirmed(events=[{**EVENT,'canon_status':'PLANEJADO'}])
        with self.assertRaises(GateError):self.head()
    def test_canon_promotion_when_all_gates_verified(self):
        self.confirmed();self.head()
        self.assertEqual(self.store.promote('SYNTH-DEL-10',author_approved=True,expected_head_day=9,expected_head_release='r7-synthetic')['day'],10)
    def test_no_events_no_promotion(self):
        self.confirmed(events=[])
        with self.assertRaises(GateError):self.head()
    def test_no_backward_day(self):
        self.prepare(meta={**META,'day':3})
        with self.assertRaises(GateError):self.store.validate('SYNTH-DEL-10')
    def test_no_future_jump(self):
        self.prepare(meta={**META,'day':15})
        with self.assertRaises(GateError):self.store.validate('SYNTH-DEL-10')
    def test_same_day_clock_regression_rejected(self):
        self.prepare(meta={**META,'day':9,'hour':'22h59'})
        with self.assertRaises(GateError):self.store.validate('SYNTH-DEL-10')
    def test_no_book_transition_without_approval(self):
        self.prepare(meta={**META,'book':'New Book'})
        with self.assertRaises(GateError):self.store.validate('SYNTH-DEL-10')
    def test_outbox_on_network_failure(self):
        self.local();self.drive.fail_download=True
        with self.assertRaises(RuntimeError):self.sync.sync(self.store,'SYNTH-DEL-10')
        self.assertEqual(self.store.outbox_receipt('SYNTH-DEL-10','DRIVE_LITERAL')['status'],'FAILED')
        self.drive.fail_download=False;self.sync.sync(self.store,'SYNTH-DEL-10')
        self.assertEqual(self.store.outbox_receipt('SYNTH-DEL-10','DRIVE_LITERAL')['status'],'DONE')
    def test_no_reuse_event_id_in_pending(self):
        self.prepare()
        with self.assertRaises(ConflictError):self.prepare('OTHER-DEL-10',events=[EVENT])

if __name__=='__main__':unittest.main()
