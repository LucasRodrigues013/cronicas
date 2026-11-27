import copy
import unittest
from worldroot import r36_chat_review as c
from worldroot import semantic_queue as q

class HistoricalChatTests(unittest.TestCase):
    def setUp(self):
        row={"original_id":42,"entity_id":"fixture","field":"role","source":"fixture","source_sha256":"a"*64,
             "source_status":"HISTORICAL_RESPONSE_UNREVIEWED","day":1,"line":1,"anchor":"A greeted B.",
             "anchor_sha256":"b"*64,"context":[{"line":1,"text":"A greeted B."}]}
        self.job=list(q.jobs([row]))[0]
    def pack(self,challenge="fixture-challenge-A"):
        return c.prepare_history([self.job],[self.job["job_id"]],"c"*64,challenge)
    def answer(self,p):
        return {"batch_id":p["batch_id"],"reviews":[{"job_id":self.job["job_id"],"source_role":"NARRATED",
            "role_reason":"Fixture","decisions":[{"original_id":42,"entity_id":"fixture","field":"role",
            "verdict":"UNKNOWN","reason":"Greeting does not prove a role","claim":"","evidence":"A greeted B.","current_state":False}]}]}
    def accept(self,p,r=None):
        return c.accept_history(p,p["batch_id"],r or self.answer(p),"a","same_conversation")
    def test_accept(self):
        p=self.pack();v=self.accept(p)
        self.assertFalse(v["semantic_certification"]);self.assertEqual(v["reviews"][0]["decisions"][0]["original_id"],42)
    def test_stale(self):
        p=self.pack();r=self.answer(p);r["batch_id"]="0"*64
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_retarget(self):
        p=self.pack();r=self.answer(p);r["reviews"][0]["decisions"][0]["entity_id"]="other"
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_claim_on_unknown(self):
        p=self.pack();r=self.answer(p);r["reviews"][0]["decisions"][0]["claim"]="invented"
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_fake_evidence(self):
        p=self.pack();r=self.answer(p);r["reviews"][0]["decisions"][0]["evidence"]="invented"
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_draft_support(self):
        j=self.job;j["source_status"]="PENDING_NOT_CLOSED";j["job_id"]=q.seal({k:v for k,v in j.items() if k!="job_id"})
        p=self.pack();r=self.answer(p);r["reviews"][0]["decisions"][0].update(verdict="SUPPORTED",claim="greeting")
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_current_state(self):
        p=self.pack();r=self.answer(p);r["reviews"][0]["decisions"][0]["current_state"]=True
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_tampered_job(self):
        self.job["anchor"]="changed"
        with self.assertRaises(ValueError):self.pack()
    def test_duplicate_job(self):
        with self.assertRaises(ValueError):c.prepare_history([self.job,self.job],[self.job["job_id"]]*2,"c"*64,"fixture-challenge")
    def test_pair(self):
        a,b=self.pack(),self.pack("fixture-challenge-B")
        r=c.reconcile_history(a,a["batch_id"],self.answer(a),"a","separate_conversation_declared",b,b["batch_id"],self.answer(b),"b","separate_conversation_declared","g")
        self.assertEqual(r["rows"][0]["route"],"AGREEMENT_CANDIDATE")
        self.assertTrue(r["requires_human_adjudication"]);self.assertFalse(r["model_independence_verified"])
    def test_same_session_block(self):
        a,b=self.pack(),self.pack("fixture-challenge-B")
        with self.assertRaises(ValueError):c.reconcile_history(a,a["batch_id"],self.answer(a),"a","separate_conversation_declared",b,b["batch_id"],self.answer(b),"a","separate_conversation_declared","g")
    def test_missing_review(self):
        p=self.pack();r=self.answer(p);r["reviews"]=[]
        with self.assertRaises(ValueError):self.accept(p,r)
