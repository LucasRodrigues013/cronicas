"""Advisory, low-overhead narrative focus/density comparison for WORLDROOT.

Measures structural signals only. Cannot judge prose quality, point of view,
narrative truth, mysteries or the author's intent. Never auto-rewrites content,
updates canon or imposes a minimum chapter length.
"""
from __future__ import annotations

import re
from statistics import median

SCENE = re.compile(r"(?m)^##\s+([IVX]{1,8})\s+[—–-]\s+([^\n]+)$")
LUCAS_SPEAKS = re.compile(r"(?mi)^\s*\*\*LUCAS\s*[—–-]\*\*")
TEXT_WORD = re.compile(r"[A-Za-zÀ-ÿ0-9]+(?:['’\-][A-Za-zÀ-ÿ0-9]+)*")
PRESENTATION_TAG = re.compile(r"</?(?:box|row|col|grid|grid-item|text|title|caption|icon|button|textarea|divider|badge|spacer)(?:\s+[^>]+)?>", re.I)
SCRIPT_LINE = re.compile(r"(?m)^\s*\{@body\b[^\n]*")
NON_SCENE = re.compile(r"(?mi)^##\s+(?:LIVRO|WORLDROOT|CHECKPOINT)\b")
CLOCK = re.compile(r"(?i)\bDIA\s+(\d+)\s*[·—–-]\s*(\d{1,2})h(\d{2})\b")

# Empirical, approximate scene metrics taken from the full archived Part II,
# not a mandatory length quota. The final section may include the end checkpoint.
REFERENCE_II = {
    "episode": "LV-C15-PII-D529-AUTHOR-SOURCE",
    "scene_count": 9,
    "median_scene_words_approx": 1019,
    "scene_words_approx": 9481,
    "lucas_dialogue_scenes": 7,
    "lucas_dialogue_scene_share": 7 / 9,
}
STATUS = "ADVISORY_ONLY_NON_CANONICAL"


def _word_count(block: str) -> int:
    visible = PRESENTATION_TAG.sub(" ", block)
    visible = SCRIPT_LINE.sub(" ", visible)
    return len(TEXT_WORD.findall(visible))


def inspect_installment(text: str) -> dict:
    """Report bounded measurements; no connector, database or heavyweight NLP."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Non-empty chapter text required")
    matches = list(SCENE.finditer(text))
    scenes = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end]
        stop = NON_SCENE.search(chunk)
        if stop:
            chunk = chunk[:stop.start()]
        # Closing label is not a scene; preserve original raw text.
        for phrase in ("**FIM DA PARTE", "FIM DA PARTE"):
            p = chunk.find(phrase)
            if p >= 0:
                chunk = chunk[:p]
                break
        count = _word_count(chunk)
        speakers = len(LUCAS_SPEAKS.findall(chunk))
        clocks = CLOCK.findall(chunk)
        scenes.append({
            "scene": match.group(1),
            "title": match.group(2).strip(),
            "words_approx": count,
            "lucas_dialogue_lines": speakers,
            "lucas_speaks": speakers > 0,
            "clock_mentions": [{"day": int(d), "time": f"{int(h):02d}h{int(m):02d}"}
                               for d, h, m in clocks if int(h) < 24 and int(m) < 60],
        })
    words = [sc["words_approx"] for sc in scenes]
    focus = sum(sc["lucas_speaks"] for sc in scenes)
    total = sum(words)
    reference = REFERENCE_II
    alerts = []
    if not scenes:
        alerts.append("No I/II/III scene headers recognized; manual literary check")
    else:
        if median(words) < 0.70 * reference["median_scene_words_approx"] and len(scenes) >= 5:
            alerts.append("Scenes are noticeably more compressed than Part II; review lived moments, dialogue and consequences")
        if focus / len(scenes) < 0.70:
            alerts.append("Many scenes lack Lucas dialogue; review protagonist focalization and off-screen interludes")
        if len(scenes) >= 5 and total < 0.60 * reference["scene_words_approx"]:
            alerts.append("Narrative scene volume substantially below the Part II reference; review depth, not a word quota")
    return {
        "status": STATUS,
        "source": "FULL_VISIBLE_CHAPTER_WITH_SCENE_SPLIT",
        "reference": reference["episode"],
        "scenes": scenes,
        "scene_count": len(scenes),
        "scene_words_approx": total,
        "median_scene_words_approx": median(words) if words else 0,
        "lucas_dialogue_scenes": focus,
        "lucas_dialogue_scene_share": round(focus / len(scenes), 3) if scenes else 0,
        "advisories": alerts,
        "canon_changed": False,
        "semantic_certification": False,
        "literary_quality_certification": False,
    }
