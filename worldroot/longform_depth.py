"""WORLDROOT longform quality budget and completion readiness.

Length is a production criterion requested by the author, not a literary
grade. Does not generate prose, infer character knowledge, alter canon or pad.
New drafts below the safety floor are rejected before archiving; immutable old
drafts are exempt from retroactive rejection. Visual and semantic gates coexist.
"""
from __future__ import annotations

import re
from statistics import median

from .story_focus_audit import inspect_installment

WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+(?:[’'-][A-Za-zÀ-ÿ0-9]+)*")
DIL_TAG = re.compile(r"</?(?:box|row|col|grid|grid-item|text|title|caption|icon|button|textarea|divider|badge|spacer)(?:\s+[^>]+)?>", re.I)
BODY_BINDING = re.compile(r"(?m)^\s*\{@body[^\n]*")
SCENE_START = re.compile(r"(?m)^##\s+[IVX]{1,8}\s+[—–-]\s+[^\n]+$")
END_MARKER = re.compile(r"(?m)^\s*(?:\*\*)?FIM DA PARTE|^##\s+(?:LIVRO|WORLDROOT|CHECKPOINT)\b", re.I)
UI_CONTENT = re.compile(r"<(?:button|title|caption|text)\b[^>]*>.*?</(?:button|title|caption|text)>", re.I | re.S)
TARGET_WORDS = 10_000
AIM_LOW = 9_400
AIM_HIGH = 11_000
MIN_ARCHIVE_WORDS = 8_800
STATUS = "STRUCTURAL_PRODUCTION_SIGNAL_NOT_LITERARY_CERTIFICATION"


def count_prose_words(prose: str) -> int:
    """Approximate rendered language in narrative prose, not UI or choices."""
    if not isinstance(prose, str):
        raise TypeError("prose must be a string")
    headings = list(SCENE_START.finditer(prose))
    # Only the literary body of scenes counts. Header, calendar, checkpoint,
    # buttons and choices can never inflate the target.
    if not headings:
        return 0
    total = 0
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(prose)
        chunk = prose[heading.end():end]
        stop = END_MARKER.search(chunk)
        if stop:
            chunk = chunk[:stop.start()]
        chunk = UI_CONTENT.sub(" ", chunk)
        chunk = BODY_BINDING.sub(" ", DIL_TAG.sub(" ", chunk))
        total += len(WORD.findall(chunk))
    return total


def inspect_longform(prose: str, *, minimum: int = MIN_ARCHIVE_WORDS) -> dict:
    """A 10k-word authorial goal with a no-padding anti-gaming warning.

    This does not enforce a scene count or an hour quota. Scene quality, human
    motive, causality, pacing and truth all require human editorial inspection.
    """
    if not isinstance(prose, str) or not prose.strip():
        raise ValueError("Nonempty narrative prose required")
    if type(minimum) is not int or minimum <= 0:
        raise ValueError("Positive production minimum required")
    words = count_prose_words(prose)
    scenes = inspect_installment(prose)
    notices = list(scenes["advisories"])
    errors = []
    if words < minimum:
        errors.append(
            "LONGFORM01: narrative prose has "
            + str(words) + " words; new longform installments require at least "
            + str(minimum) + " (goal " + str(TARGET_WORDS)
            + "). Expand lived scenes and consequences; never repeat or pad."
        )
    elif words < AIM_LOW:
        notices.append(
            "LONGFORM01: below the 10000-word narrative target; "
            "revise depth and relationships before delivery"
        )
    elif words > AIM_HIGH:
        notices.append("LONGFORM01: review pacing; density is not proportional to word count")
    lengths = [s["words_approx"] for s in scenes["scenes"]]
    very_short = [s["scene"] for s in scenes["scenes"] if s["words_approx"] < 450]
    if len(very_short) >= 2 and len(lengths) >= 5:
        notices.append("LONGFORM02: multiple short scenes " + ", ".join(very_short)
                       + "; check emotional development and causality, do not append filler")
    return {
        "status": "EXPANDIR" if errors else ("REVISAR" if notices else "ALVO"),
        "signal": STATUS,
        "prose_words_approx": words,
        "target_words": TARGET_WORDS,
        "target_range": [AIM_LOW, AIM_HIGH],
        "archive_floor": minimum,
        "scene_count": scenes["scene_count"],
        "scene_words_approx": scenes["scene_words_approx"],
        "median_scene_words_approx": median(lengths) if lengths else 0,
        "lucas_dialogue_scene_share": scenes["lucas_dialogue_scene_share"],
        "very_short_scenes": very_short,
        "errors": errors,
        "notices": notices,
        "canon_changed": False,
        "semantic_certification": False,
        "output_capacity_certification": False,
    }
