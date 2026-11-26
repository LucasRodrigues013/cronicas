"""Cross-entity checks for R35. Ordinal design is not a damage simulator.
All numerical examples are hypothetical until bound to approved designs.
"""
from __future__ import annotations
from math import isfinite

def number(x):
    return type(x) in (int,float) and isfinite(x) and x>0

def passage(body,opening,posture="upright",clearance_cm=0):
    """Height, width and load are independent; unknown never means safe."""
    h=body.get("height_cm")
    if not number(h):
        lower=body.get("height_lower_bound_cm")
        if number(lower) and number(opening.get("clear_height_cm")) and posture=="upright" and lower>=opening["clear_height_cm"]:
            return {"status":"BLOCKED","reason":"height_lower_bound"}
        return {"status":"UNKNOWN","reason":"body_height"}
    if posture not in ("upright","stoop","kneel"):raise ValueError("Unknown posture")
    if not number(opening.get("clear_height_cm")):return {"status":"UNKNOWN","reason":"opening_height"}
    if posture!="upright":
        h=body.get("posture_height_cm")
        if not number(h):return {"status":"UNKNOWN","reason":"posture_height"}
    if h+clearance_cm>opening["clear_height_cm"]:return {"status":"BLOCKED","reason":"height"}
    width=body.get("shoulder_width_cm")
    if not number(width) or not number(opening.get("clear_width_cm")):return {"status":"UNKNOWN","reason":"width"}
    if width+clearance_cm>opening["clear_width_cm"]:return {"status":"BLOCKED","reason":"width"}
    return {"status":"POSSIBLE","reason":"clearances_only"}

def seating(body,seat):
    fields=("mass_kg","seated_width_cm","comfortable_seat_height_cm")
    for k in fields:
        if not number(body.get(k)):return {"status":"UNKNOWN","reason":k}
    for k in ("rated_mass_kg","seat_width_cm","seat_height_cm"):
        if not number(seat.get(k)):return {"status":"UNKNOWN","reason":k}
    if body["mass_kg"]>seat["rated_mass_kg"]:return {"status":"BLOCKED","reason":"load"}
    if body["seated_width_cm"]>seat["seat_width_cm"]:return {"status":"BLOCKED","reason":"width"}
    if abs(body["comfortable_seat_height_cm"]-seat["seat_height_cm"])>8:
        return {"status":"ADAPTATION_REQUIRED","reason":"ergonomics"}
    return {"status":"POSSIBLE","reason":"measured_compatibility_only"}

def combat(attack,defense,*,channel,access,ability_proven):
    """No random victory, additive power levels or forced nerf.
    Inputs are channel-specific evidence-reviewed grades, not ranks of persons.
    """
    if not ability_proven:return {"status":"BLOCKED","reason":"unproven_capability"}
    if access is False:return {"status":"BLOCKED","reason":"no_access"}
    if access is not True:return {"status":"UNKNOWN","reason":"access"}
    if not isinstance(channel,str) or not channel.strip():raise ValueError("Missing channel")
    if attack is None or defense is None:return {"status":"UNKNOWN","reason":"unmeasured_channel"}
    if any(type(x) is not int or not 0<=x<=7 for x in (attack,defense)):raise ValueError("Ordinary axis 0..7 only")
    if attack<defense:return {"status":"BLOCKED","reason":"insufficient_effect_for_claimed_channel"}
    return {"status":"POSSIBLE_NOT_GUARANTEED","reason":"defense_threshold_met; reactions and consequences still required"}

def learned_in_registry(record,spell):
    return any(s.get("spell_id")==spell and s.get("status")=="CANON_DEMONSTRATED_SEMANTICALLY_REVIEWED" for s in record.get("verified_magic",[]))

def item_access(custody,actor,location=None):
    if not custody:return False
    if custody.get("state") in ("CONSUME","LOSE"):return False
    if custody.get("holder")==actor:return True
    return bool(location and custody.get("state")=="STORE" and custody.get("location")==location)

def validate_interactions(prose,review,records):
    """Validate structured cross-entity claims, not arbitrary semantics of prose.
    Unknown and blocked results require narrated adaptation or no asserted success.
    """
    from .live_codex import check_anchor
    if not isinstance(review,dict) or review.get("schema")!="worldroot-coherence-review-v1":raise ValueError("Missing coherence review")
    checks=review.get("interactions")
    if not isinstance(checks,list) or not isinstance(review.get("coverage_reason"),str) or not review["coverage_reason"].strip():raise ValueError("Explicit interaction coverage required")
    for c in checks:
        if c.get("actor") not in records or c.get("target") not in records:raise ValueError("Unknown interaction identity")
        check_anchor(prose,c["line"],c["anchor"])
        kind=c.get("kind")
        if kind not in ("PASSAGE","SEAT","VEHICLE","TOUCH","COMBAT","MAGIC","ITEM"):raise ValueError("Unknown interaction kind")
        status=c.get("disposition")
        if status not in ("SUPPORTED","ADAPTED","HELD","NOT_APPLICABLE"):raise ValueError("Invalid disposition")
        if not isinstance(c.get("reason"),str) or not c["reason"].strip():raise ValueError("Missing causal reasoning")
        # Deliberately not allow scene-supplied dimensions or combat grades to become facts.
        # Validated material inputs must refer to the bound record, not a fabricated number.
        if "inputs" in c:raise ValueError("Do not override bound profile with scene numbers")
        if status=="ADAPTED":
            check_anchor(prose,c["adaptation_line"],c["adaptation_anchor"])
        if status=="SUPPORTED" and kind in ("PASSAGE","SEAT","VEHICLE","COMBAT"):
            # Existing records do not yet contain homologated physical/channel measurements.
            # Fail closed on quantitative feasibility until matching approved fields exist.
            if not c.get("evidence_refs") or not isinstance(c["evidence_refs"],list):raise ValueError("Compatibility or combat requires reviewed evidence references")
            refs=c["evidence_refs"]
            valid=set()
            for ident in (c["actor"],c["target"]):
                for fact in records[ident].get("coherence_facts",[]):
                    if fact.get("evidence"):valid.add(ident+":"+fact["field"])
            if not all(isinstance(r,str) and r in valid for r in refs):raise ValueError("Unbound compatibility evidence")
    return {"reviewed_interactions":len(checks),"semantic_certification":False}
