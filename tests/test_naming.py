import unittest
from worldroot.naming import propose,validate,catalog,policy_packet

class NamingTest(unittest.TestCase):
    def card(self):
        p=propose("thalor","chr-new",given="Lena")
        p.update(basis="New character design from Thalor",species_id="species:human",birth_region_id="thalor",residence_region_id="tres-arcos",citizenship_region_id="tres-arcos")
        return {"id":"chr-new","name":p["full_name"],"domains":["Personagens"],"profile":{"name_identity":p}}
    def test_deterministic_and_distinct(self):
        a=propose("elfic","id")
        self.assertEqual(a,propose("elfic","id"))
        self.assertNotEqual(a["full_name"],propose("elfic","id",[a["full_name"]])["full_name"])
        self.assertGreaterEqual(len(catalog()["profiles"]),15)
        self.assertTrue(policy_packet()["preserve_legacy_names"])
    def test_validate(self):
        c=self.card()
        self.assertEqual(validate(c,[],{"thalor","tres-arcos"},{"species:human"})["birth_region_id"],"thalor")
        with self.assertRaises(ValueError):validate(c,[{"id":"old","name":c["name"],"domains":["Personagens"]}],{"thalor","tres-arcos"},{"species:human"})
        c["profile"]["name_identity"]["additional_name"]=""
        with self.assertRaises(ValueError):validate(c,[],{"thalor","tres-arcos"},{"species:human"})
    def test_mononym_explicit(self):
        c=self.card();p=c["profile"]["name_identity"]
        p.update(full_name="Nora",given_name="Nora",additional_name="",exception="CHOSEN_CREATION_NAME",exception_reason="Voluntary chosen creation identity");c["name"]="Nora"
        self.assertEqual(validate(c,[],{"thalor","tres-arcos"},{"species:human"})["full_name"],"Nora")
        del p["exception_reason"]
        with self.assertRaises(ValueError):validate(c,[],{"thalor","tres-arcos"},{"species:human"})
    def test_culture_not_species_or_residence(self):
        c=self.card();p=c["profile"]["name_identity"];p["culture_id"]="elfic";p["species_id"]="species:human"
        self.assertEqual(validate(c,[],{"thalor","tres-arcos"},{"species:human"})["culture_id"],"elfic")
        p["additional_kind"]="HOUSE"
        with self.assertRaises(ValueError):validate(c,[],{"thalor","tres-arcos"},{"species:human"})
