"""Culturally coherent prospective names; stable entity ID remains authority."""
from __future__ import annotations
import hashlib,json,unicodedata
from pathlib import Path

SCHEMA="worldroot-name-identity-v1"
EXCEPTIONS={"CONSTRUCT_DESIGNATION","SPIRIT_OR_TRUE_NAME","CULTURAL_MONONYM","CHOSEN_CREATION_NAME","PROTECTED_IDENTITY"}
KINDS={"FAMILY","CLAN","PATRONYMIC","MATRONYMIC","TOPONYMIC","CHOSEN","HOUSE","DESIGNATION"}
def norm(s):
    return " ".join("".join(c for c in unicodedata.normalize("NFKD",str(s)) if not unicodedata.combining(c)).casefold().split())
def catalog():
    return json.loads(Path(__file__).with_name("naming_catalog.json").read_text(encoding="utf-8"))
def propose(culture,stable_id,occupied=(),given=None):
    """Deterministic candidate pool, no canonical or kinship claims."""
    p=catalog()["profiles"].get(culture)
    if p is None or not isinstance(stable_id,str) or not stable_id.strip():raise ValueError("Known culture and stable ID required")
    used={norm(x) for x in occupied}
    combos=[(g,a) for g in ([given] if given else p["given"]) for a in p["additional"] if norm(g)!=norm(a)]
    if not combos:raise ValueError("No candidates")
    start=int(hashlib.sha256((culture+":"+stable_id).encode()).hexdigest(),16)%len(combos)
    for i in range(len(combos)):
        g,a=combos[(start+i)%len(combos)]
        if norm(g+" "+a) not in used:
            return {"schema":SCHEMA,"given_name":g,"additional_name":a,"additional_kind":"CHOSEN","full_name":g+" "+a,"culture_id":culture,"status":"PROSPECTIVE_DESIGN","kinship_inferred":False}
    raise ValueError("Name pool exhausted; develop new roots, never silently reuse")
def validate(card,existing_rows=(),region_ids=(),species_ids=()):
    p=card.get("profile",{}).get("name_identity")
    if not isinstance(p,dict) or p.get("schema")!=SCHEMA:raise ValueError("New named character requires cultural name identity")
    for k in ("given_name","full_name","culture_id","basis","species_id","birth_region_id","residence_region_id","citizenship_region_id"):
        if not isinstance(p.get(k),str) or not p[k].strip():raise ValueError("Missing name identity "+k)
    if p["culture_id"] not in catalog()["profiles"] and p["culture_id"]!="unknown":raise ValueError("Unknown naming culture")
    if norm(p["full_name"])!=norm(card.get("name","")):raise ValueError("Full name must match entity display name")
    for k in ("birth_region_id","residence_region_id","citizenship_region_id"):
        if p[k]!="unknown" and p[k] not in region_ids:raise ValueError("Unknown region reference "+k)
    if p["species_id"]!="unknown" and p["species_id"] not in species_ids:raise ValueError("Unknown species reference")
    if p.get("status") not in ("PROSPECTIVE_DESIGN","NARRATED_IDENTITY"):raise ValueError("Naming authority required")
    if p.get("exception"):
        if p["exception"] not in EXCEPTIONS or not str(p.get("exception_reason","")).strip() or p.get("additional_name") or norm(p["full_name"])!=norm(p["given_name"]):raise ValueError("Invalid mononym exception")
    else:
        a=p.get("additional_name")
        if not isinstance(a,str) or not a.strip() or p.get("additional_kind") not in KINDS or norm(a)==norm(p["given_name"]) or norm(p["full_name"])!=norm(p["given_name"]+" "+a):raise ValueError("Full personal name required")
        if p["culture_id"]=="unknown" and p.get("additional_kind")!="CHOSEN":raise ValueError("Unknown culture cannot imply inherited name")
        if p["additional_kind"] in ("FAMILY","CLAN","HOUSE","PATRONYMIC","MATRONYMIC") and not str(p.get("kinship_basis","")).strip():raise ValueError("Inherited name needs explicit design or evidence")
    for r in existing_rows:
        if r.get("id")==card.get("id") or "Personagens" not in r.get("domains",[]):continue
        if norm(p["full_name"])==norm(r.get("name","")) or norm(p["full_name"]) in {norm(a) for a in r.get("aliases",[])}:raise ValueError("Full name or alias collision; separate identity explicitly")
    return p
def policy_packet():
    return {"schema":SCHEMA,"culture_profiles":sorted(catalog()["profiles"]),"new_named_character_requires_full_identity":True,"preserve_legacy_names":True,"identity_is_not_name":True,"mononym_exceptions":sorted(EXCEPTIONS),"region_species_citizenship_separate":True}
