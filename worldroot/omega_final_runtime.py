"""FC-02: source locator bridge for existing scene preparation and temporal graph.
Editorial-only, pinned D579 experimental projection; no typed fact synthesis.
"""
import argparse,json,sqlite3,tempfile,subprocess
from pathlib import Path
from collections import defaultdict,Counter
from . import live_codex as codex, omega_global_p0 as p0, omega_global_p1a as a1
from . import omega_final_convergence as fc, git_cycle as g
from .omega_hybrid_receipt import ROOT,ARCHIVE,read
from .omega_turbo_recovery import SourceCache,anchor,digest,git_blob,require

CP="4ccd39bc6dc0ca7f5bf2e6884b1d3a16b3c18474"
VISIBLE="EDITORIAL_ONLY_NO_CHARACTER_INJECTION"
AUTH="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED"
def eligible(r):
    return r["role"]=="Response" and r["authority"]==AUTH and r["visibility"]==VISIBLE
class Sources:
    def __init__(self,archive):
        self.archive=Path(archive).resolve()
        self.cache=SourceCache(self.archive,read(self.archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
        self.episodes={}
    def get(self,name):
        if name in self.cache.sources:return self.cache.get(name)
        if name not in self.episodes:
            d,m=g.verify_episode(self.archive,name)
            lines=tuple(d.prose.splitlines());p=self.archive/"episodes"/name/"draft"/"episode_draft.json"
            self.episodes[name]=((lines,("Response",)*len(lines),((1,len(lines),git_blob(p.read_bytes())),),digest(d.prose)),m["original_readback_sha256"])
        return self.episodes[name][0]
    def story_sha(self,name):
        self.get(name)
        return self.episodes[name][1]
def verified_group(row,sources):
    src=sources.get(row["source"]);lo,hi=row["interval"]
    require(src[3]==row["source_sha256"] and anchor(src,lo,hi)==row["anchor"],"group literal changed")
    require(all(x==row["role"] for x in src[1][lo-1:hi]),"group role changed")
    require(sorted({b for a,z,b in src[2] if a<=hi and z>=lo})==row["physical_blobs"],"group physical changed")
    return src
def source_window(db,sources,group_id,*,editorial=False,offset=0,limit=40):
    require(editorial is True and type(offset) is int and offset>=0 and type(limit) is int and 1<=limit<=80,"bounded editorial access required")
    require(dict(db.execute("SELECT key,value FROM fc_meta")).get("archive_pin")==ARCHIVE,"source window pin")
    rows=fc.lookup(db,group_id=group_id,editorial=True)
    require(len(rows)==1 and eligible(rows[0]),"restricted or non-event group")
    r=rows[0];src=verified_group(r,sources);a,z=r["interval"];lo=a+offset;hi=min(z,lo+limit-1)
    require(lo<=z,"window offset")
    return {"group_id":group_id,"source":r["source"],"source_sha256":src[3],"group_anchor":r["anchor"],"interval":[lo,hi],"window_sha256":anchor(src,lo,hi),"lines":list(src[0][lo-1:hi]),"next_offset":hi-a+1 if hi<z else None,"authority":r["authority"],"visibility":r["visibility"],"current_state":False,"knowledge_injection":False}
def attach_temporal(db,rows,sources):
    """Exact provenance association only; never create or change canonical events."""
    by=defaultdict(list)
    for r in rows:
        if r["macro"]>=67:by[r["source"]].append(r)
    links=[];events=0;unlinked=0;visibility=Counter()
    for eid,ep,sha,line,literal,vis in db.execute("SELECT event_id,episode,source_sha,line,anchor,visibility FROM r36_canon_event ORDER BY event_id"):
        src=sources.get(ep)
        require(sources.story_sha(ep)==sha and 1<=line<=len(src[0]) and literal in src[0][line-1],"closed event literal provenance")
        matches=[r for r in by[ep] if r["interval"][0]<=line<=r["interval"][1]]
        for r in matches:
            verified_group(r,sources)
            links.append((eid,r["id"]))
        events+=1;unlinked+=not matches;visibility[vis]+=1
    with db:
        db.execute("CREATE TABLE IF NOT EXISTS fc_event_links(event_id TEXT NOT NULL REFERENCES r36_canon_event(event_id),group_id TEXT NOT NULL REFERENCES fc_groups(id),PRIMARY KEY(event_id,group_id))")
        db.execute("DELETE FROM fc_event_links")
        db.executemany("INSERT INTO fc_event_links VALUES(?,?)",links)
        db.execute("INSERT OR REPLACE INTO fc_meta VALUES('archive_pin',?)",(ARCHIVE,))
        require(not db.execute("PRAGMA foreign_key_check").fetchall(),"event link integrity")
    return {"events":events,"unlinked":unlinked,"links":len(links),"visibility":dict(visibility),"links_sha256":digest(p0.stable(links))}
def preparation_locators(db,head,ids,limit=6):
    """No literal, summary, character knowledge or candidate value enters scene context."""
    require(type(limit) is int and 1<=limit<=12,"locator limit")
    tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"fc_meta","fc_groups","fc_links","fc_event_links"}<=tables:return None
    meta=dict(db.execute("SELECT key,value FROM meta"));fm=dict(db.execute("SELECT key,value FROM fc_meta"))
    if json.loads(meta.get("head","null"))!=head or head.get("day")!=579 or head.get("sequence")!=50 or meta.get("registry_sha")!=fc.BINDING or fm.get("registry_binding")!=fc.BINDING or fm.get("archive_pin")!=ARCHIVE or fm.get("access")!="EDITORIAL_ONLY":return None
    out=[];seen=set()
    for ident in dict.fromkeys(ids):
        if not db.execute("SELECT 1 FROM records WHERE id=?",(ident,)).fetchone():continue
        # Round-robin per focal entity is handled by per-entity bounded lists.
        items=[]
        for body, in db.execute("SELECT DISTINCT g.body FROM fc_groups g JOIN fc_links l ON l.group_id=g.id WHERE l.candidate_id=? ORDER BY g.macro DESC,g.first_line DESC,g.id",(ident,)):
            r=json.loads(body)
            if not eligible(r):continue
            public=[x[0] for x in db.execute("SELECT e.event_id FROM fc_event_links l JOIN r36_canon_event e ON e.event_id=l.event_id WHERE l.group_id=? AND e.visibility='PUBLICO' ORDER BY e.event_id",(r["id"],))]
            items.append({"group_id":r["id"],"source":r["source"],"interval":r["interval"],"anchor":r["anchor"],"source_sha256":r["source_sha256"],"public_event_anchor_links":public,"identity_status":"CANDIDATE_ONLY","authority":r["authority"],"knowledge_injection":False})
            if len(items)==limit:break
        if items:out.append({"candidate_id":ident,"locators":items})
    return {"status":"EDITORIAL_LOCATORS_NOT_CHARACTER_KNOWLEDGE","source_order_not_event_time":True,"semantic_certification":False,"per_entity_limit":limit,"candidates":out}
def build(root,archive):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"fc01-checkpoint-v1.json",CP);ev=read(root,cp["evidence_path"],cp["evidence_blob"])
    require(ev["workflow_conclusion"]=="success" and ev["aggregate"]==cp["metrics"],"FC01 evidence")
    got={}
    def capture(rows,groups,partition):got["rows"]=rows
    inv=p0.inspect(root,archive,inventory_consumer=capture)
    require(inv["inventory_sha256"]==cp["metrics"]["inventory_sha256"],"inventory pin")
    prior=read(root,ROOT+"global-p1-b-batch-001-sublot-001-checkpoint-v1.json",fc.P1B)
    prepared={r["id"] for r in got["rows"] if r["receipt_blob"] in a1.PARENTS.values()}|set(prior["completed_ids"])
    data,binding=codex.load_registry(archive);records=list(codex.all_records(data));rows,links=fc.reconcile(got["rows"],records,prepared)
    require(binding==fc.BINDING and digest(p0.stable(rows))==cp["metrics"]["map_sha256"] and digest(p0.stable(links))==cp["metrics"]["links_sha256"],"FC01 map changed")
    sources=Sources(archive);verified=0
    for r in rows:verified_group(r,sources);verified+=1
    with tempfile.TemporaryDirectory(prefix="omega-fc02-") as tmp:
        path=Path(tmp)/"codex.sqlite";graph=codex.sync(archive,path)
        head=graph["head"];require(head["day"]==579 and head["sequence"]==50,"head pin")
        with sqlite3.connect(path) as db:
            before=fc.install(db,rows,links,binding,inv["inventory_sha256"])
            require(before==cp["metrics"]["canonical_graph_sha256"],"original graph changed")
            event=attach_temporal(db,rows,sources)
            require(event["events"]==inv["original_closed_events"],"closed event denominator")
            require(fc.graph_fingerprint(db)==before,"canonical graph changed")
            # Verify real journal knowledge through existing canonical projection, not a new graph or fabricated typed delta.
            g.verify_db(archive,head)
            with sqlite3.connect((archive/"canon/state.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as state:
                kn=state.execute("SELECT count(*) FROM npc_knowledge").fetchone()[0]
            require(kn==inv["original_closed_knowledge"],"knowledge denominator")
            eligible_rows=[r for r in rows if eligible(r)]
            windows=0
            for r in eligible_rows:
                w=source_window(db,sources,r["id"],editorial=True)
                require(w["window_sha256"]==digest("\n".join(w["lines"])),"window readback")
                windows+=1
            for r in rows:
                if eligible(r):continue
                try:source_window(db,sources,r["id"],editorial=True)
                except ValueError:pass
                else:raise ValueError("restricted source exposed")
            # Invoke actual scene preparation function, not a separate mock generator.
            from .scene_context import build as scene_build
            eligible_groups={r["id"] for r in eligible_rows}
            eligible_ids=sorted({i for rid,_,i,_ in links if rid in eligible_groups})
            sample=eligible_ids[:24]
            request={"head":head,"scene_plan":[{"scene":i+1,"purpose":"FC02 editorial retrieval probe"} for i in range(len(sample))],"world_scope":[{"scene":i+1,"ids":[ident]} for i,ident in enumerate(sample)]}
            packet=scene_build(request,records,data.get("_natural_overlay"),db)
            locators=[l for s in packet["scenes"] for c in s["historical_editorial_recovery"]["candidates"] for l in c["locators"]]
            require(len(locators)>0 and all("lines" not in l and not l["knowledge_injection"] for l in locators),"scene locator leakage")
            require(all(eligible(next(r for r in rows if r["id"]==l["group_id"])) for l in locators),"scene restricted locator")
            require(attach_temporal(db,rows,sources)==event and fc.graph_fingerprint(db)==before,"temporal replay")
    require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive changed")
    return dict(status="FC02_SOURCE_AND_PREPARATION_BRIDGE_PASS_SEMANTIC_HOLD",groups_verified=verified,source_windows_checked=windows,restricted_or_non_event_windows_denied=len(rows)-windows,closed_events=event,closed_knowledge_verified=kn,typed_events=graph["events"],preparation_scenes=len(sample),preparation_locators=len(locators),registry_binding=binding,canonical_graph_sha256=before,graph_unchanged=True,live_integration=False,semantic_certification=False,independent_review=False,production_gate="HOLD",promotion=False,canon_changed=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True);a=p.parse_args()
    print(json.dumps(build(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
