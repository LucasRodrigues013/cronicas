"""Private disposable integration; no publication and no real future choice."""
import json, shutil, sys, tempfile, hashlib
from pathlib import Path
from worldroot import git_cycle as g
from worldroot.r36_authority import ratify,continuation
from worldroot.r36_core import temporal_events
from worldroot.ledger import GateError,ConflictError

source=Path(sys.argv[1])
episode="LVI-C09-PII-D580-AUTHOR-SOURCE"
approval="LVI-C09-PII-D580-RATIFICATION-20261126.json"
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reject(fn):
    try:fn()
    except (GateError,ConflictError):return
    raise AssertionError("Expected rejection")
protected=[source/"canon/HEAD.json",source/"ops/RESUME.json",source/"episodes"/episode/"draft/narrativa_integral.md"]
before=[digest(p) for p in protected]
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/"archive"
    shutil.copytree(source,root,ignore=shutil.ignore_patterns(".git"))
    ap=root/"author-approvals"/approval
    original=ap.read_bytes();a=json.loads(original);a["source_sha256"]="0"*64;ap.write_bytes(g.canonical(a))
    reject(lambda:ratify(root,episode,approval));ap.write_bytes(original)
    a=json.loads(original);a["previous_sequence"]=-1;ap.write_bytes(g.canonical(a))
    reject(lambda:ratify(root,episode,approval));ap.write_bytes(original)
    result=ratify(root,episode,approval)
    assert result["sequence"]==51 and result["events"]==22 and result["knowledge"]==22
    head=g.load(root/"canon/HEAD.json")
    assert head["day"]==580 and head["hour"]=="22h37"
    closure=root/"canon/episodes"/(episode+".json");seal=digest(closure)
    assert continuation(root,episode)["choice"] is None
    assert ratify(root,episode,approval)["status"]=="IDEMPOTENT"
    # Synthetic choice ONLY in disposable copy, never an assertion of actual user intent.
    folder=root/"choices"/episode;folder.mkdir(parents=True,exist_ok=True)
    fixture={"schema":"worldroot-author-choice-v1","episode_id":episode,"option":1,"free_text":"SYNTHETIC TEST ONLY","author_source":"USER_MESSAGE"}
    (folder/"option-1.json").write_bytes(g.canonical(fixture))
    assert continuation(root,episode)["choice"]["option"]==1
    assert digest(closure)==seal
    (folder/"option-2.json").write_bytes(g.canonical({**fixture,"option":2}))
    reject(lambda:continuation(root,episode));(folder/"option-2.json").unlink()
    import sqlite3
    from worldroot.r36_temporal import coverage,query
    with sqlite3.connect(root/"canon/codex.sqlite") as graph:
        cov=coverage(graph)
        assert graph.execute("SELECT count(*) FROM r36_canon_event WHERE episode=?",(episode,)).fetchone()[0]==22
        assert graph.execute("SELECT count(*) FROM r36_canon_event WHERE day=581").fetchone()[0]==0
        assert graph.execute("SELECT count(*) FROM r36_canon_event").fetchone()[0]==cov["canonical_events"]
    assert all(x["day"]<=580 for x in query(root,"lucas",580,"22h37")["history"])
    replay=g.restore(root);assert replay["sequence"]==51 and digest(closure)==seal
    assert g.load(root/"canon/HEAD.json")==head
    with sqlite3.connect(root/"canon/codex.sqlite") as graph:
        assert coverage(graph)==cov
    print(json.dumps({"r36_temporal":cov,"d580_indexed":22,"restore":True}))
    timeline=temporal_events(root,580,"22h37")
    assert all(x["day"]<=580 for x in timeline)
    assert all(x["day"]<580 or x["hour"] is not None and x["hour"]<="22h37" for x in timeline)
    assert digest(root/"episodes"/episode/"draft/narrativa_integral.md")==before[2]
    print(json.dumps({"r36_authority":"PASS","sequence":51,"events":22,"knowledge":22,"restore":True,"idempotence":True,"synthetic_later_choice":True,"negative_cases":3,"public_timeline_rows":len(timeline),"production_changed":False}))
assert [digest(p) for p in protected]==before
