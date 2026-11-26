"""R35 author-authorized provisional continuity overlay.
Editorial data is never an episode closure or semantic proof. Production
activation requires a separately validated private archive and manifest.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

MANIFEST = "editorial/registries/r35-living-overlay-manifest.json"
PROJECT = "CRONICAS_DE_UM_NOVO_MUNDO"
STATUSES = frozenset(("CANONICO", "RECUPERADO", "DEDUZIDO", "COMPLETADO", "SEGREDO", "NAO_APLICAVEL", "PENDENTE_FONTE"))
CHAR_FIELDS = frozenset(("identity","species","lineage","origin","age_chronological","age_biological","age_apparent","age_experiential","height_cm","mass_kg","body","face","hair","eyes","skin","voice","gestures","wardrobe","occupation","roles","languages","attributes","skills","proficiencies","combat_style","magic_repertoire","equipment","inventory","condition","relationships","goals","values","contradictions","fears","preferences","knowledge","location","journey","history","visual_refs"))
PRIVATE_FIELDS = frozenset(("knowledge",))
PRIVATE_SCOPES = frozenset(("AUTHOR_ONLY","BACKSTAGE","PRIVATE_CHARACTER","PRIVATE_BOUNDARY"))
SYNC_SCHEMA = "worldroot-scene-codex-sync-v1"

def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def _read(root, name):
    root = Path(root).resolve()
    if not isinstance(name, str) or not name.startswith("editorial/registries/"):
        raise ValueError("Invalid overlay path")
    path = root / name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("Unsafe or absent overlay file")
    raw = path.read_bytes()
    return json.loads(raw), raw

def _source_present(entry):
    return bool(entry.get("origin")) and isinstance(entry.get("justification"),str) and bool(entry["justification"].strip())

def validate_fields(fields, required=()):
    if not isinstance(fields, dict) or not set(required) <= set(fields):
        raise ValueError("Incomplete profile fields")
    for key, entry in fields.items():
        if not isinstance(key,str) or not key or not isinstance(entry,dict) or entry.get("status") not in STATUSES or entry.get("value") is None or entry.get("value") == "" or not _source_present(entry):
            raise ValueError("Untraceable profile field: " + str(key))
        if entry["status"] == "SEGREDO" and entry.get("scope") != "AUTHOR_ONLY":
            raise ValueError("Secret must be author-only")
        if entry["status"] == "DEDUZIDO":
            proof = entry.get("origin")
            if not isinstance(proof,list) or len({json.dumps(x,sort_keys=True,ensure_ascii=False) for x in proof}) < 2:
                raise ValueError("Deduction requires independent evidence references")
    return fields

def public_fields(fields, vetoes=()):
    # Never return previous/replaced private values or raw traces in general retrieval.
    return {k:{x:v for x,v in entry.items() if x in ("value","status","justification","scope","valid_at","checkpoint")}
            for k,entry in fields.items() if k not in PRIVATE_FIELDS and k not in vetoes
            and entry.get("status")!="SEGREDO" and entry.get("scope") not in PRIVATE_SCOPES}

def editorial_profile(card, vetoes=()):
    return {"fields":public_fields(card["fields"],vetoes),
            "scope":"PROVISIONAL_CONTINUITY_NOT_NARRATED_FACT",
            "checkpoint":card.get("trace",{}).get("checkpoint")}

def load_overlay(root, base_raw, base):
    manifest_path=Path(root)/MANIFEST
    if not manifest_path.exists():
        return None
    m,raw=_read(root,MANIFEST)
    if m.get("schema")!="worldroot-r35-living-overlay-manifest-v1" or m.get("project")!=PROJECT or m.get("base_registry_blob")!=git_blob(base_raw):
        raise ValueError("Overlay manifest authority mismatch")
    if not m.get("rules",{}).get("no_automatic_canon_promotion"):
        raise ValueError("Overlay cannot promote canon")
    cp=m["checkpoint"]
    # A historical overlay remains usable after the HEAD advances only if its
    # original closure is still verified. The live event journal wins.
    from .git_cycle import load
    live=load(Path(root)/"canon/HEAD.json")
    if type(cp.get("sequence")) is not int or cp["sequence"]>live["sequence"]:
        raise ValueError("Overlay checkpoint is outside closed history")
    if cp["sequence"]==live["sequence"]:
        if cp["episode_id"]!=live["episode_id"] or cp["source_sha256"]!=live["source_sha256"]:
            raise ValueError("Overlay HEAD mismatch")
    else:
        receipt=load(Path(root)/"canon/episodes"/(cp["episode_id"]+".json"))
        if receipt["sequence"]!=cp["sequence"] or receipt["story_sha256"]!=cp["source_sha256"]:
            raise ValueError("Overlay historical checkpoint mismatch")
    docs=[]
    for key,schema in (("character_overlay","worldroot-r35-natural-completion-v1"),("world_overlay","worldroot-r35-world-overlay-v1")):
        spec=m[key];d,b=_read(root,spec["path"])
        if git_blob(b)!=spec["git_blob"] or d.get("schema")!=schema or d.get("project")!=PROJECT or d.get("registry_blob")!=m["base_registry_blob"]:
            raise ValueError("Overlay content identity mismatch")
        if d["checkpoint"]["episode_id"]!=cp["episode_id"] or d["checkpoint"]["source_sha256"]!=cp["source_sha256"]:
            raise ValueError("Overlay document checkpoint mismatch")
        docs.append(d)
    c,w=docs
    profiles={}
    for r in c["characters"]+w["records"]:
        ident=r["id"]
        if ident in profiles or not isinstance(ident,str) or not ident:
            raise ValueError("Duplicate overlay identity")
        validate_fields(r["fields"],CHAR_FIELDS if r in c["characters"] else ())
        profiles[ident]=r
    base_ids={r["id"] for r in base["records"]}
    all_ids=base_ids|set(profiles)
    if not base_ids<=set(profiles):
        raise ValueError("Overlay omitted existing base identity")
    for r in w.get("links",[]):
        if r["from"] not in all_ids or r["to"] not in all_ids:
            raise ValueError("Orphan cross-domain link")
    aliases={}
    for decision in c.get("alias_decisions",[]):
        if decision.get("decision")!="SEPARAR" or not set(decision["ids"])<=all_ids:
            raise ValueError("Invalid reviewed alias group")
        for ident in decision["ids"]:
            aliases.setdefault(ident,[]).append(decision["alias"])
    vetoes={}
    for v in m.get("vetoes",[]):
        ident,field=v["id"],v["field"]
        if ident not in profiles or field not in profiles[ident]["fields"] or profiles[ident]["fields"][field]["status"] not in ("COMPLETADO","SEGREDO") or not str(v.get("reason","")).strip():
            raise ValueError("Veto is limited to provisional or secret editorial values")
        vetoes.setdefault(ident,set()).add(field)
    naming_review={}
    if "naming_review" in m:
        from .naming import validate_roster
        spec=m["naming_review"];doc,blob=_read(root,spec["path"])
        if git_blob(blob)!=spec["git_blob"] or doc.get("source_overlay_blob")!=m["character_overlay"]["git_blob"]:
            raise ValueError("Naming roster content identity mismatch")
        naming_review=validate_roster(doc,c["characters"],cp)
    return {"naming_review":naming_review,"manifest_sha256":hashlib.sha256(raw).hexdigest(),
            "profiles":profiles,"aliases":aliases,"vetoes":vetoes,
            "links":w.get("links",[]),"base_ids":base_ids,
            "checkpoint":cp,"character_count":len(c["characters"]),
            "world_count":len(w["records"]),"require_sync":bool(m["rules"].get("require_scene_sync"))}

def augment_record(record, overlay):
    if not overlay:
        return record
    ident=record["id"];card=overlay["profiles"].get(ident)
    if not card:
        return record
    aliases=list(dict.fromkeys([*record.get("aliases",[]),*overlay["aliases"].get(ident,[])]))
    links=[{k:v for k,v in l.items() if k in ("from","to","relation","status","checkpoint")}
           for l in overlay["links"] if ident in (l["from"],l["to"]) and l.get("status")!="SEGREDO" and l.get("scope") not in PRIVATE_SCOPES]
    return {**record,"aliases":aliases,"natural_profile":editorial_profile(card,overlay["vetoes"].get(ident,())),
            "cross_domain_links":links}

def extra_records(overlay):
    if not overlay:
        return
    for ident,card in overlay["profiles"].items():
        if ident in overlay["base_ids"]:
            continue
        yield augment_record({"id":ident,"name":card["name"],"aliases":card.get("aliases",[]),
            "domains":card.get("domains",["Personagens"]),"scope":"RECOVERED_IDENTITY_EDITORIAL_NOT_CANON_JOURNAL"},overlay)

def validate_new_character(card,prose):
    from .live_codex import check_anchor
    profile=card.get("profile")
    if not isinstance(profile,dict):
        raise ValueError("New named character requires complete Codex profile")
    fields=validate_fields(profile.get("fields"),CHAR_FIELDS)
    for name,entry in fields.items():
        if entry["status"]=="CANONICO":
            proof=entry["origin"]
            if not isinstance(proof,dict):
                raise ValueError("New character canon claim requires a literal anchor")
            check_anchor(prose,proof.get("line"),proof.get("anchor"))
        if entry["status"]=="COMPLETADO" and name in ("condition","inventory","location","knowledge","magic_repertoire","relationships","journey","history"):
            raise ValueError("Current state or historical event requires evidence, not completion")
    return fields

def validate_scene_sync(sync,delta,prose,known_ids):
    """Structural coverage and cross-reference gate. Semantic extraction is separate."""
    from .live_codex import check_anchor
    if not isinstance(sync,dict) or sync.get("schema")!=SYNC_SCHEMA:
        raise ValueError("Scene Codex Sync required")
    scenes=sync.get("scenes")
    if not isinstance(scenes,list) or not scenes:
        raise ValueError("Missing scene coverage")
    n=len(prose.splitlines());next_line=1
    ids=set(known_ids)|{x["id"] for x in delta["new_entities"]}
    reviewed=set()
    for s in scenes:
        start,end=s.get("start_line"),s.get("end_line")
        if type(start) is not int or type(end) is not int or start!=next_line or not start<=end<=n:
            raise ValueError("Scene ranges must cover prose without gaps or overlap")
        next_line=end+1
        mentions=s.get("mentions");ordinals=s.get("event_ordinals");cross=s.get("cross_checks");hooks=s.get("hooks")
        if not isinstance(mentions,list) or not isinstance(ordinals,list) or not isinstance(cross,list) or not isinstance(hooks,list):
            raise ValueError("Explicit scene mentions, events, cross-checks and hooks required")
        for x in mentions:
            if x.get("disposition") not in ("IDENTIFIED","UNRESOLVED","MENTION_ONLY","NOT_ENTITY"):
                raise ValueError("Invalid entity disposition")
            if x.get("disposition")=="IDENTIFIED" and x.get("id") not in ids:
                raise ValueError("Unknown scene entity")
            if type(x.get("line")) is not int or not start<=x["line"]<=end:
                raise ValueError("Mention evidence outside scene")
            check_anchor(prose,x["line"],x.get("anchor"))
        for j in ordinals:
            if type(j) is not int or j in reviewed or not 0<=j<len(delta["events"]) or not start<=delta["events"][j]["line"]<=end:
                raise ValueError("Scene event missing, repeated or outside range")
            reviewed.add(j)
        for x in cross:
            if x.get("status") not in ("OK","ALERT","NOT_APPLICABLE") or not str(x.get("reason","")).strip():
                raise ValueError("Cross-domain check requires status and reasoning")
            if x.get("status")=="ALERT" and x.get("blocking") is True:
                raise ValueError("Blocking cross-domain coherence alert")
        for x in hooks:
            if x.get("id") not in ids or x.get("status") not in ("OPEN","ADVANCED","RESOLVED","PROTECTED","UNCHANGED"):
                raise ValueError("Invalid narrative hook update")
    if next_line!=n+1 or reviewed!=set(range(len(delta["events"]))):
        raise ValueError("Incomplete scene/event coverage")
    for card in delta["new_entities"]:
        if "Personagens" in card["domains"]:
            validate_new_character(card,prose)
    return {"scenes":len(scenes),"events":len(reviewed),"structural_certification":True,"semantic_certification":False}
