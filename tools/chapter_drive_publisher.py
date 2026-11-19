"""WORLDROOT: five-part chapter integrity gate and readback-verified Drive backup.

Archive sources are immutable; this module never edits episodes, choices, HEAD,
canonical journal, or character state. No private prose is printed to CI logs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from validate_episode_archive import verify_one, ArchiveInvalid

PARTS = ("I", "II", "III", "IV", "V")
FILES = (
    "narrativa_integral.md", "opcoes.json", "eventos_e_consequencias.json",
    "checkpoint_candidato.json", "episode_draft.json", "manifesto_imutavel.json",
)


class ChapterError(ValueError):
    pass


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def load(path):
    if not path.is_file() or path.is_symlink():
        raise ChapterError("Missing or unsafe archive file: " + str(path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ChapterError("Invalid JSON: " + path.name) from exc


def valid_book(book):
    if not isinstance(book, str) or not re.fullmatch(r"Livro [IVXLCDM]+", book):
        raise ChapterError("Book identifier must be Livro followed by Roman numerals")
    return book


def chapter_key(book, chapter):
    valid_book(book)
    if type(chapter) is not int or not 1 <= chapter <= 999:
        raise ChapterError("Invalid chapter number")
    return book.replace(" ", "-").upper() + "-C" + str(chapter).zfill(2)


def build_chapter(root: Path, book: str, chapter: int):
    """Return (key, blobs) only when five verified parts really exist."""
    key = chapter_key(book, chapter)
    matches = {}
    for candidate in sorted((root / "episodes").glob("*/draft/checkpoint_candidato.json")):
        meta = load(candidate)
        if meta.get("book") != book or meta.get("chapter") != chapter:
            continue
        part = meta.get("part")
        if part not in PARTS or part in matches:
            raise ChapterError("Duplicate or invalid part in " + key)
        folder = candidate.parent
        episode = folder.parent.name
        rejected = root / "editorial" / "rejections" / (episode + ".json")
        if rejected.exists():
            raise ChapterError("A rejected episode cannot be exported: " + episode)
        verify_one(folder / "manifesto_imutavel.json")
        matches[part] = (episode, folder, meta)
    if len(matches) < 5:
        return None
    if set(matches) != set(PARTS):
        raise ChapterError("Chapter parts do not match I-V")

    archive = {}
    parts_info = []
    full = []
    for part in PARTS:
        episode, folder, meta = matches[part]
        prefix = "parts/" + part + "/" + episode + "/"
        for filename in FILES:
            data = (folder / filename).read_bytes()
            archive[prefix + filename] = data
        literal = archive[prefix + "narrativa_integral.md"]
        part_sha = digest(literal)
        journal_path = root / "canon" / "episodes" / (episode + ".json")
        canonical = journal_path.is_file()
        if part != "V" and not canonical:
            raise ChapterError("Parts I-IV must be canonically closed before chapter backup")
        if canonical:
            journal = load(journal_path)
            if (journal.get("status") != "FECHADO_GITHUB"
                    or journal.get("episode_id") != episode
                    or journal.get("story_sha256") != part_sha):
                raise ChapterError("Canonical journal disagrees with literal source: " + episode)
            journal_meta = journal.get("metadata") or {}
            if any(journal_meta.get(k) != meta.get(k) for k in ("book", "chapter", "part")):
                raise ChapterError("Canonical journal metadata mismatch: " + episode)
            archive["canon/" + episode + ".json"] = journal_path.read_bytes()
        review_dir = folder.parent / "review"
        if review_dir.is_dir():
            for review in sorted(review_dir.iterdir()):
                if review.is_file() and not review.is_symlink():
                    archive[prefix + "review/" + review.name] = review.read_bytes()
        choice_dir = root / "choices" / episode
        if choice_dir.is_dir():
            for choice in sorted(choice_dir.glob("option-*.json")):
                if not choice.is_symlink():
                    archive[prefix + "author_choices/" + choice.name] = choice.read_bytes()
        full.append(("\n\n<!-- WORLDROOT " + key + " PARTE " + part + " / " + episode + " -->\n\n").encode("utf-8") + literal)
        parts_info.append({
            "part": part, "episode_id": episode, "day": meta.get("day"),
            "hour": meta.get("hour"), "location": meta.get("location"),
            "literal_sha256": part_sha, "literal_bytes": len(literal),
            "canonical_closed": canonical,
        })
    combined = b"".join(full)
    file_hashes = {name: {"sha256": digest(data), "bytes": len(data)}
                   for name, data in sorted(archive.items())}
    manifest = {
        "schema": "worldroot-five-part-chapter-backup-v1",
        "chapter_key": key, "book": book, "chapter": chapter,
        "part_count": 5, "parts": parts_info,
        "archive_entries": file_hashes,
        "combined_sha256": digest(combined), "combined_bytes": len(combined),
        "publication": "DRIVE_BACKUP_ONLY_NO_CANON_PROMOTION",
    }
    archive["chapter_manifest.json"] = encoded(manifest)
    archive["capitulo_integral.md"] = combined
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for name, data in sorted(archive.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            zipped.writestr(info, data)
    return key, {
        key + "-INTEGRAL.md": combined,
        key + "-MANIFESTO.json": encoded(manifest),
        key + "-ARQUIVO.zip": out.getvalue(),
    }


def drive_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    names = ("WORLDROOT_GOOGLE_CLIENT_ID", "WORLDROOT_GOOGLE_CLIENT_SECRET",
             "WORLDROOT_GOOGLE_REFRESH_TOKEN")
    if any(not os.environ.get(name) for name in names):
        raise ChapterError("Drive OAuth is not configured; no files were sent")
    creds = Credentials(
        token=None,
        refresh_token=os.environ[names[2]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[names[0]],
        client_secret=os.environ[names[1]],
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def publish(root, key, files, service):
    """Create-or-verify by chapter and filename. Never overwrite mismatched files."""
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

    folder = os.environ.get("WORLDROOT_DRIVE_CHAPTER_FOLDER_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,}", folder):
        raise ChapterError("Valid WORLDROOT_DRIVE_CHAPTER_FOLDER_ID required")
    # Query only exact app-tagged files in the configured destination.
    q = ("'" + folder + "' in parents and trashed = false and "
         "appProperties has {key='worldroot_chapter' and value='" + key + "'}")
    listing = service.files().list(
        q=q, fields="nextPageToken,files(id,name,size,md5Checksum,parents,appProperties,version)",
        pageSize=100, supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    if listing.get("nextPageToken"):
        raise ChapterError("Unexpected Drive pagination; do not risk duplicates")
    existing = listing.get("files", [])
    if len({entry["name"] for entry in existing}) != len(existing):
        raise ChapterError("Duplicate Drive filenames for chapter")
    by_name = {entry["name"]: entry for entry in existing}
    if any(name not in files for name in by_name):
        raise ChapterError("Unexpected chapter-tagged Drive artifact; manual audit")
    saved = []
    for name, raw in sorted(files.items()):
        expected = digest(raw)
        previous = by_name.get(name)
        if previous:
            file_id = previous["id"]
        else:
            mimetype = ("application/zip" if name.endswith(".zip") else
                        "application/json" if name.endswith(".json") else
                        "text/markdown")
            media = MediaIoBaseUpload(io.BytesIO(raw), mimetype=mimetype, resumable=False)
            created = service.files().create(
                body={"name": name, "parents": [folder],
                      "appProperties": {"worldroot_chapter": key,
                                        "worldroot_sha256": expected}},
                media_body=media, fields="id", supportsAllDrives=True,
            ).execute()
            file_id = created["id"]
        meta = service.files().get(
            fileId=file_id, supportsAllDrives=True,
            fields="id,name,size,md5Checksum,parents,appProperties,version",
        ).execute()
        if (meta.get("name") != name or folder not in meta.get("parents", [])
                or int(meta.get("size", -1)) != len(raw)
                or meta.get("appProperties", {}).get("worldroot_chapter") != key
                or meta.get("appProperties", {}).get("worldroot_sha256") != expected
                or meta.get("md5Checksum") != hashlib.md5(raw).hexdigest()
                or not meta.get("version")):
            raise ChapterError("Drive metadata/hash mismatch for " + name)
        media = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, media)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        if buffer.getvalue() != raw:
            raise ChapterError("Drive independent readback mismatch for " + name)
        saved.append({"name": name, "file_id": file_id,
                      "sha256": expected, "bytes": len(raw)})
    receipt = {
        "schema": "worldroot-drive-chapter-receipt-v1",
        "chapter_key": key, "status": "DRIVE_READBACK_VERIFIED",
        "files": saved, "verified_at": datetime.now(timezone.utc).isoformat(),
        "canon_head_modified": False, "source_episodes_modified": False,
    }
    destination = root / "delivery" / "drive_chapters" / (key + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        old = load(destination)
        if old.get("status") != "DRIVE_READBACK_VERIFIED" or old.get("files") != saved:
            raise ChapterError("GitHub receipt conflict; remote files were not overwritten")
        return destination
    destination.write_bytes(encoded(receipt))
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, default=Path("."))
    parser.add_argument("--changed-paths-file", type=Path)
    parser.add_argument("--book")
    parser.add_argument("--chapter", type=int)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    root = args.archive_root.resolve()
    targets = set()
    if args.book is not None or args.chapter is not None:
        if args.book is None or args.chapter is None:
            raise ChapterError("Specify both book and chapter")
        targets.add((args.book, args.chapter))
    if args.changed_paths_file:
        for raw_path in args.changed_paths_file.read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"episodes/([A-Za-z0-9_-]+)/draft/manifesto_imutavel\.json", raw_path)
            if not match:
                continue
            meta_path = root / "episodes" / match.group(1) / "draft" / "checkpoint_candidato.json"
            if not meta_path.is_file():
                continue
            meta = load(meta_path)
            if meta.get("part") == "V":
                targets.add((meta.get("book"), meta.get("chapter")))
    if not targets:
        print("NO_NEW_PART_V: no chapter backup attempted")
        return 0
    for book, chapter in sorted(targets):
        bundle = build_chapter(root, book, chapter)
        if bundle is None:
            print("WAITING_FOR_FIVE_PARTS:", chapter_key(book, chapter))
            continue
        key, blobs = bundle
        if args.check_only:
            print("CHAPTER_VERIFIED:", key, "files:", len(blobs),
                  "combined_sha256:", digest(blobs[key + "-INTEGRAL.md"]))
            continue
        service = drive_service()
        receipt = publish(root, key, blobs, service)
        print("DRIVE_READBACK_VERIFIED:", key, "receipt:", receipt.relative_to(root))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ChapterError, ArchiveInvalid, OSError, ValueError) as exc:
        print("WORLDROOT CHAPTER BACKUP BLOCKED:", str(exc), file=sys.stderr)
        sys.exit(1)
