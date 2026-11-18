"""Read-only preflight of an explicit author choice archived on story-archive.

No model output is an authorization by itself; the trusted caller must establish
that the choice came from an actual user message before writing the JSON file.
This gate validates shape, draft provenance and integrity, but does NOT close
an episode, assert user identity, access Drive or update the canonical HEAD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]+\Z")
NAMES = {"schema", "episode_id", "option", "free_text", "author_source"}


class IntakeError(ValueError):
    pass


def _json(path: Path) -> dict | list:
    if not path.is_file() or path.is_symlink():
        raise IntakeError("Required archive file missing or symlinked")
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeError, ValueError):
        raise IntakeError("Invalid UTF-8 JSON in archive") from None


def verify_selection(root: Path, path: Path) -> dict:
    """Check selection provenance against the immutable draft, without promotion."""
    if path.parent.parent != root / "choices":
        raise IntakeError("Choice must be in choices/<episode_id>/")
    episode_id = path.parent.name
    if not ID.fullmatch(episode_id):
        raise IntakeError("Unsafe episode ID")
    match = re.fullmatch(r"option-([1-5])\.json", path.name)
    if not match:
        raise IntakeError("Choice filename must be option-1.json ... option-5.json")

    selection = _json(path)
    if not isinstance(selection, dict) or set(selection) != NAMES:
        raise IntakeError("Unexpected/missing selection keys")
    option = selection["option"]
    if (selection["schema"] != "worldroot-author-choice-v1"
            or selection["episode_id"] != episode_id
            or selection["author_source"] != "USER_MESSAGE"
            or type(option) is not int or option != int(match.group(1))):
        raise IntakeError("Choice schema, source, ID or selected option mismatch")
    extra = selection["free_text"]
    if not isinstance(extra, str) or len(extra) > 2048:
        raise IntakeError("Additional instruction must be bounded UTF-8 text")
    if option == 5 and not extra.strip():
        raise IntakeError("Free action requires the user's instruction")

    draft_dir = root / "episodes" / episode_id / "draft"
    manifest = _json(draft_dir / "manifesto_imutavel.json")
    if not isinstance(manifest, dict):
        raise IntakeError("Manifest must be an object")
    if (manifest.get("schema") != "worldroot-episode-package-v1"
            or manifest.get("delivery_id") != episode_id
            or manifest.get("canon_status") != "RASCUNHO"):
        raise IntakeError("Immutable draft identity/status invalid")
    opts_path = draft_dir / "opcoes.json"
    raw_options = opts_path.read_bytes() if opts_path.is_file() and not opts_path.is_symlink() else b""
    record = (manifest.get("artifacts") or {}).get("opcoes.json")
    if (not isinstance(record, dict)
            or record.get("sha256") != hashlib.sha256(raw_options).hexdigest()
            or type(record.get("bytes")) is not int
            or record["bytes"] != len(raw_options)):
        raise IntakeError("Five choices failed immutable manifest verification")
    options = _json(opts_path)
    if (not isinstance(options, list) or len(options) != 5
            or any(not isinstance(entry, dict)
                   or type(entry.get("number")) is not int
                   or entry["number"] != i for i, entry in enumerate(options, 1))
            or options[3].get("is_special") is not True
            or options[4].get("is_free") is not True):
        raise IntakeError("Five-choice structure invalid")
    return {
        "episode_id": episode_id, "option": option, "intake_status": "CHOICE_SHAPE_VALIDATED",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonical_head_changed": False,
    }


def verify_tree(root: Path) -> list[dict]:
    folder = root / "choices"
    selections = sorted(folder.glob("*/option-*.json")) if folder.is_dir() else []
    if not selections:
        raise IntakeError("No author choice files found; cannot claim preflight success")
    seen: set[str] = set()
    receipts = []
    for path in selections:
        receipt = verify_selection(root, path)
        if receipt["episode_id"] in seen:
            raise IntakeError("Multiple choices found for the same draft episode")
        seen.add(receipt["episode_id"])
        receipts.append(receipt)
    return receipts


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GitHub private draft choice intake")
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_tree(args.archive_root)
    except (IntakeError, OSError) as exc:
        print("WORLDROOT CHOICE INTAKE BLOCKED: " + str(exc))
        return 1
    print(f"WORLDROOT CHOICE INTAKE: {len(result)} user-source envelope(s) match archived options.")
    print("This verifies envelope and archive integrity only; author identity, Drive and canonical HEAD were not certified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
