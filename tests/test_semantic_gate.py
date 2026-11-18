"""Synthetic tests for literal, time and knowledge provenance gates."""
import hashlib
import unittest
from copy import deepcopy
from types import SimpleNamespace
from worldroot.ledger import GateError, ConflictError
from worldroot.semantic_gate import require_reviewed_event_evidence

TEXT='WORLDROOT TEST ONLY\nAt 10h37 Character One writes a letter.\nAt 20h42 the party continues.\n'
SHA=hashlib.sha256(TEXT.encode('utf-8')).hexdigest()
BASE={'event_id':'SYNTHETIC-EP-E001','canon_status':'NARRADO','visibility':'PUBLICO',
      'summary_candidato':'A synthetic letter is written in the synthetic passage.',
      'source':{'sha256':SHA,'line':2,'literal_anchor':'At 10h37 Character One writes a letter.'}}

class EvidenceGateTest(unittest.TestCase):
    def setUp(self):self.draft=SimpleNamespace(full_text=TEXT)
    def test_positive(self):self.assertEqual(require_reviewed_event_evidence(self.draft,[deepcopy(BASE)])['verified_evidence_anchors'],1)
    def test_empty_is_blocked(self):
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[])
    def test_planned_cannot_promote(self):
        e=deepcopy(BASE);e['canon_status']='PLANEJADO'
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
    def test_wrong_document_sha_is_blocked(self):
        e=deepcopy(BASE);e['source']['sha256']='0'*64
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
    def test_wrong_line_is_blocked(self):
        e=deepcopy(BASE);e['source']['line']=3
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
    def test_false_quote_is_blocked(self):
        e=deepcopy(BASE);e['source']['literal_anchor']='Something never narrated'
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
    def test_duplicate_event_is_blocked(self):
        with self.assertRaises(ConflictError):require_reviewed_event_evidence(self.draft,[deepcopy(BASE),deepcopy(BASE)])
    def test_wrong_visibility_is_blocked(self):
        e=deepcopy(BASE);e['visibility']='TODOS_SABEM'
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
    def test_untrusted_line_is_blocked(self):
        e=deepcopy(BASE);e['source']['line']=True
        with self.assertRaises(GateError):require_reviewed_event_evidence(self.draft,[e])
if __name__=='__main__':unittest.main()
