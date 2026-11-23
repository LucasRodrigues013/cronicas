"""Creation (GÊNESE) is an AUTHORIAL AUTHORITY, never a ranked spell.

Evidence-grade mystery guard; it cannot tell a true secret or force its reveal.
False positives in attributed dialogue are marked for editorial consideration,
not used to suppress character doubts, questions or mistaken beliefs.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

BIBLE = Path(__file__).resolve().parent / "r26" / "authority_creation.json"

@lru_cache(maxsize=1)
def load_creation_authority() -> dict[str, Any]:
    source = json.loads(BIBLE.read_text(encoding="utf-8"))
    if source.get("schema") != "worldroot-r26-2-creation-authority-v1":
        raise ValueError("Unknown CREATION authority schema")
    return source


def validate_authority_bible() -> dict[str, Any]:
    book = load_creation_authority()
    errors = []
    flags = book.get("policy_flags", {})
    required = (
        "genese_is_not_spell", "no_rank_or_tier", "no_mana_budget",
        "no_magic_immunity", "no_automatic_universal_information",
        "guardian_dragons_are_independent", "aerun_institute_is_not_dragon",
        "premundane_dragons_unproven", "author_controls_final_revelation",
        "canon_head_unmodified",
    )
    errors += ["AUTHORITY_SCHEMA:" + name for name in required if flags.get(name) is not True]
    if book.get("identity", {}).get("kind") != "AUTORIDADE_PRIMORDIAL_NAO_MAGIA":
        errors.append("AUTHORITY_SCHEMA: kind cannot be magic")
    if book.get("identity", {}).get("scope") != "SEM_ESCALA_SEM_MEDIDA_SEM_LIMITE_IMPOSTO":
        errors.append("AUTHORITY_SCHEMA: authority is never rank-limited")
    mysteries = book.get("protected_unknowns", [])
    if len(mysteries) < 5:
        errors.append("AUTHORITY_SCHEMA: no mystery protection")
    elif any(m.get("status") not in ("HIPOTESE_NAO_COMPROVADA",
                                    "NÃO_RESOLVIDO", "HIPOTESE_SEM_PROVA")
             for m in mysteries):
        errors.append("AUTHORITY_SCHEMA: secret was silently canonized")
    if len(book.get("narrative_threads", [])) < 5:
        errors.append("AUTHORITY_SCHEMA: mystery arcs missing")
    return {
        "status": "OK" if not errors else "BLOQUEADO",
        "errors": errors,
        "separate_from_magic": True,
        "mysteries_protected": len(mysteries),
        "story_seeds_not_canon": len(book.get("narrative_threads", [])),
        "canonical_origin_revealed": False,
    }


HYPOTHESIS = re.compile(
    r"(?i)\b(?:talvez|sup[oô]s|hip[oó]tes|boato|rumor|"
    r"diziam|dizem|segundo|lenda|acreditam|seria|"
    r"quem sabe|pergunt\w*|suspeit\w*|duvid\w*|ningu[eé]m sabia|n[aã]o havia prova|se .*?(?:fosse|existisse))\b"
)
ATTRIBUTED_DIALOGUE = re.compile(r"^\s*(?:\*\*)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ ]+\s+—")
AUTHORITY = r"(?:G[EÊ]NESE|CREATION)"
AUTHORITY_CATEGORY = re.compile(
    rf"(?i)\b{AUTHORITY}\b[^.!?\n]{{0,95}}\b(?:era|é|foi|funcionava como|se tratava de)\b"
    r"[^.!?\n]{0,68}\b(?:magia|feitiço|círculo\s*(?:IX|9)|rank|tier)\b"
)
AUTHORITY_FUEL = re.compile(
    rf"(?i)\b{AUTHORITY}\b[^.!?\n]{{0,100}}\b"
    r"(?:parou|falhou|acabou|esgotou|desligou|não funcionou|cessou|foi bloquead[ao])\b"
    r"[^.!?\n]{0,100}\b(?:mana|reservas?\s+arcan[ao]s?|energia\s+arcana)\b"
)
AUTHORITY_COUNTER = re.compile(
    rf"(?i)\b(?:feitiço|magia|círculo\s*(?:IX|9))\b[^.!?\n]{{0,120}}"
    rf"\b(?:anulou|cancelou|desativou|neutralizou|suprimiu)\b[^.!?\n]{{0,70}}\b{AUTHORITY}\b"
    rf"|\b{AUTHORITY}\b[^.!?\n]{{0,90}}\b(?:anulad[ao]|neutralizad[ao]|cancelad[ao])\b"
    r"[^.!?\n]{0,75}\b(?:por|pela?)\b[^.!?\n]{0,55}\b(?:magia|feitiço|círculo)\b"
)
COSMOLOGY_DRAGONS = re.compile(
    r"(?i)\b(?:AER[ÚU]N|drag[oõ]es?|guardi[aã]o(?:ões)?)\b"
    r"[^.!?\n]{0,100}\b(?:antes\s+(?:do|da)|mais antig[oa]s?\s+(?:do|da|que))\b"
    r"[^.!?\n]{0,75}\b(?:mundo|cria[cç][aã]o\s+do\s+mundo)\b"
)
COSMOLOGY_SYSTEM = re.compile(
    rf"(?i)(?:\bSISTEMA\b[^.!?\n]{{0,75}}\b(?:criou|originou|gerou)\b"
    rf"[^.!?\n]{{0,75}}\b{AUTHORITY}\b|"
    rf"\b{AUTHORITY}\b[^.!?\n]{{0,55}}\b(?:foi criado|nasceu)\b"
    r"[^.!?\n]{0,50}\b(?:pelo\s+Sistema|da\s+rede\s+antiga|do\s+Cora[cç][aã]o)\b)"
)
ENTITY_MIXUP = re.compile(
    r"(?i)\b(?:instituto|campus|cidadela)\b[^.!?\n]{0,35}\bAER[ÚU]N\b"
    r"[^.!?\n]{0,65}\b(?:mesmo ser|mesma entidade|id[êe]ntic[oa]|era\s+o\s+mesmo)\b"
    r"[^.!?\n]{0,55}\b(?:drag[aã]o|AER[ÚU]N)\b"
)
DRAGON_MENTION = re.compile(r"(?i)\b(?:drag[aã]o|guardi[aã]o\s+das\s+mar[eé]s)\b")
INSTITUTE_MENTION = re.compile(r"(?i)\b(?:instituto|cidadela|campus|laborat[oó]rio)\b")


def scan_creation_prose(prose: str) -> dict[str, Any]:
    """Only block specific source-unsupported categorical narration.

    Report uncertain references separately. This is a narrow heuristic, not
    a semantic verifier for the secret history of an imaginary universe.
    """
    if not isinstance(prose, str):
        raise TypeError("Creation audit expects narrative prose")
    errors, warnings = [], []
    dragon_refs, institute_refs, unclear_refs = 0, 0, 0
    for raw in prose.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "AERÚN" in line.upper() or "AERUN" in line.upper():
            if DRAGON_MENTION.search(line):
                dragon_refs += 1
            elif INSTITUTE_MENTION.search(line):
                institute_refs += 1
            else:
                unclear_refs += 1
        if ATTRIBUTED_DIALOGUE.match(line) or HYPOTHESIS.search(line):
            # People can believe, question or speculate; no omniscient fact is inferred.
            continue
        if AUTHORITY_CATEGORY.search(line):
            errors.append("R26_CREATION: GÊNESE classified as an ordinary ranked spell")
        if AUTHORITY_FUEL.search(line):
            errors.append("R26_CREATION: artificial mana exhaustion/arcane resource limit")
        if AUTHORITY_COUNTER.search(line):
            errors.append("R26_CREATION: ordinary spell cannot automatically negate Authority")
        if COSMOLOGY_DRAGONS.search(line):
            errors.append("R26_COSMOLOGY: pre-world dragon chronology is unproven")
        if COSMOLOGY_SYSTEM.search(line):
            errors.append("R26_COSMOLOGY: Sistema/Coração origin of CREATION remains unknown")
        if ENTITY_MIXUP.search(line):
            errors.append("R26_ENTITY: AERÚN institution and dragon are distinct")
    if unclear_refs:
        warnings.append(
            "R26_ENTITY_ADVISORY: ambiguous AERÚN mention(s) require scene-context review")
    return {
        "errors": sorted(set(errors)), "warnings": warnings,
        "dragon_references": dragon_refs, "institute_references": institute_refs,
        "ambiguous_aerun_references": unclear_refs,
        "genese_kind": "AUTORIDADE_NAO_MAGIA",
        "power_measure_assigned": False,
        "cosmology_finalized": False,
        "mystery_revealed_to_lucas": False,
        "human_semantic_review_required": True,
        "canon_changed": False,
    }
