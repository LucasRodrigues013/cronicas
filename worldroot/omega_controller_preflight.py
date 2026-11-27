"""Read-only OMEGA controller preflight: aggregate native contract failures.
No auto-repair, no fabricated reviews, no writes and no release authorization.
The production archive/release gates remain mandatory and unchanged.
"""
from __future__ import annotations
import time
from pathlib import Path
from .git_cycle import load,_chronology,check_id
from .ledger import GateError,ConflictError
from .longform_segments import verify_longform_segments
from .r32_release import release_review
from .r34_experience import validate_delivery as r34
from .r35_longform import validate_delivery as r35
from .r33_runtime import verify_submission
from .reader_experience import validate_reader_review,previous_canonical_scene_counts
from .narrative_director import validate_direction
from .r26_fantasy_directors import audit_fantasy
from .draft_inbox import _assemble
from .book_closure import require_book_end_approval
from .book_opening import require_book_open_approval
from .r33_runtime import digest

def preflight(root,payload):
    root=Path(root);started=time.perf_counter();results=[]
    def stage(name,fn):
        t=time.perf_counter()
        try:
            fn()
            results.append({"stage":name,"ok":True,"seconds":round(time.perf_counter()-t,6)})
        except (GateError,ConflictError,ValueError,TypeError,KeyError,AttributeError,IndexError,OSError) as e:
            results.append({"stage":name,"ok":False,"error":type(e).__name__+": "+str(e)[:220],"seconds":round(time.perf_counter()-t,6)})
    ident=payload["delivery_id"];check_id(ident)
    head=load(root/"canon/HEAD.json");req=load(root/"requests"/(ident+".json"));packet=load(root/"preparations"/(ident+".json"))
    def checked(x,key="errors"):
        if x.get(key):raise ValueError("; ".join(x[key]))
    def segments():
        if not verify_longform_segments(root,ident,payload)["verified"]:raise ValueError("R35 exact segments required")
    def chronology():
        approved=False
        if head.get("book_closed") is True:
            require_book_open_approval(root,head,payload["metadata"]);approved=True
        _chronology(head,payload["metadata"],prose=payload["prose"],book_open_approval_verified=approved)
    def assemble():
        approved=False
        if payload.get("book_closed") is True:
            require_book_end_approval(root,ident,payload["metadata"]["book"]);approved=True
        _assemble(ident,payload,head=head,book_end_approval_verified=approved,
            previous_counts=previous_canonical_scene_counts(root,payload["metadata"]),archive_root=root)
    stage("segments",segments)
    stage("chronology",chronology)
    stage("r25_direction",lambda:checked(validate_direction(head,payload.get("narrative_direction"))))
    stage("r25_reader",lambda:checked(validate_reader_review(payload["prose"],payload.get("reader_review"),previous_counts=previous_canonical_scene_counts(root,payload["metadata"]))))
    stage("r26_fantasy",lambda:checked(audit_fantasy(payload["prose"],payload.get("fantasy_review"),head_episode_id=head["episode_id"],previous_counts=previous_canonical_scene_counts(root,payload["metadata"]),archive_root=root)))
    stage("r32_memory",lambda:release_review(root,head,payload))
    stage("r34_intent",lambda:r34(req,payload))
    stage("r35_longform",lambda:r35(root,req,payload,packet["authority"]["choice"]))
    stage("r36_submission",lambda:verify_submission(root,head,payload))
    stage("archive_assembly",assemble)
    return {"schema":"worldroot-omega-controller-preflight-v1","status":"READY_FOR_NATIVE_ARCHIVE" if all(r["ok"] for r in results) else "REVISE_BEFORE_ARCHIVE",
        "checks":results,"failed":[r["stage"] for r in results if not r["ok"]],"payload_sha256":digest(payload),
        "elapsed_seconds":round(time.perf_counter()-started,6),"release_allowed":False,"semantic_certification":False,"canon_changed":False}
