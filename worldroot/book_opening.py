"""Explicit Livro VI opening after the author closed Livro V.

A user-approved opening is an authorization to ARCHIVE the new book's draft,
not permission to fabricate a story, auto-select its continuation, or promote
an episode without a subsequent real author choice. The source is private.
"""
from __future__ import annotations
import re
from pathlib import Path
from .git_cycle import load
from .ledger import GateError

APPROVAL_FILE = "author-approvals/LVI-OPEN.json"
_SCHEMA = "worldroot-author-book-open-v1"
_OPEN = re.compile(r"(?i)\bvamos\s+come[cç]ar\s+um\s+livro\s+isekai\s+fenomenal\s+agora\b")


def require_book_open_approval(root: Path, previous: dict, metadata: dict) -> dict:
    if not isinstance(previous, dict) or previous.get("schema") != "worldroot-git-canon-v1":
        raise GateError("Missing trusted previous canonical HEAD")
    if not isinstance(metadata, dict):
        raise GateError("New book needs explicit metadata")
    if previous.get("book") != "Livro V" or previous.get("book_closed") is not True:
        raise GateError("Livro VI opening requires fully closed Livro V")
    if (metadata.get("book") != "Livro VI"
            or metadata.get("chapter") != 1 or metadata.get("part") != "I"):
        raise GateError("Approved opening is ONLY Livro VI C01 Parte I")
    approval = load(Path(root) / APPROVAL_FILE)
    if (approval.get("schema") != _SCHEMA
            or approval.get("project") != "CRONICAS_DE_UM_NOVO_MUNDO"
            or approval.get("approved") is not True
            or approval.get("author_source") != "USER_MESSAGE"
            or approval.get("previous_episode_id") != previous.get("episode_id")
            or approval.get("previous_sequence") != previous.get("sequence")
            or approval.get("previous_book") != "Livro V"
            or approval.get("next_book") != "Livro VI"
            or approval.get("previous_head_source_sha256") != previous.get("source_sha256")
            or approval.get("new_book_canon_head_written") is not False):
        raise GateError("Book opening not linked to actual author-approved closed HEAD")
    quote = approval.get("author_quote")
    if not isinstance(quote, str) or not _OPEN.search(quote):
        raise GateError("The author did not explicitly request Livro VI launch")
    return {
        "status": "AUTHOR_APPROVED_BOOK_VI_DRAFT_ONLY",
        "previous": previous["episode_id"], "book": "Livro VI",
        "canon_changed": False, "choice_recorded": False,
    }
