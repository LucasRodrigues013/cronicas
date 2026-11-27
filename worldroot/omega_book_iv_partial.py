"""Native partial Book IV receipt validation; no recovery or canon mutation."""
import argparse,json,subprocess
from pathlib import Path
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, validate_receipt, require
def verify_partial(root,archive):
    root=Path(root);archive=Path(archive)
    require(subprocess.check_output(["git","-C",str(archive),"rev-parse","HEAD"],text=True).strip()==ARCHIVE,"archive pin")
    require(not subprocess.check_output(["git","-C",str(archive),"status","--porcelain"],text=True).strip(),"archive dirty")
    release=read(root,ROOT+"book-IV-cycle-recovery-release.json","1ea9d60a58ecf00a368f0e33631164fc7cbe0051")
    require(release["recovery_gate"]=="AUTHORIZED_STAGING_ONLY" and release["production_gate"]=="HOLD","release gate")
    cp=read(root,ROOT+"recovery-checkpoint-0030-partial-01.json")
    r=read(root,cp["receipt_path"],digest=cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"][29]
    require(r["release_blob"]==cp["release_blob"]=="1ea9d60a58ecf00a368f0e33631164fc7cbe0051" and
            r["previous_macro_id"]==q["previous_macro"] and r["official_unit_seal"]==q["unit_seal"],"release chain")
    require(r["range"]==cp["range"]==[268704,269101] and cp["next_line"]==r["next_line"]==269102 and
            r["macro_complete"] is False and cp["macro_complete"] is False,"partial boundary")
    manifest=read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")
    source=SourceCache(archive,manifest).get(q["source"])
    metrics=validate_receipt(r,q,source,r["project"],ARCHIVE,expected_range=cp["range"])
    require(metrics["records"]==7 and metrics["lines"]==398 and metrics["coverage"]==7,"partial counts")
    require(sum(x["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" for x in r["records"])==4
            and sum(x["authority"]=="METADATA_NOT_EVENT" for x in r["records"])==2
            and sum(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT" for x in r["records"])==1,"authority counts")
    require(all(x["book"]=="IV" and x["promotion"] is False for x in r["records"]),"book scope")
    return {**metrics,"status":"PASS_NATIVE_PARTIAL_RECEIPT","next_line":269102,"macro_complete":False,
            "production_gate":"HOLD","semantic_certification":False,"canon_changed":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_partial(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
