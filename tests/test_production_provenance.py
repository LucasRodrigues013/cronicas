"""Synthetic guards for the 37-role director roster and 40-question evidence statuses."""
import unittest

from worldroot.production_roles import ROLES, ALWAYS, CHIEF, route, verify_roster
from worldroot.provenance_audit import verify_quiz_contract
from worldroot.ledger import GateError

URL_HEAD="https://github.com/LucasRodrigues013/cronicas/blob/story-archive/canon/HEAD.json"
URL_DRAFT="https://github.com/LucasRodrigues013/cronicas/blob/story-archive/episodes/SYNTHETIC/draft/checkpoint_candidato.json"
URL_PLAN="https://docs.google.com/document/d/SYNTHETIC/edit"
HEAD={"day":528,"episode_id":"LV-C15-PI-D528","sequence":0}
DRAFT={"day":529,"canon_status":"RASCUNHO"}

def qa_contract():
    questions=[]
    for n in range(1,41):
        planned=n>=21
        questions.append({
            "number":n,
            "statuses":["PLANEJADO"] if planned else ["CANONICO"],
            "answer":"A synthetic answer states a fact without introducing narrative.",
            "sources":[{"kind":"DRIVE_PLANEJAMENTO" if planned else "GITHUB_HEAD",
                        "url":URL_PLAN if planned else URL_HEAD}],
        })
    questions[1]["statuses"]=["CANONICO","RASCUNHO"]
    questions[1]["sources"].append({"kind":"GITHUB_DRAFT","url":URL_DRAFT})
    return {"schema":"worldroot-memory-audit-v1","head_reference":HEAD.copy(),
            "draft_reference":{"day":529,"canon_status":"RASCUNHO","episode_id":"SYNTHETIC"},
            "questions":questions}


class ProductionRosterTests(unittest.TestCase):
    def test_exact_proposed_37_9_and_single_director(self):
        self.assertTrue(verify_roster())
        self.assertEqual(len(ROLES),37)
        self.assertEqual(CHIEF,"diretor_geral_showrunner")
        self.assertEqual(len(ALWAYS),4)

    def test_always_four_and_at_most_five_context_roles(self):
        result=route(["GENESE","COMBATE","CIDADE","POLITICA"])
        self.assertEqual(result["mandatory"],list(ALWAYS))
        self.assertLessEqual(len(result["contextual"]),5)
        self.assertEqual(result["operating_mode"],"DECLARATIVE_ADVISORY_NOT_INDEPENDENT_AGENTS")
        self.assertFalse(result["canon_changed"])

    def test_character_knowledge_guard_cannot_be_duplicated(self):
        result=route(["POV_EXTERNO","SEGREDO","POV_EXTERNO"])
        self.assertEqual(len(set(result["contextual"])),len(result["contextual"]))
        self.assertNotIn("diretor_conhecimento",result["contextual"])

    def test_bad_routing_tags_blocked(self):
        with self.assertRaises(ValueError):route(["EIDORYN"])
        with self.assertRaises(TypeError):route("COMBATE")
        with self.assertRaises(ValueError):route(["GENESE"],max_contextual=6)


class FortyQuestionAuditTests(unittest.TestCase):
    def test_good_fixture_forty_questions(self):
        result=verify_quiz_contract(qa_contract(),head=HEAD,draft_checkpoint=DRAFT)
        self.assertEqual(result["checked_questions"],40)
        self.assertEqual(result["state"],"STATUS_E_REFERENCIAS_VALIDOS_SEM_CERTIFICACAO_SEMANTICA")

    def test_draft_cannot_be_marked_as_canon_by_status(self):
        obj=qa_contract()
        obj["questions"][1]["statuses"]=["CANONICO"]
        obj["questions"][1]["sources"]=[{"kind":"GITHUB_DRAFT","url":URL_DRAFT}]
        with self.assertRaises(GateError):
            verify_quiz_contract(obj,head=HEAD,draft_checkpoint=DRAFT)

    def test_future_plan_cannot_use_only_canon_head(self):
        obj=qa_contract()
        obj["questions"][20]["sources"]=[{"kind":"GITHUB_HEAD","url":URL_HEAD}]
        with self.assertRaises(GateError):
            verify_quiz_contract(obj,head=HEAD,draft_checkpoint=DRAFT)

    def test_hypothesis_cannot_be_marked_canonical(self):
        obj=qa_contract()
        obj["questions"][33]["statuses"]=["CANONICO","HIPOTESE"]
        obj["questions"][33]["sources"].append({"kind":"GITHUB_HEAD","url":URL_HEAD})
        with self.assertRaises(GateError):
            verify_quiz_contract(obj,head=HEAD,draft_checkpoint=DRAFT)

    def test_head_advance_marks_review_historical_without_retcon(self):
        obj=qa_contract()
        result=verify_quiz_contract(obj,head={**HEAD,"day":529,"sequence":1},draft_checkpoint=DRAFT)
        self.assertEqual(result["state"],"HISTORICO_HEAD_MUDOU")
        self.assertTrue(result["requires_new_audit"])
        self.assertFalse(result["canon_changed"])

    def test_duplicate_question_numbers_blocked(self):
        obj=qa_contract()
        obj["questions"][4]["number"]=4
        with self.assertRaises(GateError):
            verify_quiz_contract(obj,head=HEAD,draft_checkpoint=DRAFT)

    def test_40_answers_cannot_have_untraceable_sources(self):
        obj=qa_contract()
        obj["questions"][8]["sources"]=[{"kind":"DRIVE_PLANEJAMENTO","url":"https://example.com"}]
        with self.assertRaises(GateError):
            verify_quiz_contract(obj,head=HEAD,draft_checkpoint=DRAFT)

    def test_invalid_rascunho_state_blocked(self):
        with self.assertRaises(GateError):
            verify_quiz_contract(qa_contract(),head=HEAD,
                                 draft_checkpoint={"day":529,"canon_status":"CANONICO"})

    def test_no_independent_agents_in_roster(self):
        result=route(["PERSONAGENS"])
        self.assertEqual(result["declared_specialties"],37)
        self.assertEqual(result["director"],CHIEF)
        self.assertEqual(result["canon_changed"],False)


if __name__=="__main__":
    unittest.main()
