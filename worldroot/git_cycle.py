"""WORLDROOT GitHub-only canonical journal and recoverable SQLite projection.

No Google/OIDC credentials. The story-archive Git branch is the atomic durable
commit boundary; SQLite is a versioned local projection, rebuildable from
immutable canon/episodes/*.json. Only a trusted GitHub Action may push the
resulting changes. Neither a green CI nor this CLI authenticates the human
author or approves narrative semantics.
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

from .choice_intake import verify_tree as verify_choices, IntakeError
from .episode_pipeline import EpisodeDraft
from .semantic_gate import require_reviewed_event_evidence
from .ledger import GateError, ConflictError
from .temporal_projection import event_day, load_corrections, projected_knowledge_day

VERSION = "worldroot-git-canon-v1"
PARTS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
REQUIRED = ("narrativa_integral.md", "opcoes.json", "eventos_e_consequencias.json",
            "checkpoint_candidato.json", "episode_draft.json")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,127}$")
CLOCK = re.compile(r"^(?:[01]\d|2[0-3])h[0-5]\d$")
BOOTSTRAP_ID = "LV-C15-PI-D528"
DEFAULT_EPISODE = "LV-C15-PII-D529-AUTHOR-SOURCE"


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def load(path: Path):
    if not path.is_file() or path.is_symlink():
        raise GateError("Missing or unsafe canonical artifact: " + path.name)
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except (ValueError, UnicodeError):
        raise GateError("Invalid canonical JSON: " + path.name) from None


def check_id(value: str):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise GateError("Invalid immutable episode identifier")


def clean_db(conn: sqlite3.Connection):
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS head (
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            sequence INTEGER NOT NULL, episode_id TEXT NOT NULL,
            day INTEGER NOT NULL, book TEXT NOT NULL, chapter INTEGER NOT NULL,
            part TEXT NOT NULL, hour TEXT NOT NULL,
            head_sha256 TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS episodes (
            episode_id TEXT PRIMARY KEY,
            sequence INTEGER NOT NULL UNIQUE,
            source_sha256 TEXT NOT NULL,
            choice_sha256 TEXT NOT NULL UNIQUE,
            closure_sha256 TEXT NOT NULL UNIQUE,
            day INTEGER NOT NULL, hour TEXT NOT NULL,
            chapter INTEGER NOT NULL, part TEXT NOT NULL,
            chosen_option INTEGER NOT NULL,
            canonical_status TEXT NOT NULL CHECK(canonical_status='FECHADO')
        );
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            episode_id TEXT NOT NULL REFERENCES episodes(episode_id),
            summary TEXT NOT NULL, event_type TEXT NOT NULL,
            visibility TEXT NOT NULL, day INTEGER NOT NULL,
            hour TEXT, source_line INTEGER NOT NULL,
            source_anchor TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS npc_knowledge (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES events(event_id),
            episode_id TEXT NOT NULL REFERENCES episodes(episode_id),
            description TEXT NOT NULL, acquired_day INTEGER NOT NULL,
            acquired_time TEXT, visibility TEXT NOT NULL,
            UNIQUE(person,event_id,description)
        );
        CREATE INDEX IF NOT EXISTS ix_knowledge_asof
            ON npc_knowledge(person,acquired_day,acquired_time);
        CREATE TABLE IF NOT EXISTS receipts (
            episode_id TEXT PRIMARY KEY REFERENCES episodes(episode_id),
            choice_sha256 TEXT NOT NULL, closure_sha256 TEXT NOT NULL,
            published_to TEXT NOT NULL CHECK(published_to='GITHUB_PRIVATE_ONLY'),
            drive_status TEXT NOT NULL CHECK(drive_status='NAO_SINCRONIZADO')
        );
    """)


def verify_db(root: Path, head: dict) -> dict:
    db = root / "canon" / "state.sqlite"
    if not db.is_file() or db.is_symlink():
        raise GateError("Versioned SQLite snapshot missing; run restore from journal")
    connection = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise GateError("SQLite integrity_check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise GateError("SQLite foreign_key_check failed")
        row = connection.execute(
            "SELECT sequence,episode_id,day,book,chapter,part,hour,head_sha256 FROM head WHERE singleton=1"
        ).fetchone()
        if row is None:
            raise GateError("SQLite head is empty")
        expected = (head["sequence"], head["episode_id"], head["day"], head["book"],
                    head["chapter"], head["part"], head["hour"], sha(canonical(head)))
        if tuple(row) != expected:
            raise GateError("SQLite and canonical HEAD disagree")
        entries = connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        if entries != head["sequence"]:
            raise GateError("SQLite has a different canonical episode count")
        # Detect projection drift, including historical cross-midnight records.
        # Reading four or a few dozen small closure JSONs is deliberately cheap.
        corrections = load_corrections(root, load)
        for journal_path in sorted((root / "canon" / "episodes").glob("*.json")):
            closure = load(journal_path)
            meta_day = closure["metadata"]["day"]
            by_event = {ev["event_id"]: ev for ev in closure["events"]}
            for ev in closure["events"]:
                actual = connection.execute("SELECT day FROM events WHERE event_id=?", (ev["event_id"],)).fetchone()
                if actual is None or actual[0] != event_day(ev, meta_day):
                    raise GateError("SQLite event day diverges from immutable source; restore required")
            for item in closure["knowledge"]:
                source = by_event.get(item["source_event"])
                if source is None:
                    raise GateError("Canonical NPC knowledge references absent event")
                expected_day = projected_knowledge_day(
                    closure["episode_id"], item, source, meta_day, corrections)
                actual = connection.execute(
                    "SELECT acquired_day FROM npc_knowledge "
                    "WHERE episode_id=? AND person=? AND event_id=? AND description=?",
                    (closure["episode_id"], item["person"], item["source_event"], item["knowledge"]),
                ).fetchone()
                if actual is None or actual[0] != expected_day:
                    raise GateError("SQLite NPC knowledge day diverges from source; restore required")
        return {"sequence": row[0], "episodes": entries}
    finally:
        connection.close()


def _write_head_in_db(conn, head):
    conn.execute("DELETE FROM head WHERE singleton=1")
    conn.execute(
        "INSERT INTO head VALUES (1,?,?,?,?,?,?,?,?)",
        (head["sequence"], head["episode_id"], head["day"], head["book"],
         head["chapter"], head["part"], head["hour"], sha(canonical(head))),
    )


def _save_snapshot(conn, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".sqlite", delete=False) as f:
        tmp = Path(f.name)
    try:
        with sqlite3.connect(tmp) as destination:
            conn.backup(destination)
        with sqlite3.connect(tmp) as test:
            if test.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise GateError("SQLite backup could not be restored")
            if test.execute("PRAGMA foreign_key_check").fetchall():
                raise GateError("SQLite backup has broken references")
        tmp.replace(output)
    finally:
        if tmp.exists():
            tmp.unlink()


def write_context(root: Path, head: dict) -> dict:
    """Generate human-readable memory index from the verified SQLite projection.

    No inference, no new facts, no automatic spreading of private knowledge.
    A character without an explicit knowledge row does NOT know the event.
    """
    db = root / "canon" / "state.sqlite"
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        events = [dict(x) for x in conn.execute(
            "SELECT event_id,episode_id,summary,event_type,visibility,day,hour,source_line,source_anchor "
            "FROM events ORDER BY day DESC,COALESCE(hour,'') DESC,event_id DESC LIMIT 150"
        ).fetchall()]
        knowledge = [dict(x) for x in conn.execute(
            "SELECT person,event_id,episode_id,description,acquired_day,acquired_time,visibility "
            "FROM npc_knowledge ORDER BY acquired_day DESC,COALESCE(acquired_time,'') DESC,row_id DESC LIMIT 750"
        ).fetchall()]
    characters = {}
    for item in knowledge:
        characters.setdefault(item["person"], []).append({
            "source_event": item["event_id"], "episode_id": item["episode_id"],
            "description": item["description"], "acquired_day": item["acquired_day"],
            "acquired_time": item["acquired_time"], "visibility": item["visibility"],
        })
    payload = {
        "schema": "worldroot-context-index-v1", "derived_only": True,
        "head": head, "head_sha256": sha(canonical(head)),
        "recent_narrated_events": events, "explicit_character_knowledge": characters,
        "temporal_rule": "Unknown clock is NOT permission to learn the event earlier within the same day",
        "canonical_scope": "D528 baseline + GitHub journal closures; historical Drive records require separate read",
        "prohibited_assumptions": [
            "An event in BASTIDORES is not universal character knowledge",
            "No automatic retcon or weakening of GENESE",
            "Livro V remains open without the author's explicit closure",
            "Drive HEAD has not been synchronized by this GitHub-only runner",
        ],
    }
    (root / "canon" / "CONTEXT.json").write_bytes(canonical(payload))
    return payload


def bootstrap(root: Path) -> dict:
    """Prepare D528 historical baseline without asserting that D529 was closed."""
    canon_dir = root / "canon"
    if (canon_dir / "HEAD.json").exists() or (canon_dir / "state.sqlite").exists():
        raise GateError("Bootstrap is one-time; canonical files already exist")
    req = load(canon_dir / "BOOTSTRAP_REQUEST.json")
    if (req.get("schema") != "worldroot-bootstrap-request-v1"
            or req.get("source_episode") != BOOTSTRAP_ID
            or req.get("authorized_by") != "USER_REQUEST"):
        raise GateError("Expected explicit D528 bootstrap request")
    folder = root / "episodes" / "bootstrap" / BOOTSTRAP_ID
    manifest = load(folder / "manifesto_recuperacao.json")
    literal = folder / "fonte_literal_drive_D528.txt"
    if not literal.is_file() or literal.is_symlink():
        raise GateError("D528 original is missing")
    content = literal.read_bytes()
    if (manifest.get("schema") != "worldroot-bootstrap-source-v1"
            or manifest.get("status") != "PRESERVED_HISTORICAL_LITERAL_ONLY"
            or manifest.get("utf8_bytes") != len(content)):
        raise GateError("D528 preserved source checksum/size invalid")
    source_sha = sha(content)
    git_blob_sha1 = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + bytes([0]) + content
    ).hexdigest()
    if (manifest.get("github_blob_sha1") != git_blob_sha1
            and manifest.get("github_blob_sha1") is not None):
        raise GateError("D528 Git blob SHA-1 mismatch")
    if (req.get("source_sha256") != source_sha
            and req.get("source_git_blob_sha1") != git_blob_sha1):
        raise GateError("D528 bootstrap request must match verified source SHA")
    head = {
        "schema": VERSION, "sequence": 0, "episode_id": BOOTSTRAP_ID,
        "day": 528, "book": "Livro V", "chapter": 15, "part": "I",
        "hour": "23h06", "location": "Casa do Jardim Branco, Três Arcos",
        "source_sha256": source_sha, "previous_head_sha256": None,
        "closure_sha256": None, "drive_head_status": "LEGADO_D528_NAO_ALTERADO",
        "engine_mode": "GITHUB_PRIVADO_SEM_OIDC",
        "book_closed": False,
    }
    with tempfile.TemporaryDirectory() as temp:
        src = Path(temp) / "base.sqlite"
        conn = sqlite3.connect(src)
        try:
            clean_db(conn)
            _write_head_in_db(conn, head)
            conn.commit()
            _save_snapshot(conn, canon_dir / "state.sqlite")
        finally:
            conn.close()
    (canon_dir / "HEAD.json").write_bytes(canonical(head))
    verify_db(root, head)
    write_context(root, head)
    return {"result": "BOOTSTRAP_D528_GITHUB_ONLY", "sequence": 0, "head": BOOTSTRAP_ID,
            "source_sha256": source_sha, "drive_changed": False}


def verify_episode(root: Path, episode_id: str) -> tuple[EpisodeDraft, dict]:
    check_id(episode_id)
    folder = root / "episodes" / episode_id / "draft"
    manifest = load(folder / "manifesto_imutavel.json")
    if (manifest.get("schema") != "worldroot-episode-package-v1"
            or manifest.get("delivery_id") != episode_id
            or manifest.get("canon_status") != "RASCUNHO"):
        raise GateError("Draft manifest identity/status invalid")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(REQUIRED):
        raise GateError("Draft must have exactly the five immutable sidecars")
    blobs = {}
    for name in REQUIRED:
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise GateError("Missing immutable sidecar " + name)
        body = path.read_bytes()
        expected = artifacts[name]
        if (not isinstance(expected, dict) or expected.get("sha256") != sha(body)
                or type(expected.get("bytes")) is not int or expected["bytes"] != len(body)):
            raise GateError("Immutable sidecar checksum mismatch: " + name)
        blobs[name] = body
    if manifest.get("original_readback_sha256") != sha(blobs["narrativa_integral.md"]):
        raise GateError("Original immutable narrative hash mismatch")
    try:
        payload = json.loads(blobs["episode_draft.json"].decode("utf-8"))
        options = json.loads(blobs["opcoes.json"].decode("utf-8"))
        events = json.loads(blobs["eventos_e_consequencias.json"].decode("utf-8"))
        meta = json.loads(blobs["checkpoint_candidato.json"].decode("utf-8"))
        draft = EpisodeDraft.from_dict(payload)
    except (ValueError, UnicodeError, TypeError, KeyError):
        raise GateError("Archived draft has an invalid structured sidecar") from None
    if (payload.get("delivery_id") != episode_id or payload.get("choices") != options
            or payload.get("events") != events or payload.get("metadata") != meta
            or draft.full_text.encode("utf-8") != blobs["narrativa_integral.md"]):
        raise GateError("Archived story and structured sidecars disagree")
    draft.validate()
    return draft, manifest


def review_deltas(root: Path, episode_id: str, draft: EpisodeDraft) -> tuple[list[dict], list[dict]]:
    folder = root / "episodes" / episode_id / "review"
    reviewed = load(folder / "eventos_revisados.json")
    knowledge = load(folder / "conhecimento_revisado.json")
    if (reviewed.get("schema") != "worldroot-reviewed-events-v1"
            or reviewed.get("episode_id") != episode_id
            or reviewed.get("review_status") != "REVISADO"
            or reviewed.get("source_sha256") != sha(draft.full_text.encode("utf-8"))):
        raise GateError("Reviewed event provenance/approval marker absent")
    events = reviewed.get("events")
    if not isinstance(events, list) or not events:
        raise GateError("Closing chapter requires nonempty reviewed events")
    require_reviewed_event_evidence(draft, events)
    all_event_ids = {e["event_id"] for e in events}
    for ev in events:
        actual_day = event_day(ev, draft.metadata["day"])
        if actual_day < draft.metadata["day"] - 1:
            # Older-than-yesterday events are permitted only when the same
            # multi-day installment explicitly narrates those intermediate days.
            from .day_arc_audit import inspect_day_arc
            arc = inspect_day_arc(draft.prose)
            if (not arc["chronological"] or not arc["last"]
                    or arc["last"]["day"] != draft.metadata["day"]
                    or actual_day not in arc["days_touched"]
                    or arc["days_touched"] != list(range(arc["first"]["day"], draft.metadata["day"] + 1))):
                raise GateError("Reviewed event day outside narrated multi-day installment")
    if (knowledge.get("schema") != "worldroot-reviewed-knowledge-v1"
            or knowledge.get("episode_id") != episode_id
            or knowledge.get("review_status") != "REVISADO"):
        raise GateError("Character knowledge review absent")
    kn = knowledge.get("knowledge")
    if not isinstance(kn, list):
        raise GateError("Character knowledge must be an explicit list")
    keyset = set()
    for item in kn:
        if not isinstance(item, dict):
            raise GateError("Invalid knowledge record")
        if (not isinstance(item.get("person"), str) or not item["person"].strip()
                or not isinstance(item.get("knowledge"), str) or len(item["knowledge"]) < 8
                or item.get("source_event") not in all_event_ids):
            raise GateError("Character knowledge requires actual linked event")
        source_event = next(ev for ev in events if ev["event_id"] == item["source_event"])
        source_day = event_day(source_event, draft.metadata["day"])
        knowledge_day = item.get("acquired_day")
        if (type(knowledge_day) is not int
                or not source_day <= knowledge_day <= draft.metadata["day"]):
            raise GateError("Character knowledge day precedes source or exceeds chapter")
        clock = item.get("clock")
        if clock is not None and (not isinstance(clock, str) or not CLOCK.fullmatch(clock)):
            raise GateError("Invalid character knowledge clock")
        if item.get("visibility") not in ("PUBLICO", "PRIVADO_PERSONAGEM", "BASTIDORES"):
            raise GateError("Invalid character knowledge visibility")
        event_clock = source_event.get("clock")
        if event_clock is not None and (not isinstance(event_clock, str) or not CLOCK.fullmatch(event_clock)):
            raise GateError("Event clock must be valid HHhMM")
        if (clock is not None and event_clock is not None
                and knowledge_day == source_day and clock < event_clock):
            raise GateError("Character cannot know an event before it happened")
        if (clock is not None and knowledge_day == draft.metadata["day"]
                and clock > draft.metadata["hour"]):
            raise GateError("Character cannot gain knowledge after episode checkpoint")
        key = (item["person"], item["source_event"], item["knowledge"])
        if key in keyset:
            raise ConflictError("Duplicate character knowledge record")
        keyset.add(key)
    return events, kn


def _chronology(previous: dict, meta: dict, *, prose: str | None = None):
    for key in ("day", "chapter", "part", "hour", "book", "location"):
        if key not in meta:
            raise GateError("Episode lacks chronology " + key)
    if (type(meta["day"]) is not int or type(meta["chapter"]) is not int
            or not isinstance(meta["hour"], str) or not CLOCK.fullmatch(meta["hour"])):
        raise GateError("Invalid chapter clock/day")
    if previous.get("book_closed") is True:
        raise GateError("Previous book closed; starting a new book needs its own explicit opening workflow")
    if meta["book"] != previous["book"] or meta["day"] < previous["day"]:
        raise GateError("Book/day transition not approved")
    if meta["day"] > previous["day"] + 1:
        # r14.1: a part may LIVE several days, but must show EVERY day and
        # monotonically advance time. No date jump based on metadata alone.
        from .day_arc_audit import inspect_day_arc
        if not isinstance(prose, str) or not prose.strip():
            raise GateError("Multi-day part requires original scene prose for verification")
        arc = inspect_day_arc(prose)
        days = list(range(previous["day"], meta["day"] + 1))
        if (not arc["chronological"] or arc["days_touched"] != days
                or not arc["first"] or not arc["last"]
                or arc["first"]["day"] != previous["day"]
                or arc["last"]["day"] != meta["day"]
                or arc["last"]["hour"] != meta["hour"]):
            raise GateError("Multi-day part must narrate every date in order and end at metadata clock")
    if meta["day"] == previous["day"] and meta["hour"] < previous["hour"]:
        raise GateError("Cannot move same-day clock backwards")
    if meta["part"] not in PARTS or previous["part"] not in PARTS:
        raise GateError("Invalid five-part structure")
    expected_chapter = previous["chapter"]
    expected_part = PARTS[previous["part"]] + 1
    if expected_part > 5:
        expected_chapter += 1
        expected_part = 1
    if meta["chapter"] != expected_chapter or PARTS[meta["part"]] != expected_part:
        raise GateError("Unexpected chapter/part progression")


def _closure(root, episode_id, head, choice, draft, events, kn):
    choice_blob = canonical(choice)
    evidence = sha(draft.full_text.encode("utf-8"))
    payload = {
        "schema": "worldroot-github-closure-v1",
        "episode_id": episode_id, "sequence": head["sequence"] + 1,
        "previous_episode_id": head["episode_id"],
        "previous_head_sha256": sha(canonical(head)),
        "story_sha256": evidence,
        "choice_sha256": sha(choice_blob),
        "chosen_option": choice["option"], "free_text": choice["free_text"],
        "metadata": {key: draft.metadata[key] for key in ("day", "book", "chapter", "part", "hour", "location")},
        "events": events, "knowledge": kn,
        "visibility": "PRIVADO", "status": "FECHADO_GITHUB",
        "drive_status": "NAO_SINCRONIZADO",
    }
    if draft.book_closed:
        payload["book_closed"] = True
    return payload


def apply_closure_db(conn, closure: dict, new_head: dict, corrections=None):
    episode = closure["episode_id"]
    meta = closure["metadata"]
    corrections = corrections or {}
    events_by_id = {x["event_id"]: x for x in closure["events"]}
    conn.execute(
        "INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (episode, closure["sequence"], closure["story_sha256"],
         closure["choice_sha256"], sha(canonical(closure)), meta["day"], meta["hour"],
         meta["chapter"], meta["part"], closure["chosen_option"], "FECHADO"),
    )
    for event in closure["events"]:
        src = event["source"]
        conn.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
            (event["event_id"], episode, event["summary_candidato"], event.get("event_type", "NARRADO"),
             event["visibility"], event_day(event, meta["day"]), event.get("clock"),
             src["line"], src["literal_anchor"]),
        )
    for item in closure["knowledge"]:
        linked = events_by_id.get(item["source_event"])
        if linked is None:
            raise GateError("NPC knowledge source event missing from closure")
        projected_day = projected_knowledge_day(
            episode, item, linked, meta["day"], corrections)
        conn.execute(
            "INSERT INTO npc_knowledge (person,event_id,episode_id,description,acquired_day,acquired_time,visibility) VALUES (?,?,?,?,?,?,?)",
            (item["person"], item["source_event"], episode, item["knowledge"],
             projected_day, item["clock"], item["visibility"]),
        )
    conn.execute("INSERT INTO receipts VALUES (?,?,?,?,?)",
                 (episode, closure["choice_sha256"], sha(canonical(closure)),
                  "GITHUB_PRIVATE_ONLY", "NAO_SINCRONIZADO"))
    _write_head_in_db(conn, new_head)


def close(root: Path) -> dict:
    head = load(root / "canon" / "HEAD.json")
    if head.get("schema") != VERSION:
        raise GateError("GitHub operational canon has not been bootstrapped")
    verify_db(root, head)
    selections = verify_choices(root)
    pending = [
        item for item in selections
        if not (root / "canon" / "episodes" / (item["episode_id"] + ".json")).exists()
    ]
    if not pending:
        current = root / "canon" / "episodes" / (head["episode_id"] + ".json")
        if not current.is_file():
            raise GateError("No pending authored choice")
        return {"result": "IDEMPOTENTE", "episode_id": head["episode_id"],
                "sequence": head["sequence"]}
    if len(pending) != 1:
        raise GateError("Only one pending author choice per closure batch")
    selected = pending[0]
    episode_id = selected["episode_id"]
    path = root / "choices" / episode_id / f"option-{selected['option']}.json"
    choice = load(path)
    draft, _ = verify_episode(root, episode_id)
    closure_path = root / "canon" / "episodes" / f"{episode_id}.json"
    if closure_path.exists():
        previous = load(closure_path)
        if previous.get("choice_sha256") != sha(canonical(choice)):
            raise ConflictError("Repeated episode choice differs from canonical selection")
        if head["episode_id"] != episode_id:
            raise GateError("Closed episode is not current HEAD; cannot implicitly replay")
        return {"result": "IDEMPOTENTE", "episode_id": episode_id, "sequence": head["sequence"]}
    if head["episode_id"] == episode_id:
        raise GateError("Current HEAD already at selected episode but closure receipt missing")
    if draft.metadata.get("canon_status") != "RASCUNHO":
        raise GateError("Only a saved draft may be closed")
    _chronology(head, draft.metadata, prose=draft.prose)
    if draft.book_closed:
        from .book_closure import require_book_end_approval
        require_book_end_approval(root, episode_id, draft.metadata["book"])
    events, kn = review_deltas(root, episode_id, draft)
    closure = _closure(root, episode_id, head, choice, draft, events, kn)
    new_head = {
        "schema": VERSION, "sequence": closure["sequence"],
        "episode_id": episode_id, "day": draft.metadata["day"],
        "book": draft.metadata["book"], "chapter": draft.metadata["chapter"],
        "part": draft.metadata["part"], "hour": draft.metadata["hour"],
        "location": draft.metadata["location"],
        "source_sha256": closure["story_sha256"],
        "previous_head_sha256": closure["previous_head_sha256"],
        "closure_sha256": sha(canonical(closure)),
        "drive_head_status": "NAO_SINCRONIZADO",
        "engine_mode": "GITHUB_PRIVADO_SEM_OIDC", "book_closed": draft.book_closed,
    }
    with tempfile.TemporaryDirectory() as t:
        temporary = Path(t) / "updated.sqlite"
        with sqlite3.connect(f"file:{root / 'canon' / 'state.sqlite'}?mode=ro", uri=True) as source:
            with sqlite3.connect(temporary) as connection:
                source.backup(connection)
        with sqlite3.connect(temporary) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            try:
                connection.execute("BEGIN IMMEDIATE")
                apply_closure_db(connection, closure, new_head,
                                 load_corrections(root, load))
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            _save_snapshot(connection, root / "canon" / "state.sqlite")
    closure_path.parent.mkdir(parents=True, exist_ok=True)
    # All three outputs must be committed in a single Git commit by the caller.
    # If the Git push fails, re-run from the previous Git tree, not the runner.
    closure_path.write_bytes(canonical(closure))
    (root / "canon" / "HEAD.json").write_bytes(canonical(new_head))
    verify_db(root, new_head)
    write_context(root, new_head)
    return {"result": "FECHADO_GITHUB", "episode_id": episode_id,
            "sequence": new_head["sequence"], "head_sha256": sha(canonical(new_head)),
            "events": len(events), "knowledge": len(kn), "drive_changed": False}


def _journal(root: Path):
    current = {
        "schema": VERSION, "sequence": 0, "episode_id": BOOTSTRAP_ID,
        "day": 528, "book": "Livro V", "chapter": 15, "part": "I",
        "hour": "23h06", "location": "Casa do Jardim Branco, Três Arcos",
        "source_sha256": sha((root / "episodes" / "bootstrap" / BOOTSTRAP_ID / "fonte_literal_drive_D528.txt").read_bytes()),
        "previous_head_sha256": None, "closure_sha256": None,
        "drive_head_status": "LEGADO_D528_NAO_ALTERADO",
        "engine_mode": "GITHUB_PRIVADO_SEM_OIDC", "book_closed": False,
    }
    while True:
        files = sorted((root / "canon" / "episodes").glob("*.json")) if (root / "canon" / "episodes").exists() else []
        remaining = [f for f in files if load(f).get("sequence") == current["sequence"] + 1]
        if not remaining:
            break
        if len(remaining) != 1:
            raise ConflictError("Conflicting journal sequence")
        clos = load(remaining[0])
        if (clos.get("schema") != "worldroot-github-closure-v1"
                or clos.get("previous_head_sha256") != sha(canonical(current))
                or clos.get("previous_episode_id") != current["episode_id"]
                or clos.get("episode_id") != remaining[0].stem):
            raise GateError("Canonical journal chain failed")
        draft, manifest = verify_episode(root, clos["episode_id"])
        if clos.get("story_sha256") != manifest["original_readback_sha256"]:
            raise GateError("Journal references different immutable narrative")
        opts = clos.get("chosen_option")
        choice_path = root / "choices" / clos["episode_id"] / f"option-{opts}.json"
        choice = load(choice_path)
        if sha(canonical(choice)) != clos.get("choice_sha256"):
            raise GateError("Journal author choice SHA changed")
        require_reviewed_event_evidence(draft, clos.get("events", []))
        expected = _closure(root, clos["episode_id"], current, choice, draft,
                            clos["events"], clos["knowledge"])
        if canonical(clos) != canonical(expected):
            raise GateError("Canonical episode journal mutated after approval")
        new_head = {
            "schema": VERSION, "sequence": clos["sequence"],
            "episode_id": clos["episode_id"], "day": clos["metadata"]["day"],
            "book": clos["metadata"]["book"], "chapter": clos["metadata"]["chapter"],
            "part": clos["metadata"]["part"], "hour": clos["metadata"]["hour"],
            "location": clos["metadata"]["location"],
            "source_sha256": clos["story_sha256"],
            "previous_head_sha256": clos["previous_head_sha256"],
            "closure_sha256": sha(canonical(clos)),
            "drive_head_status": "NAO_SINCRONIZADO",
            "engine_mode": "GITHUB_PRIVADO_SEM_OIDC", "book_closed": draft.book_closed,
        }
        yield clos, new_head
        current = new_head
    if len(files) != current["sequence"]:
        raise GateError("Orphan or nonsequential closure files")


def restore(root: Path) -> dict:
    """Regenerate SQLite ONLY from immutable canonical journal, verify HEAD."""
    target = load(root / "canon" / "HEAD.json")
    literal = root / "episodes" / "bootstrap" / BOOTSTRAP_ID / "fonte_literal_drive_D528.txt"
    if not literal.is_file():
        raise GateError("Cannot recover without preserved D528 original")
    base = {
        "schema": VERSION, "sequence": 0, "episode_id": BOOTSTRAP_ID,
        "day": 528, "book": "Livro V", "chapter": 15, "part": "I",
        "hour": "23h06", "location": "Casa do Jardim Branco, Três Arcos",
        "source_sha256": sha(literal.read_bytes()),
        "previous_head_sha256": None, "closure_sha256": None,
        "drive_head_status": "LEGADO_D528_NAO_ALTERADO",
        "engine_mode": "GITHUB_PRIVADO_SEM_OIDC", "book_closed": False,
    }
    with tempfile.TemporaryDirectory() as t:
        path = Path(t) / "restored.sqlite"
        conn = sqlite3.connect(path)
        try:
            clean_db(conn)
            _write_head_in_db(conn, base)
            # Release the write transaction before SQLite online-backup.
            # Backing up an uncommitted writer on its own connection can hang.
            conn.commit()
            current = base
            n = 0
            for clos, new_head in _journal(root):
                span = clos["metadata"]["day"] - current["day"]
                literal_prose = (load(root / "episodes" / clos["episode_id"]
                                      / "draft" / "episode_draft.json")["prose"]
                                 if span > 1 else None)
                _chronology(current, clos["metadata"], prose=literal_prose)
                conn.execute("BEGIN IMMEDIATE")
                apply_closure_db(conn, clos, new_head, load_corrections(root, load))
                conn.commit()
                current = new_head
                n += 1
            if canonical(target) != canonical(current):
                raise GateError("Replay differs from durable canonical HEAD; stop")
            _save_snapshot(conn, root / "canon" / "state.sqlite")
        finally:
            conn.close()
    verify_db(root, target)
    write_context(root, target)
    return {"result": "RESTORED_FROM_IMMUTABLE_JOURNAL", "sequence": target["sequence"],
            "episodes": n, "drive_changed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="WORLDROOT GitHub-only atomic canon and SQLite")
    parser.add_argument("command", choices=("bootstrap", "close", "verify", "restore", "status"))
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.archive_root.resolve()
    if args.command == "bootstrap":
        result = bootstrap(root)
    elif args.command == "close":
        result = close(root)
    elif args.command == "restore":
        result = restore(root)
    else:
        head = load(root / "canon" / "HEAD.json")
        detail = verify_db(root, head) if args.command == "verify" else {}
        result = {"result": "VERIFIED" if args.command == "verify" else "STATUS",
                  "head": head, "sqlite": detail, "drive_changed": False}
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GateError, IntakeError, ConflictError, OSError, sqlite3.Error, ValueError) as exc:
        print("WORLDROOT_GITHUB_CYCLE_BLOCKED: " + type(exc).__name__ + ": " + str(exc)[:220],
              file=sys.stderr)
        raise SystemExit(1)
