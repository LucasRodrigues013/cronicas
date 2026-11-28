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
def verify_macro32_start(root,archive):
    root=Path(root); archive=Path(archive)
    prior=verify_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0031-validated.json","94d41c66a771ff76b3ef1e3c2f8b72764b5e9410")
    require(prior["macro_complete"] and c0["native_validation"]=="PASS" and c0["next_line"]==289145,"macro31 validated gate")
    cp=read(root,ROOT+"recovery-checkpoint-0032-partial-01.json","6a0e6ec0fa369755458adc67035102a8e0ebe2e6")
    r=read(root,cp["receipt_path"],"4eb7d142f6b28e7e45ec854b143959ab07eccfd0",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[31]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="94d41c66a771ff76b3ef1e3c2f8b72764b5e9410" and r["release_blob"]==c0["release_blob"]==cp["release_blob"],"checkpoint chain")
    require(c0["next_macro"]==m and r["previous_macro_id"]==q[30]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    p1=read(root,ROOT+"partial-macro-0031-01.json")
    p2=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    metrics=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in p1["records"]+p2["records"]],expected_range=[289145,289313])
    require(metrics["records"]==metrics["coverage"]==cp["records"]==2 and metrics["lines"]==169,"counts")
    require(all(x["book"]=="IV" and x["day"]==374 and x["chapter_hint"]==6 and x["authority"]=="HISTORICAL_RESPONSE_NOT_CANON_CERTIFIED" for x in r["records"]),"scope")
    require(source[0][289313]=="A matriz foi acionada.","next literal line")
    require(cp["next_line"]==r["next_line"]==289314 and cp["staging_records"]==c0["staging_records"]+2==2302 and cp["book_counts"]["IV"]==180 and cp["completed_macros"]==31,"checkpoint")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["macro_complete"],"gate")
    return {**metrics,"status":"PASS_NATIVE_MACRO_0032_PARTIAL","next_line":289314,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_macro32_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro32_start(root,archive)
    require(prior["records"]==2 and prior["next_line"]==289314,"macro32 opening")
    c0=read(root,ROOT+"recovery-checkpoint-0032-partial-01-validated.json","85ebd052d3895a5a927d06cf94af0d562071a251")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0032-closure-pending.json","ac42dafea22d9fe9201e08ac8b9cbd27b53ff6b4")
    r=read(root,cp["receipt_path"],"3b83e005c409d1f3e1ad1f2ab03376fa2d8fcdfe",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[31]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="85ebd052d3895a5a927d06cf94af0d562071a251" and r["release_blob"]==c0["release_blob"]==cp["release_blob"],"checkpoint chain")
    require(r["official_unit_seal"]==m["unit_seal"] and r["previous_macro_id"]==q[30]["id"] and cp["next_macro"]==q[32],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in opening["records"]],expected_range=[289314,296900])
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    combined=dict(r,range=[289145,296900],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE)
    require(new["lines"]==7587 and new["records"]==new["coverage"]==cp["records"]==61,"new counts")
    require(result["lines"]==7756 and result["records"]==result["coverage"]==cp["macro_records"]==63,"macro counts")
    require(len({x["id"] for x in allr})==63 and all(x["book"]=="IV" and x["day"] in range(374,384) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="reserved"),"restricted isolation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(source[0][289313]=="A matriz foi acionada." and source[0][291349]=="CAPÍTULO 7 — QUANDO O MAR COMEÇOU A MORRER" and source[0][292465]=="CAPÍTULO 8 — O INIMIGO QUE PRECISOU PEDIR AJUDA" and source[0][294133]=="CAPÍTULO 9 — O DIA EM QUE O CRIADOR SUSTENTOU O HORIZONTE","chapter boundaries")
    require(len(source[0])==296900 and r["next_line"]==296901 and cp["next_line"]==q[32]["start"]==1 and cp["next_source"]==q[32]["source"]!=m["source"],"source rollover")
    require(q[32]["previous_macro"]==m["id"] and cp["staging_records"]==c0["staging_records"]+61==2363 and cp["book_counts"]["IV"]==241 and cp["completed_macros"]==31,"staging totals")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0032_COMPLETE","new_records":new["records"],"new_lines":new["lines"],"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":1,"next_source":q[32]["source"],"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_macro33_start(root,archive):
    from collections import Counter
    from .omega_turbo_recovery import anchor
    root=Path(root); archive=Path(archive)
    prior=verify_macro32_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0032-validated.json","f6e04bad6a9d7fe846eafae99f0cee71e79c3d5b")
    require(prior["macro_complete"] and c0["native_validation"]=="PASS" and c0["next_line"]==1,"macro32 validated gate")
    cp=read(root,ROOT+"recovery-checkpoint-0033-partial-01.json","b6dabcf8e746dbdea32081eb4a651f42c125114c")
    r=read(root,cp["receipt_path"],"cc61ce1a59318eb92224ef34c3ffc8e12021ace8",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[32]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="f6e04bad6a9d7fe846eafae99f0cee71e79c3d5b" and r["release_blob"]==c0["release_blob"]==cp["release_blob"],"checkpoint chain")
    require(c0["next_macro"]==m and c0["next_source"]==cp["source"]==r["source"]==m["source"] and r["previous_macro_id"]==q[31]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    require(len(source[0])==85803 and r["source_sha256"]==source[3] and r["range"]==[1,2413] and r["macro_range"]==[1,10229],"source geometry")
    # The original core validator accepts Prompt/Response only. Verify the exact
    # leading Metadata span separately, then use the unmodified validator for
    # every remaining line. Do not turn export-header data into a narrative event.
    header=r["records"][0]; e=header["evidence"]; cov=r["coverage"][0]
    require(header["type"]=="metadata" and header["authority"]=="METADATA_NOT_EVENT" and header["promotion"] is False and not header["entities"] and header["visibility"]=="EDITORIAL_ONLY_NO_CHARACTER_INJECTION","header authority")
    require(e["source"]==m["source"] and e["source_sha256_manifest"]==source[3] and (e["line_start"],e["line_end"],e["role"])==(1,8,"Metadata"),"header scope")
    require(set(source[1][:8])=={"Metadata"} and source[1][8]=="Prompt" and anchor(source,1,8)==e["span_sha256_utf8"],"header hash and roles")
    require(e["blob_sha1"] in {p[2] for p in source[2] if p[0]<=8 and p[1]>=1},"header provenance")
    require(cov["start"]==1 and cov["end"]==8 and cov["role"]=="Metadata" and cov["span_sha256_utf8"]==e["span_sha256_utf8"] and cov["record_ids"]==[header["id"]] and cov["disposition"]=="NON_NARRATIVE_EXPORT_HEADER","header coverage")
    prev1=read(root,ROOT+"partial-macro-0032-01.json")
    prev2=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    ids=[x["id"] for x in prev1["records"]+prev2["records"]]
    require(header["id"] not in ids and header["axes"]==[29,30],"header identity")
    rr=r["records"][1:]
    sub=dict(r,range=[9,2413],records=rr,coverage=r["coverage"][1:],axis_coverage={"assessed":list(range(1,31)),"represented":sorted({a for x in rr for a in x["axes"]})})
    result=validate_receipt(sub,m,source,r["project"],ARCHIVE,previous_ids=ids+[header["id"]],expected_range=[9,2413])
    allr=r["records"]; represented=sorted({a for x in allr for a in x["axes"]})
    require(r["axis_coverage"]=={"assessed":list(range(1,31)),"represented":represented},"axis ledger")
    require(len(allr)==len(r["coverage"])==cp["records"]==result["records"]+1==29 and result["lines"]+8==2413,"partial counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==10 and x["day"] in range(383,387) and x["promotion"] is False for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(all(source[0][i-1]=="## Prompt:" for i in (9,2154,2159)) and all(source[0][i-1]=="## Response:" for i in (18,2164)),"role boundaries")
    require(source[0][2412]=="Mas o SISTEMA falou primeiro." and source[0][2413]=="" and source[0][2414].startswith("— E, antes que pergunte"),"continuation")
    require(cp["next_line"]==r["next_line"]==2414 and cp["staging_records"]==c0["staging_records"]+29==2392 and cp["book_counts"]["IV"]==270 and cp["completed_macros"]==32,"checkpoint")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["macro_complete"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0033_PARTIAL","lines":2413,"records":29,"coverage":29,"header_metadata_lines":8,"axes_represented":represented,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":2414,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_macro33_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro33_start(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0033-partial-01-validated.json","ded055d72640efb92eb74e88fdc60e5882e076c7")
    require(prior["next_line"]==c0["next_line"]==2414 and c0["native_validation"]=="PASS","prior gate")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0033-closure-pending.json","d3f686b52bf52c7653a175fb6fd8195efdb141e8")
    r=read(root,cp["receipt_path"],"14f2d9d312302c47cde543e7d3fb3c27ef361e26",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[32]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="ded055d72640efb92eb74e88fdc60e5882e076c7" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"chain")
    require(r["previous_macro_id"]==q[31]["id"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[33],"queue")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in opening["records"]],expected_range=[2414,10229])
    # Header 1–8 already independently verified by verify_macro33_start.
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    rr=allr[1:]
    combined=dict(r,range=[9,10229],records=rr,coverage=allc[1:],axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in rr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE,expected_range=[9,10229])
    require(new["lines"]==7816 and new["records"]==new["coverage"]==cp["records"]==51,"new counts")
    require(result["lines"]+8==10229 and result["records"]+1==result["coverage"]+1==cp["macro_records"]==80,"macro counts")
    require(len({x["id"] for x in allr})==80 and all(x["book"]=="IV" and x["chapter_hint"]==10 and x["day"] in range(383,389) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(source[0][9358]=="300×" and source[0][9512]=="100×" and source[0][9354]=="100×","power reference")
    require(source[0][10229]=="" and source[0][10230]=="LUCAS observou os recipientes.","literal continuation")
    require(cp["next_line"]==r["next_line"]==q[33]["start"]==10230 and q[33]["previous_macro"]==m["id"] and q[33]["source"]==m["source"],"next queue")
    require(cp["staging_records"]==c0["staging_records"]+51==2443 and cp["book_counts"]["IV"]==321 and cp["completed_macros"]==32,"staging counts")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0033_COMPLETE","lines":10229,"records":80,"coverage":80,"header_metadata_lines":8,"new_records":51,"new_lines":7816,"axes_represented":sorted({i for x in allr for i in x["axes"]}),"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":10230,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_macro34_start(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro33_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0033-validated.json","c4d65f3c8e3ed1d08cc05b3d5f15cc9b05ef2f6a")
    require(prior["macro_complete"] and c0["native_validation"]=="PASS" and c0["next_line"]==10230,"macro33 validated gate")
    cp=read(root,ROOT+"recovery-checkpoint-0034-partial-01.json","d7f48c9025c2d9a10ffe331ed4190a727d4cb165")
    r=read(root,cp["receipt_path"],"7e81adcd636b4d35428d7074541cd036e67ac9ca",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[33]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="c4d65f3c8e3ed1d08cc05b3d5f15cc9b05ef2f6a" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    require(c0["next_macro"]==m and r["previous_macro_id"]==q[32]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    p1=read(root,ROOT+"partial-macro-0033-01.json")
    p2=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in p1["records"]+p2["records"]],expected_range=[10230,12413])
    allr=r["records"]
    require(result["lines"]==2184 and result["records"]==result["coverage"]==cp["records"]==20,"counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==10 and x["day"] in (388,389) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(all(x["visibility"]=="RESTRICTED_KNOWLEDGE_NO_CHARACTER_INJECTION" for x in allr if x["type"]=="knowledge"),"private knowledge separation")
    require(source[0][11202]=="## Prompt:" and source[0][11207]=="## Response:" and source[0][12413]=="" and source[0][12414]=="— Ainda.","literal anchors")
    require(cp["next_line"]==r["next_line"]==12414 and cp["staging_records"]==c0["staging_records"]+20==2463 and cp["book_counts"]["IV"]==341 and cp["completed_macros"]==33,"checkpoint")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["macro_complete"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0034_PARTIAL","authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":12414,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_macro34_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro34_start(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0034-partial-01-validated.json","59de9e77c58e7dbb717007629a14e8b1b4e75e19")
    require(prior["next_line"]==c0["next_line"]==12414 and c0["native_validation"]=="PASS","prior gate")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0034-closure-pending.json","15a517b48aa2749995012602a7597ebdeb201dac")
    r=read(root,cp["receipt_path"],"b91bd09a544849ab065b114e3295a1c946354a5e",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[33]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="59de9e77c58e7dbb717007629a14e8b1b4e75e19" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"chain")
    require(r["previous_macro_id"]==q[32]["id"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[34],"queue")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=[x["id"] for x in opening["records"]],expected_range=[12414,20427])
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    combined=dict(r,range=[10230,20427],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE)
    require(new["lines"]==8014 and new["records"]==new["coverage"]==cp["records"]==50,"new counts")
    require(result["lines"]==10198 and result["records"]==result["coverage"]==cp["macro_records"]==70,"macro counts")
    require(len({x["id"] for x in allr})==70 and all(x["book"]=="IV" and x["chapter_hint"] in (10,11) and x["day"] in range(388,394) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader isolation")
    require(all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private knowledge")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(source[0][14548]=="CAEDREN." and source[0][18322]=="## Prompt:" and "cinco arcos" in source[0][18325] and "Dia 423" in source[0][17714],"literal narrative anchors")
    require(source[0][20427]=="" and source[0][20428]=="— Vamos fazer isso direito.","literal continuation")
    require(cp["next_line"]==r["next_line"]==q[34]["start"]==20428 and q[34]["previous_macro"]==m["id"],"next queue")
    require(cp["staging_records"]==c0["staging_records"]+50==2513 and cp["book_counts"]["IV"]==391 and cp["completed_macros"]==33,"staging counts")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0034_COMPLETE","new_records":50,"new_lines":8014,"next_line":20428,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_cycle_30_34(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro34_close(root,archive)
    require(prior["macro_complete"],"closure")
    review=read(root,ROOT+"cycle-0030-0034-consolidated-review-pending.json","8f7c55cf13a36a5ba07821f4e2cfbb96fdc06de4")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    allr=[]; total=0
    for i,g in enumerate(review["macros"],30):
        m=q[i-1]; cursor=m["start"]; group=[]
        require(g["macro"]==i,"cycle order")
        for entry in g["receipts"]:
            r=read(root,entry["path"],entry["blob"])
            require(r["range"]==entry["range"] and r["range"][0]==cursor and r["macro_id"]==m["id"] and r["source"]==m["source"],"cycle range")
            cursor=r["range"][1]+1;group.extend(r["records"])
        axes=sorted({a for x in group for a in x["axes"]})
        require(cursor==m["end"]+1 and g["lines"]==m["lines"] and g["records"]==len(group),"cycle coverage")
        require(g["axes_represented"]==axes and g["axes_unrepresented"]==sorted(set(range(1,31))-set(axes)),"axis report")
        total+=g["lines"];allr.extend(group)
    axes=sorted({a for x in allr for a in x["axes"]}); ids={x["id"] for x in allr}
    t=review["totals"]
    require(total==t["lines"]==48624 and len(allr)==len(ids)==t["records"]==t["unique_ids"]==391 and axes==t["axes_represented"]==list(range(1,31)),"cycle totals")
    require(t["authority_counts"]==dict(Counter(x["authority"] for x in allr)) and t["visibility_counts"]==dict(Counter(x["visibility"] for x in allr)),"cycle authority ledger")
    require(all(x["promotion"] is False for x in allr),"no promotion")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene"),"reader boundary")
    require(all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="reserved"),"reserved boundary")
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    s1=cache.get(q[31]["source"])[0]; s2=cache.get(q[32]["source"])[0]
    require("O menino" in s1[291357] and "sua mãe" in s1[291357] and "MARA" in s1[291367] and "O homem observava" in s2[4948],"Tilo conflict preserved")
    require("300×"==s2[9358] and "100×"==s2[9512] and "100×"==s2[9354],"power anchors")
    require(review["checks"]["production_gate"]=="HOLD" and review["checks"]["semantic_exhaustive"] is False and review["checks"]["independent_review"] is False,"review scope")
    return {**prior,"status":"PASS_NATIVE_CYCLE_0030_0034","cycle_lines":total,"cycle_records":len(allr),"cycle_unique_ids":len(ids),"cycle_axes_represented":axes,"cycle_authority_counts":t["authority_counts"],"cycle_visibility_counts":t["visibility_counts"],"cycle_review":"PASS_STAGING_ONLY","tilo_resolution":"UNRESOLVED_NO_MERGE","macro33_axes_represented":29}

def verify_macro35_start(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_cycle_30_34(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0034-validated.json","8354b031b5318f640b094266d47dbd94b089f08d")
    review=read(root,c0["cycle_review_path"],"3f8f84f05aef6963e0955f9fab2fdb77b99311b1")
    require(prior["macro_complete"] and c0["native_validation"]=="PASS" and c0["next_line"]==20428 and c0["cycle_consolidated_review"]==review["status"]=="PASS_STAGING_ONLY" and review["release"]=="APPROVED_STAGING_ONLY","cycle release")
    cp=read(root,ROOT+"recovery-checkpoint-0035-partial-01.json","6737be346264afaf0e08c7c4eac284ea47e6e241")
    r=read(root,cp["receipt_path"],"6cd26612896f3de794cd48e2d47a5ca0ba9a71f8",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[34]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="8354b031b5318f640b094266d47dbd94b089f08d" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    require(c0["next_macro"]==m and r["previous_macro_id"]==q[33]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    ids=[]
    for g in review["macros"]:
        for entry in g["receipts"]:
            ids.extend(x["id"] for x in read(root,entry["path"],entry["blob"])["records"])
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=[20428,22413])
    allr=r["records"]
    require(result["lines"]==1986 and result["records"]==result["coverage"]==cp["records"]==20,"counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==11 and x["day"] in (393,394) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata separation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"teaser separation")
    require(all(x["visibility"]=="RESTRICTED_KNOWLEDGE_NO_CHARACTER_INJECTION" for x in allr if x["type"]=="knowledge"),"private knowledge separation")
    require(all(x["visibility"]=="READER_ONLY_NO_CHARACTER_INJECTION" for x in allr if x["type"]=="reader_scene"),"reader separation")
    require(source[0][21522]=="## Prompt:" and source[0][21527]=="## Response:" and "29 dias"==source[0][21550] and "HORIZONTE CAFÉ" in source[0][21694] and source[0][22413]=="" and source[0][22414]=="— Então vamos fazer isso direito.","literal anchors")
    require(cp["next_line"]==r["next_line"]==22414 and cp["staging_records"]==c0["staging_records"]+20==2533 and cp["book_counts"]["IV"]==411 and cp["completed_macros"]==34,"checkpoint")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["macro_complete"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0035_PARTIAL","authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr)),"next_line":22414,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"prior_cycle_release":"PASS_STAGING_ONLY","prior_cycle_review_blob":c0["cycle_review_blob"]}


def verify_macro35_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro35_start(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0035-partial-01-validated.json","e10b5d3eb10453eb8a4329b9c06a8972caf7a33f")
    require(prior["next_line"]==c0["next_line"]==22414 and c0["native_validation"]=="PASS","prior checkpoint")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0035-closure-pending.json","a406730d2fa7d4a5e9c0d9a7b2f554b0862f78d2")
    r=read(root,cp["receipt_path"],"77050dadfec1d00e5366b675432525d60b0c56cf",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]; m=q[34]
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="e10b5d3eb10453eb8a4329b9c06a8972caf7a33f" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    require(r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[35],"queue chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    review=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids+[x["id"] for x in opening["records"]],expected_range=[22414,30641])
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    combined=dict(r,range=[20428,30641],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE,previous_ids=ids)
    require(new["lines"]==8228 and new["records"]==new["coverage"]==cp["records"]==38,"new counts")
    require(result["lines"]==10214 and result["records"]==cp["macro_records"]==58,"macro counts")
    require(cp["staging_records"]==c0["staging_records"]+new["records"] and cp["book_counts"]["IV"]==c0["book_counts"]["IV"]+new["records"],"staging counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==11 and x["day"] in range(393,400) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in r["records"] if x["type"] in ("variant","reader_scene")),"reader/variant isolation")
    require(all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"option separation")
    require(source[0][25104]=="## Prompt:" and "futebol já foi apresentado" in source[0][25107] and "substitui integralmente" in source[0][25152],"author revision")
    require("trezentas vezes" in source[0][27478] and "OBSERVAÇÃO EXTERNA."==source[0][30128],"power and antagonist anchors")
    require(cp["next_line"]==r["next_line"]==q[35]["start"]==30642 and q[35]["previous_macro"]==m["id"],"next cursor")
    require(cp["native_validation"]=="PENDING" and cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0035_COMPLETE","new_records":new["records"],"new_lines":8228,"next_line":30642,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_macro36_start(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro35_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0035-validated.json","4cf6dbe88aaf3689627e8cb5f8d2de2e8bbe03e5")
    require(prior["macro_complete"] and prior["next_line"]==c0["next_line"]==30642 and c0["native_validation"]=="PASS","prior validated checkpoint")
    cp=read(root,ROOT+"recovery-checkpoint-0036-partial-01.json","2ff961ff24ad4c1f43985c22c5a92776a614ed44")
    r=read(root,cp["receipt_path"],"c853ff4a4cb7a5a76a967486e6192bbc9df457bc",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]; m=q[35]
    require(c0["next_macro"]==cp["next_macro"]==m and r["previous_macro_id"]==q[34]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="4cf6dbe88aaf3689627e8cb5f8d2de2e8bbe03e5" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    review=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    for name in ("partial-macro-0035-01.json","partial-macro-0035-02.json"):
        ids.extend(x["id"] for x in read(root,ROOT+name)["records"])
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=[30642,32413])
    allr=r["records"]
    require(result["lines"]==1772 and result["records"]==result["coverage"]==cp["records"]==9,"counts")
    require(cp["staging_records"]==c0["staging_records"]+9==2580 and cp["book_counts"]["IV"]==458 and cp["completed_macros"]==35,"staging counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==11 and x["day"] in (399,400) for x in allr),"scope")
    require(all(x["evidence"]["role"]=="Response" for x in allr),"roles")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene") and all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private boundary")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata"),"metadata")
    require("Se Eu Souber Voltar" in source[0][31852] and "As Mãos Que Me Trouxeram" in source[0][32202],"distinct songs")
    require(source[0][32412]=="— AGORA SENTEM, PORQUE A COMIDA ESTÁ ESFRIANDO!" and source[0][32413]=="","literal boundary")
    require(cp["next_line"]==r["next_line"]==32414 and not cp["macro_complete"] and cp["native_validation"]=="PENDING","partial checkpoint")
    require(cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0036_PARTIAL","session_new_lines":10000,"session_new_records":47,"next_line":32414,"macro_complete":False,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_macro36_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro36_start(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0036-partial-01-validated.json","e13d94a207cd3d3d18ef9fa5e9bb87af71e35f08")
    require(prior["next_line"]==c0["next_line"]==32414 and c0["native_validation"]=="PASS","prior validated checkpoint")
    opening=read(root,c0["receipt_path"],c0["receipt_blob"],c0["receipt_sha256"])
    cp=read(root,ROOT+"recovery-checkpoint-0036-closure-pending.json","70b076c3f3017224143cf3fe303d3ec8532c47b3")
    r=read(root,cp["receipt_path"],"4d9faa2f2b308f43b90aeea357a391d79a7e82c9",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]; m=q[35]
    require(c0["next_macro"]==m and cp["next_macro"]==q[36] and r["previous_macro_id"]==q[34]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="e13d94a207cd3d3d18ef9fa5e9bb87af71e35f08" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    review=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    for name in ("partial-macro-0035-01.json","partial-macro-0035-02.json"):
        ids.extend(x["id"] for x in read(root,ROOT+name)["records"])
    new=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids+[x["id"] for x in opening["records"]],expected_range=[32414,40763])
    allr=opening["records"]+r["records"]; allc=opening["coverage"]+r["coverage"]
    combined=dict(r,range=[30642,40763],records=allr,coverage=allc,axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in allr for i in x["axes"]})})
    result=validate_receipt(combined,m,source,r["project"],ARCHIVE,previous_ids=ids)
    require(new["lines"]==8350 and new["records"]==new["coverage"]==cp["records"]==39,"new counts")
    require(result["lines"]==10122 and result["records"]==cp["macro_records"]==48,"macro counts")
    require(cp["staging_records"]==c0["staging_records"]+39==2619 and cp["book_counts"]["IV"]==497 and cp["completed_macros"]==36,"staging counts")
    require(all(x["book"]=="IV" and x["chapter_hint"] in (11,12) and x["day"] in range(399,408) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene") and all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private boundary")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata") and all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"non-event separation")
    require(source[0][36734]=="Pouco acima de um metro." and "CAEDREN chegou" in source[0][37144] and "não associou" in source[0][37712],"ARGOS and identity anchors")
    require(source[0][38306]=="FIM DO CAPÍTULO 11" and source[0][38358]=="## Prompt:" and source[0][38363]=="## Response:" and source[0][38352].startswith("4. ESPECIAL"),"chapter and option anchors")
    require("TALIS ELVENAR" in source[0][39186] and "não chegou" in source[0][39340],"Talis and diplomacy anchors")
    require(cp["next_line"]==r["next_line"]==q[36]["start"]==40764 and q[36]["previous_macro"]==m["id"],"next cursor")
    require(cp["native_validation"]=="PENDING" and cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0036_COMPLETE","new_records":new["records"],"new_lines":8350,"session_new_lines":18350,"session_new_records":86,"next_line":40764,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_macro37_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro36_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0036-validated.json","36b684b9e232d651c2699f5f86610539d08698fe")
    require(prior["macro_complete"] and prior["next_line"]==c0["next_line"]==40764 and c0["native_validation"]=="PASS","prior checkpoint")
    cp=read(root,ROOT+"recovery-checkpoint-0037-closure-pending.json","a2c5d831e561f09321123fa5a7f24b4140b25157")
    r=read(root,cp["receipt_path"],"8fe4504e3d81643f2fe7a2b1008ce9097e4de4f6",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"];m=q[36]
    require(c0["next_macro"]==m and cp["next_macro"]==q[37] and r["previous_macro_id"]==q[35]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="36b684b9e232d651c2699f5f86610539d08698fe" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    review=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    for name in ("partial-macro-0035-01.json","partial-macro-0035-02.json","partial-macro-0036-01.json","partial-macro-0036-02.json"):
        ids.extend(x["id"] for x in read(root,ROOT+name)["records"])
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids)
    allr=r["records"]
    require(result["lines"]==10026 and result["records"]==result["coverage"]==cp["records"]==48,"counts")
    require(cp["staging_records"]==c0["staging_records"]+48==2667 and cp["book_counts"]["IV"]==545,"staging counts")
    require(all(x["book"]=="IV" and x["chapter_hint"] in (12,13) and x["day"] in range(407,415) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene") and all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private boundary")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata") and all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"non-event separation")
    require(source[0][42098]=="## Prompt:" and "ir para o capítulo 13" in source[0][42101] and "sem inventar acontecimentos" in source[0][42110],"author chapter exception")
    require("Nenhuma das duas sabia" in source[0][44620] and "ainda não decidi" in source[0][45076],"identity and consent")
    require(source[0][47362]=="ESTÚDIO DOS HORIZONTES" and "Sem Coroa, Sem Correntes" in source[0][47532] and "Gravidade Zero" in source[0][50073],"studio and songs")
    require("Não porque fosse o hino cívico" in source[0][47696] and "TREZENTAS VEZES" in source[0][49342],"music status and power")
    require(cp["next_line"]==r["next_line"]==q[37]["start"]==50790 and q[37]["previous_macro"]==m["id"],"next cursor")
    require(cp["native_validation"]=="PENDING" and cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0037_COMPLETE","next_line":50790,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_macro38_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro37_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0037-validated.json","a54ff516aac010f9208b9e4a9b1c01d8ec636cf8")
    require(prior["macro_complete"] and prior["next_line"]==c0["next_line"]==50790 and c0["native_validation"]=="PASS","prior checkpoint")
    cp=read(root,ROOT+"recovery-checkpoint-0038-closure-pending.json","7efb86b5e7af073abd1e4ba5b535f858b4bc1658")
    r=read(root,cp["receipt_path"],"740c2efeb819adbbda9683d3542f773d53b536f0",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"];m=q[37]
    require(c0["next_macro"]==m and cp["next_macro"]==q[38] and r["previous_macro_id"]==q[36]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="a54ff516aac010f9208b9e4a9b1c01d8ec636cf8" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    review=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    for name in ("partial-macro-0035-01.json","partial-macro-0035-02.json","partial-macro-0036-01.json","partial-macro-0036-02.json","partial-macro-0037-01.json"):
        ids.extend(x["id"] for x in read(root,ROOT+name)["records"])
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids)
    allr=r["records"]
    require(result["lines"]==10132 and result["records"]==result["coverage"]==cp["records"]==50,"counts")
    require(cp["staging_records"]==c0["staging_records"]+50==2717 and cp["book_counts"]["IV"]==595,"staging counts")
    require(cp["session_new_lines"]==prior["lines"]+result["lines"]==20158 and cp["session_new_records"]==prior["records"]+result["records"]==98,"session counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==13 and x["day"] in range(414,421) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene") and all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private boundary")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata") and all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"non-event separation")
    require("referência estática" in source[0][53774] and "não o reconheceu" in source[0][53856],"Farol and identity")
    require("Aceitava o prazo" in source[0][54926] and "agenda da rainha" in source[0][54930],"diplomacy date separation")
    require("MIREN lhe dera" in source[0][55106] and "Hoje fui feliz" in source[0][59578] and "pato de borracha" in source[0][59578],"open discrepancies")
    require("Outro azul-claro" in source[0][55964] and "casamento" in source[0][57020] and "se ela quiser" in source[0][57112] and "sequer havia sido convidada" in source[0][57372],"duck and private marriage")
    require("diferenças entre a resposta de orientação" in source[0][58562] and "verificações locais foram concluídas" in source[0][60574] and "convidado civil" in source[0][60576] and "continuava desconhecida" in source[0][60586],"ARGOS and invitation gate")
    require(source[0][60920]=="CAEDREN acompanhou." and 21 not in result["axes_represented"],"source boundary and axis restraint")
    require(cp["next_line"]==r["next_line"]==q[38]["start"]==60922 and q[38]["previous_macro"]==m["id"],"next cursor")
    require(cp["native_validation"]=="PENDING" and cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0038_COMPLETE","session_new_lines":20158,"session_new_records":98,"next_line":60922,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_macro39_cycle(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro38_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0038-validated.json","648933703e70f06ebf7fa94dac1c29d9ef660686")
    require(prior["next_line"]==c0["next_line"]==60922 and c0["native_validation"]=="PASS","prior checkpoint")
    cp=read(root,ROOT+"recovery-checkpoint-0039-closure-pending.json","bc719a61a1392cb0364d52994764dc1af4daf011")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    r=read(root,cp["receipt_path"],"17dafce10337c1df360b788e4e8e2a52bba8e28c",cp["receipt_sha256"])
    require(c0["next_macro"]==q[38] and cp["next_macro"]==q[39] and r["previous_macro_id"]==q[37]["id"] and r["official_unit_seal"]==q[38]["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="648933703e70f06ebf7fa94dac1c29d9ef660686" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(q[38]["source"])
    review=read(root,ROOT+"cycle-0035-0039-consolidated-review-pending.json","227ddd8476f7f5665adf3fcee9bcd24fb0826964")
    old=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    ids={x["id"] for g in old["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    new_ids=set(); axes=set(); authority=Counter(); visibility=Counter(); at=20428; total_lines=0
    require([g["macro"] for g in review["macros"]]==list(range(35,40)),"cycle range")
    for g in review["macros"]:
        m=q[g["macro"]-1]; ga=set(); gc=0; gl=0
        require(at==m["start"],"cycle macro start")
        for entry in g["receipts"]:
            a=read(root,entry["path"],entry["blob"])
            require(a["range"]==entry["range"] and a["range"][0]==at and a["range"][1]<=m["end"] and a["official_unit_seal"]==m["unit_seal"] and a["previous_macro_id"]==m["previous_macro"],"receipt chain")
            v=validate_receipt(a,m,source,a["project"],ARCHIVE,previous_ids=ids|new_ids,expected_range=a["range"])
            for x in a["records"]:
                require(x["book"]=="IV" and not x["promotion"] and "NO_CHARACTER_INJECTION" in x["visibility"],"scope")
                require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"role authority")
                if x["type"] in ("reader_scene","variant"):
                    require(x["visibility"].startswith("READER_ONLY"),"reader privacy")
                if x["type"]=="knowledge":
                    require(x["visibility"].startswith("RESTRICTED"),"restricted privacy")
                new_ids.add(x["id"]); authority[x["authority"]]+=1;visibility[x["visibility"]]+=1
            ga.update(v["axes_represented"]);gc+=v["records"];gl+=v["lines"];at=a["range"][1]+1
        require(at==m["end"]+1 and gl==g["lines"]==m["lines"] and gc==g["records"] and sorted(ga)==g["axes_represented"] and sorted(set(range(1,31))-ga)==g["axes_unrepresented"],"macro totals")
        axes.update(ga);total_lines+=gl
    totals=review["totals"]
    require(at==71160==cp["next_line"] and total_lines==totals["lines"]==50732 and len(new_ids)==totals["records"]==totals["unique_ids"]==254,"cycle totals")
    require(dict(authority)==totals["authority_counts"] and dict(visibility)==totals["visibility_counts"] and sorted(axes)==totals["axes_represented"]==list(range(1,31)),"axis/authority totals")
    require(cp["records"]==len(r["records"])==50 and cp["staging_records"]==c0["staging_records"]+50==totals["staging_records"]==2767 and totals["official_records"]==1656,"staging counts")
    from hashlib import sha256
    for finding in review["findings"]:
        require(not finding["promotion"],"finding promoted")
        for e in finding["evidence"]:
            lo,hi=e["range"];require(e["source"]==q[38]["source"] and sha256("\n".join(source[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"finding anchor")
    require("Não precisamos mais do contador" in source[0][64639] and source[0][66154]=="## Prompt:" and source[0][66238].startswith("DIA 3 ·"),"author override and flashback")
    require("LEGIÃO" in source[0][66774] and "DIA 3" in source[0][65940] and "não uma patente" in source[0][66964].lower(),"brooch variants")
    require("A Estrada Tem Poeira e o KAEL Tem Razão" in source[0][70342] and "caminhão imobilizado" in source[0][70059],"song and safety")
    require("não temos dados" in source[0][70963] and "não possuía campo antigravitacional" in source[0][65120].lower(),"transport boundary")
    require(review["status"]=="PENDING_NATIVE_STAGING_REVIEW" and cp["native_validation"]=="PENDING" and review["production_gate"]==cp["production_gate"]=="HOLD" and not any(review[x] or cp[x] for x in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_MACRO_0039_COMPLETE","cycle_status":"PASS_STAGING_ONLY","lines":10238,"records":50,"cycle_lines":total_lines,"cycle_records":len(new_ids),"cycle_axes":sorted(axes),"next_line":71160,"staging_records":2767,"macro_complete":True,"production_gate":"HOLD","semantic_certification":False,"canon_changed":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_macro39_cycle(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
