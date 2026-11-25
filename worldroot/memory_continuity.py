"""R31 additive memory and arc controls. No canon writes, no inferred choices."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from .deep_recovery import retrieve, verify_manifest, tokens, STOP, sections
from .living_world import load_canonical, project
from .literary_experience import source_registry
from .history_index import read_verified_sources
from .history_index import read_verified_sources

DOMAINS=("identity","relationship","location","knowledge","inventory","power","world","event","promise","author_rule")
def digest(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()

def fusion(db, query, entity=None, topic=None, role=None, limit=20):
    """Reciprocal rank fusion of existing independent lexical views; bounded."""
    if type(limit) is not int or not 1<=limit<=100:raise ValueError("Invalid limit")
    hits={}; scores={}
    for strategy,ent,top in (("legacy",entity,topic),("hybrid",entity,topic),
                            ("contextual",entity,topic),("contextual",None,topic),
                            ("hybrid",None,None)):
        result=retrieve(db,query,ent,top,role,limit=80,strategy=strategy)
        for rank,h in enumerate(result["hits"],1):
            key=h["id"];hits[key]=h;scores[key]=scores.get(key,0)+1/(60+rank)
    ordered=sorted(hits,key=lambda k:(-scores[k],k))
    selected=[]
    for key in ordered:
        h=hits[key]
        if any(h["source"]==x["source"] and h["role"]==x["role"] and min(h["line_end"],x["line_end"])-max(h["line_start"],x["line_start"])+1>=9 for x in selected):continue
        selected.append(h)
        if len(selected)==limit:break
    return {"hits":selected,"status":"CANDIDATES_ONLY" if selected else "NOT_RECOVERED","canon_changed":False}

def recent_candidates(entries, query, limit=8):
    terms=set(tokens(query))-STOP
    if not terms:return []
    hits=[]
    for entry in entries:
        lines=entry["text"].splitlines(keepends=True)
        for i in range(0,len(lines),12):
            anchor="".join(lines[i:i+24])
            matched=terms.intersection(tokens(anchor))
            if not matched:continue
            hits.append({"source":entry["id"],"sequence":entry["sequence"],"day":entry["day"],"source_sha":entry["sha256"],"line_start":i+1,"line_end":min(i+24,len(lines)),"anchor":anchor,"anchor_sha":digest(anchor),"matched":len(matched)})
    hits.sort(key=lambda h:(-h["matched"],-h["sequence"],h["line_start"]))
    return hits[:limit]

def creation_packet(root, db, requirements, *, head, candidate_limit=80):
    """Retrieve separately for each material memory requirement, never one query for a whole episode."""
    if type(candidate_limit) is not int or not 1<=candidate_limit<=80:raise ValueError("Invalid candidate limit")
    root=Path(root)
    if json.loads((root/"canon/HEAD.json").read_text(encoding="utf-8"))!=head:
        raise ValueError("Stale HEAD")
    verify_manifest(root,db)
    entries,warnings=load_canonical(root,head)
    if warnings:raise ValueError("Incomplete closed episode projection")
    if not isinstance(requirements,list) or not 1<=len(requirements)<=80:raise ValueError("Requirements count")
    # Existing R28/R30 projections are additional retrieval routes, not replaced.
    registry=source_registry(root,head)
    world=project(root,head)
    ids=set();items=[]
    for req in requirements:
        rid=req["id"]
        if not isinstance(rid,str) or not rid or rid in ids or req["domain"] not in DOMAINS or type(req["critical"]) is not bool:raise ValueError("Invalid memory requirement")
        ids.add(rid)
        # Author intent and observed story are not interchangeable.
        role=req.get("role","Response")
        if role not in ("Response","Prompt"):raise ValueError("Invalid role")
        result=fusion(db,req["query"],req.get("entity"),req.get("topic"),role,limit=candidate_limit)
        entity=req.get("entity")
        words=set(tokens(req["query"]))-STOP
        def relevant(record):
            names=[record.get("name",""),*record.get("aliases",[])]
            return record.get("id")==entity or any(set(tokens(n)) and set(tokens(n)).issubset(words) for n in names)
        identities=[p for p in registry["characters"] if relevant(p)]
        related=[p for p in world["assets"]+world["plots"] if relevant(p)]
        items.append({"requirement":req,"candidate_status":result["status"],"hits":result["hits"],
                      "recent_canon_candidates":recent_candidates(entries,req["query"]) if role=="Response" else [],
                      "r30_identity_candidates":identities,"r28_world_candidates":related})
    return {"head":head,"items":items,"closed_episodes":len(entries),"status":"REVIEW_REQUIRED","canon_changed":False,
            "note":"Candidate availability is not recall or proof; reconcile current state and reviewed claim."}

def coverage(requirements, reviewed, sources):
    """95% release threshold over declared requirements, with 100% critical evidence.
    reviewed semantic decisions are external; literal anchors are checked here.
    """
    if not isinstance(requirements,list) or not requirements:raise ValueError("No denominator")
    ids=[r["id"] for r in requirements]
    if len(set(ids))!=len(ids) or any(r["domain"] not in DOMAINS or type(r["critical"]) is not bool for r in requirements):raise ValueError("Invalid requirements")
    if not isinstance(reviewed,dict) or not set(reviewed)<=set(ids):raise ValueError("Unknown review IDs")
    verified=[];missing=[]
    for req in requirements:
        rid=req["id"];r=reviewed.get(rid,{})
        body=sources.get(r.get("source"))
        lo,hi=r.get("line_start"),r.get("line_end")
        ok=False
        if isinstance(body,str) and type(lo) is int and type(hi) is int:
            lines=body.splitlines(keepends=True)
            if 1<=lo<=hi<=len(lines) and hi-lo<250:
                anchor="".join(lines[lo-1:hi])
                ok=(r.get("status")=="REVIEWED_SUPPORTED" and r.get("claim","").strip()!="" and r.get("anchor_sha")==digest(anchor) and bool(anchor.strip()))
        (verified if ok else missing).append(rid)
    critical=[r["id"] for r in requirements if r["critical"] and r["id"] in missing]
    rate=len(verified)/len(ids)
    return {"verified":len(verified),"required":len(ids),"coverage":rate,"missing":missing,"critical_missing":critical,
            "status":"REVIEWED_EVIDENCE_THRESHOLD_MET" if rate>=.95 and not critical else "RECOVER_BEFORE_RELEASE",
            "semantic_certification":False,"canon_changed":False}

def arc_review(packet):
    """Validate structured planning data; subjective parity still needs editorial review."""
    errors=[]
    if not isinstance(packet,dict):raise ValueError("Invalid arc packet")
    options=packet.get("options",[])
    if not isinstance(options,list) or len(options)!=4 or any(not isinstance(o,dict) for o in options):
        return {"status":"REVIEW","errors":["Exactly four authored routes required"],"canon_changed":False}
    if [o.get("number") for o in options]!=[1,2,3,4]:errors.append("Numbered routes 1–4")
    if [o.get("track") for o in options].count("main")!=1 or [o.get("track") for o in options].count("secondary")!=3:errors.append("One main and three secondary routes")
    arc_ids=[o.get("arc_id") for o in options]
    if any(not isinstance(a,str) or not a.strip() for a in arc_ids) or len(set(arc_ids))!=4:errors.append("Distinct arc identifiers")
    for o in options:
        for field in ("title","promise","reward","risk","next_link","unselected_progress"):
            if not isinstance(o.get(field),str) or not o[field].strip():errors.append(f"Option {o.get('number')}: {field} missing")
        if o.get("guaranteed_success") is not False:errors.append("No guaranteed victory")
        if o.get("combines_all") is not False:errors.append("No all-in-one dominant path")
    if packet.get("free_action") is not True:errors.append("Preserve separate author free action")
    if packet.get("author_choice_recorded") is not False:errors.append("Planning cannot record an author choice")
    return {"status":"REVIEW" if errors else "STRUCTURE_OK_EDITORIAL_PARITY_PENDING","errors":errors,
            "questions":["Would each route be desirable without its number?","Are rewards and risks comparably meaningful, not identical?",
                         "Does every route advance a real arc and leave the others alive?","Does any path dominate by combining rewards?"],
            "semantic_certification":False,"canon_changed":False}

def review_creation(root, head, requirements, reviewed):
    """Check source authority and prompt/response boundaries before counting evidence.

    A reviewer must still determine that the cited source supports the claim and
    resolves current-state conflicts. This is not independent semantic grading.
    """
    root=Path(root)
    if json.loads((root/"canon/HEAD.json").read_text(encoding="utf-8"))!=head:
        raise ValueError("Stale HEAD")
    _,historical=read_verified_sources(root)
    bodies={m["source_name"]:t for m,t in historical}
    entries,warnings=load_canonical(root,head)
    if warnings:raise ValueError("Incomplete closed episode projection")
    bodies.update({e["id"]:e["text"] for e in entries})
    roles={m["source_name"]:[(role,start,start+len(lines)-1) for role,start,lines in sections(t)] for m,t in historical}
    # Closed episodes are narrative evidence, not user prompts.
    for e in entries:roles[e["id"]]=[("Response",1,len(e["text"].splitlines()))]
    if not isinstance(reviewed,dict):raise ValueError("Invalid review mapping")
    reqmap={r["id"]:r for r in requirements}
    if not set(reviewed)<=set(reqmap):raise ValueError("Unknown review ID")
    valid={}
    for rid,r in reviewed.items():
        if not isinstance(r,dict):continue
        source=r.get("source");lo=r.get("line_start");hi=r.get("line_end")
        if type(lo) is not int or type(hi) is not int:continue
        expected=reqmap[rid].get("role","Response")
        if any(role==expected and start<=lo<=hi<=end for role,start,end in roles.get(source,[])):
            valid[rid]=r
    result=coverage(requirements,valid,bodies)
    return {**result,"head":head,"closed_episodes":len(entries),"verified_source_count":len(bodies),"role_rejected":sorted(set(reviewed)-set(valid))}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,required=True)
    sub=p.add_subparsers(dest="action",required=True)
    a=sub.add_parser("prepare");a.add_argument("--db",type=Path,required=True);a.add_argument("--requirements",type=Path,required=True);a.add_argument("--candidate-limit",type=int,default=80)
    b=sub.add_parser("review");b.add_argument("--requirements",type=Path,required=True);b.add_argument("--reviewed",type=Path,required=True)
    c=sub.add_parser("arcs");c.add_argument("--packet",type=Path,required=True)
    args=p.parse_args(argv)
    load=lambda f:json.loads(f.read_text(encoding="utf-8"))
    if args.action=="arcs":result=arc_review(load(args.packet))
    else:
        head=load(args.archive_root/"canon/HEAD.json")
        requirements=load(args.requirements)
        if args.action=="prepare":result=creation_packet(args.archive_root,args.db,requirements,head=head,candidate_limit=args.candidate_limit)
        else:result=review_creation(args.archive_root,head,requirements,load(args.reviewed))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
