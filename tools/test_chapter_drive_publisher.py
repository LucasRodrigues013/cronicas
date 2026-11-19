"""Synthetic regression tests: no real OAuth, GitHub, story prose, or Drive writes."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chapter_drive_publisher import build_chapter, ChapterError


def blob(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


class ChapterBackupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "canon" / "episodes").mkdir(parents=True)
        (self.root / "editorial" / "rejections").mkdir(parents=True)

    def add_part(self, index):
        part = ("I", "II", "III", "IV", "V")[index - 1]
        episode = "LV-C04-P" + part + "-D" + str(501 + index)
        folder = self.root / "episodes" / episode / "draft"
        folder.mkdir(parents=True)
        meta = {"book": "Livro V", "chapter": 4, "part": part,
                "day": 501 + index, "hour": "12h00", "location": "Três Arcos",
                "canon_status": "RASCUNHO"}
        options = [{"number": i, "title": "Escolha " + str(i),
                    "is_special": i == 4, "is_free": i == 5} for i in range(1, 6)]
        prose = "Esta é uma narrativa sintética longa para validação de integridade dos dados.\n"
        narrative = prose + "\n" + "\n".join(x["title"] for x in options)
        records = {
            "narrativa_integral.md": narrative.encode(),
            "opcoes.json": blob(options),
            "eventos_e_consequencias.json": blob([]),
            "checkpoint_candidato.json": blob(meta),
            "episode_draft.json": blob({
                "delivery_id": episode, "metadata": meta, "choices": options,
                "events": [], "prose": prose, "full_text": narrative,
                "book_closed": False}),
        }
        for filename, data in records.items():
            (folder / filename).write_bytes(data)
        sha = hashlib.sha256(records["narrativa_integral.md"]).hexdigest()
        manifest = {
            "schema": "worldroot-episode-package-v1",
            "delivery_id": episode, "canon_status": "RASCUNHO",
            "original_readback_sha256": sha,
            "artifacts": {name: {"sha256": hashlib.sha256(data).hexdigest(),
                                 "bytes": len(data)}
                          for name, data in records.items()},
        }
        (folder / "manifesto_imutavel.json").write_bytes(blob(manifest))
        if index < 5:
            journal = {"status": "FECHADO_GITHUB", "episode_id": episode,
                       "story_sha256": sha, "metadata": meta}
            (self.root / "canon" / "episodes" / (episode + ".json")).write_bytes(blob(journal))
        return episode, folder

    def test_five_parts_exact_backup(self):
        for n in range(1, 6):
            self.add_part(n)
        key, payload = build_chapter(self.root, "Livro V", 4)
        self.assertEqual(key, "LIVRO-V-C04")
        self.assertEqual(len(payload), 3)
        archive = zipfile.ZipFile(__import__("io").BytesIO(payload[key + "-ARQUIVO.zip"]))
        names = archive.namelist()
        self.assertEqual(len(names), 5 * 6 + 4 + 2)
        aggregate = archive.read("capitulo_integral.md")
        self.assertEqual(aggregate, payload[key + "-INTEGRAL.md"])
        manifest = json.loads(archive.read("chapter_manifest.json"))
        self.assertEqual(manifest["part_count"], 5)
        self.assertTrue(all(manifest["parts"][i]["canonical_closed"] for i in range(4)))
        self.assertFalse(manifest["parts"][4]["canonical_closed"])
        self.assertEqual(manifest["combined_sha256"], hashlib.sha256(aggregate).hexdigest())

    def test_only_four_parts_means_no_chapter(self):
        for n in range(1, 5):
            self.add_part(n)
        self.assertIsNone(build_chapter(self.root, "Livro V", 4))

    def test_rejected_part_is_excluded_from_active_five_part_sequence(self):
        for n in range(1, 6):
            episode, _ = self.add_part(n)
        (self.root / "editorial" / "rejections" / (episode + ".json")).write_bytes(blob({"rejected": True}))
        self.assertIsNone(build_chapter(self.root, "Livro V", 4))

    def test_rejected_older_duplicate_does_not_block_new_authorized_part(self):
        for n in range(1, 6):
            self.add_part(n)
        old_id = "LVI-OLD-REJECTED-PI"
        old_dir = self.root / "episodes" / old_id / "draft"
        old_dir.mkdir(parents=True)
        (old_dir / "checkpoint_candidato.json").write_bytes(blob(
            {"book": "Livro V", "chapter": 4, "part": "I", "canon_status": "RASCUNHO"}))
        (self.root / "editorial" / "rejections" / (old_id + ".json")).write_bytes(blob({"rejected": True}))
        key, blobs = build_chapter(self.root, "Livro V", 4)
        self.assertEqual(key, "LIVRO-V-C04")
        self.assertEqual(len(blobs), 3)

    def test_corrupt_part_blocks_export(self):
        for n in range(1, 6):
            _, folder = self.add_part(n)
        (folder / "narrativa_integral.md").write_text("alterado", encoding="utf-8")
        with self.assertRaises(Exception):
            build_chapter(self.root, "Livro V", 4)

    def test_no_previous_canonical_choice_blocks_export(self):
        for n in range(1, 6):
            self.add_part(n)
        first = self.root / "canon" / "episodes" / "LV-C04-PI-D502.json"
        first.unlink()
        with self.assertRaisesRegex(ChapterError, "canonically closed"):
            build_chapter(self.root, "Livro V", 4)


if __name__ == "__main__":
    unittest.main()
