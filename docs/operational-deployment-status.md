# WORLDROOT r7 — deployment status and safe orchestration (18 November 2026)

## Authority and release boundary

This repository is **private**. The default `main` contains the Python control plane and synthetic tests; it is **not** automatically equivalent to the canonical story HEAD. The canonical HEAD is still the Google Doc whose approved header points to **D528, Livro V, Capítulo 15, Parte I**, with documented exceptions. The exact **D529 Part II** is preserved as **RASCUNHO** in `story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/`; it is **not** a promoted event ledger. Never rewrite its literal source to repair a summary.

The new workflow `.github/workflows/worldroot-orchestrator.yml` is a **read-only audit gate**. It runs Python regression tests and independently validates the complete episode archive, then explicitly reports that the Drive/HEAD were *not* modified. No secret, Google identity or `contents: write` permission is granted to this audit. It can be manually run from the GitHub Actions tab, and is also triggered by relevant `main` code changes.

## Canonical episode workflow — required before enabling publication

1. **Author message** (`Escolha 1..4` or `5: action`): a trusted interface records the actual authored choice, stable `episode_id`, and idempotency key. Do not infer a choice from model prose.
2. **Read** `story-archive` package (five sidecars + manifest; exactly five choices). Validate SHA-256 and current Drive HEAD. Reject reused IDs with conflicting bytes or stale HEAD.
3. **Review** facts/knowledge with literal anchors, day and minute, NPC access restrictions, narrator-only facts, character agency and event status. Human/editorial review remains necessary for ambiguous claims.
4. **Prepare** durable SQLite snapshot, outbox and recovery journal **outside the ephemeral runner**. A private object store or restricted Drive versioned snapshot may be used only after a genuine restore and replay test.
5. **Publish** immutable literal copy to restricted Drive, verify with new authenticated download, apply Base Viva and Atlas semantic deltas and read them back. Never confuse adding a chapter pointer with updating characters and relations.
6. **Advance HEAD last** with Google Docs revision compare-and-swap. Reconcile ambiguous timeouts against authenticated readback; preserve prior HEAD on failure.
7. **Record** the final receipt and recovered checkpoint durably. Only then may ChatGPT write the next installment, save its original prose/options, and mark that new installment a DRAFT until the following author choice.

Recommended operational dispatch: a trusted ChatGPT-side connector makes an explicit GitHub commit or `workflow_dispatch` API call; one GitHub Actions workflow orchestrates `needs:` jobs with `concurrency` per canon and `cancel-in-progress: false`. A GitHub `GITHUB_TOKEN` commit does **not** retrigger ordinary push workflows. The ChatGPT connector must be invoked for each choice; writing an instruction file to GitHub does not configure ChatGPT project behavior.

## Gates (fail closed)

- [x] Private GitHub repository confirmed; story archive isolated.
- [x] Episode D529 PII has literal, five-choice and manifest data in the archive branch.
- [x] Synthetic code CI green for the reviewed r7 branch; safe control-plane audit added.
- [ ] Restrict writes/merges on `main` and `story-archive` using GitHub rulesets/branch protection in Settings.
- [ ] Configure Google Cloud WIF/OIDC restricted to repository, approved ref/environment and service-account access to *specific* restricted Drive files.
- [ ] Implement a genuine ChatGPT → trusted choice action, and test it in a second chat.
- [ ] Restore a durable SQLite checkpoint and test full outbox crash recovery.
- [ ] Validate Base Viva, Atlas, Drive and Docs HEAD against real readbacks before semantic promotion.
- [ ] Review 11 proposed D529 event candidates and 6 individual knowledge relationships; they remain staging, not canonical.
- [ ] Run an end-to-end synthetic release with injected errors: duplicate choice, stale HEAD, failed Drive write, lost ACK, interrupted runner and retry.

**Do not enable automatic Drive HEAD publication until the above gates pass.** GitHub code release is permitted independently, because the installed control-plane audit is read-only.

## Official sources

- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
