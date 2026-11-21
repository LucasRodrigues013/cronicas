"""WORLDROOT: fail-closed gate ONLY for the prior episode actually selected.

The archive contains several future/noncanonical drafts. A flagged future
draft cannot block closing a distinct earlier approved one; conversely, a
valid older draft cannot excuse a flagged selected one. Never writes HEAD.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from verify_lvi_original import verify_lvi
from validate_episode_archive import ArchiveInvalid

REJECTED = "LVI-C01-PI-D538-AUTHOR-SOURCE"
PARTS = ("I", "II", "III", "IV", "V")


def data(path: Path):
    if not path.is_file() or path.is_symlink():
        raise ArchiveInvalid(f"Missing required file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise ArchiveInvalid(f"Invalid JSON: {path}") from exc


def selected_pending(root: Path) -> list[str]:
    result = []
    for p in sorted((root / "choices").glob("*/option-*.json")):
        episode = p.parent.name
        if not (root / "canon" / "episodes" / (episode + ".json")).exists():
            selected = data(p)
            if (selected.get("author_source") != "USER_MESSAGE"
                    or selected.get("episode_id") != episode
                    or type(selected.get("option")) is not int
                    or not 1 <= selected["option"] <= 5):
                raise ArchiveInvalid(f"Invalid real author choice: {p}")
            result.append(episode)
    return result


def _author_scoped_c02_pv_multiday_exception(root: Path, head: dict,
                                             meta: dict, source_sha256: str,
                                             episode: str) -> bool:
    """Permit only the exact author-ratified D546-D548 literary source."""
    if (episode != "LVI-C02-PV-D546-D548-AUTHOR-SOURCE"
            or head.get("episode_id") != "LVI-C02-PIV-D545-AUTHOR-SOURCE"
            or head.get("sequence") != 18 or head.get("day") != 545
            or head.get("chapter") != 2 or head.get("part") != "IV"
            or meta.get("book") != "Livro VI" or meta.get("chapter") != 2
            or meta.get("part") != "V" or meta.get("day") != 548
            or meta.get("hour") != "22h31"):
        return False
    path = root / "author-approvals/LVI-C02-PV-EXCECAO-CRONOLOGICA-PONTUAL-2026-11-20.json"
    approval = data(path)
    target = approval.get("target", {})
    return (approval.get("schema") == "worldroot-author-scoped-chronology-ratification-v1"
            and approval.get("authorization") == "USER_MESSAGE_CURRENT_TURN"
            and approval.get("approved_status") == "EXPLICIT_AUTHOR_DIRECTIVE_SCOPED_EXCEPTION"
            and target.get("episode_id") == episode
            and target.get("full_text_sha256") == source_sha256
            and target.get("prose_sha256") ==
                "893adea655b3bf6acd946655642ba6bb143c2b1c35aece8fcae359b2793f63ef"
            and target.get("days_narrated") == [546, 547, 548]
            and target.get("scene_count") == 27)


def verify_prior(root: Path) -> dict:
    head = data(root / "canon/HEAD.json")
    pending = selected_pending(root)
    if not pending:
        return {"status": "NO_NEW_CHOICE_NO_CANON_PROMOTION", "head": head["episode_id"]}
    if len(pending) != 1:
        raise ArchiveInvalid("One previous episode per closure: multiple pending author choices")
    episode = pending[0]
    if episode == REJECTED or (root / "editorial/rejections" / (episode + ".json")).exists():
        raise ArchiveInvalid("Rejected author episode cannot close")
    if not episode.startswith("LVI-"):
        return {"status": "LEGACY_EPISODE_DEFER_TO_PINNED_ENGINE", "selected": episode}
    gate = verify_lvi(root, episode)
    folder = root / "episodes" / episode
    m = data(folder / "draft/checkpoint_candidato.json")
    if m.get("canon_status") != "RASCUNHO" or m.get("book") != "Livro VI":
        raise ArchiveInvalid("Selected episode is not a Livro VI saved draft")
    if head.get("book_closed") is True:
        if not (head.get("book") == "Livro V" and head.get("day") == 537
                and m.get("day") == 538 and m.get("chapter") == 1 and m.get("part") == "I"):
            raise ArchiveInvalid("Book boundary not adjacent to archived prior episode")
    elif head.get("book") == "Livro VI":
        previous_chapter, previous_part = head["chapter"], head["part"]
        expect_chapter = previous_chapter + (previous_part == "V")
        expect_part = "I" if previous_part == "V" else PARTS[PARTS.index(previous_part)+1]
        one_off = _author_scoped_c02_pv_multiday_exception(
            root, head, m, gate["sha256"], episode)
        if (m.get("chapter") != expect_chapter or m.get("part") != expect_part
                or type(m.get("day")) is not int
                or not (head["day"] <= m["day"] <= head["day"] + 1 or one_off)):
            raise ArchiveInvalid("Selected previous episode is out of canonical order")
    else:
        raise ArchiveInvalid("Unknown canonical head book/closure state")

    cont = data(folder / "review/continuity_review.json")
    if cont.get("status") == "REVIEWED_WITH_FLAGS":
        evidence = root / "editorial/recovery/reconciliations" / (episode + ".json")
        decision = data(evidence)
        if (decision.get("status") != "APPROVED_BY_AUTHOR"
                or not decision.get("author_decision")
                or not decision.get("source_evidence")):
            raise ArchiveInvalid("Character continuity flags lack author-backed reconciliation")
    elif cont.get("status") != "REVIEWED_WITH_EVIDENCE":
        raise ArchiveInvalid("Pre-scene character continuity not reviewed")

    ev = data(folder / "review/eventos_revisados.json")
    kn = data(folder / "review/conhecimento_revisado.json")
    if (ev.get("review_status") != "REVISADO"
            or kn.get("review_status") != "REVISADO"):
        raise ArchiveInvalid("Previous episode event/knowledge review pending; no canon promotion")
    if ev.get("source_sha256") != gate["sha256"]:
        raise ArchiveInvalid("Reviewed event SHA256 does not match original")
    if not isinstance(ev.get("events"), list) or not ev["events"]:
        raise ArchiveInvalid("Selected episode has no reviewed events")
    source = (folder / "draft/narrativa_integral.md").read_text(encoding="utf-8").splitlines()
    for e in ev["events"]:
        if e.get("canon_status") != "NARRADO":
            raise ArchiveInvalid("Unresolved or non-narrated reviewed event cannot close")
        anchor = e.get("source") or {}
        line, excerpt = anchor.get("line"), anchor.get("literal_anchor")
        if (type(line) is not int or not 1 <= line <= len(source)
                or not isinstance(excerpt, str) or excerpt not in source[line-1]
                or anchor.get("sha256") != gate["sha256"]):
            raise ArchiveInvalid("Reviewed event evidence not exact")
    return {"status": "PRIOR_EPISODE_ELIGIBLE_FOR_ENGINE_CLOSURE",
            "previous_episode": episode, "current_head": head["episode_id"],
            "source_sha256": gate["sha256"], "narrated_events": len(ev["events"]),
            "does_not_promote": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive-root", type=Path, default=Path("."))
    args = p.parse_args()
    try:
        result = verify_prior(args.archive_root)
    except (ArchiveInvalid, OSError, KeyError, IndexError) as e:
        print("WORLDROOT CANON SEQUENCE BLOCKED:", str(e))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
