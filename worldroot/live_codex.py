"""Universal living Codex: additive projection, never an authority to close story.
D580 design registry is a candidate source, not narrated history.
"""
from __future__ import annotations
import hashlib,json,re,sqlite3,unicodedata,os,tempfile
from pathlib import Path

REGISTRY="editorial/registries/universal-codex-design-d580-v1.json"
SCHEMA="worldroot-codex-delta-v1"
DOMAINS=("Personagens","Bestiário","Atlas mundial","Ambientes","Arsenal","Tecnologia","Magia e poderes","Organizações","Cultura e economia","História e mistérios")
KINDS={"APPEARANCE","MOVE","ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE","LEARN","CAST","ATTRIBUTE","KNOW","RELATION"}
ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$")
def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
def norm(s):
    return " ".join(re.findall(r"[^\W_]+",unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().casefold()))
def load_registry(root):
    path=Path(root)/REGISTRY
    if not path.exists():return None
    if path.is_symlink() or not path.is_file():raise ValueError("Unsafe Codex registry")
    b=path.read_bytes();data=json.loads(b)
    if data.get("schema")!="worldroot-universal-living-design-v1" or data.get("project")!="CRONICAS_DE_UM_NOVO_MUNDO" or set(data["domains"])!=set(DOMAINS):raise ValueError("Wrong Codex authority")
    if len({r["id"] for r in data["records"]})!=len(data["records"]):raise ValueError("Repeated entity ID")
    spells=data["arcane"]["index"]
    if len(spells)!=1020 or len({r["id"] for r in spells})!=1020 or len({norm(r["name"]) for r in spells})!=1020 or any(r["status"]!="R26_PROPOSTO_NAO_CANONICO" for r in spells):raise ValueError("Invalid R26 inventory")
    return data,hashlib.sha256(b).hexdigest()
def all_records(data):
    profiles={p["id"]:p for p in data["characters"]}
    for r in data["records"]:
        yield {**r,"design":profiles.get(r["id"]),"research_links":[s for s in data["school_links"] if s["entity_id"]==r["id"]],"scope":"HISTORICAL_REVIEW_AND_PROSPECTIVE_DESIGN"}
    for s in data["species"]:
        yield {**s,"aliases":[],"scope":"SPECIES_DESIGN_NOT_OBSERVED"}
    for s in data["arcane"]["special_authorities"]:
        yield {"id":s["id"],"name":s["nome"],"aliases":[],"domains":["Magia e poderes"],"scope":"SPECIAL_AUTHORITY_NOT_ORDINARY_SPELL","definition":s}
    for s in data["arcane"]["index"]:
        yield {**s,"aliases":[],"domains":["Magia e poderes"],"scope":"GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE"}
def aliases(rows,name,entity=None,domain=None):
    rows=list(rows)
    if entity is not None:
        return [r for r in rows if r["id"]==entity and (not domain or domain in r["domains"])]
    key=norm(name)
    return [r for r in rows if key and key in {norm(n) for n in [r["name"],r["id"],*r.get("aliases",[])]} and (not domain or domain in r["domains"])]
def initialize(db):
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS records(domain TEXT NOT NULL,id TEXT PRIMARY KEY,body TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS codex_events(event_id TEXT PRIMARY KEY, episode TEXT NOT NULL, sequence INTEGER NOT NULL, ordinal INTEGER NOT NULL, day INTEGER NOT NULL, clock TEXT, entity_id TEXT NOT NULL REFERENCES records(id), kind TEXT NOT NULL, body TEXT NOT NULL, source_sha TEXT NOT NULL, line INTEGER NOT NULL, anchor TEXT NOT NULL, UNIQUE(episode,ordinal));
    CREATE INDEX IF NOT EXISTS codex_events_entity ON codex_events(entity_id,sequence,ordinal);
    CREATE TABLE IF NOT EXISTS codex_state(entity_id TEXT NOT NULL REFERENCES records(id), field TEXT NOT NULL, value TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES codex_events(event_id), PRIMARY KEY(entity_id,field));
    CREATE TABLE IF NOT EXISTS codex_episode(episode TEXT PRIMARY KEY, sequence INTEGER NOT NULL UNIQUE, source_sha TEXT NOT NULL, delta_sha TEXT NOT NULL);
    """)
def jsonstr(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def record_type(r):
    return "dossiers" if "Personagens" in r["domains"] else ("plots" if "História e mistérios" in r["domains"] else "assets")
def seed(db,data):
    for r in all_records(data):
        db.execute("INSERT INTO records(domain,id,body) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body,domain=excluded.domain",(record_type(r),r["id"],jsonstr(r)))
def check_anchor(prose,line,anchor):
    if type(line) is not int or line<1 or not isinstance(anchor,str) or not anchor.strip():raise ValueError("Missing literal evidence")
    if prose.splitlines()[line-1:line-1+len(anchor.splitlines())]!=anchor.splitlines():raise ValueError("Literal evidence mismatch")
def validate_delta(delta,prose,episode,day,existing_ids,spell_ids):
    if not isinstance(delta,dict) or delta.get("schema")!=SCHEMA or delta.get("episode")!=episode:raise ValueError("Missing Codex delta")
    if delta.get("prose_sha256")!=hashlib.sha256(prose.encode()).hexdigest():raise ValueError("Codex prose hash mismatch")
    if not isinstance(delta.get("events"),list) or not isinstance(delta.get("new_entities"),list) or not isinstance(delta.get("unresolved"),list):raise ValueError("Explicit events, new entities and unresolved required")
    ids=set(existing_ids)
    names=set()
    for n in delta["new_entities"]:
        if not isinstance(n,dict):raise ValueError("Invalid new identity object")
        key=norm(n.get("name",""))
        if not key or key in names:raise ValueError("Repeated new name requires identity resolution")
        names.add(key)
        ident=n.get("id")
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident.startswith("candidate:") or ident in ids or not isinstance(n.get("name"),str) or not n["name"].strip() or not n.get("domains") or not set(n["domains"])<=set(DOMAINS):raise ValueError("Invalid new identity")
        check_anchor(prose,n["line"],n["anchor"]);ids.add(ident)
    for e in delta["events"]:
        if not isinstance(e,dict):raise ValueError("Invalid event object")
        if e.get("kind") not in KINDS or e.get("entity_id") not in ids or type(e.get("day")) is not int or not 1<=e["day"]<=day or (e.get("clock") is not None and not re.fullmatch(r"(?:[01]\d|2[0-3])h[0-5]\d",e["clock"])):raise ValueError("Invalid typed Codex event")
        check_anchor(prose,e["line"],e["anchor"])
        k=e["kind"];v=e.get("value")
        if e.get("scope") not in ("WORLD","PRIVATE_CHARACTER","BACKSTAGE"):raise ValueError("Missing visibility")
        if k in {"MOVE","APPEARANCE"} and (not isinstance(v,dict) or v.get("location_id") not in ids):raise ValueError("Unknown location ID")
        if k in {"LEARN","CAST"} and (not isinstance(v,dict) or v.get("spell_id") not in spell_ids):raise ValueError("Unknown spell ID")
        if k in {"ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE"} and (not isinstance(v,dict) or v.get("item_id") not in ids):raise ValueError("Unknown item instance")
        if k=="TRANSFER" and v.get("to_id") not in ids:raise ValueError("Unknown recipient")
        if k=="STORE" and v.get("location_id") not in ids:raise ValueError("Unknown storage")
        if k=="RELATION" and (not isinstance(v,dict) or v.get("target_id") not in ids or not v.get("relation")):raise ValueError("Unknown relation target")
        if k in {"ATTRIBUTE","KNOW"} and (not isinstance(v,dict) or not v.get("field") or "value" not in v):raise ValueError("Missing typed value")
        if k=="ATTRIBUTE" and v["field"] in {"id","species","age","powers","inventory","location","knowledge","relationships"}:raise ValueError("Protected attribute: use specific event or author design")
    for u in delta["unresolved"]:
        if not isinstance(u,dict) or not isinstance(u.get("name"),str) or not u["name"].strip() or not isinstance(u.get("reason"),str) or not u["reason"].strip():raise ValueError("Invalid unresolved entity")
        check_anchor(prose,u["line"],u["anchor"])
    return delta
def current(db,entity,field):
    row=db.execute("SELECT value FROM codex_state WHERE entity_id=? AND field=?",(entity,field)).fetchone()
    return json.loads(row[0]) if row else None
def setstate(db,entity,field,value,event_id):
    db.execute("INSERT INTO codex_state VALUES(?,?,?,?) ON CONFLICT(entity_id,field) DO UPDATE SET value=excluded.value,event_id=excluded.event_id",(entity,field,jsonstr(value),event_id))
def apply_delta(db,delta,prose,sequence,day,source_sha,spell_ids):
    """Only called with verified, closed episode. Immutable retry and atomic rollback."""
    episode=delta["episode"];ds=digest(delta)
    old=db.execute("SELECT sequence,source_sha,delta_sha FROM codex_episode WHERE episode=?",(episode,)).fetchone()
    if hashlib.sha256(prose.encode()).hexdigest()!=delta["prose_sha256"]:raise ValueError("Changed prose")
    if old:
        if old!=(sequence,source_sha,ds):raise ValueError("Changed closed Codex delta")
        return "IDEMPOTENT"
    latest=db.execute("SELECT MAX(sequence) FROM codex_episode").fetchone()[0]
    if latest is not None and sequence<=latest:raise ValueError("Out-of-order Codex delta")
    ids={r[0] for r in db.execute("SELECT id FROM records")}
    validate_delta(delta,prose,episode,day,ids,spell_ids)
    with db:
        for n in delta["new_entities"]:
            db.execute("INSERT INTO records VALUES(?,?,?)",(record_type(n),n["id"],jsonstr({**n,"aliases":n.get("aliases",[]),"scope":"NARRATED_IDENTITY_REVIEWED"})))
        for i,e in enumerate(delta["events"]):
            eid=episode+":"+str(i);subject=e["entity_id"];kind=e["kind"];v=e["value"]
            db.execute("INSERT INTO codex_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(eid,episode,sequence,i,e["day"],e.get("clock"),subject,kind,jsonstr(e),source_sha,e["line"],e["anchor"]))
            if kind in ("APPEARANCE","MOVE"):
                prior=db.execute("SELECT e.day,e.clock FROM codex_state s JOIN codex_events e ON e.event_id=s.event_id WHERE s.entity_id=? AND s.field='last_observed_location'",(subject,)).fetchone()
                if not prior or e["day"]>prior[0] or (e["day"]==prior[0] and (not prior[1] or (e.get("clock") and e["clock"]>=prior[1]))):
                    setstate(db,subject,"last_observed_location",v["location_id"],eid)
            elif kind in ("LEARN","CAST"):
                setstate(db,subject,("learned:" if kind=="LEARN" else "last_cast:")+v["spell_id"],{"episode":episode,"day":e["day"]},eid)
            elif kind in {"ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE"}:
                item=v["item_id"];custody=current(db,item,"custody")
                if custody and custody.get("holder") not in (None,subject) and kind!="ACQUIRE":raise ValueError("Custody contradiction")
                if custody and custody.get("state") in ("CONSUME","LOSE") and kind not in ("ACQUIRE",):raise ValueError("Unavailable item")
                if kind=="ACQUIRE" and custody and custody.get("holder") not in (None,subject):raise ValueError("Acquisition contradicts existing holder; transfer required")
                holder=v["to_id"] if kind=="TRANSFER" else None if kind in ("STORE","CONSUME","LOSE") else subject
                location=v.get("location_id") if kind=="STORE" else None
                setstate(db,item,"custody",{"holder":holder,"location":location,"state":kind,"actor":subject},eid)
            elif kind=="ATTRIBUTE":setstate(db,subject,"attribute:"+v["field"],v["value"],eid)
            elif kind=="KNOW":setstate(db,subject,"knowledge:"+v["field"],v["value"],eid)
            elif kind=="RELATION":setstate(db,subject,"relation:"+v["target_id"]+":"+v["relation"],v.get("value"),eid)
        db.execute("INSERT INTO codex_episode VALUES(?,?,?,?)",(episode,sequence,source_sha,ds))
    return "APPLIED"
def _sync(root,db_path=None):
    """Rebuildable single universal graph, derived only from registry and closed receipts."""
    from .git_cycle import load,verify_db,verify_episode
    root=Path(root);reg=load_registry(root)
    if reg is None:return None
    data,reg_sha=reg;head=load(root/"canon/HEAD.json");verify_db(root,head)
    path=Path(db_path or root/"canon/codex.sqlite")
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        initialize(db)
        old=db.execute("SELECT value FROM meta WHERE key='registry_sha'").fetchone()
        if old and old[0]!=reg_sha:raise ValueError("Registry changed; rebuild graph from verified sources")
        with db:
            seed(db,data);db.execute("INSERT OR REPLACE INTO meta VALUES('registry_sha',?)",(reg_sha,))
        spells={s["id"] for s in data["arcane"]["index"]+data["arcane"]["special_authorities"]}
        closures=sorted((load(p) for p in (root/"canon/episodes").glob("*.json")),key=lambda c:c["sequence"])
        for c in closures:
            eid=c["episode_id"];receipt_path=root/"episodes"/eid/"review/preparation_r33.json"
            if not receipt_path.is_file():continue
            receipt=load(receipt_path);delta=receipt.get("codex_delta")
            if delta is None:continue
            draft,manifest=verify_episode(root,eid)
            if manifest["original_readback_sha256"]!=c["story_sha256"] or receipt.get("codex_delta_sha256")!=digest(delta) or receipt.get("prose_sha256")!=hashlib.sha256(draft.prose.encode()).hexdigest():raise ValueError("Codex source receipt mismatch")
            apply_delta(db,delta,draft.prose,c["sequence"],c["metadata"]["day"],c["story_sha256"],spells)
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or db.execute("PRAGMA foreign_key_check").fetchall():raise ValueError("Codex projection corrupt")
        with db:db.execute("INSERT OR REPLACE INTO meta VALUES('head',?)",(jsonstr(head),))
        return {"head":head,"registry_sha":reg_sha,"records":db.execute("SELECT count(*) FROM records").fetchone()[0],"events":db.execute("SELECT count(*) FROM codex_events").fetchone()[0],"scope":"CANDIDATES_PLUS_CLOSED_TYPED_EVENTS"}
def sync(root,db_path=None):
    """Build or update on a disposable copy; publish graph atomically after checks."""
    root=Path(root);reg=load_registry(root)
    if reg is None:return None
    _,reg_sha=reg;path=Path(db_path or root/"canon/codex.sqlite")
    if path.is_symlink():raise ValueError("Unsafe graph path")
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=path.parent,prefix=".codex-") as tmp:
        candidate=Path(tmp)/"graph.sqlite"
        if path.is_file():
            with sqlite3.connect(path.resolve().as_uri()+"?mode=ro",uri=True) as src:
                try:old=src.execute("SELECT value FROM meta WHERE key='registry_sha'").fetchone()
                except sqlite3.DatabaseError:old=None
                if old and old[0]==reg_sha:
                    with sqlite3.connect(candidate) as dst:src.backup(dst)
        result=_sync(root,candidate)
        os.replace(candidate,path)
    return result

def bind_request(root,request):
    reg=load_registry(root)
    if reg is None:return None
    data,sha=reg;rows=list(all_records(data))
    graph=Path(root)/"canon/codex.sqlite"
    if graph.is_file():
        with sqlite3.connect(graph.resolve().as_uri()+"?mode=ro",uri=True) as db:
            old=db.execute("SELECT value FROM meta WHERE key='head'").fetchone()
            seal=db.execute("SELECT value FROM meta WHERE key='registry_sha'").fetchone()
            if old and seal and json.loads(old[0])==request["head"] and seal[0]==sha:
                rows=[json.loads(row[0]) for row in db.execute("SELECT body FROM records")]
    names=[x["name"] for x in request.get("r34_intent",{}).get("characters",[])]
    return {"registry_sha256":sha,"head":request["head"],"focal":[{"name":n,"ids":[r["id"] for r in aliases(rows,n,domain="Personagens")]} for n in names],"status":"REVIEW_REQUIRED"}
def validate_submission(root,request,packet,payload):
    if packet.get("universal_codex") is None:return None
    if bind_request(root,request)!=packet["universal_codex"]:raise ValueError("Codex changed after preparation")
    data,_=load_registry(root);rows=list(all_records(data))
    graph=Path(root)/"canon/codex.sqlite"
    ids={r["id"] for r in rows}
    if graph.is_file():
        with sqlite3.connect(graph.resolve().as_uri()+"?mode=ro",uri=True) as db:
            meta=dict(db.execute("SELECT key,value FROM meta"))
            if json.loads(meta["head"])==request["head"] and meta["registry_sha"]==packet["universal_codex"]["registry_sha256"]:ids.update(r[0] for r in db.execute("SELECT id FROM records"))
    spell_ids={s["id"] for s in data["arcane"]["index"]+data["arcane"]["special_authorities"]}
    delta=payload.get("r33_review",{}).get("codex_delta")
    validate_delta(delta,payload["prose"],payload["delivery_id"],payload["metadata"]["day"],ids,spell_ids)
    # A literal mention is not necessarily a physical presence. Explicitly triage focal cast.
    covered={e["entity_id"] for e in delta["events"]}|{n["id"] for n in delta["new_entities"]}
    unresolved={norm(u["name"]) for u in delta["unresolved"]}
    for f in packet["universal_codex"]["focal"]:
        if not set(f["ids"])&covered and norm(f["name"]) not in unresolved:
            raise ValueError("Focal character lacks Codex review: "+f["name"])
    return {"codex_delta":delta,"codex_delta_sha256":digest(delta),"codex_registry_sha256":packet["universal_codex"]["registry_sha256"]}

def graph_candidates(root,query,entity=None):
    reg=load_registry(root)
    if reg is None:return []
    data,sha=reg;rows=list(all_records(data))
    graph=Path(root)/"canon/codex.sqlite"
    if graph.is_file():
        with sqlite3.connect(graph.resolve().as_uri()+"?mode=ro",uri=True) as db:
            meta=dict(db.execute("SELECT key,value FROM meta"))
            head=json.loads((Path(root)/"canon/HEAD.json").read_text())
            if json.loads(meta["head"])==head and meta["registry_sha"]==sha:
                rows=[json.loads(row[0]) for row in db.execute("SELECT body FROM records")]
                for r in rows:
                    r["closed_state"]={field:{"value":json.loads(v),"event_id":event} for field,v,event in db.execute("SELECT field,value,event_id FROM codex_state WHERE entity_id=? AND field=?",(r["id"],)) if not field.startswith("knowledge:")}
    exact=aliases(rows,query,entity)
    if exact or entity:return exact
    words=set(norm(query).split())
    return [r for r in rows if set(norm(r["name"]).split()) and set(norm(r["name"]).split())<=words][:80]
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--archive-root",required=True);p.add_argument("--db");a=p.parse_args()
    print(json.dumps(sync(a.archive_root,a.db),ensure_ascii=False))
