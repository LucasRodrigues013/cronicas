import unittest,tempfile,sqlite3,hashlib
from unittest.mock import patch
from worldroot.r32_release import release_review
from worldroot.memory_continuity import DOMAINS
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
        for k in ("dossiers","inventory","power","relationships","plots","assets","historical_observations","events","knowledge","planning","unregistered_speaker_candidates"):data[k]={}
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
    def payload(self):
        packet=self.packet();rendered=render_choices(packet,"EP-001")
        head={"day":573}
        prose=rendered["body_declaration"]+"\n## I — A cena\n\nTexto."
        payload={"delivery_id":"EP-001","prose":prose,"full_text":prose+"\n"+rendered["markup"],"choices":[{"number":i,"title":"Path "+str(i),"is_special":i==4,"is_free":i==5} for i in range(1,6)]}
        payload["r32_review"]={"head":head,"prose_sha256":hashlib.sha256(prose.encode()).hexdigest(),"requirements":[{"id":"memory1","domain":"identity","critical":True,"query":"character identity"}],"domain_review":{k:{"applicable":k=="identity","reason":"reviewed"} for k in DOMAINS},"scene_requirements":[{"scene":1,"ids":["memory1"]}],"arc_packet":packet,"editorial_parity_reviewed":True,"reviewed":{}}
        return head,payload
    def test_release_rejects_low_coverage(self):
        head,p=self.payload()
        with patch("worldroot.r32_release.review_creation",return_value={"status":"RECOVER_BEFORE_RELEASE"}):
            with self.assertRaises(ValueError):release_review(Path("."),head,p)
    def test_release_accepts_structural_receipt(self):
        head,p=self.payload()
        with patch("worldroot.r32_release.review_creation",return_value={"status":"REVIEWED_EVIDENCE_THRESHOLD_MET"}):
            self.assertFalse(release_review(Path("."),head,p)["semantic_certification"])
    def test_release_rejects_changed_visible_options(self):
        head,p=self.payload();p["full_text"]=p["full_text"].replace("Path 4","Different")
        with self.assertRaises(ValueError):release_review(Path("."),head,p)
    def test_release_rejects_unmapped_requirement(self):
        head,p=self.payload();p["r32_review"]["scene_requirements"]=[]
        with self.assertRaises(ValueError):release_review(Path("."),head,p)
    def test_release_rejects_stale_head(self):
        head,p=self.payload()
        with self.assertRaises(ValueError):release_review(Path("."),{"day":574},p)
if __name__=="__main__":unittest.main()

