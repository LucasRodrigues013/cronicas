# WORLDROOT R31 — Deep historical recovery (staged)

Status: experimental branch; no canon promotion or claim of full semantic reconciliation.

## Execution
Use a verified private story-archive checkout separate from the code checkout:
```sh
python -m unittest discover -s tests -v
python -m worldroot.deep_recovery --archive-root /private/story-archive --db /private/r31.sqlite build
python -m worldroot.deep_recovery --db /private/r31.sqlite search "Serís ciúmes" --entity miren --topic relationship --role Response
python -m worldroot.deep_recovery --archive-root /private/story-archive --db /private/r31.sqlite brief "cabelos postura" --entity miren --topic appearance
```
The derived index uses overlapping role-bounded windows, not canonical facts. It verifies the existing six-source manifest through R30's historical reader. Do not export private anchors in public CI logs.

## Acceptance gates (not yet achieved)
- Full source hash validation, coverage of all lines, no prompt/response mixing, reproducible readback.
- Expand aliases and entity resolution to all named people, places, powers, items; distinguish AERÚN the dragon and campus.
- Review candidate evidence against accepted narrative and author decisions. Separate observed features, historical clothing, current appearance, conflicting evidence, unknowns.
- Recover relationships including Serís/Miren/Lucas, emotional changes and reconciliation; avoid generic romance and invented attributes. Miren and Althea are exceptionally beautiful per current author direction.
- World visual bible: actual vs proposed layouts, flags, architecture, geography, cultural identity, references.
- Inventory event ledger: acquisition, creation, consumption, transfer, loss, location, container, quantities; no guessed current balances.
- Power chronology: D137 flow and reserve vs D210/D388 comparable operational capacity; never treat historical benchmarks as current caps.
- Post-D528: ingest accepted immutable episodes and separate pending drafts; recheck HEAD before writing.
- Evaluation: identical frozen questions for R30/R31, gold source spans, separate holdout questions, measure retrieval recall@k, precision@k, answer faithfulness, ambiguity handling, abstention, latency and narrative human blind preference. Report numerator/denominator and actual execution; no fabricated ratings.
- Keep R30 narrative controls, choice history, no nerf, author agency. Integrate into preflight only after review.
- No automatic merge, no canon changes, no automatic semantic certification. Candidate records live in recovery/r31-historical-candidates.json pending review.
