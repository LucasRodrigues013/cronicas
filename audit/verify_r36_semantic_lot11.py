"""R36 lot 11: targeted historical field and scene identity recovery."""
import hashlib,json
from pathlib import Path
from worldroot.natural_codex import validate_fields,git_blob,public_fields
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(p): return json.loads(p.read_bytes())
ar=Path("archive"); st=Path("engine/editorial/codex-staging")
p7=st/"r36-multidimensional-lot-07-semantic-proposals.json"
p8=st/"r36-multidimensional-lot-08-result.json"
p9=st/"r36-multidimensional-lot-09-result.json"
p10=st/"r36-multidimensional-lot-10-result.json"
inp=st/"r36-multidimensional-lot-11-input.json"
assert sha(p7.read_bytes())=="21c995eecd942ad9fc68baae6a054125fb53fd19bbcd618680bea1b045f6bc92"
assert sha(p8.read_bytes())=="0aa9937c924c486c384bd735618942b3476eaa29d629867f9c63f0caa365b581"
assert sha(p9.read_bytes())=="d27e1419c4608893aac646703addc1d95f1dda10e5e837651001e1e30b392a35"
assert sha(p10.read_bytes())=="98e2dcd05936f8b9d60f5d550018e7f4cad6f1ed1be903216b157a17efdacd2a"
p,b,n,t,d=map(load,(p7,p8,p9,p10,inp))
assert d["base"]=="182a8c1ed41bebc045e3cb3f7eb67dd7b72fce83" and d["archive"]==b["archive"]==p["archive"]==n["archive"]==t["archive"]
assert d["head_day"]==579 and d["sequence"]==50 and d["production_hold"] and not d["canon_changed"] and not d["semantic_certification"]
assert b["counts"]["official_packets"]==192 and b["counts"]["candidate_packets"]==24 and b["counts"]["descriptive_occurrences"]==751
reg=ar/"editorial/registries"
official={x["id"]:x for x in load(reg/"r35-natural-completion-d579-v14.json")["characters"]+load(reg/"r35-world-completion-d579-v12.json")["records"]}
cand={}
for f in ("04-native-candidates","05-discoveries"):
    q=load(st/("r36-multidimensional-lot-"+f+".json"))
    cand.update({r["id"]:r for r in q["characters"]+q["records"]})
assert len(official)==192 and len(cand)==24
pending={(x["id"],k) for x in (official|cand).values() for k,v in x["fields"].items() if v["status"]=="PENDENTE_FONTE"}
assert pending=={(x["id"],k) for x in b["profile_review_packets"]+b["candidate_review_packets"] for k in x["pending_fields"]}
assert len(pending)==3897
previous={(x["id"],x["field"]) for x in p["observations"]+b["observations"]+b["new_candidate_observations"]+n["observations"]+t["observations"]}
assert len(previous&pending)==164
inv=load(st/"r36-multidimensional-lot-02-inventory.json")
idx=load(st/"r36-multidimensional-lot-06-corpus-index.json")
src={x["episode"]:x for x in inv["closed_episode_inventory"]}
hashes={x["source"]:x["sha256"] for x in idx["sources"]}
historical={x["path"]:x for x in inv["source_inventory"]}
cache={}
def lines(s):
    if s not in cache:
        if s=="D001-D383":
            raw=b"".join(z.read_bytes() for z in sorted((ar/"history/sources").glob("01*.part-*")))
            assert sha(raw)=="bb43d493ef3c28391345af7cd319e62af2f99f4f51b417bebb129fad6786cc4b"
        elif s in historical:
            e=historical[s]; raw=(ar/e["path"]).read_bytes()
            assert git_blob(raw)==e["blob"]
        else:
            e=src[s]; raw=(ar/e["source_path"]).read_bytes()
            assert git_blob(raw)==e["source_blob"]
            rr=(ar/"canon/episodes"/(s+".json")).read_bytes()
            assert git_blob(rr)==e["receipt_blob"] and json.loads(rr)["story_sha256"]==sha(raw)
        assert hashes[s]==sha(raw)
        cache[s]=raw.decode("utf-8").split("\n")
    return cache[s]
def verify(s,anchors):
    ll=lines(s)
    assert anchors
    for a in anchors:
        k=a["line"]; assert type(k) is int and 1<=k<=len(ll) and ll[k-1]==a["anchor"] and a["anchor"].strip(),(s,k)
        a["anchor_sha256"]=sha(a["anchor"].encode())
    return len(anchors)
def scope(o): assert o["scope"]=="AUTHOR_ONLY" and o["status"]=="AUTHOR_GATE_PENDING"
seen=set(); checks=0
for o in d["observations"]:
    scope(o); k=(o["id"],o["field"])
    assert k in pending and k not in previous and k not in seen,k
    seen.add(k); checks+=verify(o["source"],o["anchors"])
    f={o["field"]:{"value":o["value"],"status":"RECUPERADO","scope":"AUTHOR_ONLY","origin":o["anchors"],"justification":"Historical staging; author gate pending; not a present-state assertion."}}
    validate_fields(f); assert not public_fields(f)
dec_ids=set()
for o in d["conflicts"]:
    scope(o); ident=o["id"]; assert ident not in dec_ids; dec_ids.add(ident)
    assert o["classification"]=="CONFLICT_GUARD" and o["decision"] and o["sources"]
    for src_item in o["sources"]: checks+=verify(src_item["source"],src_item["anchors"])
counts={"new_distinct_pending_fields":len(seen),"official_fields":sum(i in official for i,k in seen),"candidate_fields":sum(i in cand for i,k in seen),"distinct_targets":len({i for i,k in seen}),"pending_baseline":len(pending),"prior_distinct_pending_proposals":len(previous&pending),"pending_without_proposal_after_lot11":len(pending-previous-seen),"conflict_guards":len(d["conflicts"]),"literal_checks":checks,"canon_fields_promoted":0}
out={"schema":"worldroot-r36-semantic-lot-11-result-v1","base":d["base"],"archive":d["archive"],"head_day":579,"sequence":50,"scope":"AUTHOR_ONLY","status":"AUTHOR_GATE_PENDING","production_hold":True,"canon_changed":False,"semantic_certification":False,"input_sha256":sha(inp.read_bytes()),"lot10_sha256":sha(p10.read_bytes()),"lot09_sha256":sha(p9.read_bytes()),"lot08_sha256":sha(p8.read_bytes()),"lot07_sha256":sha(p7.read_bytes()),"counts":counts,"observations":d["observations"],"conflicts":d["conflicts"]}
path=st/"r36-multidimensional-lot-11-result.json"
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert load(path)==out
print("R36_LOT11",json.dumps({"counts":counts,"sha256":sha(path.read_bytes())},sort_keys=True))
