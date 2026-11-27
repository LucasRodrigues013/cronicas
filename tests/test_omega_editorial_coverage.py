"""OMEGA-005: context representation is not editorial execution."""
import unittest
from worldroot.editorial_guard import compact_brief, load_policy, quick_preflight
from worldroot.literary_revision import build_live_brief

HEAD=dict(book="Livro VI",chapter=9,part="I",day=579,episode_id="fixture",sequence=50)

class OmegaEditorialCoverage(unittest.TestCase):
    def setUp(self):
        self.policy=load_policy()

    def verify_coverage(self, brief, budget):
        self.assertIn("coverage",brief)
        c=brief["coverage"]
        active={r["id"] for r in self.policy["rules"] if r["active"]}
        represented=set(c["represented_rule_ids"])
        self.assertEqual(set(c["active_rule_ids"]),active)
        self.assertEqual(represented,set(c["literal_rule_ids"])|set(c["summary_rule_ids"]))
        self.assertEqual(represented|set(c["unrepresented_rule_ids"]),active)
        self.assertFalse(represented&set(c["unrepresented_rule_ids"]))
        self.assertTrue(set(c["omitted_budget_rule_ids"])<=active-represented)
        self.assertEqual(c["evaluated_rule_ids"],[])
        self.assertFalse(c["application_certified"])
        self.assertLessEqual(len(brief["text"]),budget)
        self.assertEqual(c["rendered_chars"],len(brief["text"]))
        self.assertEqual(c["budget_chars"],budget)
        for rid in c["literal_rule_ids"]:
            directive=next(r["directive"] for r in self.policy["rules"] if r["id"]==rid)
            self.assertIn(rid+": "+directive,brief["text"])
        for block in c["represented_blocks"]:
            self.assertIn(block["text"],brief["text"])
        self.assertEqual(brief["selected_rule_ids_semantics"],"LEGACY_CANDIDATES_NOT_APPLICATION")
        return c

    def test_live_budget_and_omission(self):
        short=build_live_brief(HEAD,self.policy,900)
        c=self.verify_coverage(short,900)
        long=self.verify_coverage(build_live_brief(HEAD,self.policy,4000),4000)
        self.assertTrue(c["omitted_budget_rule_ids"])
        self.assertTrue(set(c["represented_rule_ids"])<set(long["represented_rule_ids"]))
        self.assertIn("GÊNESE",short["text"])
        self.assertIn("planejamento não é fato narrado",short["text"])

    def test_static_budget_and_legacy_ids(self):
        b=compact_brief(self.policy,scene_tags=("ROMANCE",),max_chars=320)
        c=self.verify_coverage(b,320)
        self.assertTrue(c["omitted_budget_rule_ids"])
        self.assertTrue(set(b["selected_rule_ids"])-set(c["represented_rule_ids"]))
        self.assertIn("planejamento não vira cânone",b["text"])
        self.verify_coverage(compact_brief(self.policy,scene_tags=("ROMANCE",),max_chars=1750),1750)

    def test_exact_literal_and_disabled_policy(self):
        b=compact_brief(self.policy,scene_tags=("ROMANCE",),max_chars=12000)
        c=self.verify_coverage(b,12000)
        self.assertTrue(c["literal_rule_ids"])
        for r in self.policy["rules"]:
            if r["id"]=="P110":r["active"]=False
        b=build_live_brief(HEAD,self.policy,4000)
        c=self.verify_coverage(b,4000)
        self.assertNotIn("P110",c["active_rule_ids"])
        self.assertNotIn("P110",c["represented_rule_ids"])

    def test_preflight_is_not_generation_evaluation(self):
        out=quick_preflight("A scene.",policy=self.policy,head=HEAD)
        self.assertIn("editorial_context_coverage",out)
        c=out["editorial_context_coverage"]
        self.assertEqual(out["consulted_rules"],c["represented_rule_ids"])
        self.assertEqual(out["evaluated_rule_ids"],["P01"])
        self.assertFalse(out["generation_evaluated"])
        self.assertFalse(out["semantic_certification"])
        self.assertEqual(c["evaluated_rule_ids"],[])

    def test_live_identity_and_authority_fail_closed(self):
        b=build_live_brief(HEAD,self.policy,550)
        self.verify_coverage(b,550)
        for phrase in ("D579","fixture","GÊNESE","planejamento não é fato narrado"):
            self.assertIn(phrase,b["text"])
        self.assertNotIn("D538",b["text"])
