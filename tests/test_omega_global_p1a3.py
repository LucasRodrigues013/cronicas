"""Synthetic safety regressions, never narrative data."""
import unittest,copy
from worldroot.omega_global_p1a3 import boundary,uniqueness,route,expansion
class P1A3(unittest.TestCase):
    def setUp(self):
        self.p=dict(id="parent",source="synthetic",source_sha256="x",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",source_role="Response",visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",modality="NARRATED",scope="LOCAL_NARRATION",interval=[1,5],subject="test",original_field="apparent_age",day=1)
        self.c=dict(id="child",target_id=3,parent_id="parent",source="synthetic",source_sha256="x",authority=self.p["authority"],source_role="Response",visibility=self.p["visibility"],modality="NARRATED",scope=self.p["scope"],interval=[2,2],current_state=False,knowledge_injection=False,promotion=False,independent_review=False,identity_resolved=False,state_before=None,state_after=None,value=0,unknown_reason=None,predicate="appearance_age",subject="test",day=1,preliminary_verdict="PARTIAL",claim_kind="OBSERVED_EVENT")
    def reject(self,**kw):
        with self.assertRaises(ValueError):boundary({**self.c,**kw},self.p)
    def test_zero_is_explicit(self):self.assertEqual(boundary(self.c,self.p)["value"],0)
    def test_unknown_needs_reason(self):self.reject(value=None)
    def test_unknown_not_zero(self):self.reject(value=0,unknown_reason="unknown")
    def test_unknown_not_supported(self):self.reject(value=None,unknown_reason="unknown",preliminary_verdict="SUPPORTED")
    def test_explicit_unknown(self):boundary({**self.c,"value":None,"unknown_reason":"unknown","preliminary_verdict":"UNKNOWN"},self.p)
    def test_promotion(self):self.reject(promotion=True)
    def test_current_state(self):self.reject(current_state=True)
    def test_injection(self):self.reject(knowledge_injection=True)
    def test_identity(self):self.reject(identity_resolved=True)
    def test_false_transition(self):self.reject(state_after="synthetic")
    def test_appearance_age(self):self.reject(predicate="biological_age")
    def test_scope(self):self.reject(visibility="WORLD")
    def test_subject(self):self.reject(subject="other")
    def test_time(self):self.reject(day=579)
    def test_interval(self):self.reject(interval=[0,2])
    def test_report_plan_dream(self):
        for modality,scope in [("REPORT","ATTRIBUTED_TESTIMONY_NOT_EXTERNAL_FACT"),("PLAN","INTENT_NOT_EXECUTION"),("DRAFT","EXPERIMENTAL_NOT_CANON"),("HYPOTHESIS","CONDITIONAL_NOT_CONFIRMED")]:
            with self.subTest(modality=modality):
                p={**self.p,"modality":modality,"scope":scope}
                c={**self.c,"modality":modality,"scope":scope}
                with self.assertRaises(ValueError):boundary(c,p)
                with self.assertRaises(ValueError):boundary(self.c,p)
        p={**self.p,"visibility":"READER_ONLY_NO_CHARACTER_INJECTION"}
        with self.assertRaises(ValueError):boundary(self.c,p)
    def test_duplicate(self):
        with self.assertRaises(ValueError):uniqueness([self.c,self.c])
        with self.assertRaises(ValueError):uniqueness([self.c],existing=[3])
    def test_duplicate_locator(self):
        with self.assertRaises(ValueError):uniqueness([self.c,{**self.c,"id":"other","target_id":4}])
    def test_routing_and_batch(self):
        row=dict(id="one",macro=2,source="synthetic",interval=[1680,1685],role="Response",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",disposition="PENDING_ATOMIC_REVIEW",axes=[11])
        self.assertEqual(route(row),"DEEP_SEMANTIC_REVIEW")
        self.assertEqual(route({**row,"visibility":"READER_ONLY_NO_CHARACTER_INJECTION"}),"CRITICAL_SCOPE")
        self.assertEqual(route({**row,"role":"Metadata"}),"STRUCTURAL_METADATA")
        self.assertEqual(route({**row,"role":"Prompt"}),"AUTHORITY_NON_EVENT_REVIEW")
        self.assertEqual(route({**row,"axes":[8]}),"STANDARD_SEMANTIC_REVIEW")
        batches,routes=expansion([row,{**row,"id":"two","interval":[1686,1692]},{**row,"id":"three","macro":3}],{"one"},max_records=1)
        self.assertEqual([x["count"] for x in batches],[1,1])
        self.assertEqual(sum(routes.values()),2)
    def test_oversize_not_lost(self):
        row=dict(id="one",macro=2,source="synthetic",interval=[1,100],role="Response",authority="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED",visibility="EDITORIAL_ONLY_NO_CHARACTER_INJECTION",disposition="PENDING_ATOMIC_REVIEW",axes=[8])
        p,_=expansion([row],set(),max_lines=10)
        self.assertTrue(p[0]["oversize_single"])
if __name__=="__main__":unittest.main()
