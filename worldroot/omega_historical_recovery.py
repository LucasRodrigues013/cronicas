"""OMEGA-008: source-bound historical mention recovery, never canonical facts.
Explicit offline projection on a disposable Codex copy. Source roles are kept
separate; exact names are candidate retrieval, not semantic entity resolution.
No inferred event time, physical presence, age, ownership or character knowledge.
"""
from __future__ import annotations
import hashlib,json,re,sqlite3
from collections import Counter
from pathlib import Path
from .git_cycle import load,verify_db,verify_episode,canonical
from .history_index import read_verified_sources
from .deep_recovery import sections
from .live_codex import norm,load_registry,graph_rows

SCHEMA="worldroot-omega-historical-candidates-v1"
SPEAKER=re.compile(r"^\s*\*\*([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 '\-’]{1,44})\s*[—–-]\*\*\s+")
# Explicit probes, never declare them registered or present.
PROBES=("Osvan","Orelia")
SKIP={"GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE","TRADITION_DESIGN_NOT_OBSERVED","SPECIES_DESIGN_NOT_OBSERVED"}
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def alias_index(rows,probes=PROBES):
    idx={}
    for r in rows:
        if r.get("scope") in SKIP:continue
        for a in (r["name"],*r.get("aliases",[])):
            n=norm(a)
            if len(n)>=3:idx.setdefault(n,set()).add(r["id"])
    for a in probes:
        n=norm(a)
        if len(n)>=3:idx.setdefault(n,set())
    return idx
def matcher(idx):
    return re.compile(r"(?<!\w)(?:"+"|".join(re.escape(x) for x in sorted(idx,key=lambda x:(-len(x),x)))+r")(?!\w)") if idx else re.compile(r"(?!x)x")
def mentions(line,idx,pattern):
    normalized=norm(line)
    found={m.group() for m in pattern.finditer(normalized)}
    speaker=SPEAKER.match(line)
    if speaker:found.add(norm(speaker.group(1)))
    for key in sorted(found):
        ids=sorted(idx.get(key,()))
        yield key,ids,("UNIQUE_ALIAS_CANDIDATE" if len(ids)==1 else "AMBIGUOUS_ALIAS" if ids else "UNREGISTERED_MENTION"),bool(speaker and norm(speaker.group(1))==key)
def initialize(db):
    # Do not touch records, codex_events, state, or closure journal.
    db.execute("""CREATE TABLE IF NOT EXISTS omega_source_mention(
      source_kind TEXT NOT NULL, source_id TEXT NOT NULL, source_sha TEXT NOT NULL,
      role TEXT NOT NULL, line INTEGER NOT NULL, anchor_sha TEXT NOT NULL,
      mention TEXT NOT NULL, candidates TEXT NOT NULL, disposition TEXT NOT NULL,
      speaker_label INTEGER NOT NULL, PRIMARY KEY(source_kind,source_id,line,mention))""")
    db.execute("CREATE INDEX IF NOT EXISTS omega_mention_lookup ON omega_source_mention(mention,source_kind,role)")
    db.execute("""CREATE TABLE IF NOT EXISTS omega_event_candidate(
      event_id TEXT NOT NULL REFERENCES r36_canon_event(event_id), mention TEXT NOT NULL,
      candidates TEXT NOT NULL, disposition TEXT NOT NULL,
      PRIMARY KEY(event_id,mention))""")
    db.execute("CREATE INDEX IF NOT EXISTS omega_event_lookup ON omega_event_candidate(mention)")
def line_rows(kind,source,source_sha,role,start,lines,idx,pattern):
    for n,line in enumerate(lines,start):
        # The hash binds exact line content, without retaining raw private text.
        for key,ids,status,speaker in mentions(line,idx,pattern):
            yield (kind,source,source_sha,role,n,sha(line),key,json.dumps(ids,separators=(",",":")),status,int(speaker))
def rebuild(root,db):
    """Call on a disposable, synced Codex only; exact source identity verified.
    Transcript Response is unreviewed and must never be exposed as world facts.
    """
    root=Path(root)
    head=load(root/"canon/HEAD.json");verify_db(root,head)
    reg=load_registry(root)
    meta=dict(db.execute("SELECT key,value FROM meta"))
    if not reg or meta.get("registry_sha")!=reg[1] or json.loads(meta.get("head","null"))!=head:raise ValueError("Stale graph")
    manifest,sources=read_verified_sources(root)
    idx=alias_index(graph_rows(db));pattern=matcher(idx)
    closures=sorted((load(p) for p in (root/"canon/episodes").glob("*.json")),key=lambda c:c["sequence"])
    if len(closures)!=head["sequence"]:raise ValueError("Incomplete closure journal")
    counts=[];closed_lines=0
    with db:
        initialize(db)
        db.execute("DELETE FROM omega_source_mention");db.execute("DELETE FROM omega_event_candidate")
        for src,body in sources:
            roles=Counter()
            for role,start,lines in sections(body):
                roles[role]+=len(lines)
                if role not in ("Prompt","Response"):continue
                db.executemany("INSERT INTO omega_source_mention VALUES(?,?,?,?,?,?,?,?,?,?)",
                    line_rows("TRANSCRIPT",src["source_name"],src["sha256"],role,start,lines,idx,pattern))
            counts.append({"source":src["source_name"],"nominal_days":[src["nominal_day_start"],src["nominal_day_end"]],"lines":sum(roles.values()),"roles":dict(roles)})
        for c in closures:
            d,m=verify_episode(root,c["episode_id"])
            if m["original_readback_sha256"]!=c["story_sha256"] or not d.full_text.startswith(d.prose):raise ValueError("Closed narrative source mismatch")
            lines=d.prose.splitlines(keepends=True);closed_lines+=len(lines)
            db.executemany("INSERT INTO omega_source_mention VALUES(?,?,?,?,?,?,?,?,?,?)",
                line_rows("CLOSED_PROSE",c["episode_id"],c["story_sha256"],"CLOSED_NARRATIVE",1,lines,idx,pattern))
        # Only public reviewed event summaries/anchors are candidate-indexed.
        # Names in an event do not establish a participant or physical presence.
        for eid,summary,anchor in db.execute("SELECT event_id,summary,anchor FROM r36_canon_event WHERE visibility='PUBLICO'"):
            names={}
            for key,ids,status,_ in mentions(summary+" "+anchor,idx,pattern):names[key]=(ids,status)
            db.executemany("INSERT INTO omega_event_candidate VALUES(?,?,?,?)",((eid,k,json.dumps(v[0],separators=(",",":")),v[1]) for k,v in sorted(names.items())))
        seal={"schema":SCHEMA,"head":head,"registry_sha":reg[1],"source_manifest_sha":hashlib.sha256(canonical(manifest)).hexdigest()}
        db.execute("INSERT OR REPLACE INTO meta VALUES('omega_historical_recovery',?)",(json.dumps(seal,sort_keys=True,ensure_ascii=False),))
        if db.execute("PRAGMA foreign_key_check").fetchall():raise ValueError("Recovery FK failure")
    grouped=[dict(source_kind=k,role=r,mentions=n,distinct_mentions=u) for k,r,n,u in db.execute("SELECT source_kind,role,count(*),count(DISTINCT mention) FROM omega_source_mention GROUP BY source_kind,role ORDER BY source_kind,role")]
    events=db.execute("SELECT count(DISTINCT event_id) FROM omega_event_candidate").fetchone()[0]
    public=db.execute("SELECT count(*) FROM r36_canon_event WHERE visibility='PUBLICO'").fetchone()[0]
    return {"schema":SCHEMA,"sources":counts,"closed_episodes":len(closures),"closed_lines":closed_lines,"mention_counts":grouped,
            "public_events_with_candidate":events,"public_events_total":public,
            "typed_events":db.execute("SELECT count(*) FROM codex_events").fetchone()[0],
            "alias_keys":len(idx),"semantic_certification":False,"canon_changed":False}
def lookup(db,name,*,limit=30):
    """Editorial-only references: no source prose, NPC knowledge or inferred facts."""
    if type(limit) is not int or not 1<=limit<=100 or not norm(name):raise ValueError("Invalid lookup")
    seal=db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()
    if not seal:raise ValueError("Recovery not built")
    s=json.loads(seal[0]);meta=dict(db.execute("SELECT key,value FROM meta"))
    if s["head"]!=json.loads(meta["head"]) or s["registry_sha"]!=meta["registry_sha"]:raise ValueError("Stale recovery")
    key=norm(name)
    counts=[{"source_kind":k,"role":r,"mentions":n,"speaker_labels":a} for k,r,n,a in db.execute(
        "SELECT source_kind,role,count(*),sum(speaker_label) FROM omega_source_mention WHERE mention=? GROUP BY source_kind,role ORDER BY source_kind,role",(key,))]
    # Closed narrative first; source line order is not a chronological inference.
    refs=[dict(source_kind=k,source_id=src,source_sha=sh,role=r,line=l,anchor_sha=a,candidates=json.loads(c),disposition=d,speaker_label=bool(sp)) for k,src,sh,r,l,a,c,d,sp in db.execute(
        "SELECT source_kind,source_id,source_sha,role,line,anchor_sha,candidates,disposition,speaker_label FROM omega_source_mention WHERE mention=? ORDER BY CASE source_kind WHEN 'CLOSED_PROSE' THEN 0 ELSE 1 END,source_id DESC,line DESC LIMIT ?",(key,limit))]
    event_refs=[dict(event_id=e,candidates=json.loads(c),disposition=d) for e,c,d in db.execute("SELECT event_id,candidates,disposition FROM omega_event_candidate WHERE mention=? ORDER BY event_id LIMIT ?",(key,limit))]
    return {"name":name,"counts":counts,"references":refs,"public_event_candidates":event_refs,"scope":"EDITORIAL_CANDIDATES_NOT_FACTS","semantic_certification":False}
