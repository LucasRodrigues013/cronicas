"""Synthetic tests for the nonblocking day-arc insight."""
import unittest
from worldroot.day_arc_audit import inspect_day_arc


class DayArcAuditTests(unittest.TestCase):
    def test_morning_to_afternoon_keeps_day_available(self):
        text = ("## I — A manhã\nDIA 533 · 06h43 — Casa.\n"
                "Lucas tomou café.\n"
                "## II — O entardecer\nDIA 533 · 17h29 — Campo.\n"
                "Lucas se despediu.\n**FIM DA PARTE II DE V**\n"
                "## Livro V · Capítulo 16 · Parte III — Sua escolha\n"
                "DIA 999 · 23h00 — Isto não é uma cena")
        res = inspect_day_arc(text)
        self.assertEqual(res["first"], {"day": 533, "hour": "06h43"})
        self.assertEqual(res["last"], {"day": 533, "hour": "17h29"})
        self.assertEqual(res["elapsed_minutes"], 646)
        self.assertEqual(res["days_touched"], [533])
        self.assertEqual(len(res["advisories"]), 1)
        self.assertFalse(res["day_closure_certified"])

    def test_cross_midnight_remains_valid_and_does_not_force_24_hours(self):
        text = ("## I — Noite\nDIA 531 · 22h06\n"
                "## II — Madrugada\nDIA 532 · 03h17\n"
                "## III — Anoitecer\nDIA 532 · 18h19\n")
        res = inspect_day_arc(text)
        self.assertEqual(res["days_touched"], [531, 532])
        self.assertEqual(res["elapsed_minutes"], 1213)
        self.assertTrue(res["chronological"])
        self.assertFalse(res["day_closure_certified"])

    def test_evening_scene_does_not_automatically_close_the_day(self):
        res = inspect_day_arc("## I — Manhã\nDIA 533 · 07h00\n"
                              "## II — Jantar\nDIA 533 · 21h00\n")
        self.assertEqual(res["last_phase"], "NOITE_MADRUGADA")
        self.assertEqual(res["advisories"], [])
        self.assertFalse(res["day_closure_certified"])

    def test_backwards_clock_is_review_signal_not_gate(self):
        res = inspect_day_arc("## I — Depois\nDIA 533 · 19h30\n"
                              "## II — Antes\nDIA 533 · 08h30\n")
        self.assertFalse(res["chronological"])
        self.assertIsNone(res["elapsed_minutes"])
        self.assertTrue(res["advisories"])

    def test_no_scene_clock_is_advisory(self):
        result = inspect_day_arc("## I — Um momento sem horário\nLucas sorriu.")
        self.assertIsNone(result["last"])
        self.assertTrue(result["advisories"])

    def test_invalid_and_empty_input_refused(self):
        with self.assertRaises(ValueError):
            inspect_day_arc("")
        with self.assertRaises(ValueError):
            inspect_day_arc("## I — Teste\nDIA 533 · 26h80")

    def test_author_exported_plain_scene_headings_do_not_lose_day(self):
        text = ("I — A manhã\\nDIA 538 · 06h08 — Quarto\\n"
                "Lucas tomou café.\\nII — A praça\\nDIA 538 · 11h32 — Centro\\n"
                "Lucas reencontrou Kael.\\nFIM DA PARTE I DE V")
        result = inspect_day_arc(text)
        self.assertEqual(result["days_touched"], [538])
        self.assertTrue(result["chronological"])
        self.assertEqual(result["last"], {"day": 538, "hour": "11h32"})

    def test_no_side_effects(self):
        prose = "## I — Amanhecer\nDIA 533 · 07h15\n"
        before = prose
        r = inspect_day_arc(prose)
        self.assertEqual(prose, before)
        self.assertFalse(r["canon_changed"])
        self.assertFalse(r["new_author_choice_recorded"])


if __name__ == "__main__":
    unittest.main()
