"""WORLDROOT history reader: evidence-only FTS5 of raw chat exports.

Never import these transcriptions directly into canonical events, character
knowledge or the operating HEAD. Titles give claimed ranges only, and a line
saying 'DIA 123' is a *candidate anchor*, not proof that the day was narrated.
Persist each source SHA256 and each excerpt's line range for reconstruction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

VERSION = "worldroot-history-index-v1"
ROLE_HEADER = re.compile(r"^## (Prompt|Response):\s*$", re.IGNORECASE)
DAY_HEADER = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?DIA\s+0*(\d{1,3})\b", re.IGNORECASE)
MAX_BLOCK_CHARS = 6500
MAX_FILE_SIZE = 30_000_000


class HistoryError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schema(db: sqlite3.Connection):
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS historical_sources (
            source_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            filename TEXT NOT NULL,
            byte_count INTEGER NOT NULL,
            declared_start INTEGER NOT NULL,
            declared_end INTEGER NOT NULL,
            drive_url TEXT NOT NULL,
            file_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status='LITERAL_TRANSCRIPT_UNRECONCILED'),
            active INTEGER NOT NULL CHECK(active IN (0,1)),
            PRIMARY KEY(source_id,source_sha256)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS active_source
          ON historical_sources(source_id) WHERE active=1;
        CREATE TABLE IF NOT EXISTS historical_excerpts (
            excerpt_id INTEGER PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            line_first INTEGER NOT NULL,
            line_last INTEGER NOT NULL,
            speaker TEXT NOT NULL CHECK(speaker IN ('HEADER','AUTHOR','ASSISTANT')),
            excerpt_sha256 TEXT NOT NULL,
            content TEXT NOT NULL,
            UNIQUE(source_id,source_sha256,ordinal),
            FOREIGN KEY(source_id,source_sha256)
              REFERENCES historical_sources(source_id,source_sha256)
        );
        CREATE TABLE IF NOT EXISTS historical_day_anchors (
            source_id TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            excerpt_ordinal INTEGER NOT NULL,
            source_line INTEGER NOT NULL,
            candidate_day INTEGER NOT NULL CHECK(candidate_day BETWEEN 1 AND 999),
            evidence TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status='UNVERIFIED_TEXT_HEADING'),
            PRIMARY KEY(source_id,source_sha256,source_line),
            FOREIGN KEY(source_id,source_sha256,excerpt_ordinal)
              REFERENCES historical_excerpts(source_id,source_sha256,ordinal)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS historical_fts
          USING fts5(content, tokenize='unicode61 remove_diacritics 2');
    """)


def _segments(text: str):
    """Stable, lossless partition into bounded chunks with original line numbers."""
    lines = text.splitlines(keepends=True)
    buf: list[str] = []
    speaker = "HEADER"
    start = 1
    size = 0
    ordinal = 0

    def emit():
        nonlocal ordinal, buf, size
        if not buf:
            return None
        ordinal += 1
        value = (ordinal, start, start + len(buf) - 1, speaker, "".join(buf))
        buf, size = [], 0
        return value

    for n, line in enumerate(lines, 1):
        marker = ROLE_HEADER.match(line.rstrip("\r\n"))
        if marker and buf:
            result = emit()
            if result:
                yield result
            start = n
        if marker:
            speaker = "AUTHOR" if marker.group(1).lower() == "prompt" else "ASSISTANT"
        if buf and size + len(line) > MAX_BLOCK_CHARS:
            result = emit()
            if result:
                yield result
            start = n
        if not buf:
            start = n
        buf.append(line)
        size += len(line)
    result = emit()
    if result:
        yield result


def import_one(db: sqlite3.Connection, source: dict, folder: Path, *, allow_new_version=False):
    keys = {"file_id", "filename", "declared_start", "declared_end", "size_bytes", "url"}
    if not isinstance(source, dict) or not keys.issubset(source):
        raise HistoryError("Incomplete source registry entry")
    name = source["filename"]
    if not isinstance(name, str) or name != Path(name).name or not name.endswith(".txt"):
        raise HistoryError("Source filename must be a simple .txt basename")
    declared_start, declared_end = source["declared_start"], source["declared_end"]
    if (type(declared_start) is not int or type(declared_end) is not int
            or not 1 <= declared_start <= declared_end <= 999):
        raise HistoryError("Invalid declared coverage, not actual certified days")
    path = folder / name
    if not path.is_file() or path.is_symlink():
        raise HistoryError("Missing or unsafe literal source file: " + name)
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_FILE_SIZE or len(raw) != source["size_bytes"]:
        raise HistoryError("Original byte count mismatch or excessive size: " + name)
    if b"\x00" in raw:
        raise HistoryError("NUL is not valid in the indexed chat transcript")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise HistoryError("Not valid UTF-8: " + name) from exc
    source_sha = digest(raw)
    if source.get("sha256") and source["sha256"] != source_sha:
        raise HistoryError("Source checksum mismatch: " + name)
    previous = db.execute(
        "SELECT source_sha256 FROM historical_sources WHERE source_id=? AND active=1",
        (source["file_id"],),
    ).fetchone()
    if previous and previous[0] == source_sha:
        return {"name": name, "result": "IDEMPOTENT", "sha256": source_sha}
    if previous and not allow_new_version:
        raise HistoryError("Source changed: explicit --allow-new-version required")
    if previous:
        db.execute("UPDATE historical_sources SET active=0 WHERE source_id=? AND active=1",
                   (source["file_id"],))
    db.execute("INSERT INTO historical_sources VALUES (?,?,?,?,?,?,?,?,?,?)", (
        source["file_id"], source_sha, name, len(raw), declared_start,
        declared_end, source["url"], source["file_id"],
        "LITERAL_TRANSCRIPT_UNRECONCILED", 1,
    ))
    count, anchors = 0, 0
    chunks = []
    for ordinal, first, last, speaker, content in _segments(text):
        chash = digest(content.encode("utf-8"))
        cur = db.execute("""INSERT INTO historical_excerpts
            (source_id,source_sha256,ordinal,line_first,line_last,speaker,excerpt_sha256,content)
            VALUES (?,?,?,?,?,?,?,?)""", (
            source["file_id"], source_sha, ordinal, first, last, speaker, chash, content,
        ))
        db.execute("INSERT INTO historical_fts(rowid,content) VALUES (?,?)",
                   (cur.lastrowid, content))
        for pos, line in enumerate(content.splitlines(keepends=True)):
            m = DAY_HEADER.match(line)
            if not m:
                continue
            day = int(m.group(1))
            if 1 <= day <= 999:
                db.execute("INSERT INTO historical_day_anchors VALUES (?,?,?,?,?,?,?)", (
                    source["file_id"], source_sha, ordinal, first + pos,
                    day, line.rstrip("\r\n")[:300], "UNVERIFIED_TEXT_HEADING",
                ))
                anchors += 1
        count += 1
        chunks.append(content)
    if "".join(chunks) != text:
        raise HistoryError("Byte-stable textual partition failed: " + name)
    return {"name": name, "result": "IMPORTED_UNRECONCILED", "sha256": source_sha,
            "bytes": len(raw), "excerpts": count, "candidate_day_headers": anchors}


def import_corpus(db_path: Path, registry_path: Path, source_dir: Path,
                  *, allow_new_version=False):
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    sources = registry.get("sources", [])
    if (registry.get("schema") != "worldroot-history-sources-v1" or len(sources) != 6
            or len({x.get("file_id") for x in sources}) != 6):
        raise HistoryError("Expected exactly six unique historical Drive originals")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=db_path.parent) as scratch:
        staging = Path(scratch) / "history.sqlite"
        if db_path.exists():
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as original:
                with sqlite3.connect(staging) as dest:
                    original.backup(dest)
        conn = sqlite3.connect(staging)
        try:
            schema(conn)
            conn.commit()
            conn.execute("BEGIN IMMEDIATE")
            results = [import_one(conn, source, source_dir, allow_new_version=allow_new_version)
                       for source in sources]
            conn.commit()
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise HistoryError("SQLite integrity_check failed")
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise HistoryError("SQLite foreign_key_check failed")
            count = conn.execute("SELECT COUNT(*) FROM historical_excerpts e JOIN historical_sources s ON e.source_id=s.source_id AND e.source_sha256=s.source_sha256 WHERE s.active=1").fetchone()[0]
            conn.close()
            # Filesystem replace is atomic; no canonical HEAD is touched.
            staging.replace(db_path)
            return {"status": "HISTORY_FTS5_READY_NOT_CANON", "source_files": len(sources),
                    "active_excerpts": count, "sources": results, "head_changed": False}
        except Exception:
            conn.rollback()
            conn.close()
            raise


def search(db_path: Path, question: str, limit=8, *, day=None):
    if not question or len(question) > 1000 or type(limit) is not int or not 1 <= limit <= 100:
        raise HistoryError("Invalid query or result count")
    if day is not None and (type(day) is not int or not 1 <= day <= 999):
        raise HistoryError("Day must be an integer hint, not a certified day")
    words = re.findall(r"[^\W_]+", question, flags=re.UNICODE)
    if not words:
        raise HistoryError("No searchable tokens")
    expression = " AND ".join('"' + word.replace('"','""') + '"' for word in words[:12])
    query = """SELECT s.filename,s.drive_url,s.declared_start,s.declared_end,
             e.speaker,e.line_first,e.line_last,e.excerpt_sha256,
             snippet(historical_fts,0,'[',']',' ... ',36), e.content
             FROM historical_fts
             JOIN historical_excerpts e ON e.excerpt_id=historical_fts.rowid
             JOIN historical_sources s ON s.source_id=e.source_id
              AND s.source_sha256=e.source_sha256
             WHERE historical_fts MATCH ? AND s.active=1"""
    args = [expression]
    if day is not None:
        query += " AND s.declared_start <= ? AND s.declared_end >= ?"
        args += [day, day]
    query += " ORDER BY bm25(historical_fts) LIMIT ?"
    args.append(limit)
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as db:
        return [{"source":r[0],"drive_url":r[1],"filename_range_only":[r[2],r[3]],
                 "speaker":r[4],"line_start":r[5],"line_end":r[6],
                 "excerpt_sha256":r[7],"snippet":r[8],"literal_excerpt":r[9],
                 "source_status":"LITERAL_TRANSCRIPT_UNRECONCILED"}
                for r in db.execute(query, args)]


def main(argv=None):
    cli = argparse.ArgumentParser()
    group=cli.add_subparsers(dest="command",required=True)
    ingest=group.add_parser("import")
    ingest.add_argument("--manifest", type=Path, required=True)
    ingest.add_argument("--source-dir", type=Path, required=True)
    ingest.add_argument("--database", type=Path, required=True)
    ingest.add_argument("--allow-new-version", action="store_true")
    query=group.add_parser("search")
    query.add_argument("--database", type=Path,required=True)
    query.add_argument("--query",required=True)
    query.add_argument("--day", type=int)
    query.add_argument("--limit", type=int,default=5)
    args=cli.parse_args(argv)
    try:
        if args.command=="import":
            answer=import_corpus(args.database,args.manifest,args.source_dir,
                                 allow_new_version=args.allow_new_version)
        else:
            answer=search(args.database,args.query,args.limit,day=args.day)
    except (HistoryError,sqlite3.Error,OSError) as exc:
        print("WORLDROOT_HISTORY_BLOCKED: " + str(exc)[:250],file=sys.stderr)
        return 1
    print(json.dumps(answer,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())