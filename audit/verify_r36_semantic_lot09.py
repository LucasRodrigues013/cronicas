"""R36 lot 09: adjudicate only newly recovered historical pending fields."""
import hashlib, json
from pathlib import Path
from worldroot.natural_codex import validate_fields, git_blob, public_fields
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(p): return json.loads(p.read_bytes())
ar=Path("archive")
st=Path("engine/editorial/codex-staging")
p8=st/"r36-multidimensional-lot-08-result.json"
p7=st/"r36-multidimensional-lot-07-semantic-proposals.json"
inp=st/"r36-multidimensional-lot-09-input.json"
assert git_blob(p8.read_bytes())=="bfb0e6691b76aa4b5fc25276637b0521850b26a8"
assert sha(p7.read_bytes())=="21c995eecd942ad9fc68baae6a054125fb53fd19bbcd618680bea1b045f6bc92"
b=load(p8); p=load(p7); d=load(inp)
assert d["base"]=="52df4efa6ff8ad1f1eb855df0241ab6bf13180a9" and d["archive"]==b["archive"]==p["archive"]
assert d["head_day"]==b["head_day"]==579 and d["sequence"]==b["sequence"]==50
assert d["production_hold"] and not d["canon_changed"] and not d["semantic_certification"]
assert b["counts"]["official_packets"]==192 and b["counts"]["candidate_packets"]==24 and b["counts"]["descriptive_occurrences"]==751
reg=ar/"editorial/registries"
official={x["id"]:x for x in load(reg/"r35-natural-completion-d579-v14.json")["characters"]+load(reg/"r35-world-completion-d579-v12.json")["records"]}
cand={}
for f in ("04-native-candidates","05-discoveries"):
    x=load(st/("r36-multidimensional-lot-"+f+".json"))
    cand.update({r["id"]:r for r in x["characters"]+x["records"]})
assert len(official)==192 and len(cand)==24
cards=official|cand
pending={(x["id"],k) for x in cards.values() for k,v in x["fields"].items() if v["status"]=="PENDENTE_FONTE"}
packet_pending={(x["id"],k) for x in b["profile_review_packets"]+b["candidate_review_packets"] for k in x["pending_fields"]}
assert pending==packet_pending and len(pending)==3897
previous={(x["id"],x["field"]) for x in p["observations"]+b["observations"]+b["new_candidate_observations"]}
raw=b"".join(z.read_bytes() for z in sorted((ar/"history/sources").glob("01*.part-*")))
assert sha(raw)=="bb43d493ef3c28391345af7cd319e62af2f99f4f51b417bebb129fad6786cc4b"
ll=raw.decode("utf-8").split("\n")
def verify(o):
    assert o["source"]=="D001-D383" and o["scope"]=="AUTHOR_ONLY" and o["status"]=="AUTHOR_GATE_PENDING"
    assert o["anchors"]
    for a in o["anchors"]:
        n=a["line"]; assert 1<=n<=len(ll) and ll[n-1]==a["anchor"] and a["anchor"].strip(),(o["id"],n)
        a["anchor_sha256"]=sha(a["anchor"].encode())
    return len(o["anchors"])
seen=set(); checks=0
for o in d["observations"]:
    k=(o["id"],o["field"])
    assert k in pending and k not in previous and k not in seen,k
    seen.add(k); checks+=verify(o)
    f={o["field"]:{"value":o["value"],"status":"RECUPERADO","scope":"AUTHOR_ONLY","origin":o["anchors"],"justification":"Historical staging; author gate pending, not a present-state assertion."}}
    validate_fields(f); assert not public_fields(f)
for o in d["conflicts"]:
    assert o["kind"]=="CONFLICT_ONLY"; checks+=verify(o)
prior_pending=previous&pending
counts={"new_distinct_pending_fields":len(seen),"official_fields":sum(i in official for i,k in seen),"candidate_fields":sum(i in cand for i,k in seen),"distinct_targets":len({i for i,k in seen}),"pending_baseline":len(pending),"prior_distinct_pending_proposals":len(prior_pending),"pending_without_proposal_after_lot09":len(pending-prior_pending-seen),"conflict_guards":len(d["conflicts"]),"literal_checks":checks,"canon_fields_promoted":0}
out={"schema":"worldroot-r36-semantic-lot-09-result-v1","base":d["base"],"archive":d["archive"],"head_day":579,"sequence":50,"scope":"AUTHOR_ONLY","status":"AUTHOR_GATE_PENDING","production_hold":True,"canon_changed":False,"semantic_certification":False,"input_sha256":sha(inp.read_bytes()),"lot08_sha256":sha(p8.read_bytes()),"lot07_sha256":sha(p7.read_bytes()),"historical_source_sha256":sha(raw),"counts":counts,"observations":d["observations"],"conflicts":d["conflicts"]}
path=st/"r36-multidimensional-lot-09-result.json"
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert load(path)==out
print("R36_LOT09",json.dumps({"counts":counts,"sha256":sha(path.read_bytes())},sort_keys=True))
