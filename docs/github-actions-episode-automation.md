# WORLDROOT — GitHub Actions after the episode choices

**State, 17 November 2026:** GitHub `LucasRodrigues013/cronicas` is private. An actual read-only archive package-validation workflow is installed on the `story-archive` branch: `.github/workflows/episode-archive-qa.yml`. Its first push run passed. This does **not** mean that Google Drive, HEAD, Base Viva, Atlas or semantic records have been synchronized by that workflow.

## The episode lifecycle

1. **Before releasing the message with options:** ChatGPT (when tool access permits) writes the *exact* final narrative and all five choices, a stable episode ID, metadata, candidate events, and a SHA-256 manifest into `episodes/<id>/draft/` of the private `story-archive` branch. The final file to commit is `manifesto_imutavel.json`. If the write fails, ChatGPT says the external draft is pending and does not pretend the episode was archived.
2. **GitHub Actions on manifest push:** the installed archive integrity workflow verifies all five sidecars, source text, checksum, five-choice structure and RASCUNHO state. Passing means only *GitHub archive integrity checked*.
3. **Future Drive mirror (NOT ACTIVATED):** template `docs/templates/archive-drive-sync.yml` can be installed on `story-archive` after Google OIDC federation and Drive folder permissions have been set up. It uses the existing `GoogleAPITransport` and `VerifiedArtifactPublisher` through `worldroot.archive_actions`, independently downloads all six files, and checks SHA-256. It never advances the canonical HEAD.
4. **On user's actual next choice:** ChatGPT first retrieves the preceding immutable draft, validates the choice, reviews newly narrated events and calls the guarded episode closure. The Base Viva / Atlas and HEAD updates require authenticated Drive/Docs/Sheets readback with revision checks. Only after successful closure may the next part be generated. This second operation is **not yet deployed as an Actions runner**.
5. **Failed or partial job:** the official HEAD does not move. Re-run the same idempotent operation using stable episode IDs; do not repair text from memory or fabricate a receipt.

## One-time WIF provisioning required before Drive sync

- Create/identify a Google Cloud project with Workload Identity Pool + Provider constrained to this GitHub repository **and only the allowed archive workflow/ref**. Create or reuse a service account with minimal permissions.
- Share the project's **restricted Drive target folder** with that service account (if provider policy permits). Confirm access to only the specific folder; an OIDC token by itself does not grant access to the user's Google Drive files.
- Configure **repository variables** `WORLDROOT_DRIVE_WIF_PROVIDER`, `WORLDROOT_DRIVE_SERVICE_ACCOUNT` and `WORLDROOT_DRAFTS_FOLDER_ID` in GitHub Settings → Secrets and variables → Actions. The provider and account paths are identifiers, not token secrets; never paste credentials into files or chats.
- Review and approve the WORLDROOT engine commit SHA, replace the mutable reference in the template with that SHA, install the template as `.github/workflows/archive-drive-sync.yml` on `story-archive`, and validate using an entirely synthetic episode first.
- Mark remote sync as complete only after the workflow returns success and a *new* Drive download compares identically. Keep the existing `story-archive` integrity workflow separate; a green integrity check does not mean remote sync has finished.

## Current limits

- ChatGPT itself does not emit a guaranteed end-of-response webhook. Its connected GitHub tool must explicitly create the archive files before completing the answer, or a separate trusted app must submit the manifest commit. A text prompt alone cannot guarantee a tool call in every future chat.
- Do not put a narration or character secret in issue comments, workflow input, logs, Actions artifacts, or an untrusted repository.
- A GitHub Actions runner is ephemeral. SQLite stored only in the runner is lost after the job; `WorldrootStore` needs a separately retrieved, versioned, restored snapshot for a canonical closure. The stateless Drive mirror is deliberately limited to drafts for this reason.
- **Do not start Part III automatically**: the next author choice is a necessary gate, and D529 Part II must be archived in its exact original text before it can be closed.
- No merge to `main` or release tag is implied by this prototype. Audit and approve release procedures separately.

## Acceptance checklist

- [x] Private GitHub verified with real repository metadata.
- [x] Read-only draft-integrity workflow installed on `story-archive` and confirmed successful.
- [x] 5 isolated archive integrity tests + 137 existing local engine regression tests passed.
- [ ] Automatically commit the literal final ChatGPT output at end of each new part; requires a reliable host/app action.
- [ ] Set up Google OIDC and Drive folder access for a runner.
- [ ] Install and validate the optional Drive-mirror workflow against a synthetic full package.
- [ ] Implement authenticated next-choice closure runner with versioned SQLite restore, Base/Atlas/HEAD guarded updates and real failure/retry tests.
- [ ] Verify all released scenes and characters against the approved story and perform controlled publication.
