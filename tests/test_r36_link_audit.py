import unittest
from worldroot.r36_contextual import audit_and_enrich
from worldroot.semantic_queue import seal
class LinkAuditTest(unittest.TestCase):
    def fixture(self):
        lines=["Varo fala com Miren.","Varo chega."]
        rows=[{"original_id":1,"source":"episode:e","source_sha256":"s","line":1,"entity_id":"varo","field":"behavior","anchor_sha256":"a","anchor":lines[0]}]
        p={"event_id":"event","episode":"e","source_sha256":"s","source_status":"CLOSED","visibility":"PRIVADO_PERSONAGEM","line":1,"anchor":"Varo fala","summary_candidate":"Varo e Lucas","context":[{"line":i+1,"text":v} for i,v in enumerate(lines)],"candidate_rows":[{"original_id":1,"entity_id":"varo","field":"behavior","line":1,"anchor_sha256":"a","distance":0,"match":"EXACT_BASELINE"}]}
        p["packet_sha256"]=seal(p)
        records=[{"id":i,"name":n,"scope":"EDITORIAL"} for i,n in [("varo","Varo"),("miren","Miren"),("lucas","Lucas"),("varo2","Varo")]]
        return [p],rows,{"episode:e":("s",lines,"CLOSED")},records
    def reseal(self,p):
        p.pop("packet_sha256");p["packet_sha256"]=seal(p)
    def test_valid_links_and_ambiguous_alias(self):
        a,m=audit_and_enrich(*self.fixture())
        self.assertEqual(m["ledger_links_verified"],1)
        v=next(x for x in a[0]["registry_mentions"] if x["normalized_alias"]=="varo")
        self.assertEqual(v["candidate_ids"],["varo","varo2"]);self.assertTrue(v["ambiguous"])
        self.assertFalse(a[0]["canon_promotion"])
    def test_summary_only_is_not_source(self):
        a,m=audit_and_enrich(*self.fixture())
        v=next(x for x in a[0]["registry_mentions"] if x["normalized_alias"]=="lucas")
        self.assertEqual(v["tier"],"SUMMARY_ONLY");self.assertEqual(v["source_lines"],[])
    def test_context_tamper_even_if_resealed(self):
        p,r,s,d=self.fixture();p[0]["context"][0]["text"]="changed";self.reseal(p[0])
        with self.assertRaises(ValueError):audit_and_enrich(p,r,s,d)
    def test_candidate_tamper_even_if_resealed(self):
        p,r,s,d=self.fixture();p[0]["candidate_rows"][0]["entity_id"]="lucas";self.reseal(p[0])
        with self.assertRaises(ValueError):audit_and_enrich(p,r,s,d)
    def test_open_event_recovers_mentions(self):
        p,r,s,d=self.fixture();p[0]["candidate_rows"]=[];self.reseal(p[0])
        a,m=audit_and_enrich(p,r,s,d)
        self.assertEqual(m["open_events_with_source_mentions"],1);self.assertEqual(a[0]["route"],"REGISTRY_MENTION_REVIEW")
    def test_no_candidates_from_summary_only(self):
        p,r,s,d=self.fixture();p[0]["candidate_rows"]=[];self.reseal(p[0])
        a,m=audit_and_enrich(p,r,s,[d[2]])
        self.assertEqual(m["still_open_events"],1)

    def test_heading_anchor_uses_next_scene_not_previous(self):
        lines=["Miren ficou atrás.","## XXV — retorno","","**DIA 548 · 16h19 — ESTRADA**","","Lucas retornava.","---","Varo chegou."]
        p={"event_id":"e","episode":"e","source_sha256":"s","source_status":"CLOSED","visibility":"PRIVADO_PERSONAGEM","line":2,"anchor":lines[1],"summary_candidate":"Lucas retornava","context":[{"line":1,"text":lines[0]},{"line":2,"text":lines[1]},{"line":3,"text":lines[2]}],"candidate_rows":[]}
        p["packet_sha256"]=seal(p)
        rec=[{"id":i,"name":i,"scope":"EDITORIAL"} for i in ("Lucas","Miren","Varo")]
        a,m=audit_and_enrich([p],[],{"episode:e":("s",lines,"CLOSED")},rec)
        self.assertEqual(m["heading_anchor_windows_corrected"],1)
        self.assertEqual(m["open_events_with_source_mentions"],1)
        self.assertEqual([x["candidate_ids"] for x in a[0]["registry_mentions"]],[["Lucas"]])
        self.assertEqual(a[0]["registry_mentions"][0]["source_lines"],[6])

    def test_plot_alias_is_not_another_person(self):
        p,r,s,d=self.fixture()
        d=[x for x in d if x["id"]!="varo2"]+[{"id":"plot:varo","name":"Varo","scope":"EDITORIAL"}]
        a,m=audit_and_enrich(p,r,s,d)
        v=next(x for x in a[0]["registry_mentions"] if x["normalized_alias"]=="varo")
        self.assertEqual(v["entity_candidate_ids"],["varo"])
        self.assertEqual(v["plot_reference_ids"],["plot:varo"])
        self.assertTrue(v["ambiguous"])
        self.assertEqual(m["entity_plot_groups"],1)
        self.assertFalse(a[0]["semantic_certification"])
    def test_homonym_remains_unresolved(self):
        a,m=audit_and_enrich(*self.fixture())
        v=next(x for x in a[0]["registry_mentions"] if x["normalized_alias"]=="varo")
        self.assertEqual(v["identity_route"],"MULTIPLE_ENTITY_IDS_REVIEW_REQUIRED")
        self.assertEqual(m["multiple_entity_groups"],1)
