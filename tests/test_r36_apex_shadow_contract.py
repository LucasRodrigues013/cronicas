import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from worldroot.r36_history_advisory import check_binding,validate_shadow_lanes,seal
from worldroot.git_cycle import sha,canonical
from worldroot.live_codex import shadow_field_review
from worldroot.r36_adaptive import compare_experiment

class ShadowContract(unittest.TestCase):
    def packet(self):
        req={"head":{"sequence":50},"requirements":[{"id":"q"}]}
        group={"group_id":"g","source":"ep","source_sha256":"sha","group_interval":[1,1],"group_anchor":"hash","line":1,"line_sha256":"hash","signals":[],"identity_status":"CANDIDATE_ONLY","knowledge_injection":False}
        public={"event_id":"e","episode":"ep","sequence":1,"day":1,"clock":"08h00","source_sha256":"sha","line":2,"anchor_sha256":"hash","signals":[],"scope":"PUBLIC_CANONICAL_LITERAL_ANCHOR_DIRECTOR_ONLY","identity_status":"UNRESOLVED_QUERY_MATCH","knowledge_injection":False,"semantic_certification":False}
        a={"shadow_mode":"public_anchor","request_sha256":sha(canonical(req)),"head_sha256":sha(canonical(req["head"])),"knowledge_injection":False,"canon_changed":False,"semantic_certification":False,"locator_count":2,"requirements":[{"requirement_id":"q","locators":[group],"public_anchor_locators":[public]}]}
        a["advisory_sha256"]=seal(a);return req,a
    def reseal(self,a):
        a.pop("advisory_sha256");a["advisory_sha256"]=seal(a)
    def test_shadow_is_not_production(self):
        r,a=self.packet()
        with self.assertRaises(ValueError):check_binding(r,a)
        self.assertEqual(validate_shadow_lanes(r,a)["locators"],2)
    def test_reject_leak_and_mixed_shapes(self):
        r,a=self.packet();p=a["requirements"][0]["public_anchor_locators"][0];p["anchor"]="secret";self.reseal(a)
        with self.assertRaises(ValueError):validate_shadow_lanes(r,a)
        del p["anchor"];a["requirements"][0]["locators"].append(p);self.reseal(a)
        with self.assertRaises(ValueError):validate_shadow_lanes(r,a)
    def test_duplicate_line(self):
        r,a=self.packet();a["requirements"][0]["public_anchor_locators"][0]["line"]=1;self.reseal(a)
        with self.assertRaises(ValueError):validate_shadow_lanes(r,a)
    def test_bounded_field_shadow_registry_only(self):
        h={"sequence":50};req={"project":"CRONICAS_DE_UM_NOVO_MUNDO","head":h}
        record={"id":"person","domains":["Personagens"],"natural_profile":{"fields":{"hair":{"status":"RECUPERADO","value":"dark"},"goals":{"status":"SEGREDO","scope":"AUTHOR_ONLY","value":"secret"}}}}
        with tempfile.TemporaryDirectory() as t:
            with patch("worldroot.git_cycle.load",return_value=h),patch("worldroot.git_cycle.verify_db"),patch("worldroot.live_codex.load_registry",return_value=({},"pin")),patch("worldroot.live_codex.all_records",return_value=[record]):
                out=shadow_field_review(t,req,["person"]);self.assertFalse(out["graph_used"])
                self.assertNotIn("secret",json.dumps(out));self.assertNotIn("dark",json.dumps(out));self.assertNotIn("hair",json.dumps(out))
                self.assertEqual(out["entities"][0]["field_status_counts"]["EDITORIAL_REFERENCE_NOT_CURRENT_STATE"],1)
                for ids in (["missing"],["person","person"],[]):
                    with self.assertRaises(ValueError):shadow_field_review(t,req,ids)
    def test_feedback_compare_and_preserve(self):
        rows=[{"case_id":"a","source_sha256":"a"*64,"direction":"avoid","baseline":"FAIL","candidate":"PASS"},{"case_id":"b","source_sha256":"b"*64,"direction":"preserve","baseline":"PASS","candidate":"UNKNOWN"}]
        out=compare_experiment(rows);self.assertEqual(out["paired_failure_reduction"],1)
        self.assertEqual(out["counts"]["preserve"]["lost"],1);self.assertFalse(out["longitudinal_recurrence_proven"])
        with self.assertRaises(ValueError):compare_experiment(rows+rows[:1])
    def test_no_baseline_failure_no_claim(self):
        row={"case_id":"a","source_sha256":"a"*64,"direction":"avoid","baseline":"PASS","candidate":"UNKNOWN"}
        self.assertIsNone(compare_experiment([row])["paired_failure_reduction"])
