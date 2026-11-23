"""R26: 120-spell grimoire, rank safety, magic attribution, six living directors."""
import unittest

from worldroot.r26_magic_catalog import (
    validate_codex, load_grimoire, load_world, load_people,
    search_spells, get_spell, spell_ids_used_in_prose, summon_ids_used_in_prose,
)
from worldroot.r26_fantasy_directors import audit_fantasy

HEAD = "LVI-C05-PIV-D562-AUTHOR-SOURCE"
PROSE = (
    "## I — Um mundo capaz de surpreender\n"
    "**DIA 563 · 08h00 — VALE DAS RAÍZES**\n"
    "Thaeron ergueu os braços e três correntes de ar giraram acima do desfiladeiro.\n"
    "**THAERON —** O vento é mais antigo que a minha vontade.\n"
    "Miren olhou a floresta e sorriu ao descobrir uma nova passagem entre folhas.\n"
    "**MIREN —** Existe um caminho que ninguém tinha observado.\n"
)
def fantasy(**kw):
    data = {
        "schema": "worldroot-r26-fantasy-review-v1",
        "source_episode_id": HEAD,
        "cannot_choose_for_author": True,
        "genese_unrestricted": True,
        "backstage_invisible": True,
        "spell_uses": [],
        "summon_uses": [],
        "combat": {"mode": "SEM_COMBATE"},
        "wonder": {"mode": "SEM_DESCOBERTA"},
        "moments": [],
        "character_evolution": [
            {"name": "MIREN",
             "literal_anchor": "Miren olhou a floresta e sorriu ao descobrir uma nova passagem entre folhas.",
             "decision_or_reaction": "Miren encontrou a trilha enquanto observava o vale.",
             "emotional_or_relational_delta": "Ela preservou uma hipótese própria para o grupo.",
             "new_power_claimed": False}
        ],
        "variation_decision": "A cena acompanha um único encontro e permite silêncio sem fingir uma batalha.",
    }
    data.update(kw)
    return data


class R26MagicTests(unittest.TestCase):
    def test_grimoire_is_complete_original_and_still_proposed(self):
        report = validate_codex()
        self.assertEqual(report["status"], "OK", report)
        self.assertEqual(report["schools"], 12)
        self.assertEqual(report["named_spells"], 120)
        self.assertEqual(report["summons"], 16)
        self.assertEqual(report["wonders"], 12)
        self.assertEqual(report["creatures"], 12)
        self.assertEqual(report["tracked_characters"], 25)
        self.assertEqual(report["historical_feats"], 11)
        self.assertTrue(report["genese_outside_rank"])
        for spell in load_grimoire()["spells"]:
            self.assertEqual(spell["status"], "R26_PROPOSTO_NAO_CANONICO")

    def test_all_schools_have_unique_named_circles(self):
        book = load_grimoire()
        for school in book["schools"]:
            spells = [s for s in book["spells"] if s["escola"] == school["id"]]
            self.assertEqual({s["circulo"] for s in spells}, set(range(10)))
            self.assertTrue(all(s.get("contrajogo_ou_lacuna") for s in spells))
        self.assertEqual(get_spell("Catedral do Céu Partilhado")["escola"], "AEROMANCIA")
        self.assertEqual(get_spell("Coroa do Mar Invertido")["circulo"], 9)
        self.assertEqual(len(search_spells(school="HIDROMANCIA")), 10)
        self.assertTrue(search_spells("névoa"))
        self.assertTrue(load_people()["profiles"])
        self.assertTrue(load_world()["invocations"])

    def test_invented_spells_never_autocanonize_from_simple_mentions(self):
        story = PROSE.replace("três correntes de ar",
                              "Catedral do Céu Partilhado e três correntes de ar")
        self.assertIn("R26-AEROMANCIA-08", spell_ids_used_in_prose(story))
        assessed = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(assessed["ready"])
        self.assertTrue(any("R26_MAGIC" in e for e in assessed["errors"]))
        self.assertFalse(assessed["canon_changed"])

    def test_quiet_life_is_valid_without_summon_or_battle(self):
        report = audit_fantasy(PROSE, fantasy(), head_episode_id=HEAD)
        self.assertTrue(report["ready"], report)
        self.assertEqual(report["combat"]["mode"], "SEM_COMBATE")
        self.assertEqual(report["wonder"]["mode"], "SEM_DESCOBERTA")
        self.assertFalse(report["independently_human_certified"])
        self.assertFalse(report["magic_proposals_autocanonized"])

    def test_director_rejects_preselected_winner_and_ungrounded_attack(self):
        combat = {
            "mode": "COMBATE", "scale": "GRANDE", "stake": "Proteger a aldeia durante o ataque.",
            "terrain": "Desfiladeiro e floresta enraizada.",
            "winner_predetermined": True, "does_not_nerf_genese": True,
            "other_characters_act": True,
            "beats": [{"actor": "Thaeron", "attempt": "Guia as correntes",
                       "response": "Miren observa", "consequence": "O vale se mantém",
                       "literal_anchor": "um combate que não existe na fonte"}],
        }
        r = audit_fantasy(PROSE, fantasy(combat=combat), head_episode_id=HEAD)
        self.assertFalse(r["ready"])
        self.assertTrue(any("R26_COMBAT" in e for e in r["errors"]))
        self.assertTrue(any("R26_EVIDENCE" in e for e in r["errors"]))

    def test_wonder_needs_observed_reaction_not_only_name(self):
        report = audit_fantasy(PROSE, fantasy(wonder={
            "mode": "DESCOBERTA", "encounters": [{
                "literal_anchor": "inexistente",
                "sensory_difference": "A água sobe contra o vento.",
                "character_reaction": "Lucas ergue a cabeça sem compreender.",
                "world_independence": "O fenômeno existia antes de a aeronave chegar."
            }]
        }), head_episode_id=HEAD)
        self.assertFalse(report["ready"])
        self.assertTrue(any("R26_EVIDENCE" in e for e in report["errors"]))

    def test_character_does_not_get_unrecorded_spell(self):
        claim = {**fantasy()["character_evolution"][0],
                 "new_power_claimed": True}
        report = audit_fantasy(PROSE, fantasy(character_evolution=[claim]),
                               head_episode_id=HEAD)
        self.assertFalse(report["ready"])
        self.assertTrue(any("R26_CHARACTERS" in e for e in report["errors"]))

    def test_meta_defenses_from_old_chapter_still_fail(self):
        story = PROSE + "\nO Criador não precisava fingir que sua energia estava acabando.\n"
        self.assertFalse(audit_fantasy(story, fantasy(), head_episode_id=HEAD)["ready"])

    def test_source_head_cannot_be_old(self):
        self.assertFalse(audit_fantasy(PROSE, fantasy(), head_episode_id="OLD")["ready"])

    def test_summons_and_spells_keep_their_distinct_records(self):
        self.assertTrue(summon_ids_used_in_prose(
            PROSE + "\nO Guardião da Maré Oca apareceu no crepúsculo."))
        self.assertFalse(summon_ids_used_in_prose(PROSE))


if __name__ == "__main__":
    unittest.main()
