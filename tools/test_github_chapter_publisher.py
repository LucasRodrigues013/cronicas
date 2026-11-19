"""GitHub-only chapter publishing regression; synthetic fixtures, zero network."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_chapter_drive_publisher import ChapterBackupTest, blob
from github_chapter_publisher import publish, ChapterError


class GitHubChapterPublisherTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "canon/episodes").mkdir(parents=True)
        (self.root / "editorial/rejections").mkdir(parents=True)

    def add_part(self, n):
        return ChapterBackupTest.add_part(self, n)

    def test_incomplete_chapter_has_no_files_or_receipt(self):
        for n in range(1, 5):
            self.add_part(n)
        result = publish(self.root, "Livro V", 4)
        self.assertEqual(result["status"], "WAITING_FOR_FIVE_COMPLETE_PARTS")
        self.assertFalse((self.root / "chapters").exists())

    def test_private_git_bundle_idempotent_and_integral(self):
        for n in range(1, 6):
            self.add_part(n)
        result = publish(self.root, "Livro V", 4)
        self.assertEqual(result["status"], "LOCAL_PACKAGE_SHA_VERIFIED_PENDING_GIT_PUSH")
        key = result["chapter_key"]
        self.assertEqual(publish(self.root, "Livro V", 4), result)
        receipt = json.loads((self.root / "delivery/github_chapters" / (key + ".json")).read_text())
        self.assertEqual(receipt["schema"], "worldroot-github-private-chapter-v1")
        self.assertEqual(len(receipt["artifacts"]), 3)
        self.assertFalse(receipt["canon_head_modified"])
        self.assertFalse(receipt["drive_modified"])
        manifest = json.loads((self.root / "chapters" / key / (key + "-MANIFESTO.json")).read_text())
        self.assertEqual(manifest["publication"], "GITHUB_PRIVATE_ONLY_NO_CANON_PROMOTION")
        self.assertEqual([part["part"] for part in manifest["parts"]], ["I", "II", "III", "IV", "V"])

    def test_tampered_existing_bundle_fail_closed(self):
        for n in range(1, 6):
            self.add_part(n)
        result = publish(self.root, "Livro V", 4)
        key = result["chapter_key"]
        (self.root / "chapters" / key / (key + "-INTEGRAL.md")).write_text("corrupt")
        with self.assertRaisesRegex(ChapterError, "Immutable"):
            publish(self.root, "Livro V", 4)

    def test_rejected_duplicate_does_not_replace_authorized_part(self):
        for n in range(1, 6):
            self.add_part(n)
        old = "LVI-C01-PI-D538-AUTHOR-SOURCE"
        path = self.root / "episodes" / old / "draft"
        path.mkdir(parents=True)
        (path / "checkpoint_candidato.json").write_bytes(blob(
            {"book": "Livro V", "chapter": 4, "part": "I", "canon_status": "RASCUNHO"}))
        (self.root / "editorial/rejections" / (old + ".json")).write_bytes(blob({"rejected": True}))
        self.assertEqual(publish(self.root, "Livro V", 4)["part_count"], 5)

    def test_five_parts_are_not_a_canon_promotion(self):
        for n in range(1, 6):
            self.add_part(n)
        publish(self.root, "Livro V", 4)
        self.assertFalse((self.root / "canon/HEAD.json").exists())
        self.assertFalse((self.root / "canon/episodes/LV-C04-PV-D506.json").exists())


if __name__ == "__main__":
    unittest.main()
