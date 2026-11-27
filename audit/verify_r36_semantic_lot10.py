"""R36 lot 10: targeted historical field and scene identity recovery."""
import hashlib,json
from pathlib import Path
from worldroot.natural_codex import validate_fields,git_blob,public_fields
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(p): return json.loads(p.read_bytes())
ar=Path("archive"); st=Path("engine/editorial/codex-staging")
p7=st/"r36-multidimensional-lot-07-semantic-proposals.json"
p8=st/"r36-multidimensional-lot-08-result.json"
p9=st/"r36-multidimensional-lot-09-result.json"
inp=st/"r36-multidimensional-lot-10-input.json"
assert sha(p7.read_bytes())=="21c995eecd942ad9fc68baae6a054125fb53fd19bbcd618680bea1b045f6bc92"
assert sha(p8.read_bytes())=="0aa9937c924c486c384bd735618942b3476eaa29d629867f9c63f0caa365b581"
assert sha(p9.read_bytes())=="d27e1419c4608893aac646703addc1d95f1dda10e5e837651001e1e30b392a35"
p,b,n,d=map(load,(p7,p8,p9,inp))
assert d["base"]=="e42f57281e31b95a4d67e3d11cc91e68d295d98e" and d["archive"]==b["archive"]==p["archive"]==n["archive"]
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
previous={(x["id"],x["field"]) for x in p["observations"]+b["observations"]+b["new_candidate_observations"]+n["observations"]}
assert len(previous&pending)==105
inv=load(st/"r36-multidimensional-lot-02-inventory.json")
idx=load(st/"r36-multidimensional-lot-06-corpus-index.json")
src={x["episode"]:x for x in inv["closed_episode_inventory"]}
hashes={x["source"]:x["sha256"] for x in idx["sources"]}
cache={}
def lines(s):
    if s not in cache:
        if s=="D001-D383":
            raw=b"".join(z.read_bytes() for z in sorted((ar/"history/sources").glob("01*.part-*")))
            assert sha(raw)=="bb43d493ef3c28391345af7cd319e62af2f99f4f51b417bebb129fad6786cc4b"
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
nom={x["target"] for x in b["nominal_proposals"]}
occ={o["occurrence_id"] for v in b["descriptive_occurrences"].values() for o in v}
dec_ids=set()
for o in d["context_decisions"]:
    scope(o); ident=o["id"]; assert ident not in dec_ids; dec_ids.add(ident)
    if o["classification"]=="HISTORICAL_LINK_PROPOSED_NO_ALIAS": assert ident in nom and len(o["sources"])>=2
    else: assert o["classification"]=="SCENE_ROLE_ONLY" and ident in occ
    for s in o["sources"]: checks+=verify(s["source"],s["anchors"])
counts={"new_distinct_pending_fields":len(seen),"official_fields":sum(i in official for i,k in seen),"candidate_fields":sum(i in cand for i,k in seen),"distinct_targets":len({i for i,k in seen}),"pending_baseline":len(pending),"prior_distinct_pending_proposals":len(previous&pending),"pending_without_proposal_after_lot10":len(pending-previous-seen),"historical_identity_links_proposed":sum(x["classification"]=="HISTORICAL_LINK_PROPOSED_NO_ALIAS" for x in d["context_decisions"]),"scoped_descriptor_decisions":sum(x["classification"]=="SCENE_ROLE_ONLY" for x in d["context_decisions"]),"literal_checks":checks,"canon_fields_promoted":0}
out={"schema":"worldroot-r36-semantic-lot-10-result-v1","base":d["base"],"archive":d["archive"],"head_day":579,"sequence":50,"scope":"AUTHOR_ONLY","status":"AUTHOR_GATE_PENDING","production_hold":True,"canon_changed":False,"semantic_certification":False,"input_sha256":sha(inp.read_bytes()),"lot09_sha256":sha(p9.read_bytes()),"lot08_sha256":sha(p8.read_bytes()),"lot07_sha256":sha(p7.read_bytes()),"counts":counts,"observations":d["observations"],"context_decisions":d["context_decisions"]}
path=st/"r36-multidimensional-lot-10-result.json"
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert load(path)==out
print("R36_LOT10",json.dumps({"counts":counts,"sha256":sha(path.read_bytes())},sort_keys=True))
