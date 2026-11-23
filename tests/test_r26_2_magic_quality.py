"""R26.2 catalog data-quality honesty: counts vs creative individuality."""
import unittest

from worldroot.r26_magic_quality import audit_regional_variety
from worldroot.r26_magic_catalog import load_grimoire, validate_codex


class R262QualityAudit(unittest.TestCase):
    def test_1020_are_unique_names_not_claimed_as_independent_mechanics(self):
        r = audit_regional_variety()
        self.assertEqual(r["total_named_spells"], 1020)
        self.assertEqual(r["regional_named_variants"], 900)
        self.assertEqual(r["regional_lineages"], 90)
        self.assertEqual(r["distinct_lineage_mechanisms"], 90)
        self.assertEqual(r["regional_unique_names"], 900)
        self.assertIs(r["all_1020_have_unique_real_world_mechanics"], False)

    def test_templated_900_formulas_are_visible_as_quality_debt(self):
        r = audit_regional_variety()
        self.assertEqual(r["editorial_template_risk"], "ALTO")
        self.assertLessEqual(r["formula_sentence_frames"], 15)
        self.assertGreaterEqual(r["largest_formula_frame_reuses"], 50)
        self.assertIs(r["all_1020_have_individual_narrative_review"], False)

    def test_every_circle_has_ninety_regional_candidates(self):
        r = audit_regional_variety()
        self.assertTrue(r["schools_have_50_variants"])
        self.assertEqual(r["regional_schools"], 18)
        self.assertTrue(all(r["count_by_circle"][str(i)] == 90
                            for i in range(10)))

    def test_important_creation_authority_is_not_added_as_rank_x(self):
        r = validate_codex()
        self.assertTrue(r["genese_outside_rank"])
        self.assertEqual(len([x for x in load_grimoire()["spells"]
                              if x["id"] == "CREATION_GENESE"]), 0)

    def test_quality_audit_cannot_promote_new_spell_or_reveal_dragon_secret(self):
        r = audit_regional_variety()
        self.assertFalse(r["canon_changed"])
        self.assertFalse(r["spoilers_revealed"])


if __name__ == "__main__":
    unittest.main()
