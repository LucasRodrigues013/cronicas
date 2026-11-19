"""WORLDROOT Livro VI: advisory narrative dynamics, never canon publication.

This module does not generate scenes, tick clocks, choose for Lucas, or write
the story archive. It evaluates explicit outlines and draft signals for human
editorial review. GitHub story-archive/canon/HEAD.json remains authoritative.
"""
from __future__ import annotations

import re
from typing import Any

MODULE_NAMES = (
    "WORLD_PULSE",
    "ANTAGONIST_ENGINE",
    "SPY_NETWORK",
    "AWE_SYSTEM",
    "COMBAT_CONTINUITY",
    "SCENE_DIRECTOR",
    "FACTION_CLOCK",
    "MYSTERY_GRAPH",
    "RELATIONSHIP_PULSE",
    "LEGACY_EVENTS",
)
FIVE_PARTS = ("I", "II", "III", "IV", "V")
EXPERIENCES = ("MARAVILHAMENTO", "AVENTURA", "RELACOES", "ESTRATEGIA")
AUDIT_BASELINE = {
    "fantasia": 5, "lucas": 4, "conflito": 5,
    "autonomia": 5, "antagonismo": 5, "conexoes": 4,
    "ritmo": 5, "continuidade": 5, "consequencias": 4,
}
assert sum(AUDIT_BASELINE.values()) == 42


def review_chapter_outline(outline: dict[str, Any]) -> dict[str, Any]:
    """Structural checks; advisory about artistic value and rhythm.

    Required: 5 parts, each containing a scene objective, change and hook.
    Never treats creative proposals or a successful outline as canon events.
    """
    errors: list[str] = []
    notices: list[str] = []
    if not isinstance(outline, dict):
        return {"ok": False, "errors": ["Outline must be a mapping"], "notices": []}
    parts = outline.get("parts")
    if not isinstance(parts, list) or len(parts) != 5:
        return {"ok": False, "errors": ["Exactly five chapter parts are required"], "notices": []}
    for index, (part, expected) in enumerate(zip(parts, FIVE_PARTS), start=1):
        if not isinstance(part, dict) or part.get("part") != expected:
            errors.append(f"Part {index} must use label {expected}")
            continue
        for field in ("dramatic_goal", "lived_scene", "change", "outgoing_hook"):
            if not isinstance(part.get(field), str) or not part[field].strip():
                notices.append(f"Part {expected}: describe {field} in lived narrative terms")
        experiences = part.get("experiences", [])
        if not isinstance(experiences, list):
            errors.append(f"Part {expected}: experiences must be an array")
        elif any(e not in EXPERIENCES for e in experiences):
            errors.append(f"Part {expected}: unknown experience label")
        intensity = part.get("intensity")
        if intensity is not None and (isinstance(intensity, bool)
                                     or not isinstance(intensity, int)
                                     or not 1 <= intensity <= 5):
            errors.append(f"Part {expected}: intensity must be integer 1..5 when supplied")
    finale = parts[-1] if isinstance(parts[-1], dict) else {}
    if not isinstance(finale.get("earned_payoff"), str) or not finale["earned_payoff"].strip():
        notices.append("Part V must deliver an earned dramatic payoff, not only an epilogue or status report")
    intensities = [p.get("intensity") for p in parts if isinstance(p, dict)]
    if len(intensities) == 5 and all(isinstance(i, int) and not isinstance(i, bool) for i in intensities):
        if intensities[-1] < max(intensities):
            notices.append("Part V should be the emotional climax; review if an earlier part eclipses it")
    if not outline.get("canon_checkpoint_ref"):
        notices.append("Consult live HEAD and last canonical literal source before writing")
    if not outline.get("author_choices_open", True):
        errors.append("A chapter outline must not predetermine Lucas's future irreversible choices")
    proposed_events = outline.get("seeds", [])
    if not isinstance(proposed_events, list):
        errors.append("Seeds must be an array")
    elif any(not isinstance(s, dict) or s.get("status") not in ("PROPOSTA", "EM_PREPARACAO") for s in proposed_events):
        errors.append("New seeds must remain PROPOSTA or EM_PREPARACAO, not narrated/canonical facts")
    return {"ok": not errors, "errors": errors, "notices": notices,
            "part_count": 5, "canon_updated": False, "narrative_generated": False}


def review_operation(operation: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed planning record, not an autonomous tactical simulator."""
    required = ("id", "actor", "location", "objective", "resources",
                "known_information", "route_or_access", "earliest_window",
                "possible_outcomes", "status")
    missing = [key for key in required if not operation.get(key)]
    errors = [f"Missing operation field: {field}" for field in missing]
    if operation.get("status") not in ("PROPOSTA", "EM_PREPARACAO"):
        errors.append("A planning operation cannot self-promote to narrated or canon")
    outcomes = operation.get("possible_outcomes", ())
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        errors.append("Operations need at least two possible outcomes and remain defeatable")
    if operation.get("instant_character_knowledge"):
        errors.append("Backstage operations cannot automatically inform Lucas or others")
    if operation.get("genesis_nerf"):
        errors.append("No automatic GENESE suppression")
    return {"ok": not errors, "errors": errors, "canon_updated": False}


def inspect_draft_dynamics(prose: str, metadata: dict | None = None) -> dict[str, Any]:
    """Non-blocking draft review. Signals are NOT literary quality scores."""
    if not isinstance(prose, str):
        raise TypeError("prose must be text")
    metadata = metadata or {}
    words = len(prose.split())
    part = str(metadata.get("part", "")).upper()
    scene_headers = len(re.findall(r"(?m)^\s*(?:[IVX]{1,4}\s*[—–-]|CENA\s+\d+)", prose, flags=re.I))
    has_lucas = bool(re.search(r"\bLUCAS\b", prose, flags=re.I))
    has_dialogue = bool(re.search(r"(?m)^\s*(?:\*\*)?[A-ZÁÉÍÓÚÃÕÂÊÔÇ][A-ZÁÉÍÓÚÃÕÂÊÔÇ\s]{1,25}(?:\*\*)?\s*[—–]\s*\S", prose))
    notices = []
    if not has_dialogue:
        notices.append("Review scene-level dialogue and character reactions; narration should not read like a report")
    if part == "V":
        notices.append("Human review: did Part V earn a memorable dramatic climax instead of summarizing I–IV?")
    if not has_lucas:
        notices.append("Lucas may be off-screen; confirm that this viewpoint is intentional and independently active")
    return {"status": "ADVISORY_ONLY", "words": words, "part": part,
            "scene_heading_signals": scene_headers, "lucas_mentioned": has_lucas,
            "dialogue_signal": has_dialogue, "notices": notices,
            "quality_score": None, "canon_updated": False, "narrative_generated": False}
