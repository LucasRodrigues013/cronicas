"""Reader-facing release must fail closed until the exact GitHub draft exists."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_git_cycle import META, FULL, PROSE, OPTIONS, EVENT, KNOWLEDGE, ID
from worldroot.git_cycle import canonical
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release


class ReaderDeliveryGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        h = self.root / "canon" / "HEAD.json"
        h.parent.mkdir()
        h.write_bytes(canonical({
            "schema": "worldroot-git-canon-v1",
            "episode_id": "LV-C15-PI-D528",
            "day": 528, "book": "Livro V", "chapter": 15,
            "part": "I", "hour": "23h06",
        }))
        self.inbox = self.root / "inbox" / (ID + ".json")
        self.inbox.parent.mkdir()
        self.inbox.write_bytes(canonical({
            "schema": "worldroot-draft-inbox-v1",
            "delivery_id": ID, "prose": PROSE, "full_text": FULL,
            "metadata": META, "choices": [vars(x) for x in OPTIONS],
            "book_closed": False, "editorial_visibility": "PRIVADO",
            "reviewed_events": [EVENT], "reviewed_knowledge": [KNOWLEDGE],
        }))

    def archive_synthetic(self):
        with patch("worldroot.draft_inbox.presentation_preflight", return_value={"errors": []}), \
             patch("worldroot.draft_inbox.inspect_longform", return_value={"errors": []}):
            return archive_inbox(self.root, self.inbox)

    def test_chat_release_blocked_when_inbox_not_archived(self):
        receipt = audit_release(self.root, ID)
        self.assertFalse(receipt["release_allowed"])
        self.assertEqual(receipt["status"], "DO_NOT_PRESENT_AS_COMPLETE")

    def test_real_longform_target_is_advisory_but_readback_still_required(self):
        self.archive_synthetic()
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}):
            receipt = audit_release(self.root, ID)
        self.assertTrue(receipt["release_allowed"], receipt)
        self.assertEqual(receipt["longform_target_status"], "EXPANDIR")
        self.assertTrue(receipt["checks"]["longform_measured"])
        self.assertFalse(receipt["semantic_certification"])

    def test_verified_readback_allows_release_only_with_completed_checks(self):
        self.archive_synthetic()
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}), \
             patch("worldroot.delivery_gate.inspect_longform", return_value={"errors": [], "prose_words_approx": 10000}):
            receipt = audit_release(self.root, ID)
        self.assertTrue(receipt["release_allowed"], receipt)
        self.assertTrue(receipt["checks"]["literal_source_equals_inbox"])
        self.assertEqual(receipt["prose_words_approx"], 10000)
        self.assertFalse(receipt["canon_changed"])

    def test_rejected_original_never_passes_release_gate(self):
        self.archive_synthetic()
        marker = self.root / "editorial" / "rejections" / (ID + ".json")
        marker.parent.mkdir(parents=True)
        marker.write_text('{"status":"REJEITADO_PELO_AUTOR_NAO_CANONICO"}')
        receipt = audit_release(self.root, ID)
        self.assertFalse(receipt["release_allowed"])
        self.assertTrue(any("rejected" in e for e in receipt["errors"]))

    def test_corrupted_story_cannot_be_released(self):
        self.archive_synthetic()
        file = self.root / "episodes" / ID / "draft" / "narrativa_integral.md"
        file.write_text(file.read_text() + "\nCORRUPTED", encoding="utf-8")
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}), \
             patch("worldroot.delivery_gate.inspect_longform", return_value={"errors": [], "prose_words_approx": 10000}):
            receipt = audit_release(self.root, ID)
        self.assertFalse(receipt["release_allowed"])

    def test_unpersisted_inbox_cannot_be_released_after_archive(self):
        self.archive_synthetic()
        self.inbox.unlink()
        receipt = audit_release(self.root, ID)
        self.assertFalse(receipt["release_allowed"])


if __name__ == "__main__":
    unittest.main()
