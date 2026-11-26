import unittest
from worldroot.r36_reconciliation import verify_rows,reconcile_events,prior_review,sha
class ReconciliationTests(unittest.TestCase):
    def row(self):
        return {"original_id":1,"source":"episode:e","source_sha256":"digest","source_status":"CLOSED","line":1,"anchor":"Lucas observou.","anchor_sha256":sha("Lucas observou."),"context":[{"line":1,"text":"Lucas observou."}],"entity_id":"lucas","field":"behavior"}
    def closure(self):
        return {"sequence":1,"episode_id":"e","story_sha256":"digest","events":[{"event_id":"ev","visibility":"PUBLICO","source":{"sha256":"digest","line":1,"literal_anchor":"Lucas observou"}}]}
    def test_exact_original(self):
        r=self.row();self.assertEqual(verify_rows([r],{"episode:e":("digest",["Lucas observou."],"CLOSED")},1),[r])
    def test_context_tamper(self):
        r=self.row();r["context"][0]["text"]="inventado"
        with self.assertRaises(ValueError):verify_rows([r],{"episode:e":("digest",["Lucas observou."],"CLOSED")},1)
    def test_duplicate_original(self):
        r=self.row()
        with self.assertRaises(ValueError):verify_rows([r,r],{},2)
    def test_shared_line_candidate_only(self):
        result=reconcile_events([self.closure()],[self.row()])[0]
        self.assertEqual(result["candidate_ids"],[1]);self.assertFalse(result["canon_promotion"]);self.assertFalse(result["semantic_certified"])
    def test_no_false_match(self):
        r=self.row();r["source_sha256"]="other"
        self.assertEqual(reconcile_events([self.closure()],[r])[0]["candidate_ids"],[])
    def test_prior_review_binding(self):
        r=self.row();self.assertEqual(prior_review([r],{"rows":[{**r,"canon_promotion":False}]}),{1})
        with self.assertRaises(ValueError):prior_review([r],{"rows":[{**r,"entity_id":"other","canon_promotion":False}]})
