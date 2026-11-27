import unittest
from worldroot.r36_calibration import calibration,context,comparison_context
from worldroot.r36_benchmark import *
from worldroot.r36_evaluation import RUBRICS
from worldroot.r36_evaluation_local import _unique_json

def case(i,cat="memory",split="development"):
    return {"id":str(i),"category":cat,"family":"f"+str(i),"episodes":["e"+str(i)],
            "entities":["n"+str(i)],"source_pins":[format(i,"064x")],
            "split":split,"severity":"major"}

class CalibrationTests(unittest.TestCase):
    def test_all_twelve(self):
        for j in RUBRICS:
            c=calibration(j)
            self.assertFalse(c["human_calibrated"])
            self.assertEqual(set(c["outcomes"]),{"PASS","FAIL","ABSTAIN","INCONCLUSIVE"})
    def test_role_binding(self):
        p=context("canon",[{"excerpt_id":"a","role":"CANON"}])
        q=context("canon",[{"excerpt_id":"a","role":"AUTHOR_POLICY"}])
        self.assertNotEqual(p["calibration_sha256"],q["calibration_sha256"])
    def test_conflict(self):
        with self.assertRaises(ValueError):context("canon",[{"excerpt_id":"a","role":"CANON"},{"excerpt_id":"a","role":"APPROVED_REFERENCE"}])
    def test_length_is_advisory(self):
        self.assertEqual(comparison_context("a b","a")["length_ratio"],2)
        self.assertFalse(comparison_context("a b","a")["automatic_length_penalty"])
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):_unique_json([("result","PASS"),("result","FAIL")])

class BenchmarkTests(unittest.TestCase):
    def test_exact_60(self):
        rows=[];i=0
        for cat,n in TARGETS.items():
            for _ in range(n):
                i+=1;rows.append(case(i,cat,"development" if i<=36 else "validation" if i<=48 else "reserved"))
        self.assertEqual(validate_inventory(rows)["cases"],60)
        self.assertEqual(validate_inventory(rows)["inventory_sha256"],validate_inventory(rows[::-1])["inventory_sha256"])
    def test_partial(self):
        self.assertTrue(validate_inventory([case(1)],exact=False)["structural_only"])
        with self.assertRaises(ValueError):validate_inventory([case(1)])
    def test_group_leakage(self):
        for field in ("family","episodes","entities","source_pins"):
            a,b=case(1),case(2,split="reserved");b[field]=a[field]
            with self.subTest(field=field),self.assertRaises(ValueError):validate_inventory([a,b],exact=False)
    def test_duplicate(self):
        with self.assertRaises(ValueError):validate_inventory([case(1),case(1)],exact=False)
    def test_gold_rejected(self):
        a=case(1);a["answer"]="secret"
        with self.assertRaises(ValueError):validate_inventory([a],exact=False)
        with self.assertRaises(ValueError):generation_case(a,"question")
    def test_invalid_pin(self):
        a=case(1);a["source_pins"]=["bad"]
        with self.assertRaises(ValueError):validate_inventory([a],exact=False)
    def test_projection(self):
        self.assertEqual(generation_case(case(1),"question"),{"case_id":"1","prompt":"question"})
    def test_reserved_block(self):
        with self.assertRaises(ValueError):generation_case(case(1,split="reserved"),"question")
    def test_metrics_abstention(self):
        d=factual_metrics(["CORRECT","INCORRECT","ABSTAIN","INCONCLUSIVE"])
        self.assertEqual(d["accuracy_all"],.25)
        self.assertEqual(d["accuracy_decisive"],.5)
        self.assertEqual(d["coverage"],.5)
    def test_no_decisive(self):
        self.assertIsNone(factual_metrics(["ABSTAIN"])["accuracy_decisive"])
