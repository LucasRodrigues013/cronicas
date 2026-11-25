"""R31: evidence-first deep transcript recovery; never writes canon.

Uses R30 and its verified six-source manifest. Candidate search is not semantic
certification. Author prompts and assistant responses remain distinct.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import tempfile
import re
import sqlite3
import unicodedata
from pathlib import Path
from .history_index import read_verified_sources
from .literary_experience import writer_brief

SCHEMA = "worldroot-r31-deep-recovery-v3"
ROLE = re.compile(r"^## (Prompt|Response):\s*$")
DAY = re.compile(r"\bDIA\s+(\d{1,3})\b", re.I)
TOPICS = {
    "appearance": r"cabel|olhos|rosto|feições|postura|esgui|cintura|quadris|silhueta|beleza|vestid|estatura|pele|barba|decote",
    "relationship": r"ciúm|sedu|briga|reconcil|casamento|esposa|marido|promess|beij|amizade|irmã",
    "power": r"gênese|creation|canal soberano|limiar|reserva|fluxo|matriz germinal|exponencial",
    "inventory": r"inventário|mochila|bolsa|katana|armadura|equipamento|guardad|presente|entreg|consum",
    "world": r"brasão|bandeira|arquitetura|distrito|capital|território|cidade|design|inspir|anel",
    "event": r"resgat|desaparecid|captur|batalha|vitória|derrota|ferid|viagem|chegou",
    "voice": r"gritou|sussur|respondeu|iron|humor|gargalh",
    "sensory": r"cheir|aroma|perfume|textura|vento|luz|som|eco|frio|calor|sabor",
    "epic": r"dragão|exército|maravilha|colossal|imens|batalha|assombro|horizonte|vitória",
}
ALIASES = {
    "miren": ("Miren",), "lucas": ("Lucas Rodrigues", "Lucas", "Criador"),
    "lira": ("Lira Selen Vareth", "Lira"), "ciran": ("Círan", "Ciran"),
    "seris": ("Serís Daum", "Seris Daum", "Serís"),
    "althea": ("Althea",), "varo": ("Varo",), "kael": ("Kael",),
    "kairon": ("Káiron", "Kairon"), "aerun": ("AERÚN", "AERUN"),
    "calderva": ("Calderva",), "genese": ("GÊNESE", "CREATION"),
    "inventory": ("mochila dimensional", "Matriz-Mãe", "inventário"),
    "elyan": ("Elyan",), "legiao": ("Legião", "Legionário", "legionários"),
    "astra": ("Astra",), "lysa": ("Lysa",), "brannik": ("Brannik",),
    "nox": ("NÓX", "NOX"), "caedren": ("Caedren",), "aeldric": ("Aeldric",),
    "yra": ("Yra",), "talis": ("Talis",), "thaeron": ("Thaeron",),
    "seron": ("Seron",), "naira": ("Naira",), "rumo": ("Rumo",),
    "argos": ("ARGOS",), "leviata": ("LEVIATÃ", "Leviatã"),
}

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.casefold())
                   if not unicodedata.combining(c))

def tokens(s):
    return re.findall(r"[^\W_]+", norm(s), re.UNICODE)

def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sections(body):
    """Every source line is assigned to its original role and section."""
    role, start, buf = "EXPORT_METADATA", 1, []
    for n, line in enumerate(body.splitlines(keepends=True), 1):
        m = ROLE.fullmatch(line.strip())
        if m:
            if buf:
                yield role, start, buf
            role, start, buf = m.group(1), n, []
        buf.append(line)
    if buf:
        yield role, start, buf

def windows(body, width=18, stride=9):
    """Overlapping windows never cross a prompt/response boundary."""
    if not 1 <= stride <= width <= 100:
        raise ValueError("Invalid window geometry")
    for role, start, lines in sections(body):
        for i in range(0, len(lines), stride):
            group = lines[i:i+width]
            yield role, start+i, start+i+len(group)-1, "".join(group)

def contextual_windows(body, width=18, stride=9):
    for role, start, lines in sections(body):
        for i in range(0, len(lines), stride):
            group = lines[i:i+width]
            yield role,start,start+i,start+i+len(group)-1,"".join(group)

def build(root, db):
    manifest, sources = read_verified_sources(Path(root))
    db = Path(db)
    # Derived database only, outside the archive to avoid accidental canon writes.
    if db.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("R31 projection must be outside archive")
    if db.exists():
        raise FileExistsError("Use a fresh projection path")
    fd, temporary = tempfile.mkstemp(prefix=".r31-", suffix=".sqlite", dir=db.parent)
    os.close(fd)
    temp = Path(temporary)
    try:
        with sqlite3.connect(temp) as c:
            c.executescript("""
            CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE evidence(id INTEGER PRIMARY KEY, source TEXT, source_sha TEXT,
              role TEXT, line_start INTEGER, line_end INTEGER, anchor TEXT, anchor_sha TEXT,
              topics TEXT, entities TEXT, section_start INTEGER, near_entities TEXT NOT NULL DEFAULT '');
            CREATE INDEX evidence_location ON evidence(source,section_start,line_start);
            CREATE VIRTUAL TABLE search USING fts5(anchor, entities, topics,
              content='evidence',content_rowid='id',tokenize='unicode61 remove_diacritics 2');
            """)
            stats=[]
            entity_patterns = {key: re.compile(r"(?<!\w)(?:"+"|".join(re.escape(norm(a)) for a in aliases)+r")(?!\w)") for key, aliases in ALIASES.items()}
            topic_patterns = {key: re.compile(p, re.I) for key,p in TOPICS.items()}
            for meta, body in sources:
                count=0
                for role, section_start, lo, hi, anchor in contextual_windows(body):
                    nt=norm(anchor)
                    entities=[key for key, pattern in entity_patterns.items() if pattern.search(nt)]
                    topics=[key for key, pattern in topic_patterns.items() if pattern.search(anchor)]
                    c.execute("INSERT INTO evidence(source,source_sha,role,line_start,line_end,anchor,anchor_sha,topics,entities,section_start) VALUES(?,?,?,?,?,?,?,?,?,?)",
                              (meta["source_name"],meta["sha256"],role,lo,hi,anchor,_sha(anchor)," ".join(topics)," ".join(entities),section_start))
                    count+=1
                stats.append({"source":meta["source_name"],"lines":len(body.splitlines()),"windows":count})
            # Entity mentions in nearby windows are context hints only, never attributed facts.
            c.execute("""WITH context AS (SELECT id,group_concat(entities,' ') OVER (PARTITION BY source,section_start ORDER BY line_start ROWS BETWEEN 4 PRECEDING AND 4 FOLLOWING) AS nearby FROM evidence) UPDATE evidence SET near_entities=(SELECT nearby FROM context WHERE context.id=evidence.id)""")
            c.execute("INSERT INTO search(search) VALUES('rebuild')")
            c.execute("INSERT INTO meta VALUES('schema',?)",(SCHEMA,))
            c.execute("INSERT INTO meta VALUES('manifest_sha',?)",(_sha(json.dumps(manifest,sort_keys=True,ensure_ascii=False)),))
            c.execute("INSERT INTO meta VALUES('coverage',?)",(json.dumps(stats),))
            if c.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                raise ValueError("Projection integrity failure")
        # Atomic no-clobber publication; existing valid projection is never removed.
        os.link(temp, db)
        return {"schema":SCHEMA,"coverage":stats,"canon_changed":False,"semantic_certification":False}
    finally:
        temp.unlink(missing_ok=True)

# Lexical expansion is domain-general, not a learned embedding or answer lookup.
SYNONYM_GROUPS = (
    "estatura altura alto alta altos altas esguia esguio",
    "aparencia fisica fisico feicoes rosto cabelos olhos silhueta postura beleza elegante",
    "roupa roupas traje trajes vestido vestimenta vestia tecido",
    "ciume ciumes rival rivalidade seducao seduzir briga conflito",
    "reconciliacao reconciliar desculpa desculpas confianca atitudes",
    "resgate resgatado resgatados resgatamos recuperar recuperado libertar",
    "ferido feridos ferimento ferimentos recuperacao",
    "design desenho projeto arquitetura inspiracao inspirado inspirada",
    "cidade cidade portuaria porto portos costeira litoral",
    "bandeira bandeiras brasao simbolo cores identidade",
    "capacidade potencia poder fluxo reserva crescimento",
    "escama escamas dragao criatura anciao",
    "inventario mochila bolsa bolsas armazenamento dimensao dimensional",
    "ferramenta ferramentas utensilio utensilios instrumentos equipamento equipamentos",
    "voz dialogo fala expressao respondeu perguntou",
)
STOP={"a","o","as","os","de","da","do","das","dos","e","em","que","qual","quem","como","quando","foi","era","um","uma","no","na","por","para","com"}
def expand_groups(ts):
    groups=[set(g.split()) for g in SYNONYM_GROUPS]
    return {t:set().union(*(g for g in groups if t in g))-{t} for t in ts if any(t in g for g in groups)}

def contextual_retrieve(db, query, entity=None, topic=None, role=None, limit=20):
    terms=set(tokens(query))-STOP
    if not terms: terms=set(tokens(query))
    if not entity:
        named=[k for k,aliases in ALIASES.items() if k not in ("inventory","legiao","lucas") and any(set(tokens(a)).issubset(terms) for a in aliases)]
        if len(named)==1: entity=named[0]
    expanded=expand_groups(terms)
    terms_all=terms|set().union(*expanded.values())
    def fts(ts):
        return 'anchor : ('+' OR '.join('"'+t+'"' for t in sorted(ts))+')'
    with sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro",uri=True) as c:
        c.row_factory=sqlite3.Row
        if c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]!=SCHEMA:
            raise ValueError("Wrong projection schema")
        sql="SELECT e.*,bm25(search) AS score FROM search JOIN evidence e ON e.id=search.rowid WHERE search MATCH ?"
        filters=[]; params=[]
        if role:filters.append("e.role=?");params.append(role)
        if topic:filters.append("(' '||e.topics||' ') LIKE ?");params.append("% "+topic+" %")
        base=sql+(" AND "+" AND ".join(filters) if filters else "")
        candidates={}
        for ts,restricted in ((terms,True),(terms_all,True),(terms,False)):
            args=[fts(ts)]+params
            stmt=base
            if entity and restricted:
                stmt+=" AND (' '||e.near_entities||' ') LIKE ?";args.append("% "+entity+" %")
            stmt+=" ORDER BY score,e.source,e.line_start LIMIT 240"
            for row in c.execute(stmt,args):
                h=dict(row)
                if h["id"] not in candidates:
                    candidates[h["id"]]=h
        def rank(h):
            words=set(tokens(h["anchor"]))
            direct=len(terms&words)
            extra=sum(bool((expanded.get(t,set())&words)) for t in terms-words)
            close=bool(entity and entity in h["near_entities"].split())
            exact=bool(entity and entity in h["entities"].split())
            return (-(direct+0.35*extra+0.75*close+0.10*exact),h["score"],h["source"],h["line_start"])
        ordered=sorted(candidates.values(),key=rank)
    selected=[]
    for h in ordered:
        if any(h["source"]==x["source"] and h["section_start"]==x["section_start"] and min(h["line_end"],x["line_end"])-max(h["line_start"],x["line_start"])+1>=9 for x in selected):
            continue
        selected.append(h)
        if len(selected)==limit:break
    return {"query":query,"hits":selected,"status":"CANDIDATES_ONLY" if selected else "NOT_RECOVERED","canon_changed":False,"semantic_certification":False,"context_hints_only":True}

def retrieve(db, query, entity=None, topic=None, role=None, limit=20, strategy="hybrid"):
    if not query.strip() or not 1<=limit<=100:
        raise ValueError("Invalid query/limit")
    if entity is not None and entity not in ALIASES:
        raise ValueError("Unknown entity")
    if topic is not None and topic not in TOPICS:
        raise ValueError("Unknown topic")
    if role not in (None,"Prompt","Response","EXPORT_METADATA"):
        raise ValueError("Unknown role")
    if strategy not in ("legacy", "hybrid", "contextual"):
        raise ValueError("Unknown strategy")
    ts=list(dict.fromkeys(tokens(query)))
    if not 1<=len(ts)<=24:
        raise ValueError("Invalid token count")
    if strategy=="contextual":
        return contextual_retrieve(db,query,entity,topic,role,limit)
    # Restrict matching to literal text, never synthetic entity/topic labels.
    expr=" OR ".join('"'+t+'"' for t in ts)
    if strategy=="hybrid":
        expr="anchor : ("+expr+")"
    sql="SELECT e.*,bm25(search) AS score FROM search JOIN evidence e ON e.id=search.rowid WHERE search MATCH ?"
    args=[expr]
    for field,val in (("entities",entity),("topics",topic)):
        if val is not None:
            sql+=" AND (' '||e."+field+"||' ') LIKE ?"
            args.append("% "+val+" %")
    if role:
        sql+=" AND e.role=?";args.append(role)
    sql+=" ORDER BY score,e.source,e.line_start LIMIT ?";args.append(limit if strategy=="legacy" else max(100,limit*5))
    with sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro",uri=True) as c:
        c.row_factory=sqlite3.Row
        if c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]!=SCHEMA:
            raise ValueError("Wrong projection schema")
        hits=[dict(r) for r in c.execute(sql,args)]
    if strategy=="hybrid":
        # Re-rank by literal query token coverage, then BM25. Avoid duplicate windows
        # hiding distinct scenes. This is lexical retrieval, not an embedding model.
        stop={"a","o","as","os","de","da","do","das","dos","e","em","que","qual","quem","como","quando","foi","era","um","uma","no","na","por","para","com"}
        terms=set(ts)-stop or set(ts)
        hits.sort(key=lambda h:(-len(terms.intersection(tokens(h["anchor"]))),h["score"],h["source"],h["line_start"]))
        selected=[]
        for h in hits:
            if any(h["source"]==x["source"] and h["role"]==x["role"] and min(h["line_end"],x["line_end"])-max(h["line_start"],x["line_start"])+1>=9 for x in selected):
                continue
            selected.append(h)
            if len(selected)==limit: break
        hits=selected
    return {"query":query,"hits":hits,"status":"CANDIDATES_ONLY" if hits else "NOT_RECOVERED",
            "canon_changed":False,"semantic_certification":False}

def verify_manifest(root, db):
    manifest=json.loads((Path(root)/"history/sources/MANIFEST.json").read_text(encoding="utf-8"))
    expected=_sha(json.dumps(manifest,sort_keys=True,ensure_ascii=False))
    with sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro",uri=True) as c:
        meta=dict(c.execute("SELECT key,value FROM meta"))
        if meta.get("schema")!=SCHEMA or meta.get("manifest_sha")!=expected:
            raise ValueError("Stale or incompatible R31 projection")
    return True

def brief(root, db, query, entities=(), topics=()):
    # Existing R30 observations remain in the writer context.
    root=Path(root)
    verify_manifest(root,db)
    base=writer_brief(root,character_ids=tuple(entities))
    candidates=[]
    for ent in entities or (None,):
        for topic in topics or (None,):
            candidates.append(retrieve(db,query,ent,topic,role="Response",limit=12))
            candidates.append(retrieve(db,query,ent,topic,role="Prompt",limit=6))
    return {"r30":base,"r31_candidates":candidates,
            "instructions":["Read exact anchors and neighboring scenes; resolve ambiguity.",
              "Prompts are author directions, not proof an event occurred.",
              "Never infer ownership, present location, romance or physical attributes from proximity.",
              "Preserve conflicts, temporal states, unknowns and approved choices.",
              "Use relevant sensory and emotional details naturally; no mandatory quotas."],
            "canon_changed":False}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--archive-root",type=Path)
    p.add_argument("--db",type=Path,required=True)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("build")
    r=sub.add_parser("search");r.add_argument("query");r.add_argument("--entity");r.add_argument("--topic");r.add_argument("--role");r.add_argument("--strategy",choices=("legacy","hybrid","contextual"),default="hybrid")
    b=sub.add_parser("brief");b.add_argument("query");b.add_argument("--entity",action="append",default=[]);b.add_argument("--topic",action="append",default=[])
    a=p.parse_args(argv)
    if a.action=="build": result=build(a.archive_root,a.db)
    elif a.action=="search": result=retrieve(a.db,a.query,a.entity,a.topic,a.role,strategy=a.strategy)
    else: result=brief(a.archive_root,a.db,a.query,a.entity,a.topic)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
