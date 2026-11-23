"""R26.2 red-team baseline: reproduce known holes before applying patches.

These deliberately expect the correct future behavior and should fail against
unrepaired R26.1. Re-run unchanged after repair for a real red-to-green trace.
"""
import unittest
from test_r26_magic_and_directors import fantasy, PROSE, HEAD
from worldroot.r26_fantasy_directors import audit_fantasy
from worldroot.r26_magic_catalog import get_spell


class R262RedTeamBaseline(unittest.TestCase):
    def test_book_title_is_not_a_conjuration(self):
        story = PROSE + (
            "\nMiren abriu um volume chamado Catedral do Céu Partilhado.\n"
            "Thaeron explicou que era apenas o título de um estudo antigo.\n"
        )
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertTrue(result["ready"], result["errors"])

    def test_genuine_spell_incantation_without_ledger_is_blocked(self):
        story = PROSE + "\nThaeron pronunciou Catedral do Céu Partilhado e o céu se abriu.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_MAGIC" in x for x in result["errors"]))

    def test_wrong_caster_cannot_claim_another_persons_spell(self):
        story = PROSE + "\nBrannik pronunciou Fio de Orvalho e a água subiu.\n"
        use = {
            "spell_id": "R26-HIDROMANCIA-00",
            "literal_anchor": "Brannik pronunciou Fio de Orvalho e a água subiu.",
            "caster": "THAERON", "learning_status": "ESTREIA_NARRADA",
        }
        result = audit_fantasy(story, fantasy(spell_uses=[use]), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_CASTER" in x for x in result["errors"]))

    def test_creation_mana_exhaustion_not_hidden_by_boolean_review(self):
        story = PROSE + "\nGÊNESE parou de funcionar porque Lucas ficou sem mana.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_CREATION" in x for x in result["errors"]))

    def test_creation_rank_nine_is_a_category_error(self):
        story = PROSE + "\nGÊNESE era apenas uma magia do Círculo IX.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_CREATION" in x for x in result["errors"]))

    def test_dragon_pre_world_age_remains_unproven(self):
        story = PROSE + "\nAERÚN era mais antigo que a própria criação do mundo.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_COSMOLOGY" in x for x in result["errors"]))

    def test_legend_can_remain_a_legend(self):
        story = PROSE + "\nDiziam que AERÚN talvez existisse antes do mundo. Ninguém tinha prova.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertTrue(result["ready"], result["errors"])

    def test_design_knowledge_is_not_a_resource_limit(self):
        story = PROSE + "\nLucas não conhecia o desenho das antigas torres, mas GÊNESE permanecia plena.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertTrue(result["ready"], result["errors"])

    def test_institute_and_dragon_must_not_be_mixed(self):
        story = PROSE + "\nO Instituto AERÚN era o mesmo ser que o Dragão AERÚN.\n"
        result = audit_fantasy(story, fantasy(), head_episode_id=HEAD)
        self.assertFalse(result["ready"])
        self.assertTrue(any("R26_ENTITY" in x for x in result["errors"]))

    def test_existing_canon_is_not_changed_by_testing(self):
        result = audit_fantasy(PROSE, fantasy(), head_episode_id=HEAD)
        self.assertTrue(result["ready"], result)
        self.assertFalse(result["canon_changed"])
        self.assertFalse(result["magic_proposals_autocanonized"])


if __name__ == "__main__":
    unittest.main()
