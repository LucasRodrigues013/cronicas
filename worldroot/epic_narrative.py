"""R29 story craft: optional source-bound writer-room cards and long-arc projection.
Read-only editorial assistance; no canon writes, automatic outcomes, grades or quotas.
R28 retains ownership of assets, character activity, and historical retrieval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from .living_world import project, read_obj, literal_body, scene_rows, normalize

PLAN = "planning/book-vi/r29-epic-narrative.json"
SCHEMA = "worldroot-r29-craft-review-v1"
DIRECTORS = {
    "promise_payoff": ("promise_id", "progress_or_reward", "meaning", "remaining_question"),
    "character_arc": ("character", "desire", "contradiction_or_resistance", "own_decision", "relationship_change"),
    "adventure": ("place", "reason_to_travel", "local_discovery", "experience", "consequence"),
    "culture_civilization": ("people", "local_practice", "lived_interaction", "effect_on_choices"),
    "epic_moment": ("setup", "action", "witness_response", "meaning", "lasting_consequence"),
    "power_application": ("actor", "existing_power_or_source", "application", "response", "effect"),
    "antagonist_perspective": ("actor", "own_goal", "known_information", "decision", "cost_or_consequence"),
    "emotional_legacy": ("prior_event_or_bond", "present_action", "changed_meaning"),
    "long_arc": ("arc_id", "current_movement", "chapter_reward", "open_future"),
    "originality": ("abstract_technique", "local_story_origin", "distinct_expression"),
}
PRIOR_REQUIRED = {"promise_payoff", "emotional_legacy"}
POLICY_FLAGS = ("preserve_full_authority", "preserve_agency", "no_predetermined_outcomes",
                "no_retcon", "no_copied_expression")
META = re.compile(r"(?i)\b(?:promessa progresso recompensa|diretor narrativo|originality guard|worldroot r29|arco planejado pelo autor)\b")

def _nonempty(v):
    return isinstance(v,str) and bool(v.strip())

def _literal_evidence(root: Path, head: dict, item: dict):
    """Resolve a prior source only if a closed journal entry is within HEAD and bytes agree."""
    if not isinstance(item,dict):
        return None
    episode,anchor=item.get("episode"),item.get("anchor")
    if not isinstance(episode,str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}",episode):
        return None
    if not _nonempty(anchor) or len(anchor.strip())<12 or len(anchor)>2000:
        return None
    try:
        closure=read_obj(root/"canon/episodes"/(episode+".json"))
        seq=closure.get("sequence")
        if (closure.get("schema")!="worldroot-github-closure-v1" or
            closure.get("episode_id")!=episode or type(seq) is not int or
            not 1<=seq<=head["sequence"] or
            (seq==head["sequence"] and episode!=head.get("episode_id"))):
            return None
        f=root/"episodes"/episode/"draft/narrativa_integral.md"
        if f.is_symlink() or not f.is_file():
            return None
        raw=f.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=closure.get("story_sha256"):
            return None
        text=raw.decode("utf-8")
        if anchor not in text:
            return None
        return {"episode":episode,"sha256":digest,"sequence":seq,
                "line":text.split(anchor,1)[0].count("\n")+1,"anchor":anchor,
                "scope":"PRIOR_LITERAL_NOT_UNIVERSAL_KNOWLEDGE"}
    except (OSError,ValueError,KeyError,TypeError):
        return None

def validate_plan(plan: dict) -> dict:
    """Planning metadata is deliberately not a source of narrated events."""
    if plan.get("schema")!="worldroot-r29-creative-plan-v1":
        raise ValueError("R29 planning schema mismatch")
    if plan.get("status")!="AUTHOR_APPROVED_DIRECTION_NOT_CANON":
        raise ValueError("R29 plan cannot assert canon")
    seeds=plan.get("seeds")
    if not isinstance(seeds,list):
        raise ValueError("Seed list required")
    ids=set()
    for s in seeds:
        if (not isinstance(s,dict) or not _nonempty(s.get("id")) or s["id"] in ids or
            s.get("state")!="POSSIBILITY_NOT_NARRATED" or
            not all(_nonempty(s.get(k)) for k in ("title","premise","entry_condition","possible_reward","safeguard"))):
            raise ValueError("Invalid, duplicated or promoted seed")
        ids.add(s["id"])
    arcs=plan.get("arcs")
    if not isinstance(arcs,list) or not all(isinstance(a,dict) and
        _nonempty(a.get("id")) and a.get("outcome_open") is True and
        a.get("fixed_deadline") is None and _nonempty(a.get("focus")) for a in arcs):
        raise ValueError("Long arcs require open outcomes, not preset deadlines")
    if len({a["id"] for a in arcs})!=len(arcs):
        raise ValueError("Duplicate arc")
    return {"seed_count":len(seeds),"arc_count":len(arcs),"canon_changed":False}

def review(prose: str, head: dict, root: Path, cards: dict | None=None) -> dict:
    """Explicit review cards are optional; verified anchors are not semantic certification.
    Signals never constitute evidence of artistic quality or a hard archive gate.
    """
    if not isinstance(prose,str) or not prose.strip():
        raise ValueError("Literal prose required")
    body=literal_body(prose)
    scenes=scene_rows(body)
    result={"schema":"worldroot-r29-advisory-v1","status":"ADVISORY_ONLY",
            "head_episode_id":head.get("episode_id"),"canon_changed":False,
            "independent_human_review":False,"literary_certification":False,
            "directors":{k:{"reviewed":0,"anchored":0} for k in DIRECTORS},
            "signals":{"scene_count":len(scenes),
                       "fantasy_scene_references":sum(bool(set(s["signals"])&{"magic","creature","culture","exploration"}) for s in scenes),
                       "relationship_scene_references":sum("relationship" in s["signals"] for s in scenes),
                       "meta_language":sorted(set(m.group(0) for m in META.finditer(body)))[:12]},
            "notices":[]}
    notices=result["notices"]
    if result["signals"]["meta_language"]:
        notices.append("Keep writer-room methodology outside the fiction.")
    if cards is None:
        result["card_status"]="NOT_SUPPLIED"
        return result
    if not isinstance(cards,dict) or cards.get("schema")!=SCHEMA or cards.get("source_episode_id")!=head.get("episode_id"):
        result["card_status"]="INVALID_OR_STALE"
        notices.append("R29 review cards require schema and current HEAD.")
        return result
    # This is a declared editorial safeguard, not a classifier of intent.
    for flag in POLICY_FLAGS:
        if cards.get(flag) is not True:
            notices.append("Review safeguard: "+flag)
    records=cards.get("cards",[])
    if not isinstance(records,list) or len(records)>100:
        result["card_status"]="INVALID"
        notices.append("Invalid or oversized review cards.")
        return result
    for idx,card in enumerate(records,1):
        if not isinstance(card,dict) or card.get("director") not in DIRECTORS:
            notices.append(f"Card {idx}: unknown director")
            continue
        kind=card["director"]
        stats=result["directors"][kind]
        stats["reviewed"]+=1
        missing=[k for k in DIRECTORS[kind] if not _nonempty(card.get(k))]
        anchor=card.get("draft_anchor")
        if not _nonempty(anchor) or len(anchor.strip())<12 or len(anchor)>2000 or anchor not in body:
            missing.append("exact_draft_anchor")
        if kind in PRIOR_REQUIRED or card.get("prior_source") is not None:
            prior=_literal_evidence(root,head,card.get("prior_source"))
            if prior is None:
                missing.append("verified_prior_source")
        if kind=="power_application" and card.get("weakens_genese") is not False:
            missing.append("no_artificial_weakening")
        if kind=="long_arc" and (card.get("outcome_open") is not True or card.get("fixed_deadline") is not None):
            missing.append("open_outcome_no_artificial_deadline")
        if kind=="originality" and card.get("borrowed_protected_expression") is not False:
            missing.append("no_copied_expression")
        if kind=="antagonist_perspective" and card.get("omniscient") is not False:
            missing.append("no_unearned_information")
        if missing:
            notices.append(f"Card {idx} ({kind}): review "+", ".join(missing))
        else:
            stats["anchored"]+=1
    result["card_status"]="REVIEW_NOTICES" if notices else "ANCHORS_CHECKED"
    return result

def planning_brief(root: Path, head: dict | None=None) -> dict:
    """Compose existing R28 projection and R29 possibilities, without promoting them."""
    live=read_obj(root/"canon/HEAD.json")
    if head is not None and head!=live:
        raise ValueError("Stale HEAD")
    plan=read_obj(root/PLAN)
    stats=validate_plan(plan)
    world=project(root,live)
    plots={p["id"]:p for p in world["plots"]}
    promises=[]
    for p in plan.get("promises",[]):
        linked=plots.get(p.get("plot_id"))
        evidence=linked.get("evidence_status") if linked else "NO_R28_LINK"
        promises.append({"id":p["id"],"promise":p["promise"],
                         "possible_reward":p["possible_reward"],"plot_id":p.get("plot_id"),
                         "latest_reviewed_progress":linked.get("progress") if linked and evidence=="SOURCE_MATCH" else None,
                         "last_reference":linked.get("last_reference") if linked else None,
                         "needs_review":bool(not linked or evidence!="SOURCE_MATCH" or linked.get("later_reference_needs_review")),
                         "evidence_status":evidence,"status":"EDITORIAL_TRACKING_NOT_EVENT"})
    return {"schema":"worldroot-r29-planning-brief-v1","head":live,
            "status":world["status"],"warnings":world["warnings"],"coverage":world["coverage"],
            "counts":stats,"promises":promises,"seeds":plan["seeds"],"arcs":plan["arcs"],
            "identity":plan["identity"],"references":plan["references"],
            "character_recovery":sorted(world["characters"],key=lambda c:
                (c.get("days_since_dialogue") is not None, -(c.get("days_since_dialogue") or 0)))[:12],
            "assets_for_reuse":[{"id":a["id"],"name":a["name"],"state":a["state"],
                                  "evidence_status":a["evidence_status"]} for a in world["assets"]],
            "canon_changed":False,
            "limitation":"Editorial opportunities, not scene outcomes. Consult literal and author choice."}

def receipt(prose: str, root: Path, head: dict, cards: dict | None=None) -> dict:
    try:
        return review(prose,head,root,cards)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return {"status":"UNAVAILABLE","reason":str(exc),"canon_changed":False}

def main(argv=None):
    p=argparse.ArgumentParser(description="WORLDROOT R29 read-only narrative craft")
    p.add_argument("--archive-root",type=Path,required=True)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("brief")
    s=sub.add_parser("review");s.add_argument("--literal",type=Path,required=True);s.add_argument("--cards",type=Path)
    a=p.parse_args(argv)
    if a.action=="brief": result=planning_brief(a.archive_root)
    else: result=receipt(a.literal.read_text(encoding="utf-8"),a.archive_root,
                         read_obj(a.archive_root/"canon/HEAD.json"),read_obj(a.cards) if a.cards else None)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
