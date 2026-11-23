"""WORLDROOT rich chapter presentation contract.

Fast structural preflight, not a screenshot renderer or literary judge.
Run only for new archives; existing immutable drafts are never rewritten.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

POLICY_PATH = Path(__file__).with_name("presentation_policy.json")
SCENE = re.compile(r"(?m)^\s*##\s+[IVX]{1,8}\s*[—–-]\s+\S")
DIALOGUE = re.compile(r"(?m)^\s*\*\*[A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]{1,36}\s+[—–-]\*\*\s+\S")
UNLABELED = re.compile(r"(?m)^\s*[—–]\s+\S")
CLOCK = re.compile(r"(?im)\bDIA\s+\d+\s*[·|—-]\s*\d{1,2}h\d{2}")
BUTTON = re.compile(r"<button\b", re.I)
ACTION = re.compile(r"<button\b[^>]*onClick\s*=\s*\{\s*\(\s*\)\s*=>\s*GenUI\.issueNewTurn\s*\(", re.I)


def load_presentation_policy(path: Path | None = None) -> dict:
    policy = json.loads((path or POLICY_PATH).read_text(encoding="utf-8"))
    if (policy.get("schema") != "worldroot-presentation-policy-v1"
            or policy.get("project") != "CRONICAS_DE_UM_NOVO_MUNDO"
            or type(policy.get("version")) is not int or policy["version"] < 1):
        raise ValueError("Wrong WORLDROOT presentation policy")
    rules = policy.get("classifications")
    if (not isinstance(rules, list) or len(rules) < 10
            or len({r["id"] for r in rules}) != len(rules)
            or any(r.get("level") not in ("OBRIGATORIO", "PREFERENCIAL", "PROIBIDO")
                   for r in rules)):
        raise ValueError("Malformed presentation classifications")
    return policy


def presentation_preflight(full_text: str, *, policy: dict | None = None,
                           strict_dialogue: bool = True) -> dict:
    """Check the VISIBLE installment including checkpoint and choices.

    Does not certify the narrative's truth, aesthetics or actual screen rendering.
    """
    policy = policy or load_presentation_policy()
    if policy.get("project") != "CRONICAS_DE_UM_NOVO_MUNDO":
        raise ValueError("Presentation policy crosses universes")
    errors: list[str] = []
    notices: list[str] = []
    if not isinstance(full_text, str) or not full_text.strip():
        return {"status": "BLOQUEADO", "errors": ["UX00: missing visible chapter"],
                "notices": [], "checks": {}, "semantic_certification": False}
    s = full_text
    upper = s.upper()
    scenes = SCENE.findall(s)
    checkpoint_at = upper.rfind("CHECKPOINT")
    choice_at = upper.rfind("ESCOLHA")
    first_scene_at = s.find(scenes[0]) if scenes else 0
    prose_end = checkpoint_at if checkpoint_at > first_scene_at else len(s)
    unlabeled_count = len(UNLABELED.findall(s[first_scene_at:prose_end]))
    checks = {
        "masthead": "CRÔNICAS DE UM NOVO MUNDO" in upper[:2500] and "WORLDROOT" in upper[:2500],
        "book_chapter_part": bool(re.search(r"LIVRO\s+[IVX]+\b", upper[:2500]))
            and "CAPÍTULO" in upper[:2500]
            and bool(re.search(r"PARTE\s+(?:I|II|III|IV|V)\s+DE\s+V", upper[:2500])),
        "rich_header": '<box align="center"' in s[:1800] and s[:2200].count("<title") >= 3,
        "calendar_panel": "CALENDÁRIO DO HORIZONTE" in upper[:3500]
            and "<grid" in s[:3500] and "<box border" in s[:3500],
        "scenes": len(scenes) >= 3,
        "dialogue": len(DIALOGUE.findall(s)) >= 5,
        "unlabeled_dialogue": unlabeled_count == 0,
        "scene_clocks": len(CLOCK.findall(s)) >= 2,
        "checkpoint": checkpoint_at > 0,
        "rich_checkpoint": checkpoint_at > 0
            and "<box border" in s[max(0, checkpoint_at - 260):checkpoint_at],
        "choices": "ESPECIAL" in upper[checkpoint_at:] and (
            "AÇÃO LIVRE" in upper[checkpoint_at:] or "ACAO LIVRE" in upper[checkpoint_at:]),
        "choice_controls": len(BUTTON.findall(s)) >= 4 and len(ACTION.findall(s)) >= 4,
        "free_control": "<textarea" in s and "onChange=" in s and "disabled=" in s,
        "correct_order": bool(scenes) and checkpoint_at > s.find(scenes[-1])
            and choice_at > checkpoint_at,
    }
    essential = {
        "masthead": "UX01", "book_chapter_part": "UX01", "rich_header": "UX01",
        "calendar_panel": "UX02", "checkpoint": "UX05",
        "rich_checkpoint": "UX05", "choices": "UX06",
        "choice_controls": "UX07", "free_control": "UX06",
        "correct_order": "UX05",
    }
    if strict_dialogue:
        essential.update({"dialogue": "UX04", "unlabeled_dialogue": "UX04"})
    for key, code in essential.items():
        if not checks[key]:
            errors.append(f"{code}: {key} absent or weak; use approved Part II rich presentation")
    for key, code in (("scenes", "UX03"), ("scene_clocks", "UX02")):
        if not checks[key]:
            notices.append(f"{code}: review {key}; structure cannot grade prose")
    if not strict_dialogue and not checks["dialogue"]:
        notices.append("UX04: legacy source does not prove speaker attribution")
    if len(BUTTON.findall(s)) > 18:
        notices.append("UX09: excessive interactions distract from literature")
    return {
        "status": "BLOQUEADO" if errors else ("REVISAR" if notices else "OK"),
        "errors": errors, "notices": notices, "checks": checks,
        "unlabeled_dialogue_count": unlabeled_count,
        "dialogue_contract_applied": strict_dialogue,
        "policy_version": policy["version"],
        "semantic_certification": False, "screenshot_certification": False,
        "canon_changed": False,
    }
