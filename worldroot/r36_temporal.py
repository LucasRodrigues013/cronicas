"""R36 temporal bridge: a derived index inside the existing Codex database.
An exact shared source anchor is provenance, never semantic equivalence.
Unlinked canonical events remain visible as review backlog, not entity facts.
"""
import sqlite3
from pathlib import Path
from . import git_cycle as g
from .live_codex import load_registry

def rebuild(db, closures):
    # Run inside the existing disposable Codex build; no second memory store.
    db.execute("""CREATE TABLE IF NOT EXISTS r36_canon_event(
        event_id TEXT PRIMARY KEY, episode TEXT NOT NULL, sequence INTEGER NOT NULL,
        day INTEGER NOT NULL, clock TEXT, visibility TEXT NOT NULL,
        kind TEXT NOT NULL, summary TEXT NOT NULL, source_sha TEXT NOT NULL,
        line INTEGER NOT NULL, anchor TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS r36_source_link(
        canonical_id TEXT NOT NULL REFERENCES r36_canon_event(event_id),
        typed_id TEXT NOT NULL REFERENCES codex_events(event_id),
        PRIMARY KEY(canonical_id,typed_id))""")
    db.execute("CREATE INDEX IF NOT EXISTS r36_canon_time ON r36_canon_event(day,clock,event_id)")
    db.execute("DELETE FROM r36_source_link")
    db.execute("DELETE FROM r36_canon_event")
    for c in closures:
        for e in c["events"]:
            s=e["source"]
            if s["sha256"]!=c["story_sha256"]:
                raise ValueError("Canonical source hash mismatch")
            db.execute("INSERT INTO r36_canon_event VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (e["event_id"],c["episode_id"],c["sequence"],g.event_day(e,c["metadata"]["day"]),
                 e.get("clock"),e["visibility"],e.get("event_type","NARRADO"),
                 e["summary_candidato"],s["sha256"],s["line"],s["literal_anchor"]))
    db.execute("""INSERT INTO r36_source_link
        SELECT c.event_id,t.event_id FROM r36_canon_event c JOIN codex_events t
        ON c.episode=t.episode AND c.sequence=t.sequence AND c.source_sha=t.source_sha
        AND c.day=t.day AND c.clock IS t.clock AND c.line=t.line AND c.anchor=t.anchor""")
    return coverage(db)

def coverage(db):
    total=db.execute("SELECT count(*) FROM r36_canon_event").fetchone()[0]
    linked=db.execute("SELECT count(DISTINCT canonical_id) FROM r36_source_link").fetchone()[0]
    return {"canonical_events":total,"shared_anchor_events":linked,
            "without_shared_anchor":total-linked,"semantic_certification":False}

def entity_history(db, entity, day, clock=None, limit=50):
    if type(day) is not int or day<1 or type(limit) is not int or not 1<=limit<=200:
        raise ValueError("Invalid temporal bounds")
    if clock is not None and (not isinstance(clock,str) or not g.CLOCK.fullmatch(clock)):
        raise ValueError("Invalid clock")
    if not db.execute("SELECT 1 FROM records WHERE id=?",(entity,)).fetchone():
        raise ValueError("Unknown exact entity ID")
    import json
    rows=db.execute("""SELECT e.event_id,e.episode,e.day,e.clock,e.kind,e.body,e.source_sha,e.line,
        GROUP_CONCAT(x.role) FROM codex_event_entities x JOIN codex_events e ON e.event_id=x.event_id
        WHERE x.entity_id=? AND (e.day<? OR (e.day=? AND (? IS NULL OR
        (e.clock IS NOT NULL AND e.clock<=?)))) GROUP BY e.event_id
        ORDER BY e.day DESC,e.clock DESC,e.sequence DESC,e.ordinal DESC""",
        (entity,day,day,clock,clock))
    result=[]
    for eid,ep,d,tm,kind,body,sha,line,roles in rows:
        if json.loads(body).get("scope")!="WORLD":continue
        ids=[r[0] for r in db.execute("""SELECT c.event_id FROM r36_source_link l
            JOIN r36_canon_event c ON c.event_id=l.canonical_id
            WHERE l.typed_id=? AND c.visibility='PUBLICO' ORDER BY c.event_id""",(eid,))]
        result.append({"event_id":eid,"episode":ep,"day":d,"clock":tm,"kind":kind,
            "roles":sorted(roles.split(",")),"source_sha":sha,"line":line,
            "shared_public_source_anchors":ids})
        if len(result)==limit:break
    return result

def query(root,entity,day,clock=None,limit=50):
    root=Path(root);head=g.load(root/"canon/HEAD.json");g.verify_db(root,head)
    reg=load_registry(root)
    path=root/"canon/codex.sqlite"
    if reg is None or not path.is_file() or path.is_symlink():
        raise ValueError("Temporal graph unavailable; sync required")
    import json
    with sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True) as db:
        meta=dict(db.execute("SELECT key,value FROM meta"))
        if json.loads(meta.get("head","null"))!=head or meta.get("registry_sha")!=reg[1]:
            raise ValueError("Stale graph; sync required")
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Graph integrity failed")
        return {"entity":entity,"history":entity_history(db,entity,day,clock,limit),
                "scope":"PUBLIC_TYPED_EVENTS_ONLY","coverage":coverage(db)}
