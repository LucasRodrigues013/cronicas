"""Incremental, source-bound historical review gate. No publication or canon writes."""
import copy, hashlib, json, re, sqlite3, subprocess, sys, tempfile
from pathlib import Path
from worldroot.natural_codex import git_blob, PRIVATE_SCOPES, PRIVATE_FIELDS, load_overlay
from worldroot.live_codex import REGISTRY, load_registry, sync, all_records

def need(condition, msg):
    if not condition:
        raise ValueError(msg)

def read(p):
    return json.loads(p.read_bytes())

def sha(b):
    return hashlib.sha256(b).hexdigest()

def compact(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":")).encode()

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def dump(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return git_blob(p.read_bytes())

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

def checked(root, path, expected):
    p = root / path
    raw = p.read_bytes()
    need(git_blob(raw) == expected, "Blob mismatch: " + path)
    need(git(root, "rev-parse", "HEAD:" + path) == expected, "Checkout object mismatch: " + path)
    return raw

def fields(o):
    return {(i,k):v for i,c in o["profiles"].items() for k,v in c["fields"].items()}

def protected(k, v):
    return k[1] in PRIVATE_FIELDS or v.get("scope") in PRIVATE_SCOPES or v.get("status") == "SEGREDO"

def append_value(before, value):
    if isinstance(before, list):
        return [*before, value]
    if isinstance(before, str):
        return before + "\n\n" + value
    raise ValueError("Non-appendable field; explicit editorial resolution required")

def main():
    audit, archive, engine, checkpoint_root, out = [Path(p).resolve() for p in sys.argv[1:6]]
    out.mkdir(parents=True, exist_ok=True)
    req = read(audit/"editorial/codex-staging/r36-native-review-request.json")
    need(req["mode"] == "READ_ONLY_CANDIDATE" and req["production_hold"] is True, "Read-only hold required")
    for root,key in [(archive,"archive"),(engine,"engine"),(checkpoint_root,"checkpoint")]:
        need(git(root,"rev-parse","HEAD") == req[key], "Pinned checkout mismatch: "+key)
        need(not git(root,"status","--porcelain"), "Dirty checkout: "+key)
    cp = json.loads(checked(checkpoint_root,req["checkpoint_path"],req["checkpoint_blob"]))
    inv = json.loads(checked(checkpoint_root,req["inventory_path"],req["inventory_blob"]))
    delta = read(audit/req["delta_path"])
    need(delta["schema"] == "worldroot-r36-incremental-editorial-delta-v1" and delta["status"] == "DRAFT_AUTHOR_APPROVAL_REQUIRED","Wrong delta authority")
    need(delta["base_archive"]==req["archive"]==cp["archive"]["commit"] and delta["engine"]==req["engine"] and delta["base_checkpoint"]==req["checkpoint"],"Stale base")
    need(delta["book"]==cp["book"]==inv["book"] and delta["batch"]==cp["next"]["batch"],"Wrong book/batch")
    need(cp["reservations"]["production_hold"] and not cp["canon_changed"] and not cp["production_activated"] and delta["production_hold"] and not delta["semantic_certification"],"Production/canon guard")
    rows,reviews,additional=delta["rows"],delta["reviews"],delta["additional"]
    for value,key in [(rows,"expected_rows_sha256"),(reviews,"expected_reviews_sha256"),(additional,"expected_additional_sha256")]:
        need(sha(compact(value))==req[key],"Draft transfer checksum mismatch: "+key)
    need(len(rows)==req["expected_changes"] and len({(x[0],x[1]) for x in rows})==len(rows),"Duplicate or missing fields")

    # Read all actual source parts directly from the private archive.
    source_manifest=read(archive/"history/sources/MANIFEST.json")
    spec=next(s for s in source_manifest["sources"] if s["source_name"]==inv["source"]["name"])
    source_raw=[]; part_map=[]; offset=0
    for part in spec["parts"]:
        raw=checked(archive,part["path"],part["git_blob_sha1"])
        need(len(raw)==part["bytes"],"Source part size")
        source_raw.append(raw)
        part_map.append((offset,part,raw))
        offset+=raw.count(b"\n")
    source=b"".join(source_raw)
    need(len(source)==spec["utf8_bytes"] and sha(source)==spec["sha256"]==inv["source"]["sha256"],"Full literal source mismatch")
    lines=source.decode("utf-8").splitlines()
    def literal(n):
        need(type(n) is int and 1<=n<=len(lines),"Invalid global line")
        return lines[n-1]
    def evidence(n, allow_blank=False):
        anchor=literal(n)
        need(allow_blank or bool(anchor.strip()),"Blank evidence line "+str(n))
        off,part,raw=next((o,p,b) for o,p,b in reversed(part_map) if o<n)
        local=n-off
        pl=raw.decode("utf-8").splitlines()
        need(1<=local<=len(pl) and pl[local-1]==anchor,"Part/global anchor mismatch "+str(n))
        return {"path":part["path"],"git_blob":part["git_blob_sha1"],"line":local,"global_line":n,"anchor":anchor}
    start,end=delta["ids"]
    need(start==cp["next"]["ledger_id"] and start<=end,"Wrong resume cursor")
    groups=inv["ledger"]["groups"]
    chosen=[g for g in groups if any(start<=i<=end for i in g["original_ids"])]
    ids=[i for g in chosen for i in g["original_ids"]]
    need(ids==list(range(start,end+1)),"Incomplete group or ledger gap")
    need(chosen[0]["line"]==cp["next"]["global_line"]==delta["source_lines"][0],"Resume line mismatch")
    next_groups=[g for g in groups if g["original_ids"][0]>end]
    need(bool(next_groups),"End-of-book requires separate closure gate")
    nxt=next_groups[0]
    need(delta["next"]=={"id":nxt["original_ids"][0],"line":nxt["line"]} and delta["source_lines"][1]==nxt["line"]-1,"Wrong next cursor")
    need([x[0] for x in reviews]==ids,"One adjudication per ledger record required")
    # Resolve ledger blob paths from Git's tree, not from chat attachments.
    ledger={}
    for blob in inv["ledger"]["batch_blobs"]:
        path=next(p.split("\t",1)[1] for p in git(checkpoint_root,"ls-tree","-r","HEAD","editorial/codex-staging/results/exact-context-ledger-v1").splitlines() if p.split("\t",1)[0].split()[-1]==blob)
        for rec in json.loads(checked(checkpoint_root,path,blob)):
            ledger[rec["original_id"]]=rec
    contexts=0
    for g in chosen:
        anchor=literal(g["line"])
        need(sha(anchor.encode())==g["anchor_sha256"],"Inventory anchor hash")
        for i in g["original_ids"]:
            rec=ledger[i]
            need(rec["line"]==g["line"] and rec["anchor"]==anchor and rec["anchor_sha256"]==g["anchor_sha256"],"Ledger anchor mismatch "+str(i))
            for c in rec["context"]:
                need(literal(c["line"])==c["text"],"Ledger context mismatch "+str(i))
                contexts+=1
    lower,upper=delta["source_lines"]
    def validate_span(nums):
        need(isinstance(nums,list) and nums,"Empty evidence")
        need(all(lower-4<=n<=upper for n in nums),"Evidence outside reviewed interval")
        return [evidence(n) for n in nums]
    review_receipts=[]
    for i,classification,note,nums in reviews:
        need(bool(classification.strip()) and bool(note.strip()),"Empty editorial adjudication")
        review_receipts.append({"ledger_id":i,"classification":classification,"note":note,"evidence":validate_span(nums)})
    extra_receipts=[]
    for x in additional:
        nums=x.get("lines",[x["line"]] if "line" in x else [])
        extra_receipts.append({**x,"evidence":validate_span(nums) if nums else []})

    manifest_path="editorial/registries/r35-living-overlay-manifest.json"
    old_manifest=checked(archive,manifest_path,cp["archive"]["manifest_blob"])
    m=json.loads(old_manifest)
    keys={"character_overlay":"character_overlay","world_overlay":"world_overlay","naming_review":"naming_overlay"}
    docs={}
    for k,cpkey in keys.items():
        need(m[k]["git_blob"]==cp["archive"][cpkey],"Checkpoint/manifest disagreement")
        docs[k]=json.loads(checked(archive,m[k]["path"],m[k]["git_blob"]))
    base_raw=checked(archive,REGISTRY,m["base_registry_blob"])
    base=json.loads(base_raw)
    head=json.loads(checked(archive,"canon/HEAD.json",req["expected_head_blob"]))
    need(head["day"]==req["expected_day"] and head["sequence"]==req["expected_sequence"],"Narrative HEAD changed")
    immutable={p:sha((archive/p).read_bytes()) for p in ["canon/HEAD.json","ops/RESUME.json","history/sources/MANIFEST.json",REGISTRY]}
    before=load_overlay(archive,base_raw,base)
    full_before,_=load_registry(archive)
    need(before==full_before["_natural_overlay"],"Native before disagreement")
    old_fields=fields(before)
    need(len(before["profiles"])==req["expected_profiles"] and len(old_fields)==req["expected_fields"],"Profile/field count mismatch")
    need(len(before["naming_review"])==req["expected_names"] and len(before["links"])==req["expected_links"],"Naming/link count mismatch")
    private={k:v for k,v in old_fields.items() if v.get("scope") in PRIVATE_SCOPES or v.get("status")=="SEGREDO"}
    need(len(private)==req["expected_private_fields"],"Protected count mismatch")
    cards={c["id"]:c for c in docs["character_overlay"]["characters"]+docs["world_overlay"]["records"]}
    expected=copy.deepcopy(old_fields); changes=[]
    for ident,field,before_hash,addition,nums in rows:
        key=(ident,field)
        need(key in old_fields,"Unknown existing field: "+str(key))
        prev=old_fields[key]
        need(not protected(key,prev),"Protected field write: "+str(key))
        need(field not in before["vetoes"].get(ident,()),"Vetoed field write")
        need(sha(canonical(prev["value"]))==before_hash,"Stale field value: "+str(key))
        ev=validate_span(nums)
        new=copy.deepcopy(prev)
        new["value"]=append_value(prev["value"],addition)
        # Preserve original scope/status/current-state metadata. Add dated historical evidence only.
        origin=copy.deepcopy(prev["origin"])
        if not isinstance(origin,list):
            origin=[origin]
        days=[int(n) for n in re.findall(r"\bD(\d{1,3})",addition)]
        need(days,"Missing dated historical observation")
        src={"book":delta["book"],"batch":delta["batch"],"day":days[0],"source_sha256":spec["sha256"],"evidence":ev}
        origin.append(src)
        new["origin"]=origin
        new["justification"] += " | Lote B%03d: observação histórica datada, sem afirmar estado atual." % delta["batch"]
        new.setdefault("historical_observations",[]).append({"batch":delta["batch"],"book":delta["book"],"day":days[0],"value":addition,"origin_index":len(origin)-1})
        cards[ident]["fields"][field]=new
        expected[key]=new
        changes.append({"entity_id":ident,"field":field,"before":prev,"after":new,"evidence":ev})
    # Generate versioned candidate copies, keep original files and all official pointers intact.
    candidate=copy.deepcopy(m)
    candidate["pending_historical_review"]={"batch":delta["batch"],"ids":delta["ids"],"status":"CANDIDATE_ONLY_AUTHOR_APPROVAL_REQUIRED","base_checkpoint":req["checkpoint"],"delta_sha256":sha((audit/req["delta_path"]).read_bytes()),"production_hold":True}
    generated=[]
    artifact_registry=out/"registries"
    candidate_blobs={}
    try:
        for key in ["character_overlay","world_overlay","naming_review"]:
            if key=="naming_review":
                docs[key]["source_overlay_blob"]=candidate["character_overlay"]["git_blob"]
            oldpath=m[key]["path"]
            v=req["candidate_versions"][key]
            newpath=re.sub(r"-v\d+\.json$", "-v%d.json"%v,oldpath)
            need(newpath!=oldpath and not (archive/newpath).exists(),"Candidate path collision")
            target=archive/newpath
            generated.append(target)
            blob=dump(target,docs[key])
            candidate[key]["path"]=newpath
            candidate[key]["git_blob"]=blob
            candidate_blobs[newpath]=blob
            need(dump(artifact_registry/Path(newpath).name,docs[key])==blob,"Candidate artifact mismatch")
        (archive/manifest_path).write_bytes((json.dumps(candidate,ensure_ascii=False,indent=2)+"\n").encode())
        candidate_blobs[manifest_path]=git_blob((archive/manifest_path).read_bytes())
        need(dump(artifact_registry/Path(manifest_path).name,candidate)==candidate_blobs[manifest_path],"Manifest artifact mismatch")
        after=load_overlay(archive,base_raw,base)
        full_after,_=load_registry(archive)
        need(after==full_after["_natural_overlay"],"Native after disagreement")
        new_fields=fields(after)
        need(new_fields==expected,"Unexpected field difference")
        changed={k for k in old_fields if old_fields[k]!=new_fields[k]}
        need(changed=={(x[0],x[1]) for x in rows},"Unexpected change set")
        need(set(before["profiles"])==set(after["profiles"]),"Stable IDs changed")
        for ident,card in before["profiles"].items():
            need({k:v for k,v in card.items() if k!="fields"}=={k:v for k,v in after["profiles"][ident].items() if k!="fields"},"Profile metadata changed: "+ident)
        for key in ("aliases","vetoes","links","naming_review","checkpoint","base_ids"):
            need(before[key]==after[key],"Native invariant changed: "+key)
        need(all(new_fields[k]==v for k,v in old_fields.items() if protected(k,v)),"Secret/private field changed")
        need(all(new_fields[k]["scope"]==v["scope"] and new_fields[k]["status"]==v["status"] for k,v in old_fields.items()),"Scope/status changed")
        # Reuse Book I replay and restore gate in the disposable candidate checkout.
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"graph.sqlite"; restored=Path(tmp)/"restore.sqlite"
            result=sync(archive,db)
            need(sync(archive,db)==result,"Non-idempotent projection")
            with sqlite3.connect(db) as src,sqlite3.connect(restored) as dst:
                src.backup(dst)
                need(dst.execute("PRAGMA integrity_check").fetchone()[0]=="ok","SQLite integrity")
                need(list(src.iterdump())==list(dst.iterdump()),"SQLite restore mismatch")
            need(sync(archive,restored)==result,"Restore replay mismatch")
        need(all(sha((archive/p).read_bytes())==h for p,h in immutable.items()),"Immutable source changed")
        # Future packet planner uses whole inventory groups, never auto-adjudicates.
        packets=[]; packet=[]; size=0
        for g in next_groups:
            n=len(g["original_ids"])
            if packet and size+n>100:
                packets.append(packet);packet=[];size=0
            packet.append(g);size+=n
            if size>=60:
                packets.append(packet);packet=[];size=0
        if packet:
            packets.append(packet)
        if len(packets)>1 and sum(len(g["original_ids"]) for g in packets[-1])<50 and sum(len(g["original_ids"]) for g in packets[-2]+packets[-1])<=100:
            packets[-2].extend(packets.pop())
        plan=[]
        for packet in packets:
            ii=[i for g in packet for i in g["original_ids"]]
            later=next((g for g in groups if g["original_ids"][0]>ii[-1]),None)
            plan.append({"ids":[ii[0],ii[-1]],"records":len(ii),"groups":len(packet),"source_lines":[packet[0]["line"],later["line"]-1 if later else inv["source"]["lines"][1]],"status":"UNREVIEWED_PACKET_PLAN"})
        receipt={"status":"NATIVE_CANDIDATE_VALIDATED_NOT_APPROVED","base_checkpoint":req["checkpoint"],"base_archive":req["archive"],"engine":req["engine"],"records":len(ids),"groups":len(chosen),"contexts_verified":contexts,"source_part_hashes":len(source_raw),"source_sha256":sha(source),"fields":len(old_fields),"changed_fields":len(changed),"unchanged_fields":len(old_fields)-len(changed),"profiles":len(after["profiles"]),"private_scope_fields_unchanged":len(private),"all_protected_fields_unchanged":sum(protected(k,v) for k,v in old_fields.items()),"naming_count":len(after["naming_review"]),"links":len(after["links"]),"native_load_overlay_before_after":True,"projection_records":result["records"],"projection_events":result["events"],"replay_restore":True,"candidate_blobs":candidate_blobs,"next":delta["next"],"future_packets":plan,"canon_changed":False,"production_activated":False,"semantic_certification":False,"approval_required":True}
        dump(out/"native-receipt.json",receipt)
        dump(out/"review-evidence.json",{"changes":changes,"adjudications":review_receipts,"additional":extra_receipts})
        print(json.dumps(receipt,ensure_ascii=False))
    finally:
        (archive/manifest_path).write_bytes(old_manifest)
        for p in generated:
            p.unlink(missing_ok=True)
    need(not git(archive,"status","--porcelain"),"Archive checkout not restored")
    need(not git(engine,"status","--porcelain"),"Engine checkout changed")
    need(not git(checkpoint_root,"status","--porcelain"),"Checkpoint checkout changed")

if __name__=="__main__":
    main()
