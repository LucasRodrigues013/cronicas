"""R26 original Avarenn arcane library: query, rank, and validate without canon mutation.

This is source-supported infrastructure, NOT a combat simulator and NOT a license
to assert proposed spells, summons or places have appeared in the story.
"""
from __future__ import annotations

import json
import re
from hashlib import sha256
import unicodedata
from functools import lru_cache
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent / "r26"
GRIMOIRE = BASE / "grimoire.json"
GRIMOIRE_EXPANSION = BASE / "grimoire_regional_900.json"
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


@lru_cache(maxsize=1)
def load_regional_atlas() -> dict[str, Any]:
    expansion = _data(GRIMOIRE_EXPANSION)
    if expansion.get("schema") != "worldroot-r26-regional-atlas-expansion-v1":
        raise ValueError("Wrong R26.1 atlas expansion schema")
    if expansion.get("base_grimoire") != "worldroot/r26/grimoire.json":
        raise ValueError("Wrong parent grimoire reference")
    return expansion


@lru_cache(maxsize=1)
def load_grimoire() -> dict[str, Any]:
    """Combined read-only view: preserves original 120 entries unchanged."""
    book = _data(GRIMOIRE)
    if book.get("schema") != "worldroot-r26-arcane-grimoire-v1":
        raise ValueError("Wrong R26 grimoire schema")
    expansion = load_regional_atlas()
    # Normalize expanded entries to the original API; the source files remain distinct.
    new_spells = [
        {**spell,
         "manifestacao_sensorial": spell["assinatura_sensorial"],
         "exigencia_situacional": (
             spell["substrato_necessario"]
             + "; a condição depende do terreno, da presença e do conhecimento local"
         ),
         "contrajogo_ou_lacuna": (
             spell["contrajogo"]
             + "; essa falha pode ser observada e explorada sem garantir vitória"
         )}
        for spell in expansion["spells"]
    ]
    return {**book, "schools": [*book["schools"], *expansion["schools"]],
            "spells": [*book["spells"], *new_spells],
            "regional_expansion": {
                "schema": expansion["schema"],
                "additions": len(new_spells),
                "lineages": sum(len(x["familias"]) for x in expansion["schools"]),
                "new_school_count": len(expansion["schools"]),
                "newly_canonical_spells": 0,
            }}


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
    if not isinstance(schools, list) or len(schools) != 30:
        errors.append("MAG01: missing original schools")
        schools = []
    if not isinstance(spells, list) or len(spells) != 1020:
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
        expected_per_circle = 1 if school["id"] in {
            x["id"] for x in _data(GRIMOIRE)["schools"]} else 5
        if any(circles.count(i) != expected_per_circle for i in range(10)):
            errors.append("MAG05: invalid circle density for " + school["id"])
    atlas = load_regional_atlas()
    if len(atlas.get("schools", [])) != 18 or len(atlas.get("spells", [])) != 900:
        errors.append("MAG10: altered regional atlas count")
    if len({f["mecanismo"] for school in atlas["schools"] for f in school["familias"]}) != 90:
        errors.append("MAG11: regional lineages lack distinct effect mechanisms")
    if sum(x.get("origem", "").startswith("Três Arcos") for x in atlas["spells"]) != 200:
        errors.append("MAG12: missing independent City of Three Arches pathways")
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
        "regional_new_spells": len(atlas.get("spells", [])),
        "regional_lineages": book["regional_expansion"]["lineages"],
        "regional_unique_mechanisms": len({f["mecanismo"] for school in atlas["schools"] for f in school["familias"]}),
        "proposed_three_arcos_spells": sum(x.get("origem", "").startswith("Três Arcos") for x in atlas["spells"]),
        "culturally_grounded_spells": len(atlas["spells"]),
        "proven_ownership_from_regional_expansion": 0,
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


@lru_cache(maxsize=1)
def _spell_lookup_index() -> dict[str, dict]:
    by_id = {}
    for spell in load_grimoire()["spells"]:
        by_id[spell["id"]] = spell
        by_id[norm(spell["nome"])] = spell
    return by_id


def get_spell(identifier: str) -> dict | None:
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("Spell identifier must be nonempty")
    match = _spell_lookup_index().get(identifier) or _spell_lookup_index().get(norm(identifier))
    # Return isolated mapping to prevent one caller mutating the shared cache.
    return dict(match) if match is not None else None


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


# Mentions of a spell in a library, rumor, lesson, catalog or title should not
# falsely require a cast ledger. The default for unexplained mentions remains
# conservative and is an advisory, never proof of casting.
DOCUMENT_MARKERS = re.compile(
    r"(?i)\b(?:livro|volume|manual|capítulo|titulo|título|manuscrito|"
    r"página|pergaminho|estudo|teoria|catálogo|registro|inscrição|"
    r"biblioteca|caderno|verbete|hipótese|lenda|crônica|"\n    r"leu|leitura|estudou|pesquisou|ouviu falar|citou|comentou)\b"
)
CAST_MARKERS = re.compile(
    r"(?i)\b(?:conjurou|conjurava|pronunciou|lançou|invocou|"
    r"ativou|moldou|manifestou|evocou|ergueu|teceu|"
    r"sussurrou|fez surgir|fez nascer|materializou|"
    r"canalizou|desferiu|disparou)\b"
)


def classify_named_spell_references(prose: str) -> dict[str, list[str]]:
    """Heuristic: titles and discussions are not automatically cast events."""
    if not isinstance(prose, str):
        raise TypeError("Literal prose must be text")
    acts, mentions, unresolved = set(), set(), set()
    for spell in load_grimoire()["spells"]:
        pattern = re.compile(r"(?<!\w)" + re.escape(spell["nome"]) + r"(?!\w)", re.I)
        for match in pattern.finditer(prose):
            start = prose.rfind("\n", 0, match.start()) + 1
            end = prose.find("\n", match.end())
            line = prose[start:len(prose) if end < 0 else end]
            before = line[:match.start() - start]
            # A book's title remains a mention even if a character opened it.
            doc = DOCUMENT_MARKERS.search(line) is not None
            action = CAST_MARKERS.search(before[-90:]) is not None
            if doc and not action:
                mentions.add(spell["id"])
            elif action or line.strip().startswith("**") or not doc:
                acts.add(spell["id"])
                if not action and not doc:
                    unresolved.add(spell["id"])
            else:
                mentions.add(spell["id"])
    return {
        "active_or_unresolved": sorted(acts),
        "noncasting_mentions": sorted(mentions - acts),
        "requires_human_semantics": sorted(unresolved),
    }


def verify_prior_spell_source(
    archive_root: Path | None, source_path: str | None, literal_anchor: str | None,
) -> dict:
    """Read-back only; never infer proof from a plausible filename.

    Reject traversal, missing archive roots, symlinks, no archive bytes or
    unquoted claims. Not responsible for approving whether the earlier feat
    was a genuine cast; it proves the exact text was already archived.
    """
    failure = {"verified": False, "error": "R26_PROVENANCE: no verified previous literal source"}
    if not isinstance(archive_root, Path) or not archive_root.is_dir():
        return failure
    if not isinstance(source_path, str) or not source_path.strip():
        return failure
    if not isinstance(literal_anchor, str) or len(literal_anchor.strip()) < 14:
        return failure
    normalized = source_path.replace("\\", "/")
    p = PurePosixPath(normalized)
    if p.is_absolute() or ".." in p.parts or "." in p.parts:
        return failure
    # An aggregated chapter could contain an unapproved later Part.
    # Prior-source proof must name the one ratified episode, not chapter totals.
    if len(p.parts) != 4 or p.parts[0] != "episodes" or (
        p.parts[2] != "draft" or p.parts[3] != "narrativa_integral.md"
    ):
        return failure
    target = archive_root / normalized
    canon_record = archive_root / "canon" / "episodes" / (p.parts[1] + ".json")
    if not canon_record.is_file() or canon_record.is_symlink():
        return {**failure, "error": "R26_PROVENANCE: archived draft is not a ratified episode"}
    try:
        approved = json.loads(canon_record.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return failure
    if approved.get("episode_id") != p.parts[1] or approved.get("status") != "FECHADO_GITHUB":
        return failure
    if not target.resolve().is_relative_to(archive_root.resolve()) or target.is_symlink():
        return failure
    if not target.is_file() or target.stat().st_size > 5_000_000:
        return failure
    try:
        original = target.read_bytes()
        truth = (literal_anchor in original.decode("utf-8")
                 and approved.get("story_sha256") == sha256(original).hexdigest())
    except (OSError, UnicodeError):
        return failure
    return {"verified": truth,
            "error": None if truth else "R26_PROVENANCE: anchor absent in prior source"}


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


def main(argv: list[str] | None = None) -> int:
    """Query 1,020 spells directly without opening huge JSON in an editor."""
    import argparse
    parser = argparse.ArgumentParser(description="WORLDROOT R26.1 1020 spell atlas")
    parser.add_argument("--list", action="store_true", help="search the indexed spells")
    parser.add_argument("--school", default=None, help="school identifier")
    parser.add_argument("--circle", type=int, default=None, help="circle 0 to 9")
    parser.add_argument("--search", default="", help="spell name, effect or counterplay")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--format", choices=("json", "table"), default="table")
    args = parser.parse_args(argv)
    if not args.list:
        print(json.dumps(print_stats(), ensure_ascii=False, indent=2))
        return 0
    spells = search_spells(args.search, school=args.school,
                           circle=args.circle, limit=args.limit)
    if args.format == "json":
        print(json.dumps(spells, ensure_ascii=False, indent=2))
    else:
        print("ID | Círculo | Nome | Escola | Linhagem")
        for spell in spells:
            print(" | ".join((spell["id"], str(spell["circulo"]),
                              spell["nome"], spell["escola"],
                              spell.get("linhagem", "R26 ORIGINAL"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
