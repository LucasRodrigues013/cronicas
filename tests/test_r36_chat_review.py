import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot import r36_chat_review as c
from worldroot.r36_evaluation_local import ADAPTER
from worldroot.semantic_queue import seal

class ChatReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source="The bridge was closed at sunrise. It reopened at dusk."
        self.candidate="The bridge reopened at dusk."
        self.judge="canon"
        self.make_source()
    def make_source(self):
        raw=self.source.encode();(self.root/"source.txt").write_bytes(raw)
        self.man={"schema":ADAPTER,"sources":[{"path":"source.txt","raw_sha256":hashlib.sha256(raw).hexdigest(),"line_start":1,"line_end":1,"role":"CANON"}]}
    def package(self,challenge="public-fixture-challenge-A"):
        return c.prepare(self.root,self.judge,self.candidate,self.man,seal(self.man),"a"*64,challenge)
    def answer(self,p):
        return {"exchange_id":p["exchange_id"],"result":"PASS","severity":"none","confidence":.9,
                "reason":"Matches literal source","limitations":"Fixture only","evidence":[{"source":next(iter(p["packet"]["sources"])),"quote":"It reopened at dusk."}],
                "proposed_fix":"","candidate_quote":self.candidate}
    def accept(self,p,response=None):
        return c.accept(p,p["exchange_id"],response or self.answer(p),"session-a","same_conversation")
    def test_accept_not_attestation(self):
        p=self.package();v=self.accept(p)
        self.assertFalse(v["model_independence_verified"]);self.assertFalse(v["semantic_certification"])
    def test_manifest(self):
        (self.root/"source.txt").write_text("changed")
        with self.assertRaises(ValueError):self.package()
    def test_no_path_or_gold(self):
        p=self.package();self.assertNotIn("source.txt",json.dumps(p));self.assertNotIn("expected",p)
    def test_tamper_reseal(self):
        p=self.package();old=p["exchange_id"];p["challenge"]="modified-challenge"
        p["exchange_id"]=seal({k:v for k,v in p.items() if k!="exchange_id"})
        with self.assertRaises(ValueError):c.validate_package(p,old)
    def test_wrong_quote(self):
        p=self.package();r=self.answer(p);r["evidence"][0]["quote"]="invented"
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_candidate_quote(self):
        p=self.package();r=self.answer(p);r["candidate_quote"]=""
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_stale_response(self):
        p=self.package();r=self.answer(p);r["exchange_id"]="0"*64
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_extra_fields(self):
        p=self.package();r=self.answer(p);r["independence_verified"]=True
        with self.assertRaises(ValueError):self.accept(p,r)
    def test_duplicate_json(self):
        p=self.package();r=json.dumps(self.answer(p)).replace('"result": "PASS"','"result": "PASS", "result": "FAIL"')
        with self.assertRaises(ValueError):self.accept(p,r)
    def pair(self,session_b="session-b",profile="separate_conversation_declared",disagree=False):
        a,b=self.package(),self.package("public-fixture-challenge-B")
        r=self.answer(b)
        if disagree:r.update(result="ABSTAIN",confidence=.5)
        return c.reconcile(a,a["exchange_id"],self.answer(a),"session-a",b,b["exchange_id"],r,session_b,"generator",profile,profile)
    def test_pair_declared_only(self):
        v=self.pair();self.assertTrue(v["separate_sessions_declared"]);self.assertFalse(v["model_independence_verified"])
    def test_same_session(self):
        v=self.pair(session_b="session-a");self.assertFalse(v["separate_sessions_declared"]);self.assertTrue(v["requires_human_adjudication"])
    def test_same_conversation(self):
        self.assertFalse(self.pair(profile="same_conversation")["separate_sessions_declared"])
    def test_disagreement(self):
        self.assertEqual(self.pair(disagree=True)["result"],"INCONCLUSIVE")
    def test_replay(self):
        a=self.package()
        with self.assertRaises(ValueError):c.reconcile(a,a["exchange_id"],self.answer(a),"a",a,a["exchange_id"],self.answer(a),"b","g","separate_conversation_declared","separate_conversation_declared")
    def test_public_actual_chat_review_smoke(self):
        path=Path(__file__).resolve().parents[1]/"audit"/"e7-chat-smoke.json"
        fixture=json.loads(path.read_text());self.assertEqual(fixture["review_origin"],"ACTUAL_CHATGPT_CURRENT_CONVERSATION_NON_BLIND")
        pairs=[]
        for case in fixture["cases"]:
            self.source,self.candidate,self.judge=case["source"],case["candidate"],case["judge"];self.make_source()
            p=self.package(case["id"]+"-public-challenge");r=dict(case["response"])
            q=r.pop("evidence_quote");r.update(exchange_id=p["exchange_id"],evidence=[{"source":next(iter(p["packet"]["sources"])),"quote":q}])
            v=self.accept(p,r);pairs.append({"expected":case["expected"],"observed":v["receipt"]["result"]})
        result=c.score_public_smoke(pairs);self.assertEqual(result["verdict_match_count"],3)
        self.assertEqual(result["decisive_case_metrics"]["accuracy_all"],1)
        self.assertFalse(result["semantic_certification"])
