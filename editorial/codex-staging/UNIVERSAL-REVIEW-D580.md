# Universal Codex review — D580 (staging only)
 
Reviewed source: `editorial/codex-staging/universal-review-d580-v1.json`, blob `83d46cabda140a5ddb278b1edd4c1eb2d1631c0f`; 167 review rows (136 original, 8 missing seeds, 23 provisional identity candidates), 56 attachment-linked historical observations, 34 preserved prior literal observations, 1,747 queue rows triaged without semantic certification. 18/92 visual files inspected in inventory. HEAD D579 sequence 50, D580 draft. Source readback via Git blob because Contents returned empty content. All seven structural checks passed in the readback. No canon promotion, no draft closure, no production changes.

## Field resolution
- Preserve existing IDs. candidate:* keys are provisional only; reconcile against aliases and complete sources before assigning permanent IDs.
- Current value remains unknown until the current temporal state is reconciled. Historical observations and approved prospective design are separate. An episode attachment anchor needs exact match against verified private archive and line/hash before promotion.
- Every canonical claim must include entity ID, field, typed value, validity interval, source ID/episode, exact anchor, source SHA-256, line, source role, knowledge scope and review disposition. Do not use prompts, pilot D579 or illustration labels as event proof. A later reference is not current physical presence or new use.
- A new author design can fill visual/voice fields prospectively after explicit approval; unresolved numeric ages, populations, engineering dimensions, relationships, powers and mysteries stay unknown. No external lore copied. Existing D580 v2 approved appearance takes precedence over conflicting art; Lira age 18 is explicit, other ages as recorded.
- One universal entity model, multi-domain tags, field history and typed relationships. Existing SQLite graph remains the single projection; do not create ten independent databases.
- Queue classifications are routing hints, not deletion or identity decisions. Review generic roles by scene if recurring. Plot aliases must not cause characters or artifacts to become plot identities.
 
## Incremental integration acceptance (not yet implemented)
The existing build.py scan() is an audit ingestion routine: unchanged source+status is idempotent; changed source or status is rejected; main() deletes/rebuilds the output DB, has a fixed D580 assertion, and samples at most two regex hits per entity/field/source. This is not a complete incremental semantic pipeline. Do not label it production-ready. The catalog and audit results are older projections than current seed/visual inventory. The workflow already contains a graph retrieval probe but published audit.json lacks the new probe field, so confirm a fresh CI run before relying on it.
 
1. Preserve scan() audit path. Move reviewed claims through a versioned, transactional delta on the same SQLite projection; verify immutable source hash/line and entity attribution. Use unique assertion key (source hash, entity ID, field, line, claim identity), append-only history, deterministic replay; track source lifecycle separately so a pending-to-closed transition never silently accepts altered bytes. Closure requires real author choice. Quarantine disputed or missing facts, do not write them into current fields.
2. Integrate with existing worldroot.memory_continuity.creation_packet(..., graph_db=...) on main: it checks graph HEAD and loads domains dossiers/plots/assets. Keep those transport values for backwards compatibility and store the ten canonical domain tags inside the record or linked tables. Supply fresh graph snapshot during R33/R34/R35 preparation; exact-ID requests must prioritize exact identity, ambiguous aliases return candidates with reason. Never let graph candidates bypass review_creation / evidence gate, character_design binding, or author policy.
3. Verify checksum and manifest at request time; reject stale HEAD; compare before and after state, prevent draft/pilot leakage and knowledge leakage; preserve R35 preparation, literal writing and final readback.
4. Homologation gates: identical delta twice; changed immutable source rejected; real pending-to-closed transition with choice; interruption rollback and restart; historical replay vs incremental equality; alias and homonym cases (AERÚN, Lira, Tessa, NÓX, Aeldric); fact vs design vs draft vs knowledge; ten-domain retrieval; original R35 tests; HEAD unchanged for audit. Record actual CI run IDs and results before release. Do not merge this staging artifact as production integration.
 
## Review statistics
{
  "existing_records": 136,
  "seed_missing": 8,
  "new_provisional_candidates": 23,
  "total_review_rows": 167,
  "source_attachment_observations": 56,
  "prior_literal_observations": 34,
  "queue_rows": 1747,
  "queue_classes": {
    "RESOLVE_BY_ENTITY_DOMAIN_AND_CONTEXT": 20,
    "MATCH_CANDIDATE_REVIEW": 19,
    "STRUCTURAL_LABEL_CANDIDATE": 132,
    "NEEDS_CONTEXT": 1551,
    "GENERIC_ROLE_NOT_GLOBAL_ID": 25
  },
  "visual_inspected": 18,
  "visual_total": 92,
  "candidate_contexts_not_reviewed": 9229,
  "production_integration": false,
  "structural_checks": {
    "unique_ids": true,
    "domain_membership": true,
    "observations_have_attachment_episode_literal": true,
    "all_queue_rows_preserved": true,
    "all_prior_observations_preserved": true,
    "no_canon_promotion": true,
    "all_ten_domains_represented": true
  }
}

HEAD comparison against live story-archive during prior readback: identical. Domain classification counts (multi-domain): {"Arsenal":21,"Tecnologia":32,"Ambientes":15,"Personagens":81,"História e mistérios":14,"Organizações":6,"Bestiário":5,"Atlas mundial":23,"Magia e poderes":5,"Cultura e economia":3}.
