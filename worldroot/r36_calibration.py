"""Draft calibration criteria: additive, never replace archived v1 rubrics."""
from .r36_evaluation import RUBRICS
from .semantic_queue import seal

REVISION = "r36-e7-calibration-draft-v1"
DETAIL = {
 "canon": ("A material claim conflicts with authorized fact or explicit rule.", "Distinguish fact, plan, hypothesis and draft; no silent retcon."),
 "character": ("Identity, knowledge, behavior or development contradicts established evidence without cause.", "Do not equate change with inconsistency; resolve names and time."),
 "world": ("A material world constraint or institution is contradicted.", "Allow new discoveries and autonomous changes when causally supported."),
 "timeline": ("An event, travel or state transition contradicts chronology.", "Unknown times remain unknown; distinguish simultaneous and sequential events."),
 "literary": ("A material prose weakness is supported by concrete passages and context.", "Do not impose word quotas, mechanical rhythm or a single preferred style."),
 "dialogue": ("Voice or interaction materially fails contextual authenticity.", "Differentiate intentional repetition, humor, register and speaker identity."),
 "emotional": ("An emotional transition or consequence lacks credible grounding.", "Do not require a particular emotion or resolution."),
 "adventure": ("Discovery, stakes or payoff materially fail the scene's established purpose.", "Quiet scenes need not contain an adventure."),
 "combat": ("A demonstrated capability, strategy or outcome contradicts established powers or causal setup.", "Do not invent power costs, nerfs or mandatory combat."),
 "agency": ("The protagonist is assigned an unauthorized consequential choice or NPC autonomy is materially erased.", "Consequences and disagreement are not themselves agency violations."),
 "originality": ("Material repetition or formulaic construction is demonstrable against relevant references.", "Recurring motifs, callbacks and distinct character habits are not automatic failures."),
 "engineering": ("An asserted operation violates a verified invariant or contradicts execution evidence.", "No execution claim from narrative text or unsigned receipt alone."),
}
OUTCOME_RULES = {
 "PASS": "Applicable, sufficient evidence, no material violation found in the evaluated scope.",
 "FAIL": "Applicable, specific evidenced violation and proposed correction.",
 "ABSTAIN": "Not applicable or insufficient evidence; not a pass or a failure.",
 "INCONCLUSIVE": "Material conflict between sources or interpretations cannot be resolved.",
}
SEVERITY_RULES = {"critical":"Threatens authority, integrity or a critical established rule; hold.",
 "major":"Material defect within scope.", "minor":"Localized evidenced weakness.",
 "none":"No demonstrated defect; never implies global correctness."}
ROLE_RULES = {"CANON":"Established narrative evidence within its temporal scope.",
 "AUTHOR_POLICY":"Explicit author rule within its scope; no implied retcon.",
 "APPROVED_REFERENCE":"Comparison reference; not automatically factual authority."}

def calibration(judge):
    if judge not in RUBRICS: raise ValueError("Unknown judge")
    fail,limits=DETAIL[judge]
    return {"revision":REVISION,"judge":judge,"criterion":RUBRICS[judge],
            "failure_anchor":fail,"interpretation_limits":limits,
            "outcomes":dict(OUTCOME_RULES),"severity":dict(SEVERITY_RULES),
            "source_roles":dict(ROLE_RULES),"human_calibrated":False}

def context(judge,bindings):
    roles={}
    for b in bindings:
        role=b["role"]
        if role not in ROLE_RULES:raise ValueError("Invalid role")
        roles.setdefault(b["excerpt_id"],set()).add(role)
    # Conflicting roles for identical excerpts require explicit caller resolution.
    if any(len(v)!=1 for v in roles.values()):raise ValueError("Ambiguous source role")
    obj={"rubric":calibration(judge),"excerpt_roles":{k:next(iter(v)) for k,v in sorted(roles.items())}}
    return {**obj,"calibration_sha256":seal(obj)}

def comparison_context(first,second):
    """Length signal only, not a penalty or quality metric."""
    if not isinstance(first,str) or not isinstance(second,str) or not first.strip() or not second.strip():
        raise ValueError("Missing candidate")
    a,b=len(first.split()),len(second.split())
    return {"length_ratio":max(a,b)/min(a,b),
            "instruction":"Do not reward length alone; compare coverage and quality relative to the same task.",
            "automatic_length_penalty":False}
