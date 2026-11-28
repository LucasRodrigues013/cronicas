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


def verify_macro40_close(root,archive):
    from collections import Counter
    root=Path(root); archive=Path(archive)
    prior=verify_macro39_cycle(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0039-validated.json","96871d1cf145b71eb8ec465432627e819eeb5c92")
    review=read(root,c0["cycle_review_path"],"eb0aa0cbd92dc251920145f15f83ba174c18c536")
    require(prior["next_line"]==c0["next_line"]==71160 and c0["native_validation"]=="PASS" and prior["cycle_status"]==review["status"]=="PASS_STAGING_ONLY" and review["recovery_gate"]=="AUTHORIZED_STAGING_ONLY","mandatory release")
    require(review["totals"]["records"]==prior["cycle_records"]==254 and review["totals"]["lines"]==prior["cycle_lines"]==50732,"cycle binding")
    cp=read(root,ROOT+"recovery-checkpoint-0040-closure-pending.json","781a4c7738f6c0d75bace52b24fc09b54ff35ac4")
    r=read(root,cp["receipt_path"],"479b93062eb1e47bd7b804e428af81b5b64569b8",cp["receipt_sha256"])
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"];m=q[39]
    require(c0["next_macro"]==m and cp["next_macro"]==q[40] and r["previous_macro_id"]==q[38]["id"] and r["official_unit_seal"]==m["unit_seal"],"queue chain")
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="96871d1cf145b71eb8ec465432627e819eeb5c92" and r["cycle_review_blob"]==cp["cycle_review_blob"]=="eb0aa0cbd92dc251920145f15f83ba174c18c536" and r["release_blob"]==cp["release_blob"]==c0["release_blob"],"checkpoint chain")
    source=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b")).get(m["source"])
    ids=[x["id"] for g in review["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"]]
    previous=read(root,ROOT+"cycle-0030-0034-consolidated-review-validated.json","3f8f84f05aef6963e0955f9fab2fdb77b99311b1")
    ids.extend(x["id"] for g in previous["macros"] for entry in g["receipts"] for x in read(root,entry["path"],entry["blob"])["records"])
    require(len(ids)==len(set(ids)),"prior IDs")
    result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids)
    allr=r["records"]
    require(result["lines"]==10016 and result["records"]==result["coverage"]==cp["records"]==48,"counts")
    require(cp["staging_records"]==c0["staging_records"]+48==2815 and cp["book_counts"]["IV"]==693,"staging counts")
    require(cp["session_new_lines"]==prior["lines"]+result["lines"]==20254 and cp["session_new_records"]==prior["records"]+result["records"]==98,"session counts")
    require(all(x["book"]=="IV" and x["chapter_hint"]==14 and x["day"] in range(424,431) for x in allr),"scope")
    require(all((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT") for x in allr),"author separation")
    require(all(x["visibility"].startswith("READER_ONLY") for x in allr if x["type"]=="reader_scene") and all(x["visibility"].startswith("RESTRICTED") for x in allr if x["type"]=="knowledge"),"private boundary")
    require(all(x["authority"]=="METADATA_NOT_EVENT" for x in allr if x["type"]=="metadata") and all(x["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" for x in allr if x["type"]=="transition_options"),"non-event separation")
    require("DÉLIA autorizou" in source[0][74400] and "contenção temporária" in source[0][74398] and "sem transferência de direitos" in source[0][74568],"moinho boundary")
    require("Leitura Matricial confirmou" in source[0][74480] and "frequência das observações contextuais" in source[0][77248],"power and system")
    require("documentos verdadeiros" in source[0][77940] and "não constitui autorização" in source[0][77954] and "pagou pela miniatura" in source[0][78626],"capital and identity")
    require("não havia sido concedida" in source[0][80184] and "Acompanhamento civil de observação: autorizado" in source[0][80888] and "sem direito automático" in source[0][80888],"civil permission transition")
    require("vestido azul-profundo" in source[0][81008] and source[0][81174]=="— MIREN desejava impressionar.","dress and cut")
    require(cp["next_line"]==r["next_line"]==q[40]["start"]==81176 and q[40]["previous_macro"]==m["id"],"next cursor")
    require(cp["native_validation"]=="PENDING" and cp["production_gate"]=="HOLD" and not cp["canon_changed"] and not cp["official_checkpoint_changed"] and not cp["semantic_certification"] and not cp["promotion"],"gate")
    return {**result,"status":"PASS_NATIVE_MACRO_0040_COMPLETE","prior_cycle_status":"PASS_STAGING_ONLY","session_new_lines":20254,"session_new_records":98,"next_line":81176,"macro_complete":True,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False,"authority_counts":dict(Counter(x["authority"] for x in allr)),"visibility_counts":dict(Counter(x["visibility"] for x in allr))}


def verify_book_iv_boundary(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_macro40_close(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0040-validated.json","73e3db1bb5f0c72083982a0fe3e2b85c749d18d6")
    require(prior["next_line"]==c0["next_line"]==81176 and c0["native_validation"]=="PASS","prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    review=read(root,ROOT+"book-IV-boundary-0030-0042-review-pending.json","92ff431813ab5f7e2b874aef8eacbf775d9ff38f")
    cp1=read(root,ROOT+"recovery-checkpoint-0041-closure-pending.json","a73691f531597fce0a121ac27ea90ff3eaccf1ad")
    cp2=read(root,ROOT+"recovery-checkpoint-0042-closure-pending.json","f634c993ccd47ce9bb2b31498d1a325d94282b5c")
    require(cp1["previous_checkpoint_blob"]=="73e3db1bb5f0c72083982a0fe3e2b85c749d18d6" and cp2["previous_checkpoint_blob"]=="a73691f531597fce0a121ac27ea90ff3eaccf1ad" and cp1["next_macro"]==q[41] and cp2["next_macro"]==q[42] and q[42]["book_hint"]=="V","checkpoint chain")
    require([g["macro"] for g in review["macros"]]==list(range(30,43)),"book scope")
    overlay=read(root,ROOT+"book-IV-boundary-review-overlay-01.json","6445e1451dbeab0ac0b17a0c28a2f1c572176c09")
    corrections={x["id"]:x for x in overlay["corrections"]}; used=set()
    require(not overlay["promotion"] and not overlay["canon_changed"],"overlay gate")
    ids=set();axes=set();authority=Counter();visibility=Counter();lines=0;cycle_lines=0;cycle_records=0
    for g in review["macros"]:
        m=q[g["macro"]-1];source=cache.get(m["source"]);at=m["start"];ga=set();gc=0;gl=0
        if "metadata" in g:
            e=g["metadata"];md=read(root,e["path"],e["blob"]);lo,hi=md["range"]
            require(g["macro"]==42 and (lo,hi)==(1,8) and all(x=="Metadata" for x in source[1][:8]) and md["source_sha256"]==source[3] and md["blob_sha1"]==source[2][0][2] and sha256("\n".join(source[0][:8]).encode()).hexdigest()==md["span_sha256_utf8"] and not md["promotion"],"header metadata")
            at=9;gl=8
        for e in g["receipts"]:
            r=read(root,e["path"],e["blob"])
            require(r["range"]==e["range"] and r["range"][0]==at and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"],"receipt chain")
            if g["macro"]==33 and r["range"][0]==1:
                header=r["records"][0];he=header["evidence"];hc=r["coverage"][0]
                require(header["id"]=="O8C-B33-001" and header["id"] not in ids and header["authority"]=="METADATA_NOT_EVENT" and not header["promotion"] and not header["entities"] and he["role"]=="Metadata" and [he["line_start"],he["line_end"]]==[1,8] and hc["record_ids"]==[header["id"]],"legacy header")
                require(all(x=="Metadata" for x in source[1][:8]) and he["source_sha256_manifest"]==source[3] and he["blob_sha1"]==source[2][0][2] and sha256("\n".join(source[0][:8]).encode()).hexdigest()==he["span_sha256_utf8"]==hc["span_sha256_utf8"],"legacy header hash")
                rr=r["records"][1:];sub=dict(r,range=[9,r["range"][1]],records=rr,coverage=r["coverage"][1:],axis_coverage={"assessed":list(range(1,31)),"represented":sorted({i for x in rr for i in x["axes"]})})
                v=validate_receipt(sub,m,source,r["project"],ARCHIVE,previous_ids=ids|{header["id"]},expected_range=sub["range"])
                v["lines"]+=8;v["records"]+=1;v["axes_represented"]=sorted(set(v["axes_represented"])|set(header["axes"]))
            else:
                v=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
            for x in r["records"]:
                require(x["book"]=="IV" and not x["promotion"] and "NO_CHARACTER_INJECTION" in x["visibility"],"scope")
                require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"author authority")
                if x["type"] in ("reader_scene","variant","dream"):
                    require(x["visibility"].startswith("READER_ONLY"),"reader privacy")
                effective=x["visibility"]
                if x["id"] in corrections:
                    c=corrections[x["id"]];require(c["original_receipt"]==e["blob"] and c["span_sha256"]==x["evidence"]["span_sha256_utf8"] and not c["promotion"],"overlay provenance")
                    if c["operation"]=="RESTRICT_VISIBILITY":
                        require(x["visibility"]==c["original"] and c["effective"]=="RESTRICTED_KNOWLEDGE_NO_CHARACTER_INJECTION","overlay restriction");effective=c["effective"]
                    else:
                        require(c["operation"]=="CORRECT_ENTITY_TOKENIZATION" and all(k in x["entities"] for k in c["original"]) and c["effective"]==["valdren"],"overlay entity")
                    used.add(x["id"])
                if x["type"]=="knowledge":
                    require(effective.startswith("RESTRICTED"),"restricted privacy")
                ids.add(x["id"]);authority[x["authority"]]+=1;visibility[effective]+=1
            ga.update(v["axes_represented"]);gc+=v["records"];gl+=v["lines"];at=r["range"][1]+1
        require(at==m["end"]+1 and gl==g["lines"]==m["lines"] and gc==g["records"] and sorted(ga)==g["axes_represented"],"macro totals")
        axes.update(ga);lines+=gl
        if g["macro"]>=40:cycle_lines+=gl;cycle_records+=gc
    require(used==set(corrections),"overlay coverage")
    t=review["totals"]
    require(lines==t["lines"]==122935 and len(ids)==t["records"]==773 and cycle_lines==t["cycle_lines"]==23579 and cycle_records==t["cycle_records"]==128 and sorted(axes)==t["axes_represented"]==list(range(1,31)),"review totals")
    for e in review["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"finding anchor")
    s2=cache.get(q[40]["source"])[0];s3=cache.get(q[41]["source"])[0]
    require("Herói das Sete Estradas" in s2[82688] and "não constitui compromisso militar" in s2[83522] and "Nenhum tratado definitivo" in s2[84076],"identity and diplomacy")
    require("PROTOCOLO DAS TRÊS PORTAS" in s3[1926] and "Matriz de Fundação" in s3[4069] and "pare, consulte" in s3[7376] and "Círan permanece em Calderva" in s3[8907],"author correction and continuity")
    require("T. Elvenar" in s3[7943] and "O Capítulo 15 está encerrado" in s3[8933] and s3[8935]=="## Prompt:","boundary")
    require(cp1["staging_records"]==2815+19 and cp2["staging_records"]==2895==t["staging_records"] and cp2["book_counts"]["IV"]==len(ids) and t["official_records"]==1656,"staging counts")
    require(all(x["production_gate"]=="HOLD" and not any(x[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")) for x in (cp1,cp2,review)),"gate")
    return {"status":"PASS_NATIVE_BOOK_IV_0042_COMPLETE","cycle_status":"PASS_STAGING_ONLY","book_status":"PASS_STAGING_ONLY","book_lines":lines,"book_records":len(ids),"cycle_lines":cycle_lines,"cycle_records":cycle_records,"session_lines":13563,"session_records":80,"macro41_lines":4628,"macro42_lines":8935,"metadata_lines":8,"axes":sorted(axes),"authority_counts":dict(authority),"visibility_counts":dict(visibility),"next_line":8936,"staging_records":2895,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_opening(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    previous=verify_book_iv_boundary(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0042-validated.json","a04302e6acea0af0f7da751f0efb03aeb23fdf0a")
    boundary=read(root,c0["book_boundary_review_path"],"ac930832759e89e93e5ca801894267a0a6fb3a2e")
    require(previous["book_status"]==boundary["status"]==c0["book_boundary_status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and previous["staging_records"]==c0["staging_records"]==2895,"prior boundary gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"book-V-opening-0043-0045-review-pending.json","73d26775a28261f4957f42bfe745f9f9aef36a62")
    require(audit["previous_boundary_blob"]==c0["book_boundary_review_blob"] and [g["macro"] for g in audit["macros"]]==[43,44,45],"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    require(len(ids)==773,"prior IDs")
    prior_blob="a04302e6acea0af0f7da751f0efb03aeb23fdf0a";counts=Counter();vis=Counter();axes=set();total=0;records=0;metrics=[]
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prior_blob and r["release_blob"]==cp["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        require(cp["macro_range"]==r["macro_range"]==[m["start"],m["end"]] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        extra=0
        if n==45:
            md=read(root,cp["metadata_path"],cp["metadata_blob"]);require(md["range"]==[1,8] and md["source"]==m["source"] and md["source_sha256"]==source[3] and md["blob_sha1"]==source[2][0][2] and all(x=="Metadata" for x in source[1][:8]) and sha256("\n".join(source[0][:8]).encode()).hexdigest()==md["span_sha256_utf8"] and not md["promotion"],"metadata header")
            require(r["range"]==[9,m["end"]] and m["book_hint"]=="V_OR_VI_UNRESOLVED" and source[0][327]=="LIVRO V — ALÉM DAS ÚLTIMAS ESTRADAS" and "DIA ACUMULADO 442" in source[0][345],"book resolution")
            extra=8
        else:
            require(r["range"]==[m["start"],m["end"]] and m["book_hint"]=="V","book scope")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]+extra==g["lines"]==m["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and (x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["day"] is not None or x["authority"] in ("AUTHOR_DIRECTION_NOT_EVENT","METADATA_NOT_EVENT"),"editorial not event")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader isolation")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"private isolation")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        total+=g["lines"];records+=g["records"];axes.update(g["axes"]);prior_blob=g["checkpoint_blob"]
        require(cp["staging_records"]==2895+records and cp["book_counts"]["V"]==records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"staging")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"finding anchor")
    s3=cache.get(q[42]["source"])[0];s4=cache.get(q[44]["source"])[0]
    require(s3[8935]=="## Prompt:" and s3[8981]=="LIVRO V" and s3[8983]=="ALÉM DAS ÚLTIMAS ESTRADAS" and s3[19016]=="## Prompt:","source boundaries")
    require("geograficamente inútil" in s3[11909] and "Aethron terá poder real" in s3[20001] and "não tive acesso ao texto integral" in s3[20279],"hypothesis and editorial boundary")
    require("Ele continuava em Thalor" in s4[4667] and "não significa que o arco antigo tenha sido consertado" in s4[6579] and "O acesso permanece em configuração preliminar" in s4[9449] and s4[10257].startswith("LUCAS — Amor"),"regression anchors")
    require(total==audit["totals"]["lines"]==21609 and records==audit["totals"]["records"]==135 and len(ids)==773+records and audit["production_gate"]=="HOLD" and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"aggregate")
    return {"status":"PASS_NATIVE_BOOK_V_0045_COMPLETE","prior_book_status":"PASS_STAGING_ONLY","source_transition_status":"PASS_STAGING_ONLY","macro_metrics":metrics,"session_lines":total,"session_records":records,"staging_records":2895+records,"book_v_records":records,"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":10259,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_cycle47(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    opening=verify_book_v_opening(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0045-validated.json","a4e6c743a611da2c83391f6991cc0ad6c4d33b34")
    old=read(root,c0["opening_review_path"],"f14d50ab69a64e9fe605a368e2bd13642a3f0055")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(opening["status"]=="PASS_NATIVE_BOOK_V_0045_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3030,"opening gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    review=read(root,ROOT+"cycle-0043-0047-consolidated-review-pending.json","76e0a65f0825f1e1508a16d94ff91ce869029f39")
    require(review["opening_review_blob"]==c0["opening_review_blob"] and review["previous_validated_checkpoint_blob"]=="a4e6c743a611da2c83391f6991cc0ad6c4d33b34" and review["macros"][:3]==old["macros"] and review["prior_opening_findings"]==old["findings"] and [g["macro"] for g in review["macros"]]==list(range(43,48)),"cycle scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    require(len(ids)==773,"prior boundary ids")
    counts=Counter();vis=Counter();axes=set();total=0;records=0;metrics=[]
    prior_blob="a4e6c743a611da2c83391f6991cc0ad6c4d33b34"
    for g in review["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["macro_id"]==m["id"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n] and r["release_blob"]==c0["release_blob"],"queue chain")
        extra=8 if n==45 else 0
        require(r["range"]==[m["start"]+extra,m["end"]],"range")
        if n>=46:
            require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prior_blob and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"] and m["book_hint"]=="V_OR_VI_UNRESOLVED","new checkpoint chain")
            prior_blob=g["checkpoint_blob"]
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]+extra==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"counts")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"role separation")
            require(x["day"] is not None or x["authority"] in ("AUTHOR_DIRECTION_NOT_EVENT","METADATA_NOT_EVENT"),"metadata")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"private")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        total+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==2895+records and cp["book_counts"]["V"]==records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"staging gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in review["findings"]+review["prior_opening_findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"finding hash")
    s=cache.get(q[45]["source"])[0]
    require(all(s[i-1]=="LIVRO V — ALÉM DAS ÚLTIMAS ESTRADAS" for i in (10702,13052,16637,18802,21709,24260,27508)) and not any(line.strip().startswith("LIVRO VI") for line in s[10258:30371]),"book V literal headers")
    require("SIMBIONTE VIVO — PRIMEIRA EVOLUÇÃO" in s[13853] and "NÓX" in s[13979] and "cobertura planetária de superfície" in s[14593] and "Minha estrutura foi ampliada. Nosso vínculo permanece" in s[14983],"NOX and map")
    require("Não me tragam uma proposta baseada em vencê-lo" in s[22962] and "Sua armadura azul ainda não possui vínculo" in s[27436] and "novo checkpoint narrativo Dia 451 às 23h02" in s[30369],"private and checkpoint")
    t=review["totals"];require(total==t["lines"]==41722 and records==t["records"]==243 and len(ids)==773+records and total-opening["session_lines"]==t["session_lines"]==20113 and records-opening["session_records"]==t["session_records"]==108 and t["staging_records"]==2895+records and sorted(axes)==list(range(1,31)),"consolidated counts")
    require(review["production_gate"]=="HOLD" and not any(review[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")) and all(not x["promotion"] for x in review["overlays"]),"review gate")
    return {"status":"PASS_NATIVE_BOOK_V_0047_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macro_metrics":metrics,"cycle_lines":total,"cycle_records":records,"session_lines":t["session_lines"],"session_records":t["session_records"],"staging_records":t["staging_records"],"book_v_records":records,"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":30372,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_49(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_cycle47(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0047-validated.json","1ee93e8909f47c8e6cf8434fcb698a1cf3eef9f9")
    old=read(root,c0["cycle_review_path"],"960241e971063307345ec001347a3ced1476bff5")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0047_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3138,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"macros-0048-0049-review-pending.json","55747b95d30b3aa643bd66a3c9fa460cbdc696cc")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["previous_checkpoint_blob"]=="1ee93e8909f47c8e6cf8434fcb698a1cf3eef9f9" and [g["macro"] for g in audit["macros"]]==[48,49],"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in old["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==773+243,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="1ee93e8909f47c8e6cf8434fcb698a1cf3eef9f9"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        require(r["range"]==cp["macro_range"]==[m["start"],m["end"]] and cp["next_line"]==q[n]["start"] and cp["native_validation"]=="PENDING","geometry")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"]);prev=g["checkpoint_blob"]
        require(cp["staging_records"]==3138+records and cp["book_counts"]["V"]==243+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[47]["source"])[0]
    require(all(s[i-1]=="LIVRO V — ALÉM DAS ÚLTIMAS ESTRADAS" for i in (30414,33550,36147,38903,42735,45647,48471)) and not any(l.strip().startswith("LIVRO VI") for l in s[30371:50829]),"book")
    require("A armadura azul continuava sem vínculo" in s[32619] and "Quero realizar o vínculo" in s[39354] and "O vínculo estava estabelecido" in s[39442] and "bainha interna integrada" in s[39740],"armor")
    require("Não vou fingir que foi uma ordem minha" in s[40956] and "Não sabia que Miren havia estabelecido" in s[42074],"mission")
    require("Dezessete dias antes" in s[46056] and "uma operação" in s[50522] and "Não era um comunicador de longa distância" in s[50292] and "Olsa continuava presa" in s[50306] and "O Criador partiu" in s[50822].replace("o Criador","O Criador"),"coercion and chronology")
    t=audit["totals"];require(lines==t["lines"]==20458 and records==t["records"]==94 and len(ids)==1016+records and t["staging_records"]==3138+records and t["book_v_records"]==243+records and t["book_v_lines"]==62180,"totals")
    require(audit["cycle_status"]=="OPEN_0048_0052_OR_BOOK_BOUNDARY" and audit["production_gate"]=="HOLD" and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0049_COMPLETE","review_status":"PASS_STAGING_ONLY","cycle_status":"OPEN_0048_0052_OR_BOOK_BOUNDARY","macro_metrics":metrics,"session_lines":lines,"session_records":records,"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":50830,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_52(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_49(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0049-validated.json","a1e3a6722b1d98d930897c0035483b691a7a019b")
    old=read(root,c0["session_review_path"],"31d402b8d2002f29ce86cf7526a4a968414bedf7")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    previous_cycle=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0049_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3232,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"cycle-0048-0052-consolidated-review-pending.json","21ef853fb1dd55e854243a10f409e1ac7a22a125")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["prior_session_review_blob"]==c0["session_review_blob"] and audit["previous_checkpoint_blob"]=="a1e3a6722b1d98d930897c0035483b691a7a019b" and audit["macros"][:2]==old["macros"] and audit["prior_findings"]==old["findings"] and [g["macro"] for g in audit["macros"]]==list(range(48,53)),"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in previous_cycle["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==1016,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="a1e3a6722b1d98d930897c0035483b691a7a019b"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        if n>=50:
            require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev,"new chain")
            prev=g["checkpoint_blob"]
        require(r["range"]==cp["macro_range"]==[m["start"],m["end"]] and cp["next_line"]==q[n]["start"] and cp["native_validation"]=="PENDING" and r["next_line"]==m["end"]+1,"geometry")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==3138+records and cp["book_counts"]["V"]==243+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]+audit["prior_findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[49]["source"])[0]
    require(all(s[i-1].startswith("LIVRO V") for i in (51751,54377,57239,60709,64277,67162,70362,73129,75085)) and not any(l.strip().startswith("LIVRO VI") for l in s[50829:75170]),"book")
    require(len(s)==75170 and q[51]["end"]==75170 and q[52]["start"]==1 and q[52]["source"]=="05_DIA_469_A_496_FONTE_LITERAL.txt" and s[75162]=="## Prompt:","source boundary")
    require("Tecelã foi entregue à custódia local" in s[56358] and "não possuía uma segunda consciência declarada" in "\n".join(s[55432:55534]) and "conexão bidirecional" in s[56142],"victory and armor")
    require("O retorno físico à carruagem não foi narrado" in s[60628] and "segunda lacuna" in s[60646] and "12 meses de 30 dias" in s[67032] and "Mês 04 · Dia 06" in s[67063],"errata")
    require("Identificação registrada. Rumo" in s[63782] and "Nenhuma manifestação iniciada" in s[68257] and "não demonstra superioridade sobre VARO" in s[72459] and "não vamos declarar que uma mensagem consegue atravessar o continente" in s[72185].lower(),"new controls")
    require("Dia acumulado 469" in "\n".join(s[74892:74936]) and "Parte IV" in "\n".join(s[75162:75170]),"checkpoint")
    t=audit["totals"];
    require(lines==t["lines"]==44799 and records==t["records"]==236 and len(ids)==1016+records and t["session_lines"]==24341 and t["session_records"]==records-94 and t["staging_records"]==3138+records and t["book_v_records"]==243+records and t["book_v_lines"]==86521 and sorted(axes)==list(range(1,31)),"totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0052_COMPLETE","cycle_status":"PASS_STAGING_ONLY","source_transition":"SOURCE_04_COMPLETE_BOOK_V_CONTINUES","macro_metrics":metrics,"cycle_lines":lines,"cycle_records":records,"session_lines":t["session_lines"],"session_records":t["session_records"],"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_source":q[52]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_54(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_52(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0052-validated.json","f56d1446b134148cbe079a319ddac02105ce67ce")
    old=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    old43=read(root,ROOT+"cycle-0043-0047-consolidated-review-validated.json","960241e971063307345ec001347a3ced1476bff5")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0052_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3374,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"macros-0053-0054-review-pending.json","d14332a02b27185a68ae7f9dcec63141905daf0b")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["previous_checkpoint_blob"]=="f56d1446b134148cbe079a319ddac02105ce67ce" and [g["macro"] for g in audit["macros"]]==[53,54],"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in old43["macros"]+old["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==1252,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="f56d1446b134148cbe079a319ddac02105ce67ce"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        extra=8 if n==53 else 0
        require(r["range"]==[m["start"]+extra,m["end"]] and cp["macro_range"]==r["macro_range"]==[m["start"],m["end"]] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        if extra:
            md=read(root,cp["metadata_path"],cp["metadata_blob"])
            require(md["range"]==[1,8] and md["source"]==m["source"] and md["source_sha256"]==source[3] and md["blob_sha1"]==source[2][0][2] and all(x=="Metadata" for x in source[1][:8]) and sha256("\n".join(source[0][:8]).encode()).hexdigest()==md["span_sha256_utf8"] and not md["promotion"],"metadata header")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]+extra==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            if 13122<=x["evidence"]["line_start"]<=15826:
                require(x["authority"]=="METADATA_NOT_EVENT","superseded")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"]);prev=g["checkpoint_blob"]
        require(cp["staging_records"]==3374+records and cp["book_counts"]["V"]==479+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[52]["source"])[0];s4=cache.get(q[51]["source"])[0]
    require(len(s)==31423 and all(s[i-1].startswith("LIVRO V") for i in (125,237,2511,5601,8183,10193,13163,15891,18307)) and not any(l.strip().startswith("LIVRO VI") for l in s[:20347]),"book")
    require("Parte IV" in "\n".join(s4[75162:75170]) and "D469 21h12 Pedra Mel" in s[197] and "DIA 470" in s[264],"transition")
    require("Talis continua desaparecida" in s[528] and "Nenhuma ligação demonstrada com a Tecelã" in s[4088] and "11h03" in s[4316],"independent threats")
    require("DIA 488" in s[7892] and "16h27" in s[7892] and s[10108]=="20h12","arrival")
    require(s[13111]=="## Response:" and s[13116]=="## Prompt:" and "PARTE V DE V" in s[13166] and "Refaça esse episódio" in s[15829] and "VERSÃO CORRIGIDA" in s[15894] and "SETE DIAS PARA VIVER" in s[18196:18200],"author replacement")
    require("Dia 105" in "\n".join(s[18476:18586]) and "Nenhuma consciência foi copiada" in s[18674] and "Não foi o nascimento de outro membro da Legião" in s[18672] and "Avenida dos Três Horizontes" in s[20286],"identity and avenue")
    t=audit["totals"]
    require(lines==t["lines"]==20347 and records==t["records"]==116 and len(ids)==1252+records and t["staging_records"]==3374+records and t["book_v_records"]==479+records and t["book_v_lines"]==106868,"totals")
    require(audit["cycle_status"]=="OPEN_0053_0057_OR_BOOK_BOUNDARY" and audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0054_COMPLETE","review_status":"PASS_STAGING_ONLY","cycle_status":audit["cycle_status"],"macro_metrics":metrics,"session_lines":lines,"session_records":records,"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":20348,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_57(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_54(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0054-validated.json","e9174258fbb4b25e26bdf991ab6de482e66485da")
    old=read(root,c0["session_review_path"],c0["session_review_blob"])
    old43=read(root,ROOT+"cycle-0043-0047-consolidated-review-validated.json","960241e971063307345ec001347a3ced1476bff5")
    old48=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0054_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3490,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"cycle-0053-0057-consolidated-review-pending.json","a9a4a84544a617c0092278039a75ffe889e2784f")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["prior_session_review_blob"]==c0["session_review_blob"] and audit["previous_checkpoint_blob"]=="e9174258fbb4b25e26bdf991ab6de482e66485da" and audit["macros"][:2]==old["macros"] and audit["prior_findings"]==old["findings"] and [g["macro"] for g in audit["macros"]]==list(range(53,58)),"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in old43["macros"]+old48["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==1252,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="e9174258fbb4b25e26bdf991ab6de482e66485da"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        if n>=55:
            require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev,"new chain")
            prev=g["checkpoint_blob"]
        extra=8 if n in (53,57) else 0
        require(r["range"]==[m["start"]+extra,m["end"]] and cp["macro_range"]==r["macro_range"]==[m["start"],m["end"]] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        if extra:
            md=read(root,cp["metadata_path"],cp["metadata_blob"])
            require(md["range"]==[1,8] and md["source"]==m["source"] and md["source_sha256"]==source[3] and md["blob_sha1"]==source[2][0][2] and all(x=="Metadata" for x in source[1][:8]) and sha256("\n".join(source[0][:8]).encode()).hexdigest()==md["span_sha256_utf8"] and not md["promotion"],"metadata header")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]+extra==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==3374+records and cp["book_counts"]["V"]==479+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]+audit["prior_findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s5=cache.get(q[54]["source"])[0];s6=cache.get(q[56]["source"])[0]
    require(len(s5)==31423 and len(s6)==101429 and q[55]["end"]==len(s5) and q[56]["start"]==1,"source transition")
    require(all(s5[i-1].startswith("LIVRO V") for i in (21387,24179,26675,29032)) and all(s6[i-1].startswith("LIVRO V") for i in (1139,3423,5405,8035)) and not any(l.strip().startswith("LIVRO VI") for l in s5[20347:]+s6[:10089]),"book")
    require("Integração restabelecida" in s5[21618] and "não são canônicas" in s5[24168] and "Você venceu" in s5[25820] and "Você acabou de vencer nós dois" in s5[26178],"Nox and combat")
    require("Dia 171" in s5[29015] and "dois lugares diferentes" in s5[29009] and "23h56" in s5[31309] and "Círan permanece sem retorno comprovado" in s5[31319],"errata and closure")
    require("Errado" in s6[127] and "496" in s6[130] and "DIA 497" in s6[1150] and "HZ-1 - Horizonte Exterior, Área Candidata" in s6[4932],"retake and HZ1")
    require("Nenhuma estrutura permanente de AERÚN foi criada" in s6[7894] and "240 autômatos existiam" in s6[9732] and "HZ-1 ainda não era um terreno oficialmente escolhido" in s6[9928],"project and automation")
    t=audit["totals"]
    require(lines==t["lines"]==41512 and records==t["records"]==229 and len(ids)==1252+records and t["session_lines"]==21165 and t["session_records"]==records-116 and t["staging_records"]==3374+records and t["book_v_records"]==479+records and t["book_v_lines"]==128033 and sorted(axes)==list(range(1,31)),"totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0057_COMPLETE","cycle_status":"PASS_STAGING_ONLY","source_transition":"SOURCE_05_COMPLETE_SOURCE_06_STARTED_BOOK_V_CONTINUES","macro_metrics":metrics,"cycle_lines":lines,"cycle_records":records,"session_lines":t["session_lines"],"session_records":t["session_records"],"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_source":q[57]["source"],"next_line":10090,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_59(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_57(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0057-validated.json","30d71463cb6ab57180afb7be9a195a0fca501c55")
    old=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    old43=read(root,ROOT+"cycle-0043-0047-consolidated-review-validated.json","960241e971063307345ec001347a3ced1476bff5")
    old48=read(root,"audit/omega008-c/turbo-v3/cycle-0048-0052-consolidated-review-validated.json","69a57b04c8e678716563d38e94b88c636e06294b")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0057_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3603,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"macros-0058-0059-review-pending.json","c75d68c33112ab8476854b35026121791b18a9aa")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["previous_checkpoint_blob"]=="30d71463cb6ab57180afb7be9a195a0fca501c55" and [g["macro"] for g in audit["macros"]]==[58,59],"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in old43["macros"]+old48["macros"]+old["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==1481,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="30d71463cb6ab57180afb7be9a195a0fca501c55"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev,"new chain")
        prev=g["checkpoint_blob"]
        require(r["range"]==[m["start"],m["end"]] and cp["macro_range"]==r["macro_range"]==r["range"] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==3603+records and cp["book_counts"]["V"]==708+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[57]["source"])[0]
    require(len(s)==101429 and all(s[i-1].startswith("LIVRO V") for i in (10978,13125,15487,17739,20051,22747,25677,28015)) and not any(l.strip().startswith("LIVRO VI") for l in s[10089:30385]),"book")
    require("12"==s[10478].strip() and "240"==s[10482].strip() and "3.360"==s[13028].strip() and "3.600"==s[15388].strip() and "32"==s[15392].strip() and "12"==s[15396].strip(),"malha counts")
    require("128"==s[17642].strip() and "288"==s[19936].strip() and "376"==s[22654].strip() and "320 m"==s[17646].strip() and "840 m"==s[19940].strip() and "960 m"==s[22646].strip() and "8,00 km"==s[25564].strip(),"progress")
    require("A Cidade Livre aprova a implantação de AERÚN" in s[26432] and "AOS FUNDADORES DE TRÊS ARCOS" in s[27028] and "Ainda não manifestado"==s[27936].strip() and "Coração de GÊNESE: manifestado e ativado."==s[29066].strip() and "Rede municipal de Três Arcos: independente."==s[29074].strip() and "Às 16h11" in s[29868] and "VARO - Ela continuará descobrindo coisas que ninguém conhece."==s[30384].strip(),"AERUN states")
    t=audit["totals"]
    require(lines==t["lines"]==20296 and records==t["records"]==107 and len(ids)==1481+records and t["staging_records"]==3603+records and t["book_v_records"]==708+records and t["book_v_lines"]==148329,"totals")
    require(audit["production_gate"]=="HOLD" and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0059_COMPLETE","review_status":"PASS_STAGING_ONLY","cycle_status":audit["cycle_status"],"macro_metrics":metrics,"session_lines":lines,"session_records":records,"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":30386,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_62(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_59(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0059-validated.json","31b2d581e186fae7f6c2f1c0353c61362ed8ad85")
    old=read(root,c0["session_review_path"],c0["session_review_blob"])
    old53=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    old43=read(root,ROOT+"cycle-0043-0047-consolidated-review-validated.json","960241e971063307345ec001347a3ced1476bff5")
    old48=read(root,ROOT+"cycle-0048-0052-consolidated-review-validated.json","69a57b04c8e678716563d38e94b88c636e06294b")
    boundary=read(root,c0["book_boundary_review_path"],c0["book_boundary_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0059_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["native_validation"]=="PASS" and c0["staging_records"]==3710,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"cycle-0058-0062-consolidated-review-pending.json","23ba49c4be9ed589f5392f000fe9bbd258e16317")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["prior_session_review_blob"]==c0["session_review_blob"] and audit["previous_checkpoint_blob"]=="31b2d581e186fae7f6c2f1c0353c61362ed8ad85" and audit["macros"][:2]==old["macros"] and audit["prior_findings"]==old["findings"] and [g["macro"] for g in audit["macros"]]==list(range(58,63)),"scope")
    ids={x["id"] for g in boundary["macros"] for e in g["receipts"] for x in read(root,e["path"],e["blob"])["records"]}
    ids.update(x["id"] for g in old43["macros"]+old48["macros"]+old53["macros"] for x in read(root,g["receipt"],g["blob"])["records"])
    require(len(ids)==1481,"prior ids")
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="31b2d581e186fae7f6c2f1c0353c61362ed8ad85"
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        if n>=60:
            require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev,"new chain")
            prev=g["checkpoint_blob"]
        require(r["range"]==[m["start"],m["end"]] and cp["macro_range"]==r["macro_range"]==r["range"] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids,expected_range=r["range"])
        require(result["lines"]==m["lines"]==g["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((x["evidence"]["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"]!="reader_scene" or x["visibility"].startswith("READER_ONLY"),"reader")
            ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==3603+records and cp["book_counts"]["V"]==708+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]+audit["prior_findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[59]["source"])[0]
    require(len(s)==101429 and all(s[i-1].startswith("LIVRO V") for i in (31771,35272,37466,40596,44032,46850,50082,53174,56078,58874)) and not any(l.strip().startswith("LIVRO VI") for l in s[30385:60930]),"book")
    require("Às 20h13, S-2 estava fisicamente concluído" in s[30536] and "Às 09h07" in s[32318] and "Às 14h16" in s[33218] and "Manifestado e verificado"==s[35037].strip() and "Manifestado e verificado"==s[40515].strip(),"level progress")
    require("Às 11h39" in s[41649] and "Às 12h41" in s[45163] and "Às 15h43" in s[45719] and "Estrutura física do campus AERÚN: concluída" in s[49891] and "sete dias de construção, e não oito" in s[50027],"completion and errata")
    require("2.400 lugares"==s[49971].strip() and "48 suítes"==s[49975].strip() and "Seis votos para Miren Elvenar" in s[51785] and "Três votos para Astra" in s[51789] and "REGISTRO Nº 001"==s[52389].strip() and "não altera os poderes" in s[52417] and "Favoráveis 7 votos"==s[53891].strip() and "Contrários 2 votos"==s[53893].strip(),"governance")
    require("Aniversário de Lucas: 14 do mês 06."==s[55985].strip() and "ARGOS permanecia cativo" in s[58111] and "Matriz de Compensação Coordenada: manifestada e ensaiada."==s[60417].strip() and "Voo livre: não demonstrado."==s[60423].strip() and "carta enviada por Lucas no Dia 515 ainda estava em trânsito" in s[60559] and "A academia ainda não existia fisicamente" in s[60843] and "Miren sorriu."==s[60929].strip(),"technology privacy continuity")
    t=audit["totals"]
    require(lines==t["lines"]==50841 and records==t["records"]==266 and len(ids)==1481+records and t["session_lines"]==30545 and t["session_records"]==records-107 and t["staging_records"]==3603+records and t["book_v_records"]==708+records and t["book_v_lines"]==178874,"totals")
    require(audit["production_gate"]=="HOLD" and all(not e["promotion"] for e in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0062_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macro_metrics":metrics,"cycle_lines":lines,"cycle_records":records,"session_lines":t["session_lines"],"session_records":t["session_records"],"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":60931,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_65(root,archive):
    from collections import Counter
    from hashlib import sha256
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_62(root,archive)
    c0=read(root,ROOT+"recovery-checkpoint-0062-validated.json","b0c875f4974db1be2c8f06df76b2d0fd61d5414f")
    old=read(root,c0["cycle_review_path"],c0["cycle_review_blob"])
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0062_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c0["staging_records"]==3869,"prior gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    audit=read(root,ROOT+"macros-0063-0065-review-pending.json","3fb2e673739d82bdff688e8f400fc44c1c18bc01")
    require(audit["previous_cycle_blob"]==c0["cycle_review_blob"] and audit["previous_checkpoint_blob"]=="b0c875f4974db1be2c8f06df76b2d0fd61d5414f" and [g["macro"] for g in audit["macros"]]==[63,64,65],"scope")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if f.name.startswith("partial-macro-0063-") or f.name.startswith("partial-macro-0064-") or f.name.startswith("partial-macro-0065-"):continue
        obj=json.loads(f.read_bytes())
        rows=obj.get("records")
        if isinstance(rows,list):
            ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    counts=Counter();vis=Counter();axes=set();lines=0;records=0;metrics=[];prev="b0c875f4974db1be2c8f06df76b2d0fd61d5414f";new_ids=set()
    for g in audit["macros"]:
        n=g["macro"];m=q[n-1];source=cache.get(m["source"])
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]==c0["cycle_review_blob"] and r["release_blob"]==c0["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[n],"chain")
        prev=g["checkpoint_blob"]
        require(r["range"]==[m["start"],m["end"]]==r["macro_range"]==cp["macro_range"] and cp["native_validation"]=="PENDING" and cp["next_line"]==q[n]["start"],"geometry")
        result=validate_receipt(r,m,source,r["project"],ARCHIVE,previous_ids=ids|new_ids,expected_range=r["range"])
        require(result["lines"]==g["lines"]==m["lines"] and result["records"]==g["records"]==cp["records"] and result["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"]
            require(x["book"]=="V" and "NO_CHARACTER_INJECTION" in x["visibility"] and not x["promotion"],"scope")
            require((e["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
            require(x["type"]!="knowledge" or x["visibility"].startswith("RESTRICTED"),"privacy")
            require(x["type"] not in ("reader_scene","rejected_version") or x["visibility"].startswith("READER_ONLY"),"reader")
            if 68167<=e["line_start"]<=69968:
                require(x["authority"]=="METADATA_NOT_EVENT" and x["type"]=="rejected_version","rejected D520")
            if 91245<=e["line_start"]<=91475:
                require(x["type"]=="reader_scene" and x["visibility"].startswith("READER_ONLY"),"D526 reader")
            new_ids.add(x["id"]);counts[x["authority"]]+=1;vis[x["visibility"]]+=1
        lines+=g["lines"];records+=g["records"];axes.update(g["axes"])
        require(cp["staging_records"]==3869+records and cp["book_counts"]["V"]==974+records and cp["official_records"]==1656 and cp["production_gate"]=="HOLD" and not any(cp[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
        metrics.append({"macro":n,"lines":g["lines"],"records":g["records"],"axes":g["axes"]})
    for e in audit["findings"]:
        s=cache.get(e["source"]);lo,hi=e["range"]
        require(not e["promotion"] and sha256("\n".join(s[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"anchor")
    s=cache.get(q[62]["source"])[0]
    require(len(s)==101429 and s[60929]=="Miren sorriu." and s[60931]=="MIREN - Então é isso que faremos.","continuity")
    require("A versão anterior do Dia 520 fica desconsiderada" in s[70016] and "Voo livre: não demonstrado."==s[61281].strip() and "Voo livre de ARGOS: não realizado."==s[67455].strip(),"version and prior cative")
    require("sem tripulação" in s[73874] and "Velocidade extrema e supressão de estrondo sônico" in s[73880] and "31,6 m"==s[74842].strip() and "39,2 toneladas"==s[74855].strip(),"D520 D521")
    require("320 hectares"==s[75591].strip() and "2.400 × 48 m"==s[75599].strip() and "27,6 km"==s[76854].strip() and "78 km/h"==s[76862].strip(),"field and flight 002")
    require("33,2 km"==s[78698].strip() and "Total físico conhecido: 60."==s[79245].strip() and "Serviço regular de transporte: ainda não iniciado."==s[79251].strip() and "Nenhum"==s[80915].strip(),"Eixo and D522")
    require("003 - Primeiro voo tripulado"==s[86563].strip() and "43 min"==s[86569].strip() and "36,8 km"==s[86573].strip() and "138 km/h"==s[86577].strip() and "520 m"==s[86581].strip(),"D524")
    require("Prisma da Seiva" in s[89234] and "2 mudas com melhora parcial"==s[91114].strip() and "Proposta formulada"==s[91118].strip() and "parece ter sido copiada de outra" in s[90302],"Miren and HZ1")
    require("exclusivamente do leitor" in s[91240] and "Sete confirmadas" in s[91402] and q[65]["start"]==91476 and q[66]["source"]!=q[65]["source"],"reader and boundary")
    t=audit["totals"]
    require(lines==t["lines"]==30545 and records==t["records"]==205 and len(new_ids)==records and t["staging_records"]==3869+records and t["book_v_records"]==974+records and t["book_v_lines"]==209419,"totals")
    require(audit["cycle_status"]=="OPEN_0063_0067_OR_EARLIER_BOUNDARY" and audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"audit")
    return {"status":"PASS_NATIVE_BOOK_V_0065_COMPLETE","review_status":"PASS_STAGING_ONLY","cycle_status":audit["cycle_status"],"macro_metrics":metrics,"session_lines":lines,"session_records":records,"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":t["book_v_lines"],"authority_counts":dict(counts),"visibility_counts":dict(vis),"axes":sorted(axes),"next_line":91476,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_66(root,archive):
    from collections import Counter
    from hashlib import sha256
    from .git_cycle import verify_episode
    root=Path(root);archive=Path(archive)
    previous=verify_book_v_65(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0065-validated.json","8ca69c1d43b1095348c7b73f29ce3083cca9a6d9")
    old=read(root,c["session_review_path"],"beee4b727fba61ea9b4da722af8b3d50d6433bf8")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0063-0066-frontier-review-pending.json","cf30846f47f5e756acb36301b51268ebdc08f0c7")
    require(previous["status"]=="PASS_NATIVE_BOOK_V_0065_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and audit["macros"][:3]==old["macros"] and audit["prior_findings"]==old["findings"] and audit["prior_session_review_blob"]=="beee4b727fba61ea9b4da722af8b3d50d6433bf8","prior cycle")
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    m=q[65];s=cache.get(m["source"]);g=audit["macros"][-1]
    cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if f.name.startswith("partial-macro-0066-"):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="8ca69c1d43b1095348c7b73f29ce3083cca9a6d9" and r["cycle_review_blob"]==c["cycle_review_blob"] and r["release_blob"]==c["release_blob"] and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and cp["next_macro"]==q[66],"chain")
    metrics=validate_receipt(r,m,s,c["project"],ARCHIVE,previous_ids=ids,expected_range=[91476,101429])
    require(metrics["records"]==62 and metrics["lines"]==9954 and metrics["axes_represented"]==g["axes"],"metrics")
    require(cp["range"]==r["range"]==[91476,101429] and cp["next_line"]==1 and cp["next_source"]==q[66]["source"] and cp["staging_records"]==4136 and cp["official_records"]==1656,"checkpoint")
    for x in r["records"]:
        e=x["evidence"];require(x["book"]=="V" and not x["promotion"] and (e["role"]=="Prompt")==(x["authority"]=="AUTHOR_DIRECTION_NOT_EVENT"),"authority")
        if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        if e["line_start"]<94129:require(x["type"]=="reader_scene","D526 leak")
    for e in audit["findings"]+audit["prior_findings"]:
        lo,hi=e["range"];ss=cache.get(e["source"]);require(not e["promotion"] and sha256("\n".join(ss[0][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")
    L=s[0]
    require(len(L)==101429 and L[91474]=="Selda olhou novamente para os registros." and L[91476]=="Depois fez uma pergunta:" and "Todos a bordo. Ninguém caiu ao mar." in L[91838] and "primeira Doca Ascendente" in L[92018],"Calderva")
    require("Corredor dos Ofícios Livres" in L[92534] and "três" in L[92866].lower() and "Não podia observar todo o continente."==L[93292] and "classificada como rumor" in L[93600],"external")
    require("Nenhum novo equipamento, infraestrutura, serviço regular, ensaio de voo ou autorização" in L[96901] and "39,86 toneladas" in L[99215] and "58 toneladas" in L[99245] and "não era uma nova peça instalada" in L[100701].lower(),"technology")
    require("ainda sem liberação para uso" in L[101367] and "sem linha regular" in L[101373] and "cartas enviadas aos amigos distantes ainda não têm entrega confirmada" in L[101377] and "23h06" in L[101343],"end")
    require(not any(x.strip().startswith("LIVRO VI") for x in L[91475:]),"book boundary")
    d,manifest=verify_episode(archive,q[66]["source"])
    closure=read(archive,"canon/episodes/"+q[66]["source"]+".json","35cb9b5a5c72bf49648e18954b5dd7ba3b6cd410")
    require(closure["sequence"]==1 and closure["previous_episode_id"]=="LV-C15-PI-D528" and closure["metadata"]["day"]==529 and closure["metadata"]["chapter"]==15 and closure["metadata"]["part"]=="II" and manifest["original_readback_sha256"]==closure["story_sha256"] and len(d.prose.splitlines())==3269 and q[66]["previous_macro"]==m["id"],"next episode provenance")
    axes=sorted(set(previous["axes"])|set(metrics["axes_represented"]))
    t=audit["totals"];require(t["lines"]==40499 and t["records"]==205+62 and t["book_v_lines"]==219373 and t["source06_lines"]==101429 and audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"frontier totals")
    return {"status":"PASS_NATIVE_BOOK_V_0066_COMPLETE","cycle_status":"PASS_STAGING_ONLY_FRONTIER","source06_lines":101429,"cycle_lines":40499,"cycle_records":t["records"],"session_lines":9954,"session_records":62,"staging_records":t["staging_records"],"book_v_records":t["book_v_records"],"book_v_lines":219373,"axes":axes,"macro_metrics":metrics,"next_source":q[66]["source"],"next_line":1,"next_source_full_sha256":closure["story_sha256"],"next_source_prose_sha256":sha256(d.prose.encode()).hexdigest(),"next_source_prose_lines":len(d.prose.splitlines()),"next_source_manifest":"7059f4c6c13b8126463ac2007b28d71423a251be","production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_67(root,archive):
    from hashlib import sha256
    from .git_cycle import verify_episode
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_66(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0066-validated.json","d0d98b723bd256ab46dafaa61521b400f935eee4")
    frontier=read(root,c["cycle_review_path"],"7006296be97be68839b9968bc99a57116f36006c")
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0066_COMPLETE" and frontier["status"]=="PASS_STAGING_ONLY" and frontier["cycle_status"]=="CLOSED_AT_SOURCE_FRONTIER" and c["next_line"]==1,"frontier gate")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    m=q[66];name=m["source"];require(name=="LV-C15-PII-D529-AUTHOR-SOURCE" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[65]["id"],"queue")
    d,manifest=verify_episode(archive,name)
    closure=read(archive,"canon/episodes/"+name+".json","35cb9b5a5c72bf49648e18954b5dd7ba3b6cd410")
    folder=archive/"episodes"/name/"draft"
    require(git_blob((folder/"episode_draft.json").read_bytes())=="420928c751a4df2131798c1547c2f2bbb7e411e1" and git_blob((folder/"manifesto_imutavel.json").read_bytes())=="7059f4c6c13b8126463ac2007b28d71423a251be" and git_blob((folder/"narrativa_integral.md").read_bytes())=="caaed9f3fcb7d8fd3d82eae2a26e3ca9d99482ae","immutable physical provenance")
    L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest()
    require(ph=="5cb24bfba4b90d4f710680cd598534a13376e2e6104687a6669bee754eaef7c4" and len(L)==3269 and closure["story_sha256"]==manifest["original_readback_sha256"]=="5b2a269fa91ca1c3869d59a3b6e5fe3cccef3f226f3f7a4624597fe1dc29bea9" and closure["sequence"]==1 and closure["previous_episode_id"]=="LV-C15-PI-D528","source")
    require(prior["next_source_prose_sha256"]==ph and prior["next_source_full_sha256"]==closure["story_sha256"],"frontier source bind")
    source=(L,tuple("Response" for _ in L),((1,len(L),"420928c751a4df2131798c1547c2f2bbb7e411e1"),),ph)
    audit=read(root,ROOT+"macro-0067-closed-prose-review-pending.json","b40ba1f818a2025fd6279fc326d9a005a57841a5");g=audit["macros"][0]
    cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
    require(r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]=="d0d98b723bd256ab46dafaa61521b400f935eee4" and r["cycle_review_blob"]=="7006296be97be68839b9968bc99a57116f36006c" and r["official_unit_seal"]==m["unit_seal"] and r["previous_macro_id"]==m["previous_macro"] and cp["next_macro"]==q[67],"chain")
    require(r["source_provenance"]==cp["source_provenance"]==audit["source_provenance"] and r["source_provenance"]["closure_event_count"]==len(closure["events"]) and r["source_provenance"]["closure_knowledge_count"]==len(closure["knowledge"]),"closure authority")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if f.name.startswith("partial-macro-0067-"):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    metrics=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,3269])
    require(metrics["records"]==25 and metrics["lines"]==3269 and metrics["axes_represented"]==g["axes"],"metrics")
    for x in r["records"]:
        e=x["evidence"];require(x["book"]=="V" and x["day"]==529 and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]=="35cb9b5a5c72bf49648e18954b5dd7ba3b6cd410" and e["full_story_sha256"]=="5b2a269fa91ca1c3869d59a3b6e5fe3cccef3f226f3f7a4624597fe1dc29bea9" and e["immutable_manifest_blob"]=="7059f4c6c13b8126463ac2007b28d71423a251be","closed provenance")
        if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(L[lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")
    require("Feliz aniversário, meu amor." in L[157] and "Preparei uma coisa para você." in L[991] and "Lucas comprou a pequena peça."==L[1527],"birthday letter object")
    require("Cidade Viva continuava aguardando" in L[1595] and "Não era parte instalada de ARGOS."==L[1669] and "Esperamos que você seja nosso amigo." in L[1843],"projects autonomy")
    require("Quero que leia depois." in L[2601] and "Mas gosto da minha vida." in L[2683] and "Às 20h42" in L[3069] and "A contribuição particular de Varo ainda não foi lida." in L[3265],"private gifts and open day")
    require(cp["next_line"]==1 and cp["next_source"]==q[67]["source"] and cp["staging_records"]==4161 and cp["official_records"]==1656 and cp["book_counts"]["V"]==1266,"checkpoint")
    require(audit["totals"]["book_v_lines"]==222642 and audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_V_0067_COMPLETE","frontier_status":"PASS_STAGING_ONLY","cycle_status":"NEW_CYCLE_OPEN_0067","macro_metrics":metrics,"source_provenance":r["source_provenance"],"session_lines":13223,"session_records":87,"staging_records":4161,"book_v_records":1266,"book_v_lines":222642,"next_source":q[67]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_71(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_67(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0067-validated.json","20333e8dea79adace5182c1b6f58330ac934419d")
    old=read(root,c["session_review_path"],"90e31d0f7d1860d6fe5c96565f3a61f962bc5f5a")
    frontier=read(root,c["cycle_review_path"],"7006296be97be68839b9968bc99a57116f36006c")
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0067_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and frontier["status"]=="PASS_STAGING_ONLY","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0067-0071-review-pending.json","9745b067a9dd223970d9a26bee5946319c23e998")
    require(audit["macros"][:1]==old["macros"] and audit["prior_findings"]==old["findings"] and audit["previous_cycle_blob"]=="7006296be97be68839b9968bc99a57116f36006c" and audit["prior_session_review_blob"]=="90e31d0f7d1860d6fe5c96565f3a61f962bc5f5a","cycle predecessor")
    journal=list(islice(_journal(archive),5))
    require(len(journal)==5 and journal[0][0]["episode_id"]==c["source"],"journal prefix")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(68,72)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="20333e8dea79adace5182c1b6f58330ac934419d";prev_episode=c["source"];prev_day=529;prev_clock="20h42"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set(prior["macro_metrics"]["axes_represented"])
    for g,(closure,head) in zip(audit["macros"][1:],journal[1:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==68+len(metrics) and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        require(all(k["source_event"] in {e["event_id"] for e in closure["events"]} for k in closure["knowledge"]),"knowledge links")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["start_day"]==prev_day and continuity["start_clock"]==prev_clock and str(prev_day) in "\n".join(L[:40]) and prev_clock in "\n".join(L[:40]) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro V" and head["book_closed"] is False,"chronological boundary")
        require("ESCOLHA "+str(g["editorial_choice_header"]) in "\n".join(L[:8]) and g["closed_choice"]==closure["chosen_option"],"separate choice authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="7006296be97be68839b9968bc99a57116f36006c" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="V" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4161+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1266+recs and cp["completed_macros"]==num,"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")
    A,B,C,D=[sources[x["source"]] for x in q[67:71]]
    require("Leia em casa." in A[417] and "escolhi chamar de irmão" in A[669] and "Amanhã preciso voltar a AERÚN" in A[755],"letter autonomy")
    require("GÊNESE respondeu à sua vontade, plena e imediata."==B[85] and "Nesta muda." in B[391] and "reprovar esta configuração" in B[511] and "39,86 toneladas" in B[549] and "Nenhum quarto voo" in B[549] and "não só uma carga parada" in B[567] and "Não posso garantir até onde vai" in B[715],"D530 regressions")
    require("mesmo espaço dimensional já existente" in C[131] and "simulador dimensional" in C[189] and "Seu nome será Vértice" in C[297] and "2.984" in C[553] and "376" in C[553] and "240" in C[553] and "3.600" in C[553] and "24 metros" in C[599] and "janela provisória" in C[803],"D531 regressions")
    require("EU ENTREI LÁ E SAÍ AQUI" in D[401] and "não será o piloto do voo 004" in D[867] and "Eu piloto no posto esquerdo" in D[923] and "Rumo ocupa o segundo posto" in D[923] and "Lucas permanece no solo" in D[923] and "ARGOS 004 concluído" in D[1089] and "18h19" in D[1293],"D532 regressions")
    t=audit["totals"];require(recs==56 and lines==4034 and t["lines"]==7303 and t["records"]==25+recs and t["book_v_lines"]==226676 and t["staging_records"]==4161+recs and t["book_v_records"]==1266+recs and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_V_0071_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"cycle_lines":7303,"cycle_records":25+recs,"cycle_axes":sorted(axes),"session_lines":lines,"session_records":recs,"staging_records":4161+recs,"book_v_records":1266+recs,"book_v_lines":226676,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":5,"choice_header_differences_preserved":len(audit["divergences"]),"next_source":q[71]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_v_75(root,archive):
    from hashlib import sha256
    from itertools import islice
    from collections import Counter
    from .git_cycle import verify_episode, _journal
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_71(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0071-validated.json","61a5ed0629386e2d07e523cf941a59325b2fb7a3")
    old=read(root,c["cycle_review_path"],"2fbfe32406ee958b6e723bebb199714bec0a23e8")
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0071_COMPLETE" and old["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"book-V-boundary-0043-0075-review-pending.json","7a6eb766d0bce1c90d0f4a3d6b894bb67f71a727")
    require(audit["previous_cycle_blob"]=="2fbfe32406ee958b6e723bebb199714bec0a23e8" and audit["prior_cycle_overlays"]==old["overlays"] and len(audit["macros"])==4,"cycle predecessor")
    journal=list(islice(_journal(archive),9))
    require(len(journal)==9 and journal[4][0]["episode_id"]==c["source"] and [head["book_closed"] for _,head in journal]==[False]*8+[True],"journal book boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(72,76)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="61a5ed0629386e2d07e523cf941a59325b2fb7a3";prev_episode=c["source"];prev_day=532;prev_clock="18h19"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[5:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==72+len(metrics) and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        require(all(k["source_event"] in {e["event_id"] for e in closure["events"]} for k in closure["knowledge"]),"knowledge links")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["start_day"]==prev_day and continuity["start_clock"]==prev_clock and str(prev_day) in "\n".join(L[:40]) and prev_clock in "\n".join(L[:40]) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro V" and head["book_closed"]==d.book_closed==sp["book_closed"]==(num==75),"chronological boundary")
        require(L[4]==sp["editorial_header"] and ((num==75 and closure["chosen_option"]==0 and closure["book_closed"] is True and closure["free_text"]==sp["finale_author_text"] and "encerrar o livro V" in closure["free_text"]) or (num<75 and closure["chosen_option"]==5 and sp["finale_author_text"] is None)),"separate author finale and entry authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="2fbfe32406ee958b6e723bebb199714bec0a23e8" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="V" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4217+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1322+recs and cp["completed_macros"]==num and cp["book_v_closed"]==(num==75) and cp["book_vi_started"] is False,"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,book_closed=d.book_closed))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")
    A,B,C,D=[sources[x["source"]] for x in q[71:75]]
    require("Não descobrimos a sétima nota." in A[333] and "O enlace funcionou. A interpretação do registro, não." in A[589] and "mesmo registro" in A[717] and "dois relógios" in A[1109] and "confirmação e a retirada, por pessoas" in A[1161],"D533 data authority")
    require("coração da Forja" in B[407] and "camada arcana reversível" in B[451] and "O voo 004 permanecia o último realizado" in B[921] and "Dia 208" in B[1003] and "sítio diferente" in B[1003] and "Operação Primeiras Asas" in B[1187],"D534 identity and route")
    require("modesto, mas repetível" in C[613] and "câmara de proteção independente" in C[844] and "janela condicional de voo" in C[948] and "Não embarcaria" in C[1016] and "1.462 quilômetros por hora" in C[1184] and "formação de pedras escuras" in C[1254] and "orientação de Naira" in C[1294],"D537 flight and observation")
    require("Não vou ordenar um festival de adoração" in D[592] and "Nós éramos trezentos" in D[812] and "ESCOLHER" in D[1221] and "VIVER" in D[1241] and "Nenhum fica para trás" in D[1433] and "JUNTOS" in D[1491] and "FIM DO LIVRO V" in D[1727],"D537 liberty and finale")
    t=audit["totals"];require(recs==58 and lines==5769 and t["session_lines"]==lines and t["session_records"]==recs and t["book_v_lines"]==232445 and t["staging_records"]==4217+recs and t["book_v_records"]==1322+recs and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    # Full Book V ledger: re-open all pinned receipts, preserve raw metadata and
    # use the native transcript/closed-prose adapters independently of cycle sums.
    require([g["macro"] for g in audit["book_ledger"]]==list(range(43,76)) and q[75]["book_hint"]=="VI" and [q[i]["book_hint"] for i in range(42,75)]==["V"]*2+["V_OR_VI_UNRESOLVED"]*22+["V"]*9,"book scope: preserve unresolved queue hints; audited receipts supply staging classification")
    for cy in audit["prior_cycles"]:
        y=read(root,cy["path"],cy["blob"]);require(y["status"]=="PASS_STAGING_ONLY" and not y.get("promotion",False),"prior review")
    cache=SourceCache(archive,read(archive,"history/sources/MANIFEST.json","2048141263f66151230119af9b0ee51796ac846b"))
    bids=set();baxes=set();blines=0;brecs=0;metadata_lines=0;authority=Counter();visibility=Counter();coverage_by_macro=[]
    for g in audit["book_ledger"]:
        m=q[g["macro"]-1];r=read(root,g["path"],g["blob"]);at=m["start"];mdlen=0
        if g["macro"]<67:
            source=cache.get(m["source"])
        else:
            sp=r["source_provenance"];d,manifest=verify_episode(archive,m["source"]);L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest()
            require(manifest["original_readback_sha256"]==sp["full_story_sha256"] and git_blob((archive/"episodes"/m["source"]/"draft"/"episode_draft.json").read_bytes())==sp["draft_blob"],"book closed source")
            source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        if "metadata" in g:
            md=read(root,g["metadata"]["path"],g["metadata"]["blob"]);lo,hi=md["range"]
            require(lo==at and hi==8 and all(x=="Metadata" for x in source[1][lo-1:hi]) and md["source_sha256"]==source[3] and md["blob_sha1"]==source[2][0][2] and sha256("\n".join(source[0][lo-1:hi]).encode()).hexdigest()==md["span_sha256_utf8"] and not md["promotion"],"non-narrative metadata")
            mdlen=hi-lo+1;at=hi+1;metadata_lines+=mdlen
        require(r["range"]==[at,m["end"]] and r["official_unit_seal"]==m["unit_seal"] and r["previous_macro_id"]==m["previous_macro"] and r["release_blob"]==c["release_blob"],"book receipt chain")
        result=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=bids,expected_range=[at,m["end"]])
        require(result["lines"]+mdlen==m["lines"] and all(x["book"]=="V" and not x["promotion"] for x in r["records"]),"book coverage")
        bids.update(x["id"] for x in r["records"]);baxes.update(result["axes_represented"]);brecs+=result["records"];blines+=result["lines"]+mdlen
        authority.update(x["authority"] for x in r["records"]);visibility.update(x["visibility"] for x in r["records"])
        coverage_by_macro.append({"macro":g["macro"],"lines":m["lines"],"records":result["records"],"metadata_lines":mdlen})
    require(blines==t["book_v_lines"]==sum(m["lines"] for m in q[42:75]) and brecs==t["book_v_records"]==len(bids) and metadata_lines==24 and len(coverage_by_macro)==33,"full book ledger totals")
    require(audit["boundary"]["book_closed"] and journal[-1][1]["day"]==537 and journal[-1][1]["hour"]=="23h46" and journal[-1][0]["chosen_option"]==0 and not audit["boundary"]["next_started"],"Book VI blocked")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_V_0075_BOUNDARY_COMPLETE","cycle_status":"PASS_STAGING_ONLY","book_boundary_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4217+recs,"book_v_records":brecs,"book_v_lines":blines,"book_v_macros":33,"book_v_axes":sorted(baxes),"book_v_metadata_lines":metadata_lines,"book_v_authority":dict(authority),"book_v_visibility":dict(visibility),"book_v_coverage":coverage_by_macro,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":9,"book_closed":True,"book_vi_started":False,"next_source":q[75]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_vi_80(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas
    from .omega_turbo_recovery import git_blob
    from .book_opening import require_book_open_approval
    from .retro_ratify import PARTS, _source_lines, _request, _continuity_reconciled, author_ratification_choice
    root=Path(root);archive=Path(archive)
    prior=verify_book_v_75(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0075-validated.json","75c1406ed2991e37681c96db3804ffe37aecc92e")
    old=read(root,c["cycle_review_path"],"6458f000209840e883dec25f009468bab554f85e")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    require(prior["status"]=="PASS_NATIVE_BOOK_V_0075_BOUNDARY_COMPLETE" and old["status"]==boundary["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS" and c["book_v_closed"] and not c["book_vi_started"],"prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0076-0080-review-pending.json","b99a79c2fce003cd8c6cf0ca7b7873bfcf2b92ce")
    require(audit["previous_cycle_blob"]=="6458f000209840e883dec25f009468bab554f85e" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(76,81)),"cycle predecessor")
    journal=list(islice(_journal(archive),14))
    require(len(journal)==14 and journal[8][0]["episode_id"]==c["source"] and journal[8][1]["book_closed"] is True and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[9:]),"journal boundary")
    ap=audit["authority_pins"]
    authority={k:read(archive,ap[k]["path"],ap[k]["blob"]) for k in ("opening_approval","reauthorization","ratification","trigger","rejection","caedren")}
    require(authority["ratification"]==_request(archive) and authority["reauthorization"]["new_authorization_exists"] and authority["opening_approval"]["approved"] and authority["trigger"]["expected_previous_sequence"]==9,"opening authority")
    opening=require_book_open_approval(archive,journal[8][1],journal[9][0]["metadata"])
    require(opening["status"]=="AUTHOR_APPROVED_BOOK_VI_DRAFT_ONLY" and not opening["canon_changed"],"opening gate")
    reject=authority["rejection"]; require(reject["do_not_promote"] and reject["do_not_reuse_as_opening"] and reject["status"]=="REJEITADO_PELO_AUTOR_NAO_CANONICO" and not (archive/"canon/episodes"/(reject["episode_id"]+".json")).exists() and reject["episode_id"] not in {m["source"] for m in q},"rejected version exclusion")
    for k in ("export","rejected_draft"):
        v=ap[k];raw=(archive/v["path"]).read_bytes();require(git_blob(raw)==v["blob"] and sha256(raw).hexdigest()==v["sha256"],"raw custody "+k)
    export_lines=_source_lines(archive)
    for i,item in enumerate(PARTS):
        name=item["id"];sp=audit["macros"][i]["source_provenance"];lo,hi=item["lines"]
        exact=("\n".join(export_lines[lo-1:hi])+"\n").encode()
        proof=read(archive,"episodes/"+name+"/draft/source_proof.json",ap["source_proofs"][i])
        read(archive,"episodes/"+name+"/review/continuity_review.json",ap["continuity_reviews"][i])
        _continuity_reconciled(archive,item)
        require(sha256(exact).hexdigest()==item["sha"]==sp["full_story_sha256"] and proof["source_sha256"]==item["sha"] and proof["full_export_sha256"]==ap["export"]["sha256"] and (archive/"editorial/recovery/originals"/(name+".txt")).read_bytes()==exact,"ratified exact export slice")
        require(author_ratification_choice(archive,name)["option"]==[4,4,0][i] and sp["chosen_option"]==[4,4,0][i],"ratification not fictional choice")
    require(authority["caedren"]["physical_presence_in_D539_prose"] and not authority["caedren"]["military_affiliation_proven"] and not authority["caedren"]["travel_route_proven"] and not authority["caedren"]["legion_command_assumed"],"Caedren uncertainty")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(76,81)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="75c1406ed2991e37681c96db3804ffe37aecc92e";prev_episode=c["source"];prev_day=537;prev_clock="23h46"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[9:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==76+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        require(L[8 if num<79 else 6]==sp["editorial_header"] and closure["chosen_option"]==[4,4,0,5,4][num-76],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="6458f000209840e883dec25f009468bab554f85e" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4275+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")
    A,B,C,D,E=[sources[x["source"]] for x in q[75:80]]
    require("Capacidade futura para cem mil" in A[3152] and "Nenhuma obra fora declarada aprovada" in A[3440] and "O horizonte ainda não mudou" in "\n".join(A[-12:]),"D538 proposal")
    require("três marcos reais em três dias" in B[192] and "3.600 unidades físicas" in B[1858] and "Lucas, por sua vez, não conhecia o nome de Tharvek" in B[4274],"D538 first mark and reader")
    require("Varo estava corrigindo a posição de um legionário quando Caedren apareceu."==C[1278] and "não poderei dar ordens militares" in C[1486] and "quarenta mil moradias" in C[3022] and "Não população residente" in C[3030],"D539 authority and capacity")
    require("Não eram mensagens" in D[538] and "mil e quinhentas unidades funcionais adicionais" in D[582] and "não incluiu Vértice" in D[584] and "Não vou sentar na presidência" in D[694],"D540 limits")
    require("O lote é seu. A cidade não é." in E[250] and "Trinta e um mil metros quadrados internos" in E[496] and "Não estou em três lugares" in E[1078] and "Noventa e seis autômatos físicos" in E[1100] and "ARGOS continua no Campo Aurora" in E[1226] and "Asa Livre" in E[1240] and "esta noite quero ficar aqui" in E[1694],"D541 tower")
    t=audit["totals"];require(recs==72 and lines==14243 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4275+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==recs and t["book_vi_lines"]==lines and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0080_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","book_vi_opening_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4275+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":recs,"book_vi_lines":lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":14,"ratified_exact_export_slices":3,"rejected_r17_excluded":True,"caedren_uncertainty_preserved":True,"next_source":q[80]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_vi_85(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas, _is_exact_author_approved_c02_pv_exception, _C02_PV_MULTIDAY_APPROVED_PROSE_SHA256
    from .day_arc_audit import inspect_day_arc
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_vi_80(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0080-validated.json","7bb26c6e7c63b8abaa0b7e8f23621b18fc465112")
    old=read(root,c["cycle_review_path"],"ddc148b0b9b7bcbaa2cec9aabc3c5ee8534ba2e9")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    opening=read(root,c["book_vi_opening_review_path"],"8c6c44a7dd2e10254f50810eec92f025b9a2bed4")
    require(prior["status"]=="PASS_NATIVE_BOOK_VI_0080_CYCLE_COMPLETE" and old["status"]==boundary["status"]==opening["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0081-0085-review-pending.json","bf15c7261bfead5d25ff85afc634d629f1878a34")
    require(audit["previous_cycle_blob"]=="ddc148b0b9b7bcbaa2cec9aabc3c5ee8534ba2e9" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["book_vi_opening_blob"]=="8c6c44a7dd2e10254f50810eec92f025b9a2bed4" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(81,86)),"cycle predecessor")
    journal=list(islice(_journal(archive),19))
    require(len(journal)==19 and journal[13][0]["episode_id"]==c["source"] and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[14:]),"journal boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(81,86)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="7bb26c6e7c63b8abaa0b7e8f23621b18fc465112";prev_episode=c["source"];prev_day=541;prev_clock="22h06"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[14:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==81+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        arc=inspect_day_arc(d.prose)
        require(arc["first"]=={"day":continuity["first_day"],"hour":continuity["first_clock"]} and arc["last"]=={"day":head["day"],"hour":head["hour"]},"literal clock endpoints")
        if num==85:
            require(_is_exact_author_approved_c02_pv_exception(journal[17][1],closure["metadata"],d.prose),"native exact exception")
            require(not _is_exact_author_approved_c02_pv_exception(journal[17][1],closure["metadata"],d.prose+" ") and not _is_exact_author_approved_c02_pv_exception(journal[16][1],closure["metadata"],d.prose),"exception negative controls")
            ex=audit["chronology_exception"]
            require(ph==ex["prose_sha256"]==_C02_PV_MULTIDAY_APPROVED_PROSE_SHA256 and arc["first"]==ex["first"] and arc["last"]==ex["last"] and arc["days_touched"]==ex["days"] and arc["scene_clock_count"]==ex["scene_clock_count"]==27 and not arc["chronological"],"exact multiday contract")
        else:
            require(arc["days_touched"]==[head["day"]] and not _is_exact_author_approved_c02_pv_exception(journal[num-67][1],closure["metadata"],d.prose),"no expanded exception")
            if num==84:
                require(not arc["chronological"] and "Na mesma manhã em que Lucas" in "\n".join(L[958:980]),"D545 same day parallel scenes")
            else:require(arc["chronological"],"ordinary chronological scene order")
        require(L[6]==sp["editorial_header"] and closure["chosen_option"]==[5,5,4,4,5][num-81],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="ddc148b0b9b7bcbaa2cec9aabc3c5ee8534ba2e9" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4347+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==72+recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")

    A,B,C,D,E=[sources[x["source"]] for x in q[80:85]]
    require("dois registradores indicaram uma oscilação" in A[864] and "não vou chamar cada oscilação de mensagem" in A[910] and "não posso responsabilizar os agressores" in A[966],"D542 evidence")
    require("não restaurava seres vivos" in B[492] and "autorização está datada do Dia 540" in B[568] and "Não confundam curiosidade com culpa" in B[652] and "Um deles escapou" in B[1442],"D543 safeguards")
    require("Não deve decidir sozinha quem merece ficar preso" in C[302] and "Casa das Garantias de Três Arcos" in C[676] and "Nada de invadir os laboratórios" in C[1126] and "Vesra Keth" in C[1936],"D544 institutions")
    require("LUCAS · RUMO" in D[1222] and "Ainda não decidi se quero pilotar" in "\n".join(D[1252:1394]) and "ensaio de bancada, não uma descida real em voo" in "\n".join(D[1252:1394]),"D545 prototype")
    require("Mais cedo," in E[711] and "JARDINEIRA DO CEDRO" in E[239] and "SETE CAMINHOS DO CEDRO" in E[1991] and "O primeiro ensaio de suspensão real estava concluído" in E[2247] and "Não era voo 001 em campo aberto" in "\n".join(E[2151:2303]) and "ARQUIVO DAS MARÉS" in E[2747] and "Não possuía olhos na Torre do Criador" in E[2819],"D548 evidence")
    t=audit["totals"];require(recs==96 and lines==11583 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4347+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==72+recs and t["book_vi_lines"]==14243+lines and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0085_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4347+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":72+recs,"book_vi_lines":14243+lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":19,"exact_multiday_exception":True,"exception_negative_controls":2,"scene_clock_count_0085":27,"d545_parallel_scene_preserved":True,"next_source":q[85]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_vi_90(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas, _is_exact_author_approved_c02_pv_exception
    from .day_arc_audit import inspect_day_arc
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_vi_85(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0085-validated.json","7660e9de3860cfeab4619b7610fac6090056dacb")
    old=read(root,c["cycle_review_path"],"0bff215cbc214b20f462b1d1ff6f703131f49784")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    opening=read(root,c["book_vi_opening_review_path"],"8c6c44a7dd2e10254f50810eec92f025b9a2bed4")
    chrono=read(root,c["chronology_review_path"],"b3107747317196af16bd8902af1f6b1c108d0132")
    require(prior["status"]=="PASS_NATIVE_BOOK_VI_0085_CYCLE_COMPLETE" and prior["exact_multiday_exception"] and prior["exception_negative_controls"]==2 and old["status"]==boundary["status"]==opening["status"]==chrono["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0086-0090-review-pending.json","922ebb7b88d9f1201511d0776e583288ea63d805")
    require(audit["previous_cycle_blob"]=="0bff215cbc214b20f462b1d1ff6f703131f49784" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["book_vi_opening_blob"]=="8c6c44a7dd2e10254f50810eec92f025b9a2bed4" and audit["prior_chronology_blob"]=="b3107747317196af16bd8902af1f6b1c108d0132" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(86,91)),"cycle predecessor")
    journal=list(islice(_journal(archive),24))
    require(len(journal)==24 and journal[18][0]["episode_id"]==c["source"] and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[19:]),"journal boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(86,91)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="7660e9de3860cfeab4619b7610fac6090056dacb";prev_episode=c["source"];prev_day=548;prev_clock="22h31"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[19:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==86+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        arc=inspect_day_arc(d.prose)
        require(arc["first"]=={"day":continuity["first_day"],"hour":continuity["first_clock"]} and arc["last"]=={"day":head["day"],"hour":continuity["last_scene_clock"]} and arc["days_touched"]==[head["day"]] and arc["chronological"],"literal scene clocks")
        require(not _is_exact_author_approved_c02_pv_exception(journal[num-67][1],closure["metadata"],d.prose),"no expanded exception")
        if num==87:
            require(continuity["last_scene_clock"]=="20h41" and head["hour"]=="21h36" and "Dia 550 encerrado às 21h36" in "\n".join(L[-12:]),"D550 textual closure not scene clock")
        else:require(continuity["last_scene_clock"]==head["hour"],"ordinary closure clock")
        require(L[5]==sp["editorial_header"] and closure["chosen_option"]==[4,4,4,4,5][num-86],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="0bff215cbc214b20f462b1d1ff6f703131f49784" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4443+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==168+recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")


    A,B,C,D,E=[sources[x["source"]] for x in q[85:90]]
    def has(L,*terms):
        s="\n".join(L)
        return all(x in s for x in terms)
    require(has(A,"Círan","Não havia","RUMO","Ithran não foi derrotado nesta Parte","GÊNESE nunca deixou de ser plena"),"D549 source consequences")
    require(has(B[713:833],"RUMO — PROTÓTIPO DE APOIO 01","GÊNESE manifestou as quatro plataformas adicionais","Não criou quatro pessoas conscientes"),"D550 Rumo count")
    require(has(C[1014:1102],"noventa e dois","oitenta e cinco","oitenta e um","quarenta e dois","sem serem transportados","Não havia duplicações","Trezentos.") and has(C[1102:1316],"Não houve obrigação de responder","Não como rei. Como amigo."),"D551 physical voluntary reunion")
    require(has(D[1058:1178],"Não conseguiram","A contenção funcionara","preservar as provas") and has(D[-14:],"Selo Oco inimigo contido","ainda não derrotada conclusivamente"),"D552 containment")
    require(has(E[191:259],"ITHRAN VEYK","Ainda vamos precisar confirmar o homem") and has(E[1171:1271],"Cessar fogo","Selen entregou o foco perceptivo selado","Ilvar colocou as ordens","E estava vivo para responder por isso") and has(E[1527:1587],"apenas o primeiro ponto de encaminhamento","Serakh Il-Varenn ainda não sabia") and has(E[-14:],"sem execução, absolvição ou sentença instantânea","Nenhuma delegação distante foi teleportada"),"D553 surrender and delayed knowledge")
    t=audit["totals"];require(recs==98 and lines==10020 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4443+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==168+recs and t["book_vi_lines"]==25826+lines and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0090_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4443+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":168+recs,"book_vi_lines":25826+lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":24,"prior_exact_multiday_exception_preserved":True,"d550_textual_closure_verified":True,"d551_reunion_verified":True,"d553_surrender_and_custody_verified":True,"next_source":q[90]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_vi_95(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas, _is_exact_author_approved_c02_pv_exception, canonical
    from .day_arc_audit import inspect_day_arc
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_vi_90(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0090-validated.json","5fe7b6abc14ecb1397b203b23859533aedc4c670")
    old=read(root,c["cycle_review_path"],"3171277a70304fe927c47704023d5c6d95757b34")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    opening=read(root,c["book_vi_opening_review_path"],"8c6c44a7dd2e10254f50810eec92f025b9a2bed4")
    chrono=read(root,c["chronology_review_path"],"b3107747317196af16bd8902af1f6b1c108d0132")
    require(prior["status"]=="PASS_NATIVE_BOOK_VI_0090_CYCLE_COMPLETE" and prior["prior_exact_multiday_exception_preserved"] and prior["d550_textual_closure_verified"] and prior["d551_reunion_verified"] and prior["d553_surrender_and_custody_verified"] and old["status"]==boundary["status"]==opening["status"]==chrono["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0091-0095-review-pending.json","770c82af32c291c51d767fe46a9190158df026c9")
    require(audit["previous_cycle_blob"]=="3171277a70304fe927c47704023d5c6d95757b34" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["book_vi_opening_blob"]=="8c6c44a7dd2e10254f50810eec92f025b9a2bed4" and audit["prior_chronology_blob"]=="b3107747317196af16bd8902af1f6b1c108d0132" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(91,96)),"cycle predecessor")
    journal=list(islice(_journal(archive),29))
    require(len(journal)==29 and journal[23][0]["episode_id"]==c["source"] and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[24:]),"journal boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(91,96)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="5fe7b6abc14ecb1397b203b23859533aedc4c670";prev_episode=c["source"];prev_day=553;prev_clock="22h41"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[24:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==91+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        arc=inspect_day_arc(d.prose)
        require(arc["first"]=={"day":continuity["first_day"],"hour":continuity["first_clock"]} and arc["last"]=={"day":head["day"],"hour":continuity["last_scene_clock"]} and arc["days_touched"]==[head["day"]] and arc["chronological"],"literal scene clocks")
        require(not _is_exact_author_approved_c02_pv_exception(journal[num-67][1],closure["metadata"],d.prose),"no expanded exception")
        require(continuity["last_scene_clock"]==head["hour"],"ordinary closure clock")
        require(L[5]==sp["editorial_header"] and closure["chosen_option"]==[4,5,4,4,4][num-91],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="3171277a70304fe927c47704023d5c6d95757b34" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4541+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==266+recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")



    A,B,C,D,E=[sources[x["source"]] for x in q[90:95]]
    def has(L,*terms):
        s="\n".join(L)
        return all(x in s for x in terms)
    require(has(A[264:352],"Ainda não fica","linguagem arquitetônica") and has(A[934:1038],"demonstração de princípio, não implantação definitiva","Um pequeno projétil de ensaio","Um pulso elemental controlado","Um foco de ilusão") and has(A[-8:],"nenhuma foi implantada"),"D554 proposal and isolated test")
    require(has(B[489:575],"A **Égide Interna** estava operacional","A **Égide do Horizonte** nasceu","passou a integrar a reserva de defesa") and has(B[575:640],"não proclamadas uma frota já instalada") and has(B[1193:1261],"Não está aprovado. Não está instalado."),"D555 dual aegis and unbuilt contingencies")
    require(has(C[947:1002],"Não houve falsa assinatura de Tharvek ou Elyrien") and has(C[-8:],"Nem Elyrien nem Tharvek chegaram fisicamente","sem confirmação de autoria comum"),"D556 arrival and consent")
    require(has(D[234:330],"oitenta e seis metros de comprimento e dezenove de altura","setenta e dois metros de envergadura") and has(D[856:938],"oito tripulantes e noventa e dois passageiros: cem ocupantes no total") and has(D[783:856],"Sem necessidade de intervenção de GÊNESE na sustentação") and has(D[-8:],"até 260 cascos como alocação estratégica condicional"),"D557 actual configuration and command")
    require(has(E[595:653],"Autorizo um pouso de visita neste terreno") and has(E[845:898],"Conhecia Três Arcos por relações anteriores","Possível","não concedida") and has(E[-8:],"sem audiência real ocorrida nem aceite da Conferência Continental","nenhum ataque ou transporte maciço efetivado"),"D558 diplomatic boundaries")
    x=audit["r2_authority_preflight"];pins=x["pins"];r2=x["episode"];r1=x["rejected_episode"]
    reject=read(archive,"editorial/rejections/"+r1+".json",pins["rejection"])
    rev=read(archive,"editorial/revisions/"+r1+"/R2/revision_manifest.json",pins["revision_manifest"])
    feedback=read(archive,"editorial/feedback/2026-11-21-d559-lucas-miren-althea-thaeron-rewrite.json",pins["feedback"])
    choice=read(archive,"choices/"+r2+"/option-4.json",pins["choice"])
    reader=read(archive,"delivery/reader_receipts/"+r2+".json",pins["reader_receipt"])
    proof=read(archive,"episodes/"+r2+"/draft/source_proof.json",pins["source_proof"])
    imm=read(archive,"episodes/"+r2+"/draft/manifesto_imutavel.json",pins["immutable_manifest"])
    rejected_imm=read(archive,"episodes/"+r1+"/draft/manifesto_imutavel.json",pins["rejected_manifest"])
    nextcl=read(archive,"canon/episodes/"+r2+".json",x["closure_blob"])
    require(q[95]["source"]==r2 and q[95]["lines"]==1584 and nextcl["sequence"]==30 and nextcl["previous_episode_id"]==prev_episode and nextcl["story_sha256"]==x["story_sha256"]==imm["original_readback_sha256"]==reader["story_sha256"]==proof["source_sha256"] and nextcl["chosen_option"]==choice["option"]==4 and sha256(canonical(choice)).hexdigest()==nextcl["choice_sha256"]==x["choice_sha256"],"R2 author closure")
    require(reject["do_not_promote"] and reject["do_not_reuse_as_opening"] and reject["original_narrative_sha256"]==rejected_imm["original_readback_sha256"]==x["rejected_story_sha256"]!=x["story_sha256"] and reject["approved_replacement"]["episode_id"]==rev["promoted_canon_episode_id"]==r2 and rev["promoted_sequence"]==30 and rev["promoted_story_sha256"]==x["story_sha256"] and rev["original_r1_status"]=="PRESERVED_UNPROMOTED" and feedback["prior_draft_retained"] and "CONTINUAR EXCLUSIVAMENTE da REVISÃO R2" in choice["free_text"] and not (archive/"canon"/"episodes"/(r1+".json")).exists(),"R1 exclusion")
    orig=(archive/proof["source_file"]).read_bytes();narr=(archive/"episodes"/r2/"draft"/"narrativa_integral.md").read_bytes();edit=(archive/rev["current_revision_text"]).read_bytes()
    require(orig==narr and git_blob(orig)==pins["closed_original_and_narrative"] and sha256(orig).hexdigest()==x["story_sha256"] and git_blob(edit)==pins["editorial_revision_text"]==rev["current_revision_blob_sha"] and edit!=narr and proof["ui_parity"]=="NOT_INDEPENDENTLY_VERIFIED" and x["scope"]=="AUTHORITY_PREFLIGHT_ONLY_NO_0096_RECEIPT_OR_SEMANTIC_RECOVERY","R2 distinct physical source custody")
    t=audit["totals"];require(recs==95 and lines==6426 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4541+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==266+recs and t["book_vi_lines"]==35846+lines and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0095_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4541+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":266+recs,"book_vi_lines":35846+lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":29,"prior_exact_multiday_exception_preserved":True,"d555_dual_aegis_verified":True,"d557_argos_configuration_verified":True,"d558_thalor_authority_verified":True,"r2_authority_preflight_verified":True,"r1_excluded":True,"macro_0096_recovered":False,"next_source":q[95]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}


def verify_book_vi_100(root,archive):
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas, _is_exact_author_approved_c02_pv_exception
    from .day_arc_audit import inspect_day_arc
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_vi_95(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0095-validated.json","20549e326e25f150ab466f3b8b5b90e86216ce45")
    old=read(root,c["cycle_review_path"],"17e173fc035789949ca54c71d0ad8bf45aeb5f9d")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    opening=read(root,c["book_vi_opening_review_path"],"8c6c44a7dd2e10254f50810eec92f025b9a2bed4")
    chrono=read(root,c["chronology_review_path"],"b3107747317196af16bd8902af1f6b1c108d0132")
    auth=read(root,c["r2_authority_preflight_path"],"02db7ecdb1a6e4d9cf20dd1c18ead08458971726")
    require(prior["status"]=="PASS_NATIVE_BOOK_VI_0095_CYCLE_COMPLETE" and prior["prior_exact_multiday_exception_preserved"] and prior["r2_authority_preflight_verified"] and prior["r1_excluded"] and not prior["macro_0096_recovered"] and auth["status"]=="PASS_AUTHORITY_PREFLIGHT_ONLY" and old["status"]==boundary["status"]==opening["status"]==chrono["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0096-0100-review-pending.json","95df5328fb38a0f25a3f115f5f8f6e8e63f1d108")
    require(audit["previous_cycle_blob"]=="17e173fc035789949ca54c71d0ad8bf45aeb5f9d" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["book_vi_opening_blob"]=="8c6c44a7dd2e10254f50810eec92f025b9a2bed4" and audit["prior_chronology_blob"]=="b3107747317196af16bd8902af1f6b1c108d0132" and audit["r2_authority_preflight_blob"]=="02db7ecdb1a6e4d9cf20dd1c18ead08458971726" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(96,101)),"cycle predecessor")
    journal=list(islice(_journal(archive),34))
    require(len(journal)==34 and journal[28][0]["episode_id"]==c["source"] and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[29:]),"journal boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(96,101)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="20549e326e25f150ab466f3b8b5b90e86216ce45";prev_episode=c["source"];prev_day=558;prev_clock="21h31"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[29:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==96+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        arc=inspect_day_arc(d.prose)
        require(arc["first"]=={"day":continuity["first_day"],"hour":continuity["first_clock"]} and arc["last"]=={"day":head["day"],"hour":continuity["last_scene_clock"]} and arc["days_touched"]==[head["day"]] and arc["chronological"],"literal scene clocks")
        require(not _is_exact_author_approved_c02_pv_exception(journal[num-67][1],closure["metadata"],d.prose),"no expanded exception")
        require(continuity["last_scene_clock"]==head["hour"],"ordinary closure clock")
        require(L[5]==sp["editorial_header"] and closure["chosen_option"]==[4,4,5,4,4][num-96],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="17e173fc035789949ca54c71d0ad8bf45aeb5f9d" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4636+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==361+recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")




    A,B,C,D,E=[sources[x["source"]] for x in q[95:100]]
    def has(L,*terms):
        s="\n".join(L)
        return all(x in s for x in terms)
    sp=audit["macros"][0]["source_provenance"];special=audit["r2_recovery_review"]
    require(sp["episode_id"]==auth["episode"]==special["source_only"] and sp["sequence"]==auth["sequence"]==30 and sp["closure_blob"]==auth["closure_blob"] and sp["full_story_sha256"]==auth["story_sha256"] and sp["choice_sha256"]==auth["choice_sha256"] and sp["narrative_blob"]==auth["pins"]["closed_original_and_narrative"]!=auth["pins"]["editorial_revision_text"] and special["source_provenance"]==sp and special["receipt_blob"]==audit["macros"][0]["blob"] and special["ui_parity"]=="NOT_INDEPENDENTLY_VERIFIED" and special["editorial_semantic_equivalence"]=="NOT_CERTIFIED" and all(g["source_provenance"]["episode_id"]!=auth["rejected_episode"] for g in audit["macros"]),"R2 recovered closed source exclusively")
    rr=read(root,audit["macros"][0]["receipt"],special["receipt_blob"])
    last=rr["records"][-1];require(last["type"]=="options" and last["authority"]=="NARRATOR_PROPOSED_BRANCH_NOT_EVENT" and [last["evidence"]["line_start"],last["evidence"]["line_end"]]==special["option_range"] and has(A[1573:],"ESCOLHAS","AÇÃO LIVRE"),"R2 options not events")
    require(has(A[1571:1573],"Althea já conhecia Lucas, Miren, Lysa, Kael e Varo","sem haver plenária nem aliança militar","Thaeron e Iriel **já conhecem Lucas**") and has(A[853:941],"Não era a resposta ao paradeiro de Talis"),"D559 historical relationship and documentary lead")
    require(has(B[913:1067],"Dez respirações","Não era uma resposta sobre Talis") and has(B[1163:1277],"O Sétimo Observatório não era a localização de Talis"),"D560 protected investigation")
    require(has(C[944:1072],"TALIS ELVENAR","Não havia ali o rosto de Talis") and has(C[1072:1234],"não deve ser confundido com resposta","não temos um segundo aparelho identificado") and has(C[1670:1822],"Até lá, não abriremos nenhum canal desconhecido") and has(C[1822:1938],"Não apresentou um prêmio novo","Gênese de Horizonte"),"D561 epistemic boundaries")
    require(has(D[333:437],"Chamam-nas de **velários**","Não tentou criá-las") and has(D[437:599],"Não há informação suficiente para estabelecer a causa ou a finalidade de sua chegada") and has(D[1525:1699],"Autorizo a intervenção neste espaço","Não era uma promessa de floresta ressuscitada"),"D562 natural fauna and consent")
    require(has(E[966:1054],"Uma das cartas postadas por Caedren no Dia 561","A segunda carta de Caedren, dirigida ao mago, também seguia por seus próprios caminhos") and has(E[1644:1786],"Então é melhor não plantar aqui","não uma ressurreição decretada") and has(E[-12:],"a conferência propriamente dita ainda pertence ao futuro da história"),"D563 letters seed and conference not occurred")
    t=audit["totals"];require(recs==96 and lines==9848 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4636+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==361+recs and t["book_vi_lines"]==42272+lines and t["original_events"]==original_events and t["original_knowledge"]==original_knowledge and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0100_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4636+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":361+recs,"book_vi_lines":42272+lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":34,"prior_exact_multiday_exception_preserved":True,"r2_closed_recovery_verified":True,"r1_excluded":True,"r2_options_not_events":True,"talis_documentary_only_verified":True,"velarios_and_ecology_verified":True,"conference_not_occurred_verified":True,"next_source":q[100]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def verify_book_vi_105(root,archive):
    import re
    from hashlib import sha256
    from itertools import islice
    from .git_cycle import verify_episode, _journal, review_deltas, _is_exact_author_approved_c02_pv_exception, canonical
    from .day_arc_audit import inspect_day_arc
    from .omega_turbo_recovery import git_blob
    root=Path(root);archive=Path(archive)
    prior=verify_book_vi_100(root,archive)
    c=read(root,ROOT+"recovery-checkpoint-0100-validated.json","ba27cbb336b9292f8ce785363d497acff1eddb6a")
    old=read(root,c["cycle_review_path"],"e041f823e50438cf98f3dca4732ffad16424e0e3")
    boundary=read(root,c["book_v_boundary_review_path"],"2a4f9816734f2051aa7d60fe19931b09776cc360")
    opening=read(root,c["book_vi_opening_review_path"],"8c6c44a7dd2e10254f50810eec92f025b9a2bed4")
    chrono=read(root,c["chronology_review_path"],"b3107747317196af16bd8902af1f6b1c108d0132")
    auth=read(root,c["r2_authority_preflight_path"],"02db7ecdb1a6e4d9cf20dd1c18ead08458971726")
    require(prior["status"]=="PASS_NATIVE_BOOK_VI_0100_CYCLE_COMPLETE" and prior["prior_exact_multiday_exception_preserved"] and prior["r2_closed_recovery_verified"] and prior["r1_excluded"] and auth["status"]=="PASS_AUTHORITY_PREFLIGHT_ONLY" and old["status"]==boundary["status"]==opening["status"]==chrono["status"]=="PASS_STAGING_ONLY" and c["native_validation"]=="PASS","prior")
    q=read(root,"audit/omega008-c/bulk-macro-queue.json","e5a5f9e358d20acf8559f6313c2da24b64665f48")["macros"]
    audit=read(root,ROOT+"cycle-0101-0105-review-pending.json","2c2b5b375c6a7696bf2a0648e6efa98766ea4475")
    require(audit["previous_cycle_blob"]=="e041f823e50438cf98f3dca4732ffad16424e0e3" and audit["book_v_boundary_blob"]=="2a4f9816734f2051aa7d60fe19931b09776cc360" and audit["book_vi_opening_blob"]=="8c6c44a7dd2e10254f50810eec92f025b9a2bed4" and audit["prior_chronology_blob"]=="b3107747317196af16bd8902af1f6b1c108d0132" and audit["r2_authority_preflight_blob"]=="02db7ecdb1a6e4d9cf20dd1c18ead08458971726" and audit["prior_overlays"]==old["overlays"] and [g["macro"] for g in audit["macros"]]==list(range(101,106)),"cycle predecessor")
    journal=list(islice(_journal(archive),39))
    require(len(journal)==39 and journal[33][0]["episode_id"]==c["source"] and all(head["book"]=="Livro VI" and head["book_closed"] is False for _,head in journal[34:]),"journal boundary")
    ids=set()
    for f in (root/ROOT).glob("*.json"):
        if any(f.name.startswith("partial-macro-%04d-"%i) for i in range(101,106)):continue
        obj=json.loads(f.read_bytes());rows=obj.get("records")
        if isinstance(rows,list):ids.update(x["id"] for x in rows if isinstance(x,dict) and "id" in x)
    prev="ba27cbb336b9292f8ce785363d497acff1eddb6a";prev_episode=c["source"];prev_day=563;prev_clock="22h43"
    recs=0;lines=0;original_events=0;original_knowledge=0;metrics=[];sources={};axes=set()
    for g,(closure,head) in zip(audit["macros"],journal[34:]):
        num=g["macro"];m=q[num-1];name=m["source"];sp=g["source_provenance"]
        require(num==101+len(metrics) and m["book_hint"]=="VI" and m["status"]=="PENDING_CLOSED_PROSE" and m["previous_macro"]==q[num-2]["id"] and closure["episode_id"]==name and closure["previous_episode_id"]==prev_episode and closure["sequence"]==num-66,"episode chain")
        d,manifest=verify_episode(archive,name)
        folder=archive/"episodes"/name/"draft"
        require(closure==read(archive,"canon/episodes/"+name+".json",sp["closure_blob"]) and manifest["original_readback_sha256"]==closure["story_sha256"]==sp["full_story_sha256"] and closure["previous_head_sha256"]==sp["previous_head_sha256"] and closure["choice_sha256"]==sp["choice_sha256"] and closure["chosen_option"]==sp["chosen_option"] and closure.get("ratification_kind")==sp["ratification_kind"],"closure custody")
        for fname,key in [("episode_draft.json","draft_blob"),("manifesto_imutavel.json","immutable_manifest_blob"),("narrativa_integral.md","narrative_blob")]:
            require(git_blob((folder/fname).read_bytes())==sp[key],"physical provenance")
        ev=read(archive,"episodes/"+name+"/review/eventos_revisados.json",sp["reviewed_events_blob"])
        kn=read(archive,"episodes/"+name+"/review/conhecimento_revisado.json",sp["reviewed_knowledge_blob"])
        require(ev["review_status"]==kn["review_status"]=="REVISADO" and ev["source_sha256"]==closure["story_sha256"] and ev["events"]==closure["events"] and kn["knowledge"]==closure["knowledge"],"reviewed sidecars")
        events,knowledge=review_deltas(archive,name,d)
        require(events==closure["events"] and knowledge==closure["knowledge"],"native reviewed deltas")
        L=tuple(d.prose.splitlines());ph=sha256(d.prose.encode()).hexdigest();sources[name]=L
        require(len(L)==m["lines"]==sp["prose_lines"] and ph==sp["prose_sha256"] and all(e["source"]["literal_anchor"] in L[e["source"]["line"]-1] for e in closure["events"]),"literal evidence")
        continuity=g["continuity"];require(continuity["previous_episode"]==prev_episode and continuity["previous_day"]==prev_day and continuity["previous_clock"]==prev_clock and str(continuity["first_day"]) in "\n".join(L[:100]) and continuity["first_clock"] in "\n".join(L[:100]) and continuity["first_day"] in (prev_day,prev_day+1) and (continuity["first_day"]>prev_day or continuity["first_clock"]>=prev_clock) and continuity["end_day"]==head["day"] and continuity["end_clock"]==head["hour"] and continuity["end_location"]==head["location"] and head["book"]=="Livro VI" and head["book_closed"]==d.book_closed==sp["book_closed"]==False,"chronological boundary")
        arc=inspect_day_arc(d.prose)
        require(arc["first"]=={"day":continuity["first_day"],"hour":continuity["first_clock"]} and arc["last"]=={"day":head["day"],"hour":continuity["last_scene_clock"]} and arc["days_touched"]==[head["day"]] and arc["chronological"]==(num!=104),"literal scene clocks")
        clocks=[]
        for n,line in enumerate(L,1):
            mclock=re.search(r"DIA (\d+) · (\d{2}h\d{2})",line)
            if mclock:
                clocks.append(dict(line=n,scene=len(clocks)+1,day=int(mclock[1]),hour=mclock[2]))
        require(clocks==continuity["explicit_clocks"] and len(clocks)==continuity["scene_clock_count"]==[11,12,13,11,13][num-101],"exact clocks")
        rewinds=[{"from":a,"to":b} for a,b in zip(clocks,clocks[1:]) if (b["day"],b["hour"])<(a["day"],a["hour"])]
        require(rewinds==continuity["source_order_rewinds"] and continuity["chronology_exception_0085_extended"] is False,"parallel order")
        require((len(rewinds)==1 and rewinds[0]["from"]["line"]==1466 and rewinds[0]["to"]["line"]==1694 and rewinds[0]["from"]["hour"]=="15h07" and rewinds[0]["to"]["hour"]=="11h28") if num==104 else not rewinds,"scoped single-day rewind")
        require(not _is_exact_author_approved_c02_pv_exception(journal[num-67][1],closure["metadata"],d.prose),"no expanded exception")
        require(continuity["last_scene_clock"]==head["hour"],"ordinary closure clock")
        require(L[5]==sp["editorial_header"] and closure["chosen_option"]==[4,5,5,4,4][num-101],"separate entry and closure authority")
        cp=read(root,g["checkpoint"],g["checkpoint_blob"]);r=read(root,g["receipt"],g["blob"],cp["receipt_sha256"])
        require(r["source_provenance"]==cp["source_provenance"]==sp and sp["closure_event_count"]==len(closure["events"]) and sp["closure_knowledge_count"]==len(closure["knowledge"]) and r["previous_checkpoint_blob"]==cp["previous_checkpoint_blob"]==prev and r["cycle_review_blob"]=="e041f823e50438cf98f3dca4732ffad16424e0e3" and r["previous_macro_id"]==m["previous_macro"] and r["official_unit_seal"]==m["unit_seal"] and r["release_blob"]==c["release_blob"] and cp["next_macro"]==q[num],"receipt chain")
        source=(L,tuple("Response" for _ in L),((1,len(L),sp["draft_blob"]),),ph)
        mm=validate_receipt(r,m,source,c["project"],ARCHIVE,previous_ids=ids,expected_range=[1,m["end"]])
        require(mm["records"]==g["records"] and mm["lines"]==g["lines"] and mm["axes_represented"]==g["axes"],"metrics")
        for x in r["records"]:
            e=x["evidence"];require(x["book"]=="VI" and prev_day<=x["day"]<=head["day"] and not x["promotion"] and e["source_kind"]=="CLOSED_PROSE" and e["archive_closure_blob"]==sp["closure_blob"] and e["full_story_sha256"]==sp["full_story_sha256"] and e["immutable_manifest_blob"]==sp["immutable_manifest_blob"],"authority")
            if x["type"] in ("reader_scene","knowledge"):require(x["visibility"].startswith("READER_ONLY" if x["type"]=="reader_scene" else "RESTRICTED"),"perspective")
        recs+=mm["records"];lines+=mm["lines"];original_events+=len(closure["events"]);original_knowledge+=len(closure["knowledge"]);ids.update(x["id"] for x in r["records"]);axes.update(mm["axes_represented"])
        require(cp["next_line"]==1 and cp["next_source"]==q[num]["source"] and cp["staging_records"]==4732+recs and cp["official_records"]==1656 and cp["book_counts"]["V"]==1380 and cp["book_counts"]["VI"]==457+recs and cp["completed_macros"]==num and cp["book_v_closed"] and cp["book_vi_started"],"checkpoint")
        metrics.append(dict(mm,macro=num,source=name,original_events=len(closure["events"]),original_knowledge=len(closure["knowledge"]),sequence=closure["sequence"],full_sha256=sp["full_story_sha256"],prose_sha256=ph,chosen_option=sp["chosen_option"]))
        prev=g["checkpoint_blob"];prev_episode=name;prev_day=head["day"];prev_clock=head["hour"]
    for e in audit["findings"]:
        lo,hi=e["range"];require(not e["promotion"] and sha256("\n".join(sources[e["source"]][lo-1:hi]).encode()).hexdigest()==e["sha256"],"literal regression")




    A,B,C,D,E=[sources[x["source"]] for x in q[100:105]]
    def has(L,*terms):
        s="\n".join(L)
        return all(x in s for x in terms)
    require(has(A,"Naeryn","Cântico do Equinócio") and has(B,"Níraven","alma") and has(C,"Virandor","AERÚN"),"chapter identities")
    require(has(D,"Não era a Conferência Continental.","**Lucas não sabia.**","Às 21h04, a reunião terminou."),"D567 preparation and POV")
    require(has(E,"o resultado é reproduzível","Ainda não sabemos quem colocou aquele componente ali. Nem quando.","A sétima posição não apresentava resposta semelhante.","Não posso afirmar que esteja relacionado."),"D568 bounded technical finding")
    require(has(E,"PONTE DOS QUE VOLTAM.","a passagem para pedestres recebera autorização.","O uso regular de cargas maiores continuaria sujeito","Recompensa: você chegou a tempo de ouvir um povo cantar."),"D568 physical bridge and metaphor")
    require(has(E,"Lucas Rodrigues não sabia o que Velkar fizera.","Velkar Draen não sabia que Lucas acabara de devolver","Vou apresentar as necessidades civis.","Não era a frota inteira autorizada por Velkar.","FIM DO CAPÍTULO 6"),"D568 POV and authority")
    x=read(root,audit["r2_next_authority_path"],audit["r2_next_authority_blob"])
    require(x==audit["r2_next_authority"] and audit["r2_next_authority_blob"]=="5e5344bbf34842c8fd45a11a44abfce8ce92f0c0","next authority receipt")
    pins=x["pins"];r2=x["episode"];r1=x["rejected_episode"]
    reject=read(archive,"editorial/rejections/"+r1+".json",pins["rejection"])
    rev=read(archive,"editorial/revisions/"+r1+"/R2/revision_manifest.json",pins["revision_manifest"])
    choice=read(archive,"choices/"+r2+"/option-4.json",pins["choice"])
    reader=read(archive,"delivery/reader_receipts/"+r2+".json",pins["reader_receipt"])
    proof=read(archive,"episodes/"+r2+"/draft/source_proof.json",pins["source_proof"])
    imm=read(archive,"episodes/"+r2+"/draft/manifesto_imutavel.json",pins["immutable_manifest"])
    rejected_imm=read(archive,"episodes/"+r1+"/draft/manifesto_imutavel.json",pins["rejected_manifest"])
    nextcl=read(archive,"canon/episodes/"+r2+".json",x["closure_blob"])
    require(q[105]["source"]==r2 and q[105]["lines"]==2740 and nextcl["sequence"]==40 and nextcl["previous_episode_id"]==prev_episode and nextcl["story_sha256"]==x["story_sha256"]==imm["original_readback_sha256"]==reader["story_sha256"]==proof["source_sha256"] and nextcl["chosen_option"]==choice["option"]==4 and sha256(canonical(choice)).hexdigest()==nextcl["choice_sha256"]==x["choice_sha256"],"next R2 closure authority")
    require(reject["do_not_promote"] and reject["do_not_reuse_as_opening"] and reject["original_narrative_sha256"]==rejected_imm["original_readback_sha256"]==x["rejected_story_sha256"]!=x["story_sha256"] and rev["replacement_id"]==r2 and rev["replacement_sha256"]==x["story_sha256"] and rev["not_yet_canon"] is True and not (archive/"canon"/"episodes"/(r1+".json")).exists(),"R1 exclusion; editorial manifest is earlier snapshot")
    orig=(archive/proof["source_file"]).read_bytes();narr=(archive/"episodes"/r2/"draft"/"narrativa_integral.md").read_bytes()
    require(orig==narr and sha256(orig).hexdigest()==x["story_sha256"] and len(orig)==proof["source_bytes"] and proof["ui_parity"]=="NOT_INDEPENDENTLY_VERIFIED" and x["scope"]=="AUTHORITY_PREFLIGHT_ONLY_NO_0106_RECEIPT_OR_SEMANTIC_RECOVERY" and not x["macro_0106_recovered"],"R2 hash-only custody")
    require(not list((root/ROOT).glob("partial-macro-0106-*.json")),"no next recovery")
    t=audit["totals"];require(recs==72 and lines==13709 and t["session_lines"]==lines and t["session_records"]==recs and t["staging_records"]==4732+recs and t["book_v_records"]==1380 and t["book_v_lines"]==232445 and t["book_vi_records"]==457+recs and t["book_vi_lines"]==52120+lines and t["original_events"]==original_events==60 and t["original_knowledge"]==original_knowledge==275 and sorted(axes)==audit["axis_coverage"]["represented"] and set(audit["axis_coverage"]["assessed"])==set(range(1,31)),"cycle totals")
    require(audit["production_gate"]=="HOLD" and all(not x["promotion"] for x in audit["overlays"]) and not any(audit[k] for k in ("canon_changed","official_checkpoint_changed","semantic_certification","independent_review","promotion")),"gate")
    return {"status":"PASS_NATIVE_BOOK_VI_0105_CYCLE_COMPLETE","cycle_status":"PASS_STAGING_ONLY","macros":metrics,"session_lines":lines,"session_records":recs,"session_axes":sorted(axes),"staging_records":4732+recs,"book_v_records":1380,"book_v_lines":232445,"book_vi_records":457+recs,"book_vi_lines":52120+lines,"original_events":original_events,"original_knowledge":original_knowledge,"journal_prefix_verified":39,"prior_exact_multiday_exception_preserved":True,"d567_parallel_same_day_verified":True,"r2_next_authority_verified":True,"macro_0106_recovered":False,"r1_excluded":True,"next_source":q[105]["source"],"next_line":1,"production_gate":"HOLD","canon_changed":False,"semantic_certification":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_book_vi_105(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
