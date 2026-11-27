"""Public-code tracked-path guard; no private payload reads or names in output.

Detects accidental path custody regressions, not confidentiality, content leaks,
repository visibility, or trusted-branch enforcement. CI runs after publication.
"""
from __future__ import annotations

import json
import subprocess
import unicodedata
from collections import Counter

RESERVED_NAMESPACES = frozenset({
    "private", "runtime", "archive", "story-archive", "episodes", "inbox",
    "canon", "preparations", "requests", "production", "choices", "receipts",
    "editorial", "gold", "heldout", "held-out", "held_out", "reserved", "sealed",
})
RESERVED_BASENAMES = frozenset({
    "narrativa_integral.md", "manifesto_imutavel.json", "episode_draft.json",
    "checkpoint_candidato.json", "opcoes.json", "eventos_e_consequencias.json",
    "eventos_revisados.json", "conhecimento_revisado.json",
    "preparation_r33.json", "memory_r32.json", "head.json", "context.json",
    "engine_publishing_policy.json",
})
RESERVED_SUFFIXES = (
    ".db", ".sqlite", ".sqlite-wal", ".sqlite-shm", ".sqlite3", ".db-wal",
    ".db-shm", ".zip", ".txt", ".pem", ".key",
)


def classify_path(path):
    if not isinstance(path, str) or not path or any(
            unicodedata.category(c) in ("Cc", "Cf", "Cs") for c in path):
        return "UNSAFE_PATH"
    normalized = unicodedata.normalize("NFKC", path).casefold().replace("\\", "/")
    parts = normalized.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return "UNSAFE_PATH"
    if any(p in RESERVED_NAMESPACES for p in parts[:-1]):
        return "RESERVED_NAMESPACE"
    base = parts[-1]
    if (base in RESERVED_BASENAMES or ".env" in base
            or base.endswith(RESERVED_SUFFIXES)):
        return "RESERVED_FILENAME"
    return None


def scan_paths(paths):
    counts = Counter()
    total = 0
    for path in paths:
        total += 1
        category = classify_path(path)
        if category:
            counts[category] += 1
    if not total:
        counts["EMPTY_INDEX"] += 1
    return {"schema": "worldroot-public-path-guard-v1",
            "scope": "TRACKED_PATHS_ONLY_NOT_CONTENT",
            "tracked_count": total, "blocked_count": sum(counts.values()),
            "blocked_categories": dict(sorted(counts.items())),
            "public_path_check_passed": not counts,
            "confidentiality_certified": False}


def main():
    try:
        raw = subprocess.check_output(["git", "ls-files", "-z"])
        if not raw or not raw.endswith(b"\0"):
            raise ValueError("Unsafe index framing")
        paths = raw[:-1].decode("utf-8", errors="strict").split("\0")
        report = scan_paths(paths)
    except (OSError, subprocess.SubprocessError, ValueError):
        report = scan_paths([])
    print(json.dumps(report, sort_keys=True))
    return 0 if report["public_path_check_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
