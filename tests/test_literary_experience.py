import unittest
from pathlib import Path
from worldroot.literary_experience import measure,choice_prompt,choice_review,causal_review,_historical_anchor
from worldroot.living_world import match_reference,_normalized_body,_speaker_set

class R30Tests(unittest.TestCase):
    def test_editorial_language_not_generic_negation(self):
        self.assertEqual(measure("Lucas não gostava do chá.")["meta_phrases"],[])
        self.assertEqual(len(measure("Não era uma prova. Não significava uma aliança.")["meta_phrases"]),2)
        self.assertEqual(measure("A chuva tinha cheiro de terra.")["sensory_signals"]["olfato"],1)
    def test_choice_contract(self):
        self.assertIn("WORLDROOT R30",choice_prompt("LVI-C08-PI-D574",4))
        self.assertEqual(choice_review("## AS CINCO PORTAS\nWORLDROOT R27: opção 4")["stale_versions"],[27])
        with self.assertRaises(ValueError):choice_prompt("x",5,"")
    def test_causal_order(self):
        a="A ponte ruiu com a cheia."
        b="O viajante recuou para a margem."
        c={"cause_anchor":a,"effect_anchor":b,"consequence":"mudança de rota"}
        self.assertEqual(causal_review(a+"\n"+b,Path("."),{},[c])["status"],"ANCHORS_CHECKED")
        self.assertEqual(causal_review(b+"\n"+a,Path("."),{},[c])["status"],"REVIEW")
    def test_literal_role_and_unique_anchor(self):
        text="## Prompt:\nPedido original.\n## Response:\nUma cena longa e verdadeira."
        s={"x":({"source_name":"x","sha256":"a"},text)}
        self.assertIsNotNone(_historical_anchor(s,{"source_name":"x","anchor":"Uma cena longa e verdadeira.","role":"Response"}))
        self.assertIsNone(_historical_anchor(s,{"source_name":"x","anchor":"Uma cena longa e verdadeira.","role":"Prompt"}))
    def test_cached_derived_data(self):
        _normalized_body.cache_clear();_speaker_set.cache_clear()
        p="## I — Cena\n**LUCAS —** Oi.\nÉgide Interna."
        self.assertTrue(match_reference(p,["Égide"]))
        self.assertTrue(match_reference(p,["Lucas"]))
        self.assertGreaterEqual(_normalized_body.cache_info().hits,1)
        self.assertIn("lucas",_speaker_set(p))
        self.assertNotIn("lucas",_speaker_set(p.replace("LUCAS","MIREN")))
