import unittest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch
from worldroot.deep_recovery import sections,windows,build,retrieve,norm

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

if __name__=="__main__": unittest.main()
