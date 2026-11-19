"""WORLDROOT Cycle 3: second-stage seal AFTER all five parts are canonical.

The draft-level chapter ZIP is immutable. A separate seal references the final
five canonical journals without mutating the original prose or provisional ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from chapter_drive_publisher import chapter_key, ChapterError
from github_chapter_publisher import publish, get_json, write_once, sha
from validate_episode_archive import verify_one
from verify_lvi_original import verify_lvi

PARTS=("I","II","III","IV","V")
def enc(v)->bytes:
    return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

def seal(root:Path,book:str,chapter:int,*,check_only=False)->dict:
    key=chapter_key(book,chapter)
    chapter_dir=root/"chapters"/key
    receipt_path=root/"delivery/github_chapters"/(key+".json")
    if not receipt_path.is_file():
        if check_only:
            # Fully canonical chapter without package can be checked through
            # publisher in CI; actual seal will first create its durable package.
            preview=publish(root,book,chapter,check_only=True)
            if preview["status"]=="WAITING_FOR_FIVE_COMPLETE_PARTS":
                return {"status":"WAITING_FOR_FIVE_PARTS","chapter_key":key}
            return {"status":"READY_TO_PACKAGE_AND_SEAL","chapter_key":key}
        result=publish(root,book,chapter)
        if result["status"]=="WAITING_FOR_FIVE_COMPLETE_PARTS":
            return {"status":"WAITING_FOR_FIVE_PARTS","chapter_key":key}

    receipt=get_json(receipt_path)
    manifest=get_json(chapter_dir/(key+"-MANIFESTO.json"))
    if (receipt.get("schema")!="worldroot-github-private-chapter-v1"
            or manifest.get("chapter_key")!=key or manifest.get("part_count")!=5
            or manifest.get("publication")!="GITHUB_PRIVATE_ONLY_NO_CANON_PROMOTION"):
        raise ChapterError("No valid original five-part GitHub package")
    for item in receipt.get("artifacts",[]):
        path=root/item["path"]
        if (not path.is_file() or path.is_symlink()
                or path.stat().st_size!=item["bytes"]
                or sha(path.read_bytes())!=item["sha256"]):
            raise ChapterError("Chapter stored artifact mismatch: "+item["path"])
    full=(chapter_dir/(key+"-INTEGRAL.md")).read_bytes()
    if sha(full)!=manifest.get("combined_sha256") or len(full)!=manifest.get("combined_bytes"):
        raise ChapterError("Chapter prose differs from original manifest")
    zip_bytes=(chapter_dir/(key+"-ARQUIVO.zip")).read_bytes()
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as bundle:
            for name, proof in manifest.get("archive_entries",{}).items():
                source=bundle.read(name)
                if sha(source)!=proof["sha256"] or len(source)!=proof["bytes"]:
                    raise ChapterError("Chapter ZIP source hash mismatch: "+name)
    except (zipfile.BadZipFile,KeyError,ValueError) as exc:
        raise ChapterError("Invalid chapter ZIP") from exc
    rows=manifest.get("parts")
    if not isinstance(rows,list) or [x.get("part") for x in rows]!=list(PARTS):
        raise ChapterError("Chapter must include Part I–V in exact order")
    approved=[]
    for idx,part in enumerate(rows):
        eid=part.get("episode_id")
        j=get_json(root/"canon/episodes"/(eid+".json"))
        meta=get_json(root/"episodes"/eid/"draft/checkpoint_candidato.json")
        verified=verify_lvi(root,eid) if eid.startswith("LVI-") else verify_one(
            root/"episodes"/eid/"draft/manifesto_imutavel.json")
        if (j.get("status")!="FECHADO_GITHUB"
                or j.get("episode_id")!=eid
                or j.get("story_sha256")!=part.get("literal_sha256")
                or verified["sha256"]!=j["story_sha256"]
                or any(meta.get(k)!=v for k,v in
                       (("book",book),("chapter",chapter),("part",PARTS[idx])))):
            raise ChapterError("Part not canonically reconciled: "+str(eid))
        if idx:
            previous=approved[-1]
            if (j.get("sequence")!=previous["sequence"]+1
                    or j.get("previous_episode_id")!=previous["episode_id"]):
                raise ChapterError("Non-contiguous chapter canonical journal")
        approved.append({
            "episode_id":eid,"part":PARTS[idx],"sequence":j["sequence"],
            "story_sha256":j["story_sha256"],"canon_journal_sha256":sha(enc(j)),
            "journal_path":"canon/episodes/"+eid+".json",
        })
    head=get_json(root/"canon/HEAD.json")
    if head.get("sequence",0)<approved[-1]["sequence"]:
        raise ChapterError("Canonical HEAD cannot predate chapter's final journal")
    status={
        "schema":"worldroot-fully-sealed-canonical-chapter-v1",
        "chapter_key":key,"book":book,"chapter":chapter,
        "status":"ALL_FIVE_PARTS_CANONICAL_SOURCE_AND_ZIP_VERIFIED",
        "combined_sha256":manifest["combined_sha256"],
        "parts":approved,
        "provisional_package_sha256":sha((chapter_dir/(key+"-MANIFESTO.json")).read_bytes()),
        "chapter_zip_sha256":sha(zip_bytes),
        "canon_not_changed_by_seal":True,
        "drive_not_changed":True,
        "semantic_flags_not_silently_resolved":True,
    }
    if not check_only:
        write_once(chapter_dir/"CANONICAL_SEAL.json",enc(status))
        write_once(root/"delivery/github_chapters"/(key+"-SEAL.json"),enc(status))
    return {"status":"FULL_CHAPTER_SEALED" if not check_only else "FULL_CHAPTER_CANON_VERIFIED",
            "chapter_key":key,"last_episode":approved[-1]["episode_id"],
            "canonical_part_count":5,"source_sha256":manifest["combined_sha256"]}

def seal_head_if_last(root:Path,*,check_only=False)->dict:
    head=get_json(root/"canon/HEAD.json")
    if head.get("part")!="V":
        return {"status":"CURRENT_HEAD_NOT_LAST_PART","episode_id":head["episode_id"]}
    return seal(root,head["book"],head["chapter"],check_only=check_only)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,default=Path("."))
    p.add_argument("--seal-head-if-last",action="store_true")
    p.add_argument("--book")
    p.add_argument("--chapter",type=int)
    p.add_argument("--check-only",action="store_true")
    a=p.parse_args()
    try:
        if a.seal_head_if_last:
            result=seal_head_if_last(a.archive_root,check_only=a.check_only)
        elif a.book and a.chapter:
            result=seal(a.archive_root,a.book,a.chapter,check_only=a.check_only)
        else:
            raise ChapterError("Need --seal-head-if-last or --book plus --chapter")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    except (ChapterError,OSError,ValueError,TypeError,KeyError) as exc:
        print("WORLDROOT_CHAPTER_SEAL_BLOCKED:",str(exc),file=sys.stderr)
        raise SystemExit(1)
if __name__=="__main__":
    main()
