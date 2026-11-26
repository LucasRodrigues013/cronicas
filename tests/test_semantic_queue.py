import unittest
from worldroot.semantic_queue import jobs,validate,reconcile

class QueueTest(unittest.TestCase):
    def test_group_and_validate(self):
        common={"source":"episode:x","line":1,"anchor_sha256":"abc","source_sha256":"src","source_status":"CLOSED","day":1,"anchor":"Varo chegou.","context":[{"line":1,"text":"Varo chegou."}]}
        rows=[{**common,"original_id":i,"entity_id":"varo","field":f} for i,f in [(1,"location"),(2,"role")]]
        js=list(jobs(rows));self.assertEqual(len(js),1)
        j=js[0];a={"job_id":j["job_id"],"executor":"model-A","model_revision":"v1","source_role":"NARRATED","role_reason":"test","decisions":[{"original_id":1,"entity_id":"varo","field":"location","verdict":"SUPPORTED","reason":"test","claim":"Chegou","evidence":"Varo chegou."},{"original_id":2,"entity_id":"varo","field":"role","verdict":"NOT_ATTRIBUTED","reason":"test"}]}
        self.assertEqual(validate(j,a),a)
        b={**a,"executor":"model-B"}
        self.assertTrue(all(not r["canon_promotion"] for r in reconcile(j,a,b)))
        with self.assertRaises(ValueError):reconcile(j,a,a)
        with self.assertRaises(ValueError):validate({**j,"source_status":"PENDING_NOT_CLOSED"},a)
        with self.assertRaises(ValueError):validate(j,{**a,"decisions":a["decisions"][:1]})
        self.assertEqual(len(list(jobs(rows,[1]))[0]["targets"]),1)
