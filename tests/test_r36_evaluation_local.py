import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot import r36_evaluation_local as m
from worldroot.semantic_queue import seal

class LocalEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        raw=b"Historical fixture\nPerson A stayed home.\nReserved unrelated line\n"
        (self.root/"source.md").write_bytes(raw)
        self.man={"schema":m.ADAPTER,"sources":[{"path":"source.md","raw_sha256":hashlib.sha256(raw).hexdigest(),
                  "line_start":2,"line_end":2,"role":"CANON"}]}
        self.calls=[]
        self.a="a"*64; self.b="b"*64
        self.models=[{"name":"a","digest":self.a},{"name":"b","digest":self.b}]
        self.results=["PASS","PASS"]
        self.incomplete=False
        self.extra=False
        self.quote="Person A stayed home."
        self.change_pin=False
    def api(self,path,body=None):
        if path=="/api/tags":return {"models":self.models}
        self.calls.append(body)
        p=json.loads(body["messages"][1]["content"])
        outcome=self.results[len(self.calls)-1]
        result={"result":outcome,"severity":"major" if outcome=="FAIL" else "none",
                "confidence":0.9,"reason":"synthetic fixture","limitations":"test only",
                "proposed_fix":"revise" if outcome=="FAIL" else "",
                "candidate_quote":self.quote,"evidence":[{"source":next(iter(p["sources"])),"quote":"stayed home"}]}
        if self.extra:result["executor"]="forged"
        if self.change_pin:self.models[0]["digest"]="c"*64
        return {"done":not self.incomplete,"message":{"content":json.dumps(result)}}
    def packet(self):
        return m.source_packet(self.root,"canon","Person A stayed home.",self.man,seal(self.man))
    def run_pair(self,**kw):
        return m.run_pair(self.root,"canon","Person A stayed home.",self.man,seal(self.man),"a","b",api=self.api,**kw)
    def test_literal_span_only(self):
        p,proof=self.packet()
        self.assertEqual(list(p["sources"].values()),["Person A stayed home."])
        self.assertNotIn("source.md",str(p))
        self.assertEqual(proof["bindings"][0]["raw_sha256"],self.man["sources"][0]["raw_sha256"])
    def test_manifest_pin(self):
        with self.assertRaises(ValueError):m.source_packet(self.root,"canon","x",self.man,"0"*64)
    def test_raw_change(self):
        (self.root/"source.md").write_text("tampered")
        with self.assertRaises(ValueError):self.packet()
    def test_unapproved_role(self):
        self.man["sources"][0]["role"]="DRAFT"
        with self.assertRaises(ValueError):self.packet()
    def test_traversal(self):
        self.man["sources"][0]["path"]="../source.md"
        with self.assertRaises(ValueError):self.packet()
    def test_symlink(self):
        (self.root/"alias.md").symlink_to(self.root/"source.md")
        self.man["sources"][0]["path"]="alias.md"
        with self.assertRaises(ValueError):self.packet()
    def test_invalid_span(self):
        self.man["sources"][0]["line_end"]=999
        with self.assertRaises(ValueError):self.packet()
    def test_duplicate_span(self):
        self.man["sources"].append(dict(self.man["sources"][0]))
        with self.assertRaises(ValueError):self.packet()
    def test_budget(self):
        with self.assertRaises(ValueError):m.source_packet(self.root,"canon","x"*(m.MAX_CONTEXT_BYTES+1),self.man,seal(self.man))
    def test_distinct_calls(self):
        r=self.run_pair(generator_digest="c"*64)
        self.assertEqual(len(self.calls),2)
        self.assertEqual(self.calls[0]["messages"],self.calls[1]["messages"])
        self.assertEqual(r["result"],"PASS")
        self.assertEqual(r["transport"],"INJECTED_TEST_TRANSPORT")
        self.assertFalse(r["independence_verified"])
        self.assertFalse(r["semantic_certification"])
        self.assertTrue(r["production_hold"])
        self.assertNotEqual(r["first"]["receipt"]["session_id"],r["second"]["receipt"]["session_id"])
    def test_same_digest_rejected(self):
        self.models[1]["digest"]=self.a
        with self.assertRaises(ValueError):self.run_pair()
        self.assertEqual(len(self.calls),0)
    def test_generator_rejected(self):
        with self.assertRaises(ValueError):self.run_pair(generator_digest=self.a)
        self.assertEqual(len(self.calls),0)
    def test_disagreement(self):
        self.results=["PASS","FAIL"]
        self.assertEqual(self.run_pair()["result"],"INCONCLUSIVE")
    def test_incomplete(self):
        self.incomplete=True
        with self.assertRaises(ValueError):self.run_pair()
    def test_injected_metadata(self):
        self.extra=True
        with self.assertRaises(ValueError):self.run_pair()
    def test_candidate_quote(self):
        self.quote="invented"
        with self.assertRaises(ValueError):self.run_pair()
    def test_missing_decisive_quote(self):
        self.quote=""
        with self.assertRaises(ValueError):self.run_pair()
    def test_model_pin_changes(self):
        self.change_pin=True
        with self.assertRaises(ValueError):self.run_pair()
    def test_unavailable(self):
        def fail(*args):raise ConnectionError("offline")
        with self.assertRaises(ConnectionError):
            m.run_pair(self.root,"canon","Person A stayed home.",self.man,seal(self.man),"a","b",api=fail)
