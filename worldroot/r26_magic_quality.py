"""R26.2 read-only diversity audit of 1,020 names / 90 actual regional mechanisms.

Structural counts are NOT equivalent to 1,020 distinct illustrated spells.
This report explicitly quantifies editorial templating risk, without
silently rewriting or auto-canonizing any character repertoire.
"""
from __future__ import annotations

import json
from collections import Counter

from .r26_magic_catalog import load_grimoire, load_regional_atlas, norm


def audit_regional_variety() -> dict:
    atlas = load_regional_atlas()
    expanded = atlas["spells"]
    families = [f for s in atlas["schools"] for f in s["familias"]]
    count_by_school = Counter(x["escola"] for x in expanded)
    count_by_circle = Counter(x["circulo"] for x in expanded)
    named = {norm(x["nome"]) for x in expanded}
    lineage_ids = {x["serie"] for x in expanded}
    shared_suffixes = Counter(
        x["efeito_proposto"].split(", operando sobre ", 1)[-1]
        for x in expanded
    )
    # 90 branches × 10 Círculos: each rank has the same broad sentence skeleton.
    # This is not an invalid catalog; it is a warning against numeric hype.
    repetitive = (len(shared_suffixes) <= 15
                  and max(shared_suffixes.values(), default=0) >= 50)
    return {
        "schema": "worldroot-r26-2-actual-magic-variety-audit-v1",
        "total_named_spells": len(load_grimoire()["spells"]),
        "regional_named_variants": len(expanded),
        "regional_lineages": len(lineage_ids),
        "distinct_lineage_mechanisms": len(set(f["mecanismo"] for f in families)),
        "regional_schools": len(count_by_school),
        "count_by_circle": {str(x): count_by_circle[x] for x in range(10)},
        "schools_have_50_variants": all(x == 50 for x in count_by_school.values()),
        "regional_unique_names": len(named),
        "formula_sentence_frames": len(shared_suffixes),
        "largest_formula_frame_reuses": max(shared_suffixes.values(), default=0),
        "editorial_template_risk": "ALTO" if repetitive else "NÃO_DETECTADO",
        "all_1020_have_unique_real_world_mechanics": False,
        "all_1020_have_individual_narrative_review": False,
        "authoring_guidance": [
            "1,020 names are a searchable reservoir; 90 regional families have distinct basic mechanics.",
            "Do not narrate 10 ranks as the same spell with a larger visual effect.",
            "Before debut, build a unique sensory grammar, target, counterplay, cultural owner, cost to relationships and dramatic action.",
            "An authority is not a spell. Never apply this report's circle grades to GÊNESE.",
        ],
        "canon_changed": False, "spoilers_revealed": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_regional_variety(), ensure_ascii=False, indent=2))
