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
# Full prospective-contract rehearsal on a disposable COPY, never a new story.
# Use the literal already-archived D574 prose solely as a regression fixture.
from worldroot.r33_runtime import prepare_from_request
from worldroot.history_index import read_verified_sources
from worldroot.editorial_guard import POLICY_PATH
from worldroot.presentation_guard import SCENE
from worldroot.memory_graph import locate
with tempfile.TemporaryDirectory() as d:
    scratch=pathlib.Path(d)/"archive"
    shutil.copytree(root,scratch,ignore=shutil.ignore_patterns(".git"))
    ident="R33-REHEARSAL-NOT-CANON"
    last=entries[-1];lines=last["text"].splitlines(keepends=True)
    req=[];proof={}
    def add(rid,domain,query,claim,source,lo,hi,body,role="Response"):
        req.append({"id":rid,"domain":domain,"query":query,"critical":True,"role":role})
        proof[rid]={"source":source,"line_start":lo,"line_end":hi,"anchor_sha":digest("".join(body.splitlines(keepends=True)[lo-1:hi])),"claim":claim,"status":"REVIEWED_SUPPORTED"}
    # Literal D573 evidence for current continuity.
    for rid,domain,q,claim,lo,hi in [
        ("halvern","event","Halvern correspondência Renshar","A correspondência de Halvern circulou desde D569; Renshar caiu em D567.",60,64),
        ("velkar","knowledge","Lucas Velkar nome","Lucas lê pela primeira vez o nome de Velkar Draen.",66,72),
        ("rail","world","Naira viagem técnica","Naira autorizou a demonstração tripulada em velocidade reduzida.",150,156),
        ("delegation","location","ARGOS Campo Aurora","O ARGOS chegou trazendo três visitantes.",588,598),
        ("unknown","knowledge","Lucas técnica nome desconhecido","Lucas ainda não conhece o nome da técnica imperial.",344,354),
        ("bressa","promise","Bressa selo remessas fabricante","O livro de entregas contém selo discrepante, sem autoria identificada.",558,566),
        ("althea","event","Althea conferência fronteiras","Thalor decidiu participar; Althea ordenou vigilância e estoques, não guerra.",400,410),
        ("miren","relationship","Miren Lucas mão pessoas","Miren segura a mão do marido e fala das pessoas trazidas.",815,826)
    ]:add(rid,domain,q,claim,last["id"],lo,hi,last["text"])
    _,historical=read_verified_sources(root);bodies={m["source_name"]:t for m,t in historical}
    staged=json.loads(pathlib.Path("recovery/r32-additional-evidence.json").read_text())["records"]
    for i,(domain,needle) in enumerate([("inventory","D1 equipamento"),("power","D210"),("identity","D318")]):
        c=next(c for c in staged if needle in c["claim"])
        body=bodies[c["source_name"]]
        span=locate(body,c["anchor"])
        if not span:raise AssertionError("Nonunique historical rehearsal anchor")
        add("historic-"+str(i),domain,c["claim"],c["claim"],c["source_name"],span["line_start"],span["line_end"],body,c["role"])
    policy=POLICY_PATH.read_text(encoding="utf-8");pl=policy.splitlines()
    pos=next(i for i,l in enumerate(pl,1) if '"id": "P108"' in l)
    add("author","author_rule","P108 quatro caminhos","Quatro caminhos de valor comparável, preservando ação livre.","AUTHOR_POLICY",pos,pos+5,policy,"AuthorPolicy")
    domains={k:{"applicable":any(r["domain"]==k for r in req),"reason":"Real source-bound retrospective rehearsal, not a new narrative"} for k in DOMAINS}
    draft=paths[-1].read_text()
    split=draft.index("## AS CINCO PORTAS")
    base=draft[:split]
    n=len(SCENE.findall(base))
    assert n>=1
    ids=[r["id"] for r in req]
    plan=[{"scene":i+1,"purpose":"Rehearsal of existing scene","ids":ids[i::n] or [ids[i%len(ids)]]} for i in range(n)]
    request={"schema":"worldroot-r33-request-v1","project":"CRONICAS_DE_UM_NOVO_MUNDO","delivery_id":ident,"head":head,"choice_sha256":auth["choice_sha256"],"requirements":req,"reviewed":proof,"domain_review":domains,"scene_plan":plan}
    persist(scratch/"requests"/(ident+".json"),request)
    result=prepare_from_request(scratch,request)
    assert result["result"]=="CREATED"
    assert prepare_from_request(scratch,request)["result"]=="IDEMPOTENT"
    # The choices are only fixture routes; they are never submitted to the canon.
    route={"options":[{"number":i,"track":"main" if i==1 else "secondary","arc_id":"fixture-"+str(i),"title":"Caminho "+str(i),"promise":"Possibilidade de percurso "+str(i),"reward":"Recompensa própria "+str(i),"risk":"Consequência possível "+str(i),"next_link":"Frente "+str(i),"unselected_progress":"Outras frentes seguem causalidade","guaranteed_success":False,"combines_all":False} for i in range(1,5)],"free_action":True,"author_choice_recorded":False}
    rendered=render_choices(route,ident)
    prose=rendered["body_declaration"]+"\n"+base
    full=prose+rendered["markup"]
    payload={"delivery_id":ident,"prose":prose,"full_text":full,"choices":[{"number":i,"title":"Caminho "+str(i),"description":"Possibilidade de percurso "+str(i),"is_special":i==4,"is_free":i==5} for i in range(1,6)]}
    payload["r32_review"]={"head":head,"prose_sha256":hashlib.sha256(prose.encode()).hexdigest(),"requirements":req,"reviewed":proof,"domain_review":domains,"scene_requirements":[{"scene":p["scene"],"ids":p["ids"]} for p in plan],"arc_packet":route,"editorial_parity_reviewed":True}
    # Held explicitly: this is a contract rehearsal, not a fabricated editorial judgment.
    payload["r33_review"]={"preparation_sha256":result["preparation_sha256"],"reviews":{k:{"status":"held","reason":"Fixture only; no independent literary judgment"} for k in REVIEWS}}
    receipt=verify_submission(scratch,head,payload)
    assert receipt["r32"]["memory"]["coverage"]==1
    bad=json.loads(json.dumps(payload));bad["choices"][0]["description"]="Changed after preparation"
    try:verify_submission(scratch,head,bad)
    except ValueError:pass
    else:raise AssertionError("Divergent choice accepted")
    bad=json.loads(json.dumps(payload));bad["r33_review"]["reviews"].pop("continuity")
    try:verify_submission(scratch,head,bad)
    except ValueError:pass
    else:raise AssertionError("Missing review accepted")
    emit({"stage":"FULL_CONTRACT_REHEARSAL","requirements":len(req),"domains":sum(v["applicable"] for v in domains.values()),"scenes":n,"coverage":receipt["r32"]["memory"]["coverage"],"critical_missing":0,"reviews":len(REVIEWS),"idempotent":True,"changed_choice_rejected":True,"missing_review_rejected":True,"canon_changed":False,"semantic_certification":False})
assert before==[hashfile(p) for p in paths]
emit({"stage":"R33_READ_ONLY","head":head["day"],"unchanged":True,"semantic_certification":False})
