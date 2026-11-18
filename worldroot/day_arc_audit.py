"""WORLDROOT advisory on the lived-day arc: daylight, transitions and closure.

This intentionally cannot decide that an author closed a day. It reads the
narrated scene clocks without editing the story, dates, choices or canonical
HEAD. It is not a quota, scheduler, word-count gate or literary judge.
"""
from __future__ import annotations

import re

SCENE = re.compile(r"(?m)^##\s+[IVX]{1,8}\s+[—–-]\s+[^\n]+$")
CLOCK = re.compile(r"(?i)\bDIA\s+(\d{1,4})\s*[·|—–-]\s*(\d{1,2})h(\d{2})\b")
STATUS = "EDITORIAL_ADVISORY_ONLY"


def _phase(hour: int) -> str:
    if 5 <= hour < 10:
        return "MANHA"
    if 10 <= hour < 17:
        return "DIA"
    if 17 <= hour < 21:
        return "ENTARDECER"
    return "NOITE_MADRUGADA"


def inspect_day_arc(prose: str) -> dict:
    """Summarize explicit temporal markers of scenes; leave the author in control."""
    if not isinstance(prose, str) or not prose.strip():
        raise ValueError("A nonempty installment is required")
    scenes = list(SCENE.finditer(prose))
    markers = []
    for n, scene in enumerate(scenes, 1):
        # Scene markers only: exclude options/calendar/checkpoint by limiting
        # the final scene to the first explicit end-of-part boundary.
        cut = scenes[n].start() if n < len(scenes) else len(prose)
        excerpt = prose[scene.end():cut]
        end = re.search(r"\*\*FIM DA PARTE\b|\bWORLDROOT\s*[·—–-]\s*CHECKPOINT\b", excerpt, re.I)
        if end:
            excerpt = excerpt[:end.start()]
        for c in CLOCK.finditer(excerpt):
            day, hour, minute = int(c.group(1)), int(c.group(2)), int(c.group(3))
            if day < 1 or hour > 23 or minute > 59:
                raise ValueError("Invalid scene date/time marker")
            markers.append({"scene": n, "day": day, "hour": f"{hour:02d}h{minute:02d}",
                            "minutes": day * 1440 + hour * 60 + minute,
                            "phase": _phase(hour)})
    chronological = all(x["minutes"] <= y["minutes"] for x, y in zip(markers, markers[1:]))
    first = markers[0] if markers else None
    last = markers[-1] if markers else None
    unique_days = list(dict.fromkeys(m["day"] for m in markers))
    advisories = []
    if not markers:
        advisories.append("Sem relógio explícito nas cenas; conferir ancoragem da passagem de tempo")
    elif not chronological:
        advisories.append("Relógio retrocedeu na sequência de cenas; conferir flashback ou cronologia")
    elif first["day"] == last["day"] and 5 <= int(first["hour"][:2]) < 10 and 15 <= int(last["hour"][:2]) < 19:
        advisories.append("Dia iniciado pela manhã e ainda na tarde/entardecer: a próxima escolha pode viver a noite antes de novo amanhecer")
    return {
        "status": STATUS,
        "source": "EXPLICIT_SCENE_CLOCKS_ONLY",
        "first": {"day": first["day"], "hour": first["hour"]} if first else None,
        "last": {"day": last["day"], "hour": last["hour"]} if last else None,
        "elapsed_minutes": last["minutes"] - first["minutes"] if last and first and chronological else None,
        "days_touched": unique_days,
        "chronological": chronological,
        "scene_clock_count": len(markers),
        "last_phase": last["phase"] if last else None,
        "advisories": advisories,
        "day_closure_certified": False,
        "new_author_choice_recorded": False,
        "canon_changed": False,
    }
