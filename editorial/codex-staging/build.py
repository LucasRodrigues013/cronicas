"""Read-only historical codex staging. No canon or production policy changes."""
import argparse,collections,hashlib,json,re,sqlite3,tempfile,unicodedata
from pathlib import Path
from worldroot.history_index import read_verified_sources
from worldroot.deep_recovery import sections
from worldroot.living_world import load_canonical,project,literal_body
from worldroot.literary_experience import source_registry,_historical_anchor
from worldroot.character_design import load_design
from worldroot.git_cycle import verify_episode,verify_db

def read(p):return json.loads(p.read_text(encoding="utf-8"))
def dump(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def hashstr(x):return hashlib.sha256(x.encode()).hexdigest()
def norm(x):return " ".join(re.findall(r"[^\W_]+",unicodedata.normalize("NFKD",x).encode("ascii","ignore").decode().casefold()))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
FIELDS={
"character":["appearance","age","voice","personality","relationships","role","origin","location","knowledge","powers","inventory","history"],
"guardian":["species","appearance","dimensions","habitat","powers","behavior","relationships","location","history"],
"entity":["nature","appearance","powers","behavior","location","history"],
"asset":["design","dimensions","capabilities","tests","lifecycle","location","owner","inventory","history"],
"plot":["status","participants","events","dependencies","history"],
"place":["geography","architecture","population","governance","culture","economy","connections","history"],
"organization":["origin","leadership","members","purpose","resources","relationships","history"],
"power":["origin","capabilities","limits","demonstrations","evolution","history"]}
def typ(k):
    if k in FIELDS:return k
    if k in ("institution",):return "organization"
    if k in ("city","territory","kingdom","city_or_territory","region","location","sea","building","infrastructure","archaeological_site"):return "place"
    return "entity"
PATTERNS={
"appearance":r"cabel|olhos|barba|rosto|estatura|pele |vestia|manto|armadura",
"age":r"\bidade\b|\b\d+ anos\b",
"voice":r"\bvoz\b|\btom de voz\b|sorr|riso",
"relationships":r"amig|espos|filh|irmã|irmão|casament|companheir",
"role":r"comand|capitão|conselheir|engenheir|arqueólog|pesquisador|rainha|soberan",
"powers":r"magia|poder|gênese|energia|habilidade|runas",
"capabilities":r"capacidade|sustentação|propulsão|velocidade|alcance|energia",
"dimensions":r"\b\d+(?:[,.]\d+)?\s*(?:m²|km²|metros|quilômetros|m\b|km\b|pavimentos|andares)",
"architecture":r"torre|arco|coluna|praça|edifício|jardim|salão|ponte|muralha",
"population":r"habitantes|moradores|população|residentes",
"governance":r"conselho|governo|assembleia|autoridade|soberania",
"lifecycle":r"construí|criaç|concluí|operacion|test|protótipo",
"behavior":r"observ|reag|moviment|rug|voou|respir",
"location":r"cheg|partiu|viajou|estava|pous|atravess|permaneceu"}
SPEAKER=re.compile(r"^\s*(?:\*\*)?([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ0-9 '\-’]{1,44})\s*[—–-](?:\*\*)?\s+\S")
PLACE=re.compile(r"^\s*(?:\*\*|#{1,6}\s+)?DIA\s+\d+[^\n]{0,80}?(?:\||[—–])\s*([^*\n]{3,100})",re.I)
BAD={"dia","lucas","sistema","opcao","escolha","parte","fim","checkpoint","narrador","voz","proximo","resultado","evento","worldroot","nota","objetivo","consequencia"}
def schema(db):
    db.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE records(domain TEXT,id TEXT PRIMARY KEY,body TEXT NOT NULL);
    CREATE TABLE aliases(alias TEXT,id TEXT REFERENCES records(id),PRIMARY KEY(alias,id));
    CREATE TABLE sources(id TEXT PRIMARY KEY,sha TEXT,status TEXT,day INTEGER,line_count INTEGER);
    CREATE TABLE observations(id INTEGER PRIMARY KEY,entity TEXT REFERENCES records(id),source TEXT,field TEXT,status TEXT,claim TEXT,anchor TEXT,line INTEGER,anchor_sha TEXT);
    CREATE TABLE mentions(entity TEXT REFERENCES records(id),source TEXT REFERENCES sources(id),count INTEGER,first_line INTEGER,last_line INTEGER,PRIMARY KEY(entity,source));
    CREATE TABLE candidates(kind TEXT,name TEXT,source TEXT REFERENCES sources(id),count INTEGER,first_line INTEGER,sample TEXT,PRIMARY KEY(kind,name,source));
    CREATE TABLE images(id TEXT PRIMARY KEY,body TEXT);
    CREATE VIRTUAL TABLE search USING fts5(entity,field,claim,anchor,tokenize='unicode61 remove_diacritics 2');
    """)
def lookup(db,name,kind=None):
    rows=[json.loads(row[0]) for row in db.execute("SELECT r.body FROM aliases a JOIN records r ON r.id=a.id WHERE a.alias=? ORDER BY r.id",(norm(name),))]
    return [r for r in rows if r["kind"] in kind] if kind else rows
def prepare_preview(db,request,head):
    if json.loads(db.execute("SELECT value FROM meta WHERE key='head'").fetchone()[0])!=head:raise ValueError("Stale codex")
    names=[x["name"] for x in request.get("r34_intent",{}).get("characters",[])]
    result={}
    for n in names:
        matches=lookup(db,n,{"character","guardian","entity"})
        result[n]={"resolution":"unique" if len(matches)==1 else "ambiguous" if matches else "missing","records":matches}
    return {"scope":"candidate_only","head":head,"characters":result,"canon_changed":False}
def scan(db,source,sha,status,day,lines,aliases):
    existing=db.execute("SELECT sha,status FROM sources WHERE id=?",(source,)).fetchone()
    if existing:
        if existing!=(sha,status):raise ValueError("source changed; rebuild from verified manifest")
        return False
    counts={};candidates={};samples=collections.Counter()
    rx=re.compile(r"(?<!\w)(?:"+"|".join(re.escape(a) for a in sorted(aliases,key=lambda x:(-len(x),x)))+r")(?!\w)")
    patterns={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
    with db:
        db.execute("INSERT INTO sources VALUES(?,?,?,?,?)",(source,sha,status,day,len(lines)))
        for i,line in lines:
            if not line.strip() or len(line)>4000 or line.lstrip().startswith(("<","{@","|")):continue
            n=norm(line);hits=set()
            for m in rx.finditer(n):
                ids=aliases[m.group()]
                if len(ids)==1:hits.update(ids)
                else:
                    key=("ambiguous_alias",m.group())
                    c=candidates.setdefault(key,[0,i,line[:450]]);c[0]+=1
            for eid in hits:
                c=counts.setdefault(eid,[0,i,i]);c[0]+=1;c[2]=i
                for field,pat in patterns.items():
                    if pat.search(line) and samples[eid,field]<2:
                        db.execute("INSERT INTO observations(entity,source,field,status,claim,anchor,line,anchor_sha) VALUES(?,?,?,?,?,?,?,?)",(eid,source,field,"CONTEXT_CANDIDATE_NOT_ATTRIBUTED",None,line,i,hashstr(line)))
                        samples[eid,field]+=1
            for kind,match in (("speaker",SPEAKER.match(line)),("scene_location",PLACE.match(line))):
                if not match:continue
                name=norm(match.group(1))
                if not name or name in BAD or name in aliases or len(name.split())>8 or name.startswith(("dia ","parte ","opcao ","livro ","capitulo ")) or (kind=="speaker" and (re.fullmatch(r"[ivxlcdm]+",name) or name in {"menina","menino","mulher","homem","crianca","senhora","senhor","funcionaria","mensageiro","trabalhador","comerciante","soldado","guarda","operador","operadora","voz","jovem","velho","velha"})):continue
                key=(kind,name);c=candidates.setdefault(key,[0,i,line[:450]]);c[0]+=1
        db.executemany("INSERT INTO mentions VALUES(?,?,?,?,?)",[(k,source,*v) for k,v in counts.items()])
        db.executemany("INSERT INTO candidates VALUES(?,?,?,?,?,?)",[(k,n,source,*v) for (k,n),v in candidates.items()])
    return True
def main(root,out,engine):
    head=read(root/"canon/HEAD.json");resume=read(root/"ops/RESUME.json")
    source_hash=hashstr(dump(head));verify_db(root,head)
    manifest,raw=read_verified_sources(root)
    closed,warnings=load_canonical(root,head)
    if warnings:raise ValueError(str(warnings))
    historic=source_registry(root,head);world=project(root,head);design=load_design(root)
    seed=read(root/"editorial/codex-staging/seed.json");visual=read(root/"editorial/codex-staging/visual-inventory.json")
    records={};aliases=collections.defaultdict(set)
    def add(x,kind=None):
        eid=x["id"];rec=records.setdefault(eid,{"id":eid,"name":x["name"],"kind":kind or x.get("kind","entity"),"aliases":[],"sources":[],"observations":[]})
        rec["aliases"]=sorted(set(rec["aliases"]+[x["name"],eid]+x.get("aliases",[])))
        return rec
    for x in world["assets"]:add(x,"asset")["registry_asset"]=x
    for x in read(root/"editorial/registries/r28-living-world.json")["entities"]:add(x)["registry_identity"]=x
    for x in historic["characters"]:add(x,"entity")["observations"].extend(x["observations"])
    for x in design["profiles"]:add(x,"character")["author_design"]=x
    for x in seed["entities"]:add(x)["audit_seed"]=True
    for x in world["plots"]:
        y={**x,"id":"plot:"+x["id"]}
        add(y,"plot")["registry_plot"]=x
    # Distinguish shared names and alternate IDs; do not merge institute with dragon.
    records["aerun-guardiao"]["kind"]="guardian";records["niraven"]["kind"]="entity";records["aeldric"]["kind"]="character"
    records["aerun-instituto"]["aliases"]+=["AERÚN","AERUN"]
    records["aerun-guardiao"]["aliases"]+=["AERÚN","AERUN"]
    records["lyra"]["aliases"]+=["Lira","Lyra","Lira Selen Vareth"]
    records["lysa"]["aliases"]+=["Lisa"]
    for e in records.values():
        for a in e["aliases"]:
            if norm(a):aliases[norm(a)].add(e["id"])
    source_map={m["source_name"]:(m,t) for m,t in raw}
    for x in read(engine/"recovery/r31-historical-candidates.json")["records"]+seed.get("literal_candidates",[]):
        eid=x["entity"]
        if eid in records:
            proof=_historical_anchor(source_map,x)
            records[eid]["observations"].append({"field":x["field"],"value":x["claim"],"source":x,"proof":proof,"state":"LITERAL_CANDIDATE_NOT_CANON" if proof else "UNVERIFIED"})
    for e in records.values():
        required=FIELDS[typ(e["kind"])]
        observed={x["field"] for x in e["observations"] if x.get("proof")}
        if "role_historical" in observed:observed.add("role")
        if "relationship_voice" in observed or "voice_relationship" in observed:observed.update(("voice","relationships"))
        if "relationship" in observed:observed.add("relationships")
        if e.get("author_design"):observed.add("appearance")
        if e.get("registry_asset",{}).get("evidence_status")=="SOURCE_MATCH":
            observed.update(("capabilities","tests","lifecycle","history"))
        if e.get("registry_plot",{}).get("evidence_status")=="SOURCE_MATCH":observed.update(("status","history"))
        e["required_fields"]=required;e["unresolved_fields"]=[k for k in required if k not in observed]
        e["completeness"]="PARTIAL_REVIEW_REQUIRED"
        e["visual_refs"]=[x["file_id"] for x in visual["items"] if e["id"] in x.get("entities",[])]
        e["visual_conflicts"]=[x for x in visual["conflicts"] if x["entity"]==e["id"]]
    out.mkdir(parents=True,exist_ok=True)
    path=out/"codex.sqlite"
    if path.exists():path.unlink()
    db=sqlite3.connect(path)
    schema(db)
    db.executemany("INSERT INTO meta VALUES(?,?)",[(k,dump(v)) for k,v in {"schema":"worldroot-universal-audit-v1","head":head,"pending":resume.get("latest_unclosed_draft"),"scope":"AUDIT_ONLY"}.items()])
    db.executemany("INSERT INTO records VALUES(?,?,?)",[("dossiers" if e["kind"]!="asset" and e["kind"]!="plot" else "assets" if e["kind"]=="asset" else "plots",e["id"],dump(e)) for e in records.values()])
    db.executemany("INSERT INTO aliases VALUES(?,?)",[(a,e) for a,ids in aliases.items() for e in ids])
    db.executemany("INSERT INTO images VALUES(?,?)",[(x["file_id"],dump(x)) for x in visual["items"]])
    db.commit()
    scan_aliases={a:({eid for eid in ids if records[eid]["kind"]!="plot"} or ids) for a,ids in aliases.items()}
    for m,body in raw:
        # All historical response sections scanned; prompts retained in the immutable archive.
        lines=[(start+i,l.rstrip("\r\n")) for role,start,rows in sections(body) if role=="Response" for i,l in enumerate(rows)]
        scan(db,"history:"+m["source_name"],m["sha256"],"HISTORICAL_RESPONSE_UNREVIEWED",None,lines,scan_aliases)
    for e in closed:
        text=e["text"];body=literal_body(text);start=text[:text.find(body)].count("\n")+1
        scan(db,"episode:"+e["id"],e["sha256"],"CLOSED",e["day"],[(start+i,l) for i,l in enumerate(body.splitlines())],scan_aliases)
    pending=resume.get("latest_unclosed_draft")
    assert pending and pending["day"]==580
    draft,man=verify_episode(root,pending["episode_id"])
    literal=(root/"episodes"/pending["episode_id"]/"draft/narrativa_integral.md").read_text(encoding="utf-8")
    assert hashstr(literal)==pending["source_sha256"]
    body=literal_body(literal);start=literal[:literal.find(body)].count("\n")+1
    args=("episode:"+pending["episode_id"],pending["source_sha256"],"PENDING_NOT_CLOSED",pending["day"],[(start+i,l) for i,l in enumerate(body.splitlines())],scan_aliases)
    assert scan(db,*args)
    before=db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    assert not scan(db,*args)
    assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]==before
    try:scan(db,args[0],"bad",*args[2:])
    except ValueError:pass
    else:raise AssertionError("changed source accepted")
    assert len(lookup(db,"Lira"))==1 and lookup(db,"Lira")[0]["id"]=="lyra"
    assert lookup(db,"Lysa")[0]["id"]=="lysa"
    assert len(lookup(db,"AERÚN"))==2
    assert lookup(db,"Bressa",{"character"})[0]["id"]=="bressa"
    for e in records.values():
        for o in e["observations"]:
            s=o.get("source",{});proof=o.get("proof")
            if proof and s.get("anchor"):
                a=s["anchor"]
                db.execute("INSERT INTO observations(entity,source,field,status,claim,anchor,line,anchor_sha) VALUES(?,?,?,?,?,?,?,?)",(e["id"],s.get("source_name") or s.get("episode"),o["field"],o["state"],o.get("value"),a,proof.get("line"),hashstr(a)))
    for e in records.values():
        row=e.get("registry_asset") or e.get("registry_plot")
        if row and row.get("evidence_status")=="SOURCE_MATCH":
            source=row["source"];a=source["anchor"]
            for k in ("capabilities","tests","state","status","progress"):
                if row.get(k):
                    db.execute("INSERT INTO observations(entity,source,field,status,claim,anchor,line,anchor_sha) VALUES(?,?,?,?,?,?,?,?)",(e["id"],source["episode"],k,"SOURCE_MATCH_EDITORIAL_NOT_CURRENT",str(row[k]),a,source.get("line"),hashstr(a)))
    db.execute("INSERT INTO search SELECT entity,field,COALESCE(claim,''),anchor FROM observations")
    db.commit()
    assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
    assert db.execute("SELECT count(*) FROM search WHERE search MATCH 'Káiron'").fetchone()[0]>0
    req=read(root/"requests"/(pending["episode_id"]+".json"))
    preview=prepare_preview(db,req,head)
    from worldroot.deep_recovery import build as build_recovery
    from worldroot.memory_continuity import creation_packet
    with tempfile.TemporaryDirectory() as td:
        deep=Path(td)/"deep.sqlite"
        build_recovery(root,deep)
        probes=[{"id":"probe-kairon","domain":"identity","query":"Káiron aparência olhos dourados","entity":"kairon","critical":True},{"id":"probe-argos","domain":"inventory","query":"ARGOS ASCENDENTE capacidade","entity":"argos","critical":True},{"id":"probe-orven","domain":"identity","query":"Orven cabelos grisalhos","entity":"orven","critical":True}]
        result=creation_packet(root,deep,probes,head=head,graph_db=path,candidate_limit=10)
        integration={row["requirement"]["id"]:[item["id"] for item in row["graph_candidates"]] for row in result["items"]}
        assert all(probe["entity"] in integration[probe["id"]] for probe in probes)
    try:prepare_preview(db,req,{**head,"sequence":-1})
    except ValueError:pass
    else:raise AssertionError("stale head accepted")
    stats={"sources":db.execute("SELECT count(*) FROM sources").fetchone()[0],"historical_sources":len(raw),"historical_parts":sum(len(m["parts"]) for m,_ in raw),"historical_bytes":manifest["total_source_bytes"],"closed_episodes":len(closed),"pending_episodes":1,"scan_lines":db.execute("SELECT sum(line_count) FROM sources").fetchone()[0],"records":len(records),"categories":dict(collections.Counter(e["kind"] for e in records.values())),"candidate_contexts":db.execute("SELECT count(*) FROM observations WHERE status='CONTEXT_CANDIDATE_NOT_ATTRIBUTED'").fetchone()[0],"source_matched_observations":db.execute("SELECT count(*) FROM observations WHERE status!='CONTEXT_CANDIDATE_NOT_ATTRIBUTED'").fetchone()[0],"mentions":db.execute("SELECT sum(count) FROM mentions").fetchone()[0],"unresolved_speaker_names":db.execute("SELECT count(DISTINCT name) FROM candidates WHERE kind='speaker'").fetchone()[0],"unresolved_scene_location_names":db.execute("SELECT count(DISTINCT name) FROM candidates WHERE kind='scene_location'").fetchone()[0],"image_metadata":len(visual["items"]),"images_visually_inspected":sum(x["review_status"]=="VISUALLY_INSPECTED" for x in visual["items"]),"alias_collisions":{k:sorted(v) for k,v in aliases.items() if len(v)>1},"fts_integrity":True,"incremental_pending_idempotence":True,"changed_source_rejected":True,"stale_head_rejected":True,"r35_preview":{n:x["resolution"] for n,x in preview["characters"].items()},"head_unchanged":hashstr(dump(read(root/"canon/HEAD.json")))==source_hash,"semantic_certification":False,"existing_r35_graph_retrieval_test":integration,"production_integration":False}
    assert stats["head_unchanged"]
    queue=[{"kind":k,"name":n,"mentions":c,"source_count":s} for k,n,c,s in db.execute("SELECT kind,name,sum(count),count(*) FROM candidates GROUP BY kind,name ORDER BY sum(count) DESC,kind,name")]
    for e in records.values():
        e["mention_count"]=db.execute("SELECT COALESCE(sum(count),0) FROM mentions WHERE entity=?",(e["id"],)).fetchone()[0]
        e["candidate_fields"]=[x[0] for x in db.execute("SELECT DISTINCT field FROM observations WHERE entity=? AND status='CONTEXT_CANDIDATE_NOT_ATTRIBUTED' ORDER BY field",(e["id"],))]
    write(out/"catalog.json",{"head":head,"scope":"STAGING_ONLY_NOT_CANON","records":list(records.values()),"queue":queue,"visual_conflicts":visual["conflicts"]})
    write(out/"audit.json",stats);write(out/"r35-preview.json",preview)
    db.close();print(json.dumps(stats,ensure_ascii=False))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path,required=True);p.add_argument("--engine",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(a.archive_root,a.out,a.engine)
