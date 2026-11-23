"""Synthetic regressions for future literary reviews (never a grade/canon)."""
import unittest

from worldroot.editorial_guard import compact_brief, load_policy, quick_preflight
from worldroot.literary_revision import (
    build_live_brief, review_episode, review_scene_cards,
    review_series_structure,
)

HEAD = {
    "book": "Livro VI",
    "chapter": 5,
    "part": "IV",
    "day": 562,
    "episode_id": "LVI-C05-PIV-D562-AUTHOR-SOURCE",
    "sequence": 33,
}


class LiteraryPrecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_review_detects_bastidor_microprose_and_shouting_without_banning_them(self):
        blocks = []
        for i, roman in enumerate(("I", "II", "III", "IV"), 1):
            lines = [f"## {roman} — Uma cena concreta\n"]
            lines.extend("A janela tremeu.\n" for _ in range(14))
            lines.extend("**LUCAS —** EU PRECISO FAZER ISSO AGORA!\n" for _ in range(4))
            lines.extend("**LUCAS —** Estou ouvindo você.\n" for _ in range(1))
            if i == 2:
                lines.append("Não houve uma contagem inventada de mortes.\n")
            blocks.append("".join(lines))
        r = review_episode("\n".join(blocks))
        self.assertEqual(r["scene_count"], 4)
        self.assertEqual(r["status"], "ADVISORY_ONLY")
        self.assertGreater(r["lucas_uppercase_turn_share"], 0.35)
        self.assertTrue(any("LIT01" in x for x in r["notices"]))
        self.assertTrue(any("LIT02" in x for x in r["notices"]))
        self.assertTrue(any("LIT03" in x for x in r["notices"]))
        self.assertIsNone(r["literary_grade"])
        self.assertFalse(r["canon_changed"])
        self.assertFalse(r["source_rewritten"])

    def test_lively_long_prose_does_not_trigger_mechanical_alarm(self):
        scene = ("A brisa carregou o cheiro da chuva sobre o vale, enquanto "
                 "Miren descobria que a inscrição tinha sido movida.\n")
        s = "".join(f"## {n} — Busca\n" + scene * 14 + 
                    "**LUCAS —** Posso ajudar, ou prefere investigar primeiro?\n"
                    for n in ("I", "II", "III"))
        r = review_episode(s)
        self.assertEqual(r["scene_count"], 3)
        self.assertEqual(r["notices"], [])
        self.assertEqual(r["meta_language_hits"], 0)

    def test_repeated_eighteen_scene_structure_is_only_a_notice(self):
        r = review_series_structure([{"scene_count": 18}] * 4)
        self.assertTrue(any("LIT04" in x for x in r["notices"]))
        self.assertFalse(r["canon_changed"])
        self.assertEqual(review_series_structure(
            [{"scene_count": 8}, {"scene_count": 13}])["notices"], [])

    def test_scene_cards_require_causes_without_preselecting_outcomes(self):
        r = review_scene_cards([{"desire": "Descobrir a passagem",
                                 "resistance": "Élfos divergem",
                                 "lived_action": "Miren investiga",
                                 "turn": "Uma testemunha contesta",
                                 "consequence": "Pesquisa muda de local"},
                                {"desire": "Proteger a cidade"}])
        self.assertEqual(r["cards"], 2)
        self.assertEqual(len(r["notices"]), 1)
        self.assertFalse(r["canon_changed"])

    def test_live_brief_follows_canonical_head_not_historical_p81(self):
        b = build_live_brief(HEAD, self.policy)
        self.assertIn("D562", b["text"])
        self.assertIn("C05", b["text"])
        self.assertIn("LVI-C05-PIV", b["text"])
        self.assertNotIn("D538", b["text"])
        self.assertNotIn("D539", b["text"])
        self.assertNotIn("PRE-PRODUCAO, r17", b["text"])
        self.assertEqual(b["mode"], "LIVE_HEAD_GROUNDED")
        self.assertFalse(b["canon_changed"])

    def test_precise_preflight_passes_live_head_without_promoting_canon(self):
        text = ("LIVRO VI — AS COROAS PARTIDAS\n"
                "## I — A reunião\n**LUCAS —** Vamos ouvir.\n"
                "## II — O caminho\n**MIREN —** Vou investigar.\n") * 5
        out = quick_preflight(text, policy=self.policy, head=HEAD)
        self.assertEqual(out["editorial_brief_mode"], "LIVE_HEAD_GROUNDED")
        self.assertFalse(any("LIT06" in n for n in out["notices"]))
        self.assertFalse(out["canon_changed"])
        self.assertIn("literary_review", out)

    def test_explicit_missing_head_is_reported_for_book_vi(self):
        text = "LIVRO VI\n## I — À noite\n" + (
            "A mulher avançou para compreender as antigas inscrições.\n" * 50)
        r = quick_preflight(text, policy=self.policy)
        self.assertTrue(any("LIT06" in x for x in r["notices"]))
        self.assertEqual(r["editorial_brief_mode"], "LEGACY_STATIC_NO_HEAD")
        self.assertFalse(r["canon_changed"])

    def test_blank_and_invalid_head_fail_closed(self):
        with self.assertRaises(ValueError):
            review_episode(" ")
        with self.assertRaises(ValueError):
            build_live_brief({**HEAD, "episode_id": ""}, self.policy)
        with self.assertRaises(ValueError):
            review_series_structure([{"scene_count": 2}, {"scene_count": "18"}])


if __name__ == "__main__":
    unittest.main()
