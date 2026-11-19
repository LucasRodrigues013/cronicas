"""WORLDROOT one-message draft intake: exact prose -> immutable GitHub private package.

An explicit connected ChatGPT tool must create inbox/<delivery_id>.json on the
private story-archive branch. A GitHub Action checks it and publishes a six-file
draft with verified SHA256 plus evidence-linked semantic review. It does NOT
generate the story itself, alter the canonical HEAD or call Google.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .episode_pipeline import EpisodeDraft
from .git_cycle import (load, canonical, sha, check_id, verify_episode,
                        review_deltas, _chronology)
from .semantic_gate import require_reviewed_event_evidence
from .ledger import GateError, ConflictError
from .editorial_guard import quick_preflight
from .presentation_guard import presentation_preflight
from .story_focus_audit import inspect_installment
from .day_arc_audit import inspect_day_arc
from .lived_narrative_audit import inspect_lived_narrative
from .story_dynamics import inspect_draft_dynamics
from .longform_depth import inspect_longform
from .longform_segments import verify_longform_segments
from .book_closure import require_book_end_approval

NARRATIVE_LIMIT = 500_000
INBOX_LIMIT = 1_000_000


def _bytes(obj):
    return canonical(obj)


def _assemble(episode_id: str, payload: dict, *, enforce_presentation: bool = True,
              book_end_approval_verified: bool = False):
    if (payload.get("schema") != "worldroot-draft-inbox-v1"
            or payload.get("delivery_id") != episode_id):
        raise GateError("Inbox schema or immutable ID mismatch")
    text = payload.get("full_text")
    prose = payload.get("prose")
    if not isinstance(text, str) or len(text.encode("utf-8")) > NARRATIVE_LIMIT:
        raise GateError("Exact chapter must be text within the 500 KB limit")
    if not isinstance(prose, str) or not text.startswith(prose):
        raise GateError("Narrative prose is not the exact prefix of published content")
    if payload.get("book_closed") not in (True, False):
        raise GateError("Explicit book closure boolean required")
    if payload["book_closed"] and not book_end_approval_verified:
        raise GateError("Cannot close book without verified author approval")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("canon_status") != "RASCUNHO":
        raise GateError("Draft metadata must state RASCUNHO")
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 5:
        raise GateError("A chapter must include five ordered choices")
    if payload.get("editorial_visibility") != "PRIVADO":
        raise GateError("All unreviewed chapters must remain private")
    structured = {
        "delivery_id": episode_id, "prose": prose, "full_text": text,
        "metadata": metadata, "choices": choices, "events": [],
        "book_closed": payload["book_closed"], "editorial_visibility": "PRIVADO",
    }
    try:
        draft = EpisodeDraft.from_dict(structured)
        draft.validate()
    except (KeyError, TypeError, ValueError) as exc:
        raise GateError("Episode structure invalid: " + str(exc)[:120]) from None

    # Cheap editorial contract: prohibit image embeds; flag, but never
    # automatically rewrite, short dialogue-free or otherwise unusual scenes.
    editorial = quick_preflight(prose, scene_tags=payload.get("editorial_tags", ()))
    if editorial["errors"]:
        raise GateError("Authorial editorial policy violated: " + "; ".join(editorial["errors"]))

    # Mandatory visual structure for NEW chapters. Existing immutable drafts
    # are exempt solely for idempotent readback; they must not be rewritten.
    if enforce_presentation:
        visual = presentation_preflight(text)
        if visual["errors"]:
            raise GateError("Chat presentation contract failed: " + "; ".join(visual["errors"])[:350])

    # The 10k target is now NON-BLOCKING editorial guidance: a genuine ending
    # is better than resetting arcs or padding prose. UI never counts as story.
    if enforce_presentation:
        inspect_longform(prose)

    events = payload.get("reviewed_events")
    knowledge = payload.get("reviewed_knowledge")
    if not isinstance(events, list) or not events or not isinstance(knowledge, list):
        raise GateError("Cannot auto-archive without explicit reviewed events and knowledge list")
    story_sha = sha(text.encode("utf-8"))
    populated_events = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("source"), dict):
            raise GateError("Reviewed event must have a literal source line")
        normalized = dict(event)
        source = dict(event["source"])
        if source.get("sha256") not in (None, story_sha):
            raise GateError("Event source SHA does not match original chapter")
        source["sha256"] = story_sha
        normalized["source"] = source
        populated_events.append(normalized)
    require_reviewed_event_evidence(draft, populated_events)
    reviewed_events = {
        "schema": "worldroot-reviewed-events-v1", "episode_id": episode_id,
        "review_status": "REVISADO", "source_sha256": story_sha,
        "review_note": "Assistant-prepared candidate review; exact textual anchors checked automatically; not independently human certified.",
        "events": populated_events,
    }
    reviewed_knowledge = {
        "schema": "worldroot-reviewed-knowledge-v1", "episode_id": episode_id,
        "review_status": "REVISADO", "knowledge": knowledge,
        "review_note": "Only explicitly attributed NPC knowledge is recorded. Unknown times remain unknown.",
    }
    files = {
        "narrativa_integral.md": text.encode("utf-8"),
        "opcoes.json": _bytes(choices),
        "eventos_e_consequencias.json": _bytes([]),
        "checkpoint_candidato.json": _bytes(metadata),
        "episode_draft.json": _bytes(structured),
    }
    manifest = {
        "schema": "worldroot-episode-package-v1",
        "delivery_id": episode_id, "canon_status": "RASCUNHO",
        "original_readback_sha256": story_sha,
        "artifacts": {
            name: {"sha256": sha(blob), "bytes": len(blob)}
            for name, blob in files.items()
        },
        "external_saving": "GITHUB_PRIVADO_SEM_OIDC",
        "github_full_story": True,
    }
    files["manifesto_imutavel.json"] = _bytes(manifest)
    review_files = {
        "eventos_revisados.json": _bytes(reviewed_events),
        "conhecimento_revisado.json": _bytes(reviewed_knowledge),
    }
    return draft, files, review_files


def _write_safe(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != content:
            raise ConflictError("Attempt to change immutable episode artifact: " + path.name)
        return False
    path.write_bytes(content)
    return True


def _focus_receipt(prose: str) -> dict:
    """Non-blocking, O(n) scene depth signal; never a quality verdict."""
    review = inspect_installment(prose)
    return {
        "status": review["status"],
        "scenes": review["scene_count"],
        "median_scene_words_approx": review["median_scene_words_approx"],
        "lucas_dialogue_scene_share": review["lucas_dialogue_scene_share"],
        "advisories": review["advisories"],
    }


def archive_inbox(root: Path, inbox: Path) -> dict:
    root = root.resolve()
    if inbox.parent.resolve() != (root / "inbox").resolve():
        raise GateError("Only top-level private inbox/<id>.json is accepted")
    episode_id = inbox.stem
    check_id(episode_id)
    if (root / "editorial" / "rejections" / (episode_id + ".json")).is_file():
        raise GateError("Author rejected this unsolicited episode; read-only audit, never archive/promote")
    if not inbox.is_file() or inbox.is_symlink() or inbox.stat().st_size > INBOX_LIMIT:
        raise GateError("Unsafe or oversized inbox file")
    payload = load(inbox)
    if not isinstance(payload, dict):
        raise GateError("Inbox must be a JSON object")
    head = load(root / "canon" / "HEAD.json")
    if head.get("schema") != "worldroot-git-canon-v1":
        raise GateError("GitHub operational HEAD not yet initialized")
    stage_receipt = verify_longform_segments(root, episode_id, payload)
    book_end_approval_verified = False
    if payload.get("book_closed") is True:
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            raise GateError("Book end needs episode metadata")
        require_book_end_approval(root, episode_id, metadata.get("book"))
        book_end_approval_verified = True
    existing_manifest = root / "episodes" / episode_id / "draft" / "manifesto_imutavel.json"
    draft, files, review_files = _assemble(
        episode_id, payload, enforce_presentation=not existing_manifest.is_file(),
        book_end_approval_verified=book_end_approval_verified)
    if existing_manifest.is_file():
        for name, body in files.items():
            existing = root / "episodes" / episode_id / "draft" / name
            if not existing.is_file() or existing.is_symlink() or existing.read_bytes() != body:
                raise ConflictError("Archived immutable draft differs from repeated inbox")
        for name, body in review_files.items():
            existing = root / "episodes" / episode_id / "review" / name
            if not existing.is_file() or existing.is_symlink() or existing.read_bytes() != body:
                raise ConflictError("Archived semantic review differs from repeated inbox")
        verified, manifest = verify_episode(root, episode_id)
        review_deltas(root, episode_id, verified)
        return {
            "status": "RASCUNHO_GITHUB_VERIFICADO", "episode_id": episode_id,
            "source_sha256": manifest["original_readback_sha256"],
            "narrative_bytes": len(files["narrativa_integral.md"]),
            "events": len(payload["reviewed_events"]), "knowledge": len(payload["reviewed_knowledge"]),
            "changed_file_count": 0, "canon_changed": False, "drive_changed": False,
            "editorial_preflight": quick_preflight(payload["prose"])["status"],
            "story_focus_advisory": _focus_receipt(payload["prose"]),
            "day_arc_advisory": inspect_day_arc(payload["prose"]),
            "lived_narrative_advisory": inspect_lived_narrative(payload["prose"]),
            "longform_depth": inspect_longform(payload["prose"]),
            "longform_stage": stage_receipt,
            "presentation_preflight": presentation_preflight(payload["full_text"]),
            "dynamic_scene_advisory": inspect_draft_dynamics(payload["prose"], payload["metadata"]),
        }
    if head.get("book_closed") is True:
        from .book_opening import require_book_open_approval
        require_book_open_approval(root, head, draft.metadata)
    _chronology(head, draft.metadata, prose=draft.prose,
                book_open_approval_verified=head.get("book_closed") is True)

    # Validate a disposable full package, including NPC temporal memory, BEFORE
    # any files are written to archive. This is not a cryptographic human approval.
    with tempfile.TemporaryDirectory() as temp:
        scratch = Path(temp)
        d = scratch / "episodes" / episode_id / "draft"
        r = scratch / "episodes" / episode_id / "review"
        d.mkdir(parents=True)
        r.mkdir(parents=True)
        for name, contents in files.items():
            (d / name).write_bytes(contents)
        for name, contents in review_files.items():
            (r / name).write_bytes(contents)
        clean, _ = verify_episode(scratch, episode_id)
        event_records, knowledge_records = review_deltas(scratch, episode_id, clean)
        if len(event_records) != len(payload["reviewed_events"]):
            raise GateError("Event set changed in archive preflight")

    draft_dir = root / "episodes" / episode_id / "draft"
    review_dir = root / "episodes" / episode_id / "review"
    changed = []
    # Manifest LAST; the Action commits all files as a single Git transaction.
    for name in sorted(n for n in files if n != "manifesto_imutavel.json"):
        if _write_safe(draft_dir / name, files[name]):
            changed.append(str(draft_dir / name))
    for name in sorted(review_files):
        if _write_safe(review_dir / name, review_files[name]):
            changed.append(str(review_dir / name))
    if _write_safe(draft_dir / "manifesto_imutavel.json", files["manifesto_imutavel.json"]):
        changed.append(str(draft_dir / "manifesto_imutavel.json"))
    final, final_manifest = verify_episode(root, episode_id)
    review_deltas(root, episode_id, final)
    return {
        "status": "RASCUNHO_GITHUB_VERIFICADO",
        "episode_id": episode_id, "source_sha256": final_manifest["original_readback_sha256"],
        "narrative_bytes": len(files["narrativa_integral.md"]),
        "events": len(event_records), "knowledge": len(knowledge_records),
        "changed_file_count": len(changed), "canon_changed": False, "drive_changed": False,
        "editorial_preflight": quick_preflight(payload["prose"])["status"],
            "story_focus_advisory": _focus_receipt(payload["prose"]),
            "day_arc_advisory": inspect_day_arc(payload["prose"]),
            "lived_narrative_advisory": inspect_lived_narrative(payload["prose"]),
            "longform_depth": inspect_longform(payload["prose"]),
            "longform_stage": stage_receipt,
            "presentation_preflight": presentation_preflight(payload["full_text"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Archive one immutable ChatGPT story inbox")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--inbox-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = archive_inbox(args.archive_root, args.inbox_file)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (GateError, ConflictError, ValueError, OSError) as exc:
        print("WORLDROOT_DRAFT_INBOX_BLOCKED: " + type(exc).__name__ + ": " + str(exc)[:230], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
