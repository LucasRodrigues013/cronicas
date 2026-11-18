"""Read-only pre-book semantic baseline verification.

Safeguards the distinction between established character arcs, unresolved facts,
hypotheses and editorial-only state. This verifies SOURCE provenance, not the
literary meaning of a newly generated chapter, and never starts another book.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .ledger import GateError

NAME = re.compile(r"^[A-Z0-9][A-Z0-9-]{8,85}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"ESTABELECIDO", "EM_ABERTO", "NAO_CONFIRMADO", "EDITORIAL"}
SCHEMA = "worldroot-book-transition-baseline-v1"


def inspect_transition_baseline(root: Path, baseline: dict) -> dict:
    """Fail closed on unanchored or wrong-book context, never rewrite archive."""
    if not isinstance(baseline, dict) or baseline.get("schema") != SCHEMA:
        raise GateError("Invalid semantic transition schema")
    root = Path(root).resolve()
    head = json.loads((root / "canon" / "HEAD.json").read_text(encoding="utf-8"))
    expected = baseline.get("head_guard")
    if (not isinstance(expected, dict) or
        any(head.get(key) != expected.get(key)
            for key in ("episode_id", "sequence", "source_sha256", "book_closed", "book"))):
        raise GateError("Semantic transition baseline HEAD moved or is unverified")
    if head.get("book_closed") is not True:
        raise GateError("Cannot certify next-book preparation before current book closes")
    if baseline.get("next_book") == head.get("book") or not baseline.get("next_book"):
        raise GateError("Next book must not be identical to closed book")
    claims = baseline.get("claims")
    if not isinstance(claims, list) or len(claims) < 5:
        raise GateError("Insufficient source-backed semantic transition claims")
    ids = set()
    verified = []
    for claim in claims:
        if not isinstance(claim, dict):
            raise GateError("Malformed semantic claim")
        name, status = claim.get("id"), claim.get("status")
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{3,50}", name)
            or name in ids or status not in STATUSES):
            raise GateError("Duplicate or invalid semantic claim")
        ids.add(name)
        ep, dig = claim.get("episode_id"), claim.get("source_sha256")
        anchor = claim.get("literal_anchor")
        guidance = claim.get("continuation_rule")
        if (not isinstance(ep, str) or not NAME.fullmatch(ep)
            or not isinstance(dig, str) or not SHA.fullmatch(dig)
            or not isinstance(anchor, str) or len(anchor) < 12
            or not isinstance(guidance, str) or len(guidance.strip()) < 40):
            raise GateError("Semantic claim lacks source or concrete continuation rule")
        path = root / "episodes" / ep / "draft" / "narrativa_integral.md"
        closure = root / "canon" / "episodes" / (ep + ".json")
        if not path.is_file() or path.is_symlink() or not closure.is_file():
            raise GateError("Semantic source episode not immutable/closed")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != dig:
            raise GateError("Semantic source SHA256 mismatch")
        source = data.decode("utf-8", errors="strict")
        if anchor not in source:
            raise GateError("Semantic claim literal anchor not found in source episode")
        journal = json.loads(closure.read_text(encoding="utf-8"))
        if journal.get("story_sha256") != dig or journal.get("status") != "FECHADO_GITHUB":
            raise GateError("Semantic source not linked to verified canon journal")
        verified.append({"id": name, "status": status, "episode_id": ep,
                         "rule": guidance.strip()})
    return {
        "status": "SOURCE_VERIFIED_BOOK_TRANSITION_REVIEW_REQUIRED",
        "head_episode": head["episode_id"],
        "head_book_closed": True,
        "next_book": baseline["next_book"],
        "claims_verified": len(verified),
        "narrative_guide": verified,
        "next_book_started": False,
        "canon_changed": False,
        "drive_changed": False,
        "semantic_quality_certified": False,
        "character_knowledge_certified": False,
    }
