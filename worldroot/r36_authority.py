"""R36 explicit ratification, additive to the existing immutable journal.
Only a trusted caller may authenticate author intent. Working tree changes must
be published atomically by a separate authorized deployment gate.
"""
from pathlib import Path
import sqlite3
import tempfile
from . import git_cycle as g
from .ledger import GateError, ConflictError
from .choice_intake import verify_selection

KIND="R36_EXPLICIT_RATIFICATION_NO_CONTINUATION"
SCHEMA="worldroot-r36-ratification-envelope-v1"

def envelope(root, episode, approval, previous):
    g.check_id(episode)
    root=Path(root)
    path=root/"author-approvals"/approval
    if Path(approval).name!=approval or not approval.endswith(".json"):
        raise GateError("Unsafe approval path")
    a=g.load(path)
    draft,manifest=g.verify_episode(root,episode)
    if (a.get("schema")!="worldroot-author-ratification-intent-v1"
        or a.get("project")!="CRONICAS_DE_UM_NOVO_MUNDO"
        or a.get("author_source")!="USER_MESSAGE"
        or a.get("approval") not in ("RATIFY_EXACT_D580_NARRATED_PROSE","RATIFY_EXACT_NARRATED_PROSE")
        or a.get("episode_id")!=episode
        or a.get("previous_head_id")!=previous["episode_id"]
        or a.get("previous_sequence")!=previous["sequence"]
        or a.get("source_sha256")!=manifest["original_readback_sha256"]
        or a.get("continuation_choice","missing") is not None
        or a.get("preserve_options") is not True
        or a.get("preserve_literal") is not True
        or not str(a.get("author_quote","")).strip()
        or any(a.get(k)!=draft.metadata[k] for k in ("book","chapter","part","day","hour"))):
        raise GateError("Ratification approval does not bind exact source and predecessor")
    return {"schema":SCHEMA,"episode_id":episode,"option":0,
            "free_text":a["author_quote"],"approval_file":approval,
            "approval_sha256":g.sha(path.read_bytes()),"author_source":"USER_MESSAGE"}

def ratify(root, episode, approval):
    root=Path(root);g.check_id(episode)
    head=g.load(root/"canon/HEAD.json")
    g.verify_db(root,head)
    target=root/"canon/episodes"/(episode+".json")
    if target.exists():
        c=g.load(target)
        if c.get("ratification_kind")!=KIND or c.get("approval_file")!=approval:
            raise ConflictError("Episode already closed by different authority")
        # Revalidate the entire chain, including the original approval hash.
        chain=list(g._journal(root))
        if not chain or chain[-1][1]!=head:
            raise GateError("Journal HEAD mismatch")
        return {"status":"IDEMPOTENT","episode":episode,"sequence":c["sequence"]}
    if (root/"editorial/rejections"/(episode+".json")).exists():
        raise GateError("Rejected episode")
    if list((root/"choices"/episode).glob("option-*.json")):
        raise ConflictError("Existing choice requires regular closure")
    if head.get("book_closed"):
        raise GateError("Use existing book opening authority")
    choice=envelope(root,episode,approval,head)
    draft,_=g.verify_episode(root,episode)
    if draft.book_closed:
        raise GateError("Use existing book finale authority")
    g._chronology(head,draft.metadata,prose=draft.prose)
    events,knowledge=g.review_deltas(root,episode,draft)
    closure=g._closure(root,episode,head,choice,draft,events,knowledge)
    new={**head,**closure["metadata"],"episode_id":episode,
         "sequence":closure["sequence"],"source_sha256":closure["story_sha256"],
         "previous_head_sha256":closure["previous_head_sha256"],
         "closure_sha256":g.sha(g.canonical(closure)),
         "drive_head_status":"NAO_SINCRONIZADO","book_closed":False}
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/"state.sqlite"
        with sqlite3.connect((root/"canon/state.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as src, sqlite3.connect(db) as dst:
            src.backup(dst)
        with sqlite3.connect(db) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            g.apply_closure_db(conn,closure,new,g.load_corrections(root,g.load))
            conn.commit()
            g._save_snapshot(conn,root/"canon/state.sqlite")
    target.write_bytes(g.canonical(closure))
    (root/"canon/HEAD.json").write_bytes(g.canonical(new))
    g.verify_db(root,new);g.write_context(root,new)
    return {"status":"RATIFIED","episode":episode,"sequence":new["sequence"],
            "events":len(events),"knowledge":len(knowledge),"continuation_choice":None}

def continuation(root,episode):
    """Read a later, independently archived author choice without rewriting closure."""
    root=Path(root);g.check_id(episode)
    c=g.load(root/"canon/episodes"/(episode+".json"))
    if c.get("ratification_kind")!=KIND:
        raise GateError("Not an independently ratified episode")
    paths=list((root/"choices"/episode).glob("option-*.json"))
    if len(paths)>1:raise ConflictError("Conflicting continuation choices")
    if not paths:return {"episode":episode,"choice":None,"status":"AWAITING_AUTHOR"}
    receipt=verify_selection(root,paths[0])
    return {"episode":episode,"choice":g.load(paths[0]),"receipt":receipt,
            "closure_sha256":g.sha(g.canonical(c)),"status":"CHOICE_RECORDED"}
