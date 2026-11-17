# WORLDROOT living architecture — contracts v0.1

## Authority and security

| System | Responsibility | Non-responsibility |
|---|---|---|
| Restricted Google Drive | Immutable literal chapter payloads, HEAD, checkpoint, creative documents and confidential sources | Python/Git version control |
| Public GitHub | Source code, tests, CI, API contracts and technical reviews | Story text, unpublished plots, user personal data, private SQLite |
| Private SQLite | Append-only deliveries/events, readback receipts, current operational checkpoint | Public web access or an independent creative authority |
| ChatGPT | User-facing narration, authorization, per-turn connector orchestration | Unsupervised daemon/background autosave |

## Compatibility

Existing WORLDROOT 4.3 editor/FTS runtime remains a **read-only research adapter**, living in the restricted Drive package. This repository adds an independent private event journal, not a replacement for its 618,070-line literal index. Future migration should attach a *read-only* v4.3 database and avoid changing historical tables.

## States and event classifications

`PREPARADO`: stable delivery ID, source text hash, metadata and event proposals.
`VALIDADO`: metadata, chronology and consent checked; creative semantics still require editorial validation.
`GRAVADO`: original bytes archived locally, atomic overwrite protection.
`CONFERIDO`: SHA256/byte count independently checked after local readback.
`CONFIRMADO`: journal finalized **only after** an independently checked Drive readback receipt; local-only state remains `CONFERIDO`.

For state promotion to canon: requires verified Drive readback, explicit author approval, head-version lock and a separately reviewed record of each event. `PLAN / DRAFT / SIMULATED / PENDING` cannot be promoted as narrated.

Approved event statuses: `NARRADO`, `CANONICO`, `RASCUNHO`, `SIMULADO`, `PLANEJADO`, `PENDENTE_APROVACAO`.
Knowledge scopes: `PUBLICO`, `PRIVADO_PERSONAGEM`, `BASTIDORES`. The public wiki must be generated only from whitelist public facts; hiding DOM blocks is not sufficient.

## API contracts

- `prepare(id, full_literal, metadata, events) -> receipt`: idempotent by ID+hash+metadata+events
- `validate(id) -> receipt`: monotonic story day; no future skip without approval
- `write_literal(id, full_literal) -> receipt`: archive to private directory, atomic writing
- `verify_local(id) -> receipt`: SHA256 readback
- `record_external_readback(id, provider='google_drive', locator=verified_id, returned_bytes=bytes) -> receipt`: independently verified external bytes
- `confirm(id) -> receipt`: stable, nonduplication event logging
- `promote(id, author_approved=True, expected_head_day=N) -> release`: guarded update
- `status() -> runtime status`

External Drive/Sheets/Docs connector calls run in the authorized ChatGPT/tool environment, not from public code. Workflows **must never pretend** to have sent or fetched documents if tool access was missing.

## Next adapters (not claimed implemented)

- Google Drive uploader with re-download proof and retry / deferred outbox
- HEAD and Atlas update with comparison-and-swap revision checks
- Search integration with the full v4.3 literal index and public/private knowledge views
- Chapter-close event extractor requiring review for subjective claims
- Scheduled CI/regression suite with real connector environment as opt-in

No Supabase project is required for this baseline; avoid a second authoritative database.
