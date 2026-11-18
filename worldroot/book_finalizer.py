"""Explicit author-approved final episode closes Livro V without fabricating a new choice.

The author selected option 5 on the PRECEDING part and explicitly requested
that the NEXT part end Livro V. This operation uses that authorization as an
independent book-end event (option 0 internally), never as a fictional future
selection. It commits the journal, HEAD, SQLite and context as one Git commit.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from .book_closure import require_book_end_approval
from .episode_pipeline import EpisodeDraft
from .git_cycle import (load, canonical, sha, verify_episode, verify_db, review_deltas,
                        _chronology, _closure, apply_closure_db, _save_snapshot,
                        load_corrections, write_context, VERSION)
from .ledger import GateError


def author_finale_choice(root: Path, episode_id: str) -> dict:
    approval = load(root / "author-approvals" / (episode_id + ".json"))
    require_book_end_approval(root, episode_id, approval["book"])
    return {
        "schema": "worldroot-author-book-finalize-v1",
        "episode_id": episode_id,
        "option": 0,
        "free_text": approval["author_quote"],
        "author_source": "USER_MESSAGE",
    }


def finalize_book(root: Path) -> dict:
    req_file = root / "canon" / "BOOK_END_REQUEST.json"
    if not req_file.is_file() or req_file.is_symlink():
        raise GateError("No explicit book-end request")
    req = load(req_file)
    episode_id = req.get("episode_id")
    if (req.get("schema") != "worldroot-book-end-request-v1"
            or req.get("book") != "Livro V"
            or req.get("author_source") != "USER_MESSAGE"
            or req.get("approval_path") != "author-approvals/" + str(episode_id) + ".json"):
        raise GateError("Invalid book-end request")
    approval = require_book_end_approval(root, episode_id, "Livro V")
    if approval["status"] != "EXPLICIT_AUTHOR_APPROVAL_VERIFIED":
        raise GateError("Book end author approval failed")
    approval_content = load(root / req["approval_path"])
    if req.get("previous_episode_id") != approval_content["previous_episode_id"]:
        raise GateError("Book ending previous episode differs from author choice")
    head = load(root / "canon" / "HEAD.json")
    if head.get("schema") != VERSION:
        raise GateError("No canonical operational HEAD")
    verify_db(root, head)
    if head.get("episode_id") == episode_id and head.get("book_closed") is True:
        return {"result": "BOOK_V_ALREADY_CLOSED", "episode_id": episode_id,
                "sequence": head["sequence"], "drive_changed": False}
    if head.get("episode_id") != req["previous_episode_id"] or head.get("book_closed") is True:
        raise GateError("Book finalization is not following the approved Part IV")
    draft, _ = verify_episode(root, episode_id)
    if (draft.metadata.get("book") != "Livro V"
            or draft.metadata.get("chapter") != 16
            or draft.metadata.get("part") != "V"
            or draft.metadata.get("canon_status") != "RASCUNHO"
            or draft.book_closed is not True):
        raise GateError("Final narrative has not been approved as Book V C16 Part V")
    _chronology(head, draft.metadata, prose=draft.prose)
    events, knowledge = review_deltas(root, episode_id, draft)
    choice = author_finale_choice(root, episode_id)
    closure = _closure(root, episode_id, head, choice, draft, events, knowledge)
    new_head = {
        "schema": VERSION, "sequence": closure["sequence"],
        "episode_id": episode_id, "day": draft.metadata["day"],
        "book": "Livro V", "chapter": 16, "part": "V",
        "hour": draft.metadata["hour"], "location": draft.metadata["location"],
        "source_sha256": closure["story_sha256"],
        "previous_head_sha256": closure["previous_head_sha256"],
        "closure_sha256": sha(canonical(closure)),
        "drive_head_status": "NAO_SINCRONIZADO",
        "engine_mode": "GITHUB_PRIVADO_SEM_OIDC",
        "book_closed": True,
    }
    journal = root / "canon" / "episodes" / (episode_id + ".json")
    if journal.exists():
        raise GateError("Book closure journal already exists but HEAD is not closed")
    with tempfile.TemporaryDirectory() as t:
        snapshot = Path(t) / "updated.sqlite"
        with sqlite3.connect(f"file:{root/'canon'/'state.sqlite'}?mode=ro", uri=True) as source:
            with sqlite3.connect(snapshot) as target:
                source.backup(target)
        with sqlite3.connect(snapshot) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            try:
                conn.execute("BEGIN IMMEDIATE")
                apply_closure_db(conn, closure, new_head,
                                 load_corrections(root, load))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            _save_snapshot(conn, root / "canon" / "state.sqlite")
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_bytes(canonical(closure))
    (root / "canon" / "HEAD.json").write_bytes(canonical(new_head))
    verify_db(root, new_head)
    write_context(root, new_head)
    return {"result": "LIVRO_V_FECHADO_CANONICAMENTE", "episode_id": episode_id,
            "sequence": new_head["sequence"],
            "source_sha256": closure["story_sha256"],
            "events": len(events), "knowledge": len(knowledge),
            "drive_changed": False}
