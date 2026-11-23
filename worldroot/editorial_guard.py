"""WORLDROOT fast, evidence-linked editorial memory (not a prose generator).

Policy is versioned on main; immutable chapters and canon remain on story-archive.
Checks are deliberately cheap and do not certify literary semantics.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

POLICY_PATH = Path(__file__).with_name("editorial_policy.json")
IMAGE_EMBED = re.compile(r"!\[[^\n\]]*\]\([^\n)]*\)|<\s*(?:img|svg)\b|data:image/", re.I)
ALLOWED_STANCES = {"MANTER", "EVITAR", "MELHORAR"}
ALLOWED_ENFORCEMENT = {"ESTRUTURAL", "EDITORIAL"}
ID = re.compile(r"^[A-Z][A-Z0-9_]{1,35}$")


def validate_policy(policy: dict) -> dict:
    if not isinstance(policy, dict) or policy.get("schema") != "worldroot-editorial-policy-v1":
        raise ValueError("Unrecognized WORLDROOT editorial policy")
    if policy.get("project") != "CRONICAS_DE_UM_NOVO_MUNDO":
        raise ValueError("Unrelated universe policy forbidden")
    if type(policy.get("version")) is not int or policy["version"] < 1:
        raise ValueError("Policy version required")
    sources = policy.get("sources")
    rules = policy.get("rules")
    if not isinstance(sources, list) or not sources or not isinstance(rules, list) or not rules:
        raise ValueError("Evidence sources and editorial rules required")
    source_ids = set()
    for source in sources:
        sid = source.get("id") if isinstance(source, dict) else None
        if not isinstance(sid, str) or not ID.fullmatch(sid) or sid in source_ids:
            raise ValueError("Duplicate or invalid feedback source identifier")
        if not isinstance(source.get("quote"), str) or not source["quote"].strip():
            raise ValueError("Feedback source must retain original wording")
        line = source.get("transcript_line")
        if line is not None and (type(line) is not int or line <= 0):
            raise ValueError("Invalid transcript line")
        source_ids.add(sid)
    seen = set()
    for rule in rules:
        rid = rule.get("id") if isinstance(rule, dict) else None
        if not isinstance(rid, str) or not ID.fullmatch(rid) or rid in seen:
            raise ValueError("Duplicate or invalid editorial rule")
        seen.add(rid)
        if (rule.get("stance") not in ALLOWED_STANCES
                or rule.get("enforcement") not in ALLOWED_ENFORCEMENT
                or type(rule.get("active")) is not bool
                or type(rule.get("core")) is not bool):
            raise ValueError("Invalid rule metadata: " + rid)
        if (not isinstance(rule.get("directive"), str)
                or len(rule["directive"].strip()) < 35
                or not isinstance(rule.get("tags"), list)
                or not rule["tags"]
                or any(not isinstance(t, str) or not ID.fullmatch(t) for t in rule["tags"])):
            raise ValueError("Insufficient editorial directive or invalid tags: " + rid)
        if (not isinstance(rule.get("evidence"), list)
                or not rule["evidence"]
                or any(s not in source_ids for s in rule["evidence"])):
            raise ValueError("Editorial rule lacks traceable feedback: " + rid)
    return {"rule_count": len(rules), "source_count": len(sources), "version": policy["version"]}


def load_policy(path: Path | None = None) -> dict:
    data = json.loads((path or POLICY_PATH).read_text(encoding="utf-8"))
    validate_policy(data)
    return data


def compact_brief(policy: dict, scene_tags=(), max_chars: int = 1750, *, head: dict | None = None) -> dict:
    """Stable small prompt context; no retrieval of 296,900-line historical transcript."""
    validate_policy(policy)
    if head is not None:
        from .literary_revision import build_live_brief
        return build_live_brief(head, policy, max_chars=max_chars)
    if type(max_chars) is not int or max_chars < 320:
        raise ValueError("Context budget too small")
    if isinstance(scene_tags, str):
        raise TypeError("Tags must be a collection")
    tags = {str(t).upper() for t in scene_tags}
    active = [r for r in policy["rules"] if r["active"]]
    # Core quality contract first; then at most a handful of scene-specific notes.
    scored = sorted(active, key=lambda r: (
        -int(r["core"]),
        -len(tags.intersection(r["tags"])),
        r["id"],
    ))
    lines = [
        "WORLDROOT v" + str(policy["version"]),
        "TITULO: AS COROAS PARTIDAS; PRE-PRODUCAO, r17 rejeitado; nao narrar sem ordem.",
        "ABERTURA P53: D538 acorda, corre cidade, lembra Terra, cafe Miren, depois Kael/Lysa.",
        "CIDADE P54/P59: renascentista; Kael/Lysa, AERUN e Forja crescem; inicio nao climax.",
        "REDES P55: Costura VIDEO regional D533; Malha 3600/Vertice D531; expansao urbana.",
        "ATLAS P57: Eixo33,2km Campo, Thalor320/Cald545 PROPOSTAS; ARGOS1462 pico nao cruzeiro.",
        "POVOS P58: reinos, Khelen, anoes, elfos, orcs e casas antigas autonomas.",
        "VELKAR P60: 42M/260mil/520 navios PROPOSTA; batalhas epicas, GENESE plena.",
        "ARQUITETOS P61: Coracao distribui mana; Tessa, Marés/chave PROPOSTAS.",
        "MEIO P62: portais/LEVIATA Livro VI como ponte, nao clímax.",
        "TEMPO P63: C1 cinco partes em 2-3dias, uma data por Parte; escolhas livres.",
        "VIDA P28/P29/P30: Miren, ARGOS, Talis, humor, nao relatorios.",
    ]
    prioritized = ("P57", "P58", "P59", "P60", "P61", "P62", "P63", "P64", "P53", "P54", "P55", "P56", "P49", "P50", "P51", "P52", "P43", "P44", "P45", "P46", "P47", "P48", "P35", "P36", "P37", "P38", "P39", "P40", "P41", "P42", "P31", "P32", "P33", "P34", "P26", "P27", "P28", "P29", "P30")
    available = {r["id"] for r in active}
    selected = [rid for rid in prioritized if rid in available]
    for rule in scored:
        if rule["id"] in selected:
            continue
        if not rule["core"] and not tags.intersection(rule["tags"]):
            continue
        sentence = rule["id"] + ": " + rule["directive"]
        if len("\n".join(lines + [sentence])) > max_chars:
            continue
        lines.append(sentence)
        selected.append(rule["id"])
    lines.append("Texto literal > resumos; planejamento não vira cânone; confirmação externa exige recibo.")
    return {"text": "\n".join(lines), "selected_rule_ids": selected,
            "policy_version": policy["version"], "truncated_to_budget": len(selected) < len(active)}


def quick_preflight(prose: str, *, policy: dict | None = None, scene_tags=(), head: dict | None = None) -> dict:
    """Linear-time, low-noise checks. Warnings NEVER silently rewrite or reject art."""
    policy = policy or load_policy()
    validate_policy(policy)
    errors = []
    notices = []
    if not isinstance(prose, str) or not prose.strip():
        errors.append("Full narrative text required")
        prose = ""
    if IMAGE_EMBED.search(prose):
        errors.append("Crônicas story must not embed images; preserve prose")
    words = len(prose.split())
    if 0 < words < 250:
        notices.append("Short installment: editorial review for full scenes and character interactions")
    if words >= 350 and not re.search(r"(?m)^\s*[\wÀ-ÿ][\wÀ-ÿ .'-]{0,55}\s*[—–]\s*\S", prose):
        notices.append("Review dialogue and character voices; no identifiable NAME — dialogue")
    from .literary_revision import review_episode
    literary = review_episode(prose) if prose.strip() else None
    if literary and literary["scene_count"] >= 2:
        notices.extend(literary["notices"])
    if head is None and re.search(r"\bLIVRO\s+VI\b", prose[:2000], re.I):
        notices.append("LIT06: HEAD vivo não informado; não reutilizar breve estático da abertura para a continuidade")
    selected = compact_brief(policy, scene_tags=scene_tags, max_chars=900, head=head)
    return {"status": "BLOQUEADO" if errors else ("REVISAR" if notices else "OK"),
            "errors": errors, "notices": notices, "words": words,
            "policy_version": policy["version"], "consulted_rules": selected["selected_rule_ids"],
            "editorial_brief_mode": selected.get("mode", "LEGACY_STATIC_NO_HEAD"),
            "literary_review": literary,
            "semantic_certification": False, "canon_changed": False,
            "fast_path": "LOCAL_DETERMINISTIC_NO_NETWORK"}


def verify_historical_staging(pack: dict) -> dict:
    """Structural provenance only. Never promotes historical answers into canon."""
    if (not isinstance(pack, dict)
            or pack.get("schema") != "worldroot-historical-qa-draft-v1"
            or pack.get("scope") != "CRONICAS_ONLY"
            or pack.get("canon_promotion") is not False):
        raise ValueError("Historical QA must be explicitly non-canonical and scoped")
    items = pack.get("questions")
    if not isinstance(items, list) or [q.get("n") for q in items] != list(range(1, 41)):
        raise ValueError("Exactly forty sequential historical answers required")
    limit = pack.get("source_line_count")
    if type(limit) is not int or limit < 100:
        raise ValueError("Primary source line-count required")
    for q in items:
        if (not isinstance(q.get("answer"), str) or len(q["answer"].strip()) < 40
                or q.get("status") != "HISTORICAL_SOURCE_NOT_RECONCILED"
                or type(q.get("source_start_line")) is not int
                or type(q.get("source_end_line")) is not int
                or not 1 <= q["source_start_line"] <= q["source_end_line"] <= limit):
            raise ValueError("Historical answer/evidence range requires human reconciliation")
    return {"checked": 40, "source_line_count": limit,
            "structural_provenance": "OK", "semantic_certification": False,
            "canon_changed": False, "usable_as": "HISTORICAL_STAGING_ONLY"}
