"""Additive editorial preparation integrity; not proof of model compliance."""
import hashlib
import json

from .editorial_guard import compact_brief, validate_policy


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def prepare_editorial_receipt(head, policy, budget=1700):
    validate_policy(policy)
    brief = compact_brief(policy, head=head, max_chars=budget)
    body = {
        "schema": "worldroot-editorial-receipt-v1",
        "head_sha256": _digest(head),
        "policy_sha256": _digest(policy),
        "budget_chars": budget,
        "text": brief["text"],
        "coverage": brief["coverage"],
        "semantic_certification": False,
    }
    return {**body, "receipt_sha256": _digest(body)}


def verify_editorial_receipt(receipt, head, policy, expected_sha256, *, expected_budget):
    """Expected digest and budget must come from trusted preparation, not inbox."""
    expected = prepare_editorial_receipt(head, policy, expected_budget)
    if (not isinstance(receipt, dict) or receipt != expected
            or expected_sha256 != expected["receipt_sha256"]):
        raise ValueError("Editorial preparation receipt mismatch")
    return {"integrity_verified": True, "semantic_certification": False,
            "generation_evaluated": False}
