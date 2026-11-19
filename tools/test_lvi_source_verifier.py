"""Regression tests for the mandatory original-source gate on Livro VI."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_lvi_original import PARTS, verify_lvi
from validate_episode_archive import ArchiveInvalid

def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def sha(data):
    return hashlib.sha256(data).hexdigest()

class OriginalSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.episode_id = PARTS[1]
        self.folder = self.root / "episodes" / self.episode_id / "draft"
        self.folder.mkdir(parents=True)

    def seed_complete(self):
        choices = [
            {"number": i, "title": f"Escolha literal {i}",
             "is_special": i == 4, "is_free": i == 5}
            for i in range(1, 6)
        ]
        prose = "DIA 538. Lucas ouviu Miren e construiu uma cidade com outros moradores, sem apagar as suas vozes.\n"
        literal = prose + "\n".join(x["title"] for x in choices)
        events = [{"event_id": "D538-E001", "source_anchor": "Lucas ouviu Miren"}]
        metadata = {"canon_status": "RASCUNHO", "day": 538, "book": "Livro VI"}
        draft = {"delivery_id": self.episode_id, "prose": prose,
                 "full_text": literal, "metadata": metadata,
                 "choices": choices, "events": events, "book_closed": False}
        payloads = {
            "narrativa_integral.md": literal.encode("utf-8"),
            "opcoes.json": encode(choices),
            "eventos_e_consequencias.json": encode(events),
            "checkpoint_candidato.json": encode(metadata),
            "episode_draft.json": encode(draft),
        }
        for name, blob in payloads.items():
            (self.folder / name).write_bytes(blob)
        manifest = {"schema": "worldroot-episode-package-v1",
                    "delivery_id": self.episode_id, "canon_status": "RASCUNHO",
                    "original_readback_sha256": sha(payloads["narrativa_integral.md"]),
                    "artifacts": {
                        name: {"bytes": len(blob), "sha256": sha(blob)}
                        for name, blob in payloads.items()
                    }}
        (self.folder / "manifesto_imutavel.json").write_bytes(encode(manifest))
        original = self.root / "editorial/recovery/originals" / (self.episode_id + ".txt")
        original.parent.mkdir(parents=True)
        original.write_bytes(payloads["narrativa_integral.md"])
        proof = {
            "schema": "worldroot-original-chat-source-proof-v1",
            "episode_id": self.episode_id,
            "source_kind": "USER_SUBMITTED_LITERAL_TEXT",
            "source_file": str(original.relative_to(self.root)),
            "source_sha256": sha(payloads["narrativa_integral.md"]),
            "source_bytes": len(payloads["narrativa_integral.md"]),
            "source_locator": "synthetic/test-original",
        }
        (self.folder / "source_proof.json").write_bytes(encode(proof))
        review_path = self.root / "episodes" / self.episode_id / "review/continuity_review.json"
        review_path.parent.mkdir(parents=True)
        review_path.write_bytes(encode({
            "episode_id": self.episode_id, "status": "REVIEWED_WITH_EVIDENCE",
            "characters": [{
                "name": "Lucas", "last_physical_appearance_source": "synthetic",
                "location_at_scene": "Três Arcos", "affiliation_at_scene": "Founder",
                "knowledge_at_scene": "Existing city",
            }],
        }))
        return original

    def test_undocumented_draft_fails_closed(self):
        with self.assertRaises(ArchiveInvalid):
            verify_lvi(self.root, self.episode_id)

    def test_byte_exact_archive_passes(self):
        self.seed_complete()
        result = verify_lvi(self.root, self.episode_id)
        self.assertEqual(result["result"], "ORIGINAL_MATCHED_ARCHIVE_REVIEWED")

    def test_modified_original_is_rejected(self):
        path = self.seed_complete()
        with path.open("ab") as f:
            f.write(b"\nUNAUTHORIZED MODIFICATION")
        with self.assertRaises(ArchiveInvalid):
            verify_lvi(self.root, self.episode_id)

    def test_event_without_literal_anchor_rejected(self):
        self.seed_complete()
        path = self.folder / "eventos_e_consequencias.json"
        events = [{"event_id": "D538-E001", "source_anchor": "Invented new fact"}]
        path.write_bytes(encode(events))
        # Internal manifest must also match: a fabricated sidecar cannot bypass either gate.
        with self.assertRaises(ArchiveInvalid):
            verify_lvi(self.root, self.episode_id)

if __name__ == "__main__":
    unittest.main()
