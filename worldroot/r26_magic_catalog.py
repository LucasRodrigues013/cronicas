"""R26 original Avarenn arcane library: query, rank, and validate without canon mutation.

This is source-supported infrastructure, NOT a combat simulator and NOT a license
to assert proposed spells, summons or places have appeared in the story.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent / "r26"
GRIMOIRE = BASE / "grimoire.json"
WORLDS = BASE / "world_codex.json"
CHARACTERS = BASE / "character_memory.json"
FEATS = BASE / "source_feats.json"
SPELL_STATUS = "R26_PROPOSTO_NAO_CANONICO"
CANON_HEAD_SNAPSHOT = "LVI-C05-PIV-D562-AUTHOR-SOURCE"


def _data(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("R26 catalog missing: " + path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(x for x in decomposed if not unicodedata.combining(x)).casefold()


def load_grimoire() -> dict[str, Any]:
    book = _data(GRIMOIRE)
    if book.get("schema") != "worldroot-r26-arcane-grimoire-v1":
        raise ValueError("Wrong R26 grimoire schema")
    return book


def load_world() -> dict[str, Any]:
    world = _data(WORLDS)
    if world.get("schema") != "worldroot-r26-summoning-world-v1":
        raise ValueError("Wrong R26 world codex")
    return world


def load_people() -> dict[str, Any]:
    memory = _data(CHARACTERS)
    if memory.get("schema") != "worldroot-r26-character-profiles-v1":
        raise ValueError("Wrong R26 memory schema")
    return memory


def load_feats() -> dict[str, Any]:
    feats = _data(FEATS)
    if feats.get("schema") != "worldroot-r26-canonical-feats-index-v1":
        raise ValueError("Wrong R26 historical evidence schema")
    return feats


def validate_codex() -> dict[str, Any]:
    errors = []
    book, world, people, feats = (
        load_grimoire(), load_world(), load_people(), load_feats())
    schools = book.get("schools", [])
    spells = book.get("spells", [])
    if not isinstance(schools, list) or len(schools) < 10:
        errors.append("MAG01: missing original schools")
        schools = []
    if not isinstance(spells, list) or len(spells) < 100:
        errors.append("MAG02: insufficient named spell coverage")
        spells = []
    school_ids = {x.get("id") for x in schools}
    if len(school_ids) != len(schools):
        errors.append("MAG03: duplicate school IDs")
    all_names = [norm(x.get("nome", "")) for x in spells]
    all_ids = [x.get("id") for x in spells]
    if len(all_names) != len(set(all_names)) or len(all_ids) != len(set(all_ids)):
        errors.append("MAG04: duplicate spell name or ID")
    for school in schools:
        circles = [s.get("circulo") for s in spells if s.get("escola") == school["id"]]
        if sorted(circles) != list(range(10)):
            errors.append("MAG05: each school must offer circles 0..IX: " + school["id"])
    for entry in spells:
        if entry.get("escola") not in school_ids or entry.get("status") != SPELL_STATUS:
            errors.append("MAG06: spell improperly presented as canon: " + str(entry.get("id")))
        for field in ("nome", "efeito_proposto", "manifestacao_sensorial",
                      "exigencia_situacional", "contrajogo_ou_lacuna"):
            if not isinstance(entry.get(field), str) or len(entry[field].strip()) < 12:
                errors.append("MAG07: incomplete spell " + str(entry.get("id")) + " " + field)
        if type(entry.get("circulo")) is not int or not 0 <= entry["circulo"] <= 9:
            errors.append("MAG08: impossible magic circle")
    if not any(x.get("id") == "CREATION_GENESE" and
               x.get("classification") == "FORA_DA_ESCALA_0_IX"
               for x in book.get("special_authorities", [])):
        errors.append("MAG09: GÊNESE must remain outside ordinary spell ranks")
    for group in ("invocations", "wonders", "creatures"):
        entries = world.get(group)
        if not isinstance(entries, list) or len(entries) < 10:
            errors.append("WORLD01: missing " + group)
        elif any(e.get("status") != SPELL_STATUS for e in entries):
            errors.append("WORLD02: proposed " + group + " declared canonical")
        elif len({e.get("id") for e in entries}) != len(entries):
            errors.append("WORLD03: repeated IDs " + group)
    profiles = people.get("profiles")
    if not isinstance(profiles, list) or len(profiles) < 20:
        errors.append("CHAR01: missing character dossiers")
    elif len({x.get("name") for x in profiles}) != len(profiles):
        errors.append("CHAR02: duplicate character identity")
    if not isinstance(feats.get("entries"), list) or len(feats["entries"]) < 10:
        errors.append("FEAT01: missing historical provenance")
    elif any(
        not entry.get("source", {}).get("literal_anchor")
        or entry.get("status") != (
            "DESCRITO_EM_RASCUNHO_NAO_CANONICO"
            if entry.get("published_context") == "RASCUNHO_NAO_CANONICO"
            else "DEMONSTRADO_DESCRITIVO_SEM_NOME_NOVO_DE_FEITIÇO"
        )
        for entry in feats["entries"]
    ):
        errors.append("FEAT02: unqualified historical feat or draft misclassified")
    return {
        "status": "OK" if not errors else "BLOQUEADO",
        "errors": errors,
        "schools": len(schools),
        "named_spells": len(spells),
        "summons": len(world.get("invocations", [])),
        "creatures": len(world.get("creatures", [])),
        "wonders": len(world.get("wonders", [])),
        "tracked_characters": len(profiles or []),
        "historical_feats": sum(x.get("status") == "DEMONSTRADO_DESCRITIVO_SEM_NOME_NOVO_DE_FEITIÇO"
                                for x in feats.get("entries", [])),
        "draft_only_feats": sum(x.get("status") == "DESCRITO_EM_RASCUNHO_NAO_CANONICO"
                                for x in feats.get("entries", [])),
        "genese_outside_rank": True,
        "canon_changed": False,
        "literary_quality_certified": False,
    }


def get_spell(identifier: str) -> dict | None:
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("Spell identifier must be nonempty")
    for spell in load_grimoire()["spells"]:
        if identifier == spell["id"] or norm(identifier) == norm(spell["nome"]):
            return spell
    return None


def search_spells(query: str = "", *, school: str | None = None,
                  circle: int | None = None, limit: int = 30) -> list[dict]:
    if circle is not None and (type(circle) is not int or not 0 <= circle <= 9):
        raise ValueError("Circle must be an integer 0..9")
    if type(limit) is not int or not 1 <= limit <= 150:
        raise ValueError("Limit must be an integer 1..150")
    needle = norm(query.strip())
    result = []
    for spell in load_grimoire()["spells"]:
        if school and spell["escola"] != school:
            continue
        if circle is not None and spell["circulo"] != circle:
            continue
        searchable = norm(" ".join((spell["nome"], spell["escola"],
                                    spell["efeito_proposto"], spell["contrajogo_ou_lacuna"])))
        if needle and needle not in searchable:
            continue
        result.append(spell)
        if len(result) >= limit:
            break
    return result


def spell_ids_used_in_prose(prose: str) -> list[str]:
    """Identifies literal new names. Do not infer abilities merely from theme."""
    if not isinstance(prose, str):
        raise TypeError("Literal prose must be text")
    ids = []
    for spell in load_grimoire()["spells"]:
        if re.search(r"(?<!\w)" + re.escape(spell["nome"]) + r"(?!\w)", prose, re.I):
            ids.append(spell["id"])
    return ids


def summon_ids_used_in_prose(prose: str) -> list[str]:
    if not isinstance(prose, str):
        raise TypeError("Literal prose must be text")
    ids = []
    for summon in load_world()["invocations"]:
        if re.search(r"(?<!\w)" + re.escape(summon["nome"]) + r"(?!\w)", prose, re.I):
            ids.append(summon["id"])
    return ids


def verify_historical_anchors(archive_root: Path) -> dict:
    """Optional read-only proof if branch story-archive is locally checked out."""
    confirmed, pending = [], []
    for feat in load_feats()["entries"]:
        source = feat["source"]
        path = archive_root / source["path"]
        if path.is_file():
            if source["literal_anchor"] in path.read_text(encoding="utf-8"):
                confirmed.append(feat["id"])
            else:
                raise ValueError("Historical source anchor mismatch: " + feat["id"])
        else:
            pending.append(feat["id"])
    return {
        "verified": confirmed, "not_mounted": pending,
        "not_mounted_is_not_a_failure_or_a_confirmation": True,
        "canon_changed": False,
    }


def print_stats() -> dict:
    return validate_codex()


if __name__ == "__main__":
    print(json.dumps(print_stats(), ensure_ascii=False, indent=2))
