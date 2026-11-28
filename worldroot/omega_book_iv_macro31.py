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

def main():
    p=argparse.ArgumentParser();p.add_argument("--engine-root",default=".");p.add_argument("--archive-root",required=True)
    a=p.parse_args();print(json.dumps(verify_book_v_67(a.engine_root,a.archive_root),sort_keys=True))
if __name__=="__main__":main()
