"""Opt-in local authenticated recovery, isolated staging only.
Single writer; private POSIX directory. Never run on public CI with real sources.
"""
import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from . import semantic_local as local
from . import r36_evaluation as ev
from . import r36_evaluation_local as adapter
from .r36_trust import authenticate,verify,keycheck,require,digest,authorize_manifest
from .semantic_queue import seal

VERSION="r36-e7-recovery-v1"
ATTEMPTS=2
MAX_RECORD=1_000_000

def private_dir(path):
    path=Path(path).absolute()
    require(os.name=="posix","Private POSIX custody required")
    require(path.parent.is_dir() and path.parent.resolve()==path.parent,"Unsafe parent")
    # Do not place receipts in an ordinary Git working tree.
    require(not any((a/".git").exists() for a in (path,*path.parents)),"Git working tree forbidden")
    path.mkdir(mode=0o700,exist_ok=True)
    info=path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and not(info.st_mode&0o077),
            "Require owner-only non-symlink directory")
    return path

def read_record(path):
    info=path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and not(info.st_mode&0o077)
            and info.st_size<=MAX_RECORD,"Unsafe local record")
    with path.open("rb") as f:raw=f.read(MAX_RECORD+1)
    require(len(raw)<=MAX_RECORD,"Record too large")
    return json.loads(raw,object_pairs_hook=adapter._unique_json)

def write_record(path,purpose,payload,key):
    # Reuse original no-overwrite publication; durable file and directory fsync.
    obj=authenticate(purpose,payload,key)
    require(len(json.dumps(obj,ensure_ascii=False,indent=2).encode())+1<=MAX_RECORD,"Record too large")
    local.immutable_write(path,obj)
    with path.open("rb") as f:os.fsync(f.fileno())
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)

def exists(path):
    return path.exists() or path.is_symlink()

def _bounded_api(path,payload=None):
    return local.local_api(path,payload,timeout=120 if path=="/api/chat" else 5,max_response_bytes=512_000)

def validate_saved(record,binding,p,prov,slot):
    require(set(record)=={"run_id","slot","review"} and record["run_id"]==seal(binding)
            and record["slot"]==slot,"Wrong run or slot")
    v=record["review"];r=v["receipt"]
    checked=ev.validate_receipt(p,r)
    require(v["receipt_sha256"]==checked["receipt_sha256"] and r["executor"]==slot
            and r["executor_revision"]==binding["models"][slot]["digest"]
            and r["manifest_sha256"]==prov["manifest_sha256"]
            and r["calibration_sha256"]==prov["calibration"]["calibration_sha256"],"Invalid stored receipt binding")
    require(digest(v["response_sha256"]) and digest(v["request_sha256"])
            and type(v["elapsed_ns"]) is int and v["elapsed_ns"]>=0 and v["local_call_returned"] is True,
            "Invalid stored call metadata")
    quote=r["candidate_quote"]
    require(isinstance(quote,str) and (not quote or quote in p["candidate"])
            and (r["result"] not in ("PASS","FAIL") or bool(quote.strip())),"Invalid stored candidate quote")
    return v

def run(root,out,judge,candidate,authority,scope,authority_key,receipt_key,
        model_a,model_b,pin_a,pin_b,run_nonce,generator_digest=None,api=_bounded_api):
    keycheck(authority_key);keycheck(receipt_key)
    require(authority_key!=receipt_key,"Separate authority and receipt keys required")
    approved=verify(authority,"source-authority",authority_key)
    require(set(approved)=={"scope","manifest"} and approved["scope"]==scope,"Wrong authority scope")
    require(isinstance(run_nonce,str) and 16<=len(run_nonce)<=128,"Explicit run nonce required")
    require(digest(pin_a) and digest(pin_b) and pin_a!=pin_b,"Two different expected model pins required")
    require(generator_digest is None or digest(generator_digest),"Invalid generator digest")
    require(generator_digest not in (pin_a,pin_b),"Generator cannot review itself")
    manifest=approved["manifest"]
    p,prov=adapter.source_packet(root,judge,candidate,manifest,seal(manifest))
    adapter._check_packet(p)
    binding={"schema":VERSION,"scope":scope,"authority_mac":authority["mac"],"nonce":run_nonce,
             "packet_id":p["packet_id"],"provenance_sha256":seal(prov),"generator_digest":generator_digest,
             "models":{"local-A":{"name":model_a,"digest":pin_a},"local-B":{"name":model_b,"digest":pin_b}},
             "transport":"LOOPBACK" if api is _bounded_api else "INJECTED_TEST"}
    rid=seal(binding)
    out=private_dir(out)
    lock=out/"active.lock"
    # A crashed process leaves a lock; trusted operator must verify process death before removing.
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        os.write(fd,str(os.getpid()).encode())
    finally:os.close(fd)
    calls=0
    try:
        path=out/"run.json"
        if exists(path):verify(read_record(path),"run-binding",receipt_key,binding)
        else:write_record(path,"run-binding",binding,receipt_key)
        reviews={}
        for slot,model in binding["models"].items():
            dest=out/(slot+".json")
            if exists(dest):
                saved=verify(read_record(dest),"review-receipt",receipt_key)
                reviews[slot]=validate_saved(saved,binding,p,prov,slot)
                continue
            # A durable attempt is consumed before calling. No automatic retry in this invocation.
            attempt_count=0
            for i in range(1,ATTEMPTS+1):
                marker=out/(slot+".attempt-"+str(i)+".json")
                if exists(marker):
                    verify(read_record(marker),"attempt",receipt_key,{"run_id":rid,"slot":slot,"attempt":i})
                    require(i==attempt_count+1,"Noncontiguous attempt journal")
                    attempt_count+=1
            if attempt_count==ATTEMPTS:
                return {"status":"ATTEMPT_LIMIT","run_id":rid,"slot":slot,"new_review_attempts":calls,"production_hold":True,"semantic_certification":False}
            # Check both expected pins before each new call; no inference if they changed.
            for m in binding["models"].values():
                require(local.revision(m["name"],api)==m["digest"],"Expected model pin mismatch")
            write_record(out/(slot+".attempt-"+str(attempt_count+1)+".json"),"attempt",
                         {"run_id":rid,"slot":slot,"attempt":attempt_count+1},receipt_key)
            calls+=1
            try:
                review=adapter._review(p,model["name"],model["digest"],slot,api,prov)
                saved={"run_id":rid,"slot":slot,"review":review}
                reviews[slot]=validate_saved(saved,binding,p,prov,slot)
                write_record(dest,"review-receipt",saved,receipt_key)
            except Exception as e:
                return {"status":"REVIEW_FAILED","run_id":rid,"slot":slot,"error_type":type(e).__name__,
                        "new_review_attempts":calls,"production_hold":True,"semantic_certification":False}
        a,b=(reviews[s]["receipt"] for s in ("local-A","local-B"))
        require(a["session_id"]!=b["session_id"],"Reused session")
        agrees=(a["result"],a["severity"])==(b["result"],b["severity"])
        return {"status":"LOCAL_RECEIPTS_AUTHENTICATED","run_id":rid,"new_review_attempts":calls,
                "result":a["result"] if agrees else "INCONCLUSIVE","agreement":agrees,
                "transport":binding["transport"],"local_custody_authenticated":True,
                "execution_attestation_verified":False,"independence_verified":False,
                "semantic_certification":False,"production_hold":True}
    finally:lock.unlink()

def read_key(path):
    path=Path(path).absolute()
    require(not any((a/".git").exists() for a in path.parents),"Key in Git working tree forbidden")
    info=path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and not(info.st_mode&0o077)
            and 32<=info.st_size<=4096,"Unsafe key file")
    key=path.read_bytes();keycheck(key);return key

def main(argv=None):
    p=argparse.ArgumentParser(description="Opt-in synthetic local pilot only; no story input")
    p.add_argument("--probe",action="store_true")
    for arg in ("out","authority-key","receipt-key","model-a","model-b","pin-a","pin-b","nonce","engine-revision"):
        p.add_argument("--"+arg)
    p.add_argument("--judge",choices=sorted(ev.RUBRICS),default="canon")
    a=p.parse_args(argv)
    if a.probe:
        print(json.dumps(local.availability(_bounded_api)));return 0
    if not all(getattr(a,k) for k in ("out","authority_key","receipt_key","model_a","model_b","pin_a","pin_b","nonce","engine_revision")):
        p.error("Pilot requires all custody, output, model, pin, nonce and revision arguments")
    try:
        ka,kb=read_key(a.authority_key),read_key(a.receipt_key)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=b"Synthetic fixture. Person A stayed home.\n"
            (root/"fixture.txt").write_bytes(raw)
            manifest={"schema":adapter.ADAPTER,"sources":[{"path":"fixture.txt","raw_sha256":hashlib.sha256(raw).hexdigest(),
                       "line_start":1,"line_end":1,"role":"CANON"}]}
            scope={"authority_revision":"synthetic-pilot-v1","engine_revision":a.engine_revision}
            result=run(root,a.out,a.judge,"Person A stayed home.",authorize_manifest(manifest,scope,ka),scope,ka,kb,
                       a.model_a,a.model_b,a.pin_a,a.pin_b,a.nonce)
        print(json.dumps(result));return 0 if result["status"]=="LOCAL_RECEIPTS_AUTHENTICATED" else 1
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error_type":type(e).__name__,"production_hold":True}));return 1

if __name__=="__main__":raise SystemExit(main())
