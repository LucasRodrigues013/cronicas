import unittest
from worldroot.r36_contextual import expand,metrics
from worldroot.semantic_queue import seal
class ContextualTests(unittest.TestCase):
    def fixture(self):
        lines=["## scene","near","event evidence","near2","## next","unrelated"]
        sources={"episode:e":("s",lines,"CLOSED")}
        c={"episode_id":"e","sequence":1,"story_sha256":"s","events":[{"event_id":"ev","visibility":"PUBLICO","summary_candidato":"event","source":{"sha256":"s","line":3,"literal_anchor":"event evidence"}}]}
        rows=[{"source":"episode:e","source_sha256":"s","line":i,"original_id":i,"entity_id":"x","field":"role","anchor_sha256":"a"} for i in (2,3,4,6)]
        old=[{"event_id":"ev","episode":"e","source_sha256":"s","line":3,"visibility":"PUBLICO","candidate_ids":[3]}]
        return [c],rows,sources,old
    def test_context_boundaries_and_exact_preserved(self):
        p=expand(*self.fixture())[0]
        self.assertEqual([x["original_id"] for x in p["candidate_rows"]],[3,2,4])
        self.assertEqual(metrics([p])["exact_links_preserved"],1)
        self.assertEqual(p["packet_sha256"],seal({k:v for k,v in p.items() if k!="packet_sha256"}))
        self.assertFalse(p["canon_promotion"])
    def test_open_event_without_candidate(self):
        c,r,s,b=self.fixture();b[0]["candidate_ids"]=[]
        p=expand(c,[],s,b)[0]
        self.assertEqual(p["route"],"OPEN_ENTITY_REVIEW_REQUIRED")
    def test_context_only_not_certification(self):
        c,r,s,b=self.fixture();b[0]["candidate_ids"]=[]
        p=expand(c,r,s,b)[0]
        self.assertEqual(p["route"],"CONTEXT_REVIEW_REQUIRED");self.assertFalse(p["semantic_certification"])
    def test_invalid_anchor_and_changed_visibility(self):
        c,r,s,b=self.fixture();c[0]["events"][0]["source"]["literal_anchor"]="not present"
        with self.assertRaises(ValueError):expand(c,r,s,b)
        c,r,s,b=self.fixture();b[0]["visibility"]="BASTIDORES"
        with self.assertRaises(ValueError):expand(c,r,s,b)
    def test_draft_status_preserved(self):
        c,r,s,b=self.fixture();d,l,_=s["episode:e"];s["episode:e"]=(d,l,"PENDING_NOT_CLOSED")
        self.assertEqual(expand(c,r,s,b)[0]["source_status"],"PENDING_NOT_CLOSED")
