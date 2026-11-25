import unittest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch
from worldroot.deep_recovery import sections,windows,build,retrieve,norm,verify_manifest

class DeepRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"archive"
        self.root.mkdir()
        self.db=Path(self.tmp.name)/"derived.sqlite"
        self.body="header\n## Prompt:\nMiren sente ciúmes de Serís?\n## Response:\nMiren é alta, esguia.\nSerís Daum tem olhos cinzentos.\n## Prompt:\nAERÚN inspirado em Apple Park.\n"
        self.sources=({"sources":[]},[({"source_name":"synthetic.txt","sha256":"a"*64},self.body)])
    def make(self):
        with patch("worldroot.deep_recovery.read_verified_sources",return_value=self.sources):
            return build(self.root,self.db)
    def test_role_boundaries(self):
        result=list(sections(self.body))
        self.assertEqual([r[0] for r in result],["EXPORT_METADATA","Prompt","Response","Prompt"])
        self.assertEqual("".join("".join(r[2]) for r in result),self.body)
    def test_every_line_covered(self):
        self.assertEqual(set(range(1,len(self.body.splitlines())+1)),{n for _,a,b,_ in windows(self.body) for n in range(a,b+1)})
    def test_no_cross_role(self):
        self.assertTrue(all(anchor.count("## ")<=1 for _,_,_,anchor in windows(self.body)))
    def test_accent(self):
        self.assertEqual(norm("CÍRAN"),"ciran")
    def test_build_and_retrieve(self):
        self.assertFalse(self.make()["canon_changed"])
        r=retrieve(self.db,"Miren esguia",entity="miren",topic="appearance",role="Response")
        self.assertTrue(r["hits"]); self.assertFalse(r["semantic_certification"])
    def test_author_direction_not_response(self):
        self.make()
        self.assertFalse(retrieve(self.db,"ciúmes",role="Response")["hits"])
        self.assertTrue(retrieve(self.db,"ciúmes",role="Prompt")["hits"])
    def test_existing_projection_protected(self):
        self.make()
        with self.assertRaises(FileExistsError): self.make()
    def test_archive_protected(self):
        with patch("worldroot.deep_recovery.read_verified_sources",return_value=self.sources):
            with self.assertRaises(ValueError): build(self.root,self.root/"bad.sqlite")
    def test_unknown_topic(self):
        self.make()
        with self.assertRaises(ValueError): retrieve(self.db,"Miren",topic="invented")
    def test_missing_is_not_absence(self):
        self.make()
        self.assertEqual(retrieve(self.db,"nonexistentword")["status"],"NOT_RECOVERED")
    def test_source_failure_propagates(self):
        with patch("worldroot.deep_recovery.read_verified_sources",side_effect=ValueError("hash mismatch")):
            with self.assertRaises(ValueError): build(self.root,self.db)
        self.assertFalse(self.db.exists())

    def test_invalid_geometry(self):
        for width,stride in [(0,1),(1,2),(10,0),(101,1)]:
            with self.assertRaises(ValueError): list(windows(self.body,width,stride))
    def test_no_metadata_only_hits(self):
        self.make()
        self.assertEqual(retrieve(self.db,"appearance")["status"],"NOT_RECOVERED")
    def test_stale_manifest_rejected(self):
        self.make()
        p=self.root/"history/sources/MANIFEST.json"
        p.parent.mkdir(parents=True)
        p.write_text('{"sources":[]}')
        self.assertTrue(verify_manifest(self.root,self.db))
        p.write_text('{"sources":[1]}')
        with self.assertRaises(ValueError): verify_manifest(self.root,self.db)
    def test_no_clobber(self):
        self.make()
        old=self.db.read_bytes()
        with self.assertRaises(FileExistsError): self.make()
        self.assertEqual(old,self.db.read_bytes())
    def test_accent_invariance(self):
        self.make()
        a=retrieve(self.db,"Serís",role="Response")
        b=retrieve(self.db,"SERIS",role="Response")
        self.assertEqual([h["id"] for h in a["hits"]],[h["id"] for h in b["hits"]])
    def test_strategy_validation(self):
        self.make()
        with self.assertRaises(ValueError): retrieve(self.db,"Miren",strategy="bad")
    def test_ranking_no_duplicate_windows(self):
        self.make()
        a=retrieve(self.db,"Miren",role="Response")
        self.assertEqual(len({h["id"] for h in a["hits"]}),len(a["hits"]))

    def test_context_not_crossing_roles(self):
        self.body="## Response:\nMiren é alta.\n"+"\n"*40+"## Prompt:\nSerís tem cabelos escuros.\n"
        self.sources=({"sources":[]},[({"source_name":"synthetic.txt","sha256":"a"*64},self.body)])
        self.make()
        with sqlite3.connect(self.db) as c:
            self.assertFalse(c.execute("SELECT COUNT(*) FROM evidence WHERE role='Prompt' AND near_entities LIKE '%miren%'").fetchone()[0])
    def test_context_hint_is_not_fact(self):
        self.make()
        r=retrieve(self.db,"estatura",entity="miren",role="Response",strategy="contextual")
        self.assertTrue(r["hits"])
        self.assertTrue(r["context_hints_only"])
        self.assertFalse(r["semantic_certification"])
    def test_context_unknown(self):
        self.make()
        self.assertEqual(retrieve(self.db,"zzzznoentity123",strategy="contextual")["status"],"NOT_RECOVERED")
    def test_context_respects_role(self):
        self.make()
        self.assertFalse(retrieve(self.db,"Apple Park",role="Response",strategy="contextual")["hits"])

if __name__=="__main__": unittest.main()
