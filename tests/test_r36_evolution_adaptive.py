import copy
import hashlib
import unittest
from worldroot import r36_adaptive as a
from worldroot import r36_experiment as x
from worldroot.r36_trust import authenticate

K=b"a"*32; A=b"b"*32
def obs(raw=b"fixture",**kw):
    m={"kind":"narrative","origin":"synthetic","scope":"global","target":"style","context":"GLOBAL","entity":"generic",
       "direction":"improve","severity":"major","confidence":.8,"observed_on":"2026-01-01","expires_on":None,
       "engine_revision":"a"*64,"source_sha256":hashlib.sha256(raw).hexdigest(),"source_start":1,"source_end":1,
       "quote":raw.decode(),"episode":"E1"}
    m.update(kw);return a.observation(m,raw,K)
def propose(items=None):
    return a.proposal(items or [obs()],K,"2026-01-02",0,"a"*64,"b"*64,"fixture hypothesis")
def advance(p,states):
    h=[]
    for s in states:h.append(a.event(p,h,s,"c"*64,"fixture",K))
    return h

class FeedbackTests(unittest.TestCase):
    def test_literal(self):
        with self.assertRaises(ValueError):obs(quote="fake")
    def test_source_digest(self):
        with self.assertRaises(ValueError):obs(source_sha256="0"*64)
    def test_reserved(self):
        for origin in ("reserved","validation"):
            with self.assertRaises(ValueError):obs(origin=origin)
    def test_scope(self):
        with self.assertRaises(ValueError):obs(scope="point")
    def test_duplicate(self):
        d=a.summarize([obs(),obs() ],K,"2026-01-02")
        self.assertEqual(d["duplicates"],1);self.assertEqual(d["groups"][0]["recurrence_lower_bound"],1)
    def test_independent_recurrence(self):
        d=a.summarize([obs(),obs(b"other",episode="E2")],K,"2026-01-02")
        self.assertEqual(d["groups"][0]["recurrence_lower_bound"],2)
    def test_shared_source(self):
        d=a.summarize([obs(),obs(episode="E2")],K,"2026-01-02")
        self.assertEqual(d["groups"][0]["recurrence_lower_bound"],1)
    def test_praise_conflict(self):
        d=a.summarize([obs(),obs(direction="preserve")],K,"2026-01-02")["groups"][0]
        self.assertTrue(d["conflict"]);self.assertEqual(len(d["preserve_ids"]),1)
    def test_expiry(self):
        self.assertEqual(a.summarize([obs(expires_on="2026-01-01")],K,"2026-01-02")["expired_or_future"],1)
    def test_synthetic_separate(self):
        d=a.summarize([obs(),obs(origin="author_feedback")],K,"2026-01-02")
        self.assertEqual(len(d["groups"]),2)
    def test_tamper(self):
        p=obs();p["payload"]["meta"]["direction"]="preserve"
        with self.assertRaises(ValueError):a.summarize([p],K,"2026-01-02")
    def test_skip(self):
        with self.assertRaises(ValueError):a.event(propose(),[],"EVALUATED","c"*64,"fixture",K)
    def test_synthetic_approval(self):
        p=propose();h=advance(p,["PROPOSED","EXPERIMENTED","EVALUATED"])
        with self.assertRaises(ValueError):a.event(p,h,"APPROVED","c"*64,"fixture",K,approval_key=A)
    def test_separate_approval_and_rollback(self):
        p=propose([obs(origin="author_feedback")]);h=advance(p,["PROPOSED","EXPERIMENTED","EVALUATED"])
        for state in ("APPROVED","STAGED"):
            payload={"proposal_id":p["payload"]["proposal_id"],"state":state,"policy_sha":"b"*64,"evidence_sha":"c"*64}
            h.append(a.event(p,h,state,"c"*64,"fixture",K,authenticate("feedback-approval",payload,A),A))
        h.append(a.event(p,h,"ROLLED_BACK","c"*64,"fixture",K,approval_key=A))
        self.assertEqual(a.staging_status(p,h,K,A)["state"],"ROLLED_BACK")
        self.assertFalse(a.staging_status(p,h,K,A)["incorporation_executed"])
    def test_chain_reordering(self):
        p=propose();h=advance(p,["PROPOSED","EXPERIMENTED"])
        with self.assertRaises(ValueError):a.replay(p,h[::-1],K)
    def test_proposal_tamper(self):
        p=propose();p["payload"]["group"]["synthetic"]=False
        with self.assertRaises(ValueError):a.replay(p,[],K)

def experiment():
    common={k:"d"*64 for k in x.PINS-{"case_ids","split"}};common.update(case_ids=["one"],split="reserved")
    return x.freeze("a"*64,"b"*64,common,{"setting":"fixture"})
def metric(**kw):
    m={k:1 for k in x.FIELDS-{"case_id","input_sha","outcome"}};m.update(case_id="one",input_sha="c"*64,outcome="DECISIVE",critical=0)
    m.update(kw);return m
class ExperimentTests(unittest.TestCase):
    def test_paired(self):
        d=x.paired_metrics(experiment(),[metric(latency_ns=100)],[metric(latency_ns=75,critical=1)])
        self.assertEqual(d["latency_reduction"],.25);self.assertEqual(d["critical_regression_cases"],1)
        self.assertFalse(d["measurement_attested"]);self.assertFalse(d["feedback_eligible"])
    def test_input_mismatch(self):
        with self.assertRaises(ValueError):x.paired_metrics(experiment(),[metric()],[metric(input_sha="e"*64)])
    def test_missing(self):
        with self.assertRaises(ValueError):x.paired_metrics(experiment(),[metric()],[])
    def test_abstention(self):
        with self.assertRaises(ValueError):x.paired_metrics(experiment(),[metric()],[metric(outcome="ABSTAIN")])
    def test_blind(self):
        p,q,d=x.blind_experiment(experiment(),"one","a b","c","literary")
        self.assertEqual(q["candidates"],p.packet["candidates"][::-1]);self.assertEqual(d["length_ratio"],2)
    def test_changed_freeze(self):
        e=experiment();e["common"]["split"]="development"
        with self.assertRaises(ValueError):x.paired_metrics(e,[metric()],[metric()])
