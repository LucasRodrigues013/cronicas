"""Private, opt-in longform segment verification for extended ChatGPT output.

Segments are authored in separate conversation turns, saved explicitly through
the authenticated GitHub connector under story-archive/production/<episode>/.
No automatic ChatGPT save, no AI text generation, no canon promotion. The final
inbox includes exact prose and segment receipts. This module verifies provenance.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .ledger import GateError

_SHA = re.compile(r"^[a-f0-9]{64}$")


def verify_longform_segments(root: Path, episode_id: str, payload: dict) -> dict:
    segments = payload.get("longform_segments")
    if segments is None:
        return {"status": "DIRECT_SINGLE_PROSE", "parts": 0, "verified": False}
    if not isinstance(segments, list) or not 2 <= len(segments) <= 6:
        raise GateError("Longform segmentation requires 2..6 immutable stage files")
    prose = payload.get("prose")
    if not isinstance(prose, str):
        raise GateError("Segmented chapter needs literal prose")
    concat = []
    for idx, record in enumerate(segments, 1):
        if not isinstance(record, dict):
            raise GateError("Invalid longform segment receipt")
        part = record.get("part")
        path = record.get("path")
        checksum = record.get("sha256")
        expected = f"production/{episode_id}/segments/{idx:02d}.md"
        if (type(part) is not int or part != idx or path != expected
                or not isinstance(checksum, str) or not _SHA.fullmatch(checksum)):
            raise GateError("Invalid or reordered longform source path/checksum")
        target = root / expected
        if not target.is_file() or target.is_symlink():
            raise GateError("Missing or unsafe private longform stage file")
        content = target.read_bytes()
        if len(content) > 350_000:
            raise GateError("Oversized longform segment")
        if hashlib.sha256(content).hexdigest() != checksum:
            raise GateError("Longform stage checksum mismatch")
        try:
            concat.append(content.decode("utf-8", errors="strict"))
        except UnicodeDecodeError:
            raise GateError("Longform stage is not UTF-8") from None
    if "".join(concat) != prose:
        raise GateError("Saved longform segments do not exactly reassemble narrative prose")
    return {"status": "STAGED_PROSE_SHA256_VERIFIED", "parts": len(segments),
            "verified": True, "canon_changed": False}
