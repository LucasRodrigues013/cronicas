"""P1-A3: explicit child overlay and bounded future work routing, read-only."""
import argparse,json
from pathlib import Path
from collections import Counter,defaultdict
from . import omega_global_p1a as a1, omega_global_p1a2 as a2, omega_global_p0 as p0, semantic_queue as queue, r36_chat_review as chat
from .omega_hybrid_receipt import ROOT, read
from .omega_turbo_recovery import SourceCache,anchor,digest,require
CP="18a2886d8eb45ef65989218816bf8f40439595fc"
EV="df0b4d1fee39f4725ddcf23dcfe25253ec16ab36"
CHILD="6e567b0750e4eec1ef7075202238b6f13be4cdda"
EXTRA="ae42c0cf4d1b581aedb0807114871f294ab353a7"
# Historical axis hints are deliberately conservative. They route work, not verdicts.
CRITICAL_AXES={1,2,4,5,6,9,11,12,13,14,16,19,23,24,25,26,27,28}
CONDITIONAL={"heavy_cavalry_uncertain","siege_uncertain","magic_formation_threat","organization_conditional","weapons_conditional","logistics_conditional","conquest_capacity_conditional","retreat_if_danger_order","mortality_uncertain","river_crossing_possibility","rider_reinforcement_risk","orc_regroup_risk"}
def boundary(c,p):
    require(c["parent_id"]==p["id"] and c["source"]==p["source"] and c["source_sha256"]==p["source_sha256"] and c["authority"]==p["authority"] and c["source_role"]==p["source_role"],"parent custody")
    require(c["visibility"]==p["visibility"] and c["modality"]==p["modality"] and c["scope"]==p["scope"],"scope escalation")
    require(p["interval"][0]<=c["interval"][0]<=c["interval"][1]<=p["interval"][1],"child interval")
    require(c["current_state"] is False and c["knowledge_injection"] is False and c["promotion"] is False and c["independent_review"] is False and c["identity_resolved"] is False,"historical projection boundary")
    require(c["state_before"] is None and c["state_after"] is None,"child cannot assert new transition")
    require((c["value"] is None)==bool(c["unknown_reason"]),"absence vs zero")
    require(c["predicate"]!="biological_age" or p.get("original_field")=="biological_age","apparent age not biological")
    require(c["subject"]==p["subject"] or (p["original_field"]=="humor_reaction" and c["predicate"]=="varo_laughter" and c["subject"]=="varo"),"subject change")
    require(c["day"]==p["day"] and c["preliminary_verdict"] in ("SUPPORTED","PARTIAL","UNKNOWN","AUTHOR_REQUIRED","CONTRADICTED"),"time or verdict")
    require(c["modality"]=="NARRATED" or c["claim_kind"]!="OBSERVED_EVENT","non-narrated event conversion")
    if c["source_role"]=="Prompt":require(c["modality"]=="META","prompt event")
    if c["value"] is None:require(c["preliminary_verdict"]=="UNKNOWN","unknown asserted")
    return c
def uniqueness(rows,existing=()):
    ids=[x["id"] for x in rows];nums=[x["target_id"] for x in rows]
    require(len(set(ids))==len(ids) and len(set(nums))==len(nums) and not set(nums)&set(existing),"duplicate child ID")
    require(len({(x["parent_id"],x["predicate"],x["subject"],tuple(x["interval"])) for x in rows})==len(rows),"duplicate child semantic locator")
def route(row):
    if row["visibility"].startswith("READER_ONLY") or row["disposition"]=="PENDING_ATOMIC_SCOPE_SPLIT":return "CRITICAL_SCOPE"
    if row["role"]=="Metadata" or row["authority"]=="METADATA_NOT_EVENT":return "STRUCTURAL_METADATA"
    if row["role"]=="Prompt" or row["authority"]!="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED":return "AUTHORITY_NON_EVENT_REVIEW"
    if set(row["axes"])&CRITICAL_AXES:return "DEEP_SEMANTIC_REVIEW"
    return "STANDARD_SEMANTIC_REVIEW"
def expansion(inventory,completed,max_records=100,max_lines=20000):
    require(0<max_records<=150 and max_lines>0,"batch limits")
    remaining=[r for r in inventory if r["id"] not in completed]
    require(len({r["id"] for r in remaining})==len(remaining),"duplicate inventory")
    chunks=[];current=[];weight=0
    def emit():
        nonlocal current,weight
        if current:
            chunks.append(dict(batch=len(chunks)+1,macro=current[0]["macro"],count=len(current),source=current[0]["source"],first_line=min(x["interval"][0] for x in current),last_line=max(x["interval"][1] for x in current),anchor_line_weight=weight,routes=dict(Counter(route(x) for x in current)),oversize_single=weight>max_lines,ids_sha256=digest(p0.stable([x["id"] for x in current])),disposition="PENDING_EDITORIAL_AND_SEMANTIC_REVIEW"))
        current=[];weight=0
    for r in remaining:
        w=r["interval"][1]-r["interval"][0]+1
        if current and (current[0]["macro"]!=r["macro"] or len(current)>=max_records or weight+w>max_lines):emit()
        current.append(r);weight+=w
    emit()
    require(sum(x["count"] for x in chunks)==len(remaining),"lost remaining record")
    return chunks,dict(Counter(route(x) for x in remaining))
def build(root,archive,consumer=None):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"global-p1-a2-checkpoint-v1.json",CP);ev=read(root,cp["native_evidence_path"],EV)
    first=read(root,ROOT+"global-p1-a3-child-overlay-v1.json",CHILD)
    extra=read(root,ROOT+"global-p1-a3-additional-split-v1.json",EXTRA)
    got={}
    def capture(claims,adjudicated,new,packets):got.update(claims=claims,gaps=adjudicated,new=new,packets=packets)
    prior=a2.apply(root,archive,consumer=capture)
    require(prior==ev["aggregate"] and prior["claims_sha256"]==cp["scope"]["claims_sha256"]==first["parent_claims_sha256"] and prior["gaps_sha256"]==cp["scope"]["gap_sha256"] and prior["new_sha256"]==cp["scope"]["new_sha256"],"previous seals")
    require(first["promotion"] is False and extra["promotion"] is False,"overlay authority")
    raw=read(root,ROOT+"global-p1-a-targets-v1.json",a1.TARGET)
    specs=[s for group in raw["groups"] for s in group.split(";")]+raw["gap_additions"]
    parents=dict(zip(specs,got["claims"]))
    require(len(parents)==304 and len(got["new"])==10,"parent denominator")
    required={s for s,p in parents.items() if p["normalization_status"]=="VALUE_NORMALIZED_COMPOUND_REVIEW"}
    require(len(required)==63 and {x["parent_target"] for x in first["rows"]}==required and len(first["rows"])==63,"required compounds")
    additional={x["parent_target"] for x in extra["rows"]}
    require(len(additional)==len(extra["rows"])==12 and not additional&required and additional<=set(parents),"additional compounds")
    require(sum(p["value"] is None for p in parents.values())==27,"unknown parents preserved")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(a1.SOURCE)
    children=[]
    for row in first["rows"]+extra["rows"]:
        p=parents[row["parent_target"]]
        require(len(row["children"])>=2,"not a split")
        for spec in row["children"]:
            lo,hi=spec["interval"];v=spec["value"];pred=spec["predicate"];reason=spec["unknown_reason"]
            ident="P1A3-"+digest(p0.stable([p["id"],spec["subject"],pred,lo,hi]))[:24]
            modality=p["modality"]
            conditional=pred in CONDITIONAL or modality=="HYPOTHESIS"
            kind="CONDITIONAL_CLAIM" if conditional else "ATTRIBUTED_CLAIM" if modality=="REPORT" else "OBSERVED_EVENT" if modality=="NARRATED" else "NON_EVENT_OR_SCOPED_STATUS"
            # Claim type is an editorial route; do not silently upgrade parent's verdict.
            verdict="UNKNOWN" if v is None else "PARTIAL" if p["preliminary_verdict"]=="SUPPORTED" and modality!="NARRATED" else p["preliminary_verdict"]
            c=dict(id=ident,target_id=int(digest(ident)[:13],16),parent_id=p["id"],group_id=p["parent_id"],source=p["source"],source_sha256=p["source_sha256"],physical_blobs=sorted({x[2] for x in source[2] if x[0]<=hi and x[1]>=lo}),interval=[lo,hi],anchor=anchor(source,lo,hi),literal_evidence="\n".join(source[0][lo-1:hi]),source_role=p["source_role"],authority=p["authority"],subject=spec["subject"],predicate=pred,value=v,unknown_reason=reason,modality=modality,scope=p["scope"],claim_kind=kind,attribution="PARENT_SUBJECT_OR_SOURCE_CONTEXT" if modality=="REPORT" else None,condition={"status":"CONDITIONAL_NOT_CONFIRMED","parent_field":p["original_field"]} if conditional else p["condition"],polarity="UNKNOWN_NOT_NEGATIVE" if v is None else "EXPLICIT_FALSE" if v is False else "EXPLICIT_ZERO" if type(v) is int and v==0 else "AFFIRMATIVE_OR_SCOPED_DESCRIPTION",day=p["day"],time={"source_line":lo,"clock":None,"day_authority":"INHERITED_GROUP_HINT"},visibility=p["visibility"],current_state=False,knowledge_injection=False,state_before=None,state_after=None,identity_resolved=False,preliminary_verdict=verdict,independent_review=False,promotion=False)
            require(all(x==p["source_role"] for x in source[1][lo-1:hi]) and c["literal_evidence"].strip(),"child literal role")
            children.append(boundary(c,p))
    require(len(children)==269,"child count")
    uniqueness(children,[p["target_id"] for p in got["claims"]+got["new"]])
    # Reuse neutral exact-source review exchange, never provide preliminary values/verdicts.
    bounds=defaultdict(list);days=defaultdict(set)
    for c in children:
        n=c["interval"][0];bounds[n].append(c["interval"][1]);days[n].add(c["day"])
    targets=[]
    for c in children:
        n=c["interval"][0];lo=max(1,n-3);hi=min(1679,max(bounds[n])+3)
        while lo<n and source[1][lo-1]!=c["source_role"]:lo+=1
        while hi>max(bounds[n]) and source[1][hi-1]!=c["source_role"]:hi-=1
        targets.append(dict(original_id=c["target_id"],entity_id=c["subject"],field=c["predicate"],source=c["source"],source_sha256=c["source_sha256"],source_status="HISTORICAL_TRANSCRIPT_NOT_CANON_CERTIFIED",day=next(iter(days[n])) if len(days[n])==1 else None,line=n,anchor=source[0][n-1],anchor_sha256=digest(source[0][n-1]),context=[dict(line=i,text=source[0][i-1]) for i in range(lo,hi+1)]))
    jobs=list(queue.jobs(targets));packets=[];controller=queue.seal({"checkpoint":CP,"children":CHILD,"extra":EXTRA})
    for start in range(0,len(jobs),6):
        batch=jobs[start:start+6];jids=[x["job_id"] for x in batch];n=len(packets)+1
        a=chat.prepare_history(batch,jids,controller,"omega-p1-a3-child-%03d-A"%n)
        b=chat.prepare_history(batch,jids,controller,"omega-p1-a3-child-%03d-B"%n)
        require(chat.validate_history(a,a["batch_id"])==chat.validate_history(b,b["batch_id"]) and a["batch_id"]!=b["batch_id"],"review seal")
        packets.append((a,b))
    require(sum(len(j["targets"]) for j in jobs)==len(children),"review child loss")
    # Reuse P0 inventory, not a second historical extraction.
    holder={}
    def capture_p0(inventory,groups,partition):holder["inventory"]=inventory
    inv=p0.inspect(root,archive,inventory_consumer=capture_p0)
    require(inv["inventory_sha256"]==prior["p0_inventory_sha256"],"inventory seal")
    done={x["parent_id"] for x in got["claims"] if x["parent_id"] is not None}
    require(len(done)==79,"completed group count")
    plan,routes=expansion(holder["inventory"],done)
    require(sum(routes.values())==4862 and plan[0]["macro"]==2 and plan[0]["first_line"]>=1680,"next cursor")
    if consumer:consumer(children,packets,plan)
    manifest=[dict(batch=i+1,jobs=len(a["jobs"]),targets=sum(len(j["targets"]) for j in a["jobs"]),A=a["batch_id"],B=b["batch_id"]) for i,(a,b) in enumerate(packets)]
    return dict(status="P1_A3_COMPOUND_CHILD_OVERLAY_PASS_INDEPENDENT_HOLD",parent_targets=304,prior_supplemental_targets=10,required_compound_parents=63,additional_compound_parents=12,child_candidates=len(children),required_children=238,additional_children=31,unknown_parent_values_preserved=27,unknown_child_values=sum(c["value"] is None for c in children),child_modalities=dict(Counter(c["modality"] for c in children)),child_verdicts=dict(Counter(c["preliminary_verdict"] for c in children)),child_sha256=digest(p0.stable(children)),prior_claims_sha256=prior["claims_sha256"],prior_gap_sha256=prior["gaps_sha256"],prior_new_sha256=prior["new_sha256"],prior_packets_preserved=94,child_jobs=len(jobs),child_pairs=len(packets),child_packets=len(packets)*2,child_controller=controller,child_manifest=manifest,total_candidate_ids=314+len(children),leaf_review_candidates=314-len(required|additional)+len(children),remaining_groups=4862,expansion_batches=len(plan),expansion_routes=routes,expansion_plan_sha256=digest(p0.stable(plan)),first_batch=plan[0],oversize_batches=sum(x["oversize_single"] for x in plan),inventory_sha256=inv["inventory_sha256"],registry_binding=prior["registry_binding"],independent_review=False,semantic_certification=False,typed_projection=False,production_gate="HOLD",canon_changed=False,review_returns=0)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True);a=p.parse_args();print(json.dumps(build(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
