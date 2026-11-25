"""R32 additive structured memory graph. Evidence and hypotheses are separate."""
from __future__ import annotations
import hashlib,json,re,sqlite3
from pathlib import Path
from .deep_recovery import norm,sections,tokens
from .history_index import read_verified_sources
from .living_world import load_canonical,project
from .literary_experience import source_registry

FIELDS=("appearance","voice","personality","relationships","location","knowledge","inventory","power","history")
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def locate(body,anchor):
    if not anchor or body.count(anchor)!=1:return None
    pos=body.index(anchor)
    return {"line_start":body[:pos].count("\n")+1,"line_end":body[:pos+len(anchor)].count("\n")+1,"anchor_sha":sha(anchor)}

def build(root,staged,db=None):
    root=Path(root)
    head=json.loads((root/"canon/HEAD.json").read_text())
    entries,warnings=load_canonical(root,head)
    if warnings:raise ValueError("Incomplete closure chain")
    _,raw=read_verified_sources(root)
    historical={m["source_name"]:(m,t) for m,t in raw}
    world=project(root,head);registry=source_registry(root,head)
    seed=json.loads((root/"editorial/registries/r28-living-world.json").read_text())
    nodes={};edges=[];observations=[];events=[];knowledge=[];rejected=[]
    def node(key,kind,name):
        if key not in nodes:nodes[key]={"id":key,"kind":kind,"name":name}
        return key
    def edge(a,b,kind,proof):
        edges.append({"source":a,"target":b,"kind":kind,"proof":proof})
    dossiers={}
    for p in seed["entities"]:
        if p["kind"]!="character":continue
        key=node("character:"+p["id"],"character",p["name"])
        dossiers[p["id"]]={"name":p["name"],"aliases":p.get("aliases",[]),"observations":[],"unknown_fields":list(FIELDS),"status":"PARTIAL"}
    for p in registry["characters"]:
        key=node("character:"+p["id"],"character",p["name"])
        d=dossiers.setdefault(p["id"],{"name":p["name"],"aliases":p.get("aliases",[]),"observations":[],"unknown_fields":list(FIELDS),"status":"PARTIAL"})
        for ob in p["observations"]:
            if not ob.get("proof"):continue
            d["observations"].append({"field":ob["field"],"claim":ob["value"],"source":ob["source"],"status":"R30_SOURCE_MATCH"})
        d["explicit_unknowns"]=p.get("unknown",[])
    # Preserve original candidate provenance: no candidate promoted to canonical fact.
    for i,c in enumerate(staged["records"]):
        meta,body=historical[c["source_name"]]
        part=next(p for p in meta["parts"] if p["path"]==c["part_path"])
        blob=(root/part["path"]).read_bytes()
        if hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()!=c["blob_sha"]:raise ValueError("Stale candidate blob")
        a,b=c["part_lines"];lines=blob.decode().split("\n")
        if "\n".join(lines[a-1:b])!=c["anchor"]:raise ValueError("Candidate mismatch")
        offset=sum((root/p["path"]).read_bytes().count(b"\n") for p in meta["parts"][:meta["parts"].index(part)])
        lo,hi=a+offset,b+offset
        roles=[role for role,start,ls in sections(body) if start<=lo<=hi<start+len(ls)]
        if roles!=[c["role"]]:raise ValueError("Candidate role mismatch")
        record={"id":"historical:"+str(i+1),"entity":c["entity"],"field":c["field"],"claim":c["claim"],"role":c["role"],"source":c["source_name"],"line_start":lo,"line_end":hi,"anchor_sha":sha(c["anchor"]),"status":"LITERAL_CANDIDATE_NOT_CANON"}
        observations.append(record)
        if c["entity"] in ("miren","seris","althea","elyan","ciran"):
            eid=c["entity"];d=dossiers.setdefault(eid,{"name":eid,"aliases":[],"observations":[],"unknown_fields":list(FIELDS),"status":"PARTIAL"})
            node("character:"+eid,"character",d["name"])
            d["observations"].append(record)
    for row in world["assets"]+world["plots"]:
        kind="asset" if "state" in row else "plot"
        key=node(kind+":"+row["id"],kind,row["name"])
        if row["evidence_status"]=="SOURCE_MATCH":
            source=row["source"];target=node("episode:"+source["episode"],"episode",source["episode"])
            edge(key,target,"SOURCE_REFERENCE",source)
    for entry in entries:
        ekey=node("episode:"+entry["id"],"episode",entry["id"])
        for e in entry["events"]:
            s=e.get("source",{});anchor=s.get("literal_anchor","")
            if s.get("sha256")!=entry["sha256"] or not anchor or anchor not in entry["text"]:
                rejected.append(e.get("event_id"));continue
            key=node("event:"+e["event_id"],"event",e["event_type"])
            events.append({**e,"episode":entry["id"]})
            edge(key,ekey,"NARRATED_IN",s)
        for k in entry["knowledge"]:
            knowledge.append(k)
            # Attribution is explicit; never infer a character knows an event from co-occurrence.
            name=k.get("person");ev=k.get("source_event")
            if not isinstance(name,str) or not isinstance(ev,str):continue
            aliases=[p for p,d in dossiers.items() if norm(name) in [norm(d["name"]),*[norm(a) for a in d["aliases"]]]]
            key="character:"+aliases[0] if len(aliases)==1 else node("person_literal:"+name,"unresolved_person",name)
            edge(key,"event:"+ev,"EXPLICIT_KNOWLEDGE",{"acquired_day":k.get("acquired_day"),"clock":k.get("clock"),"visibility":k.get("visibility")})
    dangling=[e for e in edges if e["source"] not in nodes or e["target"] not in nodes]
    edges=[e for e in edges if e not in dangling]
    if db is not None:enrich_dossiers(dossiers,db)
    for d in dossiers.values():
        known=set()
        for o in d["observations"]:
            if o.get("status")!="R30_SOURCE_MATCH":continue
            f=o["field"]
            if "appearance" in f:known.add("appearance")
            if "voice" in f:known.add("voice")
            if "relationship" in f:known.add("relationships")
            if "behavior" in f or "values" in f:known.add("personality")
        d["unknown_fields"]=[f for f in FIELDS if f not in known]
    # Event candidates remain ledger inputs, not computed quantities or asserted current ownership.
    inventory=[e for e in events if re.search(r"mochila|inventário|armadura|equipamento|armazen|transfer|consum|perdeu",e.get("summary_candidato",""),re.I)]
    power=[e for e in events if re.search(r"gênese|creation|autoridade|limiar|ruptura soberana",e.get("summary_candidato",""),re.I)]
    for o in observations:
        k=node(o["id"],"historical_candidate",o["field"])
        person="character:"+o["entity"]
        if person in nodes:edge(person,k,"HISTORICAL_REFERENCE_CANDIDATE",{"source":o["source"],"line_start":o["line_start"],"line_end":o["line_end"],"role":o["role"],"anchor_sha":o["anchor_sha"]})
    # Typed history, without computing a current capacity or quantity from old benchmarks.
    def select(entity,field,fragment):
        return next((o for o in observations if o["entity"]==entity and o["field"]==field and fragment in o["claim"]),None)
    power_history=[]
    for day,metric,value,unit,fragment in [(137,"steady_flow",14,"relative_to_prior","14x"),(137,"accessible_reserve",5.4,"relative_to_prior","5,4x"),(210,"comparable_material_capacity",100,"relative_to_initial","D210"),(388,"comparable_operating_capacity",300,"relative_to_initial","D388"),(388,"accessible_dimensional_capacity",100,"relative_to_initial","D388")]:
        proof=select("genese","power",fragment)
        if proof:power_history.append({"day":day,"metric":metric,"value":value,"unit":unit,"proof":proof["id"],"status":"HISTORICAL_CANDIDATE_NOT_CURRENT_CAP"})
    plan=json.loads((root/"planning/book-vi/r29-epic-narrative.json").read_text())
    return {"schema":"worldroot-r32-graph-v1","head":head,"nodes":list(nodes.values()),"edges":edges,"dossiers":dossiers,"historical_observations":observations,"events":events,"knowledge":knowledge,"inventory":{"historical":[o for o in observations if o["field"]=="inventory"],"events":inventory,"current_quantities":"UNKNOWN_UNTIL_RECONCILED"},"power":{"historical":[o for o in observations if o["field"]=="power"],"events":power,"current_ceiling":"NOT_INFERRED","benchmarks":power_history},"relationships":[o for o in observations if o["field"]=="relationship"],"plots":world["plots"],"assets":world["assets"],"planning":{"status":"DIRECTION_NOT_CANON","arcs":plan["arcs"],"seeds":plan["seeds"],"promises":plan["promises"]},"rejected_events":rejected,"unresolved_edges":len(dangling),"canon_changed":False,"semantic_certification":False}

def enrich_dossiers(dossiers,db):
    """Exact-name candidate retrieval per field, never assigns nearby features."""
    with sqlite3.connect(Path(db).resolve().as_uri()+"?mode=ro",uri=True) as c:
        c.row_factory=sqlite3.Row
        for d in dossiers.values():
            aliases=[d["name"],*d["aliases"]]
            terms=[tokens(a) for a in aliases if isinstance(a,str) and a.strip()]
            expr="anchor : ("+" OR ".join('"'+(" ".join(t))+'"' for t in terms if t)+")"
            d["candidate_evidence"]={}
            if not terms:continue
            for field,topic in (("appearance","appearance"),("voice","voice"),("relationships","relationship"),("history","event"),("inventory","inventory"),("power","power")):
                rows=c.execute("SELECT e.source,e.role,e.line_start,e.line_end,e.anchor_sha,e.anchor FROM search JOIN evidence e ON e.id=search.rowid WHERE search MATCH ? AND e.role='Response' AND (' '||e.topics||' ') LIKE ? ORDER BY bm25(search),e.id LIMIT 6",(expr,"% "+topic+" %")).fetchall()
                d["candidate_evidence"][field]=[dict(r) for r in rows]
    return dossiers

def write_graph(data,path):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    # Standalone derived database; callers must use a location outside the archive.
    with sqlite3.connect(path) as c:
        c.executescript("CREATE TABLE nodes(id TEXT PRIMARY KEY,kind TEXT,name TEXT);CREATE TABLE edges(source TEXT REFERENCES nodes(id),target TEXT REFERENCES nodes(id),kind TEXT,proof TEXT);CREATE TABLE records(domain TEXT,id TEXT,body TEXT,PRIMARY KEY(domain,id));CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);")
        c.execute("PRAGMA foreign_keys=ON")
        c.executemany("INSERT INTO nodes VALUES(:id,:kind,:name)",data["nodes"])
        c.executemany("INSERT INTO edges VALUES(?,?,?,?)",[(e["source"],e["target"],e["kind"],json.dumps(e["proof"],ensure_ascii=False)) for e in data["edges"]])
        for domain in ("dossiers","inventory","power","relationships","plots","assets","historical_observations","events","knowledge","planning"):
            obj=data[domain]
            items=obj.items() if isinstance(obj,dict) else enumerate(obj)
            c.executemany("INSERT INTO records VALUES(?,?,?)",[(domain,str(k),json.dumps(v,ensure_ascii=False)) for k,v in items])
        c.execute("INSERT INTO meta VALUES('head',?)",(json.dumps(data["head"],sort_keys=True),))
        assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert not c.execute("PRAGMA foreign_key_check").fetchall()
    return path
