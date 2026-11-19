"""WORLDROOT prepared-source provenance for NEW Livro VI inbox episodes.

Creates only verifiable sidecars from the exact explicitly submitted inbox;
never asserts independent UI export parity or silently resolves character flags.
The upstream main engine must have archived the same source first.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validate_episode_archive import ArchiveInvalid
from verify_lvi_original import verify_lvi


REQUIRED_CHARACTER_FIELDS = (
    "name", "last_physical_appearance_source", "location_at_scene",
    "affiliation_at_scene", "knowledge_at_scene"
)


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def write_once(path: Path, body: bytes):
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != body:
            raise ArchiveInvalid("Immutable source/review conflict: " + path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def prepare_lvi(root: Path, episode_id: str) -> dict:
    if not episode_id.startswith("LVI-"):
        return {"status": "NOT_LVI", "episode_id": episode_id}
    if (root / "editorial/rejections" / (episode_id + ".json")).exists():
        raise ArchiveInvalid("Rejected Livre VI source cannot be republished")

    inbox = root / "inbox" / (episode_id + ".json")
    if not inbox.is_file() or inbox.is_symlink():
        raise ArchiveInvalid("Missing assistant-prepared literal inbox")
    payload = json.loads(inbox.read_text(encoding="utf-8"))
    text = payload.get("full_text")
    if payload.get("delivery_id") != episode_id or not isinstance(text, str) or not text.strip():
        raise ArchiveInvalid("Inbox source identity not verified")
    body = text.encode("utf-8")
    archived = root / "episodes" / episode_id / "draft/narrativa_integral.md"
    if not archived.is_file() or archived.read_bytes() != body:
        raise ArchiveInvalid("GitHub archived draft differs from prepared source bytes")
    characters = payload.get("character_preflight")
    if not isinstance(characters, list) or not characters:
        raise ArchiveInvalid("New Livre VI requires character_preflight matrix in inbox")
    for person in characters:
        if not isinstance(person, dict) or any(
            not isinstance(person.get(f), str) or not person[f].strip()
            for f in REQUIRED_CHARACTER_FIELDS
        ):
            raise ArchiveInvalid("Incomplete character/location/knowledge matrix")
    flags = payload.get("continuity_flags", [])
    if (not isinstance(flags, list)
            or any(not isinstance(flag, str) or not flag.strip() for flag in flags)
            or len(flags) != len(set(flags))):
        raise ArchiveInvalid("Invalid continuity flags")
    review = {
        "schema": "worldroot-episode-character-preflight-v1",
        "episode_id": episode_id,
        "status": "REVIEWED_WITH_FLAGS" if flags else "REVIEWED_WITH_EVIDENCE",
        "characters": characters, "open_flags": flags,
        "review_basis": ["ASSISTANT_PREDELIVERY_CANDIDATE", "GITHUB_CANON_AND_LITERAL_REFERENCES_REQUIRED"],
        "independent_human_review": False,
        "note": "Mechanically validated candidate preflight: external truth of scene travel remains editorial.",
    }
    original = root / "editorial/recovery/originals" / (episode_id + ".txt")
    proof = {
        "schema": "worldroot-original-chat-source-proof-v1",
        "episode_id": episode_id,
        "source_kind": "ASSISTANT_PREDELIVERY_EXACT_TEXT",
        "source_locator": "PREDRAFT_SAME_TURN:inbox/" + episode_id + ".json",
        "source_file": "editorial/recovery/originals/" + episode_id + ".txt",
        "source_sha256": hashlib.sha256(body).hexdigest(),
        "source_bytes": len(body),
        "ui_parity": "NOT_INDEPENDENTLY_VERIFIED",
    }
    write_once(original, body)
    write_once(root / "episodes" / episode_id / "draft/source_proof.json", canonical(proof))
    write_once(root / "episodes" / episode_id / "review/continuity_review.json", canonical(review))
    evidence = verify_lvi(root, episode_id)
    return {"status": "PREDELIVERY_SOURCE_ARCHIVED_SHA_VERIFIED",
            "episode_id": episode_id, "sha256": evidence["sha256"],
            "ui_parity": "NOT_INDEPENDENTLY_VERIFIED",
            "continuity_flags": len(flags)}
