"""R36 historical reconciliation staging. No canonical promotion or new DB."""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json
from . import git_cycle as g
from .history_index import read_verified_sources
from .semantic_queue import jobs,seal

def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def verify_rows(rows,sources,expected=9229):
    if len(rows)!=expected or {r["original_id"] for r in rows}!=set(range(1,expected+1)):
        raise ValueError("Incomplete or duplicate original ledger IDs")
    for r in rows:
        key=r["source"]
        if key not in sources:raise ValueError("Unknown source")
        digest,lines,status=sources[key]
        if r["source_sha256"]!=digest or r["source_status"]!=status:
            raise ValueError("Source digest or historical status mismatch")
        n=r["line"]
        if type(n) is not int or not 1<=n<=len(lines) or lines[n-1]!=r["anchor"] or sha(r["anchor"])!=r["anchor_sha256"]:
            raise ValueError("Original anchor mismatch")
        context=r["context"]
        if not context or n not in [x["line"] for x in context]:raise ValueError("Missing anchor context")
        if any(type(x["line"]) is not int or not 1<=x["line"]<=len(lines) or lines[x["line"]-1]!=x["text"] for x in context):
            raise ValueError("Original context mismatch")
    return rows

def read_sources(root,rows):
    root=Path(root);out={}
    _,history=read_verified_sources(root)
    for src,body in history:
        out["history:"+src["source_name"]]=(src["sha256"],body.splitlines(),"HISTORICAL_RESPONSE_UNREVIEWED")
    for key in {r["source"] for r in rows if r["source"].startswith("episode:")}:
        ident=key.split(":",1)[1]
        g.check_id(ident)
        draft,manifest=g.verify_episode(root,ident)
        status="CLOSED" if (root/"canon/episodes"/(ident+".json")).exists() else "PENDING_NOT_CLOSED"
        out[key]=(manifest["original_readback_sha256"],draft.full_text.splitlines(),status)
    return out

def reconcile_events(closures,rows):
    """Candidate overlap only; proximity is not attribution or entailment."""
    index=defaultdict(list)
    for r in rows:index[(r["source"],r["source_sha256"],r["line"])].append(r)
    results=[];seen=set()
    for c in sorted(closures,key=lambda x:x["sequence"]):
        for e in c["events"]:
            ident=e["event_id"];s=e["source"]
            if ident in seen:raise ValueError("Repeated canonical event")
            seen.add(ident)
            if s["sha256"]!=c["story_sha256"]:raise ValueError("Canonical event source mismatch")
            matches=index.get(("episode:"+c["episode_id"],s["sha256"],s["line"]),[])
            matches=[r for r in matches if s["literal_anchor"] in r["anchor"]]
            results.append({"event_id":ident,"episode":c["episode_id"],"source_sha256":s["sha256"],"line":s["line"],
                "visibility":e["visibility"],"candidate_ids":[r["original_id"] for r in matches],
                "candidate_entities":sorted({r["entity_id"] for r in matches}),
                "route":"SAME_LINE_REVIEW_REQUIRED" if matches else "NO_LEDGER_ANCHOR_REVIEW_REQUIRED",
                "semantic_certified":False,"canon_promotion":False})
    return results

def prior_review(rows,first):
    by={r["original_id"]:r for r in rows};seen=set()
    for r in first["rows"]:
        ident=r["original_id"];original=by.get(ident)
        if original is None or ident in seen or any(r[k]!=original[k] for k in ("entity_id","field","source","line","anchor_sha256")) or r.get("canon_promotion") is not False:
            raise ValueError("Prior review provenance mismatch")
        seen.add(ident)
    return seen

def run(root,ledger,out,expected=9229):
    root=Path(root);ledger=Path(ledger);out=Path(out)
    summary=json.loads((ledger/"summary.json").read_text())
    rows=[r for p in sorted(ledger.glob("batch-*.json")) for r in json.loads(p.read_text())]
    if summary["exact_rows"]!=expected or len(list(ledger.glob("batch-*.json")))!=summary["batches"]:raise ValueError("Ledger manifest mismatch")
    sources=read_sources(root,rows);verify_rows(rows,sources,expected)
    first=json.loads((root/"editorial/codex-staging/r35-arquiteto-semantic-lot-001.json").read_text())
    previous=prior_review(rows,first)
    closures=[g.load(p) for p in (root/"canon/episodes").glob("*.json")]
    head=g.load(root/"canon/HEAD.json");g.verify_db(root,head)
    links=reconcile_events(closures,rows)
    # Include D580 only as a proposed event in the same staging report, never as production closure.
    from .r36_authority import ratify
    import tempfile,shutil
    with tempfile.TemporaryDirectory() as t:
        copy=Path(t)/"archive";shutil.copytree(root,copy,ignore=shutil.ignore_patterns(".git"))
        ratify(copy,"LVI-C09-PII-D580-AUTHOR-SOURCE","LVI-C09-PII-D580-RATIFICATION-20261126.json")
        all_links=reconcile_events([g.load(p) for p in (copy/"canon/episodes").glob("*.json")],rows)
    out.mkdir(parents=True,exist_ok=False)
    counts=Counter(r["route"] for r in all_links)
    tasks=list(jobs(rows))
    targets=sum(len(j["targets"]) for j in tasks)
    if targets!=expected:raise ValueError("Review queue lost original rows")
    metrics={"historical_rows_verified":len(rows),"sources":len(sources),"batches":summary["batches"],
       "routes":dict(Counter(r["route"] for r in rows)),"previous_first_pass_preserved":len(previous),
       "jobs":len(tasks),"targets":targets,"production_events":len(links),"disposable_events":len(all_links),
       "event_routes":dict(counts),"candidate_row_links":sum(len(r["candidate_ids"]) for r in all_links),
       "independently_reviewed":0,"canon_promotions":0,"semantic_certification":False}
    for name,obj in (("event-candidates.json",all_links),("metrics.json",metrics)):
        (out/name).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True),encoding="utf-8")
    with (out/"jobs.jsonl").open("x",encoding="utf-8") as f:
        for j in tasks:f.write(json.dumps(j,ensure_ascii=False,separators=(",",":"))+"\n")
    return metrics
