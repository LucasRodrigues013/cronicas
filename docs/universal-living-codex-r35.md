# Codex Vivo Universal — R35 (proposed deployment)

Author direction: 2026-11-26. Active design registry in private story-archive: editorial/registries/universal-codex-design-d580-v1.json. Age approvals in female-character-design-d580-v2.json. The registry preserves 167 review identities, 81 character cards, 14 species design profiles, 1,020 original R26/R26.1 spell IDs, 30 schools, and links to immutable original sources. It is not a canonical rewrite. Four unmatched legacy profiles and provisional identities require contextual reconciliation.

## Authority and workflow
- Before each part, recover live HEAD/RESUME, actual choice, exact entity ID, aliases, origin, species, appearance, voice, role, relationships, skills, current location, inventories and spell learning. R33/R34/R35 existing literal evidence gates remain mandatory.
- R35 preparations bind the registry SHA and focal identity candidates. Graph recovery is additive; no graph candidate is automatically a fact. Exact ID is prioritized over aliases. The single SQLite graph is a derived projection of the registry and reviewed closure receipts, not a parallel narrative motor or replacement for the canonical journal.
- A drafted episode with a new preparation has an explicit r33_review.codex_delta. Its prose hash, entity IDs, source line and literal anchor are validated. Named dialogue and focal names require disposition; other detected names are candidate mentions, not automatically appearances. New identities require review against aliases; use permanent IDs only after resolution. Generic roles and references can remain unresolved with evidence. Never merge homonyms by name alone.
- Events distinguish world/character knowledge/backstage. Do not expose secret knowledge to a character; the graph excludes private knowledge from general lookup. Location is last observation, not a permanent GPS signal. Do not fill absent information with guesses. Each spell has an independent learned/cast state and school membership; a school link is a research candidate, not possession. GÊNESE remains special, outside 0–IX.
- Item instance ID and custody are independent of item type; acquire, transfer, store, equip, unequip, consume, lose and use are separate events. A use need not change ownership. Record event location if known, actor, method, date and exact anchor. Never infer ownership from a mention or use.
- New design is prospective; generated appearance age is seeded and saved once, not a birth date, historical life or species classification. Respect explicit ages and existing source. Four blank ages remain unknown. External examples are inspirations, not transplanted lore.

## Delta example (synthetic, NOT an actual episode)
Inside r33_review:
```json
{
  "codex_delta": {
    "schema":"worldroot-codex-delta-v1",
    "episode":"EXAMPLE",
    "prose_sha256":"<sha256 of exact prose>",
    "new_entities":[],
    "unresolved":[],
    "events":[
      {"kind":"STORE","entity_id":"lucas","day":581,"clock":"09h30","scope":"WORLD","location_id":"torre-criador","value":{"item_id":"example-item-instance","location_id":"torre-criador"},"line":3,"anchor":"<exact narrative text>"}
    ]
  }
}
```
Example IDs, day and sentence are placeholders; never copy as canonical evidence. Events: APPEARANCE, MOVE, ACQUIRE, TRANSFER, STORE, EQUIP, UNEQUIP, CONSUME, LOSE, USE_ITEM, LEARN, CAST, ATTRIBUTE, KNOW, RELATION. New item/location/character must resolve to a permanent ID or explicit unresolved candidate. Source date must follow actual scenes. A technical check does not certify semantic attribution.

## Incremental operations
Run `python -m worldroot.live_codex --archive-root archive` to materialize the single graph from verified archive state. The graph is stored at canon/codex.sqlite. Replaying a closed event is idempotent; changed receipt or source, orphaned episode or custody conflict is rejected. The projection is prepared on a disposable copy and atomically replaced. If registry changes, rebuild from immutable receipts. New close/restore hooks refresh the graph; old episodes with no Codex delta remain historical recovery sources, not evidence of absence. Do not close D580 merely to test.
 
## Deployment gates
1. Run unit suite and full existing R35 regression; verify actual archive and graph readback. Run sample close/replay/restore in a disposable copy, including two different actors, named/unnamed identities, failed transaction, private knowledge and spell acquisition.
2. Verify workflow commit inclusion for canon/codex.sqlite and pin the validated engine SHA in private archive workflows; confirm actual dispatch and readback. A PR or successful local test does not prove operational deployment.
3. Review all original 9,229 candidate contexts and remaining visual references separately. Do not claim coverage of all named appearances or full semantic review based on regex. No historical episode or author menu rewritten.
4. Preserve human author control over story closure. No external system automatically reads ChatGPT messages.
