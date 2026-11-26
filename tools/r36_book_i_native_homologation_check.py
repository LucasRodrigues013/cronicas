"""Book I E/F read-only native R36 verification; no semantic certification."""
import json, hashlib, sqlite3, sys, tempfile, copy
from pathlib import Path
from collections import Counter
from worldroot.semantic_queue import jobs, validate, reconcile
from worldroot.semantic_local import verify_job, availability
from worldroot.arquiteto import discover, validate_legacy_recovery
from worldroot.live_codex import load_registry, sync

root, audit, staging = map(Path, sys.argv[1:4])
p=staging/"editorial/codex-staging"
read=lambda path:json.loads(path.read_text(encoding="utf-8"))
receipt=read(p/"r36-book-i-stage-e-consolidated-handoff.json")
assert not receipt["canon_changed"] and not receipt["production_activated"]
exchange=read(p/"r36-book-i-stage-e-semantic-queue-first-pass.json")
discovery=read(p/"r36-book-i-stage-e-arquiteto-discovery-01.json")
graph=read(p/"r36-book-i-stage-e-profile-graph-01.json")
for item in receipt["receipts"]:
    raw=(staging/item["path"]).read_bytes()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==item["blob"]
source=(root/"history/sources/01_DIA_001_A_383_FONTE_LITERAL.txt.part-001").read_text(encoding="utf-8")
book="\n".join(source.split("\n")[:40845]); lines=book.splitlines()
assert hashlib.sha256(book.encode()).hexdigest()==discovery["source_sha256"]
ledger=[r for i in range(1,5) for r in read(audit/"editorial/codex-staging/results/exact-context-ledger-v1"/f"batch-{i:03d}.json") if r["original_id"]<=307]
assert len(ledger)==307 and all(lines[r["line"]-1]==r["anchor"] for r in ledger)
queue={j["job_id"]:verify_job(j) for j in jobs(ledger)}
answers={j["job_id"]:j["answer"] for j in exchange["jobs"]}
assert set(queue)==set(answers) and len(queue)==236
for jid,j in queue.items(): validate(j,answers[jid])
registry,_=load_registry(root)
overlay=registry["_natural_overlay"]
native={x["id"]:x for x in discover(book,"book-i-d001-d090","LEGACY_MIXED",list(overlay["profiles"].values()))}
editorial={x["candidate"]["id"]:x["candidate"] for x in discovery["candidates"]}
assert native==editorial and len(native)==142
assert all(overlay["profiles"][x["entity_id"]]["fields"][x["field"]]["status"]=="PENDENTE_FONTE" for x in graph["field_proposals"])
assert all(lines[x["line"]-1]==x["anchor"] for x in graph["observations"]+graph["graph_edges"]+graph["roster"])
assert all(lines[e["line"]-1]==e["text"] for x in graph["field_proposals"] for e in x["evidence"])
# Verify native controls reject invalid admission and false independence, not fabricate reviewers.
j=next(iter(queue.values())); answer=answers[j["job_id"]]
def rejects(fn):
    try: fn()
    except ValueError: return True
    raise AssertionError("Invalid review accepted")
bad=copy.deepcopy(answer);bad["decisions"][0]["current_state"]=True
assert rejects(lambda:validate(j,bad))
assert rejects(lambda:reconcile(j,answer,answer))
assert rejects(lambda:validate_legacy_recovery(next(iter(native.values())),{},book))
protected=("canon/HEAD.json","ops/RESUME.json","history/sources/MANIFEST.json","editorial/registries/r35-living-overlay-manifest.json")
def snapshot(): return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
before=snapshot()
with tempfile.TemporaryDirectory() as tmp:
    one=Path(tmp)/"graph.sqlite";two=Path(tmp)/"restored.sqlite"
    first=sync(root,one); assert first==sync(root,one)
    with sqlite3.connect(one) as db,sqlite3.connect(two) as dest:
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.backup(dest)
        assert dest.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert list(db.iterdump())==list(dest.iterdump())
    assert first==sync(root,two)
assert snapshot()==before
print(json.dumps({"book_i_native_stage_e":"PASS","jobs":len(queue),"targets":len(ledger),"native_arquiteto_candidates":len(native),"field_proposals_checked":len(graph["field_proposals"]),"native_rejections":3,"projection_replay_restore":True,"projection_records":first["records"],"projection_events":first["events"],"local_inference":availability(),"independent_semantic_certified":0,"new_typed_events_admitted":0,"canon_changed":False},ensure_ascii=False))
