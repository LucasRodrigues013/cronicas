import unittest
from worldroot.r36_history_advisory import cues,eligible_lines,check_binding,seal
from worldroot.git_cycle import sha,canonical
class Advisory(unittest.TestCase):
    def test_epistemic_cues(self):
        self.assertEqual(cues("Estou estruturando a investigação."),("META",))
        self.assertIn("HYPOTHESIS_CUE",cues("Talvez pudesse partir."))
        self.assertIn("NEGATION_CUE",cues("Não possuía a chave."))
        self.assertIn("REPORT_OR_DIALOGUE",cues("— Ele disse que chegou."))
    def test_role_and_menu(self):
        lines=["## Prompt:","Ele avançou.","## Response:","A ponte abriu.","## Opções","Ele avançaria.","## Cena","Ela chegou."]
        self.assertEqual([n for n,_ in eligible_lines(lines,["Prompt"]*2+["Response"]*6)],[4,8])
    def test_binding(self):
        r={"head":{"sequence":50}};a={"request_sha256":sha(canonical(r)),"head_sha256":sha(canonical(r["head"])),"knowledge_injection":False,"canon_changed":False,"semantic_certification":False}
        a["advisory_sha256"]=seal(a);check_binding(r,a)
        a["knowledge_injection"]=True
        with self.assertRaises(ValueError):check_binding(r,a)
