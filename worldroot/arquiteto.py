"""R35 ARQUITETO: bounded editorial work queues, not a second canon or LLM.
The existing natural_codex/live_codex projection remains the authority adapter.
All generated proposals require a separately recorded semantic review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from .natural_codex import CHAR_FIELDS, PRIVATE_SCOPES, validate_fields

SCHEMA="worldroot-arquiteto-v1"
STATIC_DESIGN=frozenset(("body","face","hair","eyes","skin","voice","gestures","wardrobe","preferences","values","fears","contradictions","goals","age_apparent","height_cm","mass_kg"))
# Never make historical events, actual knowledge/skills, current location,
# ownership, relationships or biological/chronological age from a guess.
ROLES=frozenset(("CLOSED_PROSE","LEGACY_MIXED","AUTHOR_DIRECTION","DRAFT","REJECTED","EDITORIAL"))
DISPOSITIONS=frozenset(("SUPPORTED","PARTIAL","CONTRADICTED","UNKNOWN","NOT_ENTITY","MENTION_ONLY","NEW_ID_CANDIDATE","AUTHOR_REQUIRED"))
GENERIC=frozenset(("sistema","narrador","homem","mulher","jovem","crianca","menino","menina","guarda","soldado","comerciante","trabalhador","trabalhadora","tecnica","tecnico","responsavel","representante","artesao","mensageiro","voz"))
SPEAKER=re.compile(r"^\s*(?:>\s*)?(?:\*\*)?([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 .’'-]{1,48}?)(?:\*\*)?\s*(?:—|–| - |:)\s*(?:\*\*)?(.+)$")
def normalized(s):
    return " ".join(re.findall(r"[a-z0-9]+",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()))
def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
def stable(value):
    return sha(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")))
def aliases(cards):
    result={}
    for card in cards:
        for name in [card["id"],card["name"],*card.get("aliases",[])]:
            k=normalized(name)
            if k:result.setdefault(k,set()).add(card["id"])
    return result
def discover(text,source_id,role,cards):
    """Speaker-shaped candidates; no name matching is a semantic conclusion."""
    if role not in ROLES or not source_id:raise ValueError("Source role and ID required")
    ids=aliases(cards);source_hash=sha(text);rows=[]
    section=role
    for n,line in enumerate(text.splitlines(),1):
        if role=="LEGACY_MIXED":
            if line.strip()=="## Prompt:":section="AUTHOR_DIRECTION"
            elif line.strip()=="## Response:":section="LEGACY_MIXED"
        m=SPEAKER.match(line)
        if not m:continue
        name=m[1].strip();key=normalized(name)
        if not key or key.startswith(("livro ","capitulo ","dia ","parte ","escolha ","opcao ")):continue
        if re.fullmatch(r"[ivxlcdm]+",key):continue
        candidates=sorted(ids.get(key,()))
        kind="GENERIC_ROLE" if key in GENERIC else ("ALIAS_COLLISION" if len(candidates)>1 else ("KNOWN_CANDIDATE" if candidates else "NEW_NAME_CANDIDATE"))
        row={"source_id":source_id,"source_sha256":source_hash,"line":n,"anchor":line,"name":name,"candidates":candidates,"source_role":section,"kind":kind}
        row["id"]=stable(row);rows.append(row)
    return rows
def field_tasks(card):
    """Return explicit queue; never interpret placeholder as content."""
    fields=card["fields"];result=[]
    for name,entry in sorted(fields.items()):
        if entry["status"]!="PENDENTE_FONTE":continue
        route="RECOVER_THEN_DESIGN" if name in STATIC_DESIGN else "RECOVER_OR_EXPLICITLY_KEEP_UNKNOWN"
        basis=[k for k,v in fields.items() if v["status"] not in ("PENDENTE_FONTE","SEGREDO") and v.get("scope") not in PRIVATE_SCOPES]
        result.append({"id":stable([card["id"],name,entry]),"entity_id":card["id"],"field":name,"route":route,"basis_fields":basis})
    return result
def validate_review(row,review,text):
    """Verify structural and provenance constraints, NOT semantic correctness."""
    if review.get("candidate_id")!=row["id"] or review.get("disposition") not in DISPOSITIONS:raise ValueError("Invalid adjudication")
    if row["source_sha256"]!=sha(text):raise ValueError("Stale source")
    lines=text.splitlines();n=row["line"]
    if type(n) is not int or not 1<=n<=len(lines) or lines[n-1]!=row["anchor"]:raise ValueError("Literal mismatch")
    for key in ("extractor","reviewer","reason"):
        if not isinstance(review.get(key),str) or not review[key].strip():raise ValueError("Missing review metadata")
    if review["extractor"]==review["reviewer"]:raise ValueError("Separate review required")
    if review["disposition"]=="SUPPORTED":
        if row["source_role"]!="CLOSED_PROSE" or review.get("entity_id") not in row["candidates"]:raise ValueError("Unsupported promotion route")
        if not review.get("claim"):raise ValueError("Explicit claim required")
    return {"candidate_id":row["id"],"review":review,"semantic_certification":False,"canon_changed":False}
def design_patch(card,proposal,review):
    """Apply only approved prospective static design to a copy of a profile.
    Caller must obtain real semantic review; role labels alone do not certify it.
    """
    field=proposal.get("field");fields=card["fields"]
    if proposal.get("entity_id")!=card["id"] or field not in STATIC_DESIGN or fields.get(field,{}).get("status")!="PENDENTE_FONTE":raise ValueError("Protected or non-design field")
    if proposal.get("base_card_sha256")!=stable(card):raise ValueError("Stale profile")
    basis=proposal.get("basis_fields")
    if not isinstance(basis,list) or not basis or not all(k in fields and fields[k]["status"] not in ("PENDENTE_FONTE","SEGREDO") and fields[k].get("scope") not in PRIVATE_SCOPES for k in basis):raise ValueError("No valid contextual basis")
    if not proposal.get("value") or not str(proposal.get("reason","")).strip():raise ValueError("Empty design")
    if review.get("proposal_sha256")!=stable(proposal) or review.get("verdict")!="ACCEPT_PROSPECTIVE" or not review.get("reviewer") or review["reviewer"]==proposal.get("designer") or not proposal.get("designer") or not str(review.get("reason","")).strip():raise ValueError("Separate design review required")
    new=json.loads(json.dumps(card,ensure_ascii=False));new["fields"][field]={"value":proposal["value"],"status":"COMPLETADO","scope":"EDITORIAL","origin":{"architect":SCHEMA,"proposal_sha256":stable(proposal),"review_sha256":stable(review),"basis_fields":basis,"previous":fields[field]},"justification":proposal["reason"],"checkpoint":fields[field].get("checkpoint")}
    validate_fields(new["fields"])
    return new
def queue(root):
    """Read-only snapshot of current overlay gaps and archived speaker candidates.
    Historical exports stay mixed even when a line looks like a speaker.
    """
    from .live_codex import load_registry
    loaded=load_registry(root)
    if not loaded:raise ValueError("Missing registry")
    data,reg=loaded;overlay=data.get("_natural_overlay")
    if not overlay:raise ValueError("Missing natural overlay")
    cards=list(overlay["profiles"].values());root=Path(root)
    tasks=[t for card in cards for t in field_tasks(card)]
    sources=[];candidates=[]
    for path in sorted((root/"history/sources").glob("*")):
        if not path.is_file() or path.is_symlink():continue
        body=path.read_text(encoding="utf-8")
        rel=path.relative_to(root).as_posix();rows=discover(body,rel,"LEGACY_MIXED",cards)
        sources.append({"path":rel,"sha256":sha(body),"lines":len(body.splitlines()),"candidates":len(rows)})
        candidates.extend(rows)
    from .git_cycle import verify_episode,load
    for receipt in sorted((root/"canon/episodes").glob("*.json")):
        if receipt.is_symlink():raise ValueError("Unsafe receipt")
        episode=receipt.stem;draft,manifest=verify_episode(root,episode)
        close=load(receipt)
        if close["story_sha256"]!=manifest["original_readback_sha256"]:raise ValueError("Closure source mismatch")
        body=draft.prose;rows=discover(body,episode,"CLOSED_PROSE",cards)
        sources.append({"episode":episode,"sha256":sha(body),"lines":len(body.splitlines()),"candidates":len(rows)})
        candidates.extend(rows)
    return {"schema":SCHEMA,"registry_sha256":reg,"checkpoint":overlay["checkpoint"],"sources":sources,"field_tasks":tasks,"candidates":candidates,"semantic_certification":False,"canon_changed":False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archive-root",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    output=Path(a.output);root=Path(a.archive_root).resolve()
    if output.resolve().is_relative_to(root/"canon"):raise ValueError("Queue cannot write canon")
    result=queue(root);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"sources":len(result["sources"]),"field_tasks":len(result["field_tasks"]),"candidates":len(result["candidates"]),"semantic_certification":False}))
if __name__=="__main__":main()
