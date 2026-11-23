"""R27: a summary or absent readback can never authorize another chapter."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from worldroot.turn_continuity import audit_turn_handoff

PREV = "LVI-C06-PV-D568-AUTHOR-SOURCE"
HEAD = "LVI-C06-PIV-D567-AUTHOR-SOURCE"


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


class TurnHandoffTest(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.story = self.root / "episodes" / PREV / "draft/narrativa_integral.md"
        self.story.parent.mkdir(parents=True)
        self.full = "## I — Cena\n**LUCAS —** Oi\n## ESCOLHAS\n1 2 3 4 5\n"
        self.story.write_text(self.full, encoding="utf-8")
        self.sha = hashlib.sha256(self.story.read_bytes()).hexdigest()
        write(self.root / "canon/HEAD.json", {
            "schema": "worldroot-git-canon-v1", "episode_id": HEAD,
            "book": "Livro VI", "chapter": 6, "part": "IV", "day": 567})
        write(self.root / "episodes" / PREV / "draft/checkpoint_candidato.json", {
            "canon_status": "RASCUNHO", "book": "Livro VI",
            "chapter": 6, "part": "V", "day": 568})
        write(self.root / "inbox" / (PREV + ".json"), {
            "delivery_id": PREV, "prose": "## I — Cena\n", "full_text": self.full})
        write(self.root / "episodes" / PREV / "draft/manifesto_imutavel.json", {
            "delivery_id": PREV, "original_readback_sha256": self.sha,
            "artifacts": {"narrativa_integral.md": {
                "sha256": self.sha, "bytes": len(self.story.read_bytes())}}})
        self.receipt = (self.root / "delivery/reader_receipts" / (PREV + ".json"))
        write(self.receipt, {
            "schema": "worldroot-reader-release-receipt-v1",
            "episode_id": PREV,
            "status": "ARCHIVED_DRAFT_VERIFIED_FOR_READER",
            "story_sha256": self.sha,
            "source_path": "episodes/" + PREV + "/draft/narrativa_integral.md"})
        write(self.root / "ops/RESUME.json", {
            "canon_head": {"episode_id": HEAD},
            "latest_unclosed_draft": {"episode_id": PREV}})

    def run_gate(self, **kwargs):
        with patch("worldroot.turn_continuity.audit_release",
                   return_value={"release_allowed": True, "story_sha256": self.sha}):
            return audit_turn_handoff(self.root, PREV, **kwargs)

    def test_saved_previous_draft_verified_without_promoting(self):
        r = self.run_gate(expected_head_id=HEAD)
        self.assertTrue(r["ready"], r)
        self.assertFalse(r["canon_changed"])
        self.assertFalse(r["automatic_chat_capture"])

    def test_missing_inbox_blocks(self):
        (self.root / "inbox" / (PREV + ".json")).unlink()
        self.assertFalse(self.run_gate()["ready"])

    def test_absent_full_story_blocks(self):
        self.story.unlink()
        self.assertFalse(self.run_gate()["ready"])

    def test_missing_receipt_blocks(self):
        self.receipt.unlink()
        self.assertFalse(self.run_gate()["ready"])

    def test_forged_receipt_sha_blocks(self):
        rec = json.loads(self.receipt.read_text(encoding="utf-8"))
        rec["story_sha256"] = "0" * 64
        write(self.receipt, rec)
        self.assertFalse(self.run_gate()["ready"])

    def test_summary_substituted_for_story_blocks(self):
        self.story.write_text("Only summary", encoding="utf-8")
        self.assertFalse(self.run_gate()["ready"])

    def test_wrong_head_blocks(self):
        self.assertFalse(self.run_gate(
            expected_head_id="LVI-C06-PIII-D566-AUTHOR-SOURCE")["ready"])

    def test_resuming_older_part_when_newer_draft_exists_blocks(self):
        write(self.root / "ops/RESUME.json", {
            "canon_head": {"episode_id": HEAD},
            "latest_unclosed_draft": {"episode_id": "LVI-C07-PI-D569-AUTHOR-SOURCE"}})
        self.assertFalse(self.run_gate()["ready"])

    def test_without_real_choice_canon_claim_blocks(self):
        self.assertFalse(self.run_gate(require_canon_promotion=True)["ready"])

    def test_post_choice_matching_canon_can_pass(self):
        write(self.root / "canon/HEAD.json", {
            "schema": "worldroot-git-canon-v1", "episode_id": PREV,
            "book": "Livro VI", "chapter": 6, "part": "V", "day": 568})
        write(self.root / "ops/RESUME.json", {
            "canon_head": {"episode_id": PREV},
            "latest_unclosed_draft": {"episode_id": "LVI-C07-PI-D569-AUTHOR-SOURCE"}})
        write(self.root / "canon/episodes" / (PREV + ".json"), {
            "episode_id": PREV, "story_sha256": self.sha})
        write(self.root / "choices" / PREV / "option-4.json", {
            "episode_id": PREV, "option": 4, "author_source": "USER_MESSAGE"})
        self.assertTrue(self.run_gate(require_canon_promotion=True)["ready"])


if __name__ == "__main__":
    unittest.main()
