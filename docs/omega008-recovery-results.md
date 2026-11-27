# OMEGA-008 — Historical recovery and controller preflight (2026-11-27)

## Scope and custody
Candidate PR #79, review/omega-cycle-1. No merge, no writes to main or story-archive. Narrative source pin 9dd632fb0bcd84dfce5b631013fdc67d7492ac5d; D579 closed, D580 official draft pending. This cycle extends the existing engine, does not replace it. Free-Only; no model API or EIDORYN dependency.

## Real execution evidence
- Code commits cf5ca93c8f3ca46dff6623d362e20849c285a271 and f82ff91c0e3782516931305f42145aa203ec5fa9.
- First full-source recovery: 45990527815, success, 5.106934s. Latest recovery with source readback: 45990679306 / job 140477416544, success; scan 7.816397s, total 9.145533s.
- Six verified historical files, 611011 original lines; 50 closed episodes, 95282 additional prose lines. 154190 mention-line rows (119745 Response, 1913 Prompt, 32532 closed prose); 275 alias keys. Counts are lexical candidates, not facts, not distinct events, not proof of all days. Unregistered speakers and ambiguous aliases are explicitly marked. Speaker label recognition is limited to native bold-name format; historical text may use other formats.
- Public event candidates: 24/27 PUBLICO events have lexical candidates. Other visibility layers excluded from this linkage. 754 canonical temporal events remain in the existing bridge; zero historical typed Codex events. No automatic conversion or promotion.
- Real Osvan recovery: 12 exact references, all in D579 closed prose; six bold dialogue labels. All 12 source lines read back; one historical Response line verified; forged anchor and role swap rejected. Candidate dossier docs/omega008-osvan-candidate.json derived from exact D579 lines, with unresolved fields. This is not a new canonical registry record.
- Safe-public regression: 45990527771, 901/901, 14.167s; latest code 45990679323, 901/901, 22.297s.
- Second episode replay after changes: 45990527663 and 45990679160 both success. Clean preflight 10/10, 5.283208s first, 3.285478s latest; combined negative preflight 2.877405s first, 1.799475s latest, detected r25_reader, r35_longform, r36_submission and archive_assembly. No preflight grants release. Native release 15/15, zero errors, repeat archive idempotent and original archive unchanged. Latest entire replay 16.080728s (no new prose generation).
- These are development tests, not held-out semantic evaluation or end-to-end author command timing. Stage C HOLD; Level 7 not independently certified.

## Operator usage
Run from the candidate engine checkout, against a verified archive checkout. Projection is intentionally opt-in and outside source archive; no changes to historical preparation hashes. No automatic injection of historical candidates into future prose.

```sh
python -m worldroot.omega_historical_recovery --archive-root /path/to/archive build --output /path/outside/archive/omega.sqlite
python -m worldroot.omega_historical_recovery --archive-root /path/to/archive query --graph /path/outside/archive/omega.sqlite --name Osvan --readback
python -m worldroot.omega_controller_preflight --archive-root /path/to/archive --payload /path/to/submission.json
```

The readback command is editorial-only: it can return raw Prompt/Response material and must not be inserted into character knowledge. The query key is a name/alias; associated candidate IDs are returned rather than resolved silently. The source projection is reproducible, not deployed as a permanent production DB. The CLI preflight does not auto-generate sidecars, does not certify narrative quality, and does not replace archive/release.

## Next gate
Use candidate queue and verified references for curated identity, time, location, relationship, power, item, knowledge and world-state recovery; continue by bounded book/time batches. Preserve original sources and explicit unresolved fields. Add source-backed approval before merging identity records. Integrate with fresh preparation only after reproducibility and regression tests; don't invalidate existing receipts. OMEGA-009 literary intelligence and independent blinded validation follow this recovery work. Existing pending author choice and canon are untouched.
