"""Consultative literary precision for future WORLDROOT Book VI drafts.

Pure, deterministic and deliberately NON-CANONICAL. Its signals never grant
approval, rewrite prose, infer a character's knowledge or certify artistic merit.
Call with the literal episode text, never a synopsis or chapter manifest.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+(?:['’\-][A-Za-zÀ-ÿ0-9]+)*")
SCENE = re.compile(r"(?m)^\s*(?:##\s+)?([IVX]{1,8})\s+[—–-]\s+([^\n]+)$")
STOP = re.compile(r"(?mi)^\s*(?:##\s*)?(?:ESCOLHAS|O que vem depois|FIM DA PARTE|OPÇÕES DE CONTINUAÇÃO)\b")
SCRIPT = re.compile(
    r"(?m)^\s*(?:\*\*)?([A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]{1,32})\s*[—–-](?:\*\*)?\s*(.+)$"
)
META = re.compile(
    r"(?i)\b(?:contagem inventada|conveni[eê]ncia narrativa|"
    r"regra can[oô]nica|fato narrado|n[aã]o can[oô]nico|"
    r"erro de continuidade|o autor ainda n[aã]o|"
    r"n[aã]o era uma prova can[oô]nica|n[aã]o havia sido aprovado pelo autor)\b"
)
HEAD_PARTS = {"I", "II", "III", "IV", "V"}
EDIT_RULES = ("P70", "P71", "P72", "P73", "P74", "P75", "P76", "P77", "P78", "P79", "P82", "P83", "P84", "P85", "P86", "P87", "P88", "P89", "P90", "P91", "P92", "P93", "P94", "P95", "P96", "P97", "P98", "P99", "P100", "P101", "P102", "P103", "P104", "P105")


def _narrative(text: str) -> tuple[str, int]:
    matches = list(SCENE.finditer(text))
    if not matches:
        return text, 0
    start = matches[0].start()
    stop = STOP.search(text, start)
    return text[start:stop.start() if stop else len(text)], len(matches)


def review_episode(prose: str) -> dict[str, Any]:
    """Return *risk indicators*, not grades or automatic rejection.

    Source must be full prose; thresholds are soft and cannot substitute for
    an editor reading scenes with authorial intent and the current live HEAD.
    """
    if not isinstance(prose, str) or not prose.strip():
        raise ValueError("A complete nonempty literal draft is required")
    body, scenes = _narrative(prose)
    prose_lines: list[str] = []
    lucas_lines: list[str] = []
    voices: Counter[str] = Counter()
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith(("<", "{@", ">", "#", "|", "---", "***")):
            continue
        if SCENE.fullmatch(line):
            continue
        match = SCRIPT.match(line)
        if match:
            speaker, words = match.groups()
            speaker = speaker.strip().upper()
            voices[speaker] += 1
            if speaker == "LUCAS":
                lucas_lines.append(words)
            continue
        if re.match(r"^\*?【", line) or line.startswith("—"):
            continue
        # Tags and editorial metadata are excluded from this sample.
        if "DIA " in line[:12] and re.search(r"\d{1,2}h\d{2}", line):
            continue
        if WORD.search(line):
            prose_lines.append(line)
    short = sum(1 for line in prose_lines if len(WORD.findall(line)) <= 7)
    micro_share = short / len(prose_lines) if prose_lines else 0
    uppercase = sum(
        1 for line in lucas_lines
        if len(WORD.findall(line)) >= 3
        and len(re.findall(r"[A-Za-zÀ-ÿ]", line)) >= 12
        and re.findall(r"[A-Za-zÀ-ÿ]", line)
        and not re.search(r"[a-zà-ÿ]", line)
    )
    shout_share = uppercase / len(lucas_lines) if lucas_lines else 0
    meta_matches = META.findall(body)
    notices: list[str] = []
    if meta_matches:
        notices.append("LIT01: bastidor/editorial possivelmente exposto na ficção; revisar contexto e reescrever apenas texto futuro")
    if scenes >= 3 and len(prose_lines) >= 35 and micro_share >= 0.72:
        notices.append("LIT02: muitas linhas narrativas curtíssimas; variar cadência conforme a emoção e a ação")
    if len(lucas_lines) >= 10 and shout_share >= 0.35:
        notices.append("LIT03: proporção alta de falas gritadas de Lucas; revisar carisma, escuta e afeto sem silenciá-lo")
    return {
        "status": "ADVISORY_ONLY",
        "scene_count": scenes,
        "sampled_prose_lines": len(prose_lines),
        "short_line_share": round(micro_share, 3),
        "lucas_turns": len(lucas_lines),
        "lucas_uppercase_turn_share": round(shout_share, 3),
        "meta_language_hits": len(meta_matches),
        "top_speakers": voices.most_common(6),
        "notices": notices,
        "literary_grade": None,
        "human_review_required": True,
        "canon_changed": False,
        "source_rewritten": False,
    }


def review_series_structure(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Spot a uniform scene template across *multiple* distinct episodes."""
    if not isinstance(episodes, list):
        raise TypeError("Episodes must be a list of per-episode review dictionaries")
    counts = []
    for item in episodes:
        if not isinstance(item, dict) or type(item.get("scene_count")) is not int:
            raise ValueError("Each episode requires a measured integer scene_count")
        counts.append(item["scene_count"])
    repeated = [(n, count) for n, count in Counter(counts).items() if n >= 8 and count >= 3]
    return {
        "status": "ADVISORY_ONLY",
        "episodes_compared": len(counts),
        "repeated_scene_counts": sorted(repeated),
        "notices": (["LIT04: contagem igual de cenas em três ou mais episódios; verificar estrutura mecânica, sem impor variação"] if repeated else []),
        "canon_changed": False,
    }


def review_scene_cards(cards: list[dict[str, str]]) -> dict[str, Any]:
    """Small planning gate: explicit scene purpose, opposition, turn and cost.

    Optional planning data, never a requirement to create or change canon.
    """
    required = ("desire", "resistance", "lived_action", "turn", "consequence")
    if not isinstance(cards, list):
        raise TypeError("Scene cards must be a list")
    notices = []
    for index, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError("Each scene card must be a mapping")
        missing = [name for name in required if not isinstance(card.get(name), str) or not card[name].strip()]
        if missing:
            notices.append(f"LIT05: cena {index} precisa de revisão humana para " + ", ".join(missing))
    return {"status": "ADVISORY_ONLY", "cards": len(cards),
            "notices": notices, "canon_changed": False}


def build_live_brief(head: dict, policy: dict, max_chars: int = 1700) -> dict:
    """Use supplied, read-back *live* HEAD; never trust stale policy snapshots.

    The caller is responsible for fetching HEAD directly from story-archive.
    This function does not fetch files or assert that a draft is canon.
    """
    if not isinstance(head, dict) or not isinstance(policy, dict):
        raise TypeError("Verified live HEAD and policy mappings are required")
    if type(max_chars) is not int or max_chars < 350:
        raise ValueError("Insufficient editorial brief budget")
    for key in ("book", "chapter", "part", "day", "episode_id"):
        if not head.get(key):
            raise ValueError(f"Missing live HEAD field: {key}")
    if type(head["chapter"]) is not int or type(head["day"]) is not int:
        raise ValueError("Invalid HEAD chronological fields")
    sequence = head.get("sequence")
    if sequence is not None and (type(sequence) is not int or sequence < 0):
        raise ValueError("Invalid HEAD sequence")
    sequence_label = str(sequence) if sequence is not None else "não informada"
    if head["part"] not in HEAD_PARTS or not isinstance(head["episode_id"], str):
        raise ValueError("Invalid HEAD part/episode reference")
    lines = [
        "WORLDROOT — CONTINUIDADE EDITORIAL VIVA, SEM PROMOÇÃO AUTOMÁTICA.",
        f"HEAD FORNECIDO PELO CHAMADOR (validar leitura externa): {head['book']}, C{head['chapter']:02d}, Parte {head['part']}, D{head['day']}, sequência {sequence_label}.",
        "Fonte literal: " + head["episode_id"] + ". O novo episódio não é canônico pela escrita.",
        "Preservar CREATION/GÊNESE plena, agência de Lucas e seus aliados, Miren, Rumo e NÓX livres.",
        "Priorizar cenas vividas: desejo, resistência, ação, mudança e consequências; sem fórmulas de quantidade de cenas.",
        "Voz de Lucas: forte, divertida, gentil e amorosa; respeitar silêncio e escuta. Evitar humor gritado por inércia.",
        "Remover linguagem de auditoria do narrador; bastidores ficam nos registros, não na prosa.",
        "Variar ação épica, assombro, cultura, relações e risco humano; não converter capítulo em relatório.",
        "R28: recuperar ativos, elenco e tramas; evitar duplicação, compressão e discursos repetidos. Especial singular; magia vivida, não quota.",
        "R29: promessa/progresso/recompensa, aventura regional, arcos pessoais, legado emocional e poderes criativos; manter identidade e originalidade.",
        "R30: fichas e corpus, romance adulto não gráfico, sentidos, vozes e emoção; causalidade, bastidores fora da prosa, escolhas R30.",
        "Informação e deslocamentos só com evidência; planejamento não é fato narrado.",
    ]
    policies = {r.get("id"): r for r in policy.get("rules", []) if isinstance(r, dict) and r.get("active")}
    selected = [rid for rid in EDIT_RULES if rid in policies]
    if all(rid in policies for rid in ("P106","P107","P108","P109")):
        lines.insert(4, "R31: recuperar 95% dos requisitos por criação e 100% críticos; uma rota principal, três secundárias de igual valor e ação livre; nenhuma domina.")
        selected.extend(rid for rid in ("P106","P107","P108","P109") if rid not in selected)
    brief = "\n".join(lines)
    while len(brief) > max_chars and len(lines) > 4:
        lines.pop(-2)
        brief = "\n".join(lines)
    if len(brief) > max_chars:
        raise ValueError("Live brief cannot fit required identity and evidence")
    return {"text": brief, "policy_version": policy.get("version"),
            "selected_rule_ids": selected, "mode": "LIVE_HEAD_GROUNDED",
            "canon_changed": False}
