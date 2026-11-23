"""R25 source-grounded literary experience gate. Never certifies prose or rewrites canon."""
from __future__ import annotations
import re
from statistics import median

SCENE = re.compile(r"(?m)^##\s+([IVX]{1,8})\s+[—–-]\s+([^\n]+)$")
STOP = re.compile(r"(?mi)^\s*(?:###\s*CHECKPOINT|##\s*ESCOLHAS|\*\*FIM DA PARTE)")
WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+(?:[’'-][A-Za-zÀ-ÿ0-9]+)*")
NAMED = re.compile(r"(?m)^\s*\*\*([A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]{1,36})\s+[—–-]\*\*\s+\S")
UNLABELED = re.compile(r"(?m)^\s*[—–]\s+\S")
BACKSTAGE = re.compile(
    r"(?i)\b(?:contagem inventada de mortes|conveni[eê]ncia narrativa|"
    r"não declarou uma evolução inventada|n[aã]o havia sido aprovado pelo autor|"
    r"n[aã]o precisava fingir que sua energia estava acabando)\b"
)
SCHEMA = "worldroot-reader-review-v1"


def scene_blocks(prose: str) -> list[tuple[str, str]]:
    if not isinstance(prose, str):
        raise TypeError("Literal prose required")
    matches = list(SCENE.finditer(prose))
    out = []
    for i, hit in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prose)
        body = prose[hit.end():end]
        cut = STOP.search(body)
        if cut:
            body = body[:cut.start()]
        out.append((hit.group(1), body))
    return out


def assess_experience(prose: str, *, previous_counts: list[int] | None = None) -> dict:
    rows = scene_blocks(prose)
    counts = [len(WORD.findall(body)) for _, body in rows]
    short_share = sum(n < 650 for n in counts) / len(counts) if counts else 0
    named = sum(len(NAMED.findall(body)) for _, body in rows)
    unlabeled = sum(len(UNLABELED.findall(body)) for _, body in rows)
    leaked = [
        {"scene": number, "excerpt": match.group(0)}
        for number, body in rows for match in BACKSTAGE.finditer(body)
    ]
    previous = previous_counts or []
    if not isinstance(previous, list) or any(type(n) is not int or n < 0 for n in previous):
        raise ValueError("Previous measured scene counts must be integers")
    risks = []
    if len(rows) >= 9 and short_share >= 0.7:
        risks.append("R25_FOCUS: muitos cortes curtos; revisar experiência sustentada")
    if len(rows) >= 9 and previous.count(len(rows)) >= 2:
        risks.append("R25_TEMPLATE: terceira parte com mesma contagem de cenas")
    if leaked:
        risks.append("R25_BACKSTAGE: bastidor/editorial exposto na ficção")
    if not rows:
        risks.append("R25_SCENES: sem títulos reconhecidos")
    return {
        "status": "REVISAR" if risks else "SEM_SINAL_ESTRUTURAL",
        "scene_count": len(rows),
        "scene_words_median_approx": median(counts) if counts else 0,
        "short_scene_share": round(short_share, 3),
        "named_dialogue_turns": named,
        "unlabeled_dialogue_turns": unlabeled,
        "backstage_excerpts": leaked[:12],
        "risks": risks,
        "literary_certification": False,
        "independent_human_review": False,
        "canon_changed": False,
    }


def validate_reader_review(prose: str, review: dict | None, *,
                           previous_counts: list[int] | None = None) -> dict:
    result = assess_experience(prose, previous_counts=previous_counts)
    errors = []
    if not isinstance(review, dict) or review.get("schema") != SCHEMA:
        return {**result, "errors": ["R25_REVIEW: missing review"], "release_ready": False}
    if review.get("decision") != "REVISADO_COM_EVIDENCIAS":
        errors.append("R25_REVIEW: editorial pass not attested")
    evidence = review.get("scene_evidence")
    if not isinstance(evidence, list) or len(evidence) < 2:
        errors.append("R25_REVIEW: two distinct scenes required")
        evidence = []
    rows = dict(scene_blocks(prose))
    used = set()
    for entry in evidence:
        if not isinstance(entry, dict):
            errors.append("R25_REVIEW: malformed evidence")
            continue
        scene = entry.get("scene")
        anchor = entry.get("literal_anchor")
        if not isinstance(scene, str) or scene in used or scene not in rows:
            errors.append("R25_REVIEW: scene missing or repeated")
            continue
        used.add(scene)
        if not isinstance(anchor, str) or len(anchor.strip()) < 12 or anchor not in rows[scene]:
            errors.append("R25_REVIEW: source quote not found in its scene")
        for key in ("felt_experience", "scene_turn", "lasting_consequence"):
            value = entry.get(key)
            if not isinstance(value, str) or len(value.strip()) < 12:
                errors.append("R25_REVIEW: incomplete " + key)
    if any(x.startswith(("R25_FOCUS", "R25_TEMPLATE")) for x in result["risks"]):
        justification = review.get("pacing_decision")
        if not isinstance(justification, str) or len(justification.strip()) < 45:
            errors.append("R25_REVIEW: fragmented chapter requires documented pacing decision")
    if result["backstage_excerpts"]:
        errors.append("R25_BACKSTAGE: rewrite unambiguous auditor intrusion")
    return {**result, "errors": errors, "release_ready": not errors}


def preview_reader_review(prose: str, *, previous_counts: list[int] | None = None) -> dict:
    data = assess_experience(prose, previous_counts=previous_counts)
    return {
        "total_scenes": data["scene_count"],
        "median_scene_words": data["scene_words_median_approx"],
        "short_scene_share": data["short_scene_share"],
        "dialogue_named": data["named_dialogue_turns"],
        "dialogue_unlabeled": data["unlabeled_dialogue_turns"],
        "narrative_alerts": data["risks"],
        "literary_certification": False,
    }
