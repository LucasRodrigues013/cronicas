"""Additive opt-in R32 release receipt for NEW drafts. Never rewrites archived choices."""
from __future__ import annotations
import hashlib,re
from .memory_continuity import DOMAINS,arc_review,review_creation
from .experience_quality import render_choices
from .presentation_guard import SCENE

def release_review(root,head,payload):
    review=payload.get("r32_review")
    if not isinstance(review,dict):raise ValueError("R32 memory review required")
    text=payload["full_text"];prose=payload["prose"]
    if review.get("head")!=head or review.get("prose_sha256")!=hashlib.sha256(prose.encode()).hexdigest():raise ValueError("R32 stale HEAD or prose binding")
    req=review.get("requirements")
    if not isinstance(req,list) or not req or not all(isinstance(r,dict) for r in req) or not any(r.get("critical") is True for r in req):raise ValueError("R32 declare material memory and critical requirements")
    ids={r["id"] for r in req}
    if len(ids)!=len(req):raise ValueError("Duplicate memory requirement")
    if any(not isinstance(r.get("query"),str) or not r["query"].strip() for r in req):raise ValueError("Missing query")
    domains=review.get("domain_review")
    if not isinstance(domains,dict) or set(domains)!=set(DOMAINS):raise ValueError("Review applicability of all memory domains")
    for k,v in domains.items():
        if not isinstance(v,dict) or type(v.get("applicable")) is not bool or not isinstance(v.get("reason"),str) or not v["reason"].strip():raise ValueError("Missing domain justification")
        if v["applicable"]!=any(r["domain"]==k for r in req):raise ValueError("Domain coverage mismatch")
    scene_count=len(SCENE.findall(prose))
    scenes=review.get("scene_requirements")
    if not isinstance(scenes,list) or len(scenes)!=scene_count or not scene_count:raise ValueError("Every actual scene must declare its memory context")
    used=set()
    for i,s in enumerate(scenes,1):
        if s.get("scene")!=i or not isinstance(s.get("ids"),list) or not s["ids"] or not set(s["ids"])<=ids:raise ValueError("Invalid scene memory mapping")
        used.update(s["ids"])
    if used!=ids:raise ValueError("Unmapped memory requirements")
    a=arc_review(review.get("arc_packet"))
    if a["errors"]:raise ValueError("R32 route contract: "+"; ".join(a["errors"]))
    if review.get("editorial_parity_reviewed") is not True:raise ValueError("Explicit editorial choice review required")
    rendered=render_choices(review["arc_packet"],payload["delivery_id"],revision=payload.get("metadata",{}).get("worldroot_revision") if payload.get("metadata",{}).get("worldroot_revision") in (34,35) else 30)
    if rendered["markup"] not in text or not text.startswith(rendered["body_declaration"]):raise ValueError("Visible options differ from reviewed equal-style routes")
    choices=payload["choices"]
    for opt,c in zip(review["arc_packet"]["options"],choices[:4]):
        title=re.sub(r"^ESPECIAL\s*[—–-]\s*","",c["title"],flags=re.I)
        expected=re.sub(r"^ESPECIAL\s*[—–-]\s*","",opt["title"],flags=re.I)
        if c["number"]!=opt["number"] or title!=expected or c.get("is_special")!=(opt["number"]==4) or c.get("is_free") is not False:raise ValueError("Stored options differ from visible routes")
    if choices[4].get("is_free") is not True:raise ValueError("Missing free action")
    result=review_creation(root,head,req,review.get("reviewed"))
    if result["status"]!="REVIEWED_EVIDENCE_THRESHOLD_MET":raise ValueError("R32 memory below 95% or critical evidence missing")
    return {"schema":"worldroot-r32-release-review-v1","source_head":head,"prose_sha256":review["prose_sha256"],"memory":result,"arc":a,"semantic_certification":False,"canon_changed":False}
