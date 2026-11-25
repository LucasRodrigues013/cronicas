"""Private R31 audit: full source index, provenance, 100 retrieval probes, read-only."""
import hashlib,json,pathlib,sqlite3,time,tempfile,statistics,sys,os
from worldroot import deep_recovery as r31, history_index as hi
from worldroot.memory_continuity import fusion
def lookup(db,q,entity=None,topic=None,role=None,limit=20,strategy='hybrid'):
    if strategy=='fusion':return fusion(db,q,entity,topic,role,limit)
    return r31.retrieve(db,q,entity,topic,role,limit,strategy)
root=pathlib.Path("archive")
candidates=json.loads(pathlib.Path("recovery/r31-historical-candidates.json").read_text())["records"]
def digest(b):return hashlib.sha256(b).hexdigest()
def emit(x):print(json.dumps(x,ensure_ascii=False,sort_keys=True),flush=True)
def guard():
    return {p:digest((root/p).read_bytes()) for p in ["canon/HEAD.json","ops/RESUME.json","history/sources/MANIFEST.json"]}
before=guard()
manifest,sources=hi.read_verified_sources(root)
source_map={m["source_name"]:t for m,t in sources}
# Each previously recovered reference is verified against the original part bytes.
gold=[]
queries=[
 ["Miren estatura postura","Miren aparência física","Miren alta esguia","arqueóloga postura firme","MIREN olhos atentos"],
 ["Serís aparência roupas","Seris Daum estilo cabelo","Serís azul petróleo","comerciante traje verão","Seris cintura marcada"],
 ["Serís olhos rosto","Seris Daum olhos","comerciante cabelos negros","Seris rosto elegante","SERÍS olhos cinzentos"],
 ["Miren ciúmes Serís","Miren rival romance","ciumes de Seris","MIREN conflito afetivo","Miren ciúmes comerciante"],
 ["Serís primeira briga","Miren Lucas ciúmes","Seris sedução fiel","primeira briga casal","SERÍS DAUM provocação"],
 ["Miren Lucas reconstruir confiança","reconciliação casal","confiança atitudes","Lucas pedir desculpas","reconstruir confiança"],
 ["Althea aparência","rainha cabelos loiros","Althea alta elegante","rainha vestido azul","ALTHEA cabelos loiros"],
 ["Althea beleza","rainha beleza extraordinária","beleza da rainha","ALTHEA relatos beleza","Althea aparência majestade"],
 ["Elyan resgate","legionário Elyan vivo","Elyan recuperado","ELYAN está vivo","resgate prisioneiro Elyan"],
 ["legionários resgatados feridos","dois legionários resgatados","legião busca feridos","legionarios retorno resgate","legionários ferimentos"],
 ["Gênese Canal Soberano","Segundo Limiar fluxo","canal soberano reserva","CREATION fluxo estável","GÊNESE 14 5 4"],
 ["Matriz Germinal Convergência","Gênese técnicas desbloqueadas","convergencia voluntaria","domínio vital matriz","Canal Soberano Matriz Germinal"],
 ["Gênese capacidade operacional","CREATION capacidade dimensional","crescimento acumulado","capacidade operacional 300","capacidade dimensional 100"],
 ["Aerún design campus","AERUN inspiração arquitetura","campus circular","AERÚN Apple Park","anel setores jardim"],
 ["Aerún dragão escamas","dragão aparência escamas","AERUN escamas prateadas","dragão azul escuro","escamas azul escuras prateadas"],
 ["mochila bolsas auxiliares","inventário matriz mãe","bolsas inventário compartilhado","mochila dimensional inventário finito","matriz mãe bolsas"],
 ["mochila régua ferramentas","inventário fio medição","ferramenta fixadores","mochila ferramenta medida","régua fio medição"],
 ["Calderva cidade porto farol","cidade portuária infraestrutura","Calderva farol","porto cidade viva","Calderva infraestrutura"],
 ["Calderva bandeiras","bandeiras azuis prateadas","Calderva cores cidade","bandeiras edifícios","bandeiras azuis prata"],
 ["Ciran Varo recuperação","campeão capitão feridos","CÍRAN Varo expressão","Ciran diálogo Varo","CÍRAN naturalmente"]
]
assert len(queries)==len(candidates)==20
for i,c in enumerate(candidates):
    part=next(p for s in manifest["sources"] for p in s["parts"] if p["path"]==c["part_path"])
    raw=(root/part["path"]).read_bytes()
    assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==c["blob_sha"]
    lines=raw.decode("utf-8").split("\n")
    a,b=c["part_lines"]
    assert "\n".join(lines[a-1:b])==c["anchor"],f"candidate {i} literal mismatch"
    src=next(s for s in manifest["sources"] if s["source_name"]==c["source_name"])
    offset=0
    for p in src["parts"]:
        if p["path"]==part["path"]:break
        offset+=(root/p["path"]).read_bytes().count(b"\n")
    gold.append((c,a+offset,b+offset))
emit({"stage":"SOURCE_PROVENANCE","sources":len(sources),"parts":sum(len(s["parts"]) for s in manifest["sources"]),"bytes":sum(s["utf8_bytes"] for s in manifest["sources"]),"candidate_anchors":len(gold)})
with tempfile.TemporaryDirectory() as d:
    db=pathlib.Path(os.environ.get("R31_DB_PATH",str(pathlib.Path(d)/"r31.sqlite")))
    db.parent.mkdir(parents=True,exist_ok=True)
    t=time.monotonic()
    report=r31.build(root,db)
    assert r31.verify_manifest(root,db)
    elapsed=time.monotonic()-t
    # Check every returned window against source lines; coverage and role boundaries.
    counts=0
    with sqlite3.connect(db) as con:
        assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        con.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)")
        for name,body in source_map.items():
            lines=body.splitlines(keepends=True)
            roles={}
            for role,start,ls in r31.sections(body):
                roles.update((n,role) for n in range(start,start+len(ls)))
            covered=set()
            for lo,hi_,role,anchor,sha in con.execute("SELECT line_start,line_end,role,anchor,anchor_sha FROM evidence WHERE source=?",(name,)):
                assert anchor=="".join(lines[lo-1:hi_])
                assert digest(anchor.encode())==sha
                assert all(roles[n]==role for n in range(lo,hi_+1))
                covered.update(range(lo,hi_+1));counts+=1
            assert covered==set(range(1,len(lines)+1))
    emit({"stage":"SQLITE_FULL_INDEX","seconds":round(elapsed,3),"windows":counts,"lines":sum(len(t.splitlines()) for t in source_map.values()),"bytes":db.stat().st_size,"integrity":"ok","coverage":report["coverage"]})
    results=[]
    for strategy in ("legacy","hybrid","contextual","fusion"):
        ranks=[]; durations=[]; misses=[];by_split={}
        for i,(c,lo,hi_) in enumerate(gold):
            for j,q in enumerate(queries[i]):
                entity=c["entity"]
                if entity.startswith("aerun-"):entity="aerun"
                if entity not in r31.ALIASES:entity=None
                # Topic/entity metadata are hints, not ground truth; test unfiltered queries too.
                # No answer synthesis is scored; target is a recovered span.
                start=time.monotonic()
                r=lookup(db,q,entity=entity if j%2==0 else None,role=c["role"],limit=80 if strategy=="fusion" else 20,strategy=strategy)
                durations.append(time.monotonic()-start)
                rank=next((n for n,h in enumerate(r["hits"],1) if h["source"]==c["source_name"] and min(h["line_end"],hi_)-max(h["line_start"],lo)+1>=min(3,hi_-lo+1)),0)
                ranks.append(rank)
                split="regression" if j<3 else "challenge"
                by_split.setdefault(split,[]).append(rank)
                if not rank:misses.append(f"{i+1:02d}-{j+1}")
        row={"strategy":strategy,"n":len(ranks),"hit_at_1":sum(r==1 for r in ranks),"hit_at_5":sum(0<r<=5 for r in ranks),"hit_at_10":sum(0<r<=10 for r in ranks),"hit_at_20":sum(0<r<=20 for r in ranks),"hit_at_80":sum(r>0 for r in ranks) if strategy=="fusion" else None,"mrr":round(sum(1/r for r in ranks if r)/len(ranks),4),"median_ms":round(statistics.median(durations)*1000,2),"p95_ms":round(sorted(durations)[94]*1000,2),"miss_ids":misses,"split_hit20":{k:[sum(0<r<=20 for r in v),len(v)] for k,v in by_split.items()}}
        results.append(row);emit({"stage":"RETRIEVAL",**row})
    # A separate historical reference set, not used to tune the preceding 100 probes.
    # These are held out from this benchmark, not a blind author evaluation.
    heldout_queries={
        "origin":["nascimento Legião","primeiro dia trezentos","origem Criador acampamento"],
        "festival":["Festival dos Trezentos","aniversário duzentos dias irmãos","celebração Legião"],
        "kairon":["Kairon jardinagem","guerreiro planta ramo","mãos enormes tecido"],
        "aeldric":["Aeldric primeira impressão","patriarca Vareth aparência","Criador esperava algo diferente"],
        "aerun":["dragão observou Lucas","AERÚN companhia pessoas","guardião mar respeito poder"],
        "observatorio":["Miren convite Observatório","encontro romântico carta vestido","Crista do Vento Claro convite"],
        "romance":["Miren Lucas reclamação","arqueóloga departamento","Lucas brincadeira manhã"]
    }
    corpus=json.loads((root/"editorial/registries/r30-literary-corpus.json").read_text())["scenes"]
    heldout=[]
    for item in corpus:
        if item["id"] not in heldout_queries:continue
        proof=item["source"]
        body=source_map[proof["source_name"]]
        anchor=proof["anchor"]
        assert body.count(anchor)==1
        pos=body.index(anchor)
        lo=body[:pos].count("\n")+1
        hi_=lo+anchor.count("\n")
        heldout.append((item["id"],proof["source_name"],lo,hi_,proof.get("role","Response")))
    assert len(heldout)==7
    for strategy in ("legacy","hybrid","contextual","fusion"):
        ranks=[]
        for key,name,lo,hi_,role in heldout:
            for q in heldout_queries[key]:
                result=lookup(db,q,role=role,limit=80 if strategy=="fusion" else 20,strategy=strategy)
                rank=next((n for n,h in enumerate(result["hits"],1) if h["source"]==name and min(h["line_end"],hi_)-max(h["line_start"],lo)+1>=3),0)
                ranks.append(rank)
        emit({"stage":"HELDOUT_REFERENCE_PROBES","strategy":strategy,"n":len(ranks),"hit_at_1":sum(r==1 for r in ranks),"hit_at_5":sum(0<r<=5 for r in ranks),"hit_at_20":sum(0<r<=20 for r in ranks),"hit_at_80":sum(r>0 for r in ranks) if strategy=="fusion" else None,"mrr":round(sum(1/r for r in ranks if r)/len(ranks),4),"limitation":"Distinct reference spans; not independent human evaluation."})
    # Negative cases and stable repeated queries, not a claim of semantic abstention.
    for q in ("zzzzworldrootnonexistent123","qzxmissingentity987","nonexistentartifactzzx"):
        assert r31.retrieve(db,q)["status"]=="NOT_RECOVERED"
    a=r31.retrieve(db,"Serís ciúmes",role="Response")
    assert a==r31.retrieve(db,"SERIS CIUMES",role="Response") or [h["id"] for h in a["hits"]]==[h["id"] for h in r31.retrieve(db,"SERIS CIUMES",role="Response")["hits"]]
    assert before==guard()
    emit({"stage":"READ_ONLY","head_unchanged":True,"negative_cases":3,"accent_invariance":True,"semantic_certification":False,"literary_grade":None})
    # Do not claim a release when retrieval is weaker than the reference strategy.
    if results[1]["hit_at_20"]<results[0]["hit_at_20"]:sys.exit(2)
    emit({"stage":"CONTEXTUAL_EXPERIMENT","hit20_delta":results[2]["hit_at_20"]-results[1]["hit_at_20"],"mrr_delta":round(results[2]["mrr"]-results[1]["mrr"],4),"default_strategy":"hybrid","release_blocked":True,"reason":"development benchmark; independent holdout required"})
