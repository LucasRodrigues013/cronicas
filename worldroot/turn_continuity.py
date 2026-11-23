"""R27 WORLDROOT: fail-closed proof that the last episode is fully saved.

This code cannot intercept ChatGPT messages. The active assistant must create
the inbox through the GitHub connector; the Actions and gate validate it.
Neither changes HEAD nor makes new story facts canonical.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from .git_cycle import check_id
from .delivery_gate import audit_release

PARTS = ("I", "II", "III", "IV", "V")


def read_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe evidence: " + str(path))
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected JSON object: " + str(path))
    return obj


def audit_turn_handoff(root: Path, previous_episode_id: str, *,
                       expected_head_id: str | None = None,
                       require_canon_promotion: bool = False) -> dict:
    """Require previous full text + SHA + reader receipt + live HEAD.

    Draft immediately after HEAD is legal; canonical closure needs a REAL user
    choice and a matching journal. The caller must explicitly run this gate.
    """
    root = root.resolve()
    checks = {}
    errors = []
    story_sha = None
    head_id = None
    try:
        check_id(previous_episode_id)
        prev = previous_episode_id
        head = read_json(root / "canon/HEAD.json")
        head_id = head.get("episode_id")
        checks["head"] = (head.get("schema") == "worldroot-git-canon-v1"
                          and isinstance(head_id, str))
        checks["head_expected"] = (expected_head_id is None
                                   or head_id == expected_head_id)
        if not all((checks["head"], checks["head_expected"])):
            raise ValueError("HEAD invalid or moved; must reread before continuing")

        meta = read_json(root / "episodes" / prev / "draft/checkpoint_candidato.json")
        inbox = read_json(root / "inbox" / (prev + ".json"))
        manifest = read_json(root / "episodes" / prev / "draft/manifesto_imutavel.json")
        receipt = read_json(root / "delivery/reader_receipts" / (prev + ".json"))
        file = root / "episodes" / prev / "draft/narrativa_integral.md"
        if not file.is_file() or file.is_symlink():
            raise ValueError("Full narrative missing; synopsis is not an episode")
        body = file.read_bytes()
        story_sha = hashlib.sha256(body).hexdigest()
        full = inbox.get("full_text")
        prose = inbox.get("prose")
        checks["whole_source"] = (
            inbox.get("delivery_id") == prev
            and manifest.get("delivery_id") == prev
            and meta.get("canon_status") == "RASCUNHO"
            and isinstance(full, str) and isinstance(prose, str)
            and bool(prose.strip()) and full.startswith(prose)
            and full == body.decode("utf-8", errors="strict")
        )
        entry = manifest.get("artifacts", {}).get("narrativa_integral.md", {})
        checks["sha_bytes"] = (
            manifest.get("original_readback_sha256") == story_sha
            and entry.get("sha256") == story_sha and entry.get("bytes") == len(body)
        )
        checks["receipt"] = (
            receipt.get("schema") == "worldroot-reader-release-receipt-v1"
            and receipt.get("episode_id") == prev
            and receipt.get("status") == "ARCHIVED_DRAFT_VERIFIED_FOR_READER"
            and receipt.get("story_sha256") == story_sha
            and receipt.get("source_path")
            == "episodes/" + prev + "/draft/narrativa_integral.md"
        )
        if not all(checks.values()):
            raise ValueError("Complete text, manifest or publication receipt invalid")

        checks["adjacent"] = prev == head_id
        if not checks["adjacent"] and (
            head.get("book") == meta.get("book") == "Livro VI"
            and type(head.get("chapter")) is int
            and type(meta.get("chapter")) is int
            and head.get("part") in PARTS
            and meta.get("part") in PARTS
        ):
            oldpart = head["part"]
            checks["adjacent"] = (
                meta["chapter"] == head["chapter"] + (oldpart == "V")
                and meta["part"] == (
                    "I" if oldpart == "V"
                    else PARTS[PARTS.index(oldpart) + 1]
                ) and type(meta.get("day")) is int and type(head.get("day")) is int
                and meta["day"] >= head["day"]
            )
        if not checks["adjacent"]:
            raise ValueError("Previous episode not HEAD or immediately adjacent draft")

        resume_path = root / "ops/RESUME.json"
        if resume_path.is_file():
            resume = read_json(resume_path)
            checks["resume_head"] = (
                resume.get("canon_head", {}).get("episode_id") == head_id
            )
            latest = resume.get("latest_unclosed_draft")
            checks["latest_part_acknowledged"] = (
                not isinstance(latest, dict) or latest.get("episode_id") == prev
            )
            if not checks["resume_head"] or not checks["latest_part_acknowledged"]:
                raise ValueError("Stale RESUME or newer saved part not acknowledged")

        gate = audit_release(root, prev)
        checks["r14_r26_gate"] = (
            gate.get("release_allowed") is True
            and gate.get("story_sha256") == story_sha
        )
        if not checks["r14_r26_gate"]:
            raise ValueError("Full narrative release gate failed: " +
                             str(gate.get("errors", []))[:180])

        if require_canon_promotion:
            journal = read_json(root / "canon/episodes" / (prev + ".json"))
            selected = sorted((root / "choices" / prev).glob("option-*.json"))
            checks["real_choice_closed"] = (
                prev == head_id and journal.get("episode_id") == prev
                and journal.get("story_sha256") == story_sha
                and len(selected) == 1
            )
            if checks["real_choice_closed"]:
                choice = read_json(selected[0])
                checks["real_choice_closed"] = (
                    choice.get("episode_id") == prev
                    and choice.get("author_source") == "USER_MESSAGE"
                    and type(choice.get("option")) is int
                    and 1 <= choice["option"] <= 5
                )
            if not checks["real_choice_closed"]:
                raise ValueError("Real author choice did not advance canon HEAD")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, IndexError) as e:
        errors.append(type(e).__name__ + ": " + str(e)[:280])
    ready = not errors and all(checks.values())
    return {
        "schema": "worldroot-turn-handoff-v1",
        "previous_episode_id": previous_episode_id,
        "canon_head": head_id,
        "ready": ready,
        "status": "PREVIOUS_FULL_EPISODE_VERIFIED" if ready
                  else "BLOCK_NEXT_PART_AND_NO_SAVED_CLAIM",
        "story_sha256": story_sha,
        "checks": checks,
        "errors": errors,
        "automatic_chat_capture": False,
        "canon_changed": False, "drive_changed": False
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WORLDROOT R27 full-episode continuation gate")
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--previous-episode-id", required=True)
    p.add_argument("--expected-head-id")
    p.add_argument("--require-canon-promotion", action="store_true")
    a = p.parse_args(argv)
    result = audit_turn_handoff(
        a.archive_root, a.previous_episode_id,
        expected_head_id=a.expected_head_id,
        require_canon_promotion=a.require_canon_promotion)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
