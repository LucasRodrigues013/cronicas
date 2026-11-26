import unittest
from worldroot.arquiteto import discover, field_tasks, validate_review, design_patch, stable, preparation_context, validate_legacy_recovery

class ArchitectTest(unittest.TestCase):
    def setUp(self):
        self.cards=[{"id":"t1","name":"Tessa Arin","aliases":["Tessa"]},{"id":"t2","name":"Tessa Maren","aliases":["Tessa"]}]
        self.prose="TESSA — Olá.\n**BEREN TOL —** Bom dia.\nLIVRO VI — Teste\nMULHER — Sim."
    def test_discovery_preserves_distinct(self):
        rows=discover(self.prose,"ep","CLOSED_PROSE",self.cards)
        self.assertEqual([r["kind"] for r in rows],["ALIAS_COLLISION","NEW_NAME_CANDIDATE","GENERIC_ROLE"])
        self.assertEqual(rows[0]["candidates"],["t1","t2"])
    def test_mixed_roles(self):
        rows=discover("## Prompt:\nTESSA — exemplo\n## Response:\nTESSA — resposta","old","LEGACY_MIXED",self.cards)
        self.assertEqual([r["source_role"] for r in rows],["AUTHOR_DIRECTION","LEGACY_MIXED"])
    def test_review(self):
        row=discover(self.prose,"ep","CLOSED_PROSE",self.cards)[0]
        review={"candidate_id":row["id"],"disposition":"SUPPORTED","entity_id":"t1","claim":"test claim","extractor":"e","reviewer":"r","reason":"fixture"}
        self.assertFalse(validate_review(row,review,self.prose)["semantic_certification"])
        for mod in ({"reviewer":"e"},{"entity_id":"fake"}):
            with self.assertRaises(ValueError):validate_review(row,{**review,**mod},self.prose)
        with self.assertRaises(ValueError):validate_review(row,review,self.prose+"changed")
    def test_protected_mixed(self):
        row=discover(self.prose,"old","LEGACY_MIXED",self.cards)[0]
        with self.assertRaises(ValueError):validate_review(row,{"candidate_id":row["id"],"disposition":"SUPPORTED","entity_id":"t1","claim":"x","extractor":"a","reviewer":"b","reason":"x"},self.prose)
    def card(self):
        def f(status,value):return {"status":status,"value":value,"scope":"EDITORIAL","origin":{"source":"fixture"},"justification":"fixture","checkpoint":"D1"}
        return {"id":"t1","fields":{"voice":f("PENDENTE_FONTE","unknown"),"identity":f("RECUPERADO","Tessa"),"location":f("PENDENTE_FONTE","unknown")}}
    def test_design_patch(self):
        card=self.card();proposal={"entity_id":"t1","field":"voice","base_card_sha256":stable(card),"basis_fields":["identity"],"value":"voz calma","reason":"fixture","designer":"a"}
        review={"proposal_sha256":stable(proposal),"verdict":"ACCEPT_PROSPECTIVE","reviewer":"b","reason":"fixture"}
        out=design_patch(card,proposal,review)
        self.assertEqual(out["fields"]["voice"]["status"],"COMPLETADO")
        self.assertEqual(card["fields"]["voice"]["status"],"PENDENTE_FONTE")
        self.assertEqual(len(field_tasks(card)),2)
        for mod in ({"field":"location"},{"base_card_sha256":"stale"},{"basis_fields":["voice"]}):
            p={**proposal,**mod}
            with self.assertRaises(ValueError):design_patch(card,p,{**review,"proposal_sha256":stable(p)})
    def test_no_overwrite(self):
        card=self.card();card["fields"]["voice"]["status"]="CANONICO"
        with self.assertRaises(ValueError):design_patch(card,{"entity_id":"t1","field":"voice"},{})

    def test_preparation_context(self):
        card=self.card();card["fields"]["knowledge"]={**card["fields"]["location"],"scope":"AUTHOR_ONLY"}
        result=preparation_context({"profiles":{"t1":card}},[{"name":"Tessa","ids":["t1"]},{"name":"unknown","ids":[]}])
        self.assertEqual(result["focal"][0]["route"],"RECOVER_PROFILE")
        self.assertEqual({t["field"] for t in result["focal"][0]["tasks"]},{"voice","location"})
        self.assertEqual(result["focal"][1]["route"],"NEW_OR_ALIAS_REVIEW")
        self.assertFalse(result["canon_promotion"])
    def test_legacy_recovery_only_candidate(self):
        body="## Response:\nTESSA — exemplo"
        row=discover(body,"old","LEGACY_MIXED",self.cards)[0]
        review={"candidate_id":row["id"],"disposition":"SUPPORTED_LEGACY","context_start":2,"context_end":2,"context":"TESSA — exemplo","source_class":"NARRATED_RESPONSE","target_status":"RECUPERADO","claim":"fixture","extractor":"e","role_reviewer":"r","semantic_reviewer":"s","reason":"fixture","entity_id":"t1"}
        self.assertFalse(validate_legacy_recovery(row,review,body)["semantic_certification"])
        for mod in ({"target_status":"CANONICO"},{"semantic_reviewer":"r"},{"context":"fake"}):
            with self.assertRaises(ValueError):validate_legacy_recovery(row,{**review,**mod},body)


    def test_legacy_alias_gap_recovery(self):
        from unittest.mock import patch
        from worldroot.memory_continuity import fusion
        calls=[]
        def retrieve(db,query,entity,topic,role,limit,strategy):
            calls.append(entity)
            if entity is not None:
                raise ValueError("Unknown entity")
            return {"hits":[{"id":1,"source":"fixture","role":"Response","line_start":1,"line_end":9}]}
        with patch("worldroot.memory_continuity.retrieve",side_effect=retrieve):
            out=fusion(None,"Orven",entity="orven",role="Response")
        self.assertEqual(out["status"],"CANDIDATES_ONLY")
        self.assertEqual(out["hits"][0]["id"],1)
        self.assertFalse(out["canon_changed"])
        self.assertIn(None,calls)
        with patch("worldroot.memory_continuity.retrieve",side_effect=ValueError("Unknown topic")):
            with self.assertRaisesRegex(ValueError,"Unknown topic"):
                fusion(None,"Orven",entity="orven")
