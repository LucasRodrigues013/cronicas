"""Universal living Codex: additive projection, never an authority to close story.
D580 design registry is a candidate source, not narrated history.
"""
from __future__ import annotations
import hashlib,json,re,sqlite3,unicodedata,os,tempfile
from pathlib import Path

REGISTRY="editorial/registries/universal-codex-design-d580-v1.json"
SCHEMA="worldroot-codex-delta-v1"
DOMAINS=("Personagens","Bestiário","Atlas mundial","Ambientes","Arsenal","Tecnologia","Magia e poderes","Organizações","Cultura e economia","História e mistérios")
KINDS={"APPEARANCE","MOVE","ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE","USE_ITEM","LEARN","CAST","ATTRIBUTE","KNOW","RELATION","ALIAS","REPORT","PENDING_OPEN","PENDING_RESOLVE","PENDING_ESCALATE","DEMONSTRATE"}
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
    # Verify the source of each explicit historical custody baseline before use.
    # Last-known gifts without storage evidence are not included in this set.
    for state in data.get("coherence",{}).get("head_state_items",[]):
        from .git_cycle import verify_episode,load
        e=state["evidence"]
        ep=e["episode"]
        draft,manifest=verify_episode(Path(root),ep)
        closure=load(Path(root)/"canon/episodes"/(ep+".json"))
        if closure["story_sha256"]!=e["source_sha256"] or manifest["original_readback_sha256"]!=e["source_sha256"]:raise ValueError("Historical item source mismatch")
        check_anchor(draft.prose,e["line_start"],e["trecho_literal"])
        if state["day"]!=draft.metadata["day"]:raise ValueError("Historical item day mismatch")
    from .natural_codex import load_overlay
    overlay=load_overlay(root,b,data)
    if overlay is not None:
        data["_natural_overlay"]=overlay
        # Bind manifest and registry to the preparation; a changed manifest
        # invalidates earlier preparation and triggers disposable rebuild.
        return data,digest({"registry":hashlib.sha256(b).hexdigest(),"overlay":overlay["manifest_sha256"]})
    return data,hashlib.sha256(b).hexdigest()
def all_records(data):
    from .natural_codex import augment_record, extra_records
    overlay=data.get("_natural_overlay")
    profiles={p["id"]:p for p in data["characters"]}
    verified=data["arcane"].get("verified_historical_magic",[])
    historical=data.get("coherence",{}).get("items",[])
    custody={v["item_id"]:v for v in data.get("coherence",{}).get("head_state_items",[])}
    for r in data["records"]:
        extra={}
        if r["id"]=="genese":
            extra={"aliases":[*r.get("aliases",[]),"CREATION_GENESE"],"special_authority":data["arcane"]["special_authorities"][0]}
        yield augment_record({**r,"design":profiles.get(r["id"]),"research_links":[s for s in data["school_links"] if s["entity_id"]==r["id"]],"scope":"HISTORICAL_REVIEW_AND_PROSPECTIVE_DESIGN","verified_magic":[m for m in verified if m["entity_id"]==r["id"]],"historical_items":[m for m in historical if m["recipient"]==r["id"] or m["id"]==r["id"]],"last_observed_custody":custody.get(r["id"]),**extra},overlay)
    yield from extra_records(overlay)
    for s in data["species"]:
        yield {**s,"aliases":[],"scope":"SPECIES_DESIGN_NOT_OBSERVED"}
    for s in data["arcane"]["schools"]:
        yield {**s,"aliases":[],"domains":["Magia e poderes"],"scope":"TRADITION_DESIGN_NOT_OBSERVED"}
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
    CREATE TABLE IF NOT EXISTS codex_event_entities(event_id TEXT NOT NULL REFERENCES codex_events(event_id), entity_id TEXT NOT NULL REFERENCES records(id), role TEXT NOT NULL, PRIMARY KEY(event_id,entity_id,role));
    CREATE INDEX IF NOT EXISTS codex_event_entities_lookup ON codex_event_entities(entity_id,event_id);
    CREATE TABLE IF NOT EXISTS codex_state(entity_id TEXT NOT NULL REFERENCES records(id), field TEXT NOT NULL, value TEXT NOT NULL, event_id TEXT NOT NULL REFERENCES codex_events(event_id), PRIMARY KEY(entity_id,field));
    CREATE TABLE IF NOT EXISTS codex_episode(episode TEXT PRIMARY KEY, sequence INTEGER NOT NULL UNIQUE, source_sha TEXT NOT NULL, delta_sha TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS codex_pending(pending_id TEXT PRIMARY KEY, entity_id TEXT REFERENCES records(id), category TEXT NOT NULL, status TEXT NOT NULL, body TEXT NOT NULL, episode TEXT NOT NULL, source_sha TEXT NOT NULL, line INTEGER NOT NULL, anchor TEXT NOT NULL, last_event TEXT REFERENCES codex_events(event_id));
    CREATE INDEX IF NOT EXISTS codex_pending_entity ON codex_pending(entity_id,status);
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
    for n in delta["new_entities"]:
        if not isinstance(n,dict):raise ValueError("Invalid new identity object")
        key=norm(n.get("name",""))
        if not key:raise ValueError("Missing identity name")
        if not isinstance(n.get("aliases",[]),list) or any(not isinstance(a,str) or not norm(a) for a in n.get("aliases",[])):raise ValueError("Invalid aliases")
        ident=n.get("id")
        if not isinstance(ident,str) or not ID.fullmatch(ident) or ident.startswith("candidate:") or ident in ids or not isinstance(n.get("name"),str) or not n["name"].strip() or not n.get("domains") or not set(n["domains"])<=set(DOMAINS):raise ValueError("Invalid new identity")
        check_anchor(prose,n["line"],n["anchor"]);ids.add(ident)
    for e in delta["events"]:
        if not isinstance(e,dict):raise ValueError("Invalid event object")
        if e.get("kind") not in KINDS or e.get("entity_id") not in ids or type(e.get("day")) is not int or not 1<=e["day"]<=day or (e.get("clock") is not None and not re.fullmatch(r"(?:[01]\d|2[0-3])h[0-5]\d",e["clock"])):raise ValueError("Invalid typed Codex event")
        check_anchor(prose,e["line"],e["anchor"])
        k=e["kind"];v=e.get("value")
        if e.get("scope") not in ("WORLD","PRIVATE_CHARACTER","BACKSTAGE"):raise ValueError("Missing visibility")
        if e.get("location_id") is not None and e["location_id"] not in ids:raise ValueError("Unknown event location")
        if k in {"MOVE","APPEARANCE"} and (not isinstance(v,dict) or v.get("location_id") not in ids):raise ValueError("Unknown location ID")
        if k in {"LEARN","CAST"} and (not isinstance(v,dict) or v.get("spell_id") not in spell_ids):raise ValueError("Unknown spell ID")
        if k in {"ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE","USE_ITEM"} and (not isinstance(v,dict) or v.get("item_id") not in ids):raise ValueError("Unknown item instance")
        if k=="TRANSFER" and v.get("to_id") not in ids:raise ValueError("Unknown recipient")
        if k=="USE_ITEM" and (not isinstance(v.get("method"),str) or not v["method"].strip()):raise ValueError("Item use must describe method")
        if k=="STORE" and v.get("location_id") not in ids:raise ValueError("Unknown storage")
        if k=="RELATION" and (not isinstance(v,dict) or v.get("target_id") not in ids or not v.get("relation")):raise ValueError("Unknown relation target")
        if k in {"ATTRIBUTE","KNOW"} and (not isinstance(v,dict) or not v.get("field") or "value" not in v):raise ValueError("Missing typed value")
        if k=="ATTRIBUTE" and v["field"] in {"id","species","age","powers","inventory","location","knowledge","relationships"}:raise ValueError("Protected attribute: use specific event or author design")
        if k=="DEMONSTRATE" and (not isinstance(v,dict) or v.get("capability_id") not in ids or not isinstance(v.get("method"),str) or not v["method"].strip() or not isinstance(v.get("observed_effect"),str) or not v["observed_effect"].strip()):raise ValueError("Missing evidenced capability demonstration")
        if k=="ALIAS" and (not isinstance(v,dict) or not isinstance(v.get("alias"),str) or not norm(v["alias"])):raise ValueError("Invalid alias event")
        if k=="REPORT" and (not isinstance(v,dict) or not isinstance(v.get("field"),str) or not v["field"].strip() or "value" not in v or not isinstance(v.get("reporter"),str) or not v["reporter"].strip() or (v.get("about_day") is not None and (type(v["about_day"]) is not int or not 1<=v["about_day"]<=day))):raise ValueError("Invalid unverified report")
        if k.startswith("PENDING_"):
            if not isinstance(v,dict) or not isinstance(v.get("pending_id"),str) or not ID.fullmatch(v["pending_id"]):raise ValueError("Invalid pending ID")
            if k=="PENDING_OPEN" and (not isinstance(v.get("category"),str) or not v["category"].strip() or not isinstance(v.get("reason"),str) or not v["reason"].strip()):raise ValueError("Missing pending category or reason")
            if k!="PENDING_OPEN" and (not isinstance(v.get("reason"),str) or not v["reason"].strip()):raise ValueError("Missing resolution or escalation reason")
            if k=="PENDING_RESOLVE" and (not isinstance(v.get("resolved_by"),list) or not v["resolved_by"] or any(type(x) is not int or x<0 for x in v["resolved_by"])):raise ValueError("Pending resolution requires linked evidence events")
    for u in delta["unresolved"]:
        if not isinstance(u,dict) or not isinstance(u.get("name"),str) or not u["name"].strip() or not isinstance(u.get("reason"),str) or not u["reason"].strip():raise ValueError("Invalid unresolved entity")
        check_anchor(prose,u["line"],u["anchor"])
    return delta
def index_event_entities(db,event_id,event):
    """One immutable event, reverse-indexed by every typed participant."""
    links=[(event["entity_id"],"SUBJECT")]
    if event.get("location_id"):
        links.append((event["location_id"],"LOCATION"))
    value=event.get("value")
    if isinstance(value,dict):
        for field,role in (("location_id","LOCATION"),("item_id","ITEM"),("target_id","TARGET"),("to_id","RECIPIENT"),("spell_id","SPELL"),("capability_id","CAPABILITY")):
            ident=value.get(field)
            if isinstance(ident,str) and ident:
                if field=="spell_id" and ident=="CREATION_GENESE":ident="genese"
                links.append((ident,role))
    for ident,role in set(links):
        # Legacy receipts may reference a retired special alias not represented by
        # a record; never fabricate an entity to satisfy the projection.
        if db.execute("SELECT 1 FROM records WHERE id=?",(ident,)).fetchone():
            db.execute("INSERT OR IGNORE INTO codex_event_entities VALUES(?,?,?)",(event_id,ident,role))

def events_for_entity(db,ident,limit=20,public=True):
    if type(limit) is not int or not 1<=limit<=100:
        raise ValueError("Event lookup limit must be 1..100")
    # Scope filter precedes LIMIT so private rows cannot crowd out visible history.
    rows=db.execute("""SELECT e.event_id,e.episode,e.day,e.clock,e.kind,e.body,e.source_sha,e.line,
      GROUP_CONCAT(x.role) FROM codex_event_entities x JOIN codex_events e ON e.event_id=x.event_id
      WHERE x.entity_id=? GROUP BY e.event_id ORDER BY e.sequence DESC,e.ordinal DESC""",(ident,))
    result=[]
    for eid,episode,day,clock,kind,raw,sha,line,roles in rows:
        event=json.loads(raw)
        if public and event.get("scope")!="WORLD":continue
        result.append({"event_id":eid,"episode":episode,"day":day,"clock":clock,"kind":kind,
                       "subject":event["entity_id"],"roles":sorted(roles.split(",")),
                       "source_sha":sha,"line":line,"scope":event.get("scope")})
        if len(result)>=limit:break
    return result

def current(db,entity,field):
    row=db.execute("SELECT value FROM codex_state WHERE entity_id=? AND field=?",(entity,field)).fetchone()
    return json.loads(row[0]) if row else None
def custody_at(db,item,day,clock=None):
    v=current(db,item,"custody")
    if v is not None:return v
    row=db.execute("SELECT body FROM records WHERE id=?",(item,)).fetchone()
    base=json.loads(row[0]).get("last_observed_custody") if row else None
    if not base:return None
    if day<base["day"] or (day==base["day"] and (not clock or clock<base["clock"])):return None
    return {"holder":base["holder"],"owner":base["owner"],"location":base["location_id"],"state":base["state"],"source":base["evidence"]}
def setstate(db,entity,field,value,event_id):
    db.execute("INSERT INTO codex_state VALUES(?,?,?,?) ON CONFLICT(entity_id,field) DO UPDATE SET value=excluded.value,event_id=excluded.event_id",(entity,field,jsonstr(value),event_id))
def graph_rows(db,*,public=True):
    rows=[json.loads(row[0]) for row in db.execute("SELECT body FROM records")]
    if public:
        from .natural_codex import editorial_profile
        for r in rows:
            if isinstance(r.get("profile"),dict):
                r["natural_profile"]=editorial_profile(r.pop("profile"))
    by_id={r["id"]:r for r in rows}
    sql="SELECT entity_id,body FROM codex_events WHERE kind='ALIAS' ORDER BY sequence,ordinal"
    for ident,body in db.execute(sql):
        event=json.loads(body)
        if public and event["scope"]!="WORLD":continue
        r=by_id[ident];alias=event["value"]["alias"]
        if alias not in r.get("aliases",[]):r.setdefault("aliases",[]).append(alias)
    return rows

def check_identity_collision(rows,new):
    matches={r["id"] for name in [new["name"],*new.get("aliases",[])] for r in aliases(rows,name) if r["id"]!=new["id"]}
    if matches:
        decision=new.get("identity_resolution",{})
        if decision.get("kind")!="DISTINCT_HOMONYM" or not isinstance(decision.get("distinct_from"),list) or set(decision["distinct_from"])!=matches or not isinstance(decision.get("reason"),str) or not decision["reason"].strip():
            raise ValueError("Name/alias collision: resolve existing ID or explicitly distinguish homonym")

def save_unresolved(db,delta,source_sha):
    for i,u in enumerate(delta["unresolved"]):
        ident="candidate:"+delta["episode"]+":"+str(i)
        db.execute("INSERT OR IGNORE INTO codex_pending VALUES(?,?,?,?,?,?,?,?,?,?)",(ident,None,"IDENTITY_UNRESOLVED","OPEN",jsonstr(u),delta["episode"],source_sha,u["line"],u["anchor"],None))

def apply_delta(db,delta,prose,sequence,day,source_sha,spell_ids):
    """Only called with verified, closed episode. Immutable retry and atomic rollback."""
    episode=delta["episode"];ds=digest(delta)
    old=db.execute("SELECT sequence,source_sha,delta_sha FROM codex_episode WHERE episode=?",(episode,)).fetchone()
    if hashlib.sha256(prose.encode()).hexdigest()!=delta["prose_sha256"]:raise ValueError("Changed prose")
    if old:
        if old!=(sequence,source_sha,ds):raise ValueError("Changed closed Codex delta")
        with db:
            save_unresolved(db,delta,source_sha)
            for event_id,body in db.execute("SELECT event_id,body FROM codex_events WHERE episode=?",(episode,)):
                index_event_entities(db,event_id,json.loads(body))
        return "IDEMPOTENT"
    latest=db.execute("SELECT MAX(sequence) FROM codex_episode").fetchone()[0]
    if latest is not None and sequence<=latest:raise ValueError("Out-of-order Codex delta")
    ids={r[0] for r in db.execute("SELECT id FROM records")}
    validate_delta(delta,prose,episode,day,ids,spell_ids)
    from .world_coherence import item_access, learned_in_registry
    with db:
        rows=graph_rows(db,public=False)
        for n in delta["new_entities"]:
            check_identity_collision(rows,n)
            record={**n,"aliases":n.get("aliases",[]),"scope":"NARRATED_IDENTITY_REVIEWED"}
            db.execute("INSERT INTO records VALUES(?,?,?)",(record_type(n),n["id"],jsonstr(record)))
            rows.append(record)
        save_unresolved(db,delta,source_sha)
        for i,e in enumerate(delta["events"]):
            eid=episode+":"+str(i);subject=e["entity_id"];kind=e["kind"];v=e["value"]
            db.execute("INSERT INTO codex_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(eid,episode,sequence,i,e["day"],e.get("clock"),subject,kind,jsonstr(e),source_sha,e["line"],e["anchor"]))
            index_event_entities(db,eid,e)
            if kind in ("APPEARANCE","MOVE"):
                prior=db.execute("SELECT e.day,e.clock FROM codex_state s JOIN codex_events e ON e.event_id=s.event_id WHERE s.entity_id=? AND s.field='last_observed_location'",(subject,)).fetchone()
                if not prior or e["day"]>prior[0] or (e["day"]==prior[0] and (not prior[1] or (e.get("clock") and e["clock"]>=prior[1]))):
                    setstate(db,subject,"last_observed_location",v["location_id"],eid)
            elif kind in ("LEARN","CAST"):
                spell="genese" if v["spell_id"]=="CREATION_GENESE" else v["spell_id"]
                record=json.loads(db.execute("SELECT body FROM records WHERE id=?",(subject,)).fetchone()[0])
                if spell=="genese" and subject!="lucas":raise ValueError("GÊNESE is Lucas's singular authority")
                if kind=="LEARN" and spell!="genese" and (not isinstance(v.get("method"),str) or not v["method"].strip()):raise ValueError("Learning requires explicit acquisition method")
                if kind=="CAST" and spell!="genese" and not (current(db,subject,"learned:"+spell) or current(db,subject,"last_cast:"+spell) or learned_in_registry(record,spell)):raise ValueError("Unproven personal spell acquisition")
                setstate(db,subject,("learned:" if kind=="LEARN" else "last_cast:")+spell,{"episode":episode,"day":e["day"]},eid)
            elif kind in {"ACQUIRE","TRANSFER","STORE","EQUIP","UNEQUIP","CONSUME","LOSE"}:
                item=v["item_id"];custody=custody_at(db,item,e["day"],e.get("clock"))
                if custody and custody.get("state")=="CONSUME":raise ValueError("Consumed instance cannot reappear")
                if kind!="ACQUIRE" and not item_access(custody,subject,e.get("location_id")):raise ValueError("Item access not proven")
                if kind=="ACQUIRE" and custody and custody.get("state")=="STORE" and custody.get("location")!=e.get("location_id"):raise ValueError("Stored item must be retrieved at actual location")
                if kind=="ACQUIRE" and custody and custody.get("holder") not in (None,subject):raise ValueError("Acquisition contradicts existing holder; transfer required")
                holder=v["to_id"] if kind=="TRANSFER" else None if kind in ("STORE","CONSUME","LOSE") else subject
                location=v.get("location_id") if kind=="STORE" else None
                owner=(custody or {}).get("owner")
                if v.get("ownership_transfer") is True and kind in ("ACQUIRE","TRANSFER"):owner=v.get("to_id",subject) if kind=="TRANSFER" else subject
                setstate(db,item,"custody",{"holder":holder,"owner":owner,"location":location,"state":kind,"actor":subject},eid)
            elif kind=="USE_ITEM":
                if not item_access(custody_at(db,v["item_id"],e["day"],e.get("clock")),subject,e.get("location_id")):raise ValueError("Item access not proven")
                setstate(db,subject,"last_item_use:"+v["item_id"],{"method":v["method"],"location":e.get("location_id"),"episode":episode,"day":e["day"]},eid)
            elif kind=="ATTRIBUTE":setstate(db,subject,"attribute:"+v["field"],v["value"],eid)
            elif kind=="KNOW":setstate(db,subject,"knowledge:"+v["field"],v["value"],eid)
            elif kind=="RELATION":setstate(db,subject,"relation:"+v["target_id"]+":"+v["relation"],v.get("value"),eid)
            elif kind=="DEMONSTRATE":
                cap=v["capability_id"]
                capability=json.loads(db.execute("SELECT body FROM records WHERE id=?",(cap,)).fetchone()[0])
                if "Magia e poderes" not in capability["domains"]:raise ValueError("Capability must resolve to magic/powers domain")
                if cap=="genese" and subject!="lucas":raise ValueError("GÊNESE is Lucas's singular authority")
                setstate(db,subject,"demonstrated:"+cap,{"method":v["method"],"observed_effect":v["observed_effect"],"episode":episode,"day":e["day"]},eid)
            elif kind=="ALIAS":
                row=next(r for r in graph_rows(db,public=False) if r["id"]==subject)
                check_identity_collision(rows,{"id":subject,"name":v["alias"],"aliases":[],"identity_resolution":v.get("identity_resolution",{})})
                row.setdefault("aliases",[]).append(v["alias"])
                rows=[r if r["id"]!=subject else row for r in rows]
            elif kind=="REPORT":
                # Reports are evidence of testimony, never direct state mutations.
                if v["field"]=="life_status" and v.get("about_day") is not None and v["value"] in ("ALIVE","DEAD"):
                    for prior_id,prior_body in db.execute("SELECT event_id,body FROM codex_events WHERE entity_id=? AND kind='REPORT' AND event_id!=?",(subject,eid)):
                        prior=json.loads(prior_body);p=prior["value"]
                        if p.get("field")=="life_status" and p.get("about_day")==v["about_day"] and p.get("value") in ("ALIVE","DEAD") and p["value"]!=v["value"]:
                            pid="report:"+episode+":"+str(i)
                            body={"reason":"Incompatible unverified life-status reports","reports":[prior_id,eid],"scope":"WORLD" if prior["scope"]==e["scope"]=="WORLD" else "BACKSTAGE"}
                            db.execute("INSERT INTO codex_pending VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,subject,"CONFLICT_CHRONOLOGY","REQUIRES_AUTHOR_REVIEW",jsonstr(body),episode,source_sha,e["line"],e["anchor"],eid))
                            break
            elif kind.startswith("PENDING_"):
                pid=v["pending_id"]
                old_pending=db.execute("SELECT entity_id,status,body FROM codex_pending WHERE pending_id=?",(pid,)).fetchone()
                if kind=="PENDING_OPEN":
                    if old_pending:raise ValueError("Pending ID already exists")
                    db.execute("INSERT INTO codex_pending VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,subject,v["category"],"OPEN",jsonstr({**v,"scope":e["scope"]}),episode,source_sha,e["line"],e["anchor"],eid))
                else:
                    if not old_pending or old_pending[0] not in (None,subject) or old_pending[1]=="RESOLVED":raise ValueError("Pending is missing, resolved or belongs to another entity")
                    if kind=="PENDING_RESOLVE":
                        for j in v["resolved_by"]:
                            if j>=i:raise ValueError("Resolution evidence must precede pending event")
                            proof=delta["events"][j]
                            if proof["entity_id"]!=subject or proof["kind"] not in {"ATTRIBUTE","APPEARANCE","MOVE","ALIAS","RELATION","DEMONSTRATE","LEARN","CAST","ACQUIRE","TRANSFER","STORE","USE_ITEM"}:raise ValueError("Resolution evidence does not identify this entity and a supported fact")
                            if e["scope"]=="WORLD" and proof["scope"]!="WORLD":raise ValueError("Private evidence cannot resolve a public pending fact")
                    status="RESOLVED" if kind=="PENDING_RESOLVE" else "REQUIRES_AUTHOR_REVIEW"
                    if old_pending[1]==status:raise ValueError("Repeated escalation without progress")
                    if kind=="PENDING_RESOLVE" and old_pending[1]=="REQUIRES_AUTHOR_REVIEW":
                        # An explicit evidence event permits resolution but cannot prove the
                        # semantic truth of the claim; author-reviewed closure still governs.
                        if not v["reason"].strip():raise ValueError("Missing review disposition")
                    db.execute("UPDATE codex_pending SET status=?,entity_id=?,last_event=? WHERE pending_id=?",(status,subject,eid,pid))
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
        spells={s["id"] for s in data["arcane"]["index"]}|{"genese","CREATION_GENESE"}
        closures=sorted((load(p) for p in (root/"canon/episodes").glob("*.json")),key=lambda c:c["sequence"])
        if len(closures)!=head["sequence"]:raise ValueError("Incomplete canon journal")
        closure_ids={c["episode_id"] for c in closures}
        if any(row[0] not in closure_ids for row in db.execute("SELECT episode FROM codex_episode")):raise ValueError("Codex graph contains unclosed episode")
        verified_deltas=set()
        for c in closures:
            eid=c["episode_id"];receipt_path=root/"episodes"/eid/"review/preparation_r33.json"
            if not receipt_path.is_file():continue
            receipt=load(receipt_path);delta=receipt.get("codex_delta")
            if delta is None:continue
            draft,manifest=verify_episode(root,eid)
            if manifest["original_readback_sha256"]!=c["story_sha256"] or receipt.get("codex_delta_sha256")!=digest(delta) or receipt.get("prose_sha256")!=hashlib.sha256(draft.prose.encode()).hexdigest():raise ValueError("Codex source receipt mismatch")
            apply_delta(db,delta,draft.prose,c["sequence"],c["metadata"]["day"],c["story_sha256"],spells)
            verified_deltas.add(eid)
        if any(row[0] not in verified_deltas for row in db.execute("SELECT episode FROM codex_episode")):raise ValueError("Codex receipt missing")
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
                rows=graph_rows(db)
    names=[x["name"] for x in request.get("r34_intent",{}).get("characters",[])]
    result={"registry_sha256":sha,"head":request["head"],"focal":[{"name":n,"ids":[r["id"] for r in aliases(rows,n,domain="Personagens")]} for n in names],"status":"REVIEW_REQUIRED","coherence_required":bool(data.get("coherence"))}
    overlay=data.get("_natural_overlay")
    if overlay:
        from .natural_codex import CHAR_FIELDS,SYNC_SCHEMA
        result["natural_completion"]={"manifest_sha256":overlay["manifest_sha256"],"require_scene_sync":overlay["require_sync"],"schema":SYNC_SCHEMA,"new_character_fields":sorted(CHAR_FIELDS),"character_count":overlay["character_count"],"world_count":overlay["world_count"],"scope":"EDITORIAL_PROVISIONAL_NOT_CANON"}
    return result
def validate_submission(root,request,packet,payload):
    if packet.get("universal_codex") is None:return None
    if bind_request(root,request)!=packet["universal_codex"]:raise ValueError("Codex changed after preparation")
    data,_=load_registry(root);rows=list(all_records(data))
    graph=Path(root)/"canon/codex.sqlite"
    ids={r["id"] for r in rows}
    if graph.is_file():
        with sqlite3.connect(graph.resolve().as_uri()+"?mode=ro",uri=True) as db:
            meta=dict(db.execute("SELECT key,value FROM meta"))
            if json.loads(meta["head"])==request["head"] and meta["registry_sha"]==packet["universal_codex"]["registry_sha256"]:
                rows=graph_rows(db)
                ids.update(r["id"] for r in rows)
    spell_ids={s["id"] for s in data["arcane"]["index"]}|{"genese","CREATION_GENESE"}
    delta=payload.get("r33_review",{}).get("codex_delta")
    coherence=None
    if packet["universal_codex"].get("coherence_required"):
        from .world_coherence import validate_interactions
        review=payload.get("r33_review",{}).get("world_coherence")
        validate_delta(delta,payload["prose"],payload["delivery_id"],payload["metadata"]["day"],ids,spell_ids)
        coherence=validate_interactions(payload["prose"],review,{r["id"]:r for r in rows+delta["new_entities"]})
    else:
        validate_delta(delta,payload["prose"],payload["delivery_id"],payload["metadata"]["day"],ids,spell_ids)
    scene_sync=None
    overlay=data.get("_natural_overlay")
    if overlay and overlay["require_sync"]:
        from .natural_codex import validate_scene_sync
        scene_sync=validate_scene_sync(payload.get("r33_review",{}).get("codex_sync"),delta,payload["prose"],ids)
    # A literal mention is not necessarily a physical presence. Explicitly triage focal cast.
    covered={e["entity_id"] for e in delta["events"]}|{n["id"] for n in delta["new_entities"]}
    # Named dialogue is a candidate identity, not proof of physical location.
    # Do not silently discard unfamiliar names; require a disposition or a new entity.
    speakers=set(re.findall(r"(?m)^\s*\*\*([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 '\-’]{1,44})\s*[—–-]\*\*\s+",payload["prose"]))
    reviewed_names={norm(n["name"]) for n in delta["new_entities"]}|{norm(u["name"]) for u in delta["unresolved"]}
    for name in speakers:
        matches=aliases(rows,name,domain="Personagens")
        if not ({r["id"] for r in matches}&covered) and norm(name) not in reviewed_names:
            raise ValueError("Named speaker lacks Codex disposition: "+name)
    unresolved={norm(u["name"]) for u in delta["unresolved"]}
    for f in packet["universal_codex"]["focal"]:
        if not set(f["ids"])&covered and norm(f["name"]) not in unresolved:
            raise ValueError("Focal character lacks Codex review: "+f["name"])
    # Preflight the same mutation transaction on a disposable projection.
    with sqlite3.connect(":memory:") as test:
        initialize(test)
        seed(test,data)
        test.commit()
        if graph.is_file():
            with sqlite3.connect(graph.resolve().as_uri()+"?mode=ro",uri=True) as src:
                meta=dict(src.execute("SELECT key,value FROM meta"))
                if json.loads(meta["head"])==request["head"] and meta["registry_sha"]==packet["universal_codex"]["registry_sha256"]:src.backup(test)
        apply_delta(test,delta,payload["prose"],request["head"]["sequence"]+1,payload["metadata"]["day"],hashlib.sha256(payload["full_text"].encode()).hexdigest(),spell_ids)
    # Non-dialogue mentions are candidates for semantic review, not appearances.
    prose_norm=" "+norm(payload["prose"])+" "
    mentions=[]
    for r in rows:
        if "Personagens" in r["domains"] and any(" "+norm(n)+" " in prose_norm for n in [r["name"],*r.get("aliases",[])] if len(norm(n))>=3):
            mentions.append(r["id"])
    result={"codex_delta":delta,"codex_delta_sha256":digest(delta),"codex_registry_sha256":packet["universal_codex"]["registry_sha256"],"codex_mention_candidates":mentions,"world_coherence_result":coherence}
    if scene_sync is not None:
        raw_sync=payload["r33_review"]["codex_sync"]
        result.update({"codex_sync":raw_sync,"codex_sync_sha256":digest(raw_sync),"codex_sync_result":scene_sync})
    return result

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
                rows=graph_rows(db)
                states={}
                possessions={}
                for ident,field,v,event,event_body in db.execute("SELECT s.entity_id,s.field,s.value,s.event_id,e.body FROM codex_state s JOIN codex_events e ON e.event_id=s.event_id"):
                    if json.loads(event_body)["scope"]!="WORLD":continue
                    val=json.loads(v)
                    if not field.startswith("knowledge:"):states.setdefault(ident,{})[field]={"value":val,"event_id":event}
                    if field=="custody" and val.get("holder"):possessions.setdefault(val["holder"],[]).append({"item_id":ident,"custody":val,"event_id":event})
                pending={}
                for pid,ident,category,status,body,episode,line in db.execute("SELECT pending_id,entity_id,category,status,body,episode,line FROM codex_pending WHERE entity_id IS NOT NULL"):
                    if json.loads(body).get("scope")=="WORLD":
                        pending.setdefault(ident,[]).append({"pending_id":pid,"category":category,"status":status,"episode":episode,"line":line})
                for r in rows:
                    if pending.get(r["id"]):r["pending_review"]=pending[r["id"]]
                    history=events_for_entity(db,r["id"])
                    if history:r["recent_cross_domain_events"]=history
                    r["closed_state"]=states.get(r["id"],{})
                    if possessions.get(r["id"]):r["observed_inventory"]=possessions[r["id"]]
    exact=aliases(rows,query,entity)
    if exact or entity:
        from .r26_magic_catalog import get_spell
        for r in exact:
            if r.get("scope")=="GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE":r["definition"]=get_spell(r["id"])
        return exact
    words=set(norm(query).split())
    return [r for r in rows if set(norm(r["name"]).split()) and set(norm(r["name"]).split())<=words][:80]
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--archive-root",required=True);p.add_argument("--db");a=p.parse_args()
    print(json.dumps(sync(a.archive_root,a.db),ensure_ascii=False))
