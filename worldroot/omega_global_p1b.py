"""P1-B reusable, read-only legacy receipt expansion. Editorial overlays are not canon."""
import argparse,json
from pathlib import Path
from collections import Counter,defaultdict
from . import omega_global_p1a3 as a3,omega_global_p0 as p0,semantic_queue as queue,r36_chat_review as chat
from .omega_hybrid_receipt import ROOT,read
from .omega_turbo_recovery import SourceCache,anchor,digest,git_blob,require

CP="3432df660d63f9eddf8e755d91f6572a20678e70"
EV="54913acf7f07f91b6497d87f248d580033978b3f"
ADAPTER="6251b9fa246017a904ebbe87b1e12ff4fc5f144d"
DEFAULT=ROOT+"global-p1-b-batch-001-sublot-001-v1.json"
MODALITIES={"NARRATED","REPORT","PLAN","META","HYPOTHESIS","DRAFT","SUMMARY","OPTION","UNCERTAIN"}
def validate_spec(spec,parent):
    require(len(spec)==6,"spec shape")
    subject,predicate,value,modality,lo,hi=spec
    e=parent["evidence"]
    require(isinstance(subject,str) and subject and isinstance(predicate,str) and predicate,"locator")
    require(type(lo) is int and type(hi) is int and e["line_start"]<=lo<=hi<=e["line_end"],"child interval")
    require(modality in MODALITIES,"modality")
    require(e["role"]!="Prompt" or modality=="META","prompt event")
    require(parent["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" or modality in {"META","OPTION","DRAFT","UNCERTAIN"},"authority escalation")
    require(predicate!="biological_age_years" or value is None,"apparent vs biological age")
    return spec

def geometry(records,group_ids,gaps,bounds):
    require(group_ids==[r["id"] for r in records],"ordered group IDs")
    intervals=[(r["evidence"]["line_start"],r["evidence"]["line_end"]) for r in records]
    require(all(len(g)==3 and g[2] for g in gaps),"gap disposition")
    spans=sorted(intervals+[(g[0],g[1]) for g in gaps])
    at=bounds[0]
    for lo,hi in spans:
        require(lo==at and lo<=hi,"partition gap or overlap")
        at=hi+1
    require(at==bounds[1]+1,"partition end")

def remaining_counts(batch_count,offset,count,macro_count,absolute,global_count):
    require(0<=offset<batch_count and 0<count<=batch_count-offset and absolute+count<=macro_count and count<=global_count,"denominator")
    return batch_count-offset-count,macro_count-absolute-count,global_count-count

def build(root,archive,overlay_path=DEFAULT,consumer=None):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"global-p1-a3-checkpoint-v1.json",CP)
    ev=read(root,cp["native_evidence_path"],EV)
    require(git_blob((root/"worldroot/omega_global_p1a3.py").read_bytes())==ADAPTER,"adapter changed")
    got={}
    def capture(children,packets,plan):got.update(children=children,packets=packets,plan=plan)
    prior=a3.build(root,archive,consumer=capture)
    require(prior==ev["aggregate"] and prior["child_sha256"]==cp["scope"]["children_sha256"] and prior["expansion_plan_sha256"]==cp["scaling"]["plan_sha256"],"prior seals")
    o=read(root,overlay_path)
    require(o["schema"]=="OMEGA_GLOBAL_P1_B_EDITORIAL_SUBLOT_V1" and o["project"]==cp["project"] and o["production_gate"]=="HOLD" and o["promotion"] is False and o["semantic_certification"] is False,"overlay authority")
    require(type(o["batch"]) is int and 1<=o["batch"]<=len(got["plan"]),"batch index")
    plan=got["plan"][o["batch"]-1]
    require(plan["macro"]==o["macro"],"macro binding")
    receipt=read(root,o["receipt_path"],o["receipt_blob"])
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(plan["source"])
    require(receipt["source"]==plan["source"] and receipt["archive_pin"]==cp["archive_pin"] and receipt["source_sha256"]==source[3],"receipt source")
    records=receipt["records"];batch_count=plan["count"]
    matches=[i for i in range(len(records)-batch_count+1) if digest(p0.stable([r["id"] for r in records[i:i+batch_count]]))==plan["ids_sha256"]]
    require(len(matches)==1,"planned ID range")
    batch=records[matches[0]:matches[0]+batch_count]
    require(sum(r["evidence"]["line_end"]-r["evidence"]["line_start"]+1 for r in batch)==plan["anchor_line_weight"],"plan weight")
    require(min(r["evidence"]["line_start"] for r in batch)==plan["first_line"] and max(r["evidence"]["line_end"] for r in batch)==plan["last_line"],"plan bounds")
    offset=o["offset"];count=len(o["groups"])
    require(type(offset) is int and 0<=offset<batch_count and 0<count<=batch_count-offset,"sublot bounds")
    chosen=batch[offset:offset+count]
    absolute=matches[0]+offset
    start=receipt["range"][0] if absolute==0 else records[absolute]["evidence"]["line_start"]
    stop=records[absolute+count]["evidence"]["line_start"]-1 if absolute+count<len(records) else receipt["range"][1]
    require(o["range"]==[start,stop],"cursor boundary")
    # Chained offsets must bind a native checkpoint, never simply trust an offset.
    if absolute>0:
        prev=read(root,o["previous_checkpoint_path"],o["previous_checkpoint_blob"])
        require(prev["schema"]=="OMEGA_GLOBAL_P1_B_CHECKPOINT_V1" and prev["production_gate"]=="HOLD" and prev["receipt_blob"]==o["receipt_blob"] and prev["batch"]==o["batch"],"previous cursor authority")
        prev_ev=read(root,prev["native_evidence_path"],prev["native_evidence_blob"])
        require(prev_ev["workflow_conclusion"]=="success" and prev_ev["aggregate"]["next_anchor"]==start and prev["next_offset"]==offset and prev["next_anchor"]==start,"previous native cursor")
        require(prev["completed_ids"]==[r["id"] for r in batch[:offset]],"previous group prefix")
    else:
        require(offset==0,"initial cursor")
    geometry(chosen,[g[0] for g in o["groups"]],o["gaps"],o["range"])
    claims=[];parent_rows=[];gaps=[];ids=set();target_ids={c["target_id"] for c in got["children"]}
    for r,(_,specs) in zip(chosen,o["groups"]):
        e=r["evidence"];a,z=e["line_start"],e["line_end"]
        require(r["promotion"] is False and e["source_sha256_manifest"]==source[3] and anchor(source,a,z)==e["span_sha256_utf8"],"parent anchor")
        require(all(t==e["role"] for t in source[1][a-1:z]),"parent role")
        require(e["blob_sha1"] in {b for lo,hi,b in source[2] if lo<=z and hi>=a},"parent physical")
        require(len(specs)>0,"empty editorial review")
        parent_rows.append(dict(id=r["id"],interval=[a,z],anchor=e["span_sha256_utf8"],children=len(specs),authority=r["authority"],visibility=r["visibility"],retained=True))
        for spec in specs:
            subject,predicate,value,modality,lo,hi=validate_spec(spec,r)
            ident="P1B-"+digest(p0.stable([r["id"],subject,predicate,lo,hi]))[:24]
            target=int(digest(ident)[:13],16)
            require(ident not in ids and target not in target_ids,"duplicate child")
            ids.add(ident);target_ids.add(target)
            require(all(t==e["role"] for t in source[1][lo-1:hi]) and any(s.strip() for s in source[0][lo-1:hi]),"child literal role")
            verdict="UNKNOWN" if value is None else "SUPPORTED" if modality=="NARRATED" else "PARTIAL"
            claims.append(dict(id=ident,target_id=target,parent_id=r["id"],source=plan["source"],source_sha256=source[3],interval=[lo,hi],anchor=anchor(source,lo,hi),physical_blobs=sorted({b for a,z,b in source[2] if a<=hi and z>=lo}),subject=subject,predicate=predicate,value=value,modality=modality,source_role=e["role"],authority=r["authority"],scope=r["scope"],visibility=r["visibility"],day=r["day"],time={"source_line":lo,"clock":None,"day_authority":"INHERITED_GROUP_HINT"},attribution="SOURCE_CONTEXT_REQUIRED" if modality=="REPORT" else None,condition="CONDITIONAL_OR_UNCONFIRMED" if modality=="HYPOTHESIS" else "AS_STATED_IN_SOURCE" if modality=="PLAN" else None,polarity="UNKNOWN_NOT_NEGATIVE" if value is None else "EXPLICIT_FALSE" if value is False else "EXPLICIT_ZERO" if type(value) is int and value==0 else "AFFIRMATIVE_OR_SCOPED_DESCRIPTION",unknown_reason="NOT_ESTABLISHED_BY_LITERAL" if value is None else None,preliminary_verdict=verdict,identity_resolved=False,current_state=False,knowledge_injection=False,state_before=None,state_after=None,promotion=False,independent_review=False))
    for lo,hi,kind in o["gaps"]:
        at=lo
        while at<=hi:
            end=at
            while end<hi and source[1][end]==source[1][at-1]:end+=1
            gaps.append(dict(interval=[at,end],role=source[1][at-1],anchor=anchor(source,at,end),disposition=kind,promotion=False))
            at=end+1
    # Context for same-line targets must be identical. No values or verdicts exported to reviewers.
    bounds=defaultdict(list);days=defaultdict(set)
    for c in claims:
        lo,hi=c["interval"];bounds[lo].append(hi);days[lo].add(c["day"])
    targets=[]
    for c in claims:
        n=c["interval"][0];lo=max(start,n-3);hi=min(stop,max(bounds[n])+3)
        while lo<n and source[1][lo-1]!=c["source_role"]:lo+=1
        while hi>max(bounds[n]) and source[1][hi-1]!=c["source_role"]:hi-=1
        targets.append(dict(original_id=c["target_id"],entity_id=c["subject"],field=c["predicate"],source=c["source"],source_sha256=c["source_sha256"],source_status="HISTORICAL_TRANSCRIPT_NOT_CANON_CERTIFIED",day=next(iter(days[n])) if len(days[n])==1 else None,line=n,anchor=source[0][n-1],anchor_sha256=anchor(source,n,n),context=[dict(line=i,text=source[0][i-1]) for i in range(lo,hi+1)]))
    jobs=list(queue.jobs(targets));packets=[];controller=queue.seal(dict(checkpoint=CP,overlay=git_blob((root/overlay_path).read_bytes()),batch=o["batch"],offset=offset))
    for i in range(0,len(jobs),6):
        part=jobs[i:i+6];jids=[j["job_id"] for j in part];prefix="omega-p1b-%03d-%03d-%03d"%(o["batch"],offset,i//6+1)
        a=chat.prepare_history(part,jids,controller,prefix+"-A")
        b=chat.prepare_history(part,jids,controller,prefix+"-B")
        require(chat.validate_history(a,a["batch_id"])==chat.validate_history(b,b["batch_id"]) and a["batch_id"]!=b["batch_id"],"packet equivalence")
        packets.append((a,b))
    require(sum(len(j["targets"]) for j in jobs)==len(claims),"target loss")
    manifest=[dict(A=a["batch_id"],B=b["batch_id"],jobs=len(a["jobs"]),targets=sum(len(j["targets"]) for j in a["jobs"])) for a,b in packets]
    remaining_batch,remaining_macro,global_remaining=remaining_counts(batch_count,offset,count,len(records),absolute,prior["remaining_groups"]-offset)
    if consumer:consumer(parent_rows,claims,gaps,packets)
    return dict(status="P1_B_PARTIAL_EDITORIAL_STAGING_INDEPENDENT_HOLD",batch=o["batch"],macro=o["macro"],range=o["range"],completed_ids=[r["id"] for r in chosen],processed_groups=count,remaining_in_batch=remaining_batch,remaining_in_macro=remaining_macro,global_remaining=global_remaining,next_anchor=records[absolute+count]["evidence"]["line_start"] if absolute+count<len(records) else None,children=len(claims),modalities=dict(Counter(c["modality"] for c in claims)),verdicts=dict(Counter(c["preliminary_verdict"] for c in claims)),parents_sha256=digest(p0.stable(parent_rows)),children_sha256=digest(p0.stable(claims)),gaps_sha256=digest(p0.stable(gaps)),gap_spans=len(gaps),gap_lines=sum(g["interval"][1]-g["interval"][0]+1 for g in gaps),anchor_lines=sum(r["evidence"]["line_end"]-r["evidence"]["line_start"]+1 for r in chosen),prior_packets=prior["prior_packets_preserved"]+prior["child_packets"],new_jobs=len(jobs),new_pairs=len(packets),new_packets=len(packets)*2,review_controller=controller,review_manifest=manifest,review_returns=0,registry_binding=prior["registry_binding"],production_gate="HOLD",promotion=False,semantic_certification=False,independent_review=False,canon_changed=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True);p.add_argument("--overlay",default=DEFAULT);a=p.parse_args();print(json.dumps(build(a.engine_root,a.archive_root,a.overlay),sort_keys=True))
if __name__=="__main__":main()
