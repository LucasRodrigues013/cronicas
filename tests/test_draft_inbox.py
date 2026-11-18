"""Synthetic regression: one ChatGPT inbox produces complete private archive in one transaction."""
import tempfile
import unittest
from pathlib import Path

from test_git_cycle import META, FULL, PROSE, OPTIONS, EVENT, KNOWLEDGE, ID
from worldroot.git_cycle import canonical, load, verify_episode, review_deltas
from worldroot.draft_inbox import archive_inbox
from worldroot.ledger import GateError, ConflictError


class DraftInboxTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        h = self.root / "canon" / "HEAD.json"
        h.parent.mkdir()
        h.write_bytes(canonical({
            "schema": "worldroot-git-canon-v1", "episode_id": "LV-C15-PI-D528",
            "day": 528, "book": "Livro V", "chapter": 15, "part": "I",
            "hour": "23h06",
        }))
        self.data = {
            "schema": "worldroot-draft-inbox-v1", "delivery_id": ID,
            "prose": PROSE, "full_text": FULL, "metadata": META,
            "choices": [vars(x) for x in OPTIONS],
            "book_closed": False, "editorial_visibility": "PRIVADO",
            "reviewed_events": [EVENT], "reviewed_knowledge": [KNOWLEDGE],
        }
        self.inbox = self.root / "inbox" / (ID + ".json")
        self.write()

    def write(self):
        self.inbox.parent.mkdir(parents=True, exist_ok=True)
        self.inbox.write_bytes(canonical(self.data))

    def test_inbox_generates_exact_draft_review_and_manifest(self):
        result = archive_inbox(self.root, self.inbox)
        self.assertEqual(result["status"], "RASCUNHO_GITHUB_VERIFICADO")
        self.assertEqual(result["changed_file_count"], 8)
        self.assertEqual((result["events"], result["knowledge"]), (1, 1))
        draft, manifest = verify_episode(self.root, ID)
        self.assertEqual(draft.full_text, FULL)
        self.assertEqual(len(review_deltas(self.root, ID, draft)[0]), 1)
        self.assertFalse((self.root / "canon" / "state.sqlite").exists())

    def test_idempotent_repeated_input_does_not_duplicate(self):
        archive_inbox(self.root, self.inbox)
        self.assertEqual(archive_inbox(self.root, self.inbox)["changed_file_count"], 0)

    def test_rerun_after_head_advanced_remains_idempotent(self):
        archive_inbox(self.root, self.inbox)
        head_path = self.root / "canon" / "HEAD.json"
        head = load(head_path)
        head.update({"day": 529, "chapter": 15, "part": "II", "hour": "20h42"})
        head_path.write_bytes(canonical(head))
        self.assertEqual(archive_inbox(self.root, self.inbox)["changed_file_count"], 0)

    def test_altered_inbox_cannot_overwrite_original(self):
        archive_inbox(self.root, self.inbox)
        self.data["prose"] = PROSE + "Additional synthetic text"
        self.data["full_text"] = self.data["prose"] + FULL[len(PROSE):]
        self.write()
        with self.assertRaises((ConflictError, GateError)):
            archive_inbox(self.root, self.inbox)

    def test_missing_review_fails_before_writing(self):
        self.data["reviewed_events"] = []
        self.write()
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)
        self.assertFalse((self.root / "episodes" / ID).exists())

    def test_fake_source_anchor_fails_before_writing(self):
        e = dict(EVENT)
        e["source"] = {**EVENT["source"], "literal_anchor": "Invented event not in story"}
        self.data["reviewed_events"] = [e]
        self.write()
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)
        self.assertFalse((self.root / "episodes" / ID).exists())

    def test_wrong_head_chronology_fails_closed(self):
        h = self.root / "canon" / "HEAD.json"
        data = load(h)
        data["day"] = 530
        h.write_bytes(canonical(data))
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)

    def test_no_unauthorized_book_end(self):
        self.data["book_closed"] = True
        self.write()
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)

    def test_wrong_sha_rejected(self):
        e = dict(EVENT)
        e["source"] = {**EVENT["source"], "sha256": "0"*64}
        self.data["reviewed_events"] = [e]
        self.write()
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)

    def test_missing_character_reviewer_gate(self):
        self.data.pop("reviewed_knowledge")
        self.write()
        with self.assertRaises(GateError):
            archive_inbox(self.root, self.inbox)

    def test_invalid_inbox_path_rejected(self):
        elsewhere = self.root / "outside.json"
        elsewhere.write_bytes(canonical(self.data))
        with self.assertRaises(GateError):
            archive_inbox(self.root, elsewhere)


if __name__ == "__main__":
    unittest.main()
