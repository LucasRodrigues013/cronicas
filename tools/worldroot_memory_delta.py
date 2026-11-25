"""WORLDROOT Cycle 2: source-anchored incremental facts and replayable compact resume.

No model-authored new events: only reviewed event/knowledge source evidence.
Draft memory and canonical memory are separate immutable ledgers.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from validate_episode_archive import verify_one, ArchiveInvalid
from verify_lvi_original import verify_lvi

PARTS=("I","II","III","IV","V")
def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()
def enc(v)->bytes:
    return (json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":"))+"\n").encode()
def obj(p:Path):
    if not p.is_file() or p.is_symlink():
        raise ArchiveInvalid("Missing/unsafe memory evidence: "+str(p))
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict):
        raise ArchiveInvalid("Evidence must be a JSON object: "+str(p))
    return v
def write_once(p:Path,b:bytes):
    if p.exists():
        if not p.is_file() or p.is_symlink() or p.read_bytes()!=b:
            raise ArchiveInvalid("Immutable memory conflict: "+str(p))
        return False
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(b)
    return True

def derive(root:Path,eid:str)->dict:
    source_dir=root/"episodes"/eid/"draft"
    if (root/"editorial/rejections"/(eid+".json")).exists():
        raise ArchiveInvalid("Rejected episode cannot populate memory")
    verified=verify_lvi(root,eid) if eid.startswith("LVI-") else verify_one(source_dir/"manifesto_imutavel.json")
    story=(source_dir/"narrativa_integral.md").read_bytes()
    if verified["sha256"]!=sha(story):
        raise ArchiveInvalid("Unmatched story hash")
    meta=obj(source_dir/"checkpoint_candidato.json")
    reviewed=obj(root/"episodes"/eid/"review/eventos_revisados.json")
    if reviewed.get("source_sha256")!=sha(story) or reviewed.get("review_status")!="REVISADO":
        raise ArchiveInvalid("Invalid reviewed event source")
    characters=obj(root/"episodes"/eid/"review/continuity_review.json") if eid.startswith("LVI-") else {"characters":[],"open_flags":[]}
    knowledge=obj(root/"episodes"/eid/"review/conhecimento_revisado.json")
    if knowledge.get("review_status")!="REVISADO":
        raise ArchiveInvalid("Invalid reviewed knowledge")
    events=reviewed.get("events")
    if not isinstance(events,list) or not events:
        raise ArchiveInvalid("No reviewed narrative facts")
    lines=story.decode("utf-8").splitlines()
    selected=[]
    ids=set()
    for event in events:
        anchor=event.get("source") if isinstance(event,dict) else None
        if not isinstance(anchor,dict):
            raise ArchiveInvalid("Missing event source line")
        line,literal=anchor.get("line"),anchor.get("literal_anchor")
        if (type(line) is not int or not 1<=line<=len(lines)
                or not isinstance(literal,str) or not literal.strip()
                or literal not in lines[line-1] or anchor.get("sha256")!=sha(story)):
            raise ArchiveInvalid("Unverified event literal/source hash")
        event_id=event.get("event_id")
        if not isinstance(event_id,str) or not event_id or event_id in ids:
            raise ArchiveInvalid("Repeated event identity")
        ids.add(event_id)
        selected.append({"event_id":event_id,"event_type":event.get("event_type"),
                         "day":event.get("occurred_day"),"visibility":event.get("visibility"),
                         "summary_from_review":event.get("summary_candidato"),
                         "literal_evidence":{"line":line,"excerpt":literal}})
    facts=knowledge.get("knowledge")
    if not isinstance(facts,list):
        raise ArchiveInvalid("Invalid knowledge list")
    for fact in facts:
        if not isinstance(fact,dict) or fact.get("source_event") not in ids:
            raise ArchiveInvalid("Knowledge fact does not reference reviewed event")
        if not isinstance(fact.get("person"),str):
            raise ArchiveInvalid("Knowledge needs named person")
        if type(fact.get("acquired_day")) is not int or fact["acquired_day"]>meta.get("day",0):
            raise ArchiveInvalid("Knowledge acquired after narrated episode")
    if not isinstance(characters.get("characters"),list):
        raise ArchiveInvalid("Invalid character preflight")
    journal=root/"canon/episodes"/(eid+".json")
    if journal.is_file() and obj(journal).get("story_sha256")!=sha(story):
        raise ArchiveInvalid("Canon journal differs from literal story")
    return {"schema":"worldroot-source-anchored-incremental-memory-v1",
        "episode_id":eid,"metadata":{k:meta.get(k) for k in ("book","chapter","part","day","hour","location")},
        "source_sha256":sha(story),"source_bytes":len(story),
        "source_path":str((source_dir/"narrativa_integral.md").relative_to(root)),
        "reviewed_events":selected,"reviewed_knowledge":facts,
        "character_preflight":characters["characters"],
        "continuity_flags":characters.get("open_flags",[]),
        "capture_kind":"LITERAL_WITH_REVIEW_NOT_INFERRED",
        "canonical_at_capture":journal.is_file(),
        "note":"Draft reviews are candidates until canonical journal closes this episode; unknown travel/knowledge remains unknown."}

def draft_delta(root:Path,eid:str,*,write=False)->dict:
    d=derive(root,eid)
    path=root/"memory/deltas"/(eid+".json")
    if write:
        # Preserve the original draft capture after a later canonical closure.
        # Only this temporal observation can legitimately differ on replay.
        if path.exists():
            previous=obj(path)
            expected=dict(d)
            if d["canonical_at_capture"] is True and previous.get("canonical_at_capture") is False:
                expected["canonical_at_capture"]=False
            if path.read_bytes()!=enc(expected):
                raise ArchiveInvalid("Immutable memory conflict: "+str(path))
        else:
            write_once(path,enc(d))
    return {"episode_id":eid,"events":len(d["reviewed_events"]),
            "knowledge":len(d["reviewed_knowledge"]),
            "flags":d["continuity_flags"],"status":"VERIFIED_DRAFT_MEMORY",
            "path":str(path.relative_to(root))}

def canon_delta(root:Path,eid:str,*,write=False)->dict:
    base=derive(root,eid)
    journal=obj(root/"canon/episodes"/(eid+".json"))
    if journal.get("episode_id")!=eid or journal.get("story_sha256")!=base["source_sha256"] or journal.get("status")!="FECHADO_GITHUB":
        raise ArchiveInvalid("Not a matching closed canonical episode")
    names=[event.get("event_id") for event in journal.get("events",[])]
    if not names or set(names)!=set(v["event_id"] for v in base["reviewed_events"]):
        raise ArchiveInvalid("Canonical event set differs from reviewed literal")
    approval={
        "schema":"worldroot-canon-incremental-memory-v1","episode_id":eid,
        "source_sha256":base["source_sha256"],
        "journal_sha256":sha(enc(journal)),
        "sequence":journal.get("sequence"),"event_ids":names,
        "character_continuity_flags_preserved":base["continuity_flags"],
        "source_review_path":str(Path("memory/deltas")/(eid+".json")),
        "status":"CANONICAL_JOURNAL_VERIFIED_NO_NEW_FACTS",
    }
    path=root/"memory/canon"/(eid+".json")
    if write:
        # A draft memory capture is IMMUTABLE; canonical closure must never
        # rewrite its historical "canonical_at_capture=False" observation.
        draft_path=root/"memory/deltas"/(eid+".json")
        if draft_path.is_file():
            previous=obj(draft_path)
            if (previous.get("source_sha256")!=base["source_sha256"]
                    or previous.get("reviewed_events")!=base["reviewed_events"]
                    or previous.get("reviewed_knowledge")!=base["reviewed_knowledge"]):
                raise ArchiveInvalid("Existing draft memory differs from the literal review")
        else:
            write_once(draft_path,enc(base))
        write_once(path,enc(approval))
    return {"episode_id":eid,"status":"CANONICAL_MEMORY_VERIFIED",
            "path":str(path.relative_to(root)),"events":len(names)}

def find_active(root:Path)->list[tuple[str,dict]]:
    rows=[]
    for p in (root/"episodes").glob("*/draft/checkpoint_candidato.json"):
        eid=p.parent.parent.name
        if (root/"editorial/rejections"/(eid+".json")).exists():
            continue
        m=obj(p)
        if m.get("book")=="Livro VI" and m.get("part") in PARTS:
            rows.append((eid,m))
    return sorted(rows,key=lambda z:(z[1].get("chapter",0),z[1].get("day",0),PARTS.index(z[1]["part"])))

def resume(root:Path,*,write=False)->dict:
    head=obj(root/"canon/HEAD.json")
    canon=root/"canon/episodes"/(head["episode_id"]+".json")
    if not canon.is_file():
        raise ArchiveInvalid("HEAD lacks matching canonical journal")
    j=obj(canon)
    if j.get("story_sha256")!=head.get("source_sha256"):
        raise ArchiveInvalid("HEAD and current journal source disagree")
    active=find_active(root)
    pending=[(eid,m) for eid,m in active if not (root/"canon/episodes"/(eid+".json")).exists()]
    latest=pending[-1] if pending else None
    flags={}
    for eid,m in active:
        if not eid.startswith("LVI-"):
            continue
        p=root/"episodes"/eid/"review/continuity_review.json"
        if p.is_file():
            review=obj(p)
            if review.get("open_flags"):
                flags[eid]=review["open_flags"]
    data={
        "schema":"worldroot-replayable-resume-v1",
        "authority":"GITHUB_PRIVATE_STORY_ARCHIVE",
        "canon_head":{k:head.get(k) for k in ("episode_id","sequence","book","chapter","part","day","hour","location","source_sha256","book_closed")},
        "last_canon_journal_sha256":sha(enc(j)),
        "latest_unclosed_draft":None if latest is None else {
            "episode_id":latest[0],"book":latest[1]["book"],"chapter":latest[1]["chapter"],
            "part":latest[1]["part"],"day":latest[1]["day"],
            "source_path":"episodes/"+latest[0]+"/draft/narrativa_integral.md",
            "source_sha256":obj(root/"episodes"/latest[0]/"draft/manifesto_imutavel.json").get("original_readback_sha256")},
        "all_pending_draft_ids":[eid for eid,_ in pending],
        "continuity_flags_from_source":flags,
        "author_style_feedback":"editorial/feedback/2026-11-19-lucas-carisma-strong-kind-loving.json",
        "policies_ref":"main/worldroot/editorial_policy.json",
        "planning_ref":"planning/book-vi/",
        "drive_status":"LEGACY_NO_ACTIVE_BACKUP",
        "no_silent_promotions":True,
        "no_new_facts_inferred":True,
        "snapshot_not_source_of_truth":True,
    }
    if write:
        p=root/"ops/RESUME.json"
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(enc(data))
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-root",type=Path,default=Path("."))
    p.add_argument("--episode-id")
    p.add_argument("--mode",choices=("draft","canon","resume","backfill"),required=True)
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    try:
        if a.mode=="draft":
            result=draft_delta(a.archive_root,a.episode_id,write=a.write)
        elif a.mode=="canon":
            result=canon_delta(a.archive_root,a.episode_id,write=a.write)
        elif a.mode=="backfill":
            processed=[]
            for eid,_ in find_active(a.archive_root):
                processed.append(draft_delta(a.archive_root,eid,write=a.write))
                if (a.archive_root/"canon/episodes"/(eid+".json")).is_file():
                    processed.append(canon_delta(a.archive_root,eid,write=a.write))
            result={"episodes":len(processed),"status":"BACKFILL_VERIFIED"}
        else:
            result=resume(a.archive_root,write=a.write)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    except (ArchiveInvalid,OSError,ValueError,KeyError,TypeError) as exc:
        print("WORLDROOT_INCREMENTAL_MEMORY_BLOCKED:",str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":
    main()
