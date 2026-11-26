"""Two-pass semantic review exchange over exact private ledger.
No provider credentials or remote requests by default. Outputs are staging only.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path

SCHEMA="worldroot-semantic-review-job-v1"
VERDICTS={"SUPPORTED","PARTIAL","CONTRADICTED","UNKNOWN","NOT_ATTRIBUTED","NON_NARRATIVE","REPORT_ONLY","HYPOTHESIS","AUTHOR_REQUIRED","DRAFT_ONLY"}
ROLES={"NARRATED","REPORT","HYPOTHESIS","OPTION","PLAN","META","SUMMARY","DRAFT","UNCERTAIN"}
def seal(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def jobs(rows,already=()):
    """Group by source + exact line to avoid paying for repeated field contexts."""
    done=set(already);groups=defaultdict(list);ids=set()
    for r in rows:
        ident=r["original_id"]
        if ident in ids:raise ValueError("Duplicate original row")
        ids.add(ident)
        if ident not in done:groups[(r["source"],r["line"],r["anchor_sha256"])].append(r)
    for key,group in sorted(groups.items()):
        first=group[0]
        if any(r["context"]!=first["context"] or r["source_sha256"]!=first["source_sha256"] for r in group):raise ValueError("Conflicting repeated context")
        value={"schema":SCHEMA,"source":first["source"],"source_sha256":first["source_sha256"],"source_status":first["source_status"],"day":first.get("day"),"line":first["line"],"anchor":first["anchor"],"anchor_sha256":first["anchor_sha256"],"context":first["context"],"targets":[{"original_id":r["original_id"],"entity_id":r["entity_id"],"field":r["field"]} for r in sorted(group,key=lambda x:x["original_id"])]}
        yield {"job_id":seal(value),**value}
def validate(job,answer):
    if answer.get("job_id")!=job["job_id"] or not isinstance(answer.get("executor"),str) or not answer["executor"].strip() or not isinstance(answer.get("model_revision"),str) or not answer["model_revision"].strip():raise ValueError("Review identity required")
    if answer.get("source_role") not in ROLES or not str(answer.get("role_reason","")).strip():raise ValueError("Explicit source role required")
    rows=answer.get("decisions")
    if not isinstance(rows,list):raise ValueError("Missing decisions")
    expected={x["original_id"]:x for x in job["targets"]};seen=set()
    for r in rows:
        ident=r.get("original_id");target=expected.get(ident)
        if target is None or ident in seen or r.get("entity_id")!=target["entity_id"] or r.get("field")!=target["field"] or r.get("verdict") not in VERDICTS or not str(r.get("reason","")).strip():raise ValueError("Invalid review row")
        seen.add(ident)
        if r["verdict"]=="SUPPORTED":
            if job["source_status"]=="PENDING_NOT_CLOSED" or answer["source_role"]!="NARRATED":raise ValueError("Draft or non-narrated text cannot support factual promotion")
            evidence=r.get("evidence")
            if not isinstance(evidence,str) or not evidence.strip() or evidence not in "\n".join(x["text"] for x in job["context"]) or not str(r.get("claim","")).strip():raise ValueError("Missing literal support")
        if r.get("current_state") is True:raise ValueError("Historical claim is not current state")
    if seen!=set(expected):raise ValueError("Incomplete review")
    return answer
def reconcile(job,first,second):
    """Agreement is candidate evidence, not an automatic canon merge."""
    a=validate(job,first);b=validate(job,second)
    if (a["executor"],a["model_revision"])==(b["executor"],b["model_revision"]) or a["executor"]==b["executor"]:raise ValueError("Independent review executor required")
    # Different names alone do not prove genuine independence; workflow attestation required.
    by={r["original_id"]:r for r in b["decisions"]};out=[]
    for r in a["decisions"]:
        other=by[r["original_id"]];agree=a["source_role"]==b["source_role"] and r["verdict"]==other["verdict"] and (r["verdict"]!="SUPPORTED" or (r.get("claim")==other.get("claim") and r.get("evidence")==other.get("evidence")))
        out.append({"original_id":r["original_id"],"route":"AGREEMENT_CANDIDATE" if agree else "DISAGREEMENT_REVIEW_REQUIRED","first":r,"second":other,"source_sha256":job["source_sha256"],"anchor_sha256":job["anchor_sha256"],"canon_promotion":False,"semantic_certification":False})
    return out
def export(ledger,output,already=()):
    rows=[r for p in sorted(Path(ledger).glob("batch-*.json")) for r in read(p)]
    if len(rows)!=9229:raise ValueError("Incomplete original ledger")
    out=Path(output);count=targets=0
    with out.open("x",encoding="utf-8") as f:
        for j in jobs(rows,already):
            f.write(json.dumps(j,ensure_ascii=False,separators=(",",":"))+"\n");count+=1;targets+=len(j["targets"])
    return {"jobs":count,"targets":targets,"canon_changed":False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--ledger",required=True);p.add_argument("--output",required=True);p.add_argument("--completed-first-pass");a=p.parse_args()
    already=[r["original_id"] for r in read(a.completed_first_pass)["rows"]] if a.completed_first_pass else []
    print(json.dumps(export(a.ledger,a.output,already)))
if __name__=="__main__":main()
