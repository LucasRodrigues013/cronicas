"""WORLDROOT GitHub-only, immutable five-part chapter publisher.

Runs inside the same trusted private archive GitHub Action as the draft inbox.
Never updates canon HEAD, choices, or chapter source. No Drive credentials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from chapter_drive_publisher import build_chapter, chapter_key, ChapterError, encoded
from verify_lvi_original import verify_lvi
from validate_episode_archive import ArchiveInvalid

PARTS = ("I", "II", "III", "IV", "V")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ChapterError("Missing safe source: " + str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def assert_character_reconciliation(root: Path, book: str, chapter: int) -> None:
    """Do not publish a polished chapter bundle with unresolved continuity."""
    for meta_file in (root / "episodes").glob("*/draft/checkpoint_candidato.json"):
        meta = get_json(meta_file)
        if meta.get("book") != book or meta.get("chapter") != chapter:
            continue
        eid = meta_file.parent.parent.name
        if (root / "editorial/rejections" / (eid + ".json")).exists():
            continue
        if book == "Livro VI":
            verify_lvi(root, eid)
        review = meta_file.parent.parent / "review/continuity_review.json"
        if not review.exists():
            if book == "Livro VI":
                raise ChapterError("No character preflight: " + eid)
            continue
        status = get_json(review).get("status")
        if status == "REVIEWED_WITH_FLAGS":
            decision_file = root / "editorial/recovery/reconciliations" / (eid + ".json")
            decision = get_json(decision_file)
            if (decision.get("status") != "APPROVED_BY_AUTHOR"
                    or not decision.get("author_decision")
                    or not decision.get("source_evidence")):
                raise ChapterError("Unresolved character continuity flag: " + eid)
        elif status != "REVIEWED_WITH_EVIDENCE":
            raise ChapterError("Character continuity review not approved: " + eid)


def write_once(path: Path, payload: bytes) -> None:
    """Idempotent create, never overwrite a different previously published byte."""
    if path.is_file():
        if path.read_bytes() != payload:
            raise ChapterError("Immutable GitHub chapter conflict: " + path.name)
        return
    if path.exists():
        raise ChapterError("Unsafe chapter destination: " + path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".partial-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        if path.exists():
            if path.read_bytes() != payload:
                raise ChapterError("Chapter was concurrently modified: " + path.name)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def publish(root: Path, book: str, chapter: int, *, check_only=False) -> dict:
    result = build_chapter(root, book, chapter, publication="GITHUB_PRIVATE_ONLY_NO_CANON_PROMOTION")
    if result is None:
        return {"status": "WAITING_FOR_FIVE_COMPLETE_PARTS", "chapter_key": chapter_key(book, chapter)}
    key, payload = result
    assert_character_reconciliation(root, book, chapter)
    names = {f"{key}-INTEGRAL.md", f"{key}-MANIFESTO.json", f"{key}-ARQUIVO.zip"}
    if set(payload) != names:
        raise ChapterError("Incomplete chapter export")
    metadata = json.loads(payload[key + "-MANIFESTO.json"].decode("utf-8"))
    if (metadata.get("part_count") != 5
            or [p["part"] for p in metadata["parts"]] != list(PARTS)
            or metadata.get("publication") != "GITHUB_PRIVATE_ONLY_NO_CANON_PROMOTION"
            or sha(payload[key + "-INTEGRAL.md"]) != metadata.get("combined_sha256")):
        raise ChapterError("Chapter manifest or chronology invalid")
    artifact_refs = [
        {"path": f"chapters/{key}/{name}", "sha256": sha(data), "bytes": len(data)}
        for name, data in sorted(payload.items())
    ]
    receipt = {
        "schema": "worldroot-github-private-chapter-v1",
        "chapter_key": key,
        "status": "LOCAL_PACKAGE_SHA_VERIFIED_PENDING_GIT_PUSH",
        "source_branch": "story-archive",
        "part_count": 5, "parts": metadata["parts"],
        "artifacts": artifact_refs, "canon_head_modified": False,
        "drive_modified": False,
        "immutability": "APPEND_ONLY_OR_IDENTICAL_BYTES",
    }
    if not check_only:
        for name, data in payload.items():
            write_once(root / "chapters" / key / name, data)
        write_once(root / "delivery" / "github_chapters" / (key + ".json"), encoded(receipt))
        for row in artifact_refs:
            data = (root / row["path"]).read_bytes()
            if sha(data) != row["sha256"] or len(data) != row["bytes"]:
                raise ChapterError("Local chapter readback mismatch")
    return {"status": "FIVE_PARTS_VERIFIED" if check_only else receipt["status"],
            "chapter_key": key, "combined_sha256": metadata["combined_sha256"],
            "part_count": 5, "artifacts": len(artifact_refs)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Package five real story parts into private Git commits")
    parser.add_argument("--archive-root", type=Path, default=Path("."))
    parser.add_argument("--episode-id")
    parser.add_argument("--book")
    parser.add_argument("--chapter", type=int)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = args.archive_root.resolve()
    if args.episode_id:
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", args.episode_id):
            raise ChapterError("Unsafe episode identifier")
        metadata = get_json(root / "episodes" / args.episode_id / "draft/checkpoint_candidato.json")
        if metadata.get("part") != "V":
            print("NOT_PART_V: no full chapter package")
            return 0
        book, chapter = metadata["book"], metadata["chapter"]
    else:
        if args.book is None or args.chapter is None:
            raise ChapterError("Provide either --episode-id or --book and --chapter")
        book, chapter = args.book, args.chapter
    result = publish(root, book, chapter, check_only=args.check_only)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ChapterError, ArchiveInvalid, OSError, KeyError, ValueError) as exc:
        print("WORLDROOT GITHUB-CHAPTER BLOCKED:", str(exc), file=sys.stderr)
        raise SystemExit(1)
