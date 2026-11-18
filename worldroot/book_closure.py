"""WORLDROOT: explicit author's book-ending instruction, tied to a real choice.

Only permits marking an episode book_closed when an independently stored
user-authored choice already contains that exact instruction.
Never fabricate an approval from narrative prose or a model-generated note.
"""
from __future__ import annotations

import re
from pathlib import Path

from .ledger import GateError
from .git_cycle import load

BOOK_END = re.compile(r"(?is)\bencerrar\s+o\s+livro\s+V\b")


def require_book_end_approval(root: Path, episode_id: str, book: str):
    path = root / "author-approvals" / (episode_id + ".json")
    if not path.is_file() or path.is_symlink():
        raise GateError("Author's explicit book-end approval artifact is missing")
    approval = load(path)
    if (approval.get("schema") != "worldroot-author-book-end-v1"
            or approval.get("episode_id") != episode_id
            or approval.get("book") != book
            or approval.get("approved") is not True
            or approval.get("author_source") != "USER_MESSAGE"):
        raise GateError("Invalid book end approval")
    previous = approval.get("previous_episode_id")
    expected = f"choices/{previous}/option-5.json"
    if (not isinstance(previous, str)
            or approval.get("choice_path") != expected):
        raise GateError("Book end must cite preceding author's free-choice file")
    choice_path = root / expected
    if not choice_path.is_file() or choice_path.is_symlink():
        raise GateError("Original author choice missing")
    choice = load(choice_path)
    quote = approval.get("author_quote")
    if (choice.get("schema") != "worldroot-author-choice-v1"
            or choice.get("episode_id") != previous
            or choice.get("option") != 5
            or choice.get("author_source") != "USER_MESSAGE"
            or not isinstance(quote, str)
            or quote != choice.get("free_text")
            or not BOOK_END.search(quote)):
        raise GateError("No matched explicit request to end Livro V")
    return {"status": "EXPLICIT_AUTHOR_APPROVAL_VERIFIED", "episode_id": episode_id,
            "choice_path": expected, "book": book}
