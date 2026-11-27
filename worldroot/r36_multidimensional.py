"""R36 multidimensional candidate-only gate; never writes canon or promotes fields."""
from __future__ import annotations
from .natural_codex import CHAR_FIELDS, validate_fields, PRIVATE_FIELDS, PRIVATE_SCOPES
from .complementary_recovery import DOMAINS, digest

def verify_observations(text, observations):
    lines = text.split("\n")
    seen = set()
    out = []
    for row in observations:
        n = row["line"]
        if type(n) is not int or not 1 <= n <= len(lines) or lines[n-1] != row["anchor"] or not row["anchor"].strip():
            raise ValueError("Literal evidence mismatch")
        if row.get("scope") not in ("UNKNOWN", "RESTRICTED", "PUBLIC") or row.get("status") != "AUTHOR_GATE_PENDING":
            raise ValueError("Candidate scope or gate invalid")
        if n in seen:
            raise ValueError("Duplicate evidence line")
        seen.add(n)
        out.append({**row, "anchor_sha256": digest(row["anchor"])})
    return sorted(out, key=lambda row: row["line"])

def verify_candidate_batch(doc, source):
    policy = doc["policy"]
    if policy["days"] != [1, 579] or set(policy["dimensions"]) != DOMAINS or policy["required_character_fields"] != len(CHAR_FIELDS):
        raise ValueError("Native schema or coverage mismatch")
    if not policy["production_hold"] or not policy["author_gate"] or doc["canon_changed"] is not False or doc["production_activated"] is not False:
        raise ValueError("Production hold required")
    ids = set()
    anchors = 0
    for card in doc["profiles"]:
        if card["id"] in ids or card["domain"] not in DOMAINS or card["status"] != "AUTHOR_GATE_PENDING" or card["canon_changed"] is not False:
            raise ValueError("Invalid candidate identity")
        ids.add(card["id"])
        rows = verify_observations(source, card["temporal_observations"])
        anchors += len(rows)
        for field in card["fields"].values():
            if field["status"] != "PENDENTE_FONTE" or field["semantic_review_pending"] is not True:
                raise ValueError("Unapproved field promotion")
            verify_observations(source, field["evidence"])
    return {"candidates": len(ids), "anchors": anchors, "semantic_certification": False, "production_hold": True}

def verify_protected_profiles(before, after, allowed=()):
    """Compare native field entries exactly; all exceptions need separate author gate."""
    if set(before) != set(after):
        raise ValueError("Identity set changed")
    allowed = set(allowed)
    changed = set()
    for ident, old in before.items():
        new = after[ident]
        if set(old) != set(new):
            raise ValueError("Field set changed")
        for key, value in old.items():
            if value == new[key]:
                continue
            if key in PRIVATE_FIELDS or value.get("scope") in PRIVATE_SCOPES or value.get("status") in ("SEGREDO", "CANONICO"):
                raise ValueError("Protected field changed")
            if (ident, key) not in allowed:
                raise ValueError("Unapproved field change")
            changed.add((ident,key))
    return changed
