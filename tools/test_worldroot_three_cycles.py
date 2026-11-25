"""Synthetic WORLDROOT three-cycle regression: no real user choice, canon or prose mutated."""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parent))
from test_chapter_drive_publisher import ChapterBackupTest,blob
from worldroot_transition import route,record,ArchiveInvalid
from worldroot_memory_delta import derive,draft_delta,canon_delta,resume
from worldroot_chapter_seal import seal
from github_chapter_publisher import publish,ChapterError

def enc(x):
    return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

class TransitionTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.head_id="LVI-C01-PIII-D539-AUTHOR-SOURCE"
        self.new_id="LVI-C01-PIV-D540-AUTHOR-SOURCE"
        (self.root/"canon/episodes").mkdir(parents=True)
        (self.root/"canon/HEAD.json").write_bytes(enc({
            "episode_id":self.head_id,"book":"Livro VI","chapter":1,"part":"III",
            "day":539,"sequence":12,"source_sha256":"f"*64}))
        for eid,part,day in ((self.head_id,"III",539),(self.new_id,"IV",540)):
            p=self.root/"episodes"/eid/"draft"
            p.mkdir(parents=True)
            (p/"checkpoint_candidato.json").write_bytes(enc({
                "book":"Livro VI","chapter":1,"part":part,"day":day,
                "canon_status":"RASCUNHO"}))
            (p/"opcoes.json").write_bytes(enc([
                {"number":i,"is_special":i==4,"is_free":i==5,"title":"Teste"}
                for i in range(1,6)]))
            (self.root/"episodes"/eid/"review").mkdir()
            (self.root/"episodes"/eid/"review/continuity_review.json").write_bytes(enc({"open_flags":[]}))
        (self.root/"canon/episodes"/(self.head_id+".json")).write_bytes(enc({
            "episode_id":self.head_id,"story_sha256":"f"*64}))
    def fake(self,root,eid):
        return {"sha256":"f"*64}
    def test_draft_choice_unique_and_head_untouched(self):
        raw=(self.root/"canon/HEAD.json").read_bytes()
        with patch("worldroot_transition.verify_lvi",self.fake):
            one=record(self.root,self.new_id,4,"",expected_head=self.head_id,user_message="Escolha 4")
            two=record(self.root,self.new_id,4,"",expected_head=self.head_id,user_message="Escolha 4")
            self.assertEqual(one["route"],"DRAFT_CHOICE_READY_FOR_CANON_WORKFLOW")
            self.assertTrue(one["changed"])
            self.assertFalse(two["changed"])
            with self.assertRaisesRegex(ArchiveInvalid,"differs"):
                record(self.root,self.new_id,3,"",expected_head=self.head_id,user_message="Escolha 3")
        self.assertEqual((self.root/"canon/HEAD.json").read_bytes(),raw)
    def test_stale_and_free_text_fail_closed(self):
        with patch("worldroot_transition.verify_lvi",self.fake):
            with self.assertRaisesRegex(ArchiveInvalid,"Stale"):
                route(self.root,self.new_id,4,"",expected_head="OLD",user_message="4")
            with self.assertRaisesRegex(ArchiveInvalid,"requires"):
                route(self.root,self.new_id,5,"",expected_head=self.head_id,user_message="5")
            with self.assertRaisesRegex(ArchiveInvalid,"Real user"):
                route(self.root,self.new_id,4,"",expected_head=self.head_id,user_message="")
    def test_canon_choice_is_navigation_not_reclosure(self):
        with patch("worldroot_transition.verify_lvi",self.fake):
            out=record(self.root,self.head_id,4,"",expected_head=self.head_id,user_message="Escolha 4")
        self.assertEqual(out["route"],"ALREADY_CANONICAL_NAVIGATION_ONLY")
        self.assertTrue((self.root/"navigation/author_intents"/(self.head_id+".json")).is_file())
        self.assertFalse((self.root/"choices").exists())

class DeltaTest(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.eid="LVI-C01-PIV-D540-AUTHOR-SOURCE"
        p=self.root/"episodes"/self.eid
        (p/"draft").mkdir(parents=True)
        (p/"review").mkdir()
        self.original="LUCAS — Bom dia, Miren.\nMIREN — Bom dia, querido.\n"
        self.hash=hashlib.sha256(self.original.encode()).hexdigest()
        (p/"draft/narrativa_integral.md").write_text(self.original,encoding="utf-8")
        (p/"draft/checkpoint_candidato.json").write_bytes(enc({
            "book":"Livro VI","chapter":1,"part":"IV","day":540,
            "hour":"08h10","location":"Casa do Jardim Branco","canon_status":"RASCUNHO"}))
        self.event={"event_id":"X1","event_type":"DIALOGUE","canon_status":"NARRADO",
                    "occurred_day":540,"visibility":"PRIVADO_PERSONAGEM",
                    "source":{"line":1,"literal_anchor":"LUCAS — Bom dia","sha256":self.hash}}
        (p/"review/eventos_revisados.json").write_bytes(enc({
            "review_status":"REVISADO","source_sha256":self.hash,"events":[self.event]}))
        (p/"review/conhecimento_revisado.json").write_bytes(enc({
            "review_status":"REVISADO","knowledge":[{"source_event":"X1","person":"Miren",
            "acquired_day":540,"knowledge":"Ouvira o cumprimento"}]}))
        (p/"review/continuity_review.json").write_bytes(enc({
            "status":"REVIEWED_WITH_EVIDENCE","characters":[{"name":"Miren"}],"open_flags":[]}))
        (self.root/"canon/episodes").mkdir(parents=True)
        (self.root/"editorial/rejections").mkdir(parents=True)
    def fake(self,root,eid):
        return {"sha256":self.hash}
    def test_delta_replay_and_event_evidence(self):
        with patch("worldroot_memory_delta.verify_lvi",self.fake):
            x=draft_delta(self.root,self.eid,write=True)
            self.assertEqual(x["events"],1)
            self.assertEqual(x["knowledge"],1)
            self.assertEqual(draft_delta(self.root,self.eid,write=True),x)
            p=self.root/"canon/episodes"/(self.eid+".json")
            p.write_bytes(enc({"episode_id":self.eid,"story_sha256":self.hash,
                               "status":"FECHADO_GITHUB","sequence":13,"events":[self.event]}))
            c=canon_delta(self.root,self.eid,write=True)
            self.assertEqual(c["status"],"CANONICAL_MEMORY_VERIFIED")
            self.assertEqual(canon_delta(self.root,self.eid,write=True),c)
            path=self.root/"memory/deltas"/(self.eid+".json")
            original=path.read_bytes()
            self.assertFalse(json.loads(original)["canonical_at_capture"])
            self.assertEqual(draft_delta(self.root,self.eid,write=True),x)
            self.assertEqual(path.read_bytes(),original)
            damaged=json.loads(original)
            damaged["source_bytes"]+=1
            path.write_bytes(enc(damaged))
            with self.assertRaisesRegex(ArchiveInvalid,"Immutable memory conflict"):
                draft_delta(self.root,self.eid,write=True)
    def test_bad_literal_anchor_blocks_memory(self):
        p=self.root/"episodes"/self.eid/"review/eventos_revisados.json"
        j=json.loads(p.read_text())
        j["events"][0]["source"]["line"]=2
        p.write_bytes(enc(j))
        with patch("worldroot_memory_delta.verify_lvi",self.fake):
            with self.assertRaisesRegex(ArchiveInvalid,"Unverified"):
                derive(self.root,self.eid)

class ChapterSealTest(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        (self.root/"canon/episodes").mkdir(parents=True)
        (self.root/"editorial/rejections").mkdir(parents=True)
        ids=[]
        for i in range(1,6):
            eid,folder=ChapterBackupTest.add_part(self,i)
            ids.append(eid)
            m=json.loads((folder/"checkpoint_candidato.json").read_text())
            story=(folder/"narrativa_integral.md").read_bytes()
            j={"episode_id":eid,"story_sha256":hashlib.sha256(story).hexdigest(),
               "status":"FECHADO_GITHUB","metadata":m,"sequence":i+4,
               "previous_episode_id":ids[-2] if i>1 else "LV-PREV"}
            if i<5:
                (self.root/"canon/episodes"/(eid+".json")).write_bytes(enc(j))
            else:self.fifth_journal=j
        self.fifth=ids[-1]
        (self.root/"canon/HEAD.json").write_bytes(enc({
            "episode_id":self.fifth,"sequence":9,
            "book":"Livro V","chapter":4,"part":"V","day":506}))
    def test_draft_bundle_then_later_canon_seal(self):
        p=publish(self.root,"Livro V",4)
        self.assertEqual(p["status"],"LOCAL_PACKAGE_SHA_VERIFIED_PENDING_GIT_PUSH")
        with self.assertRaises(Exception):
            seal(self.root,"Livro V",4)
        (self.root/"canon/episodes"/(self.fifth+".json")).write_bytes(enc(self.fifth_journal))
        sealed=seal(self.root,"Livro V",4)
        self.assertEqual(sealed["status"],"FULL_CHAPTER_SEALED")
        self.assertEqual(seal(self.root,"Livro V",4),sealed)
        self.assertTrue((self.root/"chapters/LIVRO-V-C04/CANONICAL_SEAL.json").is_file())
    def test_zip_tamper_is_detected(self):
        publish(self.root,"Livro V",4)
        (self.root/"canon/episodes"/(self.fifth+".json")).write_bytes(enc(self.fifth_journal))
        (self.root/"chapters/LIVRO-V-C04/LIVRO-V-C04-ARQUIVO.zip").write_text("tampered")
        with self.assertRaisesRegex(ChapterError,"mismatch"):
            seal(self.root,"Livro V",4)

if __name__=="__main__":
    unittest.main()
