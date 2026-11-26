import copy,hashlib,tempfile,unittest
from pathlib import Path
from worldroot.r35_longform import (metrics,profile,volume_check,validate_plan,validate_delivery,FOCUS,COMPARE,PROFILES)
from worldroot.r34_experience import render_opening
from worldroot.literary_experience import choice_prompt
from worldroot.experience_quality import render_choices
from worldroot.ledger import GateError

def long_prose(n=650):
    # Deliberately synthetic varied tokens, NOT a literary example.
    return "## I — Um encontro\n\n**DIA 579 · 06h00 — LOCAL**\n\n"+"\n\n".join(
        f"Pessoa {i} encontrou um caminho diferente para conversar com seus amigos enquanto observava o jardim e esperava." for i in range(n))+"\n\n**FIM DA PARTE I.**\n"
def plan():
    cards=[{"scene":1,"word_budget":10000,"experience":"Os amigos exploram um lugar novo.","reaction":"Cada um reage de modo individual.","payoff":"O passeio ganha um significado pessoal.","focus":list(FOCUS)}]
    return {"delivery_id":"LVI-C09-PI-D579-AUTHOR-SOURCE","scene_plan":[{"scene":1}],"requirements":[{"id":"a"},{"id":"b"}],"reviewed":{"a":{},"b":{}},"r34_intent":{"dimensions":{k:{"scenes":[1]} for k in FOCUS}},"r35_plan":{"schema":"worldroot-r35-plan-v1","part":"I","profile":"special","scene_cards":cards,"references":["a","b"],"cadence_intent":"Alternar pausas e falas com naturalidade.","adult_opportunity":"Recuperar idades e vínculos quando pertinentes.","epic_payoff":"Mostrar resultados antes da reação coletiva."}}
class R35Tests(unittest.TestCase):
    def test_profile_prioritizes_finale(self):
        self.assertEqual(profile("V",4),"finale")
        self.assertEqual(profile("I",4),"special")
        self.assertEqual(profile("II",1),"regular")
    def test_short_narrative_blocks_even_with_ui(self):
        text="## I — Cena\n\n**DIA 579 · 06h00 — LOCAL**\n\n**PESSOA —** A manhã começou.\n\n<box>"+("texto "*12000)+"</box>\n\n**FIM DA PARTE I**\n"+"fora "*20000
        self.assertEqual(metrics(text)["words"],3)
        self.assertEqual(volume_check(text,"I",1)["status"],"REVISE")
    def test_exact_old_style_heading(self):
        self.assertEqual(metrics("I — Cena\n\nDIA 1 · 06h00\n\nOlá mundo.\n\nENCERRAMENTO DA PARTE I\n\nFora.")["words"],2)
    def test_no_padded_repeated_paragraphs(self):
        prose="## I — Cena\n\n"+("\n\n".join(["A manhã estava silenciosa e todos os amigos esperavam por uma resposta muito importante."]*1000))
        self.assertGreater(metrics(prose)["words"],8800)
        self.assertIn("R35_PADDING"," ".join(volume_check(prose,"I",1)["issues"]))
    def test_no_short_line_padding(self):
        prose="## I — Cena\n\n"+("\n\n".join(["Uma pausa e nada mais."]*2000))
        self.assertIn("R35_PADDING"," ".join(volume_check(prose,"I",1)["issues"]))
    def test_long_synthetic_volume(self):
        self.assertEqual(volume_check(long_prose(),"I",4)["status"],"STRUCTURAL_VOLUME_OK")
        self.assertEqual(volume_check(long_prose(550),"V",4)["status"],"REVISE")
    def test_author_exception_only_explicit(self):
        p="## I — Cena\n\nUma resposta foi dada."
        self.assertEqual(volume_check(p,"I",1,"Pode ficar curto")["status"],"REVISE")
        self.assertEqual(volume_check(p,"I",1,"AUTORIZO PARTE CURTA: Quero uma transição breve nesta ocasião")["status"],"STRUCTURAL_VOLUME_OK")
        self.assertFalse(volume_check(p,"I",1,"AUTORIZO PARTE CURTA: sim")["exception_authorized"])
    def test_plan_floor_and_profile(self):
        p=plan();self.assertEqual(validate_plan(p,{"option":4})["floor"],9500)
        p["r35_plan"]["scene_cards"][0]["word_budget"]=3500
        with self.assertRaises(ValueError):validate_plan(p,{"option":4})
    def test_plan_cannot_downgrade_finale(self):
        p=plan();p["delivery_id"]="LVI-C09-PV-D583-AUTHOR-SOURCE"
        with self.assertRaises(ValueError):validate_plan(p,{"option":4})
    def test_plan_no_lost_adult_opportunity(self):
        p=plan();p["r35_plan"]["scene_cards"][0]["focus"].remove("appearance")
        with self.assertRaises(ValueError):validate_plan(p,{"option":4})
    def test_plan_requires_two_references(self):
        p=plan();p["r35_plan"]["references"]=["a","a"]
        with self.assertRaises(ValueError):validate_plan(p,{"option":4})
    def fixture(self,root):
        req=plan();text=long_prose();id=req["delivery_id"]
        paragraphs=[x for x in text.split("\n\n") if x.startswith("Pessoa ")]
        stages=[];chunks=[text[:len(text)//2],text[len(text)//2:]]
        for i,s in enumerate(chunks,1):
            path=f"production/{id}/segments/{i:02d}.md";target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(s.encode())
            stages.append({"part":i,"path":path,"sha256":hashlib.sha256(s.encode()).hexdigest()})
        assessment="A revisão contextual compara ação e consequência."
        review={"schema":"worldroot-r35-review-v1","scenes":[{"scene":1,"planned_scene":1,"beats":dict(zip(("experience","reaction","payoff"),paragraphs[:3])),"assessment":assessment}],"opportunities":{k:{"status":"applied","assessment":assessment,"moments":[{"scene":1,"evidence":paragraphs[3],"effect":assessment},{"scene":1,"evidence":paragraphs[4],"effect":assessment}]} for k in FOCUS},"comparison":{k:{"reference_id":"a","assessment":assessment,"result":"retained"} for k in COMPARE},"no_padding":True,"no_condensed_key_events":True}
        return req,{"metadata":{"part":"I","worldroot_revision":35},"delivery_id":id,"prose":text,"full_text":text+"\nUI","longform_segments":stages,"r34_review":{"dimensions":{k:{"status":"applied"} for k in FOCUS}},"r35_review":review}
    def test_real_segment_files_full_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root)
            report=validate_delivery(root,req,p,{"option":4})
            self.assertTrue(report["segments"]["verified"]);self.assertFalse(report["semantic_certification"])
    def test_short_old_style_blocked_at_release(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);p["prose"]="## I — Cena\n\nPoucas palavras.";p["full_text"]=p["prose"]
            with self.assertRaisesRegex(ValueError,"R35_DEPTH"):validate_delivery(root,req,p,{"option":4})
    def test_incomplete_reader_text_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);p["full_text"]=p["prose"][:1000]
            with self.assertRaisesRegex(ValueError,"reader text"):validate_delivery(root,req,p,{"option":4})
    def test_missing_staged_segment_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);(root/p["longform_segments"][1]["path"]).unlink()
            with self.assertRaises(GateError):validate_delivery(root,req,p,{"option":4})
    def test_no_single_anchor_appearance(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);p["r35_review"]["opportunities"]["appearance"]["moments"]=p["r35_review"]["opportunities"]["appearance"]["moments"][:1]
            with self.assertRaisesRegex(ValueError,"more than one moment"):validate_delivery(root,req,p,{"option":4})
    def test_no_unresolved_regression(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);p["r35_review"]["comparison"]["emotion"]["result"]="regressed"
            with self.assertRaisesRegex(ValueError,"regression"):validate_delivery(root,req,p,{"option":4})
    def test_distinct_reaction_beats(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);req,p=self.fixture(root);row=p["r35_review"]["scenes"][0]["beats"];row["reaction"]=row["experience"]
            with self.assertRaisesRegex(ValueError,"distinct literal"):validate_delivery(root,req,p,{"option":4})
    def test_versioned_header_and_choice(self):
        self.assertIn("WORLDROOT R30",choice_prompt("EP-001",1))
        self.assertIn("WORLDROOT R34",choice_prompt("EP-001",1,revision=34))
        self.assertIn("WORLDROOT R35",choice_prompt("EP-001",1,revision=35))
        meta={"book":"Livro VI","chapter":9,"part":"I","day":579,"worldroot_revision":35}
        opening={"book_title":"LIVRO VI — TESTE","chapter_title":"TESTE","episode_title":"TESTE","epigraph":"Teste","calendar":"Dia 579 · Ano II","location":"Local","fronts":"Frentes"}
        self.assertIn("WORLDROOT R35",render_opening(meta,opening))
        meta["worldroot_revision"]=34;self.assertIn("WORLDROOT R34",render_opening(meta,opening))
