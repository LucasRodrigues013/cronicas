"""Synthetic regression for multi-day volume that feels like a work report."""
import unittest

from worldroot.lived_narrative_audit import inspect_lived_narrative


def chapter(days, *, words_each=500, logistics=False):
    numerals = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                "IX", "X", "XI", "XII", "XIII", "XIV", "XV")
    chunks = []
    for i, day in enumerate(days):
        header = f"## {numerals[i]} — Tempo vivido\n"
        clock = f"DIA {day} · 08h30 · CIDADE\n"
        dialog = "**LUCAS —** O que você deseja fazer?\n**MIREN —** Quero descobrir primeiro.\n"
        lexicon = ("relatório reunião ensaio autorização registro " if logistics
                   else "O mundo desperta e Miren escolhe sua própria estrada. ")
        body = (lexicon * (words_each // 8))
        chunks.append(header + clock + dialog + body + "\n")
    return "\n".join(chunks)


class LivedNarrativeAuditTests(unittest.TestCase):
    def test_reference_like_one_day_is_not_condemned(self):
        result = inspect_lived_narrative(chapter([529] * 9, words_each=1000))
        self.assertEqual(result["day_count"], 1)
        self.assertEqual(result["status"], "NO_STRUCTURAL_FLAGS")
        self.assertFalse(result["literary_quality_certification"])

    def test_four_day_long_report_pattern_is_flagged_despite_size(self):
        text = chapter([534] * 3 + [535] * 5 + [536] * 3 + [537] * 4,
                       words_each=620, logistics=True)
        result = inspect_lived_narrative(text)
        self.assertEqual(result["day_count"], 4)
        self.assertEqual(result["scene_count"], 15)
        self.assertEqual(result["status"], "REVIEW_LIVED_EXPERIENCE", result)
        self.assertTrue(any("LIFE04" in a for a in result["advisories"]))
        self.assertFalse(result["canon_changed"])

    def test_genuine_multiday_story_is_not_automatically_failed(self):
        text = chapter([535] * 3 + [536] * 3 + [537] * 3,
                       words_each=1800, logistics=False)
        result = inspect_lived_narrative(text)
        self.assertNotEqual(result["status"], "REVIEW_LIVED_EXPERIENCE")
        self.assertEqual(result["day_count"], 3)
        self.assertEqual(result["scene_count"], 9)

    def test_one_day_technical_story_is_not_high_risk(self):
        text = chapter([540] * 10, words_each=620, logistics=True)
        result = inspect_lived_narrative(text)
        self.assertNotEqual(result["status"], "REVIEW_LIVED_EXPERIENCE")
        self.assertTrue(any("LIFE03" in a for a in result["advisories"]))

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            inspect_lived_narrative("")

    def test_zero_scenes_has_no_fabricated_certification(self):
        result = inspect_lived_narrative("Uma frase sem título de cena.")
        self.assertEqual(result["scene_count"], 0)
        self.assertFalse(result["reader_experience_certification"])


if __name__ == "__main__":
    unittest.main()
