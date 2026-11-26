import json,tempfile,unittest,copy
from pathlib import Path
from worldroot.character_design import REGISTRY,IDS,load_design,source_bodies,candidate_sources,selected_design,bind_request,verify_binding,valid_requirement,design_requirement_matches_card
class CharacterDesignTests(unittest.TestCase):
    def setup(self,root):
        rows=[]
        for i in IDS:
            p={k:"fixture" for k in ("name","face","eyes","hair","build","bust","hips","legs","wardrobe","role_and_presence","effect_on_others","skin")}
            p.update(id=i,name=i,age={"years":None,"status":"UNRESOLVED"})
            if i=="lyra":p.update(name="Lira Selen Vareth",age={"years":18,"status":"AUTHOR_DEFINED"})
            if i=="miren":p.update(name="Miren",skin="Clara, sem sardas",age={"years":29,"status":"ADULT_CONFIRMED_NUMERIC_DESIGN_PROPOSAL"})
            rows.append(p)
        path=root/REGISTRY;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps({"schema":"worldroot-female-character-design-v2","project":"CRONICAS_DE_UM_NOVO_MUNDO","status":"ACTIVE_EDITORIAL_VISUAL_DIRECTION","profiles":rows}))
        return path
    def test_all_profiles_and_distinct_aliases(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup(root)
            self.assertEqual(len(load_design(root)["profiles"]),21)
            self.assertEqual([p["id"] for p in selected_design(root,["Lira"])["profiles"]],["lyra"])
            self.assertEqual([p["id"] for p in selected_design(root,["Lysa"])["profiles"]],["lysa"])
    def test_age_source_only_known(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup(root);b=source_bodies(load_design(root))
            self.assertIn("18",b["AUTHOR_DESIGN:lyra:age"])
            self.assertNotIn("29",b["AUTHOR_DESIGN:miren:age"])
            self.assertNotIn("AUTHOR_DESIGN:astra:age",b)
    def test_wrong_entity_or_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup(root);data=load_design(root)
            q={"role":"AuthorDesign","domain":"identity","design_field":"age","entity":"lyra","query":"Lira idade"}
            self.assertTrue(valid_requirement(q,{"source":"AUTHOR_DESIGN:lyra:age"},data))
            self.assertFalse(valid_requirement(q,{"source":"AUTHOR_DESIGN:lysa:age"},data))
            self.assertFalse(valid_requirement(q,{"source":"AUTHOR_DESIGN:lyra:appearance"},data))
    def test_immutable_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=self.setup(root);req={"r34_intent":{"characters":[{"name":"Miren"}]}}
            packet={"character_design":bind_request(root,req)}
            self.assertEqual(len(verify_binding(root,req,packet)["profiles"]),1)
            obj=json.loads(path.read_text());obj["profiles"][0]["hair"]="changed";path.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):verify_binding(root,req,packet)
    def test_missing_registry_legacy(self):
        with tempfile.TemporaryDirectory() as d:self.assertIsNone(load_design(Path(d)))
    def test_miren_correction_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.setup(root);obj=json.loads(p.read_text());obj["profiles"][0]["skin"]="sardas";p.write_text(json.dumps(obj))
            with self.assertRaises(ValueError):load_design(root)
    def test_candidate_literal_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup(root);r=candidate_sources(load_design(root),"Lira idade")
            self.assertEqual(len(r),1);self.assertEqual(len(r[0]["sources"]),2)
            self.assertTrue(all(s["role"]=="AuthorDesign" for s in r[0]["sources"]))
    def test_no_cross_character_age_binding(self):
        req={"entity":"lyra","design_field":"age"}
        review={"source":"AUTHOR_DESIGN:lyra:age"}
        self.assertTrue(design_requirement_matches_card(req,review,"Lira Selen Vareth","age"))
        self.assertFalse(design_requirement_matches_card(req,review,"Lysa","age"))
        self.assertFalse(design_requirement_matches_card(req,review,"Lira","appearance"))
