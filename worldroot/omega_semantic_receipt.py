"""Validate controller-authored bulk semantic receipts; no inference or promotion."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from .omega_bulk_recovery import digest_bytes,digest_text,seal,require,verify_reviewed
from .history_index import read_verified_sources
from .deep_recovery import sections
from .live_codex import load_registry
from .git_cycle import load

def roles_for(body):
    return {n:role for role,start,ls in sections(body) for n in range(start,start+len(ls))}
def anchor(lines,lo,hi):
    require(type(lo) is int and type(hi) is int and 1<=lo<=hi<=len(lines),"Bad interval")
    return digest_text("\n".join(lines[lo-1:hi]))
def check_records(records, lines, roles, source, source_sha, bounds, known_ids=None):
    ids=set()
    for rec in records:
        e=rec["evidence"];lo,hi=e["line_start"],e["line_end"]
        require(rec["id"] not in ids and rec["promotion"] is False,"Duplicate ID or promotion")
        require(bounds[0]<=lo<=hi<=bounds[1] and e["source"]==source and e["source_sha256_manifest"]==source_sha,"Source or bounds mismatch")
        require(e["role"] in ("Prompt","Response") and all(roles.get(n)==e["role"] for n in range(lo,hi+1)),"Role mismatch")
        require(anchor(lines,lo,hi)==e["span_sha256_utf8"],"Anchor mismatch")
        require(rec["axes"] and all(type(i) is int and 1<=i<=30 for i in rec["axes"]),"Axis mismatch")
        require("NO_CHARACTER_INJECTION" in rec["visibility"],"Unsafe visibility")
        require(not (e["role"]=="Prompt" and rec["authority"] not in ("AUTHOR_REQUEST_OR_CHOICE","AUTHOR_DIRECTION_NOT_EVENT")),"Prompt authority")
        require(not (rec["type"] in ("reader-only","dream","variant") and not rec["visibility"].startswith("READER_ONLY")),"Private perspective leakage")
        ids.add(rec["id"])
    return ids
def check_coverage(coverage, records,lines,roles,bounds):
    expected=bounds[0];seen=set();by_id={r["id"]:r for r in records}
    for row in coverage:
        lo,hi=row["start"],row["end"]
        require(lo==expected and hi<=bounds[1] and lo<=hi,"Coverage gap/overlap")
        require(anchor(lines,lo,hi)==row["span_sha256_utf8"],"Coverage hash mismatch")
        require(all(roles.get(n)==row["role"] for n in range(lo,hi+1)),"Coverage role mismatch")
        require(lines[lo-1].strip() in ("## Prompt:","## Response:"),"Not a section start")
        require(not any(lines[n-1].strip() in ("## Prompt:","## Response:") for n in range(lo+1,hi+1)),"Section split hidden")
        require(row["record_ids"] and len(set(row["record_ids"]))==len(row["record_ids"]),"Missing/duplicate annotations")
        for rid in row["record_ids"]:
            require(rid in by_id and rid not in seen,"Unknown or repeated annotation")
            e=by_id[rid]["evidence"];require(lo<=e["line_start"]<=e["line_end"]<=hi,"Annotation out of section")
            seen.add(rid)
        expected=hi+1
    require(expected==bounds[1]+1 and seen==set(by_id),"Incomplete coverage")
    return len(seen)
def check_links(receipt, registry_ids):
    records={r["id"]:r for r in receipt["records"]}
    labels={e for r in records.values() for e in r["entities"]}
    links=receipt["entity_links"]
    require(len(links)==len(labels) and {x["label"] for x in links}==labels,"Missing/duplicate entity mapping")
    for row in links:
        rid=row["registry_id"]
        require(rid is None or rid in registry_ids,"Fabricated registry identity")
        require((rid is None)==(row["disposition"]=="UNRESOLVED_LOCAL_LABEL"),"Invalid identity disposition")
    for row in receipt["reconciliations"]:
        require(row["evidence"] in records and (row["existing_id"] is None or row["existing_id"] in registry_ids),"Reconciliation evidence")
    seen=set()
    for row in receipt["causal_links"]:
        a,b=row["from"],row["to"]
        require(a in records and b in records and (a,b,row["kind"]) not in seen,"Missing/duplicate relation")
        require(records[a]["evidence"]["line_start"]<records[b]["evidence"]["line_start"],"Non-forward source relation")
        seen.add((a,b,row["kind"]))
    for group in receipt["duplicate_review_groups"]:
        require(group["preserve_all"] is True and len(set(group["members"]))>=2 and set(group["members"])<=set(records),"Unsafe deduplication")
    return {"entity_labels":len(labels),"existing_links":sum(x["registry_id"] is not None for x in links),"unresolved":sum(x["registry_id"] is None for x in links),"relations":len(seen),"duplicate_groups":len(receipt["duplicate_review_groups"])}
def verify_receipt(archive,engine):
    t=time.perf_counter();archive=Path(archive);engine=Path(engine)
    cp=load(engine/"docs/omega008-c-checkpoint.json")
    receipt=load(engine/"audit/omega008-c/bulk-semantic-macro-0002.json")
    require(receipt["project"]==cp["project"]=="CRONICAS_DE_UM_NOVO_MUNDO" and receipt["archive_pin"]==cp["source_archive"],"Project or pin")
    require(receipt["canon_changed"] is False and receipt["semantic_certification"] is False and receipt["independent_review"] is False,"False authority")
    require(load(archive/"canon/HEAD.json")["day"]==579,"Archive horizon")
    bulk=cp["bulk"]
    base=digest_bytes((engine/"docs/omega008-c-checkpoint.json").read_bytes())
    if "phase2" in bulk:
        require(bulk["phase2"]["base_checkpoint_sha256"]==receipt["base_checkpoint_sha256"],"Base checkpoint mismatch")
        require(digest_bytes((engine/bulk["phase2"]["receipt"]).read_bytes())==bulk["phase2"]["receipt_sha256_utf8"],"Receipt hash mismatch")
    else: require(base==receipt["base_checkpoint_sha256"],"Base checkpoint mismatch")
    queue_raw=(engine/bulk["macro_queue"]).read_bytes()
    require(digest_bytes(queue_raw)==bulk["macro_queue_sha256_utf8"],"Queue file mismatch")
    queue=json.loads(queue_raw);macros=queue["macros"]
    require(seal(macros)==bulk["macro_sha256"] and len(macros)==116,"Queue seal mismatch")
    require(all(m["previous_macro"]==(macros[i-1]["id"] if i else None) for i,m in enumerate(macros)),"Broken macro chain")
    macro=next(m for m in macros if m["id"]==receipt["macro_id"])
    require([macro["start"],macro["end"]]==receipt["macro_range"] and receipt["next_line"]==macro["end"]+1,"Macro bounds")
    require(digest_bytes((engine/bulk["report"]).read_bytes())==bulk["report_sha256_utf8"],"Pilot report mismatch")
    _,sources=read_verified_sources(archive);meta,body=sources[0]
    old=verify_reviewed(engine,cp,meta,body)
    lines=body.split("\n");roles=roles_for(body)
    sample_meta=receipt["sample"];raw=(engine/sample_meta["path"]).read_bytes()
    require(digest_bytes(raw)==sample_meta["sha256_utf8"]==bulk["sample"]["sha256_utf8"],"Sample hash mismatch")
    sample=json.loads(raw)
    require(sample["reviewed_sample_range"]==sample_meta["range"] and len(sample["records"])==sample_meta["records"]==21,"Sample metadata")
    require(sample_meta["range"][0]==macro["start"] and sample_meta["range"][1]+1==receipt["range"][0] and receipt["range"][1]==macro["end"],"Sample/receipt gap")
    first=check_records(sample["records"],lines,roles,meta["source_name"],meta["sha256"],sample_meta["range"])
    current=check_records(receipt["records"],lines,roles,meta["source_name"],meta["sha256"],receipt["range"])
    require(not first&current,"Sample duplicate ID")
    count=check_coverage(receipt["coverage"],receipt["records"],lines,roles,receipt["range"])
    registry=load_registry(archive);require(registry is not None,"Missing Codex")
    metrics=check_links(receipt,{r["id"] for r in registry[0]["records"]})
    require(receipt["open_response_tail"] and roles[macro["end"]]==roles[macro["end"]+1]=="Response","Unreported cut response")
    axes={a for r in receipt["records"] for a in r["axes"]}
    require(set(receipt["axis_coverage"]["assessed"])==set(range(1,31)) and axes==set(receipt["axis_coverage"]["represented"]),"Axis ledger")
    return dict(status="PASS_CONTROLLER_RECEIPT_INTEGRITY",old_records=old["records_verified"],sample_records=len(first),new_records=count,review_sections=len(receipt["coverage"]),controller_review_lines=macro["lines"],represented_axes=len(axes),next_line=receipt["next_line"],**metrics,semantic_certification=False,independent_review=False,canon_changed=False,elapsed_seconds=round(time.perf_counter()-t,6))
def main():
    p=argparse.ArgumentParser();p.add_argument("--archive-root",required=True);p.add_argument("--engine-root",default=".")
    a=p.parse_args();print("SEMANTIC_RECEIPT "+json.dumps(verify_receipt(a.archive_root,a.engine_root),sort_keys=True),flush=True)
if __name__=="__main__":main()
