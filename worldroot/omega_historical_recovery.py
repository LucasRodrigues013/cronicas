"""OMEGA-008: source-bound historical mention recovery, never canonical facts.
Explicit offline projection on a disposable Codex copy. Source roles are kept
separate; exact names are candidate retrieval, not semantic entity resolution.
No inferred event time, physical presence, age, ownership or character knowledge.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sqlite3,tempfile
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
    root=Path(root).resolve()
    graph_file=next((r[2] for r in db.execute("PRAGMA database_list") if r[1]=="main"),"")
    if graph_file and Path(graph_file).resolve().is_relative_to(root):raise ValueError("Recovery projection must remain outside the source archive")
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


class SourceReader:
    """Editorial readback of exact source lines; never supplies character knowledge.
    Refuse forged hashes, unclosed episodes, and mismatched transcript roles.
    """
    def __init__(self,root):
        self.root=Path(root).resolve()
        self.head=load(self.root/"canon/HEAD.json");verify_db(self.root,self.head)
        self.closed={c["episode_id"]:c for c in (load(p) for p in (self.root/"canon/episodes").glob("*.json"))}
        if len(self.closed)!=self.head["sequence"]:raise ValueError("Incomplete closure journal")
        self._transcripts=None;self._episodes={}
    def read(self,ref):
        n=ref["line"];source=ref["source_id"];kind=ref["source_kind"];role=ref["role"]
        if type(n) is not int or n<1:raise ValueError("Invalid source line")
        if kind=="CLOSED_PROSE":
            if source not in self.closed or role!="CLOSED_NARRATIVE":raise ValueError("Unclosed or invalid narrative reference")
            c=self.closed[source]
            if source not in self._episodes:
                d,m=verify_episode(self.root,source)
                if m["original_readback_sha256"]!=c["story_sha256"]:raise ValueError("Closed source mismatch")
                self._episodes[source]=d.prose.splitlines(keepends=True)
            lines=self._episodes[source]
            if n>len(lines) or ref["source_sha"]!=c["story_sha256"]:raise ValueError("Closed source hash or range mismatch")
            anchor=lines[n-1]
        elif kind=="TRANSCRIPT":
            if self._transcripts is None:
                _,verified=read_verified_sources(self.root)
                self._transcripts={m["source_name"]:(m,b) for m,b in verified}
            if source not in self._transcripts or role not in ("Prompt","Response"):raise ValueError("Invalid transcript reference")
            m,b=self._transcripts[source]
            if m["sha256"]!=ref["source_sha"]:raise ValueError("Transcript source hash mismatch")
            anchor=None
            for actual,start,lines in sections(b):
                if start<=n<start+len(lines):
                    if actual!=role:raise ValueError("Transcript role mismatch")
                    anchor=lines[n-start];break
            if anchor is None:raise ValueError("Transcript line out of range")
        else:raise ValueError("Unknown source kind")
        if sha(anchor)!=ref["anchor_sha"]:raise ValueError("Source anchor hash mismatch")
        return {**ref,"literal":anchor,"scope":"EDITORIAL_SOURCE_READBACK_NOT_CHARACTER_KNOWLEDGE","semantic_certification":False}

def build_projection(root,destination):
    """Create a new derived DB outside the archive, no clobber, atomically."""
    from .live_codex import sync
    root=Path(root).resolve();destination=Path(destination)
    if destination.resolve().is_relative_to(root) or destination.exists() or destination.is_symlink():
        raise ValueError("Use a new projection outside the archive")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".omega-recovery-",dir=destination.parent) as tmp:
        candidate=Path(tmp)/"graph.sqlite";sync(root,candidate)
        with sqlite3.connect(candidate) as db:
            result=rebuild(root,db)
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Projection integrity failure")
        os.link(candidate,destination)
    return result

def query_projection(root,path,name,limit=30,readback=False):
    root=Path(root).resolve();path=Path(path)
    if not path.is_file() or path.is_symlink():raise ValueError("Projection not available")
    head=load(root/"canon/HEAD.json");verify_db(root,head)
    reg=load_registry(root)
    with sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True) as db:
        raw=db.execute("SELECT value FROM meta WHERE key='omega_historical_recovery'").fetchone()
        if not raw:raise ValueError("Missing historical recovery seal")
        seal=json.loads(raw[0])
        from .history_index import MANIFEST
        if seal.get("schema")!=SCHEMA or seal.get("head")!=head or not reg or seal.get("registry_sha")!=reg[1] or seal.get("source_manifest_sha")!=hashlib.sha256(canonical(load(root/MANIFEST))).hexdigest():raise ValueError("Stale historical recovery")
        result=lookup(db,name,limit=limit)
        if readback:
            reader=SourceReader(root)
            result["references"]=[reader.read(r) for r in result["references"]]
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archive-root",type=Path,required=True)
    subs=p.add_subparsers(dest="action",required=True)
    b=subs.add_parser("build");b.add_argument("--output",type=Path,required=True)
    q=subs.add_parser("query");q.add_argument("--graph",type=Path,required=True);q.add_argument("--name",required=True);q.add_argument("--limit",type=int,default=30);q.add_argument("--readback",action="store_true")
    a=p.parse_args()
    result=build_projection(a.archive_root,a.output) if a.action=="build" else query_projection(a.archive_root,a.graph,a.name,a.limit,a.readback)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
