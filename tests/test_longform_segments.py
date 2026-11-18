"""Verify optional multi-turn private staged narrative never changes canon."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from worldroot.ledger import GateError
from worldroot.longform_segments import verify_longform_segments

ID = "SYNTHETIC-C16-PIV-D534"


def stage(root: Path, parts: list[str]):
    entries = []
    for number, part in enumerate(parts, 1):
        path = f"production/{ID}/segments/{number:02d}.md"
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(part, encoding="utf-8")
        entries.append({"part": number, "path": path,
                        "sha256": hashlib.sha256(part.encode()).hexdigest()})
    return {"prose": "".join(parts), "longform_segments": entries}


class LongformSegmentsTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)

    def test_direct_prose_needs_no_staging(self):
        self.assertEqual(verify_longform_segments(self.root, ID, {"prose": "hello"})["status"],
                         "DIRECT_SINGLE_PROSE")

    def test_two_stage_round_trip(self):
        payload = stage(self.root, ["Uma primeira cena.\n", "Uma segunda cena.\n"])
        receipt = verify_longform_segments(self.root, ID, payload)
        self.assertEqual(receipt["parts"], 2)
        self.assertTrue(receipt["verified"])
        self.assertFalse(receipt["canon_changed"])

    def test_tamper_blocks(self):
        payload = stage(self.root, ["A primeira.\n", "A segunda.\n"])
        (self.root / payload["longform_segments"][0]["path"]).write_text("ALTO", encoding="utf-8")
        with self.assertRaises(GateError):
            verify_longform_segments(self.root, ID, payload)

    def test_source_mismatch_blocks(self):
        payload = stage(self.root, ["A primeira.\n", "A segunda.\n"])
        payload["prose"] = "capitulo diferente"
        with self.assertRaises(GateError):
            verify_longform_segments(self.root, ID, payload)

    def test_traversal_and_order_block(self):
        payload = stage(self.root, ["A primeira.\n", "A segunda.\n"])
        payload["longform_segments"][0]["path"] = "../secret"
        with self.assertRaises(GateError):
            verify_longform_segments(self.root, ID, payload)
        payload = stage(self.root, ["A primeira.\n", "A segunda.\n"])
        payload["longform_segments"] = payload["longform_segments"][::-1]
        with self.assertRaises(GateError):
            verify_longform_segments(self.root, ID, payload)

    def test_symlinks_block(self):
        payload = stage(self.root, ["A primeira.\n", "A segunda.\n"])
        path = self.root / payload["longform_segments"][0]["path"]
        path.unlink()
        path.symlink_to(self.root / payload["longform_segments"][1]["path"])
        with self.assertRaises(GateError):
            verify_longform_segments(self.root, ID, payload)

if __name__ == "__main__":
    unittest.main()
