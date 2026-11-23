"""WORLDROOT r14.1 — fail-closed pre-delivery gate for *already archived* story parts.

This does not create prose, certify literary quality, change canon, or intercept
ChatGPT messages. It makes the required pre-delivery GitHub evidence testable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .git_cycle import check_id, load, sha, verify_episode, review_deltas
from .longform_depth import inspect_longform
from .presentation_guard import presentation_preflight
from .editorial_guard import quick_preflight
from .lived_narrative_audit import inspect_lived_narrative
from .reader_experience import validate_reader_review
from .narrative_director import validate_direction
from .ledger import GateError, ConflictError
from .book_closure import require_book_end_approval


def audit_release(root: Path, episode_id: str) -> dict:
    """Allow a reader-facing final chapter only after readback and mandatory QA."""
    check_id(episode_id)
    root = root.resolve()
    errors = []
    checks = {}
    pkg = root / "episodes" / episode_id
    story_path = pkg / "draft" / "narrativa_integral.md"
    inbox_path = root / "inbox" / (episode_id + ".json")
    head_path = root / "canon" / "HEAD.json"
    source_sha = None
    prose_words = 0
    lived_advisory = None

    try:
        if (root / "editorial" / "rejections" / (episode_id + ".json")).is_file():
            raise GateError("Author rejected the episode; not approved for reader or canon")
        if not head_path.is_file():
            raise GateError("No operational canonical HEAD")
        head = load(head_path)
        checks["operational_head"] = head.get("schema") == "worldroot-git-canon-v1"
        if not checks["operational_head"]:
            raise GateError("Wrong canonical HEAD format")
        if not inbox_path.is_file():
            raise GateError("No explicit inbox submission for chapter")
        inbox = load(inbox_path)
        checks["inbox_status"] = (
            inbox.get("schema") in ("worldroot-draft-inbox-v1", "worldroot-draft-inbox-v2")
            and inbox.get("delivery_id") == episode_id
            and inbox.get("metadata", {}).get("canon_status") == "RASCUNHO"
        )
        if not checks["inbox_status"]:
            raise GateError("Wrong draft inbox or attempt to declare a closed episode")
        if not story_path.is_file():
            raise GateError("No archived literal story readback")
        draft, manifest = verify_episode(root, episode_id)
        checks["immutable_manifest"] = True
        source = story_path.read_text(encoding="utf-8")
        checks["literal_source_equals_inbox"] = (
            source == inbox["full_text"]
            and inbox["full_text"].startswith(inbox["prose"])
            and sha(source.encode("utf-8")) == manifest["original_readback_sha256"]
        )
        if not checks["literal_source_equals_inbox"]:
            raise GateError("Readback, draft prose, or immutable source SHA mismatch")
        checks["five_choices"] = len(inbox.get("choices", [])) == 5
        if not checks["five_choices"]:
            raise GateError("Five choices missing")
        if inbox.get("book_closed") is True:
            require_book_end_approval(root, episode_id, inbox["metadata"]["book"])
            checks["book_status_authorized"] = (draft.book_closed is True
                and "FIM DO LIVRO V" in inbox["prose"].upper())
        else:
            checks["book_status_authorized"] = (
                inbox.get("book_closed") is False and draft.book_closed is False)
        if not checks["book_status_authorized"]:
            raise GateError("Book closure or book-open state does not match approved story")
        depth = inspect_longform(inbox["prose"])
        prose_words = depth["prose_words_approx"]
        # Volume is guidance only; passing 10000 words is NOT a prose verdict.
        checks["longform_measured"] = isinstance(prose_words, int)
        if not checks["longform_measured"]:
            raise GateError("Narrative word count missing")
        lived_advisory = inspect_lived_narrative(inbox["prose"])
        visual = presentation_preflight(
            source, strict_dialogue=inbox["schema"] == "worldroot-draft-inbox-v2")
        checks["ux_rich_contract"] = not visual["errors"]
        if not checks["ux_rich_contract"]:
            raise GateError("; ".join(visual["errors"]))
        literary = quick_preflight(inbox["prose"], scene_tags=inbox.get("editorial_tags", ()))
        checks["editorial_structural"] = not literary["errors"]
        if not checks["editorial_structural"]:
            raise GateError("; ".join(literary["errors"]))
        if inbox["schema"] == "worldroot-draft-inbox-v2":
            direction = inbox.get("narrative_direction") or {}
            compass = validate_direction({"episode_id": direction.get("source_episode_id")},
                                         direction)
            experience = validate_reader_review(inbox["prose"], inbox.get("reader_review"))
            sidecar = pkg / "review" / "experiencia_r25.json"
            checks["r25_reader_evidence"] = (
                not compass["errors"] and not experience["errors"]
                and sidecar.is_file() and load(sidecar).get("assessment") == experience
                and load(sidecar).get("director") == compass
            )
            if not checks["r25_reader_evidence"]:
                raise GateError("R25: reader evidence or director differs from archive")
        event_records, knowledge_records = review_deltas(root, episode_id, draft)
        checks["semantic_sidecars"] = bool(event_records) and isinstance(knowledge_records, list)
        if not checks["semantic_sidecars"]:
            raise GateError("Reviewed source-evidenced events are absent")
        source_sha = manifest["original_readback_sha256"]
        checks["github_archive_readback"] = True
    except (GateError, ConflictError, KeyError, TypeError, ValueError, OSError, UnicodeError) as exc:
        errors.append(type(exc).__name__ + ": " + str(exc)[:300])

    allowed = not errors and all(checks.values())
    return {
        "schema": "worldroot-reader-delivery-gate-v1",
        "episode_id": episode_id,
        "status": "ARCHIVED_DRAFT_VERIFIED_FOR_READER" if allowed else "DO_NOT_PRESENT_AS_COMPLETE",
        "release_allowed": allowed,
        "checks": checks,
        "errors": errors,
        "prose_words_approx": prose_words,
        "longform_target_status": (depth.get("status") if "depth" in locals() else None),
        "lived_narrative_advisory": lived_advisory,
        "r25_contract": ("ENFORCED" if "inbox" in locals() and isinstance(inbox, dict)
                         and inbox.get("schema") == "worldroot-draft-inbox-v2"
                         else "LEGACY_READBACK_NO_RETROACTIVE_REJECTION"),
        "story_sha256": source_sha,
        "canon_changed": False,
        "drive_changed": False,
        "semantic_certification": False,
        "note": "Does not guarantee that the ChatGPT user-visible message matches GitHub, nor certify literary quality; verify the exact text before delivery.",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Verify archived WORLDROOT draft before publishing chapter in chat")
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--episode-id", required=True)
    args = p.parse_args(argv)
    result = audit_release(args.archive_root, args.episode_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["release_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
