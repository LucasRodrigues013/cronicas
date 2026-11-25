import copy,json,unittest
from unittest.mock import patch
from worldroot.r34_experience import DIMENSIONS,validate_intent,validate_delivery,render_opening,identity_context
from worldroot.editorial_guard import POLICY_PATH
from worldroot.experience_quality import render_choices
from worldroot.literary_experience import choice_prompt,choice_review

class R34Tests(unittest.TestCase):
    def request(self):
        text=POLICY_PATH.read_text(encoding="utf-8")
        lines=text.splitlines()
        req=[];reviewed={};dims={}
        for name,rule in DIMENSIONS.items():
            i=next(i for i,l in enumerate(lines,1) if '"id": "'+rule+'"' in l)
            req.append({"id":name,"domain":"author_rule","critical":True,"role":"AuthorPolicy","query":rule})
            reviewed[name]={"source":"AUTHOR_POLICY","line_start":i,"line_end":i+2}
            dims[name]={"rule":rule,"requirement_id":name,"status":"planned","reason":"Contexto narrativo justifica aplicar esta direção.","scenes":[1]}
        req.append({"id":"hist","domain":"identity","critical":True,"query":"Referência histórica"})
        reviewed["hist"]={"source":"historic"}
        card={"name":"Pessoa","scenes":[1],"fields":{k:{"status":"unknown","reason":"Campo ainda não possui evidência suficiente."} for k in ("appearance","voice","relationship","age")}}
        card["fields"]["appearance"]={"status":"sourced","reason":"Identidade física registrada na fonte literal.","requirement_ids":["hist"]}
        return {"requirements":req,"reviewed":reviewed,"scene_plan":[{"scene":1,"ids":[r["id"] for r in req]}],"r34_intent":{"schema":"worldroot-r34-intent-v1","dimensions":dims,"characters":[card],"comparison":{"requirement_id":"hist","reason":"Comparar efeito com referência histórica pertinente."}}}
    def payload(self):
        prose="## I — Uma manhã\nPessoa ajeitou os cabelos negros.\nPessoa tomou a mão do amigo."
        d={k:{"status":"applied","reason":"Este trecho mostra uma escolha narrativa.","scene":1,"evidence":"Pessoa tomou a mão do amigo."} for k in DIMENSIONS}
        d["appearance"].update(evidence="Pessoa ajeitou os cabelos negros.",concrete_detail="cabelos negros",character="Pessoa")
        metadata={"book":"Livro VI","chapter":8,"part":"III","day":576}
        opening={"book_title":"LIVRO VI — AS COROAS PARTIDAS","chapter_title":"QUANDO O CONTINENTE DESPERTA","episode_title":"UMA MANHÃ","epigraph":"Uma nova manhã de teste.","calendar":"Dia 576 · Ano II","location":"Torre","fronts":"Três Arcos"}
        d["design"]["evidence"]="CRÔNICAS DE UM NOVO MUNDO · WORLDROOT R34"
        return {"metadata":metadata,"prose":prose,"full_text":render_opening(metadata,opening)+"\n"+prose,"r34_review":{"schema":"worldroot-r34-review-v1","opening":opening,"dimensions":d,"comparison_result":"Comparação revela maior atenção à identidade.","no_forced_scenes":True,"no_unsupported_traits":True}}
    def test_complete_intent(self):
        self.assertEqual(validate_intent(self.request())["dimensions"],7)
    def test_missing_appearance_rejected(self):
        r=self.request();del r["r34_intent"]["dimensions"]["appearance"]
        with self.assertRaises(ValueError):validate_intent(r)
    def test_collapsed_author_requirements_rejected(self):
        r=self.request();r["r34_intent"]["dimensions"]["appearance"]["requirement_id"]="relationships"
        with self.assertRaises(ValueError):validate_intent(r)
    def test_wrong_policy_anchor_rejected(self):
        r=self.request();r["reviewed"]["appearance"]=r["reviewed"]["relationships"]
        with self.assertRaises(ValueError):validate_intent(r)
    def test_unknown_is_not_source(self):
        r=self.request();r["r34_intent"]["characters"][0]["fields"]["age"]["requirement_ids"]=["hist"]
        with self.assertRaises(ValueError):validate_intent(r)
    def test_held_without_quota(self):
        r=self.request();r["r34_intent"]["dimensions"]["appearance"].update(status="held",scenes=[],reason="A cena não comporta descrição física pertinente.")
        self.assertEqual(validate_intent(r)["dimensions"],7)
    def test_held_planned_needs_changed_context(self):
        r=self.request();p=self.payload();p["r34_review"]["dimensions"]["appearance"]={"status":"held","reason":"O desenvolvimento mudou o foco narrativo."}
        with patch("worldroot.r34_experience.presentation_preflight",return_value={"errors":[]}):
            with self.assertRaises(ValueError):validate_delivery(r,p)
            p["r34_review"]["dimensions"]["appearance"]["changed_context"]="A urgência interrompeu o encontro planejado."
            self.assertFalse(validate_delivery(r,p)["semantic_certification"])
    def test_evidence_is_scene_bound(self):
        r=self.request();p=self.payload();p["r34_review"]["dimensions"]["appearance"]["scene"]=2
        with self.assertRaises(ValueError):validate_delivery(r,p)
    def test_physical_and_relationship_evidence_distinct(self):
        r=self.request();p=self.payload();p["r34_review"]["dimensions"]["appearance"]["evidence"]=p["r34_review"]["dimensions"]["relationships"]["evidence"]
        with self.assertRaises(ValueError):validate_delivery(r,p)
    def test_valid_review_does_not_certify_semantics(self):
        with patch("worldroot.r34_experience.presentation_preflight",return_value={"errors":[]}):
            self.assertFalse(validate_delivery(self.request(),self.payload())["semantic_certification"])
    def test_choice_version_preserves_legacy(self):
        self.assertIn("WORLDROOT R30",choice_prompt("EP-001",4))
        self.assertIn("WORLDROOT R34",choice_prompt("EP-001",4,revision=34))
        self.assertEqual(choice_review("## AS CINCO PORTAS\nWORLDROOT R34: opção",revision=34)["stale_versions"],[])
        packet={"options":[{"number":i,"track":"main" if i==1 else "secondary","arc_id":str(i),"title":"Path "+str(i),"promise":"Promise","reward":"Reward","risk":"Risk","next_link":"Next","unselected_progress":"Other","guaranteed_success":False,"combines_all":False} for i in range(1,5)],"free_action":True,"author_choice_recorded":False}
        old=render_choices(packet,"EP-001");new=render_choices(packet,"EP-001",revision=34)
        self.assertEqual(old["markup"].count("WORLDROOT R30"),5)
        self.assertEqual(new["markup"].count("WORLDROOT R34"),5)
        self.assertEqual(new["markup"].count('button block color="secondary" variant="outline"'),4)
        self.assertIn("O que está em jogo",new["markup"])
    def test_rendered_opening_rejects_changed_date(self):
        p=self.payload();o=p["r34_review"]["opening"];o["calendar"]="Dia 577 · Ano II"
        with self.assertRaises(ValueError):render_opening(p["metadata"],o)
    def test_rendered_opening_rejects_markup_injection(self):
        p=self.payload();p["r34_review"]["opening"]["epigraph"]="<button>invalid"
        with self.assertRaises(ValueError):render_opening(p["metadata"],p["r34_review"]["opening"])
    def test_rendered_opening_cannot_be_substituted(self):
        p=self.payload();p["full_text"]=p["full_text"].replace("UMA MANHÃ","OUTRA MANHÃ")
        with self.assertRaises(ValueError):validate_delivery(self.request(),p)
    def test_identity_context_keeps_candidates_and_unknowns(self):
        reg={"head":{"day":575},"characters":[{"id":"miren","observations":[{"field":"appearance","proof":{"line":1}}]}]}
        with patch("worldroot.literary_experience.source_registry",return_value=reg),patch("worldroot.history_index.read_verified_sources",return_value=({},[])),patch("worldroot.literary_experience._historical_anchor",return_value={"line":2,"role":"Response"}):
            result=identity_context(".",["miren","unknown"])
        self.assertTrue(result["characters"][0]["candidates"])
        self.assertTrue(all(x["state"]=="LITERAL_CANDIDATE_NOT_CANON" for x in result["characters"][0]["candidates"]))
        self.assertIn("age",result["characters"][0]["missing_fields"])
        self.assertFalse(result["characters"][0]["current_state_verified"])
        self.assertIn("appearance",result["characters"][1]["missing_fields"])
