"""R28: source-bound living world projection and nonblocking literary advisories.
Never modifies canon, author choices, narrative text or character knowledge.
Seed annotations are editorial interpretations of cited literal evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path

from .history_index import search as search_history

SEED = "editorial/registries/r28-living-world.json"
SCENES = re.compile(r"(?m)^##\s+[IVXL]+\s+[—–-]\s+(.+)$")
STOP = re.compile(r"(?mi)^\s*(?:\*\*)?FIM D[AO] (?:PARTE|CAPÍTULO)|^##\s+(?:ESCOLHAS|AS CINCO PORTAS|CINCO ESCOLHAS)")
WORD = re.compile(r"[^\W_]+", re.UNICODE)
SPEAKER = re.compile(r"(?m)^\s*\*\*([^*\n]{1,45}?)\s*[—–-]\*\*")
STATES = ("PROPOSED", "PROTOTYPE", "CREATED", "TESTED", "OPERATIONAL", "EVOLVED", "DEFERRED")
TAGS = {
    "morning": r"\b(café da manhã|acordou|treino matinal|desjejum)\b",
    "deliberation": r"\b(reunião|conselho|sessão|autorizou|deliberou)\b",
    "creation": r"\b(gênese|materializou|criou|construiu)\b",
    "exploration": r"\b(expedição|explorou|travessia|ruínas|caverna|desconhecid[oa])\b",
    "magic": r"\b(conjuração|feitiço|encantamento|ritual|magia|arcano|arcana)\b",
    "creature": r"\b(criatura|dragão|guardiã|guardião|velários|fera)\b",
    "culture": r"\b(tradição|festival|cerimônia|costumes|clãs|canção)\b",
    "action": r"\b(atacou|combate|duelo|resgate|perseguição|golpe|feridos)\b",
    "relationship": r"\b(beijou|abraçou|amizade|esposa|irmã|família)\b",
    "night": r"\b(anoitecer|naquela noite|estrelas|22h\d\d|23h\d\d)\b",
}
MOTIFS = {
    "authorization": r"\b(autorização|autorizad[oa]s?|consentimento|competência legítima)\b",
    "autonomy": r"\b(autonomia|livre para|direito de escolher|não (?:era|seria) propriedade)\b",
    "bureaucracy": r"\b(não (?:estava|está|foi) aprovad[oa]|não comprovad[oa]|sem declarar|não havia sido)\b",
    "shouted_humor": r"(?m)^\*\*(?:BRANNIK|LUCAS)\s*[—–-]\*\*\s*[A-ZÀ-Ú !?,.]{12,}$",
}

def normalize(value: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                            if not unicodedata.combining(c)).split())

def read_obj(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/unsafe source: " + str(path))
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected object: " + str(path))
    return obj

def literal_body(text: str) -> str:
    match = SCENES.search(text)
    start = match.start() if match else 0
    stop = STOP.search(text, start)
    return text[start:stop.start() if stop else len(text)]

def scene_rows(text: str) -> list[dict]:
    body = literal_body(text)
    matches = list(SCENES.finditer(body))
    spans = [(m.group(1), body[m.end():matches[i+1].start() if i+1 < len(matches) else len(body)])
             for i,m in enumerate(matches)] or [("unsectioned",body)]
    rows = []
    for title, block in spans:
        prose = "\n".join(x for x in block.splitlines() if not x.lstrip().startswith(("<","{@","|")))
        words = len(WORD.findall(prose))
        tags = {k: len(re.findall(v, prose, re.I)) for k,v in TAGS.items()}
        rows.append({"title":title,"words_approx":words,
                     "speakers":sorted(set(normalize(s) for s in SPEAKER.findall(prose))),
                     "signals":{k:v for k,v in tags.items() if v},
                     "dominant_signal":max(tags,key=tags.get) if max(tags.values()) else "other"})
    return rows

def advisory(prose: str, previous: list[str] | None = None) -> dict:
    """No word quotas, grades, automatic scene facts or hard rejection."""
    body = literal_body(prose)
    rows = scene_rows(body)
    sizes = [r["words_approx"] for r in rows]
    median = statistics.median(sizes)
    earlier = [sum(r["words_approx"] for r in scene_rows(p)) for p in (previous or []) if p.strip()]
    total = sum(sizes)
    ratio = round(total / statistics.median(earlier), 3) if earlier and statistics.median(earlier) else None
    pattern = [r["dominant_signal"] for r in rows]
    previous_patterns = [[r["dominant_signal"] for r in scene_rows(p)] for p in (previous or []) if p.strip()]
    motifs = {k:len(re.findall(v,body,0 if k=="shouted_humor" else re.I)) for k,v in MOTIFS.items()}
    notices = []
    if ratio is not None and ratio < .6 and len(rows) >= 5:
        notices.append("DEPTH: substantial compression relative to supplied prior parts; read important scenes in full.")
    if len(rows) >= 7 and sum(n < median * .7 for n in sizes) >= 3:
        notices.append("DEPTH: multiple short scenes; inspect desire, resistance, action and payoff.")
    if any(pattern == p for p in previous_patterns) or (len(rows)>=5 and len(set(pattern))<=2):
        notices.append("VARIETY: similar structural pattern; vary focus without forcing randomness.")
    if motifs["authorization"] + motifs["autonomy"] + motifs["bureaucracy"] >= max(6,len(rows)):
        notices.append("MOTIF: check repeated governance explanations; dramatize decisions instead.")
    if motifs["shouted_humor"] >= 4:
        notices.append("HUMOR: inspect repeated shouted punchlines; preserve spontaneous character voices.")
    if not any(r["signals"].get(t) for r in rows for t in ("magic","creature","culture","exploration")):
        notices.append("FANTASY: no lexical signal in this part; check lived wonder across the arc, not a quota.")
    return {"status":"ADVISORY_ONLY","canon_changed":False,"depth":{
        "words_approx":total,"scene_count":len(rows),"median_scene_words_approx":median,
        "relative_to_prior_median":ratio},"scene_variety":pattern,"motifs":motifs,
        "fantasy_signals":{t:sum(r["signals"].get(t,0) for r in rows)
                           for t in ("magic","creature","culture","exploration")},
        "scenes":rows,"notices":notices,
        "limitation":"Lexical signals, not proof of action, artistic merit or required content."}

def load_canonical(root: Path, head: dict) -> tuple[list[dict], list[str]]:
    """Read only closed episodes up to the supplied verified HEAD; verify literal bytes."""
    entries, warnings = [], []
    for p in sorted((root/"canon/episodes").glob("*.json")):
        try:
            c = read_obj(p)
            seq = c.get("sequence")
            if type(seq) is not int or seq > head["sequence"]:
                continue
            ident = c["episode_id"]
            if p.stem != ident or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}",ident):
                raise ValueError("episode identity mismatch")
            if c.get("schema") != "worldroot-github-closure-v1":
                raise ValueError("closure schema mismatch")
            f = root/"episodes"/ident/"draft/narrativa_integral.md"
            if f.is_symlink():
                raise ValueError("symlink")
            raw = f.read_bytes()
            if hashlib.sha256(raw).hexdigest() != c.get("story_sha256"):
                raise ValueError("literal SHA mismatch")
            entries.append({"id":ident,"sequence":seq,"day":c["metadata"]["day"],
                            "text":raw.decode("utf-8"),"sha256":c["story_sha256"],
                            "events":c.get("events",[]),"knowledge":c.get("knowledge",[])})
        except (OSError,ValueError,KeyError,TypeError) as exc:
            warnings.append(p.name+": "+str(exc))
    entries.sort(key=lambda e:e["sequence"])
    expected=list(range(1,head["sequence"]+1))
    if [e["sequence"] for e in entries] != expected:
        warnings.append("Incomplete or duplicate closure sequences; projection not complete.")
    if not entries or entries[-1]["id"]!=head["episode_id"] or entries[-1]["sha256"]!=head.get("source_sha256"):
        warnings.append("Projection does not reach the supplied HEAD.")
    return entries,warnings

def match_reference(text: str, aliases: list[str]) -> bool:
    body=normalize(literal_body(text))
    return any(re.search(r"(?<!\w)"+re.escape(normalize(a))+r"(?!\w)",body) for a in aliases if a.strip())

def resolve_entities(seed: dict) -> dict:
    """Only explicit aliases; accent-fold collisions remain ambiguous."""
    index = {}
    for row in seed.get("entities",[]):
        for alias in [row["name"],*row.get("aliases",[])]:
            index.setdefault(normalize(alias),set()).add(row["id"])
    return {"aliases":{k:next(iter(v)) for k,v in sorted(index.items()) if len(v)==1},
            "ambiguous":{k:sorted(v) for k,v in sorted(index.items()) if len(v)>1}}

def bound_record(row: dict, entries: dict, head: dict) -> dict:
    source=row["source"]
    episode=entries.get(source["episode"])
    anchor=source["anchor"]
    valid=bool(episode and anchor and anchor in episode["text"])
    result=dict(row)
    result["evidence_status"]="SOURCE_MATCH" if valid else "UNVERIFIED"
    if valid:
        result["source"]={**source,"sha256":episode["sha256"],"day":episode["day"],
                          "line":episode["text"].split(anchor,1)[0].count("\n")+1}
    result["editorial_annotation_not_canon"]=True
    return result

def project(root: Path, head: dict | None = None) -> dict:
    """Rebuild projection without touching source. Missing evidence stays visible."""
    root=root.resolve()
    live=read_obj(root/"canon/HEAD.json")
    if head is not None and head!=live:
        raise ValueError("Stale HEAD; reread canonical source")
    head=live
    if head.get("schema")!="worldroot-git-canon-v1" or type(head.get("sequence")) is not int:
        raise ValueError("Invalid HEAD")
    seed=read_obj(root/SEED)
    entries,warnings=load_canonical(root,head)
    byid={e["id"]:e for e in entries}
    assets=[]
    for row in seed.get("assets",[]):
        item=bound_record(row,byid,head)
        if item["state"] not in STATES:
            raise ValueError("Unknown lifecycle state")
        refs=[e for e in entries if match_reference(e["text"],[row["name"],*row.get("aliases",[])])]
        item["last_literal_reference"]={"episode":refs[-1]["id"],"day":refs[-1]["day"]} if refs else None
        # Last use is deliberately distinct from a mention; never auto-promote.
        if "last_use" in row:
            item["last_use"]=bound_record({"source":row["last_use"]},byid,head)
        item["later_reference_needs_review"]=bool(refs and refs[-1]["sequence"]>byid.get(row["source"]["episode"],{}).get("sequence",0))
        assets.append(item)
    activity=[]
    for row in seed.get("entities",[]):
        if row.get("kind")!="character":
            continue
        refs=[e for e in entries if match_reference(e["text"],[row["name"],*row.get("aliases",[])])]
        appearances=[]
        for e in refs:
            if any(normalize(row["name"]) in scene["speakers"] or
                   any(normalize(a) in scene["speakers"] for a in row.get("aliases",[]))
                   for scene in scene_rows(e["text"])):
                appearances.append(e)
        last=appearances[-1] if appearances else None
        activity.append({"id":row["id"],"name":row["name"],"last_dialogue_evidence":
                         {"episode":last["id"],"day":last["day"]} if last else None,
                         "days_since_dialogue":head["day"]-last["day"] if last else None,
                         "last_reference":{"episode":refs[-1]["id"],"day":refs[-1]["day"]} if refs else None,
                         "requires_legacy_recovery":not bool(refs),
                         "limitation":"Dialogue/reference is not proof of physical presence or current location."})
    plots=[]
    for row in seed.get("plots",[]):
        item=bound_record(row,byid,head)
        refs=[e for e in entries if match_reference(e["text"],row.get("aliases",[]))]
        item["last_reference"]={"episode":refs[-1]["id"],"day":refs[-1]["day"]} if refs else None
        item["later_reference_needs_review"]=bool(refs and refs[-1]["sequence"]>byid.get(row["source"]["episode"],{}).get("sequence",0))
        plots.append(item)
    aliases=resolve_entities(seed)
    return {"schema":"worldroot-r28-living-projection-v1","status":"PARTIAL" if warnings else "SOURCE_PROJECTION",
            "head":head,"warnings":warnings,"coverage":{"closed_episodes":len(entries),"seed_assets":len(assets),
            "seed_characters":len(activity),"seed_plots":len(plots),"inventory_exhaustive":False},
            "assets":assets,"characters":activity,"plots":plots,"entity_resolution":aliases,
            "recent_literary_advisories":advisory(entries[-1]["text"],[e["text"] for e in entries[-6:-1]]) if entries else None,
            "canon_changed":False}

def legacy_retrieve(root: Path, query: str, limit: int=6) -> dict:
    """Use existing verified D001-D528 FTS, not a second history database."""
    return search_history(root,query,limit=limit,role="ASSISTANT_RESPONSE",match_mode="any")

def receipt(prose: str, root: Path, head: dict) -> dict:
    """Best-effort advisory in intake; never block an existing valid draft."""
    try:
        entries,warnings=load_canonical(root,head)
        result=advisory(prose,[e["text"] for e in entries[-5:]])
        result["source_warnings"]=warnings[:12]
        result["prior_parts"]=len(entries[-5:])
        return result
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return {"status":"UNAVAILABLE","reason":str(exc),"canon_changed":False}

def main(argv=None):
    p=argparse.ArgumentParser(description="WORLDROOT R28 read-only living-world intelligence")
    p.add_argument("--archive-root",type=Path,required=True)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("project")
    s=sub.add_parser("review");s.add_argument("--literal",type=Path,required=True)
    s=sub.add_parser("legacy");s.add_argument("--query",required=True);s.add_argument("--limit",type=int,default=6)
    a=p.parse_args(argv)
    if a.action=="project": result=project(a.archive_root)
    elif a.action=="legacy": result=legacy_retrieve(a.archive_root,a.query,a.limit)
    else: result=receipt(a.literal.read_text(encoding="utf-8"),a.archive_root,read_obj(a.archive_root/"canon/HEAD.json"))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
