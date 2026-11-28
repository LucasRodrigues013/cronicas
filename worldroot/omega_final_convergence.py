"""FC-01: source-bound global candidate lookup in the existing disposable Codex graph.
No new canonical events, permanent identity decisions, or character knowledge.
"""
import argparse,json,sqlite3,tempfile,subprocess
from pathlib import Path
from collections import Counter,defaultdict
from . import live_codex as codex, omega_global_p0 as p0, omega_global_p1a as a1
from .omega_global_p1a3 import route
from .omega_hybrid_receipt import ROOT, read
from .omega_turbo_recovery import digest,require

P0="00007832ee28d0e3f4a58095eec3cccded80b556"
P1B="e3d04ea281d96f7fe4912fb85fd42d24ca834781"
BINDING="f2301e1723f4ba352f4c75ce5d4e1c3baecf7e7e5bd4779ecdc453bc68f05d30"
def reconcile(inventory,records,prepared):
    idx=defaultdict(set)
    ids={r["id"] for r in records}
    require(len(ids)==len(records),"registry duplicate")
    for r in records:
        for label in [r["id"],r["name"],*r.get("aliases",[])]:
            key=codex.norm(label)
            if key:idx[key].add(r["id"])
    result=[];links=[];seen=set()
    for row in inventory:
        rid=row["id"]
        require(rid not in seen and row["promotion"] is False and "NO_CHARACTER_INJECTION" in row["visibility"],"inventory authority")
        seen.add(rid)
        labels=[]
        for label in sorted(set(row["entities"])):
            matches=sorted(idx.get(codex.norm(label),()))
            status="UNMATCHED" if not matches else "SINGLE_CANDIDATE" if len(matches)==1 else "AMBIGUOUS"
            labels.append({"label":label,"candidate_ids":matches,"status":status})
            for ident in matches:links.append((rid,label,ident,status))
        result.append({**row,"labels":labels,"review_route":route(row),"editorially_prepared":rid in prepared,
                       "identity_resolved":False,"current_state":False,"knowledge_injection":False,
                       "access":"EDITORIAL_ONLY","semantic_certification":False})
    require(prepared<=seen,"lost prior coverage")
    return result,sorted(links)
def graph_fingerprint(db):
    tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name") if not r[0].startswith(("fc_","sqlite_"))]
    return digest(p0.stable([[t,sorted([list(r) for r in db.execute('SELECT * FROM "'+t.replace('"','""')+'"')],key=codex.jsonstr)] for t in tables]))
def install(db,rows,links,binding,inventory_sha):
    """Derived candidate layer only, on a disposable graph; replace atomically."""
    db.execute("PRAGMA foreign_keys=ON")
    before=graph_fingerprint(db)
    with db:
        db.execute("CREATE TABLE IF NOT EXISTS fc_groups(id TEXT PRIMARY KEY, macro INTEGER NOT NULL, source TEXT NOT NULL, first_line INTEGER NOT NULL, body TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS fc_links(group_id TEXT NOT NULL REFERENCES fc_groups(id), label TEXT NOT NULL, candidate_id TEXT NOT NULL REFERENCES records(id), status TEXT NOT NULL, PRIMARY KEY(group_id,label,candidate_id))")
        db.execute("CREATE INDEX IF NOT EXISTS fc_links_candidate ON fc_links(candidate_id,group_id)")
        db.execute("CREATE INDEX IF NOT EXISTS fc_groups_source ON fc_groups(source,first_line)")
        db.execute("CREATE TABLE IF NOT EXISTS fc_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        db.execute("DELETE FROM fc_links");db.execute("DELETE FROM fc_groups");db.execute("DELETE FROM fc_meta")
        db.executemany("INSERT INTO fc_groups VALUES(?,?,?,?,?)",[(r["id"],r["macro"],r["source"],r["interval"][0],codex.jsonstr(r)) for r in rows])
        db.executemany("INSERT INTO fc_links VALUES(?,?,?,?)",links)
        db.executemany("INSERT INTO fc_meta VALUES(?,?)",[("registry_binding",binding),("inventory_sha256",inventory_sha),("access","EDITORIAL_ONLY")])
        require(graph_fingerprint(db)==before,"canonical graph changed")
        require(db.execute("PRAGMA integrity_check").fetchone()[0]=="ok" and not db.execute("PRAGMA foreign_key_check").fetchall(),"graph integrity")
    return before
def lookup(db,*,candidate_id=None,group_id=None,source=None,editorial=False,limit=20):
    """Exact candidate/locator lookup. Never expose through character state API."""
    require(editorial is True,"editorial access required")
    require(sum(x is not None for x in (candidate_id,group_id,source))==1 and type(limit) is int and 1<=limit<=100,"lookup bounds")
    if candidate_id is not None:
        sql="SELECT DISTINCT g.body,g.macro,g.first_line,g.id FROM fc_groups g JOIN fc_links l ON l.group_id=g.id WHERE l.candidate_id=? ORDER BY g.macro,g.first_line,g.id LIMIT ?";value=candidate_id
    elif group_id is not None:
        sql="SELECT body FROM fc_groups WHERE id=? LIMIT ?";value=group_id
    else:
        sql="SELECT body FROM fc_groups WHERE source=? ORDER BY macro,first_line,id LIMIT ?";value=source
    return [json.loads(r[0]) for r in db.execute(sql,(value,limit))]
def build(root,archive):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"global-p0-checkpoint-v1.json",P0)
    previous=read(root,ROOT+"global-p1-b-batch-001-sublot-001-checkpoint-v1.json",P1B)
    ev=read(root,previous["native_evidence_path"],previous["native_evidence_blob"])
    require(ev["workflow_conclusion"]=="success" and previous["global_groups_prepared"]==84 and previous["review"]["returns"]==0,"previous checkpoint")
    got={}
    def capture(rows,groups,partition):got.update(rows=rows,partition=partition)
    inv=p0.inspect(root,archive,inventory_consumer=capture)
    require(inv["status"]=="P0_INVENTORY_STRUCTURAL_PASS" and inv["inventory_sha256"]==cp["inventory"]["sha256"],"global inventory seal")
    prepared={r["id"] for r in got["rows"] if r["receipt_blob"] in a1.PARENTS.values()}
    require(len(prepared)==79 and not prepared&set(previous["completed_ids"]),"prior group coverage")
    prepared.update(previous["completed_ids"])
    reg,binding=codex.load_registry(archive)
    require(binding==BINDING and binding==previous["registry_binding"],"registry binding")
    records=list(codex.all_records(reg))
    require(len(records)==1256,"registry denominator")
    rows,links=reconcile(got["rows"],records,prepared)
    require(len(rows)==4941 and len(prepared)==84,"global denominator")
    label_counts=Counter(l["status"] for r in rows for l in r["labels"])
    unique_labels={l["label"]:l["status"] for r in rows for l in r["labels"]}
    with tempfile.TemporaryDirectory(prefix="omega-fc-") as tmp:
        path=Path(tmp)/"codex.sqlite"
        graph=codex.sync(archive,path)
        require(graph["registry_sha"]==binding and graph["head"]["day"]==579 and graph["head"]["sequence"]==50,"graph authority")
        with sqlite3.connect(path) as db:
            before=install(db,rows,links,binding,inv["inventory_sha256"])
            read_rows={r[0]:json.loads(r[1]) for r in db.execute("SELECT id,body FROM fc_groups")}
            require(read_rows=={r["id"]:r for r in rows},"full row readback")
            require(list(db.execute("SELECT group_id,label,candidate_id,status FROM fc_links ORDER BY group_id,label,candidate_id,status"))==links,"full link readback")
            require(all(lookup(db,group_id=r["id"],editorial=True)==[r] for r in rows),"locator retrieval")
            by=defaultdict(set)
            for rid,_,ident,_ in links:by[ident].add(rid)
            checked=0
            for ident,expected in by.items():
                found=lookup(db,candidate_id=ident,editorial=True,limit=100)
                require(len(found)==min(100,len(expected)) and {r["id"] for r in found}<=expected,"candidate retrieval")
                checked+=1
            require(install(db,rows,links,binding,inv["inventory_sha256"])==before and graph_fingerprint(db)==before,"idempotent graph preservation")
            require(db.execute("SELECT count(*) FROM fc_groups").fetchone()[0]==len(rows) and db.execute("SELECT count(*) FROM fc_links").fetchone()[0]==len(links),"replay counts")
    require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive changed")
    return dict(status="FC01_GLOBAL_CANDIDATE_MAP_PASS_SEMANTIC_HOLD",groups=len(rows),registry_records=len(records),graph_records=graph["records"],closed_typed_events=graph["events"],source_lines=inv["queue_lines"],sources=len({r["source"] for r in rows}),macros=inv["macros"],prior_prepared=len(prepared),remaining_deep_preparation=len(rows)-len(prepared),routes=dict(Counter(r["review_route"] for r in rows)),label_occurrences=dict(label_counts),unique_labels=dict(Counter(unique_labels.values())),groups_with_candidate=sum(any(l["candidate_ids"] for l in r["labels"]) for r in rows),groups_without_labels=sum(not r["labels"] for r in rows),candidate_links=len(links),registry_ids_with_links=checked,all_group_lookups=len(rows),candidate_lookup_checks=checked,inventory_sha256=inv["inventory_sha256"],registry_binding=binding,map_sha256=digest(p0.stable(rows)),links_sha256=digest(p0.stable(links)),canonical_graph_sha256=before,graph_unchanged=True,idempotent_replay=True,semantic_certification=False,independent_review=False,typed_historical_projection=False,live_integration=False,production_gate="HOLD",canon_changed=False,promotion=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True);a=p.parse_args()
    print(json.dumps(build(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
