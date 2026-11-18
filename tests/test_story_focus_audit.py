"""Synthetic, fast regression tests for advisory narrative audit."""
import unittest

from worldroot.story_focus_audit import REFERENCE_II, inspect_installment


def scene(n, length=850, speaker=True):
    header = f"## {n} — Teste de cena com consequências\n"
    line = ("**LUCAS —** Vamos descobrir o que aconteceu.\n" if speaker else
            "**ASTRA —** Os experimentos continuam.\n")
    return header + line + ("A vida acontece. O mundo responde. " * (length // 6)) + "\n"


class StoryFocusAuditTests(unittest.TestCase):
    def test_approved_reference_is_a_soft_comparison(self):
        self.assertEqual(REFERENCE_II["scene_count"], 9)
        self.assertEqual(REFERENCE_II["median_scene_words_approx"], 1019)
        self.assertEqual(REFERENCE_II["lucas_dialogue_scenes"], 7)

    def test_short_parallel_draft_gets_advisory_not_failure(self):
        body = "".join(scene(n, 220, i < 2) for i, n in
                       enumerate(["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]))
        result = inspect_installment(body)
        self.assertEqual(result["scene_count"], 8)
        self.assertTrue(result["advisories"])
        self.assertFalse(result["canon_changed"])
        self.assertFalse(result["literary_quality_certification"])

    def test_long_focused_episode_does_not_require_extra_length(self):
        body = "".join(scene(n, 1050, True) for n in
                       ["I", "II", "III", "IV", "V", "VI", "VII"])
        result = inspect_installment(body)
        self.assertEqual(result["scene_count"], 7)
        self.assertAlmostEqual(result["lucas_dialogue_scene_share"], 1.0)
        self.assertFalse(result["advisories"])

    def test_lucas_may_be_silent_without_blocking(self):
        body = scene("I", 900, speaker=False)
        result = inspect_installment(body)
        self.assertEqual(result["lucas_dialogue_scenes"], 0)
        self.assertEqual(result["status"], "ADVISORY_ONLY_NON_CANONICAL")
        self.assertEqual(result["advisories"], [])

    def test_checkpoint_not_counted_as_literature(self):
        body = scene("I", 850, True) + "\n## LIVRO V · CAPÍTULO 15 · PARTE V — ESCOLHAS\n" + ("narrativa " * 5000)
        result = inspect_installment(body)
        self.assertLess(result["scene_words_approx"], 2000)

    def test_markup_not_assumed_to_be_literary_words(self):
        body = '## I — Cena\n<box border radius="lg"><text color="secondary">teste</text></box>\n**LUCAS —** Oi.'
        result = inspect_installment(body)
        self.assertEqual(result["scene_count"], 1)
        self.assertLess(result["scene_words_approx"], 20)

    def test_blank_rejected(self):
        with self.assertRaises(ValueError):
            inspect_installment("")


if __name__ == "__main__":
    unittest.main()
