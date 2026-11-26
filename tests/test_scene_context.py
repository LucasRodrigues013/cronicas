import unittest
from worldroot.scene_context import build,pending_fronts

class SceneContextTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"id":"city","name":"Três Arcos","domains":["Atlas mundial"]},{"id":"other","name":"Halvern","domains":["Atlas mundial"]},{"id":"varo","name":"Varo","domains":["Personagens"],"natural_profile":{"fields":{"voice":{"value":"preciso","status":"COMPLETADO","scope":"EDITORIAL"},"origin":{"value":"secret","status":"SEGREDO","scope":"AUTHOR_ONLY"},"knowledge":{"value":"secret","status":"CANONICO"}}}},{"id":"t1","name":"Tessa Arin","aliases":["Tessa"],"domains":["Personagens"]},{"id":"t2","name":"Tessa Maren","aliases":["Tessa"],"domains":["Personagens"]},{"id":"s","name":"Feitiço","domains":["Magia e poderes"],"scope":"GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE"}]
    def test_locality_privacy(self):
        req={"scene_plan":[{"scene":1,"purpose":"Varo em Três Arcos e Tessa"},{"scene":2,"purpose":"Halvern"}]}
        s=build(req,self.rows)["scenes"]
        self.assertEqual(set(s[0]["direct_ids"]),{"city","varo"})
        self.assertEqual(s[0]["ambiguities"][0]["ids"],["t1","t2"])
        self.assertEqual(s[1]["direct_ids"],["other"])
        self.assertNotIn("secret",str(s))
    def test_explicit_and_link_budget(self):
        req={"scene_plan":[{"scene":1,"purpose":"Tessa"}],"world_scope":[{"scene":1,"ids":["t2"]}]}
        s=build(req,self.rows,{"links":[{"from":"t2","to":"city","relation":"residence"},{"from":"t2","to":"other","relation":"secret","scope":"AUTHOR_ONLY"}]})["scenes"][0]
        self.assertEqual(s["direct_ids"],["t2"])
        self.assertEqual({r["id"] for r in s["records"]},{"t2","city"})
        self.assertEqual(s["ambiguities"],[])
    def test_missing_and_unknown_scope(self):
        req={"scene_plan":[{"scene":1,"purpose":"desconhecido"}]}
        self.assertTrue(build(req,self.rows)["scenes"][0]["needs_targeted_recovery"])
        with self.assertRaises(ValueError):build({**req,"world_scope":[{"scene":1,"ids":["missing"]}]},self.rows)
        self.assertEqual(pending_fronts(None,579)["status"],"GRAPH_NOT_READY")

    def test_place_plot_alias_is_not_a_place_collision(self):
        rows=self.rows+[{"id":"plot-halvern","name":"Trama de Halvern","aliases":["Halvern"],"domains":["História e mistérios"]}]
        result=build({"scene_plan":[{"scene":1,"purpose":"Halvern"}]},rows)["scenes"][0]
        self.assertEqual(result["direct_ids"],["other"])
        self.assertEqual(result["ambiguities"],[])
        rows.append({"id":"other2","name":"Outra Halvern","aliases":["Halvern"],"domains":["Atlas mundial"]})
        result=build({"scene_plan":[{"scene":1,"purpose":"Halvern"}]},rows)["scenes"][0]
        self.assertEqual(result["direct_ids"],[])
        self.assertTrue(result["ambiguities"])
