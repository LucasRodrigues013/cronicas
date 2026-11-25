"""R31: evidence-first deep transcript recovery; never writes canon.

Uses R30 and its verified six-source manifest. Candidate search is not semantic
certification. Author prompts and assistant responses remain distinct.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from .history_index import read_verified_sources
from .literary_experience import writer_brief

SCHEMA = "worldroot-r31-deep-recovery-v1"
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
}
ALIASES = {
    "miren": ("Miren",), "lucas": ("Lucas Rodrigues", "Lucas", "Criador"),
    "lira": ("Lira Selen Vareth", "Lira"), "ciran": ("Círan", "Ciran"),
    "seris": ("Serís Daum", "Seris Daum", "Serís"),
    "althea": ("Althea",), "varo": ("Varo",), "kael": ("Kael",),
    "kairon": ("Káiron", "Kairon"), "aerun": ("AERÚN", "AERUN"),
    "calderva": ("Calderva",), "genese": ("GÊNESE", "CREATION"),
    "inventory": ("mochila dimensional", "Matriz-Mãe", "inventário"),
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
    for role, start, lines in sections(body):
        for i in range(0, len(lines), stride):
            group = lines[i:i+width]
            yield role, start+i, start+i+len(group)-1, "".join(group)

def build(root, db):
    manifest, sources = read_verified_sources(Path(root))
    db = Path(db)
    # Derived database only, outside the archive to avoid accidental canon writes.
    if db.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("R31 projection must be outside archive")
    if db.exists():
        raise FileExistsError("Use a fresh projection path")
    try:
        with sqlite3.connect(db) as c:
            c.executescript("""
            CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE evidence(id INTEGER PRIMARY KEY, source TEXT, source_sha TEXT,
              role TEXT, line_start INTEGER, line_end INTEGER, anchor TEXT, anchor_sha TEXT,
              topics TEXT, entities TEXT);
            CREATE VIRTUAL TABLE search USING fts5(anchor, entities, topics,
              content='evidence',content_rowid='id',tokenize='unicode61 remove_diacritics 2');
            """)
            stats=[]
            for meta, body in sources:
                count=0
                for role, lo, hi, anchor in windows(body):
                    nt=norm(anchor)
                    entities=[key for key, aliases in ALIASES.items()
                              if any(re.search(r"(?<!\w)"+re.escape(norm(a))+r"(?!\w)", nt)
                                     for a in aliases)]
                    topics=[k for k,p in TOPICS.items() if re.search(p,anchor,re.I)]
                    c.execute("INSERT INTO evidence(source,source_sha,role,line_start,line_end,anchor,anchor_sha,topics,entities) VALUES(?,?,?,?,?,?,?,?,?)",
                              (meta["source_name"],meta["sha256"],role,lo,hi,anchor,_sha(anchor)," ".join(topics)," ".join(entities)))
                    count+=1
                stats.append({"source":meta["source_name"],"lines":len(body.splitlines()),"windows":count})
            c.execute("INSERT INTO search(search) VALUES('rebuild')")
            c.execute("INSERT INTO meta VALUES('schema',?)",(SCHEMA,))
            c.execute("INSERT INTO meta VALUES('manifest_sha',?)",(_sha(json.dumps(manifest,sort_keys=True,ensure_ascii=False)),))
            c.execute("INSERT INTO meta VALUES('coverage',?)",(json.dumps(stats),))
            if c.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                raise ValueError("Projection integrity failure")
        return {"schema":SCHEMA,"coverage":stats,"canon_changed":False,"semantic_certification":False}
    except BaseException:
        db.unlink(missing_ok=True)
        raise

def retrieve(db, query, entity=None, topic=None, role=None, limit=20):
    if not query.strip() or not 1<=limit<=100:
        raise ValueError("Invalid query/limit")
    if entity is not None and entity not in ALIASES:
        raise ValueError("Unknown entity")
    if topic is not None and topic not in TOPICS:
        raise ValueError("Unknown topic")
    if role not in (None,"Prompt","Response","EXPORT_METADATA"):
        raise ValueError("Unknown role")
    ts=tokens(query)
    if not 1<=len(ts)<=24:
        raise ValueError("Invalid token count")
    expr=" OR ".join('"'+t+'"' for t in ts)
    sql="SELECT e.*,bm25(search) AS score FROM search JOIN evidence e ON e.id=search.rowid WHERE search MATCH ?"
    args=[expr]
    for field,val in (("entities",entity),("topics",topic)):
        if val is not None:
            sql+=" AND (' '||e."+field+"||' ') LIKE ?"
            args.append("% "+val+" %")
    if role:
        sql+=" AND e.role=?";args.append(role)
    sql+=" ORDER BY score,e.source,e.line_start LIMIT ?";args.append(limit)
    with sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro",uri=True) as c:
        c.row_factory=sqlite3.Row
        if c.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]!=SCHEMA:
            raise ValueError("Wrong projection schema")
        hits=[dict(r) for r in c.execute(sql,args)]
    return {"query":query,"hits":hits,"status":"CANDIDATES_ONLY" if hits else "NOT_RECOVERED",
            "canon_changed":False,"semantic_certification":False}

def brief(root, db, query, entities=(), topics=()):
    # Existing R30 observations remain in the writer context.
    base=writer_brief(Path(root),character_ids=tuple(entities))
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
    r=sub.add_parser("search");r.add_argument("query");r.add_argument("--entity");r.add_argument("--topic");r.add_argument("--role")
    b=sub.add_parser("brief");b.add_argument("query");b.add_argument("--entity",action="append",default=[]);b.add_argument("--topic",action="append",default=[])
    a=p.parse_args(argv)
    if a.action=="build": result=build(a.archive_root,a.db)
    elif a.action=="search": result=retrieve(a.db,a.query,a.entity,a.topic,a.role)
    else: result=brief(a.archive_root,a.db,a.query,a.entity,a.topic)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
