import unittest,tempfile,sqlite3
from pathlib import Path
from worldroot.memory_graph import locate,write_graph
from worldroot.experience_quality import render_choices,review_scores,CRITERIA
class R32Tests(unittest.TestCase):
    def packet(self):
        return {"options":[{"number":i,"track":"main" if i==2 else "secondary","arc_id":str(i),"title":"Path "+str(i),"promise":"Promise","reward":"Reward","risk":"Risk","next_link":"Next","unselected_progress":"Other","guaranteed_success":False,"combines_all":False} for i in range(1,5)],"free_action":True,"author_choice_recorded":False}
    def test_unique_anchor(self):
        self.assertEqual(locate("a\nb\nc","b")["line_start"],2)
        self.assertIsNone(locate("abc abc","abc"))
        self.assertIsNone(locate("abc","z"))
    def test_graph_integrity(self):
        data={"head":{"day":573},"nodes":[{"id":"a","kind":"character","name":"A"},{"id":"b","kind":"event","name":"B"}],"edges":[{"source":"a","target":"b","kind":"EXPLICIT_KNOWLEDGE","proof":{"day":573}}]}
        for k in ("dossiers","inventory","power","relationships","plots","assets","historical_observations","events","knowledge","planning"):data[k]={}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"graph.sqlite";write_graph(data,path)
            with sqlite3.connect(path) as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM edges").fetchone()[0],1)
                self.assertEqual(c.execute("PRAGMA integrity_check").fetchone()[0],"ok")
            with self.assertRaises(FileExistsError):write_graph(data,path)
    def test_equal_visual_treatment(self):
        r=render_choices(self.packet(),"EP-001")
        self.assertEqual(r["markup"].count('button block color="secondary" variant="outline"'),4)
        self.assertIn("4 — ESPECIAL",r["markup"])
        self.assertIn("AÇÃO LIVRE",r["markup"])
        self.assertIn("acaoLivre.trim()",r["markup"])
        self.assertIn("DIL.useState",r["body_declaration"])
    def test_no_dominant_route(self):
        p=self.packet();p["options"][3]["combines_all"]=True
        with self.assertRaises(ValueError):render_choices(p,"EP-001")
    def test_no_markup_injection(self):
        p=self.packet();p["options"][0]["title"]="<button>"
        with self.assertRaises(ValueError):render_choices(p,"EP-001")
    def test_review_requires_all_dimensions(self):
        self.assertEqual(review_scores({k:8 for k in CRITERIA})["mean"],8)
        with self.assertRaises(ValueError):review_scores({"continuity":10})
    def test_free_action_bound_to_original_episode(self):
        r=render_choices(self.packet(),"EP-001")
        self.assertEqual(r["markup"].count("EP-001"),5)
        self.assertNotIn("__FREE_TEXT__",r["markup"])
if __name__=="__main__":unittest.main()
