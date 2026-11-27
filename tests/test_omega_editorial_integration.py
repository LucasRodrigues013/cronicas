"""Synthetic OMEGA-005 integration regressions; no private material."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from worldroot import r33_runtime as runtime
from worldroot.editorial_guard import load_policy
from worldroot.editorial_receipt import prepare_editorial_receipt
from worldroot.git_cycle import canonical
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release
from worldroot.ledger import GateError
import test_delivery_gate as gate_fixture


class EditorialIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.head = dict(book="Livro VI", chapter=7, part="V", day=573,
                         episode_id="OLD-001", sequence=44)
        self.ident = "NEW-001"
        self.requirements = [{"id": "a", "query": "synthetic", "domain": "identity", "critical": True}]
        self.domains = {k: {"applicable": k == "identity", "reason": "synthetic"} for k in runtime.DOMAINS}
        self.scenes = [{"scene": 1, "purpose": "synthetic", "ids": ["a"]}]

    def prepare(self):
        with patch.object(runtime, "author_context", return_value={"choice_sha256": "synthetic"}), \
             patch.object(runtime, "review_creation", return_value={"status": "REVIEWED_EVIDENCE_THRESHOLD_MET"}):
            return runtime.preparation(self.root, self.head, self.ident, self.requirements,
                                       {}, self.domains, self.scenes)

    def payload(self, packet):
        return {"delivery_id": self.ident, "metadata": {"worldroot_revision": 33},
                "r33_review": {"preparation_sha256": packet["preparation_sha256"],
                               "editorial_receipt_sha256": packet["editorial_receipt_sha256"]}}

    def test_preparation_contains_editorial_pin(self):
        packet = self.prepare()
        self.assertEqual(packet["editorial_receipt"]["receipt_sha256"], packet["editorial_receipt_sha256"])
        self.assertEqual(packet["editorial_receipt"]["budget_chars"], 1700)
        self.assertFalse(packet["editorial_receipt"]["semantic_certification"])

    def test_verify_preparation_editorial_roundtrip(self):
        packet = self.prepare()
        result = runtime.verify_preparation_editorial(packet, self.payload(packet), self.head)
        self.assertTrue(result["integrity_verified"])
        self.assertFalse(result["generation_evaluated"])

    def test_missing_acknowledgement(self):
        packet = self.prepare()
        payload = self.payload(packet)
        del payload["r33_review"]["editorial_receipt_sha256"]
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, payload, self.head)

    def test_missing_receipt(self):
        packet = self.prepare()
        payload = self.payload(packet)
        del packet["editorial_receipt"]
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, payload, self.head)

    def test_altered_text(self):
        packet = self.prepare()
        payload = self.payload(packet)
        packet["editorial_receipt"]["text"] += " changed"
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, payload, self.head)

    def test_budget_recomputed_and_echoed(self):
        packet = self.prepare()
        receipt = prepare_editorial_receipt(self.head, load_policy(), 900)
        packet["editorial_receipt"] = receipt
        packet["editorial_receipt_sha256"] = receipt["receipt_sha256"]
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, self.payload(packet), self.head)

    def test_policy_changed(self):
        packet = self.prepare()
        policy = copy.deepcopy(load_policy())
        policy["version"] += 1
        with patch.object(runtime, "load_policy", return_value=policy), self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, self.payload(packet), self.head)

    def test_head_changed(self):
        packet = self.prepare()
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, self.payload(packet), {**self.head, "day": 574})

    def test_preparation_downgrade_is_rejected(self):
        packet = self.prepare()
        payload = self.payload(packet)
        payload["metadata"]["worldroot_revision"] = 32
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, payload, self.head)

    def test_r35_cannot_be_downgraded_to_r33(self):
        packet = self.prepare()
        packet["r35_plan"] = {}
        with self.assertRaises(ValueError):
            runtime.verify_preparation_editorial(packet, self.payload(packet), self.head)


class ConsumerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = gate_fixture.ReaderDeliveryGateTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.ident = gate_fixture.ID

    def write_preparation(self):
        path = self.root / "preparations" / (self.ident + ".json")
        path.parent.mkdir()
        path.write_bytes(canonical({"schema": "worldroot-r33-preparation-v1", "delivery_id": self.ident}))

    def test_inbox_cannot_omit_r33_when_preparation_exists(self):
        self.write_preparation()
        with self.assertRaises(GateError):
            self.fixture.archive_synthetic()
        self.assertFalse((self.root / "episodes" / self.ident / "draft" / "manifesto_imutavel.json").exists())

    def test_delivery_cannot_ignore_preparation_without_sidecar(self):
        self.fixture.archive_synthetic()
        self.write_preparation()
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}):
            result = audit_release(self.root, self.ident)
        self.assertFalse(result["release_allowed"])

    def test_history_cannot_ignore_missing_r33_sidecar(self):
        self.fixture.archive_synthetic()
        self.write_preparation()
        with self.assertRaises((ValueError, GateError)):
            runtime.verify_history(self.root)

    def test_legacy_without_preparation_is_read_only(self):
        self.fixture.archive_synthetic()
        before = self.fixture.inbox.read_bytes()
        self.assertEqual(runtime.verify_history(self.root)["verified_r33_receipts"], 0)
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}):
            self.assertTrue(audit_release(self.root, self.ident)["release_allowed"])
        self.assertEqual(self.fixture.inbox.read_bytes(), before)
