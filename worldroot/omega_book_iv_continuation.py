"""Native read-only validation of chapter-one continuation and cumulative chain."""
import argparse,json,subprocess
from pathlib import Path
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, validate_receipt, require
from .omega_book_iv_partial import verify_partial

def verify_continuation(root,archive):
    root=Path(root);archive=Path(archive)
    earlier=verify_partial(root,archive)
    prior=read(root,ROOT+"recovery-checkpoint-0030-partial-01-validated.json","a05229f7e660a51aeb3d1fd7f0f94f0c679d33b5")
    require(prior["native_validation"]=="PASS" and prior["next_line"]==earlier["next_line"],"prior checkpoint")
    old=read(root,prior["receipt_path"],prior["receipt_blob"],prior["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0030-partial-02.json")
    r=read(root,cp["receipt_path"],digest=cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"][29]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="a05229f7e660a51aeb3d1fd7f0f94f0c679d33b5"
            and r["release_blob"]==prior["release_blob"] and r["previous_macro_id"]==q["previous_macro"]
            and r["official_unit_seal"]==q["unit_seal"],"chain pin")
    require(r["range"]==cp["range"]==[269102,273043] and r["range"][0]==prior["next_line"]
            and r["next_line"]==cp["next_line"]==273044 and not cp["macro_complete"] and not r["macro_complete"],"partial boundary")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(q["source"])
    require(source[0][273019]=="FIM DO CAPÍTULO 1 — QUANDO A LEGIÃO RESPONDE" and source[0][273043]=="## Prompt:","chapter boundary")
    metrics=validate_receipt(r,q,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in old["records"]],expected_range=cp["range"])
    require(metrics["records"]==cp["records"] and metrics["coverage"]==cp["records"] and metrics["lines"]==3942,"counts")
    require(cp["macro_records"]==len(old["records"])+len(r["records"]) and cp["lines_recovered_this_macro"]==4340,"cumulative counts")
    require(all(x["book"]=="IV" and x["day"]==366 and x["promotion"] is False and x["evidence"]["role"]=="Response" for x in r["records"]),"scope")
    private=[x for x in r["records"] if x["visibility"].startswith("READER_ONLY")]
    require(len(private)==cp["reader_only"]==5 and all(x["type"]=="reader_scene" for x in private),"private visibility")
    require(r["records"][-1]["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT","transition authority")
    require(cp["production_gate"]=="HOLD" and cp["recovery_gate"]=="AUTHORIZED_STAGING_ONLY","gate")
    return {**metrics,"status":"PASS_NATIVE_CHAPTER_1_CONTINUATION","cumulative_lines":4340,"cumulative_records":cp["macro_records"],
            "chapter_1_closed":True,"next_line":273044,"reader_only":len(private),"macro_complete":False,
            "production_gate":"HOLD","canon_changed":False,"semantic_certification":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_continuation(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
