"""R36 lot 07: verify selected literal proposals, never reindex or promote."""
import hashlib,json
from pathlib import Path
from worldroot.natural_codex import CHAR_FIELDS,validate_fields,git_blob,public_fields
from worldroot.r36_multidimensional import verify_protected_profiles
def sha(b): return hashlib.sha256(b).hexdigest()
ar=Path("archive"); st=Path("engine/editorial/codex-staging")
d=json.loads((st/"r36-multidimensional-lot-07-semantic-proposals.json").read_bytes())
i=json.loads((st/"r36-multidimensional-lot-06-corpus-index.json").read_bytes())
inv=json.loads((st/"r36-multidimensional-lot-02-inventory.json").read_bytes())
assert d["base"]=="51e2f3b263cf8ffbf8e0c9b82a8476e1e584d26e" and d["archive"]==i["archive"]
assert d["head_day"]==579 and d["sequence"]==50 and d["production_hold"] and not d["canon_changed"] and not d["production_activated"] and not d["semantic_certification"]
assert set(d["label_triage"])==set(i["unresolved_speaker_labels"])
assert {x["id"] for x in d["zero_hit_triage"]}=={k for k,v in i["profiles"].items() if not v["mentions"]}
assert {x["id"] for x in d["profile_review_inventory"]}==set(i["profiles"])
reg=ar/"editorial/registries"
c=json.loads((reg/"r35-natural-completion-d579-v14.json").read_bytes())["characters"]
w=json.loads((reg/"r35-world-completion-d579-v12.json").read_bytes())["records"]
before={x["id"]:x["fields"] for x in c+w}
assert len(before)==192 and sum(map(len,before.values()))==5923
assert not verify_protected_profiles(before,json.loads(json.dumps(before)))
candidates=set()
for f in ("04-native-candidates","05-discoveries"):
    x=json.loads((st/("r36-multidimensional-lot-"+f+".json")).read_bytes())
    candidates.update(r["id"] for r in x["characters"]+x["records"])
assert len(candidates)==24
assert {x['id'] for x in d['candidate_review_inventory']}==candidates
source_map={x["path"]:(x["path"],x["blob"],None) for x in inv["source_inventory"]}
source_map.update({x["episode"]:(x["source_path"],x["source_blob"],x["receipt_blob"]) for x in inv["closed_episode_inventory"]})
hashes={x["source"]:x["sha256"] for x in i["sources"]}
cache={}
def lines(source):
    if source not in cache:
        if source=="D001-D383":
            raw=b"".join(p.read_bytes() for p in sorted((ar/"history/sources").glob("01*.part-*")))
        else:
            path,blob,receipt=source_map[source]
            raw=(ar/path).read_bytes()
            assert git_blob(raw)==blob,source
            if receipt:
                rec=(ar/"canon/episodes"/(source+".json")).read_bytes()
                assert git_blob(rec)==receipt and json.loads(rec)["story_sha256"]==sha(raw),source
        if source in hashes: assert sha(raw)==hashes[source],source
        cache[source]=raw.decode("utf-8").split("\n")
    return cache[source]
errors=[];checked=0
def anchor(source,a):
    global checked
    l=lines(source)
    n=a["line"]
    if not (type(n) is int and 1<=n<=len(l) and l[n-1]==a["anchor"] and a["anchor"].strip()):
        errors.append({"source":source,"line":n,"reason":"literal mismatch"})
    else: checked+=1
for o in d["observations"]:
    assert o["id"] in before or o["id"] in candidates
    assert o["status"]=="AUTHOR_GATE_PENDING" and o["scope"]=="AUTHOR_ONLY" and o["anchors"]
    if o["id"] in before: assert o["field"] in before[o["id"]],o["id"]
    f={o["field"]:{"value":o["value"],"status":"RECUPERADO","scope":"AUTHOR_ONLY","origin":o["anchors"],"justification":"Historical staging; author gate pending."}}
    validate_fields(f)
    assert not public_fields(f)
    for a in o["anchors"]: anchor(o["source"],a)
for label,x in d["label_triage"].items():
    old=i["unresolved_speaker_labels"][label]
    assert not x["activate_alias"] and not x["semantic_resolution"]
    assert x["first_anchor_sha256"]==old["first_anchor_sha256"]
    l=lines(old["first_source"]); n=old["first_line"]
    if sha(l[n-1].encode())!=old["first_anchor_sha256"]: errors.append({"label":label,"reason":"index anchor mismatch"})
    else: checked+=1
    if "proposal" in x:
        p=x["proposal"]
        assert not p["activate_alias"] and p["scope"]=="AUTHOR_ONLY" and p["status"]=="AUTHOR_GATE_PENDING"
        for a in p["anchors"]: anchor(p["source"],a)
print("R36_LOT07",json.dumps({"counts":d["counts"],"anchor_checks":checked,"errors":errors,"sha256":sha((st/"r36-multidimensional-lot-07-semantic-proposals.json").read_bytes())},ensure_ascii=False))
assert not errors,errors
