"""Evidence-bound temporal projection overrides without rewriting immutable story.

An older closure may carry an NPC-knowledge date equal to the final chapter day
even when the person learned the fact during a preceding day in the same text.
Corrections are keyed to exact event, person and source anchor and affect ONLY
the rebuildable SQLite/CONTEXT projections, never the signed source journal.
"""
from __future__ import annotations

from pathlib import Path

from .ledger import GateError

SCHEMA = "worldroot-temporal-reconciliation-v1"


def event_day(event: dict, episode_end_day: int) -> int:
    day = event.get("occurred_day", episode_end_day)
    if type(day) is not int or not 1 <= day <= episode_end_day:
        raise GateError("Invalid or future reviewed event day")
    return day


def load_corrections(root: Path, load_json) -> dict:
    path = root / "canon" / "temporal-reconciliation.json"
    if not path.exists():
        return {}
    data = load_json(path)
    if (not isinstance(data, dict) or data.get("schema") != SCHEMA
            or data.get("scope") != "PROJECTION_ONLY_NO_CANON_REWRITE"
            or not isinstance(data.get("corrections"), list)):
        raise GateError("Invalid protected temporal correction registry")
    out = {}
    for row in data["corrections"]:
        if not isinstance(row, dict):
            raise GateError("Invalid temporal correction record")
        key = (row.get("episode_id"), row.get("person"), row.get("source_event"))
        if (any(not isinstance(part, str) or not part for part in key)
                or key in out):
            raise GateError("Duplicate or unscoped temporal correction")
        original = row.get("recorded_acquired_day")
        corrected = row.get("corrected_acquired_day")
        source_day = row.get("source_event_day")
        if (any(type(v) is not int or v < 1 for v in (original, corrected, source_day))
                or not (source_day == corrected < original)
                or not isinstance(row.get("literal_anchor"), str)
                or len(row["literal_anchor"].strip()) < 8
                or type(row.get("source_line")) is not int
                or row["source_line"] < 1
                or not isinstance(row.get("reason"), str)
                or len(row["reason"]) < 30):
            raise GateError("Temporal correction lacks credible day and literal evidence")
        out[key] = row
    return out


def projected_knowledge_day(episode_id: str, record: dict, event: dict,
                            episode_end_day: int, corrections: dict) -> int:
    event_when = event_day(event, episode_end_day)
    original = record.get("acquired_day")
    if type(original) is not int or not (event_when <= original <= episode_end_day):
        raise GateError("Knowledge precedes source event or exceeds checkpoint")
    entry = corrections.get((episode_id, record.get("person"), record.get("source_event")))
    if entry is None:
        return original
    src = event.get("source")
    if (original != entry["recorded_acquired_day"]
            or event_when != entry["source_event_day"]
            or src is None or src.get("line") != entry["source_line"]
            or src.get("literal_anchor") != entry["literal_anchor"]):
        raise GateError("Temporal correction evidence no longer matches immutable event")
    return entry["corrected_acquired_day"]
