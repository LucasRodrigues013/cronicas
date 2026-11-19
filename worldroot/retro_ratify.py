"""Limited, explicit author ratification of three immutable Livro VI originals.

This is NOT a generic shortcut around user choices. It runs only for the fixed
three recovered episodes, on a real user-written one-time request. The first
two episodes retain the actual historical option-4 messages in the export; the
third has no fictional option selected and receives a distinct '0 = ratified'
envelope. All three closures, HEAD, CONTEXT and SQLite must be pushed as ONE
atomic Git commit by the authenticated caller, never from a chat claim.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from .git_cycle import (
    VERSION, _chronology, _closure, _save_snapshot, apply_closure_db,
    canonical, load, review_deltas, sha, verify_db, verify_episode,
    write_context,
)
from .book_opening import require_book_open_approval
from .ledger import GateError
from .temporal_projection import load_corrections

REQUEST = Path("author-approvals/LVI-C01-D538-D539-RATIFICATION-20261119.json")
EXPORT = Path("history/source_exports/ChatGPT-CRONICAS_DE_UM_NOVO_MUNDO_9-20261119-1028.txt")
AUTHOR_QUOTE = (
    "Salve os 3 capítulos como cânone e não mais rascunho. "
    "E me traga as últimas 4 opções atualizadas pra continuarmos."
)
ORIGINAL_SHA = "ac693e60ec6e9dfef2ffee6fc423641541cb52fd53bbd7ffebc9691822be95f9"
PRIOR_HEAD = "LV-C16-PV-D537-AUTHOR-SOURCE"
PARTS = (
    {
        "id": "LVI-C01-PI-D538-REAUTHORIZED-R2-AUTHOR-SOURCE",
        "day": 538, "part": "I",
        "sha": "fd6aa23fa1ea5e929d81e0aaebc7776ca30a697120f20d310f9b3fd1f25f98ee",
        "lines": (357, 4043), "prompt_lines": (4048, 4058), "option": 4,
    },
    {
        "id": "LVI-C01-PII-D538-AUTHOR-SOURCE",
        "day": 538, "part": "II",
        "sha": "69be6e8eb86e68718c3eccdb823456a0e913816f94e1ca607ff44dc37d9eb740",
        "lines": (4089, 8451), "prompt_lines": (8456, 8460), "option": 4,
    },
    {
        "id": "LVI-C01-PIII-D539-AUTHOR-SOURCE",
        "day": 539, "part": "III",
        "sha": "74bb2ae185f21262a292d1a48e2c75e703d8ee92659f43f97c39d0174c2fd2e7",
        "lines": (8481, 12185), "prompt_lines": None, "option": 0,
    },
)
CAEDREN_FILE = Path(
    "editorial/recovery/reconciliations/LVI-C01-PIII-D539-AUTHOR-SOURCE.json"
)


def _source_lines(root: Path) -> list[str]:
    path = root / EXPORT
    if not path.is_file() or path.is_symlink():
        raise GateError("Missing user-provided original ChatGPT export")
    raw = path.read_bytes()
    if sha(raw) != ORIGINAL_SHA:
        raise GateError("Original user export bytes changed; ratification refused")
    return raw.decode("utf-8").splitlines()


def _request(root: Path) -> dict:
    req = load(root / REQUEST)
    if (req.get("schema") != "worldroot-explicit-three-episode-ratification-v1"
            or req.get("project") != "CRONICAS_DE_UM_NOVO_MUNDO"
            or req.get("author_source") != "USER_MESSAGE"
            or req.get("approval") != "RATIFY_EXACT_THREE_EPISODES"
            or req.get("author_quote") != AUTHOR_QUOTE
            or req.get("original_export_sha256") != ORIGINAL_SHA
            or req.get("previous_head_id") != PRIOR_HEAD
            or req.get("episodes") != [
                {"id": item["id"], "source_sha256": item["sha"]} for item in PARTS
            ]
            or req.get("does_not_infer_choice_on_part_III") is not True
            or req.get("preserve_narrative_literals") is not True):
        raise GateError("No valid explicit author ratification of exactly these three episodes")
    return req


def author_ratification_choice(root: Path, episode_id: str) -> dict:
    """Read authenticated intent; NEVER synthesize Part III's future choice."""
    _request(root)
    lines = _source_lines(root)
    item = next((v for v in PARTS if v["id"] == episode_id), None)
    if item is None:
        raise GateError("This authorization cannot ratify another episode")
    if item["prompt_lines"]:
        first, last = item["prompt_lines"]
        direct = "\n".join(lines[first-1:last]).strip()
        if not direct.startswith("Vamos de ação 4."):
            raise GateError("Prior option 4 is not evidenced by original chat source")
        loc = f"{EXPORT}#L{first}-L{last}"
    else:
        direct = AUTHOR_QUOTE
        loc = str(REQUEST)
    return {
        "schema": "worldroot-author-retro-ratification-v1",
        "episode_id": episode_id,
        "option": item["option"],
        "free_text": direct,
        "author_source": "USER_MESSAGE",
        "source_locator": loc,
    }


def _continuity_reconciled(root: Path, item: dict) -> None:
    review = load(root / "episodes" / item["id"] / "review/continuity_review.json")
    if item["part"] != "III":
        if review.get("status") != "REVIEWED_WITH_EVIDENCE" or review.get("open_flags"):
            raise GateError("Unexpected unresolved prior-character conflict")
        return
    if (review.get("status") != "REVIEWED_WITH_FLAGS"
            or review.get("open_flags") != ["CAEDREN_ROLE_LOCATION"]):
        raise GateError("D539 Caedren original discrepancy was not retained")
    decision = load(root / CAEDREN_FILE)
    if (decision.get("schema") != "worldroot-author-ratified-uncertainty-v1"
            or decision.get("issue") != "CAEDREN_ROLE_LOCATION"
            or decision.get("status") != "APPROVED_BY_AUTHOR_FOR_LITERAL_CANON"
            or decision.get("approval_file") != str(REQUEST)
            or decision.get("episode_id") != item["id"]
            or decision.get("source_evidence") != [
                "Varo estava corrigindo a posição de um legionário quando Caedren apareceu."
            ]
            or decision.get("physical_presence_in_D539_prose") is not True
            or decision.get("military_affiliation_proven") is not False
            or decision.get("travel_route_proven") is not False
            or decision.get("legion_command_assumed") is not False):
        raise GateError("Caedren literal presence / unproved allegiance not transparently reconciled")


def ratify(root: Path) -> dict:
    """Atomically prepare all three journal entries and SQLite on working tree."""
    _request(root)
    source_lines = _source_lines(root)
    head = load(root / "canon/HEAD.json")
    verify_db(root, head)
    closure_paths = [
        root / "canon/episodes" / (p["id"] + ".json") for p in PARTS
    ]
    if all(p.is_file() for p in closure_paths):
        if (head["episode_id"] == PARTS[-1]["id"] and head["sequence"] == 12):
            return {"result": "IDEMPOTENT_THREE_EPISODES_ALREADY_RATIFIED",
                    "head": head["episode_id"], "sequence": head["sequence"]}
        raise GateError("Existing ratifications do not match canonical HEAD")
    if any(p.exists() for p in closure_paths):
        raise GateError("Partial prior ratification; requires investigation, no overwrite")
    if (head["sequence"] != 9 or head["episode_id"] != PRIOR_HEAD
            or head["book"] != "Livro V" or head["book_closed"] is not True):
        raise GateError("Historical ratification cannot be applied to a different live HEAD")
    choices_dir = root / "choices"
    if any(p.parent.name in {x["id"] for x in PARTS}
           for p in choices_dir.glob("*/option-*.json")):
        raise GateError("Conflicting episode choice already exists; stop")

    work = []
    for item in PARTS:
        ident = item["id"]
        a, b = item["lines"]
        exact = ("\n".join(source_lines[a-1:b]) + "\n").encode("utf-8")
        if sha(exact) != item["sha"]:
            raise GateError("User export slice integrity failed for " + ident)
        origin = root / "editorial/recovery/originals" / (ident + ".txt")
        if not origin.is_file() or origin.read_bytes() != exact:
            raise GateError("Archived original is missing/differs: " + ident)
        draft, manifest = verify_episode(root, ident)
        if sha(draft.full_text.encode("utf-8")) != item["sha"]:
            raise GateError("Immutable draft cannot be reworded while ratifying")
        if (draft.metadata["book"] != "Livro VI"
                or draft.metadata["day"] != item["day"]
                or draft.metadata["part"] != item["part"]
                or draft.metadata["canon_status"] != "RASCUNHO"):
            raise GateError("Episode chronology/identity is not the approved draft")
        _continuity_reconciled(root, item)
        events, knowledge = review_deltas(root, ident, draft)
        choice = author_ratification_choice(root, ident)
        if choice["option"] != item["option"]:
            raise GateError("Ratification selection differs from original user message")
        work.append((item, draft, choice, events, knowledge))
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "updated.sqlite"
        with sqlite3.connect(f"file:{root / 'canon/state.sqlite'}?mode=ro", uri=True) as origin:
            with sqlite3.connect(dest) as target:
                origin.backup(target)
        new_head = head
        receipts = []
        with sqlite3.connect(dest) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            for item, draft, choice, events, knowledge in work:
                opening = new_head.get("book_closed") is True
                if opening:
                    require_book_open_approval(root, new_head, draft.metadata)
                _chronology(new_head, draft.metadata, prose=draft.prose,
                            book_open_approval_verified=opening)
                closure = _closure(root, item["id"], new_head, choice, draft, events, knowledge)
                receipt = {
                    "schema": VERSION, "sequence": closure["sequence"],
                    "episode_id": item["id"], "day": draft.metadata["day"],
                    "book": draft.metadata["book"], "chapter": draft.metadata["chapter"],
                    "part": draft.metadata["part"], "hour": draft.metadata["hour"],
                    "location": draft.metadata["location"],
                    "source_sha256": closure["story_sha256"],
                    "previous_head_sha256": closure["previous_head_sha256"],
                    "closure_sha256": sha(canonical(closure)),
                    "drive_head_status": "NAO_SINCRONIZADO",
                    "engine_mode": "GITHUB_PRIVADO_SEM_OIDC",
                    "book_closed": False,
                }
                apply_closure_db(conn, closure, receipt, load_corrections(root, load))
                new_head = receipt
                receipts.append((item, closure))
            conn.commit()
            _save_snapshot(conn, root / "canon/state.sqlite")
        for item, closure in receipts:
            file = root / "canon/episodes" / (item["id"] + ".json")
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(canonical(closure))
        (root / "canon/HEAD.json").write_bytes(canonical(new_head))
        write_context(root, new_head)
        verified = verify_db(root, new_head)
    return {"result": "AUTHOR_RATIFIED_THREE_VERBATIM_EPISODES",
            "old_sequence": head["sequence"], "sequence": new_head["sequence"],
            "head": new_head["episode_id"], "sqlite": verified,
            "canonical_source_sha256": [v["sha"] for v in PARTS],
            "narratives_rewritten": False, "drive_changed": False}


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", type=Path, required=True)
    args = p.parse_args(argv)
    result = ratify(args.archive_root.resolve())
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    from .ledger import ConflictError
    try:
        raise SystemExit(main())
    except (GateError, ConflictError, OSError, sqlite3.Error, KeyError, ValueError) as exc:
        print(f"WORLDROOT_RETRO_RATIFICATION_BLOCKED: {type(exc).__name__}: {str(exc)[:300]}")
        raise SystemExit(1)
