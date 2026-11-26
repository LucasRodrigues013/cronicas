"""R35: hard production regression gate, not a literary grading model.
Versioned and additive. Historic episodes are measured read-only, never rejected.
"""
from __future__ import annotations
import re,unicodedata
from collections import Counter
from pathlib import Path
from .r34_experience import require,reason
from .longform_segments import verify_longform_segments

HEADING=re.compile(r"(?m)^\s*(?:#{1,6}\s+)?(?:\*\*)?([IVX]{1,8})\s+[—–-]\s+\S[^\n]*$")
END=re.compile(r"(?mi)^\s*(?:#{1,6}\s+)?(?:\*\*)?(?:FIM (?:DA PARTE|DO CAP[IÍ]TULO)|ENCERRAMENTO DA PARTE|WORLDROOT\s*[·—-]\s*CHECKPOINT|AS CINCO PORTAS|OPÇÕES DE CONTINUAÇÃO)\b")
WORD=re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*",re.UNICODE)
SPEAKER=re.compile(r"^\s*(?:\*\*)?[A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]{1,36}\s+[—–-](?:\*\*)?\s+")
CLOCK=re.compile(r"^\s*(?:\*\*)?DIA\s+\d+",re.I)
FOCUS=("daily_life","appearance","relationships","cast","wonder","rhythm")
COMPARE=("cadence","emotion","adventure","character","design")
PROFILES={"regular":(8800,9000,11000),"special":(9500,10000,13000),"finale":(11000,12000,15000)}
EXCEPTION=re.compile(r"(?im)^AUTORIZO PARTE CURTA:\s*(\S[^\n]+)$")
def profile(part,option):
    require(part in ("I","II","III","IV","V") and type(option) is int and 1<=option<=5,"R35 invalid part/choice")
    return "finale" if part=="V" else "special" if option==4 else "regular"
def clean_scene(text):
    paragraphs=[]
    for block in re.split(r"\n\s*\n",text):
        lines=[]
        for line in block.splitlines():
            s=line.strip()
            if not s or s.startswith(("<","{@","#","|","---","***")) or CLOCK.match(s):continue
            s=SPEAKER.sub("",s).replace("*","").replace("_","").replace("`","")
            s=re.sub(r"<[^>]*>","",s).strip()
            if s and WORD.search(s):lines.append(s)
        if lines:paragraphs.append("\n".join(lines))
    return paragraphs
def scene_texts(prose):
    h=list(HEADING.finditer(prose));out={}
    for i,m in enumerate(h):
        chunk=prose[m.end():h[i+1].start() if i+1<len(h) else len(prose)]
        end=END.search(chunk)
        if end:chunk=chunk[:end.start()]
        out[i+1]=chunk
    return out
def metrics(prose):
    require(isinstance(prose,str) and bool(prose.strip()),"R35 literal prose required")
    scenes=scene_texts(prose)
    paras=[p for s in scenes.values() for p in clean_scene(s)]
    wc=[len(WORD.findall(p)) for p in paras];total=sum(wc)
    normalized=[" ".join(WORD.findall(unicodedata.normalize("NFKC",p).casefold())) for p in paras]
    duplicates=Counter(p for p,n in zip(normalized,wc) if n>=12)
    duplicate_words=sum((n-1)*len(WORD.findall(p)) for p,n in duplicates.items() if n>1)
    # Also catch repeated short sentence padding; exclude isolated small callbacks.
    repeats=Counter(p for p,n in zip(normalized,wc) if 3<=n<12)
    repeated_short=sum((n-3)*len(WORD.findall(p)) for p,n in repeats.items() if n>3)
    duplicate_words+=repeated_short
    sentence_units=sum(len([x for x in re.split(r"(?<=[.!?…])\s+|\n+",p) if WORD.search(x)]) for p in paras)
    return {"words":total,"paragraphs":len(paras),"sentence_units_approx":sentence_units,"scenes":len(scenes),
            "words_per_paragraph":round(total/max(1,len(paras)),2),"paragraphs_per_1000":round(1000*len(paras)/max(1,total),2),
            "duplicate_word_share":round(duplicate_words/max(1,total),4),
            "scene_words":{str(i):sum(len(WORD.findall(p)) for p in clean_scene(s)) for i,s in scenes.items()}}
def volume_check(prose,part,option,author_text=""):
    mode=profile(part,option);floor,low,high=PROFILES[mode];m=metrics(prose)
    exception=EXCEPTION.search(author_text or "")
    allowed=bool(exception and reason(exception.group(1)))
    issues=[]
    if m["words"]<floor and not allowed:issues.append("R35_DEPTH: expand lived scenes to "+str(floor)+" real prose words; no filler")
    if m["duplicate_word_share"]>=.08:issues.append("R35_PADDING: repeated paragraphs inflate prose; revise")
    return {**m,"profile":mode,"floor":floor,"target":[low,high],"exception_authorized":allowed,"issues":issues,"status":"REVISE" if issues else "STRUCTURAL_VOLUME_OK","semantic_certification":False}
def validate_plan(request,choice):
    plan=request.get("r35_plan");require(isinstance(plan,dict) and plan.get("schema")=="worldroot-r35-plan-v1","R35 longform plan missing")
    part=plan.get("part");mode=profile(part,choice["option"])
    # Delivery ID uses exact episode part; no profile downgrade.
    match=re.search(r"-P(I{1,3}|IV|V)-D",request["delivery_id"])
    require(match and match.group(1)==part,"R35 part inconsistent with delivery")
    require(plan.get("profile")==mode,"R35 profile must match author choice/part")
    floor,low,high=PROFILES[mode]
    cards=plan.get("scene_cards");scenes=request["scene_plan"]
    require(isinstance(cards,list) and len(cards)==len(scenes),"R35 plan every scene")
    total=0;focus_map={k:set() for k in FOCUS}
    for c,s in zip(cards,scenes):
        require(isinstance(c,dict) and c.get("scene")==s["scene"],"R35 scene plan order")
        n=c.get("word_budget");require(type(n) is int and n>0,"R35 positive scene budget")
        total+=n
        require(all(reason(c.get(k)) for k in ("experience","reaction","payoff")),"R35 scene needs experience, reaction and payoff")
        focus=c.get("focus");require(isinstance(focus,list) and len(set(focus))==len(focus) and set(focus)<=set(FOCUS),"R35 invalid focus")
        for k in focus:focus_map[k].add(c["scene"])
    authorized=EXCEPTION.search(choice.get("free_text","") or "")
    require(total>=floor or (authorized and reason(authorized.group(1))),"R35 planned word budget below profile floor")
    for k in FOCUS:
        d=request["r34_intent"]["dimensions"][k]
        require(set(d["scenes"])<=focus_map[k],"R35 lost R34 planned opportunity: "+k)
    refs=plan.get("references");req={r["id"]:r for r in request["requirements"]}
    require(isinstance(refs,list) and len(refs)>=2 and len(set(refs))==len(refs) and all(i in req and req[i].get("role","Response")=="Response" and i in request["reviewed"] for i in refs),"R35 compare two distinct evidence-backed narrative references")
    require(reason(plan.get("cadence_intent")) and reason(plan.get("adult_opportunity")) and reason(plan.get("epic_payoff")),"R35 editorial opportunities not articulated")
    return {"profile":mode,"planned_words":total,"floor":floor,"target":[low,high],"scene_count":len(cards),"semantic_certification":False}
def validate_delivery(root,request,payload,choice):
    review=payload.get("r35_review");require(isinstance(review,dict) and review.get("schema")=="worldroot-r35-review-v1","R35 release review missing")
    plan=request["r35_plan"];meta=payload["metadata"]
    require(meta["part"]==plan["part"],"R35 mismatched part")
    result=volume_check(payload["prose"],meta["part"],choice["option"],choice.get("free_text",""))
    require(not result["issues"],"; ".join(result["issues"]))
    stage=verify_longform_segments(Path(root),payload["delivery_id"],payload)
    require(stage["verified"],"R35 requires 2–6 exact final segment receipts")
    actual=scene_texts(payload["prose"]);rows=review.get("scenes")
    require(isinstance(rows,list) and len(rows)==len(actual),"R35 review every lived scene")
    require(len(actual)==len(plan["scene_cards"]) or reason(review.get("scene_plan_change")),"R35 explain organic scene change")
    planned={c["scene"]:c for c in plan["scene_cards"]};covered=set()
    for i,row in enumerate(rows,1):
        require(isinstance(row,dict) and row.get("scene")==i and row.get("planned_scene") in planned,"R35 review scene mapping")
        covered.add(row["planned_scene"])
        anchors=row.get("beats")
        require(isinstance(anchors,dict) and set(anchors)=={"experience","reaction","payoff"},"R35 lived scene beats missing")
        values=list(anchors.values())
        require(all(isinstance(x,str) and len(WORD.findall(x))>=4 and x in actual[i] for x in values) and len(set(values))==3,"R35 distinct literal scene beats missing")
        require(all(not (a in b or b in a) for k,a in enumerate(values) for b in values[k+1:]),"R35 overlapping scene evidence")
        require(reason(row.get("assessment")),"R35 scene assessment missing")
    if covered!=set(planned):require(reason(review.get("scene_plan_change")),"R35 missing planned scenes")
    opportunities=review.get("opportunities")
    require(isinstance(opportunities,dict) and set(opportunities)==set(FOCUS),"R35 opportunity review incomplete")
    for k,v in opportunities.items():
        old=payload["r34_review"]["dimensions"][k]
        require(isinstance(v,dict) and v.get("status")==old["status"] and reason(v.get("assessment")),"R35 opportunity status mismatch: "+k)
        if v["status"]=="applied":
            proof=v.get("moments")
            require(isinstance(proof,list) and len(proof)>=2,"R35 more than one moment required: "+k)
            literals=[]
            for m in proof:
                require(isinstance(m,dict) and type(m.get("scene")) is int and m["scene"] in actual and isinstance(m.get("evidence"),str) and len(WORD.findall(m["evidence"]))>=4 and m["evidence"] in actual[m["scene"]] and reason(m.get("effect")),"R35 missing opportunity moment: "+k)
                literals.append(m["evidence"])
            require(len(set(literals))==len(literals) and all(not (a in b or b in a) for i,a in enumerate(literals) for b in literals[i+1:]),"R35 repeated opportunity evidence: "+k)
        else:require(not v.get("moments") and reason(v.get("context")),"R35 justified natural deferral required")
    comparison=review.get("comparison")
    require(isinstance(comparison,dict) and set(comparison)==set(COMPARE),"R35 review comparative dimensions")
    for k,v in comparison.items():
        require(isinstance(v,dict) and v.get("reference_id") in plan["references"] and reason(v.get("assessment")) and v.get("result") in ("retained","improved","contextual_difference"),"R35 unresolved comparative regression: "+k)
    require(review.get("no_padding") is True and review.get("no_condensed_key_events") is True,"R35 review depth and repetition")
    return {"schema":"worldroot-r35-longform-receipt-v1","volume":result,"segments":stage,"scene_reviews":len(rows),"opportunities":opportunities,"comparison":comparison,"semantic_certification":False,"canon_changed":False}
