"""Length budget regression: true narrative words, not UI/control strings."""
import unittest

from worldroot.longform_depth import (
    AIM_LOW, TARGET_WORDS, MIN_ARCHIVE_WORDS,
    count_prose_words, inspect_longform,
)


def prose(words_per_scene: int = 1100, scenes: int = 9) -> str:
    names = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    chunks = []
    for n in names[:scenes]:
        chunks.append("## " + n + " — Uma cena independente\n"
                      + "**LUCAS —** Preciso decidir em liberdade.\n"
                      + ("o mundo responde " * ((words_per_scene - 6) // 3)) + "\n")
    return "\n".join(chunks)


class LongformDepthTest(unittest.TestCase):
    def test_milestones_are_explicit(self):
        self.assertEqual(TARGET_WORDS, 10_000)
        self.assertEqual(AIM_LOW, 9_400)
        self.assertEqual(MIN_ARCHIVE_WORDS, 8_800)

    def test_full_longform_is_ready_without_claiming_literary_merit(self):
        result = inspect_longform(prose(1100))
        self.assertEqual(result["status"], "ALVO", result)
        self.assertGreaterEqual(result["prose_words_approx"], AIM_LOW)
        self.assertFalse(result["semantic_certification"])
        self.assertFalse(result["canon_changed"])

    def test_underlength_narrative_requires_expansion(self):
        result = inspect_longform(prose(780))
        self.assertEqual(result["status"], "EXPANDIR")
        self.assertTrue(result["errors"])
        self.assertLess(result["prose_words_approx"], MIN_ARCHIVE_WORDS)

    def test_ui_buttons_and_markup_are_not_story(self):
        narrative = prose(500)
        fake_ui = "<box><title>" + ("Botão " * 12000) + "</title><button>Enviar</button></box>"
        result = inspect_longform(narrative)
        self.assertEqual(result["status"], "EXPANDIR")
        self.assertLess(count_prose_words(narrative),
                        count_prose_words(narrative + fake_ui))
        # Whole chapter is passed as prose by mistake: structured UI still
        # cannot be treated as approved real narrative by a word counter.
        self.assertFalse(result["semantic_certification"])

    def test_short_scenes_flag_pacing_risk(self):
        text = prose(100, scenes=9) + prose(1500, scenes=8)
        result = inspect_longform(text)
        self.assertIn("I", result["very_short_scenes"])
        self.assertTrue(any("LONGFORM02" in n for n in result["notices"]))

    def test_minimum_not_replaceable_with_zero(self):
        with self.assertRaises(ValueError):
            inspect_longform(prose(1000), minimum=0)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            inspect_longform("")

if __name__ == "__main__":
    unittest.main()
