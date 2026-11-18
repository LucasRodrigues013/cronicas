"""Synthetic provenance and integrity tests, no real private story on main."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from worldroot.history_index import build, search, verify, process_requests
from worldroot.ledger import GateError

NAMES = (
    "01_DIA_001_A_383_FONTE_LITERAL.txt",
    "02_DIA_383_A_431_FONTE_LITERAL.txt",
    "03_DIA_431_A_457_FONTE_LITERAL.txt",
    "04_DIA_457_A_469_FONTE_LITERAL.txt",
    "05_DIA_469_A_496_FONTE_LITERAL.txt",
    "06_DIA_497_A_528_FONTE_LITERAL.txt",
)
RANGES = ((1,383),(383,431),(431,457),(457,469),(469,496),(497,528))


def raw_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii")
                        + bytes([0]) + data).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class DriveLiteralHistoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.sources = self.root / "history" / "sources"
        self.sources.mkdir(parents=True)
        self.entries = []
        for i, (name, (lo, hi)) in enumerate(zip(NAMES, RANGES), 1):
            sections = ["CRONICAS synthetic transcript\nUser: Anonymous\n"]
            for j in range(20):
                sections += [
                    "## Prompt:\n", f"Dia {lo} autor pediu liberdade e continuidade capitulo {j}\n",
                    "## Response:\n",
                    f"DIA {lo} Lucas conversa com Káiron na Casa do Jardim Branco, "
                    f"e Miren pesquisa os jardins reais da cidade. Exemplo {j}. "
                    "Cada personagem conserva vontade própria e ação verificável. "
                    "SISTEMA comenta o novo projeto sem reescrever o passado.\n",
                ]
            raw = "".join(sections).encode("utf-8")
            source_path = "history/sources/" + name
            (self.root / source_path).write_bytes(raw)
            self.entries.append({
                "source_name": name,
                "drive_id": "TESTSYNTHETICDRIVE" + str(i).zfill(3),
                "drive_url": f"https://drive.google.com/file/d/TESTSYNTHETICDRIVE{i:03d}/view",
                "mime_type": "text/plain",
                "nominal_day_start": lo, "nominal_day_end": hi,
                "source_kind": "CHAT_EXPORT_LITERAL",
                "semantic_status": "UNREVIEWED_LITERAL",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "utf8_bytes": len(raw),
                "parts": [{"path":source_path, "git_blob_sha1": raw_blob_sha(raw),
                           "bytes": len(raw)}],
            })
        self.manifest = {
            "schema": "worldroot-literal-source-manifest-v1",
            "project": "CRONICAS_DE_UM_NOVO_MUNDO",
            "source_count": 6, "sources": self.entries,
            "total_source_bytes": sum(x["utf8_bytes"] for x in self.entries),
        }
        write_json(self.sources / "MANIFEST.json", self.manifest)

    def test_six_verbatim_sources_build_and_query(self):
        result = build(self.root)
        self.assertEqual(result["result"], "REBUILT_VERIFIED_PRIVATE_FTS")
        self.assertEqual(result["source_count"], 6)
        self.assertGreaterEqual(result["chunk_count"], 100)
        hits = search(self.root, "Káiron Miren", limit=3)
        self.assertTrue(hits["hits"])
        self.assertEqual(hits["hits"][0]["editorial_state"],
                         "LITERAL_SOURCE_EVIDENCE_NOT_CANON_CERTIFIED")
        self.assertTrue(hits["hits"][0]["drive_url"].startswith("https://drive.google.com/"))
        self.assertGreater(hits["hits"][0]["line_start"], 1)
        self.assertFalse(hits["canon_changed"])

    def test_rebuild_is_idempotent_with_same_files(self):
        build(self.root)
        a = (self.root / "history" / "LITERAL_INDEX.sqlite").read_bytes()
        result = build(self.root)
        b = (self.root / "history" / "LITERAL_INDEX.sqlite").read_bytes()
        self.assertEqual(result["result"], "IDEMPOTENT_ALREADY_INDEXED")
        self.assertEqual(a, b)

    def test_does_not_create_or_change_canon_head(self):
        build(self.root)
        self.assertFalse((self.root / "canon" / "HEAD.json").exists())
        self.assertFalse((self.root / "canon" / "state.sqlite").exists())

    def test_corrupted_source_sha_is_rejected(self):
        source = self.sources / NAMES[2]
        source.write_bytes(source.read_bytes() + b"FAKE EVENT")
        with self.assertRaises(GateError):
            build(self.root)
        self.assertFalse((self.root / "history" / "LITERAL_INDEX.sqlite").exists())

    def test_changed_manifest_digest_never_silently_reuses_old_db(self):
        build(self.root)
        self.manifest["coverage_note"] = "Changed source inventory metadata"
        write_json(self.sources / "MANIFEST.json", self.manifest)
        with self.assertRaises(GateError):
            verify(self.root)
        self.assertEqual(build(self.root)["result"], "REBUILT_VERIFIED_PRIVATE_FTS")

    def test_author_prompt_vs_assistant_response_distinct(self):
        build(self.root)
        a = search(self.root, "autor liberdade", role="AUTHOR_PROMPT")
        self.assertTrue(a["hits"])
        b = search(self.root, "Káiron Miren", role="ASSISTANT_RESPONSE")
        self.assertTrue(b["hits"])
        self.assertTrue(all(z["section_role"] == "ASSISTANT_RESPONSE" for z in b["hits"]))

    def test_nominal_day_not_claimed_canon(self):
        build(self.root)
        q = search(self.root, "jardins", day_hint=1)
        self.assertTrue(q["hits"])
        self.assertTrue(all(z["nominal_day_start"] <= 1 <= z["nominal_day_end"]
                            for z in q["hits"]))
        summary = json.loads((self.root / "history" / "INDEX_SUMMARY.json").read_text())
        self.assertIn("not proof", summary["coverage_warning"])

    def test_query_bounded_and_no_sql_injection(self):
        build(self.root)
        for query in ("", "x" * 180, "a" * 60):
            with self.assertRaises(GateError):
                search(self.root, query)
        with self.assertRaises(GateError):
            search(self.root, "Káiron", limit=30)
        with self.assertRaises(GateError):
            search(self.root, "Miren", day_hint=529)

    def test_tampered_part_blob_is_rejected(self):
        blob = self.sources / NAMES[1]
        blob.write_bytes(b"X" * blob.stat().st_size)
        with self.assertRaises(GateError):
            build(self.root)

    def test_real_multi_part_source_recomposition(self):
        entry = self.entries[0]
        original = (self.sources / NAMES[0]).read_bytes()
        (self.sources / NAMES[0]).unlink()
        parts = []
        for j, data in enumerate((original[:1200], original[1200:]), 1):
            path = "history/sources/" + NAMES[0] + f".part-{j:03d}"
            (self.root / path).write_bytes(data)
            parts.append({"path":path, "git_blob_sha1":raw_blob_sha(data),"bytes":len(data)})
        entry["parts"] = parts
        write_json(self.sources / "MANIFEST.json", self.manifest)
        self.assertEqual(build(self.root)["source_count"], 6)
        self.assertEqual(verify(self.root, with_source_checks=True)["source_count"], 6)

    def test_private_query_request_and_response(self):
        build(self.root)
        req = self.root / "history" / "requests" / "query-001.json"
        write_json(req, {"schema":"worldroot-literal-search-request-v1",
                        "query":"Lucas Káiron", "author_source":"USER_MESSAGE",
                        "limit":3, "match_mode":"all"})
        done = process_requests(self.root)
        self.assertEqual(done["processed"], 1)
        out = json.loads((self.root / "history" / "results" / "query-001.json").read_text())
        self.assertGreater(out["result_count"], 0)
        self.assertEqual(process_requests(self.root)["processed"], 0)

    def test_request_missing_user_source_fails_closed(self):
        build(self.root)
        req = self.root / "history" / "requests" / "query-001.json"
        write_json(req, {"schema":"worldroot-literal-search-request-v1",
                        "query":"Miren"})
        with self.assertRaises(GateError):
            process_requests(self.root)

    def test_index_remains_rebuildable_after_binary_loss(self):
        build(self.root)
        (self.root / "history" / "LITERAL_INDEX.sqlite").unlink()
        self.assertEqual(build(self.root)["result"], "REBUILT_VERIFIED_PRIVATE_FTS")
        self.assertTrue(search(self.root, "Miren")["hits"])


if __name__ == "__main__":
    unittest.main()
