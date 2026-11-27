"""R36 lot 08: targeted semantic retrieval and native literal verification, no corpus reindex."""
import hashlib,json,re
from pathlib import Path
from collections import defaultdict,Counter
from worldroot.natural_codex import validate_fields,git_blob,public_fields
def sha(b): return hashlib.sha256(b).hexdigest()
ar=Path("archive"); st=Path("engine/editorial/codex-staging")
def load(p): return json.loads(p.read_bytes())
oldp=st/"r36-multidimensional-lot-07-semantic-proposals.json"
assert sha(oldp.read_bytes())=="21c995eecd942ad9fc68baae6a054125fb53fd19bbcd618680bea1b045f6bc92"
p=load(oldp); d=load(st/"r36-multidimensional-lot-08-input.json")
i=load(st/"r36-multidimensional-lot-06-corpus-index.json"); inv=load(st/"r36-multidimensional-lot-02-inventory.json")
assert d["base"]=="05a9bde61a9d60c79a9a4efc0cbe1cbebc246508" and d["archive"]==p["archive"]==i["archive"]
assert d["head_day"]==579 and d["sequence"]==50 and d["production_hold"] and not d["canon_changed"] and not d["production_activated"] and not d["semantic_certification"]
reg=ar/"editorial/registries"
cards={x["id"]:x for x in load(reg/"r35-natural-completion-d579-v14.json")["characters"]+load(reg/"r35-world-completion-d579-v12.json")["records"]}
cand={}
for f in ("04-native-candidates","05-discoveries"):
    x=load(st/("r36-multidimensional-lot-"+f+".json"))
    cand.update({r["id"]:r for r in x["characters"]+x["records"]})
assert len(cards)==192 and len(cand)==24
src={x["path"]:(x["path"],x["blob"],None) for x in inv["source_inventory"]}
src.update({x["episode"]:(x["source_path"],x["source_blob"],x["receipt_blob"]) for x in inv["closed_episode_inventory"]})
src["episodes/bootstrap/LV-C15-PI-D528/fonte_literal_drive_D528.txt"]=("episodes/bootstrap/LV-C15-PI-D528/fonte_literal_drive_D528.txt","d7016b84eb7477b0341904da616e06035292d8f3",None)
hashes={x["source"]:x["sha256"] for x in i["sources"]}; cache={}
def lines(s):
    if s not in cache:
        if s=="D001-D383": raw=b"".join(z.read_bytes() for z in sorted((ar/"history/sources").glob("01*.part-*")))
        else:
            path,blob,receipt=src[s]; raw=(ar/path).read_bytes(); assert git_blob(raw)==blob,s
            if receipt:
                rr=(ar/"canon/episodes"/(s+".json")).read_bytes()
                assert git_blob(rr)==receipt and load(ar/"canon/episodes"/(s+".json"))["story_sha256"]==sha(raw),s
        if s in hashes: assert sha(raw)==hashes[s],s
        cache[s]=raw.decode("utf-8").split("\n")
    return cache[s]
checked=0
def verify(s,a):
    global checked
    ll=lines(s); n=a["line"]
    assert type(n) is int and 1<=n<=len(ll) and ll[n-1]==a["anchor"] and a["anchor"].strip(),(s,n,ll[n-1] if 1<=n<=len(ll) else None,a["anchor"])
    checked+=1
def window(s,n,r=6):
    ll=lines(s); assert 1<=n<=len(ll)
    return [{"line":k,"anchor":ll[k-1],"anchor_sha256":sha(ll[k-1].encode())} for k in range(max(1,n-r),min(len(ll),n+r)+1) if ll[k-1].strip()]
def scope(x): assert x["scope"]=="AUTHOR_ONLY" and x["status"]=="AUTHOR_GATE_PENDING"
nom={x["label"]:x for x in d["nominal_proposals"]}
assert set(nom)=={k for k,v in p["label_triage"].items() if v["triage"]=="NAMED_OR_AMBIGUOUS_PENDING"}
for k,x in nom.items():
    scope(x); assert not x["activate_alias"] and x["source"]==p["label_triage"][k]["first_source"]
    for a in x["anchors"]: verify(x["source"],a)
    ll=lines(x["source"]); assert sha(ll[x["first_line"]-1].encode())==p["label_triage"][k]["first_anchor_sha256"]
previous={(o["id"],o["field"],o["source"],tuple(a["line"] for a in o["anchors"])) for o in p["observations"]}
for o in d["observations"]+d["new_candidate_observations"]:
    scope(o); assert o["anchors"]
    if o in d["observations"]:
        card=cards.get(o["id"]) or cand.get(o["id"]); assert card and o["field"] in card["fields"],(o["id"],o["field"])
        assert (o["id"],o["field"],o["source"],tuple(a["line"] for a in o["anchors"])) not in previous
    else: assert o["id"] in {x["target"] for x in nom.values()}|{"candidate:mara-vellen-r36"}
    for a in o["anchors"]: verify(o["source"],a)
    f={o["field"]:{"value":o["value"],"status":"RECUPERADO","scope":"AUTHOR_ONLY","origin":o["anchors"],"justification":"Historical staging, author gate pending."}}
    validate_fields(f); assert not public_fields(f)
zero={x["id"] for x in p["zero_hit_triage"] if x["status"]=="PENDENTE_FONTE"}
assert zero<={x["id"] for x in d["observations"]}
# Target only the 116 already indexed labels in closed episodes. No rebuild of lexical index.
generic={k:v for k,v in p["label_triage"].items() if v["triage"]=="DESCRIPTIVE_OR_UNCLASSIFIED_NO_GLOBAL_ID"}
assert len(generic)==116
speaker=re.compile(r"^\s*(?:>\s*)?\*\*([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 '-]{1,50})\s*—\*\*")
kin={"pai","mãe","filha","filho","pai de nelo","companheira de neris","companheira","companheiro"}
age={"senhora","menino","menina","criança","outra criança","rapaz","mulher","homem","garoto","jovem","velho","idosa","idoso","homem na multidão"}
ordinal={"outro","segundo","primeiro homem","segundo homem","primeiro vigia","segundo vigia"}
nonperson={"voz","controle","patrulha norte","autômato"}
occ=defaultdict(list)
for e in inv["closed_episode_inventory"]:
    s=e["episode"]; ll=lines(s); scene=None; scene_header=None; section=None
    for n,line in enumerate(ll,1):
        if re.match(r"^\s*#{1,5}\s+",line): section=n
        if re.match(r"^\s*(?:\*\*|<text[^>]*>)?DIA\s+\d{1,3}\b",line,re.I): scene=n; scene_header=line
        if re.match(r"^\s*(?:\*\*|<text[^>]*>)?DIA\s+\d{1,3}\b",line,re.I) is None and line.strip()=="---": scene=None; scene_header=None
        m=speaker.match(line)
        if not m: continue
        k=m[1].strip().casefold()
        if k not in generic: continue
        cat="RELATIONAL_DESCRIPTOR" if k in kin else "AGE_OR_PERSON_DESCRIPTOR" if k in age else "LOCAL_ORDINAL" if k in ordinal else "VOICE_GROUP_OR_NONPERSON_UNCERTAIN" if k in nonperson else "ROLE_OR_OTHER_DESCRIPTOR"
        occ[k].append({"source":s,"line":n,"anchor":line,"anchor_sha256":sha(line.encode()),"scene_heading_line":scene,"scene_heading":scene_header,"section_heading_line":section,"classification":cat,"occurrence_id":s+":"+str(n),"context":window(s,n,5),"global_identity":None,"identity_status":"PENDENTE_FONTE","scope":"AUTHOR_ONLY","source_role":"UNADJUDICATED"})
# Do not conflate all equal labels, even within a scene. Counts must reproduce prior index for target labels.
assert set(occ)==set(generic)
mismatch={k:{"indexed":v["count"],"retrieved":len(occ[k])} for k,v in generic.items() if v["count"]!=len(occ[k])}
# Some historic source labels may have appeared outside closed episode files; surface any discrepancy, never fabricate.
for k,v in generic.items():
    matches=[o for o in occ[k] if o["source"]==v["first_source"] and o["line"]==v["first_line"]]
    assert matches and matches[0]["anchor_sha256"]==v["first_anchor_sha256"],k
# Reuse exact existing profile anchors, not new name scan. Retrieval packets are not semantic findings.
packets=[]
newids={o["id"] for o in d["observations"]}; oldids={o["id"] for o in p["observations"]}
for ident,card in cards.items():
    profile=i["profiles"][ident]
    pending=sorted(k for k,v in card["fields"].items() if v["status"]=="PENDENTE_FONTE")
    chosen=[]
    for s,v in list(profile["sources"].items())[:2]:
        n=v["first_line"]; ll=lines(s)
        assert sha(ll[n-1].encode())==v["first_anchor_sha256"],(ident,s,n)
        chosen.append({"source":s,"line":n,"context":window(s,n,6),"source_role":"UNADJUDICATED"})
    packets.append({"id":ident,"pending_fields":pending,"contexts":chosen,"new_semantic_proposal":ident in newids,"prior_semantic_proposal":ident in oldids,"status":"AUTHOR_GATE_PENDING","scope":"AUTHOR_ONLY","semantic_certification":False})
candidate_packets=[]
for ident,card in cand.items():
    pending=sorted(k for k,v in card["fields"].items() if v["status"]=="PENDENTE_FONTE")
    anchor=next((a for v in card["fields"].values() if v["status"]=="RECUPERADO" and isinstance(v.get("origin"),list) for a in v["origin"] if isinstance(a,dict) and isinstance(a.get("line"),int)),None)
    assert anchor,ident
    verify("D001-D383",anchor)
    candidate_packets.append({"id":ident,"pending_fields":pending,"context":window("D001-D383",anchor["line"],10),"source":"D001-D383","new_semantic_proposal":ident in newids,"prior_semantic_proposal":ident in oldids,"status":"AUTHOR_GATE_PENDING","scope":"AUTHOR_ONLY","semantic_certification":False})
counts={"new_observations":len(d["observations"]),"new_candidate_observations":len(d["new_candidate_observations"]),"official_targets":len(newids&set(cards)),"candidate_targets":len(newids&set(cand)),"nominal_contextual_proposals":len(nom),"nominal_globally_ambiguous":sum(x["action"]=="SCENE_IDENTITY_UNRESOLVED_GLOBALLY" for x in nom.values()),"zero_hit_proposals":len(zero),"descriptive_labels":len(occ),"descriptive_occurrences":sum(map(len,occ.values())),"descriptor_count_mismatch":len(mismatch),"official_packets":len(packets),"official_packets_with_context":sum(bool(x["contexts"]) for x in packets),"candidate_packets":len(candidate_packets),"literal_checks":checked}
out={"schema":"worldroot-r36-semantic-lot-08-result-v1","base":d["base"],"archive":d["archive"],"scope":"AUTHOR_ONLY","status":"AUTHOR_GATE_PENDING","production_hold":True,"canon_changed":False,"semantic_certification":False,"head_day":579,"sequence":50,"input_sha256":sha((st/"r36-multidimensional-lot-08-input.json").read_bytes()),"previous_lot_sha256":sha(oldp.read_bytes()),"counts":counts,"nominal_proposals":d["nominal_proposals"],"observations":d["observations"],"new_candidate_observations":d["new_candidate_observations"],"descriptive_occurrences":dict(occ),"descriptor_count_mismatch":mismatch,"profile_review_packets":packets,"candidate_review_packets":candidate_packets,"policy":"Retrieval packets and descriptor occurrences are evidence queues only; no global identities, no automatic field promotion or character access."}
path=st/"r36-multidimensional-lot-08-result.json"
path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert load(path)==out
print("R36_LOT08",json.dumps({"counts":counts,"sha256":sha(path.read_bytes()),"mismatch":mismatch},ensure_ascii=False,sort_keys=True))
