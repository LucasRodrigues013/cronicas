"""WORLDROOT R26.2: adversarial authorial scenarios, no canon mutation.

Each numbered scenario is executable in GitHub Actions, not a qualitative promise.
Tests use synthetic prose for validation behavior and a temporary hashed canonical
archive to prove actual old-source readback.
"""
import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from test_r26_magic_and_directors import PROSE, HEAD, fantasy
from worldroot.r26_fantasy_directors import audit_fantasy
from worldroot.r26_authority_guard import load_creation_authority, validate_authority_bible
from worldroot.r26_magic_catalog import (
    get_spell, verify_prior_spell_source, classify_named_spell_references,
    load_grimoire, validate_codex,
)


class R262Scenarios(unittest.TestCase):
    def audit(self, extra, *, extra_review=None, archive_root=None, head=HEAD):
        return audit_fantasy(
            PROSE + "\n" + extra,
            fantasy(**(extra_review or {})),
            head_episode_id=head,
            archive_root=archive_root,
        )

    def assert_reason(self, report, fragment):
        self.assertFalse(report["ready"], report)
        self.assertTrue(any(fragment in e for e in report["errors"]), report["errors"])

    @staticmethod
    def old_spell(caster="Thaeron", spell="Fio de Orvalho"):
        anchor = f"{caster} pronunciou {spell} e a gota parou no ar."
        return (
            anchor, {
                "spell_id": get_spell(spell)["id"],
                "literal_anchor": anchor,
                "caster": caster.upper(),
                "learning_status": "JA_CONHECIDA_COM_PROVA",
                "previous_source": "episodes/LVI-C04-PI-D554-AUTHOR-SOURCE/draft/narrativa_integral.md",
                "previous_literal_anchor": f"{caster} conjurou {spell} em outro lugar.",
            }
        )

    @staticmethod
    def staged_canon(root, *, corrupt=False, authorized=True):
        eid = "LVI-C04-PI-D554-AUTHOR-SOURCE"
        src = root / "episodes" / eid / "draft" / "narrativa_integral.md"
        src.parent.mkdir(parents=True, exist_ok=True)
        raw = "Na escola, Thaeron conjurou Fio de Orvalho em outro lugar.\n"
        src.write_text(raw, encoding="utf-8")
        if authorized:
            j = root / "canon" / "episodes" / (eid + ".json")
            j.parent.mkdir(parents=True, exist_ok=True)
            j.write_text(json.dumps({
                "episode_id": eid, "status": "FECHADO_GITHUB",
                "story_sha256": "0" * 64 if corrupt
                                 else sha256(src.read_bytes()).hexdigest(),
            }), encoding="utf-8")
        return src

    def test_s01_creation_without_a_magical_spell_is_valid(self):
        r = self.audit("Lucas usou CREATION para materializar uma ponte inteira sobre o vale.")
        self.assertTrue(r["ready"], r["errors"])
        self.assertEqual(r["authority"]["genese_kind"], "AUTORIDADE_NAO_MAGIA")

    def test_s02_no_energy_limit_or_rank_is_introduced(self):
        r = self.audit("Lucas decidiu não construir mais casas hoje. Estava com saudade de Miren.")
        self.assertTrue(r["ready"], r["errors"])
        self.assertFalse(r["authority"]["power_measure_assigned"])

    def test_s03_creation_as_circle_ix_is_forbidden(self):
        self.assert_reason(self.audit("GÊNESE era uma magia do Círculo IX."), "R26_CREATION")

    def test_s04_mana_exhaustion_is_forbidden(self):
        self.assert_reason(
            self.audit("GÊNESE parou de funcionar porque Lucas ficou sem mana."),
            "R26_CREATION")

    def test_s05_counterspell_automatically_nullifying_genesis_is_forbidden(self):
        self.assert_reason(
            self.audit("Uma magia anulou GÊNESE, mesmo sem conhecer sua origem."),
            "R26_CREATION")

    def test_s06_knowledge_gaps_are_allowed(self):
        r = self.audit("Lucas desconhecia aquela canção de vento e fez perguntas a Thaeron.")
        self.assertTrue(r["ready"], r["errors"])

    def test_s07_world_creation_prior_dragon_claim_needs_evidence(self):
        self.assert_reason(
            self.audit("AERÚN era mais antigo que a própria criação do mundo."),
            "R26_COSMOLOGY")

    def test_s08_legend_about_primordial_dragon_is_allowed(self):
        r = self.audit("Diziam que AERÚN talvez existisse antes do mundo, mas ninguém provara isso.")
        self.assertTrue(r["ready"], r["errors"])

    def test_s09_system_made_genese_not_established(self):
        self.assert_reason(self.audit("O SISTEMA criou GÊNESE antes de Lucas nascer."),
                           "R26_COSMOLOGY")

    def test_s10_lucas_question_is_not_a_cosmology_proof(self):
        r = self.audit("Lucas perguntou se o SISTEMA criou GÊNESE, sem acreditar na hipótese.")
        self.assertTrue(r["ready"], r["errors"])

    def test_s11_two_aerun_entities_can_coexist(self):
        r = self.audit("O Instituto AERÚN abriu a biblioteca.\nO dragão AERÚN viveu além dos mapas.")
        self.assertTrue(r["ready"], r["errors"])
        self.assertGreaterEqual(r["authority"]["dragon_references"], 1)
        self.assertGreaterEqual(r["authority"]["institute_references"], 1)

    def test_s12_dragon_cannot_become_institute(self):
        self.assert_reason(
            self.audit("O Instituto AERÚN era o mesmo ser que o Dragão AERÚN."),
            "R26_ENTITY")

    def test_s13_volume_title_does_not_cast(self):
        r = self.audit("Miren abriu um volume chamado Catedral do Céu Partilhado.")
        self.assertTrue(r["ready"], r["errors"])
        self.assertIn("R26-AEROMANCIA-08",
                      r["magic"]["book_title_or_reference_mentions"])

    def test_s14_incantation_without_registration_fails(self):
        self.assert_reason(
            self.audit("Thaeron pronunciou Catedral do Céu Partilhado e a luz tomou o vale."),
            "R26_MAGIC")

    def test_s15_wizard_cannot_steal_another_casters_entry(self):
        anchor = "Brannik pronunciou Fio de Orvalho e a água se ergueu."
        ledger = {"spell_id": "R26-HIDROMANCIA-00", "literal_anchor": anchor,
                  "caster": "THAERON", "learning_status": "ESTREIA_NARRADA"}
        self.assert_reason(self.audit(anchor, extra_review={"spell_uses": [ledger]}),
                           "R26_CASTER")

    def test_s16_legitimate_small_spell_is_accepted(self):
        anchor = "Thaeron pronunciou Fio de Orvalho e a água se ergueu."
        ledger = {"spell_id": "R26-HIDROMANCIA-00", "literal_anchor": anchor,
                  "caster": "THAERON", "learning_status": "ESTREIA_NARRADA"}
        r = self.audit(anchor, extra_review={"spell_uses": [ledger]})
        self.assertTrue(r["ready"], r["errors"])

    def test_s17_book_title_with_fabricated_cast_ledger_fails(self):
        anchor = "Thaeron abriu um livro chamado Fio de Orvalho."
        ledger = {"spell_id": "R26-HIDROMANCIA-00", "literal_anchor": anchor,
                  "caster": "THAERON", "learning_status": "ESTREIA_NARRADA"}
        self.assert_reason(self.audit(anchor, extra_review={"spell_uses": [ledger]}),
                           "R26_MAGIC")

    def test_s18_prior_spell_cannot_be_claimed_without_source(self):
        anchor, use = self.old_spell()
        self.assert_reason(self.audit(anchor, extra_review={"spell_uses": [use]}),
                           "R26_PROVENANCE")

    def test_s19_unratified_draft_cannot_be_used_as_old_knowledge(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.staged_canon(root, authorized=False)
            anchor, use = self.old_spell()
            self.assert_reason(
                self.audit(anchor, extra_review={"spell_uses": [use]},
                           archive_root=root), "R26_PROVENANCE")

    def test_s20_verified_ratified_earlier_spell_is_reusable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.staged_canon(root)
            anchor, use = self.old_spell()
            r = self.audit(anchor, extra_review={"spell_uses": [use]},
                           archive_root=root)
            self.assertTrue(r["ready"], r["errors"])

    def test_s21_corrupt_prior_story_sha_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.staged_canon(root, corrupt=True)
            anchor, use = self.old_spell()
            self.assert_reason(
                self.audit(anchor, extra_review={"spell_uses": [use]},
                           archive_root=root), "R26_PROVENANCE")

    def test_s22_traversal_and_aggregate_chapter_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.staged_canon(root)
            for path in (
                "../episodes/LVI-C04-PI-D554-AUTHOR-SOURCE/draft/narrativa_integral.md",
                "chapters/LIVRO-VI-C04/LIVRO-VI-C04-INTEGRAL.md"
            ):
                p = verify_prior_spell_source(
                    root, path, "Thaeron conjurou Fio de Orvalho em outro lugar.")
                self.assertFalse(p["verified"])

    def test_s23_previous_quote_must_name_same_spell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.staged_canon(root)
            anchor, use = self.old_spell()
            use["previous_literal_anchor"] = "Na escola, Thaeron conjurou Outra Magia em outro lugar."
            self.assert_reason(
                self.audit(anchor, extra_review={"spell_uses": [use]},
                           archive_root=root), "R26_PROVENANCE")

    def test_s24_dialogue_question_about_spell_is_not_cast(self):
        r = self.audit("**MIREN —** Thaeron, já leu Catedral do Céu Partilhado?")
        self.assertTrue(r["ready"], r["errors"])

    def test_s25_three_arcos_invention_requires_nonlucas_actor(self):
        spell = get_spell("R26X-FORJA_AURORA_ESTUDOS-F1-C0")
        anchor = "Lucas pronunciou " + spell["nome"] + " e o metal brilhou."
        proto = "Lucas fez sozinho a primeira demonstração na Forja Aurora."
        use = {"spell_id": spell["id"], "literal_anchor": anchor,
               "caster": "LUCAS", "learning_status": "ESTREIA_NARRADA",
               "acquisition": {"pathway": "INVENCAO_INSTITUCIONAL",
                               "school_lineage": "Runotecnologia da Forja Aurora",
                               "inventor": "Lucas Rodrigues",
                               "literal_origin_anchor": proto,
                               "prototype_anchor": proto,
                               "not_automatically_invented_by_lucas": True}}
        self.assert_reason(
            self.audit(proto + "\n" + anchor, extra_review={"spell_uses": [use]}),
            "R26_ORIGIN")

    def test_s26_three_arcos_real_independent_inventor_is_allowed(self):
        spell = get_spell("R26X-FORJA_AURORA_ESTUDOS-F1-C0")
        anchor = "Brannik pronunciou " + spell["nome"] + " no salão dos artífices."
        proto = "Brannik estudou sete ligas diferentes antes de propor seu novo gesto."
        use = {"spell_id": spell["id"], "literal_anchor": anchor,
               "caster": "BRANNIK", "learning_status": "ESTREIA_NARRADA",
               "acquisition": {"pathway": "INVENCAO_INSTITUCIONAL",
                               "school_lineage": "Runotecnologia da Forja Aurora",
                               "inventor": "BRANNIK",
                               "literal_origin_anchor": proto,
                               "prototype_anchor": proto,
                               "not_automatically_invented_by_lucas": True}}
        r = self.audit(proto + "\n" + anchor, extra_review={"spell_uses": [use]})
        self.assertTrue(r["ready"], r["errors"])
        self.assertFalse(r["magic_proposals_autocanonized"])

    def test_s27_catalog_does_not_pretend_every_spell_was_learned(self):
        r = validate_codex()
        self.assertEqual(r["named_spells"], 1020)
        self.assertEqual(r["proven_ownership_from_regional_expansion"], 0)
        self.assertEqual(r["regional_lineages"], 90)

    def test_s28_authority_bible_keeps_dragon_secrets_open(self):
        b = load_creation_authority()
        self.assertEqual(validate_authority_bible()["status"], "OK")
        self.assertTrue(b["policy_flags"]["premundane_dragons_unproven"])
        self.assertEqual(b["identity"]["kind"], "AUTORIDADE_PRIMORDIAL_NAO_MAGIA")
        self.assertTrue(all(x["status"].startswith("SEMENTE_")
                            for x in b["narrative_threads"]))

    def test_s29_no_fake_new_known_spells_from_magic_only_catalog(self):
        p = get_spell("R26X-VELATH_METEOROS-F2-C8")
        self.assertEqual(p["status"], "R26_PROPOSTO_NAO_CANONICO")
        self.assertEqual(p["inventor_personagem"], "NAO_ATRIBUIDO")

    def test_s30_wrong_head_is_rejected(self):
        self.assert_reason(self.audit("Lucas leu as nuvens.", head="OLD_HEAD"),
                           "R26_HEAD")

    def test_s31_wonder_without_discovery_and_without_battle_is_valid(self):
        r = self.audit("Miren beijou Lucas sob a luz do jardim.")
        self.assertTrue(r["ready"], r["errors"])
        self.assertEqual(r["combat"]["mode"], "SEM_COMBATE")
        self.assertEqual(r["wonder"]["mode"], "SEM_DESCOBERTA")

    def test_s32_dragon_knowing_creations_origin_remains_speculative(self):
        mystery = load_creation_authority()["protected_unknowns"]
        self.assertTrue(any(x["id"] == "MYSTERY-DRAGON-WITNESS"
                            and x["status"] == "HIPOTESE_NAO_COMPROVADA"
                            and x["knowledge_of_aerun"] == "NÃO_ESTABELECIDO"
                            for x in mystery))

    def test_s34_speculation_in_first_sentence_cannot_hide_mana_nerf_afterward(self):
        self.assert_reason(
            self.audit("Talvez AERÚN existisse antes do mundo. GÊNESE parou de funcionar porque Lucas ficou sem mana."),
            "R26_CREATION")

    def test_s35_character_dialogue_is_not_automatic_narrator_truth(self):
        story = "**THAERON —** Talvez os dragões sejam mais antigos que o mundo. Eu não sei."
        r = self.audit(story)
        self.assertTrue(r["ready"], r["errors"])

    def test_s33_spell_lookup_returns_copy_not_shared_catalog_object(self):
        x = get_spell("R26-AEROMANCIA-08")
        original = x["nome"]
        x["nome"] = "CORROMPIDO"
        self.assertEqual(get_spell("R26-AEROMANCIA-08")["nome"], original)
        self.assertEqual(load_grimoire()["spells"][28]["nome"], original)


if __name__ == "__main__":
    unittest.main()
