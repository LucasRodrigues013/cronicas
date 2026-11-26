"""Private read-only source audit and materialization; never advance narrative HEAD."""
import hashlib,json,sqlite3,sys
from pathlib import Path
from worldroot.live_codex import load_registry,all_records,sync,aliases,norm
from worldroot.git_cycle import load,verify_db,verify_episode
from worldroot.r33_runtime import verify_history
from worldroot.r26_magic_catalog import validate_codex
root=Path(sys.argv[1]);head=load(root/"canon/HEAD.json")
before=(root/"canon/HEAD.json").read_bytes()
verify_db(root,head);verify_history(root)
data,registry_sha=load_registry(root)
rows=list(all_records(data))
assert len(rows)==len({r["id"] for r in rows})
assert len(data["arcane"]["index"])==1020 and len(data["arcane"]["schools"])==30
assert all(x["entity_id"] for x in data["legacy_character_links"])
magic=validate_codex();assert magic["status"]=="OK",magic.get("errors")
result=sync(root)
assert result["records"]==len(rows)
db_path=root/"canon/codex.sqlite"
with sqlite3.connect(db_path) as db:
    assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
    assert json.loads(db.execute("SELECT value FROM meta WHERE key='head'").fetchone()[0])==head
    first=db.execute("SELECT count(*) FROM codex_events").fetchone()[0]
second=sync(root)
assert second["events"]==first and second["records"]==result["records"]
# Existing reviews: confirmed archived spell-use annotations vs mere mentions.
closed=sorted((load(p) for p in (root/"canon/episodes").glob("*.json")),key=lambda r:r["sequence"])
uses=[];unresolved=[];reviewed_count=0
for c in closed:
    ep=c["episode_id"]
    path=root/"episodes"/ep/"review/fantasia_r26.json"
    if not path.is_file():continue
    draft,manifest=verify_episode(root,ep)
    assert manifest["original_readback_sha256"]==c["story_sha256"]
    review=load(path);reviewed_count+=1
    for u in review.get("editorial",{}).get("spell_uses",[]):
        anchor=u.get("literal_anchor","")
        spell=next((s for s in data["arcane"]["index"] if s["id"]==u.get("spell_id")),None)
        matches=aliases(rows,u.get("caster",""),domain="Personagens")
        if not spell or not anchor or anchor not in draft.prose or len(matches)!=1:
            unresolved.append({"episode":ep,"spell_id":u.get("spell_id"),"caster":u.get("caster"),"status":"REVIEW_REQUIRED"})
            continue
        offset=draft.prose.index(anchor)
        uses.append({"episode":ep,"day":c["metadata"]["day"],"entity_id":matches[0]["id"],"spell_id":spell["id"],"line":draft.prose[:offset].count("\n")+1,"literal_anchor":anchor,"source_sha256":c["story_sha256"],"learning_status":u.get("learning_status"),"status":"ARCHIVED_REVIEW_LITERAL_MATCH_REQUIRES_SEMANTIC_RECONCILIATION"})
feats=[]
for f in data["arcane"]["historical_feats"]:
    path=root/f["source"]["path"];anchor=f["source"]["literal_anchor"]
    text=path.read_text(encoding="utf-8") if path.is_file() else ""
    n=text.count(anchor)
    feats.append({"id":f["id"],"source_path":f["source"]["path"],"literal_anchor":anchor,"match_count":n,"source_sha256":hashlib.sha256(text.encode()).hexdigest() if text else None,"status":"LITERAL_MATCH_NOT_ACTOR_CERTIFICATION" if n else "MISSING_OR_DIFFERENT_SOURCE"})
assert (root/"canon/HEAD.json").read_bytes()==before
report={"head_day":head["day"],"sequence":head["sequence"],"head_unchanged":True,"registry_sha256":registry_sha,"records":result["records"],"graph_events":first,"repeat_sync_idempotent":True,"sqlite_integrity":True,"foreign_keys":True,"spell_catalog_validation":magic,"closed_episodes":len(closed),"r26_review_files":reviewed_count,"named_spell_use_matches":uses,"unresolved_spell_uses":unresolved,"historical_feat_matches":feats,"semantic_certification":False,"production_deployed":False}
dest=root/"editorial/codex-staging/results/live-codex-audit-d580.json"
dest.parent.mkdir(parents=True,exist_ok=True)
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"records":result["records"],"events":first,"closed_episodes":len(closed),"review_files":reviewed_count,"named_use_matches":len(uses),"unresolved_uses":len(unresolved),"feat_anchors_found":sum(f["match_count"]>0 for f in feats),"head_unchanged":True}))
