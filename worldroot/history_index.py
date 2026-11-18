"""Private, source-verified historical SQLite FTS5 index for original Drive TXT exports.

Read-only relative to the story's canon. This builds a *search projection* from
immutable GitHub mirrors of Drive bytes, with exact file/line provenance. It
does not deduce narrative truth, merge ambiguous day labels or promote facts.
No Google auth/OIDC or HTTP connections are required inside GitHub Actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path, PurePosixPath

from .ledger import GateError

MANIFEST = "history/sources/MANIFEST.json"
INDEX = "history/LITERAL_INDEX.sqlite"
SUMMARY = "history/INDEX_SUMMARY.json"
PROJECT = "CRONICAS_DE_UM_NOVO_MUNDO"
MANIFEST_SCHEMA = "worldroot-literal-source-manifest-v1"
INDEX_VERSION = "worldroot-literal-fts-v1"
SOURCE_SHA = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
DRIVE_ID = re.compile(r"^[A-Za-z0-9_-]{15,100}$")
ROLE_MARKER = re.compile(r"^## (Prompt|Response):\s*$")
DAY_TAG = re.compile(r"\b(?:DIA\s*0*|D\s*0*)(\d{1,3})\b", re.IGNORECASE)
WORD = re.compile(r"[^\W_]+", re.UNICODE)
MAX_CHARS = 3200
MAX_QUERY = 160
MAX_RESULT = 12


def _canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n").encode("utf-8")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_json(path: Path):
    if not path.is_file() or path.is_symlink():
        raise GateError("Missing or unsafe historical file: " + path.name)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise GateError("Invalid historical JSON: " + path.name) from None


def _safe_file(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel.startswith("history/sources/"):
        raise GateError("Historical blobs must stay in the dedicated private directory")
    path = PurePosixPath(rel)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 3:
        raise GateError("Unsafe source path")
    target = root.joinpath(*path.parts)
    if target.is_symlink() or not target.is_file():
        raise GateError("Missing historical Git blob: " + path.name)
    return target


def read_verified_sources(root: Path):
    """Check all six raw files, every part Git SHA-1, length and full SHA-256."""
    doc = _load_json(root / MANIFEST)
    if doc.get("schema") != MANIFEST_SCHEMA or doc.get("project") != PROJECT:
        raise GateError("Wrong historical project/schema")
    sources = doc.get("sources")
    if not isinstance(sources, list) or len(sources) != 6 or doc.get("source_count") != 6:
        raise GateError("Expected the six inventoried Drive transcript exports")
    result, seen_names, seen_ids = [], set(), set()
    total = 0
    for index, src in enumerate(sources, 1):
        if not isinstance(src, dict):
            raise GateError("Malformed Drive source entry")
        name = src.get("source_name")
        drive_id = src.get("drive_id")
        length = src.get("utf8_bytes")
        claimed_hash = src.get("sha256")
        parts = src.get("parts")
        if (not isinstance(name, str)
                or not name.startswith(f"{index:02d}_DIA_")
                or not name.endswith("_FONTE_LITERAL.txt")
                or name in seen_names
                or not isinstance(drive_id, str) or not DRIVE_ID.fullmatch(drive_id)
                or drive_id in seen_ids or not SOURCE_SHA.fullmatch(str(claimed_hash))
                or type(length) is not int or not 0 < length <= 30_000_000
                or src.get("mime_type") != "text/plain"
                or src.get("source_kind") != "CHAT_EXPORT_LITERAL"
                or src.get("semantic_status") != "UNREVIEWED_LITERAL"
                or not isinstance(parts, list) or not 1 <= len(parts) <= 12
                or not isinstance(src.get("nominal_day_start"), int)
                or not isinstance(src.get("nominal_day_end"), int)
                or src["nominal_day_start"] > src["nominal_day_end"]):
            raise GateError("Unverified Drive source identity, filename, size or status")
        seen_names.add(name)
        seen_ids.add(drive_id)
        blobs = []
        for part_index, part in enumerate(parts, 1):
            if not isinstance(part, dict):
                raise GateError("Malformed Git source part")
            expected_path = "history/sources/" + name
            if len(parts) > 1:
                expected_path += f".part-{part_index:03d}"
            if part.get("path") != expected_path or not GIT_SHA.fullmatch(str(part.get("git_blob_sha1"))):
                raise GateError("Git source part must use the exact expected path and SHA")
            content = _safe_file(root, part["path"]).read_bytes()
            if type(part.get("bytes")) is not int or len(content) != part["bytes"]:
                raise GateError("Git source part length mismatch")
            git_sha = hashlib.sha1(
                b"blob " + str(len(content)).encode("ascii") + bytes([0]) + content
            ).hexdigest()
            if git_sha != part["git_blob_sha1"]:
                raise GateError("Git source part failed immutable SHA-1")
            blobs.append(content)
        original = b"".join(blobs)
        if len(original) != length or _sha(original) != claimed_hash:
            raise GateError("Original Drive text failed its full SHA-256/length")
        try:
            literal = original.decode("utf-8")
        except UnicodeDecodeError:
            raise GateError("Original Drive TXT is not UTF-8") from None
        total += length
        result.append((src, literal))
    if total != doc.get("total_source_bytes"):
        raise GateError("Total historical source byte count does not match")
    return doc, result


def _chunks(text: str):
    role = "EXPORT_METADATA"
    lines = text.splitlines(keepends=True)
    buf, start, length = [], 1, 0

    def emit(current):
        if not buf:
            return None
        body = "".join(buf)
        tags = sorted({
            int(m.group(1)) for m in DAY_TAG.finditer(body)
            if 1 <= int(m.group(1)) <= 999
        })
        return (start, start + len(buf) - 1, current, body,
                json.dumps(tags, separators=(",", ":")))

    for line_number, line in enumerate(lines, 1):
        marker = ROLE_MARKER.fullmatch(line.strip())
        if marker and buf:
            yield emit(role)
            buf, length = [], 0
        if marker:
            role = "AUTHOR_PROMPT" if marker.group(1) == "Prompt" else "ASSISTANT_RESPONSE"
        if buf and length + len(line) > MAX_CHARS:
            yield emit(role)
            buf, length = [], 0
        if not buf:
            start = line_number
        buf.append(line)
        length += len(line)
    if buf:
        yield emit(role)


def _new_db(conn: sqlite3.Connection):
    conn.executescript("""
        PRAGMA journal_mode=DELETE;
        PRAGMA foreign_keys=ON;
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE source_files (
            source_id INTEGER PRIMARY KEY,
            file_name TEXT UNIQUE NOT NULL,
            drive_id TEXT UNIQUE NOT NULL,
            drive_url TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            utf8_bytes INTEGER NOT NULL,
            line_count INTEGER NOT NULL,
            nominal_day_start INTEGER NOT NULL,
            nominal_day_end INTEGER NOT NULL,
            editorial_status TEXT NOT NULL
                CHECK(editorial_status='UNREVIEWED_LITERAL')
        );
        CREATE TABLE chunks (
            chunk_id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES source_files(source_id),
            line_start INTEGER NOT NULL,
            line_end INTEGER NOT NULL,
            section_role TEXT NOT NULL,
            day_mentions_json TEXT NOT NULL,
            body TEXT NOT NULL,
            UNIQUE(source_id,line_start,line_end)
        );
        CREATE INDEX idx_chunk_source_lines ON chunks(source_id,line_start,line_end);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            body, content='chunks', content_rowid='chunk_id',
            tokenize='unicode61 remove_diacritics 2'
        );
    """)


def _connect_db(path: Path, *, readonly=True):
    if not path.is_file() or path.is_symlink():
        raise GateError("Historical SQLite search projection does not exist")
    if readonly:
        return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    return sqlite3.connect(path)


def verify(root: Path, *, with_source_checks=False):
    if with_source_checks:
        manifest, _ = read_verified_sources(root)
    else:
        manifest = _load_json(root / MANIFEST)
    manifest_digest = _sha(_canonical(manifest))
    with _connect_db(root / INDEX) as conn:
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise GateError("Historical index SQLite quick_check failed")
        meta = dict(conn.execute("SELECT key,value FROM metadata").fetchall())
        if meta.get("schema") != INDEX_VERSION or meta.get("manifest_sha256") != manifest_digest:
            raise GateError("Historical index does not match source manifest")
        rows = conn.execute("SELECT COUNT(*) FROM source_files").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        if rows != 6 or chunks < 100:
            raise GateError("Historical index incomplete; not safe to search")
        if int(meta.get("chunk_count", -1)) != chunks:
            raise GateError("Historical chunk count differs from indexed source count")
        probe = conn.execute("SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT 1",
                             ("Lucas",)).fetchone()
        if probe is None:
            raise GateError("Historical full-text index lacks expected source content")
        return {
            "schema": INDEX_VERSION,
            "manifest_sha256": manifest_digest,
            "source_count": rows,
            "chunk_count": chunks,
            "literal_bytes": int(meta["literal_bytes"]),
            "canon_changed": False,
            "projection_only": True,
        }


def build(root: Path):
    root = root.resolve()
    manifest, verified = read_verified_sources(root)
    digest = _sha(_canonical(manifest))
    destination = root / INDEX
    if destination.is_file() and not destination.is_symlink():
        try:
            old = verify(root)
            if old["manifest_sha256"] == digest:
                return {"result": "IDEMPOTENT_ALREADY_INDEXED", **old}
        except (sqlite3.DatabaseError, GateError, ValueError):
            pass

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".literal-fts-", suffix=".sqlite", dir=destination.parent)
    os.close(fd)
    temp = Path(temp_path)
    try:
        with sqlite3.connect(temp) as conn:
            _new_db(conn)
            conn.execute("INSERT INTO metadata VALUES (?,?)", ("schema", INDEX_VERSION))
            conn.execute("INSERT INTO metadata VALUES (?,?)", ("manifest_sha256", digest))
            conn.execute("INSERT INTO metadata VALUES (?,?)",
                         ("literal_bytes", str(manifest["total_source_bytes"])))
            total_chunks = 0
            source_summary = []
            for source_id, (src, text) in enumerate(verified, 1):
                line_count = len(text.splitlines())
                conn.execute(
                    "INSERT INTO source_files VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (source_id, src["source_name"], src["drive_id"],
                     src["drive_url"], src["sha256"], src["utf8_bytes"],
                     line_count, src["nominal_day_start"], src["nominal_day_end"],
                     src["semantic_status"])
                )
                count = 0
                for start, end, role, body, mentions in _chunks(text):
                    conn.execute(
                        "INSERT INTO chunks (source_id,line_start,line_end,section_role,"
                        "day_mentions_json,body) VALUES (?,?,?,?,?,?)",
                        (source_id, start, end, role, mentions, body)
                    )
                    count += 1
                total_chunks += count
                source_summary.append({
                    "name": src["source_name"],
                    "drive_url": src["drive_url"],
                    "sha256": src["sha256"], "utf8_bytes": src["utf8_bytes"],
                    "source_lines": line_count, "indexed_chunks": count,
                    "day_start_label": src["nominal_day_start"],
                    "day_end_label": src["nominal_day_end"],
                    "status": "LITERAL_INDEXED_NOT_CANON_CERTIFIED",
                })
            conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')")
            conn.execute("INSERT INTO metadata VALUES (?,?)", ("chunk_count", str(total_chunks)))
            conn.commit()
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise GateError("New FTS index quick_check failed")
        os.replace(temp, destination)
        result = verify(root)
        summary = {
            **result,
            "sources": source_summary,
            "coverage_warning": (
                "Original filenames indicate intervals D001-D528, not proof "
                "of individually narrated scenes on every day. Boundary-day "
                "overlaps are retained; raw sources may contain assistant plans/errors."
            ),
            "priority": "GITHUB_CANON_HEAD_AND_APPROVED_LITERAL_OVERRIDES_SEARCH_HITS",
            "separation": "Never attach these chunks to canon/state.sqlite as approved facts",
        }
        (root / SUMMARY).write_bytes(_canonical(summary))
        return {"result": "REBUILT_VERIFIED_PRIVATE_FTS", **result}
    finally:
        if temp.exists():
            temp.unlink()


def search(root: Path, phrase: str, *, limit=6, role=None, day_hint=None, match_mode="all"):
    if not isinstance(phrase, str) or not 1 <= len(phrase.strip()) <= MAX_QUERY:
        raise GateError("Search query must be bounded, explicit text")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULT:
        raise GateError("Result limit out of bounds")
    if role not in (None, "AUTHOR_PROMPT", "ASSISTANT_RESPONSE", "EXPORT_METADATA"):
        raise GateError("Role filter invalid")
    if day_hint is not None and (type(day_hint) is not int or not 1 <= day_hint <= 528):
        raise GateError("Nominal day hint must be in D001-D528")
    if match_mode not in ("all", "any"):
        raise GateError("Unknown FTS match mode")
    words = WORD.findall(phrase)
    if not 1 <= len(words) <= 12 or any(len(word) > 45 for word in words):
        raise GateError("Search query tokens missing or oversized")
    expr = (" AND " if match_mode == "all" else " OR ").join('"' + x + '"' for x in words)
    state = verify(root)
    query = (
        "SELECT s.file_name,s.drive_url,s.sha256,s.nominal_day_start,"
        "s.nominal_day_end,c.line_start,c.line_end,c.section_role,c.day_mentions_json,"
        "snippet(chunks_fts,0,'[',']','...',30) AS snippet,"
        "bm25(chunks_fts) AS score "
        "FROM chunks_fts JOIN chunks c ON c.chunk_id=chunks_fts.rowid "
        "JOIN source_files s ON s.source_id=c.source_id "
        "WHERE chunks_fts MATCH ? "
    )
    params = [expr]
    if role:
        query += "AND c.section_role=? "
        params.append(role)
    if day_hint:
        query += "AND s.nominal_day_start<=? AND s.nominal_day_end>=? "
        params.extend([day_hint, day_hint])
    query += "ORDER BY score LIMIT ?"
    params.append(limit)
    try:
        with _connect_db(root / INDEX) as conn:
            conn.row_factory = sqlite3.Row
            hits = []
            for row in conn.execute(query, params):
                record = dict(row)
                record["literal_day_mentions"] = json.loads(record.pop("day_mentions_json"))
                record["editorial_state"] = "LITERAL_SOURCE_EVIDENCE_NOT_CANON_CERTIFIED"
                record["snippet"] = record["snippet"][:1000]
                hits.append(record)
    except sqlite3.Error as exc:
        raise GateError("Historical text query failed valid FTS syntax") from None
    return {
        "schema": "worldroot-literal-search-result-v1", "query": phrase,
        "match_mode": match_mode, "hits": hits, "result_count": len(hits),
        "historical_index_sha256": state["manifest_sha256"],
        "canon_changed": False,
        "limitation": (
            "A matching transcript is literal evidence, not a certified canonical "
            "event. Verify original lines and present HEAD before narrating."
        ),
    }


def process_requests(root: Path):
    requests = root / "history" / "requests"
    results = root / "history" / "results"
    if not requests.is_dir():
        return {"processed": 0}
    results.mkdir(parents=True, exist_ok=True)
    pending = sorted(requests.glob("*.json"))
    if len(pending) > 200:
        raise GateError("Too many historical search requests")
    count = 0
    for file in pending:
        if file.is_symlink() or not re.fullmatch(r"[a-zA-Z0-9_-]{3,100}\.json", file.name):
            raise GateError("Unsafe search request file")
        dest = results / file.name
        if dest.exists():
            if dest.is_symlink():
                raise GateError("Unsafe historical result path")
            continue
        req = _load_json(file)
        if req.get("schema") != "worldroot-literal-search-request-v1" or (
                req.get("author_source") != "USER_MESSAGE"):
            raise GateError("Untrusted historical search request envelope")
        result = search(
            root, req.get("query"), limit=req.get("limit", 6),
            role=req.get("role"), day_hint=req.get("day_hint"),
            match_mode=req.get("match_mode", "all"),
        )
        dest.write_bytes(_canonical(result))
        count += 1
    return {"processed": count, "canon_changed": False}


def main(argv=None):
    p = argparse.ArgumentParser(description="Immutable historic Drive transcript search")
    p.add_argument("action", choices=("build", "verify", "search", "process-requests"))
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--day-hint", type=int)
    p.add_argument("--role")
    p.add_argument("--match-mode", default="all")
    args = p.parse_args(argv)
    try:
        if args.action == "build":
            result = build(args.archive_root)
        elif args.action == "verify":
            result = verify(args.archive_root, with_source_checks=True)
        elif args.action == "search":
            result = search(
                args.archive_root, args.query, limit=args.limit, role=args.role,
                day_hint=args.day_hint, match_mode=args.match_mode,
            )
        else:
            result = process_requests(args.archive_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (GateError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
        print("WORLDROOT_HISTORY_GATE_BLOCKED: " + type(exc).__name__ + ": "
              + str(exc)[:200], file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
