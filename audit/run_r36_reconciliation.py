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

# Operational review of the existing ambiguity and field backlog, private staging only.
from worldroot.semantic_queue import seal,validate
from worldroot.semantic_local import verify_job
from worldroot.live_codex import norm
from worldroot.r36_reconciliation import sha
from copy import deepcopy
from collections import defaultdict
review=load(Path(sys.argv[4]))
assert review["canon_promotion"] is False and review["semantic_certification"] is False
packets={p["event_id"]:p for p in load(out/"event-review-packets.json")}
link_audit=load(out/"event-link-audit.json")
group={(x["event_id"],m["normalized_alias"]):m for x in link_audit for m in x["registry_mentions"] if len(m["entity_candidate_ids"])>1}
assert len(group)==188
source_cache={}
def literal(event_id,line):
    p=packets[event_id]
    if p["episode"] not in source_cache:
        d,m=verify_episode(root,p["episode"])
        assert m["original_readback_sha256"]==p["source_sha256"]
        source_cache[p["episode"]]=d.full_text.splitlines()
    lines=source_cache[p["episode"]]
    assert type(line) is int and 1<=line<=len(lines)
    return p,lines[line-1]
selected={}
for r in review["decisions"]:
    key=(r["event_id"],r["alias"]);m=group[key]
    p,line=literal(r["event_id"],r["line"])
    assert key not in selected and r["selected_id"] in m["entity_candidate_ids"]
    assert " "+r["alias"]+" " in " "+norm(line)+" "
    # Full-name evidence in same packet may be earlier than the alias match.
    assert abs(p["line"]-r["line"])<=64
    selected[key]={**r,"source_sha256":p["source_sha256"],"source_status":p["source_status"],"visibility":p["visibility"],"evidence_sha256":sha(line)}
ambiguities=[]
for key,m in group.items():
    p=packets[key[0]];r=selected.get(key)
    reason="Campo e Base Aurora preservados como registros distintos; a expressão compartilhada não comprova qual nível da instalação é referido." if key[1]=="campo aurora" else "Evidência insuficiente neste lote para atribuir o referente."
    ambiguities.append({"event_id":key[0],"alias":key[1],"candidate_ids":m["entity_candidate_ids"],"source_lines":m["source_lines"],"source_sha256":p["source_sha256"],"source_status":p["source_status"],"visibility":p["visibility"],"review":r,"disposition":"EDITORIAL_REFERENT_CANDIDATE" if r else "HELD_IDENTITY_REVIEW", "reason":r["reason"] if r else reason,"canon_promotion":False,"semantic_certification":False})
# Exact field names only; no inferred alias mappings or projection writes.
pending={(i,k) for i,p in overlay["profiles"].items() for k,v in p["fields"].items() if v["status"]=="PENDENTE_FONTE"}
assert len(pending)==3448
jobs_by_field=defaultdict(list);jobs_all=[]
for line in (out/"jobs.jsonl").read_text(encoding="utf-8").splitlines():
    j=verify_job(json.loads(line));jobs_all.append(j)
    for t in j["targets"]:
        key=(t["entity_id"],t["field"])
        if key in pending:jobs_by_field[key].append({"job_id":j["job_id"],"original_id":t["original_id"],"source_status":j["source_status"]})
proposals={}
for r in review["fields"]:
    key=(r["entity_id"],r["field"])
    assert key in pending and key not in proposals
    p,line=literal(r["event_id"],r["line"])
    assert p["source_status"]=="CLOSED" and abs(p["line"]-r["line"])<=64
    proposals[key]={**r,"source_sha256":p["source_sha256"],"source_status":p["source_status"],"visibility":p["visibility"],"evidence_sha256":sha(line),"current_state":False,"canon_promotion":False}
field_queue=[{"entity_id":i,"field":k,"ledger_candidates":jobs_by_field.get((i,k),[]),"proposal":proposals.get((i,k)),"status":"EDITORIAL_CANDIDATE" if (i,k) in proposals else "EXACT_LEDGER_CANDIDATES" if (i,k) in jobs_by_field else "NO_EXACT_FIELD_MATCH","canon_promotion":False} for i,k in sorted(pending)]
# Real source-bound adversarial validator calls, not simulated inference.
j=next(x for x in jobs_all if x["source_status"]=="CLOSED" and len(x["targets"])==1)
target=j["targets"][0]
base={"job_id":j["job_id"],"executor":"ADVERSARIAL_FIXTURE","model_revision":"FIXTURE_NOT_MODEL","source_role":"UNCERTAIN","role_reason":"Fixture only, not a semantic judgment","decisions":[{**target,"verdict":"UNKNOWN","reason":"Fixture only","claim":"","evidence":"","current_state":False}]}
validate(j,base)
attacks=[("current_state_string",{"current_state":"true"}),("current_state_integer",{"current_state":1}),("current_state_null",{"current_state":None}),("null_reason",{"reason":None}),("wrong_entity",{"entity_id":"UNKNOWN_ID"}),("wrong_field",{"field":"UNKNOWN_FIELD"}),("wrong_id",{"original_id":True}),("unsupported_claim",{"verdict":"SUPPORTED","claim":"invented","evidence":"not in source"})]
blocked=[]
for name,patch in attacks:
    bad=deepcopy(base);bad["decisions"][0].update(patch)
    try:validate(j,bad)
    except ValueError:blocked.append(name)
    else:raise AssertionError("Adversarial review accepted: "+name)
# Public timeline excludes private/backstage events and the unclosed D580.
from worldroot.r36_core import temporal_events
with __import__("sqlite3").connect((root/"canon/state.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as db:
    public_ids={x[0] for x in db.execute("SELECT event_id FROM events WHERE visibility='PUBLICO'")}
public=temporal_events(root,580,limit=200)
assert public and all(x["event_id"] in public_ids and x["day"]<=579 for x in public)
# Audit the existing release gates; independent semantic review remains unavailable.
operational={"identity_groups":len(ambiguities),"editorial_referent_candidates":len(selected),"held_identity_groups":len(group)-len(selected),"referent_candidates_by_id":dict(Counter(r["selected_id"] for r in selected.values())),"pending_fields":len(pending),"pending_fields_with_exact_ledger_matches":len(jobs_by_field),"field_ledger_targets":sum(len(v) for v in jobs_by_field.values()),"field_proposals":len(proposals),"pending_fields_without_exact_ledger_match":len(pending)-len(jobs_by_field),"adversarial_review_cases_blocked":len(blocked),"public_timeline_rows_checked":len(public),"release_decision":"HOLD_PRODUCTION","independent_semantic_certified":0,"canon_promotions":0}
for name,obj in (("identity-editorial-review.json",ambiguities),("pending-field-priority.json",field_queue),("operational-release-gate.json",operational)):
    (out/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True),encoding="utf-8")
assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in protected]
print(json.dumps({"r36_operational":operational},ensure_ascii=False))
