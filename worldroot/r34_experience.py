"""R34 author-intent coverage: structural evidence, not automatic literary judgment.

An explicit, independent ledger makes omitted author priorities observable. No
word quotas, forced scenes, invented identity or retroactive changes.
"""
from __future__ import annotations
import re,json
from .editorial_guard import POLICY_PATH
from .presentation_guard import SCENE,presentation_preflight
from .literary_experience import measure

DIMENSIONS={"daily_life":"P110","appearance":"P111","relationships":"P112",
            "cast":"P113","wonder":"P114","rhythm":"P115","design":"P119"}
FIELDS=("appearance","voice","relationship","age")
DOMAINS={"appearance":"identity","voice":"identity","relationship":"relationship","age":"identity"}

def require(condition,message):
    if not condition:raise ValueError(message)

def reason(value):
    return isinstance(value,str) and len(value.split())>=5

def policy_anchor(rule,ref,policy_text):
    if not isinstance(ref,dict) or ref.get("source")!="AUTHOR_POLICY":return False
    lo,hi=ref.get("line_start"),ref.get("line_end")
    lines=policy_text.splitlines()
    if type(lo) is not int or type(hi) is not int or not 1<=lo<=hi<=len(lines):return False
    span="\n".join(lines[lo-1:hi])
    return bool(re.search(r'"id"\s*:\s*"'+re.escape(rule)+r'"',span) and '"directive"' in span)

def validate_intent(request,policy_text=None):
    """Independent author policy dimensions must be bound to distinct requirements.
    Human authoring still determines relevance, meaning and factual support."""
    policy_text=POLICY_PATH.read_text(encoding="utf-8") if policy_text is None else policy_text
    policy=json.loads(policy_text)
    active={x["id"] for x in policy["rules"] if x.get("active")}
    require(set(DIMENSIONS.values())<=active,"R34 active policy incomplete")
    intent=request.get("r34_intent")
    require(isinstance(intent,dict) and intent.get("schema")=="worldroot-r34-intent-v1","R34 intent missing")
    dims=intent.get("dimensions")
    require(isinstance(dims,dict) and set(dims)==set(DIMENSIONS),"R34 review all independent intent dimensions")
    req={x["id"]:x for x in request["requirements"]}
    reviewed=request["reviewed"]
    scenes={x["scene"]:set(x["ids"]) for x in request["scene_plan"]}
    used=set()
    for name,rule in DIMENSIONS.items():
        d=dims[name]
        require(isinstance(d,dict) and d.get("rule")==rule and d.get("status") in ("planned","held") and reason(d.get("reason")),"R34 invalid intent: "+name)
        rid=d.get("requirement_id")
        r=req.get(rid,{})
        require(rid not in used and r.get("domain")=="author_rule" and r.get("role")=="AuthorPolicy" and r.get("critical") is True and policy_anchor(rule,reviewed.get(rid),policy_text),"R34 missing distinct policy evidence: "+name)
        used.add(rid)
        planned=d.get("scenes")
        require(isinstance(planned,list) and all(type(i) is int and i in scenes and rid in scenes[i] for i in planned) and len(set(planned))==len(planned),"R34 invalid scene mapping: "+name)
        require((d["status"]=="planned")==bool(planned),"R34 planned/held mismatch: "+name)
        if name=="design":require(d["status"]=="planned","R34 presentation always reviewed")
    cards=intent.get("characters")
    require(isinstance(cards,list) and len(cards)<=40,"R34 focal character cards required")
    seen=set()
    for c in cards:
        require(isinstance(c,dict) and isinstance(c.get("name"),str) and c["name"].strip() and c["name"].casefold() not in seen,"R34 invalid character")
        seen.add(c["name"].casefold())
        sc=c.get("scenes")
        require(isinstance(sc,list) and bool(sc) and all(type(i) is int and i in scenes for i in sc),"R34 invalid character scene")
        fields=c.get("fields")
        require(isinstance(fields,dict) and set(fields)==set(FIELDS),"R34 review appearance, voice, relationship and age")
        for field,v in fields.items():
            require(isinstance(v,dict) and v.get("status") in ("sourced","unknown","not_material") and reason(v.get("reason")),"R34 character field missing")
            if v["status"]=="sourced":
                ids=v.get("requirement_ids")
                require(isinstance(ids,list) and bool(ids) and all(req.get(i,{}).get("domain")==DOMAINS[field] and req.get(i,{}).get("role","Response")=="Response" and i in reviewed and any(i in scenes[n] for n in sc) for i in ids),"R34 character source not mapped")
            else:require(not v.get("requirement_ids"),"R34 unresolved field cannot claim sources")
    if dims["appearance"]["status"]=="planned":require(bool(cards),"R34 appearance needs focal character cards")
    reference=intent.get("comparison")
    require(isinstance(reference,dict) and reference.get("requirement_id") in req and req[reference["requirement_id"]].get("role","Response")=="Response" and reference["requirement_id"] in reviewed and reason(reference.get("reason")),"R34 historical comparison source required")
    return {"dimensions":len(dims),"characters":len(cards),"status":"INTENT_STRUCTURE_CHECKED","semantic_certification":False}

def render_opening(metadata,packet):
    """A versioned, deterministic, prose-first visual opening for new episodes."""
    from .experience_quality import safe
    require(isinstance(packet,dict),"R34 opening packet missing")
    fields=("book_title","chapter_title","episode_title","epigraph","calendar","location","fronts")
    require(set(packet)==set(fields),"R34 opening fields incomplete")
    p={k:safe(packet[k]) for k in fields}
    part=metadata.get("part");chapter=metadata.get("chapter");day=metadata.get("day")
    version=35 if metadata.get("worldroot_revision")==35 else 34
    parts=("I","II","III","IV","V")
    require(part in parts and type(chapter) is int and chapter>0 and type(day) is int and day>0,"R34 invalid episode metadata")
    require(p["book_title"].casefold().startswith(str(metadata.get("book","")).casefold()+" — "),"R34 book title mismatch")
    require(bool(re.match(r"^Dia "+str(day)+r"(?:\s*·|$)",p["calendar"],re.I)),"R34 calendar day mismatch")
    index=parts.index(part)
    progress="".join('    <box flex={1} height={5} radius="full" background="'+("#64748B" if n<=index else "surface-tertiary")+'"/>\n' for n in range(5)).rstrip()
    return "\n".join([
        '<box align="center" gap={2}>',
        '  <caption>CRÔNICAS DE UM NOVO MUNDO · WORLDROOT R'+str(version)+'</caption>',
        '  <title size="lg" textAlign="center">'+p["book_title"]+'</title>',
        '  <title size="lg" textAlign="center">CAPÍTULO '+str(chapter)+' — '+p["chapter_title"]+'</title>',
        '  <caption>PARTE '+part+' DE V · DIA '+str(day)+'</caption>',
        '  <title size="xl" textAlign="center">'+p["episode_title"]+'</title>',
        '  <text italic textAlign="center" color="secondary">'+p["epigraph"]+'</text>',
        '</box>',
        '<box border radius="lg" padding={3} gap={2}>',
        '  <caption>CALENDÁRIO DO HORIZONTE</caption>',
        '  <row gap={1}>',progress,'  </row>',
        '  <grid columns={2} gap={2}>',
        '    <grid-item><caption>Calendário</caption>**'+p["calendar"]+'**</grid-item>',
        '    <grid-item><caption>Progresso do capítulo</caption>**Parte '+part+' de V**</grid-item>',
        '    <grid-item><caption>Local inicial</caption>**'+p["location"]+'**</grid-item>',
        '    <grid-item><caption>Horizontes da parte</caption>'+p["fronts"]+'</grid-item>',
        '  </grid>',
        '</box>'])
 
def identity_context(root,character_ids,head=None):
    """Read-only merge of R30 source-matched observations and R31 literal candidates.
    Keep source candidates separate; do not assert current traits or age."""
    from pathlib import Path
    from .literary_experience import source_registry,_historical_anchor
    from .history_index import read_verified_sources
    root=Path(root)
    reg=source_registry(root,head)
    _,raw=read_verified_sources(root)
    sources={m["source_name"]:(m,t) for m,t in raw}
    candidates=json.loads((Path(__file__).resolve().parent.parent/"recovery/r31-historical-candidates.json").read_text(encoding="utf-8"))
    result=[]
    people={p["id"]:p for p in reg["characters"]}
    for ident in dict.fromkeys(character_ids):
        rows=[]
        for c in candidates["records"]:
            if c.get("entity")!=ident or c.get("role")!="Response" or c.get("field") not in ("appearance","relationship"):continue
            proof=_historical_anchor(sources,c)
            rows.append({"field":c["field"],"claim":c["claim"],"proof":proof,"state":"LITERAL_CANDIDATE_NOT_CANON" if proof else "UNVERIFIED"})
        old=people.get(ident)
        obs=old["observations"] if old else []
        result.append({"id":ident,"observations":obs,"candidates":rows,
                       "missing_fields":[field for field in FIELDS if not any(o.get("proof") and o["field"]==field for o in obs) and not any(o["proof"] and o["field"]==field for o in rows)],
                       "current_state_verified":False})
    return {"head":reg["head"],"characters":result,"status":"REVIEW_CURRENT_STATE_AND_CONFLICTS","semantic_certification":False,"canon_changed":False}
 
def scene_bodies(prose):
    matches=list(SCENE.finditer(prose))
    return {i+1:prose[m.start():matches[i+1].start() if i+1<len(matches) else len(prose)] for i,m in enumerate(matches)}

def validate_delivery(request,payload):
    intent=request["r34_intent"];review=payload.get("r34_review")
    require(isinstance(review,dict) and review.get("schema")=="worldroot-r34-review-v1","R34 review required")
    actual=scene_bodies(payload["prose"])
    dims=review.get("dimensions")
    require(isinstance(dims,dict) and set(dims)==set(DIMENSIONS),"R34 delivery dimensions incomplete")
    anchors={}
    for name,d in dims.items():
        plan=intent["dimensions"][name]
        require(isinstance(d,dict) and d.get("status") in ("applied","held") and reason(d.get("reason")),"R34 invalid delivery review: "+name)
        if d["status"]=="held":
            require(name!="design" and not d.get("evidence"),"R34 design or evidence cannot be held")
            if plan["status"]=="planned":require(reason(d.get("changed_context")),"R34 missed planned opportunity: "+name)
            continue
        require(plan["status"]=="planned" or reason(d.get("changed_context")),"R34 unplanned application needs context")
        evidence=d.get("evidence")
        require(isinstance(evidence,str) and len(evidence.split())>=4,"R34 literal evidence required: "+name)
        if name=="design":
            require(evidence in payload["full_text"] and ("WORLDROOT R35" if payload.get("metadata",{}).get("worldroot_revision")==35 else "WORLDROOT R34") in payload["full_text"][:2000],"R34/R35 design/header mismatch")
            opening=render_opening(payload.get("metadata",{}),review.get("opening"))
            require(opening in payload["full_text"][:len(opening)+400],"R34 rendered opening differs")
            check=presentation_preflight(payload["full_text"],min_scenes=1,min_named_turns=0)
            require(not check["errors"],"R34 visual structural regression")
        else:
            n=d.get("scene")
            require(type(n) is int and n in actual and evidence in actual[n],"R34 evidence not in declared scene: "+name)
            if n not in plan["scenes"]:require(reason(d.get("changed_context")),"R34 scene shift needs context")
        anchors[name]=evidence
    if "appearance" in anchors and "relationships" in anchors:
        require(anchors["appearance"]!=anchors["relationships"],"R34 physical identity cannot reuse relationship evidence")
    if "appearance" in anchors:
        a=dims["appearance"];detail=a.get("concrete_detail")
        require(isinstance(detail,str) and len(detail.strip())>=3 and detail in anchors["appearance"],"R34 concrete physical/visual detail absent")
        name=a.get("character")
        require(any(c["name"]==name and a["scene"] in c["scenes"] for c in intent["characters"]),"R34 appearance not linked to character")
    require(reason(review.get("comparison_result")),"R34 comparison requires editorial conclusion")
    require(review.get("no_forced_scenes") is True and review.get("no_unsupported_traits") is True,"R34 editorial boundary not reviewed")
    return {"schema":"worldroot-r34-intent-receipt-v1","dimensions":dims,"character_count":len(intent["characters"]),"comparison_result":review["comparison_result"],"signals":measure(payload["prose"]),"status":"EVIDENCE_STRUCTURE_CHECKED_HUMAN_REVIEW_REQUIRED","semantic_certification":False,"canon_changed":False}

if __name__=="__main__":
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path,required=True);p.add_argument("--character",action="append",required=True)
    args=p.parse_args();print(json.dumps(identity_context(args.archive_root,args.character),ensure_ascii=False,indent=2))
