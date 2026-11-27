import unittest
from worldroot.omega_semantic_receipt import check_records,check_coverage,check_links,anchor,roles_for

class OmegaSemanticReceiptTests(unittest.TestCase):
    def setUp(self):
        self.body="## Prompt:\nchoice\n## Response:\nVaro returns\n"
        self.lines=self.body.split("\n");self.roles=roles_for(self.body)
        self.rec=dict(id="r",type="event",axes=[3],entities=["varo"],promotion=False,visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",evidence=dict(source="fixture",source_sha256_manifest="a",role="Response",line_start=4,line_end=4,span_sha256_utf8=anchor(self.lines,4,4)))
    def check(self,recs=None):return check_records(recs or [self.rec],self.lines,self.roles,"fixture","a",[3,4])
    def coverage(self):return [dict(start=3,end=4,role="Response",span_sha256_utf8=anchor(self.lines,3,4),record_ids=["r"])]
    def test_good(self):
        self.assertEqual(self.check(),{"r"})
        self.assertEqual(check_coverage(self.coverage(),[self.rec],self.lines,self.roles,[3,4]),1)
    def test_changed_anchor(self):
        self.lines[3]="changed"
        with self.assertRaises(ValueError):self.check()
    def test_wrong_role(self):
        self.rec["evidence"]["role"]="Prompt"
        with self.assertRaises(ValueError):self.check()
    def test_no_promotion(self):
        self.rec["promotion"]=True
        with self.assertRaises(ValueError):self.check()
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):self.check([self.rec,self.rec])
    def test_gap(self):
        with self.assertRaises(ValueError):check_coverage(self.coverage(),[self.rec],self.lines,self.roles,[2,4])
    def test_unlisted_record(self):
        rows=self.coverage();rows[0]["record_ids"]=[]
        with self.assertRaises(ValueError):check_coverage(rows,[self.rec],self.lines,self.roles,[3,4])
    def test_reader_leak(self):
        self.rec["type"]="reader-only"
        with self.assertRaises(ValueError):self.check()
    def test_unknown_registry_id(self):
        receipt=dict(records=[self.rec],entity_links=[dict(label="varo",registry_id="fake",disposition="EXISTING_ID_CANDIDATE_LINK")],reconciliations=[],causal_links=[],duplicate_review_groups=[])
        with self.assertRaises(ValueError):check_links(receipt,{"varo"})
    def test_unresolved_registry_id_permitted(self):
        receipt=dict(records=[self.rec],entity_links=[dict(label="varo",registry_id=None,disposition="UNRESOLVED_LOCAL_LABEL")],reconciliations=[],causal_links=[],duplicate_review_groups=[])
        self.assertEqual(check_links(receipt,{"varo"})["unresolved"],1)
