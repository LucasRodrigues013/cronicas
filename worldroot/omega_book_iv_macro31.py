"""Native validation of first Book IV macro 0031 continuation."""
import argparse,json
from pathlib import Path
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, validate_receipt, require
from .omega_book_iv_macro30 import verify_close
def verify_start(root,archive):
    root=Path(root);archive=Path(archive)
    prior=verify_close(root,archive)
    cp0=read(root,ROOT+"recovery-checkpoint-0030-validated.json","9965a1ce58bf6bcc24411c82e83e91927022b515")
    require(prior["macro_complete"] and cp0["native_validation"]=="PASS" and cp0["next_line"]==279002,"previous gate")
    cp=read(root,ROOT+"recovery-checkpoint-0031-partial-01.json")
    r=read(root,cp["receipt_path"],digest=cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[30]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="9965a1ce58bf6bcc24411c82e83e91927022b515" and r["release_blob"]==cp0["release_blob"],"chain")
    require(r["previous_macro_id"]==q[29]["id"] and r["official_unit_seal"]==m["unit_seal"] and m["start"]==279002,"queue")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    require(source[0][279313]=="XI — Uma carta, uma promessa e uma pequena vergonha","next section")
    metrics=validate_receipt(r,m,source,r["project"],ARCHIVE,expected_range=[279002,279313])
    require(metrics["records"]==3 and metrics["coverage"]==3 and metrics["lines"]==312,"counts")
    require(all(x["book"]=="IV" and x["day"]==368 and x["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" for x in r["records"]),"authority")
    require(r["next_line"]==cp["next_line"]==279314 and cp["staging_records"]==cp0["staging_records"]+3 and cp["production_gate"]=="HOLD","checkpoint")
    return {**metrics,"status":"PASS_NATIVE_MACRO_0031_PARTIAL","next_line":279314,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_start(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
