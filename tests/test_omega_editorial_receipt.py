import copy
import unittest

from worldroot.editorial_guard import load_policy
from worldroot.editorial_receipt import prepare_editorial_receipt, verify_editorial_receipt


class EditorialReceiptTests(unittest.TestCase):
    def setUp(self):
        self.head = dict(book="Livro VI", chapter=7, part="V", day=573,
                         episode_id="synthetic", sequence=44)
        self.policy = load_policy()
        self.receipt = prepare_editorial_receipt(self.head, self.policy, 900)

    def verify(self, receipt, head=None, policy=None, digest=None, budget=900):
        return verify_editorial_receipt(
            receipt, head or self.head, policy or self.policy,
            digest if digest is not None else self.receipt["receipt_sha256"],
            expected_budget=budget)

    def test_roundtrip_not_semantic(self):
        result = self.verify(self.receipt)
        self.assertTrue(result["integrity_verified"])
        self.assertFalse(result["semantic_certification"])
        self.assertFalse(result["generation_evaluated"])

    def test_text_mutation(self):
        changed = copy.deepcopy(self.receipt)
        changed["text"] += " altered"
        with self.assertRaises(ValueError):
            self.verify(changed)

    def test_false_coverage(self):
        changed = copy.deepcopy(self.receipt)
        changed["coverage"]["application_certified"] = True
        with self.assertRaises(ValueError):
            self.verify(changed)

    def test_head_substitution(self):
        with self.assertRaises(ValueError):
            self.verify(self.receipt, head={**self.head, "day": 574})

    def test_policy_substitution(self):
        changed = copy.deepcopy(self.policy)
        changed["version"] += 1
        with self.assertRaises(ValueError):
            self.verify(self.receipt, policy=changed)

    def test_budget_substitution(self):
        with self.assertRaises(ValueError):
            self.verify(self.receipt, budget=1750)

    def test_missing_or_wrong_digest(self):
        for receipt, digest in [(None, None), (self.receipt, "0"*64)]:
            with self.assertRaises(ValueError):
                self.verify(receipt, digest=digest)

    def test_recomputed_receipt_cannot_replace_trusted_pin(self):
        replacement = prepare_editorial_receipt(self.head, self.policy, 1750)
        with self.assertRaises(ValueError):
            self.verify(replacement, budget=1750)
