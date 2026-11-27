"""Additional production-contract and end-to-end synthetic regressions."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from worldroot import r33_runtime as runtime
from worldroot.editorial_guard import load_policy
from worldroot.editorial_receipt import prepare_editorial_receipt
from worldroot.git_cycle import canonical, load
from worldroot.delivery_gate import audit_release
from worldroot.ledger import GateError
import test_delivery_gate as fixture_module
import test_r34_experience as intent_fixture
import test_r35_longform as plan_fixture
import test_r35_refinement as refinement_fixture


class ProductionEditorialIntegration(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.ReaderDeliveryGateTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.ident = "LV-C15-PII-D529-SYNTHETIC"
        self.head = load(self.root/"canon/HEAD.json")
        self.auth = {"choice_sha256": "synthetic", "choice": {"option": 4}}
        self.request = intent_fixture.R34Tests().request()
        self.request["requirements"].append({"id": "hist2", "domain": "identity",
                                             "critical": True, "query": "Synthetic second reference"})
        self.request["reviewed"]["hist2"] = {"source": "synthetic"}
        self.request["scene_plan"][0]["ids"].append("hist2")
        self.request["scene_plan"][0]["purpose"] = "Synthetic integrated scene"
        self.request["domain_review"] = {k: {"applicable": any(r["domain"] == k for r in self.request["requirements"]),
                                              "reason": "Synthetic domain fixture"} for k in runtime.DOMAINS}
        plan = plan_fixture.plan()["r35_plan"]
        plan["part"] = "II"
        plan["references"] = ["hist", "hist2"]
        refinement = refinement_fixture.RefinementTests().fixture()[0]["r35_plan"]["refinement"]
        for axis in refinement["axes"].values():
            axis["reference_id"] = "hist"
        refinement["identity_recovery"][0]["character"] = "Pessoa"
        plan["refinement"] = refinement
        self.request.update(schema="worldroot-r33-request-v1", project="CRONICAS_DE_UM_NOVO_MUNDO",
                            delivery_id=self.ident, head=self.head, choice_sha256="synthetic", r35_plan=plan)
        self.request_path = self.root/"requests"/(self.ident+".json")
        self.request_path.parent.mkdir()
        self.prep_path = self.root/"preparations"/(self.ident+".json")
        self.inbox_path = self.root/"inbox"/(self.ident+".json")
        self.fixture.inbox.rename(self.inbox_path)
        self.fixture.inbox = self.inbox_path

    def prepare(self, request):
        self.request_path.write_bytes(canonical(request))
        with patch.object(runtime, "author_context", return_value=self.auth), \
             patch.object(runtime, "review_creation", return_value={"status": "REVIEWED_EVIDENCE_THRESHOLD_MET"}):
            return runtime.prepare_from_request(self.root, request)

    def test_new_request_cannot_omit_r34_r35(self):
        for keys in (("r34_intent", "r35_plan"), ("r35_plan",)):
            request = copy.deepcopy(self.request)
            for key in keys:
                del request[key]
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                self.prepare(request)
            self.assertFalse(self.prep_path.exists())

    def test_new_request_cannot_omit_v22_refinement(self):
        request = copy.deepcopy(self.request)
        del request["r35_plan"]["refinement"]
        with self.assertRaises(ValueError):
            self.prepare(request)
        self.assertFalse(self.prep_path.exists())

    def test_mandatory_structural_rules_represented_at_production_budget(self):
        policy = load_policy()
        receipt = prepare_editorial_receipt(self.head, policy, 1700)
        self.assertEqual(policy["version"], 22)
        self.assertEqual(set(receipt["coverage"]["active_rule_ids"]), {"P%02d" % i for i in range(1,131)})
        self.assertTrue({"P01", "P19", "P08", "P36", "P15", "P33", "P68", "P121", "P122"} <= set(receipt["coverage"]["represented_rule_ids"]))
        self.assertNotIn("P99", receipt["coverage"]["summary_rule_ids"])

    def test_persist_submission_archive_release_history_and_tamper(self):
        result = self.prepare(self.request)
        packet = load(self.prep_path)
        self.assertEqual(result["editorial_receipt_sha256"], packet["editorial_receipt_sha256"])
        self.assertEqual(self.prepare(self.request)["result"], "IDEMPOTENT")
        payload = load(self.inbox_path)
        payload["delivery_id"] = self.ident
        payload["metadata"]["worldroot_revision"] = 35
        payload["r32_review"] = {k: packet[k] for k in ("requirements", "reviewed", "domain_review")}
        payload["r32_review"]["scene_requirements"] = [{"scene": x["scene"], "ids": x["ids"]} for x in packet["scene_plan"]]
        payload["r32_review"]["arc_packet"] = {"options": [{"promise": c["description"]} for c in payload["choices"][:4]]}
        payload["r33_review"] = {
            "preparation_sha256": packet["preparation_sha256"],
            "editorial_receipt_sha256": packet["editorial_receipt_sha256"],
            "reviews": {k: {"status": "held", "reason": "Synthetic fixture with no literary judgment"} for k in runtime.REVIEWS},
        }
        payload["r34_review"] = {"synthetic": 34}
        payload["r35_review"] = {"synthetic": 35}
        prose = payload["prose"]
        payload["longform_segments"] = []
        for i, chunk in enumerate((prose[:len(prose)//2], prose[len(prose)//2:]), 1):
            relative = f"production/{self.ident}/segments/{i:02d}.md"
            path = self.root/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(chunk.encode())
            payload["longform_segments"].append({"part": i, "path": relative, "sha256": hashlib.sha256(chunk.encode()).hexdigest()})
        self.inbox_path.write_bytes(canonical(payload))
        # Only independent R32/R34/R35 literary-delivery validators are isolated;
        # real preparation validators, editorial verification, archive, manifests,
        # segment readback and history/release consumers execute unchanged.
        with patch.object(runtime, "author_context", return_value=self.auth), \
             patch.object(runtime, "release_review", return_value={"synthetic": 32}), \
             patch("worldroot.r32_release.release_review", return_value={"synthetic": 32}), \
             patch("worldroot.r34_experience.validate_delivery", return_value={"synthetic": 34}) as r34, \
             patch("worldroot.r35_longform.validate_delivery", return_value={"synthetic": 35}) as r35:
            rr = runtime.verify_submission(self.root, self.head, payload)
            self.assertTrue(rr["editorial"]["integrity_verified"])
            self.assertFalse(rr["editorial"]["generation_evaluated"])
            self.fixture.archive_synthetic()
            r34.assert_called()
            r35.assert_called()
        with patch("worldroot.delivery_gate.presentation_preflight", return_value={"errors": []}):
            release = audit_release(self.root, self.ident)
            self.assertTrue(release["release_allowed"], release)
            self.assertTrue(release["checks"]["editorial_preparation_integrity"])
        self.assertEqual(runtime.verify_history(self.root)["verified_r33_receipts"], 1)
        self.assertEqual(self.fixture.archive_synthetic()["changed_file_count"], 0)
        before = self.prep_path.read_bytes()
        # Historic readback never consults the replacement current policy.
        with patch.object(runtime, "load_policy", side_effect=AssertionError("Do not replay current policy")):
            self.assertEqual(runtime.verify_history(self.root)["verified_r33_receipts"], 1)
        self.assertEqual(self.prep_path.read_bytes(), before)
        sidecar = self.root/"episodes"/self.ident/"review/preparation_r33.json"
        sidecar.unlink()
        with self.assertRaises((ValueError, GateError)):
            runtime.verify_history(self.root)
        self.assertFalse(audit_release(self.root, self.ident)["release_allowed"])
