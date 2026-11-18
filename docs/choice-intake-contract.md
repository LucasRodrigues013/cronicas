# WORLDROOT — author choice intake (read-only stage)

This document describes **actual implemented validation**, not automatic canon promotion.

## Input

When the reader writes `Opção 4`, an **explicit ChatGPT GitHub connector operation** (or a separately trusted app) may create exactly one UTF-8 file on the private `story-archive` branch:

`choices/LV-C15-PII-D529-AUTHOR-SOURCE/option-4.json`

```json
{
  "schema": "worldroot-author-choice-v1",
  "episode_id": "LV-C15-PII-D529-AUTHOR-SOURCE",
  "option": 4,
  "free_text": "",
  "author_source": "USER_MESSAGE"
}
```

Do **not** create this file until the author actually chooses that option. A prior assistant suggestion or proposed branch is NOT user authorization. Free action is `option-5.json` with a non-empty `free_text`. For other options, `free_text` may contain additional *author-written* instructions; the ingest limit is 2048 characters. Never include private GitHub tokens in the file.

The read-only validator `python -m worldroot.choice_intake --archive-root archive` checks:
- exactly one selection per episode;
- ID / filename / number / source envelope consistency;
- corresponding private immutable draft and its SHA256-verified `opcoes.json`;
- five options, fourth special and fifth free;
- refusal of missing, altered, ambiguous or duplicate inputs.

A green check **does not authenticate the author**, merely checks the submitted envelope. The caller must trust and preserve provenance of the live user message. The canonical closer still requires Drive HEAD CAS, event/character knowledge review, durable SQLite state, Drive/Base/Atlas authenticated readbacks and crash recovery.

## GitHub Action

The separate `story-archive` workflow `.github/workflows/choice-intake-qa.yml` can run on actual `choices/*/option-*.json` commits. It checks out the motor from the reviewed private `main` branch and inspects archive data without Drive credentials or write permission. A green check means `CHOICE_SHAPE_VALIDATED`, **never** `FECHADO`.

## Safety and recoverability

Do not overwrite an already issued choice path; create operations should fail rather than modify it. If a different choice appears for the same episode, validation blocks intake until a trusted explicit human reconciliation. Only a real-world author decision should resolve the conflict. Do not give this workflow OIDC credentials or a `contents: write` token: use a different, reviewed canonical publication pipeline later.

**The ChatGPT-to-GitHub connector has no guaranteed automatic end-of-message trigger.** The assistant must explicitly call GitHub when the author makes the selection; saving this contract in `main` does not alter ChatGPT project settings.
