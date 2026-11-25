"""R30: literary experience, provenance and choice-version checks.
Consultative indicators; no automatic quality grade, invented facts or canon writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from .living_world import literal_body, normalize, read_obj
from .history_index import read_verified_sources
from .epic_narrative import _literal_evidence

REGISTRY = "editorial/registries/r30-character-identity.json"
CORPUS = "editorial/registries/r30-literary-corpus.json"
VERSION = 30
WORDS = re.compile(r"[^\W_]+", re.UNICODE)
META = re.compile(r"\b(?:não (?:era|é|seria|significava|significa|constituía) (?:uma? )?(?:prova|aliança|conquista definitiva|autorização|confirmação)|não (?:havia|existia) (?:evidência|conhecimento suficiente)|não (?:dependia|precisava) da autorização|não (?:era|foi) (?:canonizado|canônico)|autorização do autor|conveniência narrativa|fonte literal|estado canônico|escolha autoral|sem (?:promover|canonizar|inventar (?:capacidade|alcance|localização|autoria|resultado|números))|(?:após|depois de) (?:recuperação prévia|confirmar (?:a )?última localização)|trajetória hipotética|sessão (?:de ensino )?compatível com (?:a )?presença|em (?:um )?intervalo narrado|(?:não|nem) (?:declarou|declarava) (?:a )?(?:costa|terra|cidade|região) conquistada|sem atribuir autoria|certeza fabricada|não era uma missão de Lucas|não era um relatório|não era carta náutica confirmada|(?:a )?recompensa daquele capítulo)\b", re.I)
SENSES = {
    "olfato": r"\b(?:cheir\w*|aroma\w*|perfume\w*|odor\w*|fragrância\w*)\b",
    "som": r"\b(?:sussurr\w*|rang\w*|estrond\w*|eco\w*|silêncio|voz\w*|murmur\w*|resso\w*)\b",
    "toque_temperatura": r"\b(?:frio|quente|calor|gelad\w*|ásper\w*|macio|suave|textura|arrepio|pele)\b",
    "visao": r"\b(?:cabel\w*|olhos|rosto|feições|sombra\w*|brilh\w*|cor\w*|luz\w*)\b",
    "paladar": r"\b(?:sabor\w*|amargo|doce|salgad\w*|azed\w*|paladar)\b",
}
EMOTION = {
    "alegria": r"\b(?:ris\w*|gargalh\w*|sorri\w*|alegr\w*)\b",
    "tensao": r"\b(?:ameaç\w*|medo|temor|trem\w*|perigo|ferid\w*)\b",
    "assombro": r"\b(?:espant\w*|maravilh\w*|assombr\w*|impossível|surpres\w*)\b",
    "afeto": r"\b(?:beij\w*|abraç\w*|saudade|desej\w*|amor|carinh\w*|intimidade)\b",
    "perda": r"\b(?:luto|chor\w*|lágrima\w*|perdeu|perda|desped\w*)\b",
}
DIALOGUE = re.compile(r"(?m)^\s*(?:\*\*)?([A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]{1,35})\s*[—–-](?:\*\*)?\s*(.+)$")
VERSION_TAG = re.compile(r"\bWORLDROOT\s+R(\d+)\b", re.I)
SPECIAL_COMBINE = re.compile(r"\b(?:combinar|combina|reúne|reunir|todas)\s+(?:as\s+)?(?:três|3|demais|outras|opções|frentes)\b",re.I)

def _prose(text: str) -> str:
    body=literal_body(text)
    # Scene headings/UI are not novel prose.
    return "\n".join(line for line in body.splitlines()
                     if not line.lstrip().startswith(("#","<","{@","|","**FIM")))

def measure(prose: str) -> dict:
    body=_prose(prose)
    words=len(WORDS.findall(body))
    lexical=lambda patterns:{k:len(re.findall(v,body,re.I)) for k,v in patterns.items()}
    voices={}
    for speaker,line in DIALOGUE.findall(body):
        key=normalize(speaker)
        voices.setdefault(key,[]).append(line.strip())
    shared={}
    for who,lines in voices.items():
        for line in lines:
            if len(WORDS.findall(line))>=4:
                shared.setdefault(normalize(line),set()).add(who)
    return {"words_approx":words,"sensory_signals":lexical(SENSES),
            "emotion_signals":lexical(EMOTION),"meta_phrases":[m.group(0) for m in META.finditer(body)][:30],
            "negations":len(re.findall(r"\b(?:não|nem|sem)\b",body,re.I)),
            "named_dialogue_turns":sum(map(len,voices.values())),
            "unattributed_turns":len(re.findall(r"(?m)^\s*—\s+\S",body)),
            "voices":{k:{"turns":len(v),"mean_words":round(sum(len(WORDS.findall(t)) for t in v)/len(v),1)}
                      for k,v in voices.items()},
            "shared_exact_dialogue":sum(len(s)>1 for s in shared.values()),
            "lucas_miren_reference":bool(re.search(r"\bLucas\b",body,re.I) and re.search(r"\bMiren\b",body,re.I)),
            "limitation":"Lexical signals only; not emotions, intimacy, character traits or aesthetic proof."}

def _historical_anchor(sources: dict, source: dict) -> dict | None:
    entry=sources.get(source.get("source_name"))
    anchor=source.get("anchor")
    if not entry or not isinstance(anchor,str) or len(anchor.strip())<12:
        return None
    meta,body=entry
    matches=[m.start() for m in re.finditer(re.escape(anchor),body)]
    if len(matches)!=1:
        return None
    pos=matches[0]
    before=body[:pos]
    roles=list(re.finditer(r"(?m)^## (Prompt|Response):\s*$",before))
    role=roles[-1].group(1) if roles else "UNMARKED"
    if role!=source.get("role","Response"):
        return None
    return {"source_name":meta["source_name"],"sha256":meta["sha256"],
            "line":before.count("\n")+1,"role":role,"status":"LITERAL_MATCH_NOT_CANON_CERTIFICATION"}

def source_registry(root: Path, head: dict | None=None) -> dict:
    live=read_obj(root/"canon/HEAD.json")
    if head is not None and live!=head:
        raise ValueError("Stale HEAD")
    _,raw=read_verified_sources(root)
    sources={m["source_name"]:(m,t) for m,t in raw}
    reg=read_obj(root/REGISTRY)
    corpus=read_obj(root/CORPUS)
    if reg.get("schema")!="worldroot-r30-identity-v1" or corpus.get("schema")!="worldroot-r30-corpus-v1":
        raise ValueError("Invalid registry/corpus")
    def anchor(s):
        if s.get("source_name"):
            return _historical_anchor(sources,s)
        return _literal_evidence(root,live,s)
    people=[]
    for p in reg["characters"]:
        confirmed=[]
        for item in p.get("observations",[]):
            proof=anchor(item["source"])
            confirmed.append({**item,"proof":proof,"state":"SOURCE_MATCH" if proof else "UNVERIFIED"})
        people.append({**p,"observations":confirmed})
    examples=[]
    for c in corpus["scenes"]:
        proof=anchor(c["source"])
        approval=anchor(c["author_feedback"]) if c.get("author_feedback") else None
        examples.append({**c,"proof":proof,"feedback_proof":approval,
                         "state":"SOURCE_MATCH" if proof else "UNVERIFIED",
                         "comparison":measure(c["source"]["anchor"]) if proof else None})
    return {"head":live,"characters":people,"scenes":examples,"canon_changed":False,
            "status":"REVIEW_REQUIRED" if any(not x["proof"] for p in people for x in p["observations"]) or any(not x["proof"] or (x.get("author_feedback") and not x["feedback_proof"]) for x in examples) else "SOURCE_MATCHES",
            "limitation":"Historical transcript observations are not universal knowledge or current state; preserve conflicts and unknowns."}

def writer_brief(root: Path, character_ids=(), scene_ids=(), head=None) -> dict:
    """Select relevant reviewed observations and literary examples; do not infer current state."""
    reg=source_registry(root,head)
    people={p["id"]:p for p in reg["characters"]}
    examples={s["id"]:s for s in reg["scenes"]}
    unknown=[f"character:{x}" for x in character_ids if x not in people]+[f"scene:{x}" for x in scene_ids if x not in examples]
    selected_people=[people[x] for x in dict.fromkeys(character_ids) if x in people]
    selected_examples=[examples[x] for x in dict.fromkeys(scene_ids) if x in examples]
    unresolved=[p["id"] for p in selected_people if any(not o["proof"] for o in p["observations"])]
    unresolved.extend(s["id"] for s in selected_examples if not s["proof"])
    return {"head":reg["head"],"status":"RECOVER_BEFORE_ASSERTING" if unknown or unresolved else "EDITORIAL_CONTEXT",
            "missing_ids":unknown,"unresolved":unresolved,"characters":selected_people,
            "examples":selected_examples,"canon_changed":False,
            "instructions":["Recover current location, knowledge, relationships and latest state separately from historical observations.",
                            "Use physical features only when sourced and relevant; clothing and mood may change.",
                            "Read examples for emotional effect, timing, sensory detail, agency and consequence, not as templates.",
                            "Resolve material ambiguity before narrating; if unresolved, preserve the unknown."],
            "limitation":"Explicit selection, not automatic relevance ranking or factual certification."}

def compare(prose: str, root: Path, scene_ids, head=None) -> dict:
    brief=writer_brief(root,(),scene_ids,head)
    return {"status":brief["status"],"head":brief["head"],"draft_metrics":measure(prose),
            "references":[{"id":s["id"],"title":s["title"],"why":s["why"],"metrics":s["comparison"],"proof":s["proof"]}
                          for s in brief["examples"]],"missing_ids":brief["missing_ids"],"unresolved":brief["unresolved"],
            "questions":["What changes for the characters through action rather than exposition?",
                         "Do sensory details matter to the viewpoint and situation?",
                         "Do voices, attraction and disagreement reflect the established relationships?",
                         "Is the emotional or epic payoff earned by preceding events?"],
            "literary_grade":None,"canon_changed":False}

EXPERIENCE_DIMENSIONS={
    "romance":("reciprocal_initiative","emotional_change","relationship_context"),
    "sensory":("viewpoint","meaningful_detail","effect_on_experience"),
    "emotion":("desire","resistance","emotional_turn","consequence"),
    "voice":("speaker","individual_intent","distinct_expression"),
    "epic":("setup","power_or_skill","witness_or_effect","lasting_consequence"),
}

def experience_cards(prose: str, root: Path, head: dict, packet=None) -> dict:
    """Optional human/editorial review, not an inferred or mandatory emotion quota."""
    if packet is None:
        return {"status":"NOT_SUPPLIED","checked":0,"issues":[]}
    if not isinstance(packet,dict) or packet.get("schema")!="worldroot-r30-experience-review-v1" or packet.get("source_episode_id")!=head.get("episode_id"):
        return {"status":"REVIEW","checked":0,"issues":["Invalid or stale review packet"]}
    cards=packet.get("cards")
    if not isinstance(cards,list) or len(cards)>100:
        return {"status":"REVIEW","checked":0,"issues":["Invalid review cards"]}
    issues=[]
    body=_prose(prose)
    for i,c in enumerate(cards,1):
        if not isinstance(c,dict) or c.get("dimension") not in EXPERIENCE_DIMENSIONS:
            issues.append(f"Card {i}: unknown dimension");continue
        dim=c["dimension"]
        anchor=c.get("draft_anchor")
        missing=[k for k in EXPERIENCE_DIMENSIONS[dim] if not isinstance(c.get(k),str) or not c[k].strip()]
        if not isinstance(anchor,str) or not 12<=len(anchor.strip())<=2000 or anchor not in body:
            missing.append("literal_draft_anchor")
        if dim=="epic" and c.get("artificial_weakening") is not False:
            missing.append("no_artificial_weakening")
        if dim=="romance" and c.get("reciprocal_agency") is not True:
            missing.append("reciprocal_agency")
        if c.get("prior_source") is not None and not _literal_evidence(root,head,c["prior_source"]):
            missing.append("verified_prior_source")
        if missing:
            issues.append(f"Card {i} ({dim}): "+", ".join(missing))
    return {"status":"REVIEW" if issues else "ANCHORS_CHECKED","checked":len(cards),"issues":issues,
            "semantic_certification":False}

def choice_prompt(episode_id: str, option: int, free_text: str="") -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,128}",episode_id) or type(option) is not int or option not in range(1,6):
        raise ValueError("Invalid episode/option")
    if not isinstance(free_text,str) or len(free_text)>2048 or (option==5 and not free_text.strip()):
        raise ValueError("Invalid free action")
    return f"WORLDROOT R{VERSION}: escolho opção {option} do episódio {episode_id}." + (
        " Ação livre/instrução adicional: "+free_text if free_text.strip() else "") + " Recuperar HEAD, RESUME e opção literal; registrar somente esta escolha real."

def choice_review(full_text: str) -> dict:
    cut=re.search(r"(?mi)^##\s+(?:AS CINCO PORTAS|ESCOLHAS|CINCO ESCOLHAS)",full_text)
    tail=full_text[cut.start():] if cut else ""
    versions=sorted(set(int(x) for x in VERSION_TAG.findall(tail)))
    return {"versions":versions,"stale_versions":[v for v in versions if v!=VERSION],
            "special_combination_signal":bool(SPECIAL_COMBINE.search(tail)),
            "status":"REVIEW" if not versions or any(v!=VERSION for v in versions) or SPECIAL_COMBINE.search(tail) else "CURRENT_VERSION_SIGNAL",
            "legacy_preserved":True,"canon_changed":False}

def causal_review(prose: str, root: Path, head: dict, cards=None) -> dict:
    # Require explicit linked evidence for claimed causality, not a mandatory card per scene.
    if cards is None:
        return {"status":"NOT_SUPPLIED","checked":0,"issues":[]}
    if not isinstance(cards,list) or len(cards)>100:
        return {"status":"REVIEW","checked":0,"issues":["Invalid causal card list"]}
    body=_prose(prose)
    issues=[]
    for i,c in enumerate(cards,1):
        if not isinstance(c,dict):
            issues.append(f"Card {i}: invalid");continue
        effect=c.get("effect_anchor")
        cause=c.get("cause_anchor")
        pos=body.find(effect) if isinstance(effect,str) and len(effect.strip())>=12 else -1
        local=body.find(cause) if isinstance(cause,str) and len(cause.strip())>=12 else -1
        prior=_literal_evidence(root,head,c.get("prior_source")) if c.get("prior_source") else None
        if pos<0 or not ((0<=local<pos) or prior):
            issues.append(f"Card {i}: causal evidence missing or out of order")
        if not isinstance(c.get("consequence"),str) or not c["consequence"].strip():
            issues.append(f"Card {i}: consequence missing")
    return {"status":"REVIEW" if issues else "ANCHORS_CHECKED","checked":len(cards),"issues":issues,
            "semantic_certification":False}

def review(prose: str, root: Path, head: dict, full_text=None, cards=None, experience=None) -> dict:
    m=measure(prose)
    notes=[]
    if m["meta_phrases"]:
        notes.append("R30: examine editorial language in scene; keep only organically spoken or necessary facts.")
    if m["shared_exact_dialogue"]:
        notes.append("R30: inspect repeated exact speech across voices; an intentional callback is valid.")
    if m["lucas_miren_reference"]:
        notes.append("R30: when relationship is central, examine reciprocal desire, agency, tension, intimacy, change and memory; not a quota.")
    notes.extend(["R30: read meaningful sensory detail, emotional stakes and consequence in context.",
                  "R30: inspect earned epic progression; never weaken GÊNESE or manufacture opposition to make a scene exciting."])
    return {"status":"ADVISORY_ONLY","metrics":m,"notices":notes,
            "causality":causal_review(prose,root,head,cards),
            "experience_review":experience_cards(prose,root,head,experience),
            "choice_contract":choice_review(full_text) if isinstance(full_text,str) else None,
            "literary_certification":False,"canon_changed":False}

def receipt(prose,root,head,full_text=None,cards=None,experience=None):
    try:return review(prose,root,head,full_text,cards,experience)
    except (ValueError,TypeError,OSError,KeyError) as exc:
        return {"status":"UNAVAILABLE","reason":str(exc),"canon_changed":False}

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,required=True)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("registry")
    r=sub.add_parser("review");r.add_argument("--literal",type=Path,required=True)
    b=sub.add_parser("brief");b.add_argument("--character",action="append",default=[]);b.add_argument("--scene",action="append",default=[])
    c=sub.add_parser("compare");c.add_argument("--literal",type=Path,required=True);c.add_argument("--scene",action="append",required=True)
    a=p.parse_args(argv)
    if a.action=="registry":result=source_registry(a.archive_root)
    elif a.action=="brief":result=writer_brief(a.archive_root,a.character,a.scene)
    elif a.action=="compare":result=compare(a.literal.read_text(encoding="utf-8"),a.archive_root,a.scene)
    else:result=review(a.literal.read_text(encoding="utf-8"),a.archive_root,read_obj(a.archive_root/"canon/HEAD.json"))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
