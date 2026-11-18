"""Synthetic choice intake tests: no real-world narrative and no credentials."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from worldroot.choice_intake import verify_selection, verify_tree, IntakeError


def put_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


class IntakeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.id = "SYNTHETIC-EPISODE-003"
        self.options = [
            {"number": 1, "title": "A"},
            {"number": 2, "title": "B"},
            {"number": 3, "title": "C"},
            {"number": 4, "title": "SPECIAL", "is_special": True},
            {"number": 5, "title": "FREE", "is_free": True},
        ]
        d = self.root / "episodes" / self.id / "draft"
        self.options_path = d / "opcoes.json"
        put_json(self.options_path, self.options)
        raw = self.options_path.read_bytes()
        self.manifest = d / "manifesto_imutavel.json"
        put_json(self.manifest, {
            "schema": "worldroot-episode-package-v1",
            "delivery_id": self.id, "canon_status": "RASCUNHO",
            "artifacts": {"opcoes.json": {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}},
        })
        self.selection = self.root / "choices" / self.id / "option-4.json"
        self.payload = {"schema": "worldroot-author-choice-v1", "episode_id": self.id,
                        "option": 4, "free_text": "", "author_source": "USER_MESSAGE"}
        put_json(self.selection, self.payload)

    def test_real_choice_envelope_passes(self):
        self.assertEqual(verify_selection(self.root, self.selection)["option"], 4)
        self.assertEqual(len(verify_tree(self.root)), 1)

    def test_boolean_is_not_an_option(self):
        self.payload["option"] = True
        put_json(self.selection, self.payload)
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_filename_must_match_option(self):
        self.payload["option"] = 3
        put_json(self.selection, self.payload)
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_cannot_claim_author_source_from_model(self):
        self.payload["author_source"] = "MODEL_GENERATED"
        put_json(self.selection, self.payload)
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_tampered_options_refused(self):
        put_json(self.options_path, [{"number": 4, "title": "FAKE"}])
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_free_choice_requires_instruction(self):
        self.selection.unlink()
        self.selection = self.selection.parent / "option-5.json"
        self.payload["option"] = 5
        put_json(self.selection, self.payload)
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_duplicate_choices_refused(self):
        other = self.selection.parent / "option-3.json"
        put_json(other, {**self.payload, "option": 3})
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_unknown_fields_refused(self):
        self.payload["auto_approve_canon"] = True
        put_json(self.selection, self.payload)
        with self.assertRaises(IntakeError):
            verify_tree(self.root)

    def test_missing_choice_does_not_pass(self):
        self.selection.unlink()
        with self.assertRaises(IntakeError):
            verify_tree(self.root)


if __name__ == "__main__":
    unittest.main()
