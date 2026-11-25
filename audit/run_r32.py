"""R32 evaluation of original immutable D574 draft (not a new canon episode)."""
from __future__ import annotations
import hashlib,json,pathlib,time,os
from worldroot import memory_graph as graph
from worldroot.semantic_memory import DenseIndex
from worldroot.memory_continuity import fusion,review_creation,digest
from worldroot.history_index import read_verified_sources
from worldroot.living_world import load_canonical
from worldroot.presentation_guard import presentation_preflight
from worldroot.literary_experience import measure,choice_review
root=pathlib.Path("archive")
db=pathlib.Path(os.environ["R31_DB_PATH"])
head=json.loads((root/"canon/HEAD.json").read_text())
staged=json.loads(pathlib.Path("recovery/r31-historical-candidates.json").read_text())
def emit(x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[root/"canon/HEAD.json",root/"ops/RESUME.json",root/"episodes/LVI-C08-PI-D574-AUTHOR-SOURCE/draft/narrativa_integral.md"]
before=[sha(p) for p in paths]
g=graph.build(root,staged)
graph.write_graph(g,db.parent/"r32-graph.sqlite")
emit({"stage":"GRAPH","nodes":len(g["nodes"]),"edges":len(g["edges"]),"dossiers":len(g["dossiers"]),"dossiers_with_observations":sum(bool(d["observations"]) for d in g["dossiers"].values()),"events":len(g["events"]),"knowledge":len(g["knowledge"]),"inventory_candidates":len(g["inventory"]["events"]),"power_candidates":len(g["power"]["events"]),"historical_power":len(g["power"]["historical"]),"relationship_candidates":len(g["relationships"]),"plots":len(g["plots"]),"assets":len(g["assets"]),"rejected_events":len(g["rejected_events"]),"unresolved_edges":g["unresolved_edges"],"canon_changed":False})
# Independent episode-context questions: exact literal proof chosen from closed D573,
# distinct from historical R31 benchmark. This is retrospective, not a blind reader test.
entries,warnings=load_canonical(root,head)
assert not warnings and len(entries)==44
last=entries[-1]
draft=paths[-1].read_text()
events=last["events"]
req=[];review={}
for e in events:
    s=e["source"];anchor=s["literal_anchor"];p=graph.locate(last["text"],anchor)
    if not p:continue
    rid=e["event_id"]
    # Verify source anchor and role. Human semantic review of summary remains separate.
    line=p["line_start"];end=p["line_end"]
    body="".join(last["text"].splitlines(keepends=True)[line-1:end])
    req.append({"id":rid,"domain":"event","critical":True,"role":"Response"})
    review[rid]={"source":last["id"],"line_start":line,"line_end":end,"anchor_sha":digest(body),"claim":e["summary_candidato"],"status":"REVIEWED_SUPPORTED"}
result=review_creation(root,head,req,review)
emit({"stage":"REAL_EPISODE_REFERENCE_REPLAY","episode":paths[-1].parent.parent.name,"requirements":len(req),"literal_references_verified":result["verified"],"critical_missing":len(result["critical_missing"]),"coverage":result["coverage"],"limitation":"Known closure anchor replay only; not independent retrieval or semantic faithfulness."})
emit({"stage":"LITERARY_BASELINE","episode":paths[-1].parent.parent.name,"metrics":measure(draft),"choice":choice_review(draft),"presentation":presentation_preflight(draft),"literary_grade":None})
# Actual dense benchmark, frozen previous 121 questions from code, not new labels.
# Load just the declarative query list through AST, never execute prior script.
import ast
tree=ast.parse(pathlib.Path("audit/run_r31.py").read_text())
queries=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="queries" for t in n.targets))
held=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="heldout_queries" for t in n.targets))
_,raw=read_verified_sources(root);bodies={m["source_name"]:t for m,t in raw}
gold=[]
for i,c in enumerate(g["historical_observations"]):
    for q in queries[i]:gold.append(("development",q,c["source"],c["line_start"],c["line_end"],c["role"]))
corpus=json.loads((root/"editorial/registries/r30-literary-corpus.json").read_text())["scenes"]
for row in corpus:
    if row["id"] not in held:continue
    s=row["source"];span=graph.locate(bodies[s["source_name"]],s["anchor"])
    assert span
    for q in held[row["id"]]:gold.append(("additional",q,s["source_name"],span["line_start"],span["line_end"],s.get("role","Response")))
start=time.monotonic();idx=DenseIndex(db)
emit({"stage":"DENSE_BUILD","backend":"lsa","vectors":len(idx.rows),"dimension":idx.vectors.shape[1],"seconds":round(time.monotonic()-start,3)})
for strategy in ("dense","combined"):
    ranks={"development":[],"additional":[]};start=time.monotonic()
    for split,q,source,lo,hi,role in gold:
        hits=idx.search(q,role,80) if strategy=="dense" else idx.combined(q,role=role,limit=160)
        rank=next((i for i,h in enumerate(hits,1) if h["source"]==source and min(h["line_end"],hi)-max(h["line_start"],lo)+1>=min(3,hi-lo+1)),0)
        ranks[split].append(rank)
    emit({"stage":"DENSE_EVAL","strategy":strategy,"seconds":round(time.monotonic()-start,3),"splits":{k:{"n":len(v),"hit20":sum(0<r<=20 for r in v),"hit80":sum(0<r<=80 for r in v),"hit160":sum(r>0 for r in v),"mrr":round(sum(1/r for r in v if r)/len(v),4)} for k,v in ranks.items()}})
assert before==[sha(p) for p in paths]
emit({"stage":"R32_READ_ONLY","unchanged":True,"head":head["day"]})
