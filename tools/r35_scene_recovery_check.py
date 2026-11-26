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
