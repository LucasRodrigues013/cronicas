# WORLDROOT — Public hardening roadmap (code only)

The purpose of this branch is to harden a private interactive-narrative runtime without replacing or publishing its story data. The source of truth for literary content is an **authorized private Google Drive**. Neither story text, character details, unpublished plots, nor private SQLite archives are appropriate for this public repository.

## Implemented code in this branch

- `ledger.py`: append-only delivery/event ledger, idempotent literal hashes, local archive, strict story-clock validation, no arbitrary manually supplied Drive receipt, receipt-gated confirmation, SQLite migration and durable outbox. HEAD release/day compare-and-swap guard.
- `drive_bridge.py`: Google Drive API client instantiated via Application Default Credentials in a trusted environment, idempotent file discovery using restricted `appProperties`, independent metadata retrieval and blob download with SHA256/MD5/size verification. Google Docs HEAD publisher uses `requiredRevisionId` and readback. Synthetic API fixture only with explicitly enabled test mode.
- `memory.py`: immutable entity IDs, candidate aliases without silent merges, fact provenance by source line, per-character temporal knowledge, relationship evidence and threads. Planned facts cannot be queried as canon or exported as public facts.
- `narrative.py`: non-destructive editorial preflight for book closure, five-choice interface contract, repetition warnings, world-reaction and agency principles. This **does not autonomously generate chapters**.
- `backup.py`: SQLite Online Backup API plus independent restore/integrity drill and SHA256 manifest.
- `legacy.py`: read-only access to the previously created private FTS5 literal index; no migration or overwrite.
- GitHub Actions: offline synthetic tests, full-commit-SHA-pinned actions, no private credentials.

## Production status

**Not a deployed autosave service.** `GoogleAPITransport.from_adc()` requires a separately deployed authenticated Python runner. Tests use fixtures, not real Google credentials. The Google Docs HEAD publisher is guarded, but independent Base/Atlas connectors and a distributed outbox/controller for all writes are still necessary. Python source executed with malicious in-process access is not isolated by this adapter alone.

Required evidence before production: real authenticated upload/download after deliberate transient failure and retry without duplicate; independent HEAD/Atlas/other dependency readbacks; current Google Docs revision guard; protected worker identity; backup/restore exercise; author approval and immutable event proof; a dedicated public-Wiki spoiler audit.

## Research and source references

- Google Drive v3 downloads and metadata: https://developers.google.com/workspace/drive/api/guides/manage-downloads ; https://developers.google.com/workspace/drive/api/reference/rest/v3/files
- Google Drive appProperties: https://developers.google.com/workspace/drive/api/guides/properties
- Google Docs revision write control: https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate
- SQLite online backup: https://sqlite.org/backup.html
- OWASP RAG security: https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
- GitHub Actions secure use: https://docs.github.com/en/actions/reference/security/secure-use
- Interactive narrative variables/choice patterns: https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md

The substantive story audit, canonical facts, proposed plots and character histories remain on private Drive, not here.
