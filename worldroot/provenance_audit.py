"""Source-status gates for the 40-question WORLDROOT memory audit.

A green result validates provenance categories, baseline identity and presence
of source references. It NEVER proves that prose answers are semantically true.
No planning or hypothesis may acquire a CANONICO label from this audit.
"""
from __future__ import annotations

import json
from pathlib import Path

from .ledger import GateError

STATUS = frozenset({"CANONICO", "RASCUNHO", "PLANEJADO", "HIPOTESE", "NAO_CONFIRMADO"})
SOURCE_KIND = frozenset({
    "GITHUB_HEAD", "GITHUB_DRAFT", "GITHUB_REVIEW",
    "DRIVE_HOMOLOGADO", "DRIVE_NARRADO", "DRIVE_PLANEJAMENTO", "DRIVE_HIPOTESE",
})
SUPPORT = {
    "CANONICO": {"GITHUB_HEAD", "DRIVE_HOMOLOGADO", "DRIVE_NARRADO"},
    "RASCUNHO": {"GITHUB_DRAFT", "GITHUB_REVIEW"},
    "PLANEJADO": {"DRIVE_PLANEJAMENTO"},
    "HIPOTESE": {"DRIVE_HIPOTESE", "DRIVE_PLANEJAMENTO"},
    "NAO_CONFIRMADO": SOURCE_KIND,
}

def verify_quiz_contract(contract: dict, *, head: dict, draft_checkpoint: dict):
    if not isinstance(contract, dict) or contract.get("schema") != "worldroot-memory-audit-v1":
        raise GateError("Unknown memory-audit schema")
    reference = contract.get("head_reference")
    if not isinstance(reference, dict):
        raise GateError("Canonical HEAD reference required")
    if (type(reference.get("day")) is not int or not reference.get("episode_id")
            or type(reference.get("sequence")) is not int):
        raise GateError("HEAD reference fields missing")
    if not isinstance(head, dict):
        raise GateError("Canonical HEAD has no object")
    if (head.get("day"), head.get("episode_id"), head.get("sequence")) != (
        reference["day"], reference["episode_id"], reference["sequence"]
    ):
        # This is an old review, not a reason to revert the new HEAD.
        return {
            "state": "HISTORICO_HEAD_MUDOU", "expected_head": reference,
            "current_head": {
                "day": head.get("day"), "episode_id": head.get("episode_id"),
                "sequence": head.get("sequence"),
            },
            "canon_changed": False, "requires_new_audit": True,
        }

    draft_ref = contract.get("draft_reference")
    if (not isinstance(draft_ref, dict)
            or draft_checkpoint.get("canon_status") != "RASCUNHO"
            or draft_ref.get("day") != draft_checkpoint.get("day")
            or draft_ref.get("canon_status") != "RASCUNHO"):
        raise GateError("Draft D529 must not be declared canonical")
    questions = contract.get("questions")
    if not isinstance(questions, list) or len(questions) != 40:
        raise GateError("Exactly forty reviewed question entries required")
    nums = [q.get("number") for q in questions if isinstance(q, dict)]
    if nums != list(range(1, 41)):
        raise GateError("40 question IDs must be in sequence, with no omissions")
    counts = {s: 0 for s in STATUS}
    for item in questions:
        statuses = item.get("statuses")
        sources = item.get("sources")
        answer = item.get("answer")
        if (not isinstance(statuses, list) or not statuses
                or any(x not in STATUS for x in statuses)
                or len(set(statuses)) != len(statuses)):
            raise GateError("Every answer needs distinct explicit valid status")
        if not isinstance(answer, str) or len(answer.strip()) < 22:
            raise GateError("Every answer requires an independently useful summary")
        if not isinstance(sources, list) or not sources:
            raise GateError("Every answer must include real source references")
        kinds = set()
        for src in sources:
            if (not isinstance(src, dict)
                    or src.get("kind") not in SOURCE_KIND
                    or not isinstance(src.get("url"), str)
                    or not (src["url"].startswith("https://github.com/LucasRodrigues013/cronicas/")
                            or src["url"].startswith("https://docs.google.com/document/d/"))):
                raise GateError("Source must be an approved project resource URL with kind")
            kinds.add(src["kind"])
        for status in statuses:
            if not kinds.intersection(SUPPORT[status]):
                raise GateError(f"Question {item['number']}: {status} missing required source category")
            counts[status] += 1
        if "PLANEJADO" in statuses and "CANONICO" in statuses:
            raise GateError("Planned material cannot be labeled canonically narrated in one record")
        if "HIPOTESE" in statuses and "CANONICO" in statuses:
            raise GateError("Unproven interpretation cannot be canonical fact")
    return {
        "state": "STATUS_E_REFERENCIAS_VALIDOS_SEM_CERTIFICACAO_SEMANTICA",
        "head_day": head["day"],
        "checked_questions": len(questions),
        "status_counts": {key: counts[key] for key in sorted(counts)},
        "canon_changed": False,
        "semantic_certification": False,
    }


def read_and_verify(archive: Path, filename: Path):
    if filename.suffix != ".json" or filename.parent.resolve() != (archive / "audit" / "qa40").resolve():
        raise GateError("Audit contract must reside in private audit/qa40/*.json")
    if not filename.is_file() or filename.is_symlink():
        raise GateError("Cannot use unknown or symlinked QA file")
    contract = json.loads(filename.read_text(encoding="utf-8"))
    head = json.loads((archive / "canon" / "HEAD.json").read_text(encoding="utf-8"))
    draft_id = contract.get("draft_reference", {}).get("episode_id")
    if not isinstance(draft_id, str) or "/" in draft_id or ".." in draft_id:
        raise GateError("Unsafe draft identity")
    draft = json.loads((archive / "episodes" / draft_id / "draft" /
                        "checkpoint_candidato.json").read_text(encoding="utf-8"))
    return verify_quiz_contract(contract, head=head, draft_checkpoint=draft)
