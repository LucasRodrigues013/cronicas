from __future__ import annotations

import copy
import unittest

from worldroot.editorial_guard import (
    load_policy, validate_policy, compact_brief,
    quick_preflight, verify_historical_staging,
)


class EditorialMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_policy_is_versioned_scoped_and_evidence_linked(self):
        v = validate_policy(self.policy)
        self.assertEqual(v["version"], 7)
        self.assertGreaterEqual(v["rule_count"], 15)
        self.assertEqual(self.policy["project"], "CRONICAS_DE_UM_NOVO_MUNDO")
        self.assertIn("P01", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P19", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P23", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P24", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P25", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P26", {r["id"] for r in self.policy["rules"]})
        self.assertIn("P27", {r["id"] for r in self.policy["rules"]})
        for rid in ("P28", "P29", "P30", "P31", "P32", "P33", "P34"):
            self.assertIn(rid, {r["id"] for r in self.policy["rules"]})

    def test_brief_prioritizes_lived_story_over_task_reporting(self):
        result = compact_brief(self.policy, scene_tags=("CENA",), max_chars=900)
        self.assertTrue({"P28", "P29", "P30"}.issubset(result["selected_rule_ids"]))
        self.assertIn("VIDA P28/P29/P30", result["text"])
        self.assertLessEqual(len(result["text"]), 1000)

    def test_duplicate_or_unverified_feedback_is_rejected(self):
        p = copy.deepcopy(self.policy)
        p["rules"][1]["id"] = p["rules"][0]["id"]
        with self.assertRaises(ValueError):
            validate_policy(p)
        p = copy.deepcopy(self.policy)
        p["rules"][0]["evidence"] = ["NONEXISTENT"]
        with self.assertRaises(ValueError):
            validate_policy(p)

    def test_other_universe_is_rejected(self):
        p = copy.deepcopy(self.policy)
        p["project"] = "EIDORYN"
        with self.assertRaises(ValueError):
            validate_policy(p)

    def test_brief_is_small_and_contextual(self):
        result = compact_brief(self.policy, scene_tags=("MIREN", "ROMANCE"), max_chars=1750)
        self.assertLessEqual(len(result["text"]), 1900)
        self.assertIn("P06", result["selected_rule_ids"])
        self.assertEqual(result["policy_version"], 7)
        self.assertNotIn("SOURCE_COUNT", result["text"])

    def test_images_are_structurally_rejected(self):
        for body in ("Uma cena.\n![lucas](abc.png)", "Texto <img src='foto'>", "data:image/png;base64,a"):
            out = quick_preflight(body, policy=self.policy)
            self.assertEqual(out["status"], "BLOQUEADO")
            self.assertFalse(out["semantic_certification"])

    def test_short_scene_warns_but_does_not_block(self):
        out = quick_preflight("LUCAS — Olá.\nMIREN — Venha.", policy=self.policy)
        self.assertEqual(out["status"], "REVISAR")
        self.assertEqual(out["errors"], [])
        self.assertEqual(out["canon_changed"], False)

    def test_full_text_keeps_healthy_performance(self):
        out = quick_preflight(("LUCAS — Vamos viver esta aventura.\n" * 280), policy=self.policy)
        self.assertEqual(out["status"], "OK")
        self.assertEqual(out["fast_path"], "LOCAL_DETERMINISTIC_NO_NETWORK")

    def test_historical_staging_validates_provenance_not_semantics(self):
        questions = [
            dict(n=i, answer="Registro histórico não promovido, com resposta verificável por fonte literal.",
                 source_start_line=i*10, source_end_line=i*10+4,
                 status="HISTORICAL_SOURCE_NOT_RECONCILED")
            for i in range(1, 41)
        ]
        p = dict(schema="worldroot-historical-qa-draft-v1",
                 scope="CRONICAS_ONLY",canon_promotion=False,
                 source_line_count=296900,questions=questions)
        out = verify_historical_staging(p)
        self.assertEqual(out["checked"], 40)
        self.assertFalse(out["semantic_certification"])
        p["questions"][0]["source_end_line"] = 400000
        with self.assertRaises(ValueError):
            verify_historical_staging(p)

    def test_prior_praise_does_not_override_current_no_image_rule(self):
        self.assertEqual(
            next(r for r in self.policy["rules"] if r["id"] == "P01")["enforcement"],
            "ESTRUTURAL")


if __name__ == "__main__":
    unittest.main()
