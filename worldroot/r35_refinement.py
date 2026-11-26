"""R35 literary refinement; contextual editorial evidence, not artistic certification."""
from __future__ import annotations
import re
from collections import Counter
from .r34_experience import require,reason

AXES=("cadence","voice_identity","emotion_adult","wonder_payoff","exposition")
BASELINE_PARAGRAPHS_PER_1000=113.08
PILOT_PARAGRAPHS_PER_1000=93.17

def rhythm_signals(prose):
    from .r35_longform import scene_texts,clean_scene,WORD,SPEAKER,metrics
    scenes=scene_texts(prose);m=metrics(prose)
    lengths=[len(WORD.findall(p)) for s in scenes.values() for p in clean_scene(s)]
    total=max(len(lengths),1)
    voices=Counter()
    for s in scenes.values():
        for line in s.splitlines():
            a=SPEAKER.match(line)
            if a:voices[a.group().replace("*","").strip(" —–-")]+=1
    density=m["paragraphs_per_1000"]
    return {"paragraphs_per_1000":density,"historical_reference":BASELINE_PARAGRAPHS_PER_1000,
            "pilot_reference":PILOT_PARAGRAPHS_PER_1000,
            "dense_paragraph_share":round(sum(n>=35 for n in lengths)/total,4),
            "very_short_paragraph_share":round(sum(n<=3 for n in lengths)/total,4),
            "dialogue_turns":sum(voices.values()),"named_voices":len(voices),
            "cadence_review_signal":"REVIEW_COMPRESSION" if density<100 else "CONTEXTUAL_REVIEW",
            "advisory_only":True,"semantic_certification":False}

def validate_refinement_plan(request):
    plan=request["r35_plan"];data=plan.get("refinement")
    require(isinstance(data,dict) and data.get("schema")=="worldroot-r35-refinement-v1","R35 refinement plan missing")
    axes=data.get("axes");require(isinstance(axes,dict) and set(axes)==set(AXES),"R35 review all five refinement axes")
    scene_ids={x["scene"] for x in request["scene_plan"]};refs=set(plan["references"])
    aims=set()
    for k,d in axes.items():
        require(isinstance(d,dict) and reason(d.get("aim")) and d["aim"] not in aims,"R35 distinct editorial aim: "+k)
        aims.add(d["aim"])
        require(d.get("reference_id") in refs,"R35 refinement needs historical reference: "+k)
        sc=d.get("scenes")
        require(isinstance(sc,list) and bool(sc) and len(set(sc))==len(sc) and all(type(n) is int and n in scene_ids for n in sc),"R35 refinement scene mapping: "+k)
    cards=request["r34_intent"].get("characters",[])
    roster=data.get("identity_recovery")
    require(isinstance(roster,list) and {c["name"] for c in cards}=={x.get("character") for x in roster} and len(roster)==len(cards),"R35 focal identity recovery must cover R34 roster")
    for c in roster:
        require(reason(c.get("source_review")) and reason(c.get("voice_direction")) and reason(c.get("trait_gaps")),"R35 identity recovery must distinguish evidence and gaps")
    return {"axes":len(AXES),"identity_cards":len(roster),"semantic_certification":False}

def validate_refinement_review(request,payload):
    from .r35_longform import scene_texts,WORD
    plan=request["r35_plan"]["refinement"];review=payload["r35_review"].get("refinement")
    require(isinstance(review,dict) and review.get("schema")=="worldroot-r35-refinement-review-v1","R35 refinement review missing")
    axes=review.get("axes")
    require(isinstance(axes,dict) and set(axes)==set(AXES),"R35 five-axis refinement review incomplete")
    actual=scene_texts(payload["prose"]);signals=rhythm_signals(payload["prose"]);notes=set()
    for k,v in axes.items():
        target=plan["axes"][k]
        require(isinstance(v,dict) and v.get("reference_id")==target["reference_id"] and v.get("result") in ("revised","retained","contextual_difference"),"R35 unresolved refinement: "+k)
        require(reason(v.get("assessment")) and reason(v.get("contrast")) and v["assessment"] not in notes,"R35 specific comparative review: "+k)
        notes.add(v["assessment"])
        moments=v.get("moments")
        require(isinstance(moments,list) and len(moments)>=2,"R35 refinement needs two distinct narrative moments: "+k)
        seen=[]
        for m in moments:
            n=m.get("scene");e=m.get("evidence")
            require(type(n) is int and n in actual and (n in target["scenes"] or reason(v.get("changed_context"))) and isinstance(e,str) and len(WORD.findall(e))>=4 and e in actual[n] and reason(m.get("effect")),"R35 refinement evidence not grounded in scene: "+k)
            require(all(e not in a and a not in e for a in seen),"R35 refinement repeats one moment: "+k);seen.append(e)
        if k=="cadence" and signals["cadence_review_signal"]=="REVIEW_COMPRESSION":
            require(reason(v.get("density_response")),"R35 review measured cadence gap rather than silently accept compression")
    require(review.get("no_artificial_fragmentation") is True and review.get("no_administrative_padding") is True and review.get("no_forced_conflict_or_romance") is True,"R35 literary boundaries not reviewed")
    return {"schema":"worldroot-r35-refinement-receipt-v1","signals":signals,"axes":axes,"semantic_certification":False,"canon_changed":False}
