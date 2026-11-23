"""R26 six fantasy directors: evidence-only editorial validation, no authored outcomes.

Coupled to R25, but no wizard/creature/ability becomes canon on validation.
No scene count, spell quota, forced battle, or power-based winner decision.
"""
from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from .r26_authority_guard import scan_creation_prose, validate_authority_bible
from .reader_experience import assess_experience, scene_blocks
from .r26_magic_catalog import (
    get_spell, load_world, load_people, classify_named_spell_references,
    verify_prior_spell_source, summon_ids_used_in_prose, validate_codex,
)

SCHEMA = "worldroot-r26-fantasy-review-v1"
MOTIF = re.compile(
    r"(?i)\b(?:não era uma prova|não precisava fingir|não tinha mana|"
    r"conforme as regras|não foi um nerf|não havia sido aprovado|"
    r"não declarou uma evolução inventada|precisava ser verificado pelo motor)\b"
)
ALIASES = {
    "NOX": "NÓX",
    "SISTEMA AZUL": "SISTEMA",
    "CAEDREN": "CAEDREN",
    "THAERON": "THAERON",
    "MIREN": "MIREN",
    "VARO": "VARO",
}


def _words(item: object, minimum: int) -> bool:
    return isinstance(item, str) and len(item.strip()) >= minimum


def _anchor(prose: str, source: object, errors: list[str], label: str,
            *, minimum: int = 12, body: str | None = None) -> bool:
    if not _words(source, minimum) or source not in (body if body is not None else prose):
        errors.append("R26_EVIDENCE: " + label + " must quote exact narrative text")
        return False
    return True


def _combat(prose: str, body: dict, errors: list[str]) -> dict:
    mode = body.get("mode")
    if mode == "SEM_COMBATE":
        return {"mode": mode, "confirmed_action_responses": 0,
                "winner_predetermined": False}
    if mode != "COMBATE":
        errors.append("R26_COMBAT: set SEM_COMBATE or COMBATE")
        return {"mode": mode, "confirmed_action_responses": 0}
    if body.get("winner_predetermined") is not False:
        errors.append("R26_COMBAT: no predetermined winning side")
    if not _words(body.get("stake"), 20) or not _words(body.get("terrain"), 16):
        errors.append("R26_COMBAT: why this fight matters and its real terrain required")
    beats = body.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append("R26_COMBAT: dramatize at least an action and its response")
        beats = []
    if body.get("scale") == "GRANDE" and len(beats) < 2:
        errors.append("R26_COMBAT: large battle needs at least two evidenced interactions")
    for n, item in enumerate(beats):
        if not isinstance(item, dict):
            errors.append("R26_COMBAT: malformed beat")
            continue
        _anchor(prose, item.get("literal_anchor"), errors, "combat beat " + str(n + 1))
        for key in ("actor", "attempt", "response", "consequence"):
            if not _words(item.get(key), 8):
                errors.append("R26_COMBAT: incomplete " + key)
    if body.get("does_not_nerf_genese") is not True:
        errors.append("R26_COMBAT: preserve GÊNESE, use terrain/choice/other characters")
    if body.get("other_characters_act") is not True:
        errors.append("R26_COMBAT: combatants must have agency")
    return {"mode": mode, "confirmed_action_responses": len(beats),
            "winner_predetermined": body.get("winner_predetermined")}


def _wonder(prose: str, body: dict, errors: list[str]) -> dict:
    mode = body.get("mode")
    if mode == "SEM_DESCOBERTA":
        return {"mode": mode, "evidenced_encounters": 0}
    if mode != "DESCOBERTA":
        errors.append("R26_WONDER: set DESCOBERTA or SEM_DESCOBERTA")
        return {"mode": mode, "evidenced_encounters": 0}
    encounters = body.get("encounters")
    if not isinstance(encounters, list) or not encounters:
        errors.append("R26_WONDER: a discovery needs witnessed evidence")
        encounters = []
    for item in encounters:
        if not isinstance(item, dict):
            errors.append("R26_WONDER: invalid encounter")
            continue
        _anchor(prose, item.get("literal_anchor"), errors, "wonder")
        for key in ("sensory_difference", "character_reaction", "world_independence"):
            if not _words(item.get(key), 18):
                errors.append("R26_WONDER: incomplete " + key)
    return {"mode": mode, "evidenced_encounters": len(encounters)}


def _magic(prose: str, body: dict, errors: list[str],
           archive_root: Path | None = None) -> dict:
    references = classify_named_spell_references(prose)
    known = set(references["active_or_unresolved"])
    used = body.get("spell_uses")
    if not isinstance(used, list):
        errors.append("R26_MAGIC: explicit spell_uses list required, may be empty")
        used = []
    identifiers = []
    majestic = []
    for item in used:
        if not isinstance(item, dict):
            errors.append("R26_MAGIC: malformed spell use")
            continue
        ident = item.get("spell_id")
        spell = get_spell(ident) if isinstance(ident, str) and ident else None
        if spell is None:
            errors.append("R26_MAGIC: unknown spell " + str(ident))
            continue
        identifiers.append(spell["id"])
        if spell["id"] in references["noncasting_mentions"]:
            errors.append("R26_MAGIC: a manual title or discussion cannot be claimed as a cast")
        literal = item.get("literal_anchor")
        _anchor(prose, literal, errors, "named spell " + spell["nome"])
        if not isinstance(literal, str) or spell["nome"].casefold() not in literal.casefold():
            errors.append("R26_MAGIC: spell name must be quoted in its usage anchor")
        if spell["nome"].casefold() not in prose.casefold():
            errors.append("R26_MAGIC: catalog spell name absent from prose " + spell["id"])
        caster = item.get("caster")
        if not _words(caster, 2):
            errors.append("R26_MAGIC: a specific caster must be named")
        else:
            source = str(literal or "")
            caster_in_anchor = caster.casefold() in source.casefold()
            extra = item.get("caster_anchor")
            same_scene = (
                isinstance(extra, str) and len(extra) >= 12
                and extra in prose and caster.casefold() in extra.casefold()
                and any(extra in scene and source in scene
                        for _, scene in scene_blocks(prose))
            )
            if not caster_in_anchor and not same_scene:
                errors.append("R26_CASTER: caster must be witnessed in literal spell scene")
        status = item.get("learning_status")
        if status not in ("ESTREIA_NARRADA", "JA_CONHECIDA_COM_PROVA"):
            errors.append("R26_MAGIC: distinguish first showing from already demonstrated")
        if status == "JA_CONHECIDA_COM_PROVA":
            proof = verify_prior_spell_source(
                archive_root, item.get("previous_source"),
                item.get("previous_literal_anchor"))
            if not proof["verified"]:
                errors.append(proof["error"])
            prior_quote = item.get("previous_literal_anchor") or ""
            if spell["nome"].casefold() not in str(prior_quote).casefold():
                errors.append("R26_PROVENANCE: previous quote does not name the same spell")
            if not _words(item.get("previous_source"), 20):
                errors.append("R26_MAGIC: prior demonstrated claim needs an exact source path")
        if spell["id"].startswith("R26X-"):
            # An atlas is not an already learned skill. The very first
            # appearance must show exactly how this particular tradition was
            # accessed, taught, discovered or independently invented.
            if status == "ESTREIA_NARRADA":
                lineage = item.get("acquisition") or {}
                if not isinstance(lineage, dict):
                    errors.append("R26_ORIGIN: acquisition must be a structured source")
                else:
                    pathway = lineage.get("pathway")
                    if pathway not in ("INVENCAO_INSTITUCIONAL",
                                       "ENSINO_DE_TRADICAO", "DESCOBERTA",
                                       "RITO_CULTURAL_APRENDIDO"):
                        errors.append("R26_ORIGIN: missing justified path to spell")
                    _anchor(prose, lineage.get("literal_origin_anchor"), errors,
                            "magical origin of " + spell["nome"])
                    if not _words(lineage.get("school_lineage"), 12):
                        errors.append("R26_ORIGIN: missing known magical lineage")
                    if pathway == "INVENCAO_INSTITUCIONAL":
                        person = lineage.get("inventor")
                        if not _words(person, 2) or person.casefold().strip().startswith("lucas"):
                            errors.append("R26_ORIGIN: city magic requires a specific non-Lucas inventor")
                        _anchor(prose, lineage.get("prototype_anchor"), errors,
                                "independent city invention")
                        if lineage.get("not_automatically_invented_by_lucas") is not True:
                            errors.append("R26_ORIGIN: no auto-invention by Lucas")
                        if not spell.get("origem", "").startswith("Três Arcos"):
                            errors.append("R26_ORIGIN: institutional origin outside established city")
                    elif spell.get("origem", "").startswith("Três Arcos"):
                        # Residents may LEARN foreign traditions; however this
                        # does not retroactively make a city-origin invention
                        # already exist without someone developing it.
                        errors.append("R26_ORIGIN: new Three Arches methods need narrated research")
            elif status == "JA_CONHECIDA_COM_PROVA":
                if not _words(item.get("previous_source"), 20) or not _words(item.get("previous_literal_anchor"), 14):
                    errors.append("R26_ORIGIN: reused technique needs prior episode path and literal evidence")
        if spell["id"].startswith("R26X-") and spell["circulo"] >= 7:
            # Large regional spells from the template-based 900 must be
            # individualized in lived fiction, not just assign a bigger rank.
            craft = item.get("individual_scene_design")
            if not isinstance(craft, dict):
                errors.append("R26_SPECIFICITY: high-circle regional magic needs unique scene design")
            else:
                for key in ("cultural_signature", "unique_mechanism",
                            "character_choice_or_meaning"):
                    if not _words(craft.get(key), 24):
                        errors.append("R26_SPECIFICITY: incomplete " + key)
                witness = craft.get("sensory_witness_anchor")
                consequence = craft.get("world_response_anchor")
                _anchor(prose, witness, errors, "individual regional magic sensory witness")
                _anchor(prose, consequence, errors, "individual regional magic consequence")
                narrative = str(literal or "")
                if not (
                    isinstance(witness, str) and isinstance(consequence, str)
                    and any(
                        narrative in scene and witness in scene and consequence in scene
                        and scene.index(narrative) < scene.index(witness) < scene.index(consequence)
                        for _, scene in scene_blocks(prose)
                    )
                ):
                    errors.append("R26_SPECIFICITY: sensory witness and effect must unfold in one scene")
        if spell["circulo"] >= 7:
            majestic.append(spell["id"])
    # A conjurer may repeat a legitimate spell in separate beats/scenes.
    # Each occurrence can carry its own literal anchor; no one-cast quota.
    if known.difference(identifiers):
        errors.append("R26_MAGIC: named grimoire spells in story not registered: " +
                      ", ".join(sorted(known.difference(identifiers)))[:160])
    summons = body.get("summon_uses")
    if not isinstance(summons, list):
        errors.append("R26_SUMMON: explicit summon_uses list required, may be empty")
        summons = []
    valid = {s["id"]: s for s in load_world()["invocations"]}
    summon_ids = []
    for item in summons:
        if not isinstance(item, dict) or item.get("summon_id") not in valid:
            errors.append("R26_SUMMON: unrecognized invocation")
            continue
        summon_ids.append(item["summon_id"])
        _anchor(prose, item.get("literal_anchor"), errors, "summon")
        if valid[item["summon_id"]]["nome"].casefold() not in prose.casefold():
            errors.append("R26_SUMMON: invocation name not in actual prose")
        if item.get("voluntary_pact_or_unconscious_construct") is not True:
            errors.append("R26_SUMMON: consent or non-conscious construction must be preserved")
    literal_summons = set(summon_ids_used_in_prose(prose))
    if literal_summons.difference(summon_ids):
        errors.append("R26_SUMMON: unregistered named invocation")
    return {
        "spells_used": sorted(set(identifiers)),
        "summons_used": sorted(set(summon_ids)),
        "high_circle_spells": majestic,
        "book_title_or_reference_mentions": references["noncasting_mentions"],
        "potential_unnarrated_incantations_for_human_review":
            references["requires_human_semantics"],
        "new_magic_does_not_retroactively_change_canon": True,
    }


def _spectacle(prose: str, body: dict, errors: list[str], high_circles: list[str]) -> dict:
    listed = body.get("moments")
    if not isinstance(listed, list):
        errors.append("R26_SPECTACLE: moments must be list, may be empty")
        listed = []
    scenes = dict(scene_blocks(prose))
    names = set()
    for item in listed:
        if not isinstance(item, dict):
            errors.append("R26_SPECTACLE: invalid moment")
            continue
        scene = item.get("scene")
        if scene not in scenes:
            errors.append("R26_SPECTACLE: scene does not exist")
            continue
        names.add(scene)
        bodytext = scenes[scene]
        first = item.get("first_anchor")
        second = item.get("reaction_anchor")
        _anchor(prose, first, errors, "spectacle action", body=bodytext)
        _anchor(prose, second, errors, "spectacle reaction", body=bodytext)
        if isinstance(first, str) and isinstance(second, str) and (
            first in bodytext and second in bodytext
            and bodytext.index(second) <= bodytext.index(first)
        ):
            errors.append("R26_SPECTACLE: reaction must follow manifested action")
        if first == second:
            errors.append("R26_SPECTACLE: action and reaction must be distinct moments")
        for key in ("dramatic_promise", "sensory_change", "lasting_consequence"):
            if not _words(item.get(key), 20):
                errors.append("R26_SPECTACLE: incomplete " + key)
        if item.get("not_just_reported") is not True:
            errors.append("R26_SPECTACLE: explicitly distinguish dramatization from summary")
    if high_circles and not listed:
        errors.append("R26_SPECTACLE: high-circle spell needs witnessed scene and reaction")
    return {"evidenced_moments": len(listed),
            "high_magic_needs_real_reaction": bool(high_circles),
            "quality_certification": False}


def _characters(prose: str, body: dict, errors: list[str]) -> dict:
    motions = body.get("character_evolution")
    if not isinstance(motions, list) or not motions:
        errors.append("R26_CHARACTERS: at least one grounded character beat required")
        motions = []
    known = {x["name"] for x in load_people()["profiles"]}
    distinct = set()
    for item in motions:
        if not isinstance(item, dict):
            errors.append("R26_CHARACTERS: invalid character beat")
            continue
        name = item.get("name")
        if not _words(name, 2):
            errors.append("R26_CHARACTERS: name required")
        else:
            distinct.add(name)
        _anchor(prose, item.get("literal_anchor"), errors, "character decision")
        if not _words(item.get("decision_or_reaction"), 20):
            errors.append("R26_CHARACTERS: show what character did")
        if not _words(item.get("emotional_or_relational_delta"), 20):
            errors.append("R26_CHARACTERS: show genuine change or sustained identity")
        if item.get("new_power_claimed") is True and not _words(item.get("power_source"), 20):
            errors.append("R26_CHARACTERS: no new remembered power without historical or first-scene proof")
    return {"characters_evidenced": sorted(distinct), "known_important_characters": len(known),
            "memory_automatically_promoted": False}


def _repeat(prose: str, body: dict, errors: list[str],
            previous_counts: list[int] | None) -> dict:
    structure = assess_experience(prose, previous_counts=previous_counts)
    risks = list(structure["risks"])
    leaked = [(m.start(), m.group(0)) for m in MOTIF.finditer(prose)]
    if leaked:
        errors.append("R26_REPEAT: obvious backstage justification leaked into fiction")
    if any(r.startswith(("R25_FOCUS", "R25_TEMPLATE")) for r in risks):
        if not _words(body.get("pacing_justification"), 55):
            errors.append("R26_REPEAT: explain repetitive scene mold using actual dramatic need")
    note = body.get("variation_decision")
    if not _words(note, 20):
        errors.append("R26_REPEAT: review narrative variation without scene quotas")
    return {
        "scenes": structure["scene_count"], "short_scene_share": structure["short_scene_share"],
        "risks": risks, "backstage_intrusions": [x for _, x in leaked[:8]],
        "historical_scene_template_risk": any(x.startswith("R25_TEMPLATE") for x in risks),
        "not_an_artistic_grade": True,
    }


def audit_fantasy(prose: str, review: dict | None, *,
                  head_episode_id: str, previous_counts: list[int] | None = None,
                  archive_root: Path | None = None) -> dict:
    """Evaluates one *actual* chapter prose, never chooses an outcome or writes canon."""
    if not isinstance(prose, str) or not prose.strip():
        raise ValueError("R26 needs source prose")
    errors = []
    codex = validate_codex()
    authority_bible = validate_authority_bible()
    if authority_bible["errors"]:
        return {"errors": authority_bible["errors"],
                "ready": False, "canon_changed": False}
    if codex["errors"]:
        return {"errors": ["R26_CATALOG: " + "; ".join(codex["errors"])],
                "ready": False, "canon_changed": False}
    if not isinstance(review, dict) or review.get("schema") != SCHEMA:
        return {"errors": ["R26: missing v3 fantasy review"],
                "ready": False, "canon_changed": False}
    if review.get("source_episode_id") != head_episode_id:
        errors.append("R26_HEAD: fantasy review not anchored to live author choice HEAD")
    if review.get("cannot_choose_for_author") is not True:
        errors.append("R26_AUTHORITY: never preselect future author actions")
    if review.get("genese_unrestricted") is not True:
        errors.append("R26_GENESE: GÊNESE remains unrestricted; no arbitrary resource nerfs")
    if review.get("backstage_invisible") is not True:
        errors.append("R26_BACKSTAGE: audit notes cannot be narrator prose")
    authority = scan_creation_prose(prose)
    errors.extend(authority["errors"])
    magic = _magic(prose, review, errors, archive_root=archive_root)
    combat = _combat(prose, review.get("combat", {}), errors)
    wonder = _wonder(prose, review.get("wonder", {}), errors)
    spectacle = _spectacle(prose, review, errors, magic["high_circle_spells"])
    characters = _characters(prose, review, errors)
    repetition = _repeat(prose, review, errors, previous_counts)
    return {
        "schema": "worldroot-r26-evidence-receipt-v1",
        "status": "R26_VERIFICADO_NA_ESTRUTURA" if not errors else "R26_BLOQUEADO",
        "ready": not errors, "errors": errors,
        "source_sha256": sha256(prose.encode("utf-8")).hexdigest(),
        "source_head_episode_id": head_episode_id,
        "codex_counts": {k: codex[k] for k in
                         ("schools", "named_spells", "summons", "creatures", "wonders",
                          "tracked_characters", "historical_feats")},
        "magic": magic, "authority": authority, "combat": combat,
        "wonder": wonder, "spectacle": spectacle,
        "character_memory": characters, "repetition": repetition,
        "canon_changed": False, "independently_human_certified": False,
        "narrative_automatically_generated": False,
        "magic_proposals_autocanonized": False,
    }
