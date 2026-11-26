"""Read-only native review gate for historical deltas. Never publish canon."""
import copy, hashlib, json, re, subprocess, sys
from pathlib import Path
from worldroot.live_codex import load_registry, REGISTRY
from worldroot.natural_codex import load_overlay, git_blob, PRIVATE_FIELDS, PRIVATE_SCOPES, MANIFEST

def read(p):
    return json.loads(p.read_bytes())
def raw(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()
def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
def git(path,*args):
    return subprocess.check_output(["git","-C",str(path),*args],text=True).strip()
def protected(key,entry):
    return key in PRIVATE_FIELDS or entry.get("status")=="SEGREDO" or entry.get("scope") in PRIVATE_SCOPES

def run(root, audit, engine, delta_path, output):
    d=read(delta_path)
    assert d["status"]=="DRAFT_AUTHOR_APPROVAL_REQUIRED" and d["production_hold"] is True
    assert d["semantic_certification"] is False
    assert git(root,"rev-parse","HEAD")==d["base_archive"]
    assert git(engine,"rev-parse","HEAD")==d["engine"]
    cp=read(audit/"editorial/codex-staging"/f'r36-book-ii-stage-b-checkpoint-{d["batch"]-1:03}.json')
    assert cp["archive"]["commit"]==d["base_archive"]
    assert cp["next"]["ledger_id"]==d["ids"][0] and cp["next"]["global_line"]==d["source_lines"][0]
    assert cp["reservations"]["production_hold"] is True
    head=read(root/"canon/HEAD.json")
    assert (head["day"],head["sequence"])==(579,50)
    assert git_blob((root/"canon/HEAD.json").read_bytes())==cp["verification"]["narrative_head_blob"]
    inventory=read(audit/"editorial/codex-staging/r36-book-ii-stage-a-inventory.json")
    parts=sorted((root/"history/sources").glob(inventory["source"]["name"]+".part-*"))
    assert parts
    src=b"".join(p.read_bytes() for p in parts)
    assert hashlib.sha256(src).hexdigest()==inventory["source"]["sha256"]
    partmap={}
    lines=[]
    for p in parts:
        a=p.read_bytes(); local=a.decode("utf-8").splitlines()
        partmap[str(p.relative_to(root))]=(len(lines),local,git_blob(a))
        lines+=local
    assert lines==src.decode("utf-8").splitlines()
    for spec in inventory["source"]["parts"]:
        assert partmap[spec["path"]][2]==spec["git_blob"]
    first,last=d["ids"]; ids=list(range(first,last+1))
    groups=[g for g in inventory["ledger"]["groups"] if set(g["original_ids"])&set(ids)]
    assert [i for g in groups for i in g["original_ids"]]==ids
    following=next(g for g in inventory["ledger"]["groups"] if g["original_ids"][0]==last+1)
    assert d["next"]=={"id":last+1,"line":following["line"]}
    assert d["source_lines"][1]==following["line"]-1
    led=[]
    for p in sorted((audit/"editorial/codex-staging/results/exact-context-ledger-v1").glob("batch-*.json")):
        b=p.read_bytes()
        if git_blob(b) in inventory["ledger"]["batch_blobs"]:
            led.extend(json.loads(b))
    led=[x for x in led if x["original_id"] in ids]
    assert [x["original_id"] for x in led]==ids
    contexts=0
    for x in led:
        assert lines[x["line"]-1]==x["anchor"]
        assert hashlib.sha256(x["anchor"].encode()).hexdigest()==x["anchor_sha256"]
        for item in x["context"]:
            assert lines[item["line"]-1]==item["text"]
            contexts+=1
    assert [x[0] for x in d["reviews"]]==ids
    assert sha(d["rows"])==d["compact_rows_sha256"]
    def evidence(ns):
        result=[]
        for n in ns:
            assert d["source_lines"][0]-24<=n<=d["source_lines"][1]
            assert lines[n-1].strip()
            for path,(offset,local,blob) in partmap.items():
                if offset<n<=offset+len(local):
                    result.append({"path":path,"git_blob":blob,"source_sha256":inventory["source"]["sha256"],
                        "global_line":n,"line":n-offset,"anchor":lines[n-1]})
                    break
            else: raise ValueError("No source part")
        assert len(result)==len(ns)
        return result
    for i,classification,note,ns in d["reviews"]:
        assert classification and note and evidence(ns)
    for item in d["additional"]:
        ns=item.get("lines",[item["line"]] if "line" in item else [])
        if ns: evidence(ns)
    mpath=root/MANIFEST; oldm=mpath.read_bytes(); m=json.loads(oldm)
    base=(root/REGISTRY).read_bytes(); base_doc=json.loads(base)
    assert git_blob(oldm)==cp["archive"]["manifest_blob"]
    assert git_blob(base)==m["base_registry_blob"]
    before=load_overlay(root,base,base_doc)
    loaded,_=load_registry(root)
    assert loaded["_natural_overlay"]["profiles"]==before["profiles"]
    original=before["profiles"]
    specs=[("character_overlay","characters"),("world_overlay","records")]
    docs={key:read(root/m[key]["path"]) for key,_ in specs}
    cards={c["id"]:c for key,arr in specs for c in docs[key][arr]}
    assert cards==original
    keys=set(); changes=[]
    for ident,field,h,addition,ns in d["rows"]:
        assert (ident,field) not in keys;keys.add((ident,field))
        entry=cards[ident]["fields"][field]
        assert not protected(field,entry) and sha(entry["value"])==h
        assert addition.strip() and addition.startswith("Livro II, D")
        old=copy.deepcopy(entry)
        ev=evidence(ns)
        value=entry["value"]
        assert isinstance(value,(str,list))
        entry["value"]=value+[addition] if isinstance(value,list) else value+"\n\n"+addition
        prior=entry["origin"]
        if not isinstance(prior,list): prior=[prior]
        source={"book":d["book"],"batch":d["batch"],"evidence":ev,
                "source_sha256":inventory["source"]["sha256"]}
        entry["origin"]=prior+[source]
        entry.setdefault("historical_observations",[]).append({"book":d["book"],"batch":d["batch"],
            "value":addition,"origin_index":len(prior)})
        entry["justification"]+=" | B006: observacao historica datada; estado atual e classificacao anterior preservados."
        changes.append({"id":ident,"field":field,"before":old,"after":copy.deepcopy(entry)})
    naming=read(root/m["naming_review"]["path"])
    created=[]
    output.mkdir(parents=True,exist_ok=True)
    def new_document(key,doc):
        spec=m[key]; old=root/spec["path"]
        match=re.fullmatch(r"(.+)-v(\d+)\.json",old.name)
        assert match
        path=old.with_name(f"{match[1]}-v{int(match[2])+1}.json")
        assert not path.exists()
        b=raw(doc)
        path.write_bytes(b);created.append(path)
        spec["path"]=str(path.relative_to(root));spec["git_blob"]=git_blob(b)
        return path
    try:
        for key,_ in specs: new_document(key,docs[key])
        naming["source_overlay_blob"]=m["character_overlay"]["git_blob"]
        new_document("naming_review",naming)
        m["candidate_review"]={"book":d["book"],"batch":d["batch"],"status":d["status"],
            "ids":d["ids"],"delta_rows_sha256":d["compact_rows_sha256"],"production_hold":True}
        mpath.write_bytes(raw(m))
        after=load_overlay(root,base,base_doc)
        loaded,_=load_registry(root)
        assert loaded["_natural_overlay"]["profiles"]==after["profiles"]
        assert set(original)==set(after["profiles"])
        assert before["aliases"]==after["aliases"] and before["links"]==after["links"]
        assert before["naming_review"]==after["naming_review"]
        changed=set();private_count=0;total=0
        for ident,card in original.items():
            other=after["profiles"][ident]
            assert {k:v for k,v in card.items() if k!="fields"}=={k:v for k,v in other.items() if k!="fields"}
            assert set(card["fields"])==set(other["fields"])
            for k,v in card["fields"].items():
                total+=1
                new=other["fields"][k]
                if protected(k,v):
                    private_count+=1
                    assert new==v
                if new!=v: changed.add((ident,k))
        assert changed==keys
        for change in changes:
            assert after["profiles"][change["id"]]["fields"][change["field"]]==change["after"]
        for path in created+[mpath]:
            (output/path.name).write_bytes(path.read_bytes())
        receipt={"status":"NATIVE_CANDIDATE_PASS_NOT_APPROVED","base_archive":d["base_archive"],
            "engine":d["engine"],"draft_sha256":sha(d),"records":len(ids),"groups":len(groups),
            "contexts":contexts,"fields":total,"changed_fields":len(keys),"unchanged_fields":total-len(keys),
            "protected_fields":private_count,"profiles":len(original),"naming":len(after["naming_review"]),
            "links":len(after["links"]),"blobs":{p.name:git_blob(p.read_bytes()) for p in created+[mpath]},
            "canon_changed":False,"production_activated":False,"semantic_certification":False}
        (output/"candidate-receipt.json").write_bytes(raw(receipt))
        (output/"candidate-diff.json").write_bytes(raw(changes))
        print(json.dumps(receipt,ensure_ascii=False))
    finally:
        mpath.write_bytes(oldm)
        for path in created: path.unlink()
    assert not git(root,"status","--porcelain","--untracked-files=all")
    assert not git(engine,"diff","--name-only")

if __name__=="__main__":
    run(*(Path(x).resolve() for x in sys.argv[1:6]))
