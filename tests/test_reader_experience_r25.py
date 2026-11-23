"""R25 regressions from historical dialogue/scene patterns and the live contract."""
import unittest

from worldroot.reader_experience import assess_experience, validate_reader_review
from worldroot.narrative_director import validate_direction, private_direction_brief
from worldroot.presentation_guard import presentation_preflight
from test_presentation_guard import RICH

HEAD = {"episode_id": "LVI-C05-PIV-D562-AUTHOR-SOURCE",
        "book": "Livro VI", "chapter": 5, "part": "IV", "day": 562}
DIRECTION = {
    "schema": "worldroot-narrative-direction-v1",
    "source_episode_id": HEAD["episode_id"],
    "author_choice": "Lucas visita a floresta e respeita as decisões de Elyrien.",
    "reader_promise": "Viver a floresta por dentro e descobrir suas feridas reais.",
    "lucas_lived_focus": "Lucas participa com Miren e escuta a voz dos guardiões.",
    "central_change": "Um acontecimento muda a atitude da comunidade.",
    "independent_world": ["Elyrien decide em conselho próprio."],
    "unknowns_preserved": ["Talis continua não localizada"],
    "does_not_choose_for_lucas": True,
}
NARRATIVE = (
    "## I — O primeiro encontro\n"
    "O chão tremeu quando Miren encontrou a inscrição antiga.\n"
    "**LUCAS —** O que aconteceu aqui?\n"
    "## II — A decisão\n"
    "Elyrien olhou a raiz e percebeu que o risco alcançava sua aldeia.\n"
    "**MIREN —** Precisamos escutar a floresta.\n"
    "## III — A passagem\n"
    "Lucas ofereceu a mão e o guarda escolheu segui-lo.\n"
    "**ELEN —** Eu sei onde começa o caminho.\n"
)
REVIEW = {
    "schema": "worldroot-reader-review-v1",
    "decision": "REVISADO_COM_EVIDENCIAS",
    "scene_evidence": [
        {"scene": "I",
         "literal_anchor": "O chão tremeu quando Miren encontrou a inscrição antiga.",
         "felt_experience": "Lucas observa algo cuja origem não compreende.",
         "scene_turn": "Miren revela uma inscrição física no solo.",
         "lasting_consequence": "O grupo passa a investigar uma nova rota."},
        {"scene": "II",
         "literal_anchor": "Elyrien olhou a raiz e percebeu que o risco alcançava sua aldeia.",
         "felt_experience": "A soberana sente a ameaça chegar ao seu povo.",
         "scene_turn": "A raiz mostra risco para a comunidade.",
         "lasting_consequence": "Os guardiões assumem a decisão local."},
    ],
    "pacing_decision": "As cenas têm objetivos distintos; não há interrupção de ação contínua.",
}


class R25ContractTest(unittest.TestCase):
    def test_reference_named_style_remains_accepted(self):
        self.assertEqual(presentation_preflight(RICH)["status"], "OK")

    def test_unlabeled_dialogue_is_hard_failure_for_new_stories(self):
        legacy_style = RICH.replace("**LUCAS —** Bom dia.", "— Bom dia.")
        result = presentation_preflight(legacy_style)
        self.assertEqual(result["status"], "BLOQUEADO")
        self.assertIn("unlabeled_dialogue", " ".join(result["errors"]))
        self.assertGreater(result["unlabeled_dialogue_count"], 0)
        self.assertEqual(presentation_preflight(legacy_style, strict_dialogue=False)["errors"], [])

    def test_fewer_than_five_named_turns_block(self):
        sample = RICH.replace("**LUCAS —**", "—").replace("**MIREN —**", "—")
        self.assertIn("dialogue", " ".join(presentation_preflight(sample)["errors"]))

    def test_editorial_intrusion_requires_rewrite(self):
        s = NARRATIVE.replace("O chão tremeu quando Miren encontrou a inscrição antiga.",
                              "Não declarou uma evolução inventada. O chão tremeu.")
        assessment = validate_reader_review(s, REVIEW)
        self.assertFalse(assessment["release_ready"])
        self.assertTrue(any("R25_BACKSTAGE" in x for x in assessment["errors"]))

    def test_review_must_include_real_quotes_in_distinct_scenes(self):
        outcome = validate_reader_review(NARRATIVE, REVIEW)
        self.assertTrue(outcome["release_ready"], outcome["errors"])
        self.assertFalse(outcome["literary_certification"])
        fake = {**REVIEW, "scene_evidence": [
            {**REVIEW["scene_evidence"][0], "literal_anchor": "Invenção ausente."},
            REVIEW["scene_evidence"][1],
        ]}
        self.assertFalse(validate_reader_review(NARRATIVE, fake)["release_ready"])

    def test_direction_follows_head_not_old_checkpoint(self):
        self.assertTrue(validate_direction(HEAD, DIRECTION)["ready"])
        brief = private_direction_brief(HEAD, DIRECTION)
        self.assertIn(HEAD["episode_id"], brief)
        self.assertNotIn("D539", brief)
        invalid = {**DIRECTION, "source_episode_id": "LVI-C01-PIII-D539"}
        self.assertFalse(validate_direction(HEAD, invalid)["ready"])
        invalid = {**DIRECTION, "does_not_choose_for_lucas": False}
        self.assertFalse(validate_direction(HEAD, invalid)["ready"])

    def test_eighteen_scene_mold_warns_without_forcing_a_quota(self):
        roman = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII",
                 "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII")
        body = "".join("## " + n + " — Dia vivido\n"
                       "Lucas conversou e o mundo respondeu ao que aconteceu.\n"
                       "**LUCAS —** Vamos observar.\n" for n in roman)
        assessment = assess_experience(body, previous_counts=[18, 18])
        self.assertTrue(any("R25_TEMPLATE" in x for x in assessment["risks"]))
        self.assertTrue(any("R25_FOCUS" in x for x in assessment["risks"]))
        self.assertFalse(assessment["literary_certification"])
        self.assertFalse(assessment["canon_changed"])

    def test_unlabeled_voices_do_not_create_fake_absence_of_lucas(self):
        from worldroot.story_focus_audit import inspect_installment
        scene = "## I — Cena\nLucas sorriu.\n— Vamos agora?\n"
        outcome = inspect_installment(scene)
        self.assertFalse(outcome["speaker_attribution_reliable"])
        self.assertIsNone(outcome["lucas_dialogue_scene_share"])

    def test_review_not_generated_by_storage_provenance(self):
        self.assertFalse(assess_experience(NARRATIVE)["canon_changed"])
        self.assertFalse(validate_direction(HEAD, DIRECTION)["fiction_content"])


if __name__ == "__main__":
    unittest.main()
