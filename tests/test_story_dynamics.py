"""Regression checks for non-mutating Book VI story dynamics."""
import unittest

from worldroot.story_dynamics import (
    MODULE_NAMES, AUDIT_BASELINE, FIVE_PARTS,
    review_chapter_outline, review_operation, inspect_draft_dynamics,
)


class StoryDynamicsTests(unittest.TestCase):
    @staticmethod
    def outline():
        return {
            "canon_checkpoint_ref": "canon/HEAD.json",
            "author_choices_open": True,
            "parts": [
                {"part": tag, "dramatic_goal": f"Goal {tag}",
                 "lived_scene": f"Scene {tag}", "change": f"Change {tag}",
                 "outgoing_hook": f"Hook {tag}", "intensity": i,
                 "experiences": ["AVENTURA"]}
                for i, tag in enumerate(FIVE_PARTS, 1)
            ],
            "seeds": [{"id": "S01", "status": "PROPOSTA"}],
        }

    def test_10_modules_and_42_editorial_baseline(self):
        self.assertEqual(len(MODULE_NAMES), 10)
        self.assertEqual(sum(AUDIT_BASELINE.values()), 42)

    def test_five_part_outline_is_reviewed_not_canonized(self):
        outline = self.outline()
        outline["parts"][-1]["earned_payoff"] = "An earned climax"
        r = review_chapter_outline(outline)
        self.assertTrue(r["ok"])
        self.assertFalse(r["canon_updated"])
        self.assertFalse(r["narrative_generated"])
        self.assertEqual(r["notices"], [])

    def test_fifth_part_cannot_be_only_status_report_without_notice(self):
        r = review_chapter_outline(self.outline())
        self.assertTrue(r["ok"])
        self.assertTrue(any("Part V" in x for x in r["notices"]))

    def test_no_premature_canonicalization_of_seeds(self):
        outline = self.outline()
        outline["seeds"][0]["status"] = "CANONICO"
        self.assertFalse(review_chapter_outline(outline)["ok"])

    def test_operation_cannot_force_genesis_nerf_or_omniscience(self):
        op = {"id": "SP01", "actor": "Unidentified spy",
              "location": "On a documented route", "objective": "Observe",
              "resources": ["safe cover"], "known_information": ["reported rumor"],
              "route_or_access": "verified road",
              "earliest_window": "after arrival", "possible_outcomes": ["detected", "evades"],
              "status": "PROPOSTA"}
        self.assertTrue(review_operation(op)["ok"])
        op["instant_character_knowledge"] = True
        op["genesis_nerf"] = True
        r = review_operation(op)
        self.assertFalse(r["ok"])
        self.assertEqual(len(r["errors"]), 2)

    def test_new_prose_advisory_does_not_replace_human_editor(self):
        r = inspect_draft_dynamics("LUCAS — Vamos descobrir o que aconteceu.", {"part": "V"})
        self.assertEqual(r["status"], "ADVISORY_ONLY")
        self.assertIsNone(r["quality_score"])
        self.assertFalse(r["canon_updated"])
        self.assertTrue(any("Part V" in x for x in r["notices"]))


if __name__ == "__main__":
    unittest.main()
