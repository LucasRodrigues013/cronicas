"""R25 writer-room compass; never narrator text, canon facts or story generation."""
from __future__ import annotations

SCHEMA = "worldroot-narrative-direction-v1"


def validate_direction(head: dict, direction: dict | None) -> dict:
    if not isinstance(head, dict) or not head.get("episode_id"):
        raise ValueError("Live canonical HEAD is required")
    errors = []
    if not isinstance(direction, dict) or direction.get("schema") != SCHEMA:
        return {"errors": ["R25_DIRECTOR: missing direction"], "ready": False}
    if direction.get("source_episode_id") != head["episode_id"]:
        errors.append("R25_DIRECTOR: source is not the current HEAD")
    for key, minimum in (("author_choice", 12), ("reader_promise", 28),
                         ("lucas_lived_focus", 28), ("central_change", 22)):
        v = direction.get(key)
        if not isinstance(v, str) or len(v.strip()) < minimum:
            errors.append("R25_DIRECTOR: insufficient " + key)
    world = direction.get("independent_world")
    if not isinstance(world, list) or not 1 <= len(world) <= 3 or any(
        not isinstance(v, str) or len(v.strip()) < 12 for v in world
    ):
        errors.append("R25_DIRECTOR: one to three causal independent beats required")
    unknown = direction.get("unknowns_preserved")
    if not isinstance(unknown, list) or not unknown or any(
        not isinstance(v, str) or len(v.strip()) < 8 for v in unknown
    ):
        errors.append("R25_DIRECTOR: preserve actual unknowns")
    if direction.get("does_not_choose_for_lucas") is not True:
        errors.append("R25_DIRECTOR: do not preselect author decisions")
    return {"errors": errors, "ready": not errors,
            "head_episode_id": head["episode_id"],
            "canon_changed": False, "fiction_content": False}


def private_direction_brief(head: dict, direction: dict) -> str:
    checked = validate_direction(head, direction)
    if checked["errors"]:
        raise ValueError("; ".join(checked["errors"]))
    return "\n".join((
        "WORLDROOT R25 — PRIVATE WRITER ROOM (never render in prose)",
        "HEAD: " + head["episode_id"],
        "CHOICE: " + direction["author_choice"],
        "READER PROMISE: " + direction["reader_promise"],
        "LUCAS LIVES: " + direction["lucas_lived_focus"],
        "SCENE TURN: " + direction["central_change"],
        "INDEPENDENT WORLD: " + " | ".join(direction["independent_world"]),
        "NOT YET KNOWN: " + " | ".join(direction["unknowns_preserved"]),
        "Labeled voices; full scenes; humor, affection; GÊNESE intact; five choices.",
    ))
