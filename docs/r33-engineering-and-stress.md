# WORLDROOT R33 — engineering and resilience candidate

Scope: Crônicas only. No fictional material, rules of magic, world, entities or narrative data from another project. Engineering comparison read from Eidoryn main, docs/operations/UNIFIED_RUNTIME_1_6_2.md, LEGENDARY_EXPERIENCE_1_7.md, GITHUB_ONLY.md; src/eidoryn/github_store.py (blob 6aa8c984f4765103616291940376723cb84a21e2), src/eidoryn/runtime.py (blob 265c94ac8e1654fcac572e74c781ebf12d9bc108). Reimplemented independently, preserving WORLDROOT's own HEAD/choice/closure semantics.

## Procedure
1. Retrieve canonical HEAD, pending immutable draft and exact current choices. Never manufacture choice for maintenance. The existing D574 draft remains immutable. Only after actual author choice, normal closure advances HEAD; read back choice, closure and HEAD.
2. Use R32/R33 memory preparation: SQLite, existing source-verified cards, graph, current events and character knowledge; optional deep pool up to 400. Curated candidates are references, not new canon. Critical facts and all material claims reviewed; no invented attributes or quantities. Use current policy as distinct authority. Do not pass entire candidate pool into prose.
3. Create new requests/<delivery_id>.json with schema worldroot-r33-request-v1, project CRONICAS_DE_UM_NOVO_MUNDO, delivery_id, head, choice_sha256, requirements, reviewed, domain_review, scene_plan. Exact closed author choice captured by existing workflow, not re-created. The request must exist before preparation. Run python -m worldroot.r33_runtime --archive-root archive --request archive/requests/<id>.json in a disposable verified checkout; persist preparations/<id>.json once, commit/read back before writing. No overwrite or force-push. The new CLI does not itself publish a GitHub commit. A branch-specific pipeline still needs operational deployment after acceptance.
4. Draft with metadata.worldroot_revision=33, prior existing v3 inbox schema and R25/R26 rules, r32_review, r33_review (preparation_sha256, eleven reviewed dimensions, optional explanation of organic scene change). R33 permits changed scene mapping only with explanation and all original requirements retained. Applied review needs literal prose evidence; held must have genuine reason; no forced scenes. No auto literary grade.
5. Verify submission with r33_runtime.verify_submission, then existing draft inbox; read back original immutable narrative, R32 sidecar and preparation_r33 receipt. The receipt binds request, preparation, source HEAD, choice, prose hash. Verify historic receipts with --verify-history. No automatic story closure or choice generation.
6. Maintain equal visual treatment and four meaningful routes (one main, three secondary), action free 5. Preserve archived choices, R30 version compatibility, all 109 rules; side branches move causally and independently. No fictional status report instead of story.

## Tests and quality gates
- R32 frozen real corpus: 100 known and 21 additional reference queries; 99/100 and 17/21 at 400 candidates, not independent semantic accuracy.
- R33 curated route: pre-existing source-checked R30 cards, separate benchmark disclosure. New randomized literal replay of 120 sampled closed-episode text probes, seed 3301, not human paraphrase evaluation.
- Read-only stress matrix: 128 queries at each of 1/4/16/32 workers; compare deterministic IDs and report p95/throughput, not universal production capacity.
- 256 concurrent identical preparations with exact one creation; conflicting inputs rejected, backup restore, corruption/stale vector rejection, all critical evidence.
- Full contract rehearsal with a disposable archive copy and D574 existing prose, ten domains, all scene mappings, eleven editorial review statuses, no real new narrative or choice.
- Complete previous regression suite and R30/R31/R32 audits. No claimed independent literary quality without author/readers. Failures block release; no forced main merge.
- Source methods: OpenAI evaluation best practices and trustworthy third party evaluations; Google SRE testing reliability and cascading failures. Continuous evaluation after changes, separate holdout, stress and fault injection, verify results and recovery.
- Neural E5 and independently authored multi-fact semantic gold set remain separate requirements. 95% candidate recovery in development is not a 95% guarantee for every narrative.

## Release
The private branch remains a candidate while any required acceptance is unverified. A main-only commit diverges: reconcile actual file differences and test combined tree before merging. Do not retcon, update story-archive or promote the pending D574 draft as part of engineering maintenance.
