import json, pathlib, hashlib, time
from worldroot import epic_narrative as ep
from worldroot import living_world as lw
from worldroot import history_index as hist
root=pathlib.Path("archive")
head=lw.read_obj(root/"canon/HEAD.json")
before={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in ["canon/HEAD.json","ops/RESUME.json"]}
def report(name,f):
    start=time.monotonic()
    try:
        value=f()
        print(json.dumps({"test":name,"elapsed_s":round(time.monotonic()-start,3),**value},ensure_ascii=False,sort_keys=True),flush=True)
    except Exception as exc:
        print(json.dumps({"test":name,"error_type":type(exc).__name__,"error":str(exc)[:250]},ensure_ascii=False),flush=True)
def projection():
    p=ep.planning_brief(root,head)
    return {"status":p["status"],"coverage":p["coverage"],"promises":len(p["promises"]),"linked_source_match":sum(x["evidence_status"]=="SOURCE_MATCH" for x in p["promises"]),"warnings":len(p["warnings"]),"seed_count":p["counts"]["seed_count"],"canon_changed":p["canon_changed"]}
def history():
    hist.build(root)
    v=hist.verify(root,with_source_checks=True)
    res=hist.search(root,"Aeldric esperava diferente",limit=6,role="ASSISTANT_RESPONSE",match_mode="all")
    return {"verified":True,"index_keys":sorted(v.keys()),"phrase_hits":res["result_count"],"historical_status":res["limitation"]}
def micro():
    rows=json.loads(pathlib.Path("audit/r29-microepisodes.json").read_text(encoding="utf-8"))
    reports=[]
    for row in rows:
        prose="## I — "+row["title"]+"\n\n"+row["prose"]
        rr=ep.review(prose,head,root)
        reports.append(rr)
    return {"count":len(reports),"advisory_only":sum(x["status"]=="ADVISORY_ONLY" for x in reports),"cards_not_supplied":sum(x["card_status"]=="NOT_SUPPLIED" for x in reports),"narrative_scene_refs":sum(x["signals"]["scene_count"] for x in reports),"fantasy_scene_refs":sum(x["signals"]["fantasy_scene_references"] for x in reports),"relationship_scene_refs":sum(x["signals"]["relationship_scene_references"] for x in reports),"meta_signals":sum(bool(x["signals"]["meta_language"]) for x in reports),"canon_changed_count":sum(x["canon_changed"] for x in reports)}
report("R29_ACTUAL_100_MICROEPISODES",micro)
report("R28_R29_LIVE_PROJECTION",projection)
report("HISTORICAL_FTS_VERIFICATION",history)
after={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in before}
print(json.dumps({"test":"HEAD_RESUME_READ_ONLY","unchanged":before==after,"head_day":head["day"]}),flush=True)
assert before==after
