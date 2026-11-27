"""Read-only cumulative macro 0030 closure."""
import argparse,json
from pathlib import Path
from collections import Counter
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, validate_receipt, require
from .omega_book_iv_continuation import verify_continuation

def verify_close(root,archive):
    root=Path(root);archive=Path(archive)
    prior=verify_continuation(root,archive)
    require(prior["cumulative_records"]==44 and prior["next_line"]==273044,"prior native chain")
    c1=read(root,ROOT+"recovery-checkpoint-0030-partial-01-validated.json","a05229f7e660a51aeb3d1fd7f0f94f0c679d33b5")
    c2=read(root,ROOT+"recovery-checkpoint-0030-partial-02-validated.json","293af174c55475d52d10ee14fcc40bcc55538a07")
    old=[read(root,c["receipt_path"],c["receipt_blob"],c["receipt_sha256"]) for c in (c1,c2)]
    cp=read(root,ROOT+"recovery-checkpoint-0030-closure-pending.json")
    r=read(root,cp["receipt_path"],digest=cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[29]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="293af174c55475d52d10ee14fcc40bcc55538a07" and r["release_blob"]==c2["release_blob"],"checkpoint chain")
    require(r["official_unit_seal"]==m["unit_seal"] and r["previous_macro_id"]==m["previous_macro"] and cp["next_macro"]==q[30],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    metrics=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for v in old for x in v["records"]],expected_range=[273044,279001])
    require(metrics["records"]==cp["records"] and metrics["lines"]==5958 and r["range"]==cp["range"],"partial counts")
    allr=[x for v in old+[r] for x in v["records"]]
    allc=[x for v in old+[r] for x in v["coverage"]]
    combined=dict(r,range=[268704,279001],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE)
    require(result["lines"]==10298 and result["records"]==cp["macro_records"] and len(allr)==len(set(x["id"] for x in allr)),"complete macro")
    require(all(x["book"]=="IV" and x["promotion"] is False and x["day"] in (366,367,368) for x in allr),"scope")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="reserved"),"reserved isolation")
    require(all((x["evidence"]["role"]=="Prompt")== (x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(source[0][273095]=="CAPÍTULO 2 — A MARCHA DOS TREZENTOS" and source[0][276624]=="CAPÍTULO 3 — A CANÇÃO DOS QUE NÃO FICAM PARA TRÁS","literal chapter titles")
    require(source[0][273397]=="2.918" and source[0][273355]=="1.142 residentes." and 146+64+90==300,"census/mobilization")
    require(q[30]["start"]==279002 and q[30]["previous_macro"]==m["id"] and cp["production_gate"]=="HOLD","next gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0030_COMPLETE","new_records":metrics["records"],"new_lines":5958,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":279002,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_close(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
