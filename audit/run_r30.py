import json, pathlib, hashlib, time
from worldroot import living_world as lw, epic_narrative as ep, literary_experience as r30
from worldroot import history_index as hist
root=pathlib.Path("archive")
head=lw.read_obj(root/"canon/HEAD.json")
paths=["canon/HEAD.json","ops/RESUME.json","episodes/LVI-C08-PI-D574-AUTHOR-SOURCE/draft/narrativa_integral.md"]
def hashes():return {x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths}
before=hashes()
def emit(obj):print(json.dumps(obj,ensure_ascii=False,sort_keys=True),flush=True)
start=time.monotonic()
p=ep.planning_brief(root,head)
cold=time.monotonic()-start
start=time.monotonic()
p2=ep.planning_brief(root,head)
warm=time.monotonic()-start
emit({"test":"R30_PROJECTION","status":p["status"],"coverage":p["coverage"],"warnings":len(p["warnings"]),"cold_s":round(cold,3),"warm_s":round(warm,3),"same_result":p==p2,"cache":lw._normalized_body.cache_info()._asdict()})
assert p==p2 and not p["warnings"] and p["coverage"]["closed_episodes"]==44
reg=r30.source_registry(root,head)
bad=[(x["id"],o["field"]) for x in reg["characters"] for o in x["observations"] if not o["proof"]]
badsc=[x["id"] for x in reg["scenes"] if not x["proof"] or (x.get("author_feedback") and not x["feedback_proof"])]
emit({"test":"R30_REGISTRY_CORPUS","status":reg["status"],"characters":len(reg["characters"]),"observations":sum(len(x["observations"]) for x in reg["characters"]),"scenes":len(reg["scenes"]),"unverified_observations":bad,"unverified_scenes":badsc})
rows=json.loads(pathlib.Path("audit/r29-microepisodes.json").read_text())
reports=[r30.review("## I — "+x["title"]+"\n\n"+x["prose"],root,head) for x in rows]
emit({"test":"R30_100_MICROEPISODES","count":len(reports),"editorial_signals":sum(bool(x["metrics"]["meta_phrases"]) for x in reports),"olfactory_signals":sum(bool(x["metrics"]["sensory_signals"]["olfato"]) for x in reports),"relationship_references":sum(x["metrics"]["lucas_miren_reference"] for x in reports),"causal_cards_missing":sum(x["causality"]["status"]=="NOT_SUPPLIED" for x in reports),"canon_changes":sum(x["canon_changed"] for x in reports)})
literal=(root/paths[2]).read_text()
c=r30.choice_review(literal)
emit({"test":"R30_OLD_CHOICE","result":c})
emit({"test":"R30_HEAD_READONLY","unchanged":before==hashes(),"head_day":head["day"]})
assert len(reports)==100 and before==hashes() and reg["status"]=="SOURCE_MATCHES"
