"""R26: end-to-end v3 inbox, sidecar and release, without rewriting archives."""
import unittest
from pathlib import Path
from unittest.mock import patch
from test_r25_archive_integration import (
    R25ArchiveIntegrationTest, NEW_ID, HEAD_ID, PROSE,
)
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release
from worldroot.git_cycle import load, canonical
from worldroot.ledger import GateError
from test_r26_magic_and_directors import fantasy


class R26ArchiveIntegrationTest(unittest.TestCase):
    write = R25ArchiveIntegrationTest.write
    run_archive = R25ArchiveIntegrationTest.run_archive
    def setUp(self):
        R25ArchiveIntegrationTest.setUp(self)
        self.payload["schema"] = "worldroot-draft-inbox-v3"
        self.payload["fantasy_review"] = fantasy(
            character_evolution=[{
                "name": "LUCAS",
                "literal_anchor": "Uma personagem sintetica decide escrever uma carta por vontade propria.",
                "decision_or_reaction": "Lucas aceita a decisão livre da pessoa e a escuta.",
                "emotional_or_relational_delta": "A relação com o grupo se preserva sem submissão.",
                "new_power_claimed": False
            }],
            variation_decision="A Parte é sintética e apresenta três cenas ligadas pela escolha e resposta."
        )
        self.write()

    def test_v3_is_archived_with_r25_and_r26_sidecars(self):
        result = self.run_archive()
        self.assertEqual(result["changed_file_count"], 10)
        review = self.root / "episodes" / NEW_ID / "review"
        self.assertTrue((review / "experiencia_r25.json").is_file())
        self.assertTrue((review / "fantasia_r26.json").is_file())
        self.assertTrue(load(review / "fantasia_r26.json")["assessment"]["ready"])
        self.assertEqual(load(self.root / "canon" / "HEAD.json")["episode_id"], HEAD_ID)
        with patch("worldroot.delivery_gate.presentation_preflight",
                   return_value={"errors": [], "status": "OK"}):
            receipt = audit_release(self.root, NEW_ID)
        self.assertTrue(receipt["release_allowed"], receipt)
        self.assertEqual(receipt["r26_contract"], "ENFORCED")
        self.assertTrue(receipt["checks"]["r26_fantasy_evidence"])
        self.assertTrue(receipt["checks"]["r25_reader_evidence"])

    def test_malformed_review_blocks_before_any_story_bytes_written(self):
        self.payload["fantasy_review"]["source_episode_id"] = "not-canon-head"
        self.write()
        with self.assertRaises(GateError):
            self.run_archive()
        self.assertFalse((self.root / "episodes" / NEW_ID).exists())

    def test_new_v2_is_rejected_after_r26_but_historical_v2_remains_compatible(self):
        self.payload["schema"] = "worldroot-draft-inbox-v2"
        self.payload.pop("fantasy_review")
        self.write()
        with self.assertRaisesRegex(GateError, "R26"):
            self.run_archive()

    def test_v3_readback_after_head_advances_stays_idempotent(self):
        self.run_archive()
        head = self.root / "canon" / "HEAD.json"
        data = load(head)
        data.update({"episode_id": NEW_ID, "day": 563, "part": "V", "hour": "22h43"})
        head.write_bytes(canonical(data))
        self.assertEqual(self.run_archive()["changed_file_count"], 0)

    def test_tampered_r26_sidecar_cannot_release(self):
        self.run_archive()
        path = self.root / "episodes" / NEW_ID / "review" / "fantasia_r26.json"
        path.write_text('{"schema":"fake"}', encoding="utf-8")
        with patch("worldroot.delivery_gate.presentation_preflight",
                   return_value={"errors": [], "status": "OK"}):
            receipt = audit_release(self.root, NEW_ID)
        self.assertFalse(receipt["release_allowed"])
        self.assertTrue(receipt["errors"])


if __name__ == "__main__":
    unittest.main()
