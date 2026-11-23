"""WORLDROOT advisory: an episode can be long and still feel like a progress report.

Provides low-cost, non-semantic *risk signals*, never literary verdicts or
automatic rewrites. The author explicitly asked to prevent repetition of the
C16 Parte IV multi-day, high-volume, operational-report pattern.
"""
from __future__ import annotations

import re
from statistics import median

from .story_focus_audit import SCENE, NON_SCENE, _word_count

CLOCK = re.compile(r"(?mi)\bDIA\s+(\d{1,4})\s*[·—–-]\s*(\d{1,2})h(\d{2})\b")
DIALOGUE = re.compile(r"(?mi)^\s*\*\*[A-ZÀ-Ÿ][A-ZÀ-Ÿ .'-]+\s*[—–-]\*\*")
LUCAS = re.compile(r"(?mi)^\s*\*\*LUCAS\s*[—–-]\*\*")
UNLABELED = re.compile(r"(?m)^\s*[—–]\s+\S")
# This is a vocabulary *hint*, NOT a semantic 'technical scene' classifier.
LOGISTICS = re.compile(
    r"(?i)\b(?:relat[oó]rios?|registros?|reuni[oõ]es?|ensaios?|"
    r"testes?|autoriza(?:ção|ções|do|da|r|ram|ção|çōes)|"
    r"aprova(?:ção|ções|do|da|r)|"
    r"verifica(?:ção|ções|r|ram)|"
    r"protocolos?|checklists?|planilhas?|"
    r"medi(?:ção|ções|das|dos)|inspe(?:ção|ções)|"
    r"cronogramas?|prepara(?:ção|ções)|"
    r"valida(?:ção|ções)|instrumentos?)\b"
)
ALERT_STATUS = "ADVISORY_ONLY_REQUIRES_HUMAN_EDITORIAL_REVIEW"


def inspect_lived_narrative(prose: str) -> dict:
    """Risk of compressed lived experience across days and task-like scenes.

    Signals are deliberately advisory: action fiction may legitimately mention
    instruments, meetings and plans. A brief scene is not inherently a flaw.
    """
    if not isinstance(prose, str) or not prose.strip():
        raise ValueError("Literal nonempty narrative prose required")
    matches = list(SCENE.finditer(prose))
    scene_rows = []
    for i, heading in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prose)
        text = prose[heading.end():end]
        stop = NON_SCENE.search(text)
        if stop:
            text = text[:stop.start()]
        cut = re.search(r"\*\*FIM DA PARTE\b|\bFIM DA PARTE\b", text, re.I)
        if cut:
            text = text[:cut.start()]
        clocks = []
        for marker in CLOCK.finditer(text):
            day, hour, minute = map(int, marker.groups())
            if hour < 24 and minute < 60:
                clocks.append({"day": day, "time": f"{hour:02d}h{minute:02d}"})
        scene_rows.append({
            "scene": heading.group(1),
            "title": heading.group(2).strip(),
            "words_approx": _word_count(text),
            "clock": clocks[0] if clocks else None,
            "dialogue_lines": len(DIALOGUE.findall(text)),
            "lucas_dialogue_lines": len(LUCAS.findall(text)),
            "unlabeled_dialogue_lines": len(UNLABELED.findall(text)),
            "procedural_word_hits": len(LOGISTICS.findall(text)),
        })
    days = list(dict.fromkeys(
        row["clock"]["day"] for row in scene_rows if row["clock"] is not None
    ))
    words = sum(x["words_approx"] for x in scene_rows)
    procedural_hits = sum(x["procedural_word_hits"] for x in scene_rows)
    short = [x["scene"] for x in scene_rows if x["words_approx"] < 650]
    dialogue = sum(x["dialogue_lines"] for x in scene_rows)
    lucas = sum(x["lucas_dialogue_lines"] for x in scene_rows)
    unattributed = sum(x["unlabeled_dialogue_lines"] for x in scene_rows)
    number = len(scene_rows)
    short_share = len(short) / number if number else 0.0
    per_thousand = 1000 * procedural_hits / words if words else 0.0
    advisories = []
    if not number:
        advisories.append("LIFE00: nenhuma cena com cabeçalho reconhecido")
    if len(days) >= 3 and number >= 9:
        advisories.append(
            "LIFE01: múltiplos dias e muitas cenas; revisar se cada dia foi VIVIDO "
            "por personagens, em vez de virar preparação do marco seguinte"
        )
    if number >= 8 and short_share >= 0.40:
        advisories.append(
            "LIFE02: pelo menos 40% das cenas são breves (<650 palavras); "
            "verificar cenas-chave comprimidas, não prolongar transições artificiais"
        )
    if words >= 3000 and per_thousand >= 5.0:
        advisories.append(
            "LIFE03: alta incidência de vocabulário operacional; "
            "verificar se a trama virou ata de reuniões/testes/checkpoints"
        )
    # Conjunction is an explicit *review risk*, not a grade or banned format.
    high_risk = (
        len(days) >= 3
        and number >= 9
        and short_share >= 0.40
        and per_thousand >= 5.0
    )
    if high_risk:
        advisories.append(
            "LIFE04: combinação multi-dia + fragmentação + linguagem operacional. "
            "Antes de entregar, editor deve conferir desenvolvimento humano, "
            "surpresa, conflito, convivência e tempo sentido, não apenas volume."
        )
    return {
        "status": "REVIEW_LIVED_EXPERIENCE" if high_risk else (
            "CHECK_EDITORIAL_SIGNALS" if advisories else "NO_STRUCTURAL_FLAGS"
        ),
        "source": "FULL_LITERAL_SCENE_TEXT_STRUCTURAL_HEURISTICS",
        "scene_count": number,
        "days_touched": days,
        "day_count": len(days),
        "scene_words_approx": words,
        "median_scene_words_approx": median(
            row["words_approx"] for row in scene_rows
        ) if scene_rows else 0,
        "short_scenes_under_650": short,
        "short_scene_share": round(short_share, 3),
        "dialogue_lines": dialogue,
        "lucas_dialogue_lines": lucas if not unattributed else None,
        "unlabeled_dialogue_lines": unattributed,
        "speaker_attribution_reliable": unattributed == 0,
        "procedural_word_hits": procedural_hits,
        "procedural_hits_per_1000_words": round(per_thousand, 2),
        "scene_signals": scene_rows,
        "advisories": advisories,
        "editorial_checks": [
            "Qual cena foi vivida pelo leitor, e não apenas concluída?",
            "O que Lucas quis, experimentou, sentiu e decidiu em cada cena central?",
            "Miren, amigos e NPCs viveram desejos próprios fora de relatórios?",
            "O dia saltou por decisão dramática ou para cumprir uma data planejada?",
            "O ponto alto recebeu tempo emocional antes e depois?",
            "O texto respirou sem enfraquecer GÊNESE ou negar acontecimentos?",
        ],
        "canon_changed": False,
        "literary_quality_certification": False,
        "semantic_certification": False,
        "reader_experience_certification": False,
    }
