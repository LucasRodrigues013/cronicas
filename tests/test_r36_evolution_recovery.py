import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from worldroot import r36_recovery as r
from worldroot import r36_trust as t
from worldroot import r36_evaluation_local as a
from worldroot import r36_evaluation as ev
from worldroot.r36_partition import feasibility
from worldroot.r36_human_review import record
from worldroot.r36_benchmark import TARGETS
from worldroot.semantic_queue import seal

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        raw=b"Fixture: A stayed home.\n";(self.root/"source").write_bytes(raw)
        self.man={"schema":a.ADAPTER,"sources":[{"path":"source","raw_sha256":hashlib.sha256(raw).hexdigest(),"line_start":1,"line_end":1,"role":"CANON"}]}
        self.scope={"authority_revision":"test","engine_revision":"fixture"}
        self.ka=b"a"*32;self.kb=b"b"*32
        self.auth=t.authorize_manifest(self.man,self.scope,self.ka)
        self.calls=[];self.fail_b=False
        self.pins=["a"*64,"b"*64]
    def api(self,path,body=None):
        if path=="/api/tags":return {"models":[{"name":"a","digest":self.pins[0]},{"name":"b","digest":self.pins[1]}]}
        self.calls.append(body["model"])
        if body["model"]=="b" and self.fail_b:raise TimeoutError("fixture")
        p=json.loads(body["messages"][1]["content"])
        raw={"result":"PASS","severity":"none","confidence":.8,"reason":"fixture","limitations":"synthetic",
             "evidence":[{"source":next(iter(p["sources"])),"quote":"stayed home"}],"proposed_fix":"","candidate_quote":"A stayed home."}
        return {"done":True,"message":{"content":json.dumps(raw)}}
    def invoke(self,**kw):
        params=dict(root=self.root,out=self.root/"out",judge="canon",candidate="A stayed home.",authority=self.auth,
                    scope=self.scope,authority_key=self.ka,receipt_key=self.kb,model_a="a",model_b="b",
                    pin_a="a"*64,pin_b="b"*64,run_nonce="synthetic-test-nonce",api=self.api)
        params.update(kw);return r.run(**params)
    def test_manifest_tamper(self):
        x=copy.deepcopy(self.auth);x["payload"]["manifest"]["sources"][0]["role"]="AUTHOR_POLICY"
        with self.assertRaises(ValueError):self.invoke(authority=x)
    def test_scope_mismatch(self):
        with self.assertRaises(ValueError):self.invoke(scope={"authority_revision":"different","engine_revision":"fixture"})
    def test_key_separation(self):
        with self.assertRaises(ValueError):self.invoke(receipt_key=self.ka)
    def test_domain_separation(self):
        with self.assertRaises(ValueError):t.verify(self.auth,"attempt",self.ka)
    def test_resume_after_b_failure(self):
        self.fail_b=True
        self.assertEqual(self.invoke()["status"],"REVIEW_FAILED")
        self.fail_b=False
        v=self.invoke();self.assertEqual(v["status"],"LOCAL_RECEIPTS_AUTHENTICATED")
        self.assertEqual(self.calls,["a","b","b"])
        self.assertFalse(v["independence_verified"])
        self.assertEqual(self.invoke()["new_review_attempts"],0)
        self.assertEqual(self.calls,["a","b","b"])
    def test_attempt_limit(self):
        self.fail_b=True
        self.invoke();self.invoke()
        self.assertEqual(self.invoke()["status"],"ATTEMPT_LIMIT")
        self.assertEqual(self.calls,["a","b","b"])
    def test_nonce_replay(self):
        self.invoke()
        with self.assertRaises(ValueError):self.invoke(run_nonce="new-synthetic-nonce")
    def test_changed_packet(self):
        self.invoke()
        with self.assertRaises(ValueError):self.invoke(candidate="Changed.")
    def test_tampered_receipt(self):
        self.invoke();p=self.root/"out"/"local-A.json";x=json.loads(p.read_text())
        x["payload"]["review"]["receipt"]["confidence"]=.99;p.write_text(json.dumps(x))
        with self.assertRaises(ValueError):self.invoke()
    def test_cross_slot_replay(self):
        self.invoke();p=self.root/"out"/"local-B.json";p.write_bytes((self.root/"out"/"local-A.json").read_bytes())
        with self.assertRaises(ValueError):self.invoke()
    def test_pin_change(self):
        self.pins[0]="c"*64
        with self.assertRaises(ValueError):self.invoke()
        self.assertEqual(self.calls,[])
    def test_lock(self):
        out=r.private_dir(self.root/"out");(out/"active.lock").write_text("test")
        with self.assertRaises(FileExistsError):self.invoke()
    def test_private_permissions(self):
        out=self.root/"out";out.mkdir(mode=0o755)
        with self.assertRaises(ValueError):self.invoke()
    def test_symlink_record(self):
        self.invoke();p=self.root/"out"/"local-A.json";p.unlink();p.symlink_to(self.root/"source")
        with self.assertRaises(ValueError):self.invoke()
    def test_in_git(self):
        (self.root/".git").mkdir()
        with self.assertRaises(ValueError):self.invoke()
    def test_no_model_self_review(self):
        with self.assertRaises(ValueError):self.invoke(generator_digest="a"*64)

def rows60():
    out=[];i=0
    for category,n in TARGETS.items():
        for _ in range(n):
            i+=1;out.append({"id":str(i),"category":category,"family":"f"+str(i),"episodes":["e"+str(i)],
                             "entities":["x"+str(i)],"source_pins":[format(i,"064x")],"severity":"major"})
    return out

class PartitionTests(unittest.TestCase):
    def test_feasible(self):
        self.assertTrue(feasibility(rows60())["exact_60_feasible"])
    def test_transitive(self):
        x=rows60()[:3];x[1]["family"]=x[0]["family"];x[2]["entities"]=x[1]["entities"]
        self.assertEqual(feasibility(x)["component_sizes"],[3])
    def test_giant_component(self):
        x=rows60()
        for v in x:v["entities"]=["shared"]
        self.assertFalse(feasibility(x)["capacity_feasible"])
    def test_partial(self):
        self.assertFalse(feasibility(rows60()[:3])["exact_60_feasible"])
    def test_order_invariant(self):
        x=rows60();x[1]["family"]=x[0]["family"]
        self.assertEqual(feasibility(x),feasibility(x[::-1]))
    def test_secret_field(self):
        x=rows60();x[0]["gold"]="secret"
        with self.assertRaises(ValueError):feasibility(x)

class HumanTests(unittest.TestCase):
    def setUp(self):
        self.p=ev.blind_pair("alpha text","beta text","literary");self.q=ev.reverse_pair(self.p.packet)
        self.id=next(iter(self.p.mapping))
        self.a={"packet_id":self.p.packet["packet_id"],"winner":self.id,"session_id":"a","reason":"test"}
        self.b={"packet_id":self.q["packet_id"],"winner":self.id,"session_id":"b","reason":"test"}
        self.h={"packet_id":self.p.packet["packet_id"],"winner":self.id,"reviewer":"fixture","reason":"test",
                "limitations":"synthetic","evidence":[{"candidate_id":self.id,"quote":"alpha"}]}
    def test_auth_not_identity(self):
        x=record(self.p,self.q,self.a,self.b,self.h,b"c"*32)
        v=t.verify(x,"human-review",b"c"*32)
        self.assertTrue(v["agreement"]);self.assertFalse(v["human_identity_verified"])
    def test_fake_quote(self):
        self.h["evidence"][0]["quote"]="invented"
        with self.assertRaises(ValueError):record(self.p,self.q,self.a,self.b,self.h,b"c"*32)
    def test_abstention(self):
        self.h.update(winner="ABSTAIN",evidence=[])
        v=record(self.p,self.q,self.a,self.b,self.h,b"c"*32)["payload"]
        self.assertFalse(v["agreement"])
