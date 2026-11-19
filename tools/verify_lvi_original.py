"""WORLDROOT LVI external-source gate. No file writes or canon promotion.

An internally consistent archive is not proof of fidelity to an original
ChatGPT message. For NEW Livre VI episodes require an independently provided
literal source, a readback hash, anchored events and a continuity review.
Older rejected r17 is retained exclusively for audit, never accepted here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_episode_archive import verify_one, ArchiveInvalid

REJECTED = "LVI-C01-PI-D538-AUTHOR-SOURCE"
REJECTED_SHA256 = "bde62ddbd8ac0977925a7ed74e9abb09c461d53cb08f36a1e245ab20a212a3da"
PARTS = (
    "LVI-C01-PI-D538-REAUTHORIZED-R2-AUTHOR-SOURCE",
    "LVI-C01-PII-D538-AUTHOR-SOURCE",
    "LVI-C01-PIII-D539-AUTHOR-SOURCE",
)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveInvalid(f"{path}: missing or invalid JSON") from exc

def verify_lvi(root: Path, episode_id: str) -> dict:
    if not episode_id.startswith("LVI-") or episode_id == REJECTED:
        raise ArchiveInvalid(f"Unexpected or rejected episode id: {episode_id}")

    folder = root / "episodes" / episode_id / "draft"
    narrative_file = folder / "narrativa_integral.md"
    proof_file = folder / "source_proof.json"
    source_file = root / "editorial" / "recovery" / "originals" / (episode_id + ".txt")
    review_file = root / "episodes" / episode_id / "review" / "continuity_review.json"

    if not (narrative_file.is_file() and proof_file.is_file()
            and source_file.is_file() and review_file.is_file()):
        raise ArchiveInvalid(f"{episode_id}: missing literal export/proof/archive/review (FAIL CLOSED)")

    source = source_file.read_bytes()
    archived = narrative_file.read_bytes()
    if not source or source != archived:
        raise ArchiveInvalid(f"{episode_id}: original export and archived narrative differ")
    if digest(source) == REJECTED_SHA256:
        raise ArchiveInvalid(f"{episode_id}: rejected r17 narrative may not be reused")

    proof = read_json(proof_file)
    if not isinstance(proof, dict):
        raise ArchiveInvalid(f"{episode_id}: source proof is not an object")
    if (proof.get("schema") != "worldroot-original-chat-source-proof-v1"
            or proof.get("episode_id") != episode_id
            or proof.get("source_kind") not in (
                "USER_SUPPLIED_CHAT_EXPORT", "USER_SUBMITTED_LITERAL_TEXT")
            or proof.get("source_sha256") != digest(source)
            or type(proof.get("source_bytes")) is not int
            or proof.get("source_bytes") != len(source)
            or proof.get("source_file") != str(source_file.relative_to(root))
            or not isinstance(proof.get("source_locator"), str)
            or not proof["source_locator"].strip()):
        raise ArchiveInvalid(f"{episode_id}: independent source proof invalid")
    try:
        source.decode("utf-8")
    except UnicodeError as exc:
        raise ArchiveInvalid(f"{episode_id}: exported source is not UTF-8") from exc

    archive = verify_one(folder / "manifesto_imutavel.json")
    if archive["sha256"] != digest(source):
        raise ArchiveInvalid(f"{episode_id}: archive and original SHA256 diverge")

    events = read_json(folder / "eventos_e_consequencias.json")
    if not isinstance(events, list) or not events:
        raise ArchiveInvalid(f"{episode_id}: zero source-anchored events")
    original_text = source.decode("utf-8")
    for i, event in enumerate(events, 1):
        anchor = event.get("source_anchor") if isinstance(event, dict) else None
        if not isinstance(anchor, str) or not anchor.strip() or anchor not in original_text:
            raise ArchiveInvalid(f"{episode_id}: event {i} lacks a literal source anchor")

    review = read_json(review_file)
    if (not isinstance(review, dict)
            or review.get("episode_id") != episode_id
            or review.get("status") != "REVIEWED_WITH_EVIDENCE"
            or not isinstance(review.get("characters"), list)
            or not review["characters"]):
        raise ArchiveInvalid(f"{episode_id}: continuity review missing or incomplete")
    for item in review["characters"]:
        if (not isinstance(item, dict) or not item.get("name")
                or not item.get("last_physical_appearance_source")
                or not item.get("location_at_scene")
                or not item.get("affiliation_at_scene")
                or not item.get("knowledge_at_scene")):
            raise ArchiveInvalid(f"{episode_id}: incomplete character location/agency matrix")

    if episode_id == PARTS[2]:
        fix = root / "editorial" / "recovery" / "reconciliations" / (episode_id + ".json")
        resolution = read_json(fix)
        if (not isinstance(resolution, dict)
                or resolution.get("issue") != "CAEDREN_ROLE_LOCATION"
                or resolution.get("status") != "APPROVED_BY_AUTHOR"
                or not resolution.get("source_evidence")
                or not resolution.get("author_decision")):
            raise ArchiveInvalid("D539 Caedren contradiction is not author-reconciled")

    return {"episode_id": episode_id, "bytes": len(source),
            "sha256": digest(source), "result": "ORIGINAL_MATCHED_ARCHIVE_REVIEWED"}

def main() -> int:
    p = argparse.ArgumentParser(description="Verify exact original Livro VI episode against GitHub archive")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--require-all", action="store_true",
                   help="fail if any D538-D539 episode is not yet archived")
    args = p.parse_args()
    root = args.root
    present = sorted(p.parent.name for p in (root / "episodes").glob("LVI-*/draft")
                     if p.parent.name != REJECTED)
    if args.require_all and not all(e in present for e in PARTS):
        print("BLOCKED: not all D538-D539 literal episode packages exist")
        return 1
    try:
        for episode_id in present:
            result = verify_lvi(root, episode_id)
            print(f"EXACT-READBACK {result['episode_id']}: {result['bytes']} bytes SHA256 {result['sha256']}")
    except (ArchiveInvalid, OSError) as exc:
        print("WORLDROOT ORIGINAL-SOURCE GATE BLOCKED:", exc)
        return 1
    if not present:
        print("NO NEW LVI ARCHIVES: original D538-D539 sources still needed; nothing promoted")
    else:
        print("External-source gate passed for present archives only; not an approval to promote canon")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
