# WORLDROOT r7 — narrative regression gate (pre-continuation)

**Public technical documentation only.** No unpublished narrative, private character sheets, secret hypotheses, complete chapter content, or private SQLite archives are included here.

## Reproducible execution

```sh
python -m unittest discover -s tests -v
```

The regressions are synthetic and require no Google Drive credentials. Review the exact CI commit, not only an earlier successful run. Genuine Drive authentication, Docs revisions and client-host ChatGPT interactions require separate tests in trusted deployment environments.

## New checks

- Scene ID, place, chronological day/HHhMM, relative-to-head order and approved book transition.
- All five choices including fourth SPECIAL and fifth free-form path.
- `FIM DO LIVRO` cannot substitute for `FIM DA PARTE` in an open book.
- `SIMULADO` cannot silently become `NARRADO`, cannot claim an external save, and must not advance the canonical HEAD.
- Caller-supplied dicts with `file_id` and `verification` cannot display `DRIVE CONFERIDO` without a trusted runtime receipt verifier; this is not a new remote-authentication service.
- Per-character fact receipt can be queried at story minute precision; unknown same-day receipt times fail closed for minute-specific queries. Older day-only calls remain backward compatible.
- Configurable forbidden-universe and spoiler-marker lint for private QA packages; only explicitly structured claim annotations are checked for knowledge leakage.
- Unlabeled dialogue lines receive a **warning** to avoid hard-failing legitimate prose. Repeated stock expressions remain a warning.

## Limits of automation

**This module does not generate chapters, independently evaluate literary meaning, inspect unseen knowledge claims in arbitrary unannotated prose, infer travel routes, simulate all NPC agendas, or establish authenticity of a remote Drive file by itself.** The trusted external Drive adapter and editorial review remain separate gates.

The private project QA used three connected scenes (opening, development and close), two complementary stress samples (unrestricted creation and offstage perspective), synthetic negative mutations, and browser tests on desktop/mobile. The literary samples are not here because the GitHub repository is public. These samples were authored in a single assistant response workflow; they do **not** constitute independent multi-model or repeated-temperature sampling.

## Publication and privacy

- User's last narrated point remains D528 23h06, active Book V; D529 test scenes remain SIMULADO.
- No production auto-save / merge / wiki release is activated by running this command.
- Public repository must contain only code and synthetic fixtures. Place audit-only materials in restricted storage.
- Keep versioned schema migrations backward-compatible. Never correct the old literal text silently; record errata in a separate release artifact.
