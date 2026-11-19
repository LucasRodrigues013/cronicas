"""Negative gates for fixed user-initiated ratification (no invented approvals)."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from worldroot.retro_ratify import (
    AUTHOR_QUOTE, PARTS, REQUEST, _request,
    author_ratification_choice, ratify,
)
from worldroot.ledger import GateError


class UserRatificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_no_explicit_approval_cannot_ratify(self):
        with self.assertRaises(GateError):
            ratify(self.root)

    def test_unquoted_message_does_not_approve_three_episodes(self):
        REQUEST_FILE = self.root / REQUEST
        REQUEST_FILE.parent.mkdir(parents=True)
        REQUEST_FILE.write_text('{"schema":"worldroot-explicit-three-episode-ratification-v1",'
                                '"author_source":"MODEL_GENERATED"}', encoding="utf-8")
        with self.assertRaises(GateError):
            _request(self.root)

    def test_request_is_exactly_three_and_special_fourth_selection_not_fabricated(self):
        self.assertEqual(len(PARTS), 3)
        self.assertEqual([p["part"] for p in PARTS], ["I", "II", "III"])
        self.assertEqual([p["option"] for p in PARTS], [4, 4, 0])
        self.assertEqual(len({p["sha"] for p in PARTS}), 3)
        self.assertIn("Salve os 3 capítulos como cânone", AUTHOR_QUOTE)

    def test_no_source_cannot_fake_choice_from_export(self):
        with self.assertRaises(GateError):
            author_ratification_choice(self.root, PARTS[0]["id"])


if __name__ == "__main__":
    unittest.main()
