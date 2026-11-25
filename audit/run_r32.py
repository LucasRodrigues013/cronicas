"""R32 evaluation of original immutable D574 draft (not a new canon episode)."""
from __future__ import annotations
import hashlib,json,pathlib,time,os
from worldroot import memory_graph as graph
from worldroot.semantic_memory import DenseIndex
from worldroot.memory_continuity import fusion,review_creation,digest,recent_candidates,arc_review
from worldroot.experience_quality import render_choices,compare_versions
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
extra=json.loads(pathlib.Path("recovery/r32-additional-evidence.json").read_text())
staged["records"].extend(extra["records"])
g=graph.build(root,staged,db)
graph.write_graph(g,db.parent/"r32-graph.sqlite")
emit({"stage":"GRAPH","nodes":len(g["nodes"]),"edges":len(g["edges"]),"dossiers":len(g["dossiers"]),"dossiers_with_observations":sum(bool(d["observations"]) for d in g["dossiers"].values()),"dossiers_with_candidates":sum(any(d.get("candidate_evidence",{}).values()) for d in g["dossiers"].values()),"power_benchmarks":len(g["power"]["benchmarks"]),"events":len(g["events"]),"knowledge":len(g["knowledge"]),"inventory_candidates":len(g["inventory"]["events"]),"power_candidates":len(g["power"]["events"]),"historical_power":len(g["power"]["historical"]),"relationship_candidates":len(g["relationships"]),"plots":len(g["plots"]),"assets":len(g["assets"]),"rejected_events":len(g["rejected_events"]),"unresolved_edges":g["unresolved_edges"],"canon_changed":False})
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
# Freeze twenty material context requirements for the archived D574 creation.
# Independent retrieval over all 44 prior episodes; only exact source spans count.
questions=[
 ("correspondência Halvern dia 569",60,"event"),("Renshar caiu dia 567",64,"event"),
 ("Lucas nome Velkar Draen",68,"knowledge"),("segunda unidade instrumentos ensaio",152,"inventory"),
 ("Naira viagem demonstração velocidade reduzida",156,"event"),("enxurrada ponte crianças feridos",268,"event"),
 ("mensageira Kheran dia 571",338,"knowledge"),("sobrevivente Renshar cobrança imperial",344,"knowledge"),
 ("Lucas desconhecia nome técnica",354,"knowledge"),("governo representação preliminar conferência",360,"promise"),
 ("representante civil autorização escrita",364,"event"),("Althea Thalor confirmação conferência",404,"promise"),
 ("Althea fronteiras estoques não guerra",408,"event"),("Serakh Lethira sustentação",456,"event"),
 ("Ruptura Soberana Velkar",460,"power"),("Bressa divergência selo remessas autoria",562,"promise"),
 ("ARGOS pousou três pessoas",592,"event"),("mensageira representante sobrevivente Renshar",596,"event"),
 ("Miren escuta reservada Astra Varo",650,"relationship"),("sessão preparatória amanhã Lysa",680,"promise")]
replay=[];checked={}
for i,(q,line,domain) in enumerate(questions):
    rid="D574-"+str(i+1)
    item={"id":rid,"query":q,"domain":domain,"critical":i in (1,2,8,11,14,15,19),"role":"Response"}
    replay.append(item)
    hits=recent_candidates(entries,q,limit=80)
    h=next((h for h in hits if h["source"]==last["id"] and h["line_start"]<=line<=h["line_end"]),None)
    if h:
        checked[rid]={"source":h["source"],"line_start":h["line_start"],"line_end":h["line_end"],"anchor_sha":h["anchor_sha"],"claim":"Reference located for "+q,"status":"REVIEWED_SUPPORTED"}
rep=review_creation(root,head,replay,checked)
emit({"stage":"CREATION_RETRIEVAL_REPLAY","requirements":20,"found":rep["verified"],"coverage":rep["coverage"],"critical_missing":rep["critical_missing"],"missing":rep["missing"],"status":rep["status"],"limitation":"Retrospective 20 reference requirements; lexical span overlap is not independent semantic approval."})
# Noncanonical prototype: same D574 prose, only re-render ending options for comparison.
packet={"options":[
 {"number":1,"track":"main","arc_id":"halvern","title":"A carta que precisa atravessar a guerra","promise":"Levar assistência e procurar uma rota autorizada para a carta de Ordan.","reward":"Auxílio recebido e possibilidade de contato familiar.","risk":"Acesso recusado ou entrega interrompida.","next_link":"Halvern e conferência","unselected_progress":"AERÚN conduz contatos.","guaranteed_success":False,"combines_all":False},
 {"number":2,"track":"secondary","arc_id":"ferro","title":"O expresso que mudou Três Arcos","promise":"Acompanhar a ferrovia e as vidas dos transportadores.","reward":"Transformação vivida do transporte civil.","risk":"Conflito econômico ou necessidade de novos ensaios.","next_link":"Horizonte de Ferro","unselected_progress":"A Forja mantém a investigação.","guaranteed_success":False,"combines_all":False},
 {"number":3,"track":"secondary","arc_id":"mar","title":"O oceano antes da conquista","promise":"Acompanhar o reconhecimento das ilhas por Varkhess e Serina.","reward":"Novas informações sobre desaparecidos e alianças.","risk":"Perigos marítimos e interesses conflitantes.","next_link":"Campanha marítima","unselected_progress":"Povos respondem conforme suas informações.","guaranteed_success":False,"combines_all":False},
 {"number":4,"track":"secondary","arc_id":"seis-marcas","title":"A oficina que perdeu seu nome","promise":"Acompanhar a perícia da amostra antiga com os mestres anões.","reward":"Uma propriedade ou técnica demonstrável.","risk":"Uma interpretação precipitada ou descoberta perigosa.","next_link":"Seis Marcas","unselected_progress":"As demais frentes continuam conforme causalidade.","guaranteed_success":False,"combines_all":False}
],"free_action":True,"author_choice_recorded":False}
assert not arc_review(packet)["errors"]
rendered=render_choices(packet,paths[-1].parent.parent.name)
assert rendered["markup"].count('button block color="secondary" variant="outline"')==4
split=draft.index("## AS CINCO PORTAS")
prototype=rendered["body_declaration"]+"\n"+draft[:split]+rendered["markup"]
comp=compare_versions(draft,prototype)
(db.parent/"r32-literary-comparison.json").write_text(json.dumps({"status":"NONCANONICAL_EDITORIAL_PROTOTYPE","comparison":comp,"option_prototype":rendered},ensure_ascii=False))
emit({"stage":"CHOICE_DESIGN_COMPARISON","old_special_highlighted":'<button block onClick' in draft[split:],"new_equal_buttons":4,"old_presentation":comp["A"]["structure"]["status"],"new_presentation":comp["B"]["structure"]["status"],"human_preference":None,"canon_changed":False})
emit({"stage":"LITERARY_BASELINE","episode":paths[-1].parent.parent.name,"metrics":measure(draft),"choice":choice_review(draft),"presentation":presentation_preflight(draft),"literary_grade":None})
# Actual dense benchmark, frozen previous 121 questions from code, not new labels.
# Load just the declarative query list through AST, never execute prior script.
import ast
tree=ast.parse(pathlib.Path("audit/run_r31.py").read_text())
queries=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="queries" for t in n.targets))
held=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="heldout_queries" for t in n.targets))
_,raw=read_verified_sources(root);bodies={m["source_name"]:t for m,t in raw}
gold=[]
for i,c in enumerate(g["historical_observations"][:len(queries)]):
    for q in queries[i]:gold.append(("development",q,c["source"],c["line_start"],c["line_end"],c["role"]))
corpus=json.loads((root/"editorial/registries/r30-literary-corpus.json").read_text())["scenes"]
for row in corpus:
    if row["id"] not in held:continue
    s=row["source"];span=graph.locate(bodies[s["source_name"]],s["anchor"])
    assert span
    for q in held[row["id"]]:gold.append(("additional",q,s["source_name"],span["line_start"],span["line_end"],s.get("role","Response")))
start=time.monotonic();idx=DenseIndex(db)
emit({"stage":"DENSE_BUILD","backend":"lsa","vectors":len(idx.rows),"dimension":idx.vectors.shape[1],"seconds":round(time.monotonic()-start,3)})
idx.save_lsa(db.parent/"r32-lsa")
reloaded=DenseIndex.load_lsa(db,db.parent/"r32-lsa")
assert [h["id"] for h in idx.search("Miren",limit=20)]==[h["id"] for h in reloaded.search("Miren",limit=20)]
emit({"stage":"DENSE_READBACK","same_top20":True})
for strategy in ("dense","combined"):
    ranks={"development":[],"additional":[]};start=time.monotonic()
    for split,q,source,lo,hi,role in gold:
        hits=idx.search(q,role,80) if strategy=="dense" else idx.combined(q,role=role,limit=160)
        rank=next((i for i,h in enumerate(hits,1) if h["source"]==source and min(h["line_end"],hi)-max(h["line_start"],lo)+1>=min(3,hi-lo+1)),0)
        ranks[split].append(rank)
    emit({"stage":"DENSE_EVAL","strategy":strategy,"seconds":round(time.monotonic()-start,3),"splits":{k:{"n":len(v),"hit20":sum(0<r<=20 for r in v),"hit80":sum(0<r<=80 for r in v),"hit160":sum(r>0 for r in v),"mrr":round(sum(1/r for r in v if r)/len(v),4)} for k,v in ranks.items()}})
assert before==[sha(p) for p in paths]
emit({"stage":"R32_READ_ONLY","unchanged":True,"head":head["day"]})
