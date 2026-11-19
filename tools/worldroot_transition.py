"""WORLDROOT Cycle 1: explicit, idempotent user choice routing.

Does not touch canon HEAD or fabricate a user choice. A caller must supply the
verbatim USER_MESSAGE and expected current HEAD; GitHub is the only commit store.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from verify_lvi_original import verify_lvi
from validate_episode_archive import verify_one, ArchiveInvalid

PARTS = ("I", "II", "III", "IV", "V")
ID = re.compile(r"[A-Za-z0-9_-]{3,128}\Z")

def load(p: Path) -> dict:
    if not p.is_file() or p.is_symlink():
        raise ArchiveInvalid("Missing or unsafe file: " + str(p))
    item = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(item, dict):
        raise ArchiveInvalid("Expected object: " + str(p))
    return item

def encoded(obj: dict) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))+"\n").encode()

def write_once(p: Path, content: bytes):
    if p.exists():
        if not p.is_file() or p.is_symlink() or p.read_bytes() != content:
            raise ArchiveInvalid("Existing immutable choice differs: " + str(p))
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return True

def _adjacent(head: dict, meta: dict):
    if head.get("book_closed"):
        return head.get("book") == "Livro V" and head.get("day") == 537 and meta.get("book") == "Livro VI" and meta.get("chapter") == 1 and meta.get("part") == "I"
    if meta.get("book") != head.get("book"):
        return False
    hpart = head.get("part")
    if hpart not in PARTS:
        return False
    return (meta.get("chapter") == head.get("chapter") + (hpart == "V")
            and meta.get("part") == ("I" if hpart == "V" else PARTS[PARTS.index(hpart)+1])
            and type(meta.get("day")) is int
            and head.get("day") <= meta["day"] <= head.get("day")+1)

def route(root: Path, episode_id: str, option: int, free_text: str,
          *, expected_head: str, user_message: str) -> dict:
    if not ID.fullmatch(episode_id):
        raise ArchiveInvalid("Unsafe episode id")
    if not user_message.strip():
        raise ArchiveInvalid("Real user message evidence required, no assistant-inferred selection")
    if type(option) is not int or not 1 <= option <= 5:
        raise ArchiveInvalid("Option must be 1-5")
    if not isinstance(free_text, str) or len(free_text)>2048:
        raise ArchiveInvalid("Invalid free choice text")
    if option==5 and not free_text.strip():
        raise ArchiveInvalid("Option 5 requires user's exact free action")
    head = load(root/"canon/HEAD.json")
    if head.get("episode_id") != expected_head:
        raise ArchiveInvalid("Stale expected HEAD: refresh before committing user choice")
    if (root/"editorial/rejections"/(episode_id+".json")).exists():
        raise ArchiveInvalid("Author-rejected episode cannot be selected")
    base = root/"episodes"/episode_id
    meta = load(base/"draft/checkpoint_candidato.json")
    opts = json.loads((base/"draft/opcoes.json").read_text(encoding="utf-8"))
    if (not isinstance(opts,list) or len(opts)!=5
            or [v.get("number") for v in opts] != [1,2,3,4,5]
            or opts[3].get("is_special") is not True
            or opts[4].get("is_free") is not True):
        raise ArchiveInvalid("Five genuine story options required")
    if episode_id.startswith("LVI-"):
        check=verify_lvi(root,episode_id)
    else:
        check=verify_one(base/"draft/manifesto_imutavel.json")
    src_hash=check["sha256"]
    journal=root/"canon/episodes"/(episode_id+".json")
    if journal.is_file():
        if head["episode_id"]!=episode_id:
            raise ArchiveInvalid("Historical canonical episode cannot be selected as active HEAD")
        original=load(journal)
        if original.get("story_sha256")!=src_hash:
            raise ArchiveInvalid("Canon and source hashes differ")
        return {"route":"ALREADY_CANONICAL_NAVIGATION_ONLY",
                "episode_id":episode_id,"current_head":head["episode_id"],
                "source_sha256":src_hash,"record_path":"navigation/author_intents/"+episode_id+".json",
                "closes_canon":False,"requires_next_draft_alignment":True}
    if not _adjacent(head,meta):
        raise ArchiveInvalid("Draft is not adjacent to current canonical HEAD")
    review=load(base/"review/continuity_review.json") if episode_id.startswith("LVI-") else {}
    if review.get("open_flags"):
        raise ArchiveInvalid("Episode has open continuity flags; no silent choice closure")
    others = []
    for p in (root/"choices").glob("*/option-*.json"):
        if p.parent.name==episode_id or (root/"canon/episodes"/(p.parent.name+".json")).exists():
            continue
        others.append(p.parent.name)
    if others:
        raise ArchiveInvalid("Other pending unclosed choice: " + ",".join(sorted(set(others))))
    return {"route":"DRAFT_CHOICE_READY_FOR_CANON_WORKFLOW",
            "episode_id":episode_id,"current_head":head["episode_id"],
            "source_sha256":src_hash,"record_path":f"choices/{episode_id}/option-{option}.json",
            "closes_canon":False,"requires_next_draft_alignment":False}

def record(root: Path, episode_id: str, option: int, free_text: str,
           *, expected_head: str, user_message: str) -> dict:
    decision=route(root,episode_id,option,free_text,
                   expected_head=expected_head,user_message=user_message)
    if decision["route"]=="ALREADY_CANONICAL_NAVIGATION_ONLY":
        body={
            "schema":"worldroot-canonical-navigation-intent-v1",
            "episode_id":episode_id,"option":option,"free_text":free_text,
            "author_source":"USER_MESSAGE","verbatim_user_message":user_message,
            "source_sha256":decision["source_sha256"],
            "expected_head_episode_id":expected_head,
            "does_not_reclose_canon":True,
            "requires_next_draft_alignment":True
        }
    else:
        body={"schema":"worldroot-author-choice-v1",
              "episode_id":episode_id,"option":option,"free_text":free_text,
              "author_source":"USER_MESSAGE"}
    changed=write_once(root/decision["record_path"],encoded(body))
    return {**decision, "changed":changed, "next_action":
            "REVIEW_NAVIGATION_WITH_EXISTING_DRAFT" if "NAVIGATION" in decision["route"]
            else "COMMIT_CHOICE_TO_GITHUB_THEN_RUN_GIT_CANON_CYCLE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,default=Path("."))
    p.add_argument("--episode-id",required=True)
    p.add_argument("--option",required=True,type=int)
    p.add_argument("--free-text",default="")
    p.add_argument("--expected-head",required=True)
    p.add_argument("--user-message",required=True)
    p.add_argument("--record",action="store_true")
    a=p.parse_args()
    try:
        fn=record if a.record else route
        result=fn(a.archive_root,a.episode_id,a.option,a.free_text,
                  expected_head=a.expected_head,user_message=a.user_message)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    except (ArchiveInvalid,OSError,ValueError,KeyError,IndexError) as exc:
        print("WORLDROOT_CHOICE_ROUTING_BLOCKED:",str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
