"""R33 stress and recovery audit. No writes to archive; no source text in logs."""
import ast,concurrent.futures,hashlib,json,os,pathlib,random,sqlite3,statistics,tempfile,time,shutil
from worldroot import deep_recovery as dr
from worldroot.memory_continuity import DOMAINS,digest,review_creation,recent_candidates,narrative_evidence
from worldroot.living_world import load_canonical
from worldroot.r33_runtime import author_context,preparation,persist,verify_submission,REVIEWS
from worldroot.curated_memory import build_cards,search_cards
from worldroot.semantic_memory import DenseIndex
from worldroot.experience_quality import render_choices
root=pathlib.Path("archive")
db=pathlib.Path(os.environ["R31_DB_PATH"])
def emit(x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
head=json.loads((root/"canon/HEAD.json").read_text())
paths=[root/"canon/HEAD.json",root/"ops/RESUME.json",root/"history/sources/MANIFEST.json",root/"episodes/LVI-C08-PI-D574-AUTHOR-SOURCE/draft/narrativa_integral.md"]
before=[hashfile(p) for p in paths]
entries,warnings=load_canonical(root,head);assert not warnings and len(entries)==44
auth=author_context(root,head)
emit({"stage":"AUTHORITY_READBACK","head":head["day"],"sequence":head["sequence"],"choice":auth["choice"]["option"],"closure_sha":auth["closure_sha256"]})
# Reuse frozen additional references. This is a registry-assisted test, not a blind holdout.
tree=ast.parse(pathlib.Path("audit/run_r31.py").read_text())
held=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="heldout_queries" for t in n.targets))
cards=build_cards(root)
idx=DenseIndex.load_lsa(db,db.parent/"r32-lsa")
counts={"wide":0,"cards":0,"union":0,"n":0}
for key,qs in held.items():
    target=next(c for c in cards if c["card"]=="scene:"+key)
    for q in qs:
        wide=idx.wide(q,role=target["role"],limit=400)
        ca=search_cards(cards,q,target["role"],limit=5)
        a=any(h["source"]==target["source"] and min(h["line_end"],target["line_end"])-max(h["line_start"],target["line_start"])+1>=3 for h in wide)
        b=any(h["card"]==target["card"] for h in ca)
        counts["wide"]+=a;counts["cards"]+=b;counts["union"]+=a or b;counts["n"]+=1
emit({"stage":"CURATED_REFERENCE_EVAL","verified_cards":len(cards),**counts,"limitation":"Existing editorial cards overlap with target references; not independent semantic generalization."})
# New randomized literal span benchmark, frozen seed; excludes unchosen options.
rng=random.Random(3301); eligible=[]
for e in entries:
    lines=narrative_evidence(e["text"]).splitlines()
    for i,line in enumerate(lines,1):
        words=[w for w in dr.tokens(line) if len(w)>=6 and w not in dr.STOP]
        if len(set(words))>=7 and not line.startswith(("<","{","|","#","**")):
            eligible.append((e["id"],i,words))
sample=rng.sample(eligible,120)
ranks=[]
for source,line,words in sample:
    q=" ".join(rng.sample(list(dict.fromkeys(words)),5))
    hits=recent_candidates(entries,q,limit=20)
    ranks.append(next((i for i,h in enumerate(hits,1) if h["source"]==source and h["line_start"]<=line<=h["line_end"]),0))
emit({"stage":"RANDOMIZED_LITERAL_REPLAY","n":len(ranks),"hit20":sum(r>0 for r in ranks),"hit1":sum(r==1 for r in ranks),"seed":3301,"limitation":"New sampled exact-word probes, not paraphrased human eval."})
# Concurrency test on immutable real index. Baselines use exact same queries and roles.
qs=[("Miren cabelos postura","Response"),("Gênese Canal Soberano","Response"),("AERÚN dragão escamas","Response"),("Calderva porto farol","Response"),("Serís ciúmes","Response"),("mochila dimensional","Response"),("Festival dos Trezentos","Response"),("zzzzqzxmissing987","Response"),("Talis inventário","Prompt"),("Lucas criação","Prompt"),("Varo resgate","Response"),("Althea cabelos","Response")]
def lookup(q):
    return [h["id"] for h in dr.retrieve(db,q[0],role=q[1],limit=20)["hits"]]
baseline={q:lookup(q) for q in qs};assert not baseline[qs[7]]
for workers in (1,4,16,32):
    inputs=[qs[i%len(qs)] for i in range(128)]
    def task(q):
        t=time.monotonic();got=lookup(q);return (got==baseline[q],time.monotonic()-t)
    t=time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:out=list(pool.map(task,inputs))
    secs=time.monotonic()-t;dur=sorted(x[1] for x in out);assert all(x[0] for x in out)
    emit({"stage":"LOAD","workers":workers,"requests":len(out),"errors":0,"seconds":round(secs,3),"throughput":round(len(out)/secs,2),"p95_ms":round(dur[int(.95*(len(dur)-1))]*1000,2),"max_ms":round(max(dur)*1000,2)})
# Read-only backup/restore and corruption. No actual authoritative state touched.
with tempfile.TemporaryDirectory() as d:
    path=pathlib.Path(d);backup=path/"backup.sqlite"
    with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as a,sqlite3.connect(backup) as b:a.backup(b)
    with sqlite3.connect(backup) as b:assert b.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert [h["id"] for h in dr.retrieve(backup,"Miren cabelos postura")["hits"]]==[h["id"] for h in dr.retrieve(db,"Miren cabelos postura")["hits"]]
    # Inject corrupt SQLite header, then ensure query rejected.
    with backup.open("r+b") as f:f.write(b"CORRUPTED-HEADER")
    try:dr.retrieve(backup,"Miren")
    except (sqlite3.DatabaseError,ValueError):pass
    else:raise AssertionError("Corruption accepted")
    # Simulate stale/corrupt vector manifest without mutating original.
    folder=path/"vector";folder.mkdir()
    manifest=json.loads((db.parent/"r32-lsa/manifest.json").read_text());manifest["db_sha256"]="0"*64
    (folder/"manifest.json").write_text(json.dumps(manifest));(folder/"vectors.npz").write_bytes(b"invalid")
    try:DenseIndex.load_lsa(db,folder)
    except ValueError:pass
    else:raise AssertionError("Corrupt vector accepted")
    # R33 preparation uses 20 real literal references, with fake target ID only in temporary copy.
    # Archive is read-only. A disposable copy contains only prep files and symlink-free originals.
    last=entries[-1];lines=last["text"].splitlines(keepends=True)
    ids=[60,64,68,152,156,268,338,344,354,360,364,404,408,456,460,562,592,596,650,680]
    requirements=[];reviewed={}
    for i,line in enumerate(ids,1):
        rid="ref-"+str(i);lo=max(1,line-2);hi=line+2
        anchor="".join(lines[lo-1:hi]);requirements.append({"id":rid,"query":" ".join(dr.tokens(lines[line-1])[:12]) or "reference","domain":"event","critical":True,"role":"Response"})
        reviewed[rid]={"source":last["id"],"line_start":lo,"line_end":hi,"anchor_sha":digest(anchor),"claim":"Retrospective reference "+rid,"status":"REVIEWED_SUPPORTED"}
    domains={k:{"applicable":k=="event","reason":"Retrospective stress fixture only"} for k in DOMAINS}
    scene=[{"scene":1,"purpose":"Disposable preparation test","ids":[r["id"] for r in requirements]}]
    packet=preparation(root,head,"R33-STRESS-NOT-A-STORY",requirements,reviewed,domains,scene)
    p=path/"prep.json"
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:out=list(pool.map(lambda _:persist(p,packet),range(256)))
    assert out.count("CREATED")==1 and out.count("IDEMPOTENT")==255
    changed=dict(packet);changed["delivery_id"]="DIFFERENT"
    try:persist(p,changed)
    except ValueError:pass
    else:raise AssertionError("Overwrite accepted")
    assert json.loads(p.read_text())==packet
    bad={k:v for k,v in reviewed.items() if k!="ref-1"}
    try:preparation(root,head,"R33-STRESS-NOT-A-STORY",requirements,bad,domains,scene)
    except ValueError:pass
    else:raise AssertionError("Missing critical accepted")
    emit({"stage":"FAULT_RECOVERY","backup_integrity":True,"corrupt_db_rejected":True,"stale_vector_rejected":True,"parallel_preparations":len(out),"created":1,"idempotent":255,"conflicting_write_rejected":True,"critical_missing_rejected":True,"preparation_coverage":packet["memory"]["coverage"]})
assert before==[hashfile(p) for p in paths]
emit({"stage":"R33_READ_ONLY","head":head["day"],"unchanged":True,"semantic_certification":False})
