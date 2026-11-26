"""Bounded, deterministic scene streaming for the existing Codex.
Selection is a candidate retrieval, not semantic proof or simulation of events.
"""
from __future__ import annotations
import json,re
from .live_codex import norm,events_for_entity

SCHEMA="worldroot-r35-scene-context-v1"
MAX_RECORDS=24
MAX_EVENTS=4
PROFILE_FIELDS=("identity","species","origin","occupation","voice","body","appearance","relationships","goals","values","condition","location","equipment","inventory","magic_repertoire")
def index(rows):
    by_id={r["id"]:r for r in rows}
    aliases={}
    for r in rows:
        # Do not flood scene scope with every proposed spell or species definition.
        if r.get("scope") in ("GRIMOIRE_PROPOSAL_NOT_PERSONAL_REPERTOIRE","TRADITION_DESIGN_NOT_OBSERVED","SPECIES_DESIGN_NOT_OBSERVED"):continue
        for a in [r["name"],*r.get("aliases",[])]:
            key=norm(a)
            if len(key)>=3:aliases.setdefault(key,set()).add(r["id"])
    return by_id,aliases
def candidates(text,aliases):
    words=" "+norm(text)+" ";found=[];spans=[]
    for key,ids in sorted(aliases.items(),key=lambda x:(-len(x[0]),x[0])):
        m=re.search(r"(?<!\w)"+re.escape(key)+r"(?!\w)",words)
        if not m or any(m.start()>=a and m.end()<=b for a,b in spans):continue
        spans.append(m.span());found.append((key,sorted(ids)))
    return found
def compact(r,db=None):
    out={"id":r["id"],"name":r["name"],"domains":r["domains"],"scope":r.get("scope","UNKNOWN")}
    fields=r.get("natural_profile",{}).get("fields",{})
    out["profile"]={k:{"value":fields[k]["value"],"status":fields[k]["status"]} for k in PROFILE_FIELDS if k in fields and fields[k].get("status") not in ("SEGREDO","PENDENTE_FONTE") and fields[k].get("scope") not in ("AUTHOR_ONLY","BACKSTAGE","PRIVATE_CHARACTER","PRIVATE_BOUNDARY")}
    if db is not None:
        ident=r["id"];out["recent_events"]=events_for_entity(db,ident,limit=MAX_EVENTS)
        state={}
        for field,value,event_id,raw in db.execute("SELECT s.field,s.value,s.event_id,e.body FROM codex_state s JOIN codex_events e ON e.event_id=s.event_id WHERE s.entity_id=?",(ident,)):
            if not field.startswith("knowledge:") and json.loads(raw).get("scope")=="WORLD":state[field]={"value":json.loads(value),"event_id":event_id}
        out["closed_state"]=state
    return out
def build(request,rows,overlay=None,db=None):
    by_id,aliases=index(rows);result=[];explicit=request.get("world_scope",[])
    if not isinstance(explicit,list):raise ValueError("Invalid world scope")
    explicit_by={}
    valid_scenes={s["scene"] for s in request.get("scene_plan",[])}
    for s in explicit:
        if s.get("scene") not in valid_scenes or s["scene"] in explicit_by or not isinstance(s.get("ids"),list) or any(i not in by_id for i in s["ids"]):raise ValueError("Invalid explicit scene entity")
        explicit_by[s["scene"]]=s["ids"]
    for scene in request.get("scene_plan",[]):
        number=scene["scene"];direct=list(dict.fromkeys(explicit_by.get(number,[])));ambiguous=[]
        for key,ids in candidates(scene.get("purpose",""),aliases):
            if len(ids)==1:
                if ids[0] not in direct:direct.append(ids[0])
            elif not set(ids).intersection(direct):ambiguous.append({"mention":key,"ids":ids})
        for f in request.get("r34_intent",{}).get("characters",[]):
            if number not in f.get("scenes",[]):continue
            ids=aliases.get(norm(f["name"]),set())
            if len(ids)==1:
                for ident in ids:
                    if ident not in direct:direct.append(ident)
            elif not set(ids).intersection(direct):ambiguous.append({"mention":f["name"],"ids":sorted(ids)})
        if len(direct)>MAX_RECORDS:raise ValueError("Split scene scope; too many explicit/focal records")
        links=[]
        for link in (overlay or {}).get("links",[]):
            if link.get("status")=="SEGREDO" or link.get("scope") in ("AUTHOR_ONLY","PRIVATE_CHARACTER","PRIVATE_BOUNDARY","BACKSTAGE"):continue
            if link.get("from") in direct or link.get("to") in direct:
                other=link["to"] if link["from"] in direct else link["from"]
                if other in by_id:links.append((other,link.get("relation")))
        neighbor=[]
        for ident,_ in sorted(set(links),key=lambda v:(v[0],str(v[1]))):
            if ident not in direct and ident not in neighbor:neighbor.append(ident)
        selected=direct+neighbor[:MAX_RECORDS-len(direct)]
        result.append({"scene":number,"direct_ids":direct,"records":[compact(by_id[i],db) for i in selected],"ambiguities":ambiguous,"deferred_link_count":max(0,len(direct)+len(neighbor)-MAX_RECORDS),"needs_targeted_recovery":not direct or bool(ambiguous),"source_status":"CLOSED_GRAPH_AND_EDITORIAL_CANDIDATES" if db is not None else "EDITORIAL_REGISTRY_ONLY_GRAPH_NOT_READY"})
    return {"schema":SCHEMA,"scenes":result,"max_records_per_scene":MAX_RECORDS,"max_events_per_record":MAX_EVENTS,"policy":"FOCAL_SCENE_ONLY; EXPLICIT_IDS_FIRST; PRIVATE_KNOWLEDGE_EXCLUDED; ESCALATE_MISSING_FACTS","semantic_certification":False}
def pending_fronts(db,day,limit=12):
    """Advisory opportunities, never silently create or advance fictional events."""
    if db is None:return {"status":"GRAPH_NOT_READY","fronts":[]}
    rows=[]
    for pid,ident,category,status,raw,event in db.execute("SELECT pending_id,entity_id,category,status,body,last_event FROM codex_pending WHERE status IN ('OPEN','ESCALATED') ORDER BY pending_id"):
        data=json.loads(raw)
        if data.get("scope")!="WORLD" or not ident:continue
        v=data.get("value",data)
        due=v.get("due_day")
        if type(due) is not int or due>day:continue
        rows.append({"id":pid,"entity_id":ident,"category":category,"status":status,"due_day":due,"event_id":event})
    rows.sort(key=lambda r:(r["due_day"],r["id"]))
    return {"status":"DUE_CANDIDATES_ONLY","fronts":rows[:limit],"deferred":max(0,len(rows)-limit)}
