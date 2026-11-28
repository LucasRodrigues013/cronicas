"""P1-A source-bound atomization adapter. No public text export, no canon writes."""
import argparse,json,re
from pathlib import Path
from collections import Counter,defaultdict
from . import omega_global_p0 as p0, semantic_queue as queue, r36_chat_review as chat
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, anchor, digest, require
from .live_codex import norm

P0="00007832ee28d0e3f4a58095eec3cccded80b556"
TARGET="0ab64aa1b4365312c14d17e2a695478d3ad7ac87"
SOURCE="01_DIA_001_A_383_FONTE_LITERAL.txt"
PARENTS={"book-I/lote-0001.json":"5987092e0900f850a793bead4689bae63342d5b4","book-I/lote-0002.json":"7215b608da83a002b73fa4bfc8a8d46fdbbfd0aa","bulk-pilot-semantic-sample.json":"a9e070cab943ae05c1601a818379c57fbd6df1ac"}
ROLES={"N":"NARRATED","R":"REPORT","H":"HYPOTHESIS","P":"PLAN","O":"OPTION","S":"SUMMARY","M":"META","D":"DRAFT"}
VERDICTS={"S":"SUPPORTED","P":"PARTIAL","U":"UNKNOWN","C":"CONTRADICTED","A":"AUTHOR_REQUIRED"}
# Explicitly scoped values for early numerical/temporal claims, not current state.
VALUES={"created_count":300,"creation_reserve_estimate":None,"alive_count":300,"fit_count":275,"lightly_wounded_count":18,"temporarily_unfit_count":7,"confirmed_deaths":0,"two_need_monitoring":2,"no_cavalry":False,"three_teams_of_four":[3,4],"twenty_minute_delay":20,"four_missing_report":4,"three_missing":3,"no_formal_institution_or_claim":False,"kingdom_not_founded":False,"last_count_alive":300,"one_returned_three_no_contact":[1,3],"self_chosen_name":None}
def parse(s):
    span,entity,field,role,verdict=s.split(":")
    ends=[int(x) for x in span.split("-")]
    return ends[0],ends[-1],entity,field,ROLES[role],VERDICTS[verdict]
def build(root,archive,consumer=None):
    root=Path(root);archive=Path(archive)
    cp=read(root,ROOT+"global-p0-checkpoint-v1.json",P0)
    t=read(root,ROOT+"global-p1-a-targets-v1.json",TARGET)
    captured={}
    def take(inventory,groups,partition):
        captured.update(inventory=inventory,groups=groups,partition=partition)
    prior=p0.inspect(root,archive,inventory_consumer=take)
    require(prior["status"]=="P0_INVENTORY_STRUCTURAL_PASS" and prior["inventory_sha256"]==cp["inventory"]["sha256"] and prior["p1_groups_sha256"]==cp["p1"]["group_manifest_sha256"] and prior["legacy_partition_sha256"]==cp["coverage"]["partition_sha256"],"P0 immutable binding")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(SOURCE)
    originals=[]
    for path in t["parent_order"]:
        raw=read(root,p0.PREFIX+path,PARENTS[path]);originals.extend(raw["records"])
    parents={r["id"]:r for r in captured["inventory"] if r["receipt_blob"] in PARENTS.values()}
    require(len(originals)==len(parents)==len(t["groups"])==79 and set(parents)=={r["id"] for r in originals},"parent coverage")
    registry=read(archive,"editorial/registries/universal-codex-design-d580-v1.json",p0.REGISTRY_PINS["universal-codex-design-d580-v1.json"])
    rows=registry["records"]+registry["species"]+registry["arcane"]["schools"]+registry["arcane"]["index"]
    idx=defaultdict(set)
    for r in rows:
        for label in [r["id"],r["name"],*r.get("aliases",[])]:idx[norm(label)].add(r["id"])
    atoms=[]; ids=set(); numeric=set(); gap_parts=[]
    gaps=[g for g in captured["partition"] if g["disposition"]=="UNANNOTATED_PENDING_P1"]
    require(sum(g["end"]-g["start"]+1 for g in gaps)==534,"legacy gap denominator")
    def add(spec,parent,gap=None):
        a,z,entity,field,role,verdict=parse(spec)
        bounds=parent["interval"] if parent else [gap["start"],gap["end"]]
        require(bounds[0]<=a<=z<=bounds[1] and all(v==source[1][a-1] for v in source[1][a-1:z]),"target span "+field)
        require(any(v.strip() for v in source[0][a-1:z]),"empty target")
        origin=parent["id"] if parent else "GAP-%04d-%04d"%(gap["start"],gap["end"])
        ident="P1A-"+digest(p0.stable([origin,a,z,entity,field]))[:24];num=int(digest(ident)[:13],16)
        require(ident not in ids and num not in numeric,"atom duplicate");ids.add(ident);numeric.add(num)
        rawrole=source[1][a-1]
        require(rawrole!="Prompt" or role=="META","prompt promoted")
        day=parent["day"] if parent else 1
        vis=parent["visibility"] if parent else "EDITORIAL_ONLY_NO_CHARACTER_INJECTION"
        authority=parent["authority"] if parent else "HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED"
        value=VALUES.get(field)
        if field=="creation_reserve_estimate":value=[5,5] if a==259 else [1,2] if a in (1485,1639) else None
        if field=="self_chosen_name":value="VARO" if a==982 else "KAEL" if a==1453 else None
        if field=="no_cavalry":value=0
        candidates=sorted(idx[norm(entity)])
        atom=dict(id=ident,target_id=num,parent_id=parent["id"] if parent else None,gap_interval=bounds if gap else None,source=SOURCE,source_sha256=source[3],interval=[a,z],anchor=anchor(source,a,z),physical_blobs=sorted({p[2] for p in source[2] if p[0]<=z and p[1]>=a}),role=rawrole,authority=authority,day=day,time_scope="HISTORICAL_SOURCE_ONLY",entity=entity,field=field,registry_candidates=candidates,identity_status="LEXICAL_CANDIDATE_ONLY" if len(candidates)==1 else "AMBIGUOUS" if candidates else "UNRESOLVED_LOCAL_LABEL",visibility=vis,modality=role,preliminary_verdict=verdict,condition="SOURCE_BOUND_CONDITIONAL" if role=="HYPOTHESIS" else None,negation="EXPLICIT_FIELD_NEGATION" if any(x in field for x in ("unknown","no_","not_","unconfirmed","unidentified","unresolved")) else "NOT_FORMALLY_NORMALIZED",state_before=None,state_after=value,normalized_value_status="SCOPED_VALUE" if value is not None else "PENDING_VALUE_NORMALIZATION",literal_evidence="\n".join(source[0][a-1:z]),current_state=False,promotion=False,independent=False)
        atoms.append(atom)
    for original,spec in zip(originals,t["groups"]):
        p=parents[original["id"]]
        require(p["anchor"]==original["evidence"]["span_sha256_utf8"] and p["interval"]==[original["evidence"]["line_start"],original["evidence"]["line_end"]],"parent anchor")
        for s in spec.split(";"):add(s,p)
    for spec in t["gap_additions"]:
        a,z,*_=parse(spec);match=[g for g in gaps if g["start"]<=a<=z<=g["end"]]
        require(len(match)==1,"gap candidate outside legacy gap")
        add(spec,None,match[0])
    # Each previously unannotated line is dispositioned. Narrative remainder is
    # explicitly pending semantic completeness, not silently declared duplicate.
    additions={n for x in atoms if x["parent_id"] is None for n in range(x["interval"][0],x["interval"][1]+1)}
    for g in gaps:
        last=None
        for n in range(g["start"],g["end"]+1):
            line=source[0][n-1];rawrole=source[1][n-1]
            matches=[x[2] for x in t["gap_rules"] if x[0]<=n<=x[1]]
            require(len(matches)==1,"gap rule geometry")
            if not line.strip() or re.match(r"^(## (Prompt|Response):|\d\d/\d\d/\d{4},)",line):category="EXPORT_FORMAT_OR_METADATA"
            elif n in additions:category="NEW_ATOMIC_CANDIDATE"
            elif rawrole=="Prompt":category="AUTHOR_DIRECTION_OR_ATTACHMENT_GAP"
            else:category=matches[0]
            if last==category:gap_parts[-1]["end"]=n
            else:gap_parts.append(dict(start=n,end=n,category=category,source=SOURCE,role=rawrole,parent_gap_sha256=g["sha256"]))
            last=category
    for g in gap_parts:g["sha256"]=anchor(source,g["start"],g["end"])
    require(sum(g["end"]-g["start"]+1 for g in gap_parts)==534,"gap classification coverage")
    # Reuse historical queue contract. Group per exact anchor line; reviewers
    # see neutral targets and exact source only, never preliminary verdicts.
    max_end=defaultdict(int)
    for x in atoms:max_end[x["interval"][0]]=max(max_end[x["interval"][0]],x["interval"][1])
    targets=[]
    for x in atoms:
        a,z=x["interval"];lo=max(1,a-3);hi=min(1679,max_end[a]+3)
        while lo<a and source[1][lo-1]!=x["role"]:lo+=1
        while hi>z and source[1][hi-1]!=x["role"]:hi-=1
        ctx=[{"line":i,"text":source[0][i-1]} for i in range(lo,hi+1)]
        # Shared anchor context must not depend on a particular target.
        targets.append(dict(original_id=x["target_id"],entity_id=x["entity"],field=x["field"],source=SOURCE,source_sha256=source[3],source_status="HISTORICAL_TRANSCRIPT_NOT_CANON_CERTIFIED",day=x["day"],line=a,anchor=source[0][a-1],anchor_sha256=digest(source[0][a-1]),context=ctx))
    # Same anchor can be present in two groups with different day metadata;
    # keep day unknown for reviewer when historical day labels disagree.
    daysets=defaultdict(set)
    for row in targets:daysets[row["line"]].add(row["day"])
    for row in targets:
        if len(daysets[row["line"]])>1:row["day"]=None
    jobs=list(queue.jobs(targets))
    # Reuse existing A/B transport; each batch <=12 jobs and byte budget.
    packets=[];controller=queue.seal({"p0":P0,"target":TARGET,"scope":[1,1679]})
    for start in range(0,len(jobs),6):
        batch=jobs[start:start+6];jids=[j["job_id"] for j in batch];n=len(packets)+1
        a=chat.prepare_history(batch,jids,controller,"omega-p1-a-%03d-review-A"%n)
        b=chat.prepare_history(batch,jids,controller,"omega-p1-a-%03d-review-B"%n)
        require(chat.validate_history(a,a["batch_id"])==chat.validate_history(b,b["batch_id"]) and a["batch_id"]!=b["batch_id"],"review packet parity")
        packets.append((a,b))
    require(sum(len(j["targets"]) for j in jobs)==len(atoms),"target loss")
    if consumer:consumer(atoms,gap_parts,packets)
    return dict(status="P1_A_PRELIMINARY_TARGETS_NATIVE_PASS_INDEPENDENT_HOLD",parents=len(parents),parent_atoms=sum(x["parent_id"] is not None for x in atoms),gap_atoms=sum(x["parent_id"] is None for x in atoms),targets=len(atoms),unique_ids=len(ids),gap_lines=534,gap_parts=len(gap_parts),gap_categories=dict(Counter({k:sum(g["end"]-g["start"]+1 for g in gap_parts if g["category"]==k) for k in {g["category"] for g in gap_parts}})),preliminary_verdicts=dict(Counter(x["preliminary_verdict"] for x in atoms)),modalities=dict(Counter(x["modality"] for x in atoms)),identity_status=dict(Counter(x["identity_status"] for x in atoms)),normalized_value_targets=sum(x["state_after"] is not None for x in atoms),jobs=len(jobs),batch_pairs=len(packets),packet_manifest=[{"batch":i+1,"jobs":len(a["jobs"]),"targets":sum(len(j["targets"]) for j in a["jobs"]),"A":a["batch_id"],"B":b["batch_id"]} for i,(a,b) in enumerate(packets)],atom_sha256=digest(p0.stable(atoms)),gap_sha256=digest(p0.stable(gap_parts)),controller_pin=controller,source_sha256=source[3],p0_inventory_sha256=prior["inventory_sha256"],cumulative_status=prior["cumulative_status"],atomic_claims_independently_certified=0,independent_review=False,semantic_certification=False,typed_projection=False,production_gate="HOLD",canon_changed=False)
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(build(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
