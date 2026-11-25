import unittest
from worldroot.memory_continuity import coverage,arc_review,digest
class TestMemoryContinuity(unittest.TestCase):
    def setUp(self):
        self.req=[{"id":str(i),"domain":"identity","critical":i==0} for i in range(20)]
        self.sources={"a":"literal evidence\n"}
        self.good={"source":"a","line_start":1,"line_end":1,"anchor_sha":digest(self.sources["a"]),"claim":"Reviewed claim","status":"REVIEWED_SUPPORTED"}
        self.arc={"options":[{"number":i,"track":"main" if i==2 else "secondary","arc_id":str(i),"title":"Title","promise":"Promise","reward":"Reward","risk":"Risk","next_link":"Link","unselected_progress":"Independent progress","guaranteed_success":False,"combines_all":False} for i in range(1,5)],"free_action":True,"author_choice_recorded":False}
    def test_threshold(self):
        self.assertEqual(coverage(self.req,{str(i):self.good for i in range(19)},self.sources)["status"],"REVIEWED_EVIDENCE_THRESHOLD_MET")
    def test_below_threshold(self):
        self.assertEqual(coverage(self.req,{str(i):self.good for i in range(18)},self.sources)["status"],"RECOVER_BEFORE_RELEASE")
    def test_critical_missing(self):
        self.assertEqual(coverage(self.req,{str(i):self.good for i in range(1,20)},self.sources)["status"],"RECOVER_BEFORE_RELEASE")
    def test_bad_hash(self):
        bad={**self.good,"anchor_sha":"bad"}
        self.assertEqual(coverage(self.req,{"0":bad},self.sources)["verified"],0)
    def test_candidate_not_reviewed(self):
        self.assertEqual(coverage(self.req,{"0":{**self.good,"status":"CANDIDATE"}},self.sources)["verified"],0)
    def test_unknown_review(self):
        with self.assertRaises(ValueError):coverage(self.req,{"unknown":self.good},self.sources)
    def test_empty_requirements(self):
        with self.assertRaises(ValueError):coverage([],{},self.sources)
    def test_parity_structure(self):
        self.assertEqual(arc_review(self.arc)["status"],"STRUCTURE_OK_EDITORIAL_PARITY_PENDING")
    def test_no_dominant_special(self):
        self.arc["options"][3]["combines_all"]=True
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
    def test_missing_risk(self):
        self.arc["options"][0]["risk"]=""
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
    def test_preserve_free_action(self):
        self.arc["free_action"]=False
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
    def test_not_four_main_routes(self):
        self.arc["options"][0]["track"]="main"
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
    def test_no_inferred_author_choice(self):
        self.arc["author_choice_recorded"]=True
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
    def test_no_duplicate_arcs(self):
        self.arc["options"][1]["arc_id"]="1"
        self.assertEqual(arc_review(self.arc)["status"],"REVIEW")
if __name__=="__main__":unittest.main()
