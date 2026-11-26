import copy,unittest
from worldroot.r35_refinement import AXES,rhythm_signals,validate_refinement_plan,validate_refinement_review
from worldroot.r35_longform import validate_plan

class RefinementTests(unittest.TestCase):
    def fixture(self):
        a="O viajante chegou e viu a ponte dourada."
        b="A amiga sorriu e chamou os demais para perto."
        prose="## I — A ponte\n\n"+a+"\n\n"+b
        axes={k:{"aim":"O objetivo contextual desta revisão é "+k,"reference_id":"a","scenes":[1]} for k in AXES}
        review={k:{"reference_id":"a","result":"retained","assessment":"A leitura contextual explica este aspecto "+k,"contrast":"A referência possui uma situação narrativa distinta.","moments":[{"scene":1,"evidence":a,"effect":"Mostra a experiência concreta do viajante."},{"scene":1,"evidence":b,"effect":"Mostra a reação independente da amiga."}]} for k in AXES}
        req={"scene_plan":[{"scene":1}],"r34_intent":{"characters":[{"name":"Amiga"}]},"r35_plan":{"references":["a","b"],"refinement":{"schema":"worldroot-r35-refinement-v1","axes":axes,"identity_recovery":[{"character":"Amiga","source_review":"A fonte descreve a presença da personagem.","voice_direction":"A personagem fala de maneira direta.","trait_gaps":"A aparência permanece em aberto por enquanto."}]}}}
        payload={"prose":prose,"r35_review":{"refinement":{"schema":"worldroot-r35-refinement-review-v1","axes":review,"no_artificial_fragmentation":True,"no_administrative_padding":True,"no_forced_conflict_or_romance":True}}}
        return req,payload
    def test_plan_and_review(self):
        r,p=self.fixture()
        self.assertEqual(validate_refinement_plan(r)["axes"],5)
        self.assertFalse(validate_refinement_review(r,p)["semantic_certification"])
    def test_roster_gaps(self):
        r,p=self.fixture();r["r35_plan"]["refinement"]["identity_recovery"]=[]
        with self.assertRaisesRegex(ValueError,"roster"):validate_refinement_plan(r)
    def test_no_repeated_generic_aim(self):
        r,p=self.fixture();x=r["r35_plan"]["refinement"]["axes"];x["cadence"]["aim"]=x["exposition"]["aim"]
        with self.assertRaisesRegex(ValueError,"distinct editorial aim"):validate_refinement_plan(r)
    def test_missing_axis(self):
        r,p=self.fixture();del r["r35_plan"]["refinement"]["axes"]["wonder_payoff"]
        with self.assertRaises(ValueError):validate_refinement_plan(r)
    def test_missing_literal_evidence(self):
        r,p=self.fixture();p["r35_review"]["refinement"]["axes"]["emotion_adult"]["moments"][0]["evidence"]="A frase não existe na narrativa."
        with self.assertRaisesRegex(ValueError,"grounded"):validate_refinement_review(r,p)
    def test_duplicate_literal_evidence(self):
        r,p=self.fixture();v=p["r35_review"]["refinement"]["axes"]["voice_identity"];v["moments"][1]=copy.deepcopy(v["moments"][0])
        with self.assertRaisesRegex(ValueError,"repeats"):validate_refinement_review(r,p)
    def test_compressed_prose_requires_context_not_quota(self):
        r,p=self.fixture();p["prose"]+="\n\n"+"Uma nova frase com muitos detalhes e explicações. "*30
        self.assertEqual(rhythm_signals(p["prose"])["cadence_review_signal"],"REVIEW_COMPRESSION")
        with self.assertRaisesRegex(ValueError,"cadence gap"):validate_refinement_review(r,p)
        p["r35_review"]["refinement"]["axes"]["cadence"]["density_response"]="A densidade foi revisada na passagem de descrição contínua."
        self.assertTrue(validate_refinement_review(r,p)["signals"]["advisory_only"])
    def test_no_forced_story_elements(self):
        r,p=self.fixture();p["r35_review"]["refinement"]["no_forced_conflict_or_romance"]=False
        with self.assertRaisesRegex(ValueError,"boundaries"):validate_refinement_review(r,p)
