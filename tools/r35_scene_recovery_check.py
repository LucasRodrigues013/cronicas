import hashlib,json,sys,tempfile,time
from pathlib import Path
from worldroot.live_codex import load_registry,all_records,aliases
from worldroot.scene_context import build
from worldroot.semantic_queue import export
root=Path(sys.argv[1]);audit=Path(sys.argv[2]);head=json.loads((root/"canon/HEAD.json").read_text());start=time.perf_counter()
data,seal=load_registry(root);load_ms=round((time.perf_counter()-start)*1000,2);rows=list(all_records(data));overlay=data["_natural_overlay"]
assert overlay["character_count"]==96 and overlay["world_count"]==96
pack=json.loads((root/"editorial/codex-staging/r35-source-bound-regression-v1.json").read_text())
checked=0
for case in pack["cases"]:
    for s in case["sources"]:
        raw=(root/s["path"]).read_bytes()
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==s["blob"]
        lo,hi=s["lines"];assert "\n".join(raw.decode().splitlines()[lo-1:hi])==s["anchor"]
        checked+=1
assert aliases(rows,"Durghan",domain="Personagens")[0]["id"]=="chr-durghan-uzgor"
assert aliases(rows,"Uzgor")[0]["id"]=="org-uzgor"
assert aliases(rows,"Elyan",domain="Personagens")[0]["id"]=="chr-elyan-legiao"
req={"scene_plan":[{"scene":1,"purpose":"Durghan e Grazha, Uzgor"},{"scene":2,"purpose":"Elyan, Pedreira Oriental de Arvendell"},{"scene":3,"purpose":"Elion, Câmara de Origem"},{"scene":4,"purpose":"Halvern"}]}
start=time.perf_counter()
for _ in range(25):scope=build(req,rows,overlay)
scene_ms=round((time.perf_counter()-start)*1000/25,2)
s=scope["scenes"];assert "org-uzgor" in s[0]["direct_ids"]
assert "chr-durghan-uzgor" in s[0]["direct_ids"]
assert "place-pedreira-oriental-arvendell" in s[1]["direct_ids"]
assert "chr-elion-genese" in s[2]["direct_ids"]
assert "chr-durghan-uzgor" not in {x["id"] for x in s[3]["records"]}
assert "halvern-region" in s[3]["direct_ids"], s[3]["ambiguities"]
assert all(len(x["records"])<=24 for x in s)
elion=next(x for x in s[2]["records"] if x["id"]=="chr-elion-genese");assert "origin" not in elion["profile"]
with tempfile.TemporaryDirectory() as tmp:
    result=export(audit/"editorial/codex-staging/results/exact-context-ledger-v1",Path(tmp)/"jobs.jsonl")
    assert result["targets"]==9229
print(json.dumps({"head":head["day"],"registry_sha":seal,"characters":overlay["character_count"],"world_records":overlay["world_count"],"source_recall_cases":len(pack["cases"]),"exact_source_anchors":checked,"global_records":len(rows),"scene_counts":[len(x["records"]) for x in s],"registry_load_ms":load_ms,"four_scene_packet_ms_mean_25":scene_ms,"semantic_jobs":result,"scope":"REAL_PRIVATE_ARCHIVE_READ_ONLY; structural and source tests, not independent semantic certification"},ensure_ascii=False))


# Book I Stage D: real historical source and Arquiteto runtime smoke tests.
from worldroot.arquiteto import discover, validate_legacy_recovery
from worldroot.history_index import search
book_source=(root/"history/sources/01_DIA_001_A_383_FONTE_LITERAL.txt.part-001").read_text(encoding="utf-8")
book="\n".join(book_source.split("\n")[:40845])
assert "FIM DO LIVRO I" in book.splitlines()[-1]
profiles=list(overlay["profiles"].values())
candidates=discover(book,"book-i-d001-d090","LEGACY_MIXED",profiles)
assert candidates and all(1<=x["line"]<=40845 for x in candidates)
assert all(book.splitlines()[x["line"]-1]==x["anchor"] for x in candidates)
assert len({x["id"] for x in candidates})==len(candidates)
try:
    validate_legacy_recovery(candidates[0],{},book)
except ValueError:
    pass
else:
    raise AssertionError("Unreviewed legacy candidate unexpectedly admitted")
cases=[("razhka Grazha",8),("Néria Valmont",10),("Hadrin Fell",6),("Elira Voss",46),("Selene Arvost",5)]
recall=[]
for term,day in cases:
    result=search(root,term,limit=10,role="ASSISTANT_RESPONSE",day_hint=day)
    hits=[h for h in result["hits"] if h["line_start"]<=40845 and h["file_name"]=="01_DIA_001_A_383_FONTE_LITERAL.txt"]
    assert hits, term
    recall.append({"query":term,"book_i_hits":len(hits)})
print(json.dumps({"book_i_runtime":"PASS","candidates":len(candidates),"legacy_gate_rejects_unreviewed":True,"historical_recall":recall,"canon_changed":False,"semantic_certification":False},ensure_ascii=False))


# Book I Stage E: original ledger grouping and disposable projection replay/restore.
from worldroot.semantic_queue import jobs
from worldroot.live_codex import sync
import sqlite3
ledger_dir=audit/"editorial/codex-staging/results/exact-context-ledger-v1"
book_rows=[r for p in sorted(ledger_dir.glob("batch-*.json")) for r in json.loads(p.read_text()) if r["source"]=="history:01_DIA_001_A_383_FONTE_LITERAL.txt" and r["line"]<=40845]
assert len(book_rows)==307 and {r["original_id"] for r in book_rows}==set(range(1,308))
queue=list(jobs(book_rows))
assert sum(len(j["targets"]) for j in queue)==307 and len(queue)==236
assert all(book.splitlines()[r["line"]-1]==r["anchor"] for r in book_rows)
overlap=set(r["line"] for r in book_rows)&set(r["line"] for r in candidates)
def protected():
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ("canon/HEAD.json","ops/RESUME.json","history/sources/MANIFEST.json","editorial/registries/r35-living-overlay-manifest.json")}
before=protected()
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp); graph=folder/"graph.sqlite"; restored=folder/"restore.sqlite"
    first=sync(root,graph); second=sync(root,graph)
    assert first==second and first["head"]==head
    with sqlite3.connect(graph) as db, sqlite3.connect(restored) as dst:
        assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        db.backup(dst)
        assert dst.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert list(db.iterdump())==list(dst.iterdump())
    third=sync(root,restored)
    assert third==first
assert protected()==before
print(json.dumps({"book_i_stage_e":"PASS","ledger_targets":len(book_rows),"grouped_jobs":len(queue),"discovery_candidates":len(candidates),"overlapping_source_lines":len(overlap),"projection_replay_restore":True,"projection_records":first["records"],"projection_events":first["events"],"canon_changed":False,"semantic_certification":False},ensure_ascii=False))
