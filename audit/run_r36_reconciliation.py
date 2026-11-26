"""Private, read-only readiness audit; never certifies prose by metrics."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
from worldroot.r36_reconciliation import run
from worldroot.editorial_guard import load_policy,validate_policy,POLICY_PATH
from worldroot.live_codex import load_registry
from worldroot.git_cycle import verify_episode,load
from worldroot.living_world import load_canonical
from worldroot.memory_continuity import recent_candidates
from worldroot.r35_longform import volume_check
from worldroot.presentation_guard import presentation_preflight
from audit.run_r35 import run as legacy_volume

root,ledger,out=map(Path,sys.argv[1:4])
protected=[root/"canon/HEAD.json",root/"ops/RESUME.json"]
before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in protected]
metrics=run(root,ledger,out)
print(json.dumps(metrics,ensure_ascii=False))
policy=load_policy();policy_stats=validate_policy(policy)
raw=POLICY_PATH.read_bytes()
policy_blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
assert policy_blob=="615151fc89228ddb222ea01613c23e977f8c418b"
assert {r["id"] for r in policy["rules"]}=={"P"+str(i).zfill(2) for i in range(1,131)}
assert all(r["active"] for r in policy["rules"])
policy_report={**policy_stats,"git_blob":policy_blob,"enforcement":dict(Counter(r["enforcement"] for r in policy["rules"])),"core":sum(r["core"] for r in policy["rules"]),"rules":[{"id":r["id"],"title":r["title"],"enforcement":r["enforcement"],"evidence":r["evidence"],"status":"POLICY_METADATA_AND_REFERENCE_VERIFIED","individual_narrative_certification":False} for r in policy["rules"]]}
registry,registry_sha=load_registry(root)
overlay=registry.get("_natural_overlay")
assert overlay is not None
fields=Counter(v["status"] for p in overlay["profiles"].values() for v in p["fields"].values())
profile_report={"registry_sha256":registry_sha,"character_profiles":overlay["character_count"],"world_profiles":overlay["world_count"],"profile_count":len(overlay["profiles"]),"field_statuses":dict(fields),"manifest_verified":True,"semantic_certification":False}
head=load(root/"canon/HEAD.json")
entries,warnings=load_canonical(root,head)
assert not warnings and all(x["day"]<=head["day"] for x in entries)
# Author-facing retrospective probes; expected source lines selected from actual original narrative, not generated plot.
d579="LVI-C09-PI-D579-AUTHOR-SOURCE"
probes=[
("O presente romântico que Miren guardou para uma viagem futura",d579,75),
("Como terminou a entrega dos vizinhos de Garran no terminal civil",d579,365),
("Onde a aeronave pousou no posto civil de Halvern",d579,547),
("A construção autorizada da cobertura e escoamento para o abrigo",d579,767),
("Os protótipos de bancadas transportáveis entregues por Lucas",d579,843),
("Custódia da carta de Ordan sem abrir o envelope",d579,927),
("O instituto tinha setenta e dois hectares e setores científicos protegidos","LVI-C02-PIII-D544-AUTHOR-SOURCE",743),
("Os pesquisadores observavam vibrações sem abrir o Coração de Convergência","LVI-C06-PV-D568-AUTHOR-SOURCE",490),
("O nome de Velkar ainda não chegou ao Instituto AERÚN","LVI-C07-PIII-D571-AUTHOR-SOURCE",483),
("A conferência continental dependia da adesão livre dos convidados","LVI-C07-PI-D569-R2-AUTHOR-SOURCE",2193)]
retrieval=[]
for query,source,line in probes:
    hits=recent_candidates(entries,query,limit=80)
    rank=next((i for i,h in enumerate(hits,1) if h["source"]==source and h["line_start"]<=line<=h["line_end"]),None)
    assert all(h["day"]<=head["day"] for h in hits)
    retrieval.append({"query":query,"source":source,"line":line,"rank":rank})
retrospective={"questions":len(retrieval),"hit20":sum(x["rank"] is not None and x["rank"]<=20 for x in retrieval),"hit80":sum(x["rank"] is not None for x in retrieval),"rows":retrieval,"method":"Existing closed-source recent_candidates; retrospective question probes, not independent semantic evaluation"}
literary=legacy_volume(root)
latest=[]
for ident in (d579,"LVI-C09-PII-D580-AUTHOR-SOURCE"):
    draft,_=verify_episode(root,ident)
    previous=load(root/"canon/episodes"/(ident+".json"))["previous_episode_id"] if ident==d579 else d579
    option=load(root/"canon/episodes"/(previous+".json")).get("chosen_option",1)
    # Closure choice describes the next part; use the preceding closure.
    if type(option) is not int or not 1<=option<=5:raise ValueError("Missing valid retrospective choice")
    v=volume_check(draft.prose,draft.metadata["part"],option)
    presentation=presentation_preflight(draft.full_text)
    latest.append({"episode":ident,"source_status":"CLOSED" if ident==d579 else "PENDING_NOT_CLOSED","option":option,"volume":v,"presentation_status":presentation["status"],"presentation_errors":presentation["errors"]})
report={"policy":policy_report,"profiles":profile_report,"retrospective":retrospective,"literary_corpus":literary,"latest":latest,"semantic_certification":False,"canon_changed":False}
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in protected]
(out/"readiness-audit.json").write_text(json.dumps(report,ensure_ascii=False,sort_keys=True),encoding="utf-8")
print(json.dumps({"r36_readiness":{"policy":{k:v for k,v in policy_report.items() if k!="rules"},"profiles":profile_report,"retrieval":{k:v for k,v in retrospective.items() if k!="rows"},"corpus":{"episodes":literary["episodes"],"short_parts_detected":literary["short_parts_detected"],"source_files_verified":literary["source_files_verified"],"pre_break_mean":literary["pre_break_mean"],"r34_mean":literary["r34_mean"]},"latest":[{"episode":x["episode"],"status":x["source_status"],"words":x["volume"]["words"],"floor":x["volume"]["floor"],"volume_status":x["volume"]["status"],"presentation_status":x["presentation_status"]} for x in latest],"semantic_certification":False,"canon_changed":False}},ensure_ascii=False))
