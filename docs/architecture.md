# WORLDROOT living architecture — contracts v0.2

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
- `record_external_readback(...)`: **DEPRECATED AND BLOCKED**. Untrusted client-supplied bytes cannot certify an upload.
- `GoogleDriveSynchronizer.sync(...)`: authenticated Google API client, idempotent search, metadata + independent blob download and SHA256 verification; synthetic fixture is allowed only explicitly in tests.
- `GoogleDocsHeadPublisher.publish(...)`: guarded `requiredRevisionId` Google Docs HEAD update with readback and explicit author approval.
- `confirm(id) -> receipt`: stable, nonduplication event logging
- `promote(id, author_approved=True, expected_head_day=N, expected_head_release=R) -> release`: guarded only after independently verified HEAD receipt
- `status() -> runtime status`

External Drive/Sheets/Docs connector calls run in the authorized ChatGPT/tool environment, not from public code. Workflows **must never pretend** to have sent or fetched documents if tool access was missing.

## Remaining adapters (NOT yet production ready)

- Google Drive downloader exists in Python (ADC), but has only synthetic local tests and is not deployed to an authenticated runner. Outbox stores retries.
- Google Docs HEAD revision guard exists; Base/Atlas multi-service synchronization and its authenticated proof are not implemented end-to-end.
- Read-only `legacy.py` FTS bridge and evidence-first `memory.py` exist; authenticated per-character retrieval and complete semantic review are still pending.
- Chapter-close event extractor requiring review for subjective claims
- Scheduled CI/regression suite with real connector environment as opt-in

No Supabase project is required for this baseline; avoid a second authoritative database. The Google APIs/SQLite bridge is NOT a security boundary against malicious code running in the same interpreter.

See [new hardening roadmap](hardening-r7-roadmap.md) and [narrative interface contract](narrative-interface-contract.md).
