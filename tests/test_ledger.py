import tempfile
import unittest
from pathlib import Path
from worldroot import WorldrootStore, ConflictError, GateError, InvalidStateError

META={'day':10,'book':'Livro de Testes','chapter':1,'part':'II','hour':'09h00','location':'local fictício','choice':'4'}
EVENT={'event_id':'EVT-0001','event_type':'DECISAO','body':'consequência de teste',
       'visibility':'PRIVADO_PERSONAGEM','canon_status':'NARRADO'}

class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=WorldrootStore(self.tmp.name)
        self.baseline()

    def baseline(self):
        return self.store.baseline(release='r7-test-baseline',day=9,book='Livro de Testes',chapter=1,
              part='I',hour='23h06',location='ponto canônico de teste',
              debts=['completude semântica pendente'],approved_by_author=True)

    def prepared(self):
        return self.store.prepare('UNIT-CH1-P2-D10','Texto literal de teste.\n',META,[EVENT])

    def checked_locally(self):
        self.prepared();self.store.validate('UNIT-CH1-P2-D10')
        self.store.write_literal('UNIT-CH1-P2-D10','Texto literal de teste.\n')
        return self.store.verify_local('UNIT-CH1-P2-D10')

    def completed(self):
        self.checked_locally()
        self.store.record_external_readback('UNIT-CH1-P2-D10',provider='google_drive',locator='drive-fixture-id',returned_bytes=b'Texto literal de teste.\n')
        return self.store.confirm('UNIT-CH1-P2-D10')

    def test_schema_integrity(self):self.assertEqual(self.store.status()['db_integrity'],'ok')
    def test_baseline_no_semantic_certification(self):
        self.assertIn('NOT_CERTIFIED',str(self.store.status()['head']['release_record_json']))
    def test_baseline_no_double(self):self.assertEqual(self.baseline()['release'],'r7-test-baseline')
    def test_baseline_requires_debt(self):
        with self.assertRaises(GateError):self.store.baseline(release='other',day=528,book='V',chapter=1,part='I',hour='00',location='x',debts=[],approved_by_author=True)
    def test_prepare_idempotent(self):self.assertEqual(self.prepared(),self.prepared())
    def test_duplicate_different_text_forbidden(self):
        self.prepared()
        with self.assertRaises(ConflictError):self.store.prepare('UNIT-CH1-P2-D10','Diferente',META,[EVENT])
    def test_missing_choice(self):
        m=dict(META);m.pop('choice')
        with self.assertRaises(ValueError):self.store.prepare('UNIT-CH1-P2-D10','texto',m,[])
    def test_no_unapproved_baseline(self):
        with self.assertRaises(GateError):self.store.baseline(release='other',day=528,book='V',chapter=1,part='I',hour='00',location='x',debts=['x'],approved_by_author=False)
    def test_no_write_before_validation(self):
        self.prepared()
        with self.assertRaises(InvalidStateError):self.store.write_literal('UNIT-CH1-P2-D10','Texto literal de teste.\n')
    def test_no_changed_bytes_written(self):
        self.prepared();self.store.validate('UNIT-CH1-P2-D10')
        with self.assertRaises(ConflictError):self.store.write_literal('UNIT-CH1-P2-D10','Outro texto')
    def test_full_local_flow(self):
        r=self.completed()
        self.assertEqual(r['state'],'CONFIRMADO')
        self.assertEqual(Path(r['local_path']).read_text(),'Texto literal de teste.\n')
    def test_no_duplicate_events_on_retry(self):
        self.completed();self.store.confirm('UNIT-CH1-P2-D10')
        self.assertEqual(self.store.status()['event_count'],1)
    def test_no_promotion_without_drive(self):
        r=self.checked_locally()
        self.assertEqual(r['state'],'CONFERIDO')
        with self.assertRaises(GateError):self.store.confirm('UNIT-CH1-P2-D10')
        with self.assertRaises(GateError):self.store.promote('UNIT-CH1-P2-D10',author_approved=True,expected_head_day=9)
    def test_no_promotion_without_approval(self):
        self.completed()
        with self.assertRaises(GateError):self.store.promote('UNIT-CH1-P2-D10',author_approved=False,expected_head_day=9)
    def test_reject_external_wrong_bytes(self):
        self.completed()
        with self.assertRaises(GateError):self.store.record_external_readback('UNIT-CH1-P2-D10',provider='google_drive',locator='id',returned_bytes=b'wrong')
    def test_external_validated_promote(self):
        self.completed();self.store.record_external_readback('UNIT-CH1-P2-D10',provider='google_drive',locator='drive-fixture-id',returned_bytes=b'Texto literal de teste.\n')
        promoted=self.store.promote('UNIT-CH1-P2-D10',author_approved=True,expected_head_day=9)
        self.assertEqual(promoted['day'],10)
        self.assertEqual(self.store.status()['head']['day'],10)
    def test_reject_stale_head(self):
        self.completed()
        with self.assertRaises(GateError):self.store.promote('UNIT-CH1-P2-D10',author_approved=True,expected_head_day=8)
    def test_chronology_day_must_be_int(self):
        with self.assertRaises(ValueError):self.store.prepare('BAD-DATE-001','texto',dict(META,day='10'),[])
    def test_still_pending_local_only(self):
        r=self.checked_locally()
        self.assertIsNone(r['external'])
        self.assertEqual(r['state'],'CONFERIDO')
        self.assertEqual(self.store.status()['event_count'],0)

    def test_no_unauthorized_event_state(self):
        bad={**EVENT,'canon_status':'FAKE'}
        with self.assertRaises(ValueError):self.store.prepare('UNIT-CH1-P2-D10','x',META,[bad])
    def test_no_event_overwrite(self):
        self.completed()
        meta={**META,'day':9}
        with self.assertRaises(ConflictError):
            self.store.prepare('UNIT-CH1-OTHER','Diferente',meta,[{**EVENT}])
    def test_no_promotion_without_events(self):
        self.store.prepare('EVENTLESS-DELIVERY','Texto de teste', META, [])
        self.store.validate('EVENTLESS-DELIVERY')
        self.store.write_literal('EVENTLESS-DELIVERY','Texto de teste')
        self.store.verify_local('EVENTLESS-DELIVERY')
        self.store.record_external_readback('EVENTLESS-DELIVERY', provider='google_drive', locator='fixture', returned_bytes=b'Texto de teste')
        self.store.confirm('EVENTLESS-DELIVERY')
        with self.assertRaises(GateError):
            self.store.promote('EVENTLESS-DELIVERY',author_approved=True,expected_head_day=9)

    def test_no_backward_chronology(self):
        self.store.prepare('OLD-DELIVERY','Texto',dict(META,day=5),[])
        with self.assertRaises(GateError):self.store.validate('OLD-DELIVERY')
    def test_no_future_leap(self):
        self.store.prepare('FUTURE-DELIVERY','Texto',dict(META,day=15),[])
        with self.assertRaises(GateError):self.store.validate('FUTURE-DELIVERY')

if __name__=='__main__':unittest.main(verbosity=2)
