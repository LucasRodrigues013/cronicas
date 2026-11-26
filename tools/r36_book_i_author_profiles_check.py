"""Validate author-authorized Book I profile recovery in an isolated archive checkout."""
import json,hashlib,sys,tempfile,sqlite3
from pathlib import Path
from worldroot.live_codex import load_registry,sync,all_records
from worldroot.natural_codex import validate_fields,CHAR_FIELDS
root,staging=map(Path,sys.argv[1:3])
p=root/"editorial/registries"
manifest=p/"r35-living-overlay-manifest.json"
old=manifest.read_bytes()
candidate=(p/"r35-living-overlay-manifest-book-i-review.json").read_bytes()
patch=json.loads((staging/"editorial/codex-staging/r36-book-i-author-recovered-profiles-v2.json").read_text())
protected=[root/"canon/HEAD.json",root/"ops/RESUME.json",root/"history/sources/MANIFEST.json"]
before=[hashlib.sha256(x.read_bytes()).hexdigest() for x in protected]
base,_=load_registry(root)
old_profiles=base["_natural_overlay"]["profiles"]
expected={c["id"]:c for c in patch["existing_profiles"]}
assert len(expected)==17
try:
    manifest.write_bytes(candidate)
    registry,sha=load_registry(root)
    profiles=registry["_natural_overlay"]["profiles"]
    assert set(profiles)==set(old_profiles) and len(profiles)==192
    assert all(profiles[i]==expected.get(i,old_profiles[i]) for i in profiles)
    assert all(profiles[x["id"]]["fields"][x["field"]]==x["next"] for x in patch["changes"])
    assert len(patch["changes"])==52
    assert len(patch["candidate_profiles"])==14
    for c in patch["candidate_profiles"]:
        validate_fields(c["fields"],CHAR_FIELDS)
        assert c["id"] not in profiles
    astra=profiles["astra"]["fields"]
    assert "escuros" in astra["hair"]["value"] and astra["eyes"]["value"].startswith("Cinzentos")
    assert astra["age_biological"]["value"]==27
    assert astra["roles"]["status"]=="CANONICO"
    assert astra["height_cm"]["status"]=="PENDENTE_FONTE"
    assert "21h16" in astra["location"]["value"]
    record=next(r for r in all_records(registry) if r["id"]=="astra")
    public=record["natural_profile"]["fields"]
    assert "escuros" in public["hair"]["value"] and "knowledge" not in public
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/"graph.sqlite"; restored=Path(d)/"restore.sqlite"
        result=sync(root,db)
        assert sync(root,db)==result
        with sqlite3.connect(db) as src,sqlite3.connect(restored) as dst:
            src.backup(dst)
            assert dst.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
            assert list(src.iterdump())==list(dst.iterdump())
        assert sync(root,restored)==result
    assert before==[hashlib.sha256(x.read_bytes()).hexdigest() for x in protected]
finally:
    manifest.write_bytes(old)
print(json.dumps({"book_i_author_profile_overlay":"PASS","existing_profiles":len(profiles),"changed_profiles":len(expected),"changes":len(patch["changes"]),"separate_candidate_profiles":len(patch["candidate_profiles"]),"naming_review_bound":True,"astra_hair_verified":True,"private_knowledge_excluded":True,"projection_records":result["records"],"projection_events":result["events"],"replay_restore":True,"canon_changed":False,"semantic_certification":False},ensure_ascii=False))
