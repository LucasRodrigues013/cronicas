# WORLDROOT R36 — Evolution 7 / P0–P1 isolated experiment

Status: production HOLD. This is an additive engineering candidate, not a version promotion, canon change, or independent certification.

## P0 pinned baseline
Champion authorized engine: 9b34bc491275028fe32fff018b405ab94dcc5c8a.
Challenger parent: 46c40e18d3e0f4fbcafc025ae9d08b91ca6e6417 (SQLite compatibility fix).
Historical native validation: GitHub run 45919601447, 706 existing unittest tests in 11.641 seconds, SQLite 3.45.1, successful. This is historical evidence, not an execution of this change or narrative quality benchmark. Python >=3.10, no core runtime dependencies (pyproject). B008 incorporation was scoped; Stage C independent review and production hold remain. Canon/RESUME/archive unchanged by this experiment. Do not use public CI for historical source or reserved gold data. This repository's metadata currently says public: only generic code and synthetic fixtures in this PR. No change to visibility.

## Cross-check and design
- Reuse semantic_queue seals and semantic_local offline executor for historical attribution. Do not duplicate SQLite or memory graph. Existing R36 temporal/contextual/reconciliation modules retain ownership.
- Existing R32/R33/R34/R35 preparation/release and story_qa gates remain mandatory; no integration or alteration here. Add an experimental evaluation receipt exchange only. No receipt self-certifies execution or independence.
- Anthropic agent evals: https://www.anthropic.com/research/demystifying-evals-for-ai-agents (combine deterministic, model and human evaluation).
- MT-Bench: https://arxiv.org/abs/2306.05685 (position and verbosity bias; reverse blind pairs, separate review context).
- LongMemEval: https://proceedings.iclr.cc/paper_files/paper/2025/hash/d813d324dbf0598bbdc9c8e79740ed01-Abstract-Conference.html (temporal updates, abstention).
- Context engineering: https://www.anthropic.com/research/effective-context-engineering-for-ai-agents (selective retrieval).
- Re3: https://aclanthology.org/2022.emnlp-main.296/ (scene context and revision, no formulaic quotas).

## Acceptance boundaries
Twelve rubric identifiers and baseline criteria are initial contracts, not calibrated graders. Receipt checks are syntactic and provenance-binding, not semantic inference or authentication. Source digests use semantic_queue.seal on JSON strings, not historical raw-file SHA; adapters must verify literal raw source independently before creating packets. Blind pair mapping stays outside reviewer context; candidate text may itself reveal identity; session IDs alone prove nothing. No reserved answers in packets. Independent executor attestation, calibration against human judgments, bias controls beyond position, and source authorization are outstanding. No production wiring yet. All synthetic tests must pass and existing tests remain intact.

## Next dependencies
P0: complete Stage C independent semantic validation and existing historical recovery sequence; confirm author authority, private storage and native replay. P1: provision two distinct pinned offline models per existing semantic_local contract, real separate execution and trusted audit receipts; calibrate rubric and human reviews. P2: inventory existing 40-part regression and source-verified test cases; partition by episode/entity/family; protect held-out gold outside public repository. P3: measure actual latency/context/retrieval on same workload before optimization. P4–P7: gated comparisons, feedback proposals, telemetry and longitudinal acceptance. No release until author approval and all ten gates. Rollback: abandon isolated branch; no production refs modified.
