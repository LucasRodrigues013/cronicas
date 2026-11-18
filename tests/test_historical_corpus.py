"""WORLDROOT history must be searchable but never self-certifying as canon."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worldroot.historical_corpus import import_corpus, search, HistoryError


class HistoryIndexTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = self.root / "sources"
        self.raw.mkdir()
        self.manifest = self.root / "manifest.json"
        self.db = self.root / "search.sqlite"
        self.lines = (
            "CRÔNICAS — arquivo fictício\nUser: Anônimo\n\n"
            "## Prompt:\nO autor determina: GÊNESE não será enfraquecida.\n"
            "## Response:\nDIA 001 — O herói falou com Miren na praça.\n"
            "Rumo não é NÓX. O SISTEMA é outro.\n"
            "## Prompt:\nNão faça do plano do Livro VI um fato narrado.\n"
            "## Response:\nAstra lidera os pesquisadores do jardim.\n"
        )
        self.filename = "sample.txt"
        self.source_id = "SOURCE-ID-ONE"
        self._write()

    def _write(self):
        raw = self.lines.encode("utf-8")
        (self.raw / self.filename).write_bytes(raw)
        source = {
            "file_id": self.source_id, "filename": self.filename,
            "declared_start": 1, "declared_end": 528,
            "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "url": "https://drive.google.com/file/d/SOURCE-ID-ONE/view",
        }
        sources = [{**source, "file_id": f"SOURCE-ID-{n}", "filename": f"sample-{n}.txt"}
                   for n in range(1, 7)]
        for item in sources:
            (self.raw / item["filename"]).write_bytes(raw)
        self.manifest.write_text(json.dumps({"schema": "worldroot-history-sources-v1",
                                              "sources": sources}), encoding="utf-8")

    def index(self):
        return import_corpus(self.db, self.manifest, self.raw)

    def test_six_file_ingest_and_fts_query(self):
        out = self.index()
        self.assertEqual(out["source_files"], 6)
        self.assertFalse(out["head_changed"])
        result = search(self.db, "Miren", 3)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["source_status"], "LITERAL_TRANSCRIPT_UNRECONCILED")
        self.assertEqual(result[0]["speaker"], "ASSISTANT")
        self.assertIn("Miren", result[0]["literal_excerpt"])

    def test_no_canon_mutation_even_when_fake_head_exists(self):
        head = self.root / "canon" / "HEAD.json"
        head.parent.mkdir()
        head.write_text('{"episode_id":"LV-C15-PI-D528","day":528}',encoding="utf-8")
        original = head.read_bytes()
        self.index()
        self.assertEqual(head.read_bytes(), original)

    def test_recovery_repeat_is_idempotent(self):
        self.index()
        first = self.db.read_bytes()
        out = self.index()
        self.assertTrue(all(x["result"] == "IDEMPOTENT" for x in out["sources"]))
        self.assertEqual(self.db.read_bytes(), first)

    def test_sha_mismatch_fails_closed_without_partial_db(self):
        data = json.loads(self.manifest.read_text())
        data["sources"][4]["sha256"] = "0" * 64
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(HistoryError):self.index()
        self.assertFalse(self.db.exists())

    def test_missing_source_fails_closed(self):
        (self.raw / "sample-4.txt").unlink()
        with self.assertRaises(HistoryError):self.index()
        self.assertFalse(self.db.exists())

    def test_day_is_a_hint_not_event_proof(self):
        self.index()
        results = search(self.db,"Rumo",4,day=1)
        self.assertTrue(results)
        self.assertEqual(results[0]["filename_range_only"],[1,528])
        with sqlite3.connect(self.db) as conn:
            rows=conn.execute("SELECT status,evidence FROM historical_day_anchors").fetchall()
        self.assertTrue(rows)
        self.assertEqual(rows[0][0],"UNVERIFIED_TEXT_HEADING")

    def test_author_and_assistant_remain_distinct(self):
        self.index()
        self.assertEqual(search(self.db,"enfraquecida")[0]["speaker"],"AUTHOR")
        self.assertEqual(search(self.db,"jardim")[0]["speaker"],"ASSISTANT")

    def test_mutated_source_not_accepted_without_new_manifest(self):
        self.index()
        p=self.raw/"sample-2.txt"
        p.write_bytes(p.read_bytes()+b"\nALTERADO")
        with self.assertRaises(HistoryError):self.index()

    def test_fts_and_integrity_check(self):
        self.index()
        with sqlite3.connect(self.db) as conn:
            self.assertEqual(conn.execute("pragma integrity_check").fetchone()[0],"ok")
            self.assertEqual(conn.execute("pragma foreign_key_check").fetchall(),[])
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM historical_sources WHERE active=1").fetchone()[0],6)

    def test_unknown_query_returns_nothing(self):
        self.index()
        self.assertEqual(search(self.db,"termoimpossivel"),[])
        with self.assertRaises(HistoryError):search(self.db, "")


if __name__ == "__main__":
    unittest.main()