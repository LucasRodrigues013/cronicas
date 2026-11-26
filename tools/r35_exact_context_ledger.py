"""Exact original R35 audit queue, conservative structural/context triage.
No LLM or semantic certification. Never writes canon or original database.
"""
import collections,hashlib,json,re,sqlite3,sys
from pathlib import Path
from worldroot.history_index import read_verified_sources
from worldroot.deep_recovery import sections
from worldroot.living_world import load_canonical,literal_body
from worldroot.git_cycle import verify_episode
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def jread(p):return json.loads(p.read_text(encoding="utf-8"))
root=Path(sys.argv[1]);out=root/"editorial/codex-staging/results/exact-context-ledger-v1"
out.mkdir(parents=True,exist_ok=False)
dbpath=root/"editorial/codex-staging/results/codex.sqlite"
dbhash=hashlib.sha256(dbpath.read_bytes()).hexdigest()
db=sqlite3.connect(dbpath.resolve().as_uri()+"?mode=ro",uri=True)
db.row_factory=sqlite3.Row
head=jread(root/"canon/HEAD.json")
_,raw=read_verified_sources(root)
maps={}
for m,body in raw:
    maps["history:"+m["source_name"]]=(m["sha256"],{start+i:l.rstrip("\r\n") for role,start,rows in sections(body) if role=="Response" for i,l in enumerate(rows)})
closed,warnings=load_canonical(root,head)
if warnings:raise ValueError(str(warnings))
for e in closed:
    txt=e["text"];body=literal_body(txt);start=txt[:txt.find(body)].count("\n")+1
    maps["episode:"+e["id"]]=(e["sha256"],{start+i:l for i,l in enumerate(body.splitlines())})
pending=jread(root/"ops/RESUME.json")["latest_unclosed_draft"]
verify_episode(root,pending["episode_id"])
txt=(root/"episodes"/pending["episode_id"]/"draft/narrativa_integral.md").read_text(encoding="utf-8")
body=literal_body(txt);start=txt[:txt.find(body)].count("\n")+1
maps["episode:"+pending["episode_id"]]=(sha(txt),{start+i:l for i,l in enumerate(body.splitlines())})
rows=db.execute("SELECT o.*,s.status AS source_status,s.sha AS source_sha,s.day FROM observations o JOIN sources s ON s.id=o.source WHERE o.status='CONTEXT_CANDIDATE_NOT_ATTRIBUTED' ORDER BY o.id").fetchall()
assert len(rows)==9229
seen=set();counts=collections.Counter();by_field=collections.Counter();by_source=collections.Counter()
batch=[]
for r in rows:
    h,lines=maps[r["source"]];n=r["line"]
    if h!=r["source_sha"] or lines.get(n)!=r["anchor"] or sha(r["anchor"])!=r["anchor_sha"]:raise ValueError("Exact source/line mismatch "+str(r["id"]))
    key=(r["entity"],r["source"],r["field"],n,r["anchor_sha"])
    if key in seen:raise ValueError("Duplicate original row")
    seen.add(key)
    # Small line window only; additional semantic context is loaded on demand.
    context=[{"line":i,"text":lines[i]} for i in range(max(1,n-4),n+5) if i in lines]
    anchor=r["anchor"].strip()
    if r["source_status"]=="PENDING_NOT_CLOSED":route="DRAFT_NOT_CANON"
    elif r["source_status"]=="HISTORICAL_RESPONSE_UNREVIEWED":route="LEGACY_ROLE_AND_SEMANTIC_REVIEW"
    elif r["source_status"]=="CLOSED":route="CLOSED_PROSE_SEMANTIC_REVIEW"
    else:raise ValueError("Unexpected source status")
    flags=[]
    if re.match(r"^(?:#{1,6}\s*)?(?:\*\*)?(?:OPÇÃO|ESCOLHA|PRÓXIM[AO]|ROTEIRO|PLANEJAMENTO|RESUMO|CHECKPOINT)\b",anchor,re.I):flags.append("POSSIBLE_NON_NARRATIVE")
    if re.search(r"\b(?:não|nunca|talvez|poderia|supostamente|provavelmente)\b",anchor,re.I):flags.append("NEGATION_OR_MODALITY")
    if re.search(r"\b(?:disse|relatou|ouviu|segundo|acredita|contou)\b",anchor,re.I):flags.append("REPORTED_KNOWLEDGE")
    if len(anchor)<25:flags.append("SHORT_ANCHOR")
    entry={"original_id":r["id"],"entity_id":r["entity"],"field":r["field"],"source":r["source"],"source_sha256":h,"source_status":r["source_status"],"day":r["day"],"line":n,"anchor":r["anchor"],"anchor_sha256":r["anchor_sha"],"context":context,"route":route,"flags":flags,"verdict":"PENDING_SEMANTIC_REVIEW","semantic_certified":False}
    batch.append(entry);counts[route]+=1;by_field[r["field"]]+=1;by_source[r["source"]]+=1
    if len(batch)==100:
        (out/("batch-%03d.json"%((len(seen)+99)//100))).write_text(json.dumps(batch,ensure_ascii=False,indent=1),encoding="utf-8");batch=[]
if batch:(out/("batch-%03d.json"%((len(seen)+99)//100))).write_text(json.dumps(batch,ensure_ascii=False,indent=1),encoding="utf-8")
assert sum(counts.values())==9229
summary={"schema":"worldroot-arquiteto-exact-queue-v1","original_audit_commit":"c07d915ee9500ba18f7e4327693c154a1b2f8408","original_db_sha256":dbhash,"head":head["day"],"sequence":head["sequence"],"exact_rows":len(seen),"verified_literal_anchors":len(seen),"batches":(len(seen)+99)//100,"routes":dict(counts),"fields":dict(by_field),"sources":dict(by_source),"semantic_reviewed":0,"canon_changed":False,"note":"Structural provenance/route verified. No inference of facts or state. Independent semantic review still required."}
(out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=False))
