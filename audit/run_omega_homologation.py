"""Public-authorized development homologation on a pinned, already public archive.
Aggregate output only. No held-out evaluation, no inference, no original archive writes.
"""
import argparse
import hashlib
import json
import random
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path

from worldroot import deep_recovery as dr
from worldroot.history_index import read_verified_sources
from worldroot.git_cycle import verify_episode, review_deltas, canonical
from worldroot.r35_longform import volume_check
from worldroot.r33_runtime import prepare_from_request, verify_submission, verify_history
from worldroot.draft_inbox import archive_inbox
from worldroot.delivery_gate import audit_release
from worldroot.turn_continuity import audit_turn_handoff
from audit.run_r35 import run as replay_r35

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def measure(name, func):
    t = time.perf_counter()
    try:
        result = func()
        row = {"stage": name, "status": "PASS", **result}
    except Exception as exc:
        row = {"stage": name, "status": "FAIL", "error_type": type(exc).__name__}
    row["elapsed_seconds"] = round(time.perf_counter()-t, 6)
    print(json.dumps(row, sort_keys=True), flush=True)
    return row

def main(root):
    root = root.resolve()
    head = load(root/"canon/HEAD.json")
    resume = load(root/"ops/RESUME.json")
    ident = resume["latest_unclosed_draft"]["episode_id"]
    target = root/"episodes"/ident
    original = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [root/"canon/HEAD.json", root/"ops/RESUME.json",
                 target/"draft/narrativa_integral.md", root/"inbox"/(ident+".json"),
                 root/"preparations"/(ident+".json"), root/"requests"/(ident+".json")]}
    results = []
    def stage(name, f):
        row = measure(name, f)
        results.append(row)
        return row
    def sources():
        manifest, data = read_verified_sources(root)
        return {"logical_sources": len(data), "git_parts": sum(len(m["parts"]) for m,t in data),
                "bytes": manifest["total_source_bytes"],
                "lines": sum(len(t.splitlines()) for m,t in data),
                "raw_sha256_verified": True}
    stage("historical_sources", sources)
    def archived():
        total = ok = events = knowledge = 0
        for m in sorted((root/"episodes").glob("*/draft/manifesto_imutavel.json")):
            total += 1
            try:
                draft, manifest = verify_episode(root, m.parent.parent.name)
                event, know = review_deltas(root, m.parent.parent.name, draft)
                events += len(event); knowledge += len(know)
                ok += 1
            except Exception:
                pass
        return {"status": "PASS" if total and total == ok else "FAIL",
                "packages": total, "verified_packages": ok, "event_records": events,
                "knowledge_records": knowledge}
    stage("immutable_packages", archived)
    def literary():
        r = replay_r35(root)
        return {k:r[k] for k in ("episodes","source_files_verified","chapter_totals",
                    "short_parts_detected","pre_break_mean","r34_mean","semantic_certification")}
    stage("historical_r35_replay", literary)
    stage("historical_r33_receipts", lambda: verify_history(root))
    def pending():
        draft, manifest = verify_episode(root,ident)
        request = load(root/"requests"/(ident+".json"))
        result = volume_check(draft.prose,draft.metadata["part"],1)
        gate = audit_release(root,ident)
        handoff = audit_turn_handoff(root,ident,expected_head_id=head["episode_id"])
        return {"status":"PASS" if gate["release_allowed"] else "FAIL",
                "words":result["words"],"floor":result["floor"],
                "volume_status":result["status"],"paragraphs":result["paragraphs"],
                "scene_count":result["scenes"],"duplicate_word_share":result["duplicate_word_share"],
                "requested_memory_requirements":len(request["requirements"]),
                "declared_reviewed":len(request["reviewed"]),
                "release_allowed":gate["release_allowed"],"gate_checks":gate["checks"],
                "handoff":{k:v for k,v in handoff.get("checks",{}).items() if isinstance(v,bool)},
                "semantic_certification":False}
    stage("existing_full_episode_readback", pending)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        # Test the current code against the historical request and exact prose:
        # only the disposable copy has old target outputs removed.
        work=tmp/"archive"
        def copy():
            shutil.copytree(root,work,ignore=shutil.ignore_patterns(".git"))
            shutil.rmtree(work/"episodes"/ident)
            (work/"preparations"/(ident+".json")).unlink()
            return {"disposable":True}
        copy_result=stage("disposable_copy",copy)
        if copy_result["status"]=="PASS":
            request=load(work/"requests"/(ident+".json"))
            def prep():
                r=prepare_from_request(work,request)
                packet=load(work/"preparations"/(ident+".json"))
                mem=packet["memory"]
                return {"persisted":r["result"],"required":mem["required"],"verified":mem["verified"],
                        "critical_missing":len(mem["critical_missing"]),
                        "represented":len(packet["editorial_receipt"]["coverage"]["represented_rule_ids"]),
                        "editorial_budget":packet["editorial_receipt"]["budget_chars"],
                        "codex_bound":"universal_codex" in packet,"semantic_certification":False}
            p=stage("actual_request_current_preparation",prep)
            if p["status"]=="PASS":
                packet=load(work/"preparations"/(ident+".json"))
                payload=load(work/"inbox"/(ident+".json"))
                payload["r33_review"]["preparation_sha256"]=packet["preparation_sha256"]
                payload["r33_review"]["editorial_receipt_sha256"]=packet["editorial_receipt_sha256"]
                (work/"inbox"/(ident+".json")).write_bytes(canonical(payload))
                def submit():
                    r=verify_submission(work,head,payload)
                    return {"editorial_integrity":r["editorial"]["integrity_verified"],
                            "r34":"r34" in r,"r35":"r35" in r,"semantic_certification":False}
                s=stage("exact_historical_prose_current_submission",submit)
                if s["status"]=="PASS":
                    def archive():
                        r=archive_inbox(work,work/"inbox"/(ident+".json"))
                        return {"archive_status":r["status"],"changed_file_count":r["changed_file_count"]}
                    a=stage("disposable_archive",archive)
                    if a["status"]=="PASS":
                        def release():
                            r=audit_release(work,ident)
                            return {"status":"PASS" if r["release_allowed"] else "FAIL",
                                    "release_allowed":r["release_allowed"],"checks":r["checks"]}
                        stage("disposable_release",release)
                        stage("disposable_history",lambda:verify_history(work))
        db=tmp/"recovery.sqlite"
        def index():
            r=dr.build(root,db)
            return {"sources":len(r["coverage"]),"windows":sum(x["windows"] for x in r["coverage"]),
                    "manifest_verified":dr.verify_manifest(root,db),"bytes":db.stat().st_size}
        built=stage("full_historical_reindex",index)
        if built["status"]=="PASS":
            def retrieval():
                rng=random.Random(360079)
                cases=[]
                with sqlite3.connect(db) as conn:
                    source_names=[r[0] for r in conn.execute("SELECT DISTINCT source FROM evidence ORDER BY source")]
                    for source in source_names:
                        rows=conn.execute("SELECT line_start,line_end,anchor FROM evidence WHERE source=? AND role='Response' ORDER BY id",(source,)).fetchall()
                        rng.shuffle(rows)
                        for lo,hi,anchor in rows:
                            words=list(dict.fromkeys(w for w in dr.tokens(anchor) if len(w)>=6 and w not in dr.STOP))
                            if len(words)<8:
                                continue
                            cases.append((source,lo,hi," ".join(rng.sample(words,5))))
                            if sum(x[0]==source for x in cases)==6:
                                break
                assert len(cases)==36
                out={}
                for strategy in ("legacy","hybrid","contextual"):
                    durations=[]; top1=top20=0
                    for source,lo,hi,query in cases:
                        t=time.perf_counter()
                        hits=dr.retrieve(db,query,role="Response",limit=20,strategy=strategy)["hits"]
                        durations.append((time.perf_counter()-t)*1000)
                        def match(h):
                            return h["source"]==source and min(h["line_end"],hi)-max(h["line_start"],lo)+1>=3
                        top1+=bool(hits and match(hits[0]))
                        top20+=any(match(h) for h in hits)
                    durations.sort()
                    out[strategy]={"top1":top1,"top20":top20,
                                   "median_ms":round(durations[len(durations)//2],3),
                                   "p95_ms":round(durations[int(.95*(len(durations)-1))],3)}
                return {"cases":len(cases),"source_count":len(source_names),
                        "probe_type":"DEVELOPMENT_EXACT_WORD_SOURCE_OVERLAP_NOT_SEMANTIC",
                        "strategies":out}
            stage("historical_retrieval_same_workload",retrieval)
    unchanged=all(hashlib.sha256(p.read_bytes()).hexdigest()==s for p,s in original.items())
    print(json.dumps({"stage":"summary","passed":sum(x["status"]=="PASS" for x in results),
                      "failed":sum(x["status"]=="FAIL" for x in results),
                      "source_pins_unchanged":unchanged,"generation_executed":False,
                      "semantic_certification":False,"canon_changed":False},sort_keys=True),flush=True)
    return 0 if unchanged and all(x["status"]=="PASS" for x in results) else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive-root",type=Path,required=True)
    raise SystemExit(main(parser.parse_args().archive_root))
