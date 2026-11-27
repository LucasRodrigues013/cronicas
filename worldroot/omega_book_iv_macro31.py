"""Native validation of first Book IV macro 0031 continuation."""
import argparse,json
from pathlib import Path
from .omega_hybrid_receipt import ROOT, ARCHIVE, read
from .omega_turbo_recovery import SourceCache, validate_receipt, require
from .omega_book_iv_macro30 import verify_close as verify_macro30_close
def verify_start(root,archive):
    root=Path(root);archive=Path(archive)
    prior=verify_macro30_close(root,archive)
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

def verify_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_start(root,archive)
    require(prior["next_line"]==279314 and prior["records"]==3,"opening gate")
    c0=read(root,ROOT+"recovery-checkpoint-0031-partial-01-validated.json","58ec44f8a2ed61c1705da6f59552ef1bcebfe842")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0031-closure-pending.json","72d364c5762c113fc4c1d3565a920acb1b5b487f")
    r=read(root,cp["receipt_path"],"b890d9a2fa544fabf5ba267810311d713edb5dd2",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[30]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="58ec44f8a2ed61c1705da6f59552ef1bcebfe842" and r["release_blob"]==c0["release_blob"]==cp["release_blob"],"checkpoint chain")
    require(r["official_unit_seal"]==m["unit_seal"] and r["previous_macro_id"]==m["previous_macro"] and cp["next_macro"]==q[31],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in opening["records"]],expected_range=[279314,289144])
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    combined=dict(r,range=[279002,289144],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE)
    require(new["lines"]==9831 and new["records"]==cp["records"]==78 and new["coverage"]==78,"new counts")
    require(result["lines"]==10143 and result["records"]==cp["macro_records"]==81 and result["coverage"]==81,"macro counts")
    require(len({x["id"] for x in allr})==81 and all(x["book"]=="IV" and x["day"] in range(368,375) for x in allr),"scope and unique IDs")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="reserved"),"restricted isolation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(source[0][279313]=="XI — Uma carta, uma promessa e uma pequena vergonha","first section")
    require(source[0][280149]=="CAPÍTULO 4 — O ALMIRANTE QUE NAVEGOU POR TERRA" and source[0][284233]=="CAPÍTULO 5 — A MARÉ QUE NÃO SE CURVOU" and source[0][288567]=="CAPÍTULO 6 — O SEGREDO DAS LANTERNAS AFOGADAS","effective chapter titles")
    require(all(source[0][i-1]=="## Prompt:" for i in (280114,284224,287412,288538)),"prompt boundaries")
    require(q[31]["start"]==r["next_line"]==cp["next_line"]==289145 and q[31]["previous_macro"]==m["id"],"next queue")
    require(cp["staging_records"]==c0["staging_records"]+78==2300 and cp["book_counts"]["IV"]==178 and cp["completed_macros"]==30,"staging totals")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0031_COMPLETE","new_records":new["records"],"new_lines":new["lines"],"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":289145,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_close(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
