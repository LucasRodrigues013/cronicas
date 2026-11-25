# WORLDROOT R32 — operational and literary contract (staged)

Scope: incremental extension of R31, P01–P109 unchanged. HEAD D573 / sequence 44 remains untouched. D574 C08 PI remains an immutable pending draft. Do not merge until real retrieval acceptance, integration tests and conflict reconciliation with main.

## Local private workflow
1. Verify live HEAD/RESUME, current choice, pending draft, historical manifest. R31 uses six TXT and 11 parts. Closed episode projection is separate, never ingest a pending draft as canon.
2. Build source-verified SQLite outside archive. Run audit/run_r32.py with R31_DB_PATH pointing to the fresh projection.
3. Graph data: verified canonical closure references, explicit character knowledge, R28 assets/plots, R29 plan as direction, R30 observations, R31/R32 candidate sources. Historical candidates remain candidates; no inferred ownership, current location, causal fact, relationship or quantity. Unresolved speaker labels are not automatically new characters. Graph edges NEXT_CLOSED_EPISODE are chronological only; CAUSAL_CANDIDATE requires review.
4. Vector projection: LSA using TF-IDF plus truncated SVD, 96 dimensions; local fit, no story sent to third-party inference, source DB and vector arrays hashed, no pickle deserialization. Optional E5 backend requires pinned model commit and separate dependency installation/evaluation; not yet homologated. Keep lexical routes as fallback.
5. Prepare each creation:
   `python -m worldroot.memory_continuity --archive-root archive prepare --db /private/r31.sqlite --vector-folder /private/r32-lsa --graph-db /private/r32-graph.sqlite --requirements /private/requirements.json`
   Declare all material requirements, partition across scenes, assess applicability for all ten domains, review current-state conflicts and exact source anchors. Do not reduce denominator by removing failed facts.
6. New opt-in draft: metadata.worldroot_revision=32 and r32_review (HEAD, prose SHA-256, requirements, domain_review, scene_requirements, reviewed evidence, arc_packet, editorial_parity_reviewed). Existing R25/R26 controls remain. release_review requires 95% reviewed evidence and 100% critical, exact visible equal-choice rendering, title/number/special/free consistency. This gate checks structure and literal proof; semantic accuracy is reviewed separately, not guaranteed by a hash.
7. Four substantial routes (one main, three secondary) with equally meaningful risks/rewards. Option 4 remains singular and explicitly named ESPECIAL, not privileged by styling or rewards. Preserve free action 5 and old immutable choices. Render via experience_quality.render_choices and place body declaration at the start. Main/secondary classification is private planning, not an incentive to choose a specific number.
8. Save review sidecar only when a new R32 draft is actually validated. Never auto-close, promote or choose for the author.

## Evaluation and thresholds
- Frozen 100 historical development queries and 21 additional references; compare at matched candidate budgets. Expanded candidate retrieval is not top-k quality or 95% semantic recall. Add independently authored questions with multiple acceptable supporting passages and atomic claim gold labels, including temporal contradiction, unknown fact and author vs narrated role.
- Real D574 retrospective creation replay uses 20 declared contextual references from D573 (all recovered in an earlier execution). This is lexical span retrieval and reviewed-anchor mechanics, not prospective independent literary/semantic certification.
- Require 95% recall of material evidence on independent multi-fact creations, all critical facts, source/role checks, no invented attributes, no regressions and no release if criteria fail.
- 11 editorial dimensions: continuity, causality, voice, appearance, senses, relationships, emotion, epic, world experience, visual design, choice parity. Blind human preference not simulated by a heuristic. Automated signals are advisory.

## Literary A/B pilot (editorial demonstration, not canon)
Source: story-archive/episodes/LVI-C08-PI-D574-AUTHOR-SOURCE/draft/narrativa_integral.md, lines 22–72. Original scene establishes cold dawn, flags, run, breakfast, notes, silver locomotive, Brannik's suggested name, NÓX notice, municipal corridor, AERÚN session, station plan, diplomatic objective, kiss and Mustang. Preserve all these if adapting full scene. Compare the opening only, not the complete episode.

Candidate opening (B), preserving the same moment:
> O frio da manhã ainda acompanhava Lucas quando ele deixou o terraço. Lá embaixo, Três Arcos despertava devagar; o primeiro sol dourava as bandeiras que se moviam sobre os telhados. A cidade era bela antes mesmo de perceber que estava sendo observada.
>
> Miren estava à mesa do salão suspenso, tão concentrada nas anotações que não ouviu o marido aproximar-se. Lucas deixou uma pequena locomotiva de prata diante de sua xícara.
>
> **MIREN —** Espero que ela não tenha vindo solicitar uma audiência.
>
> **LUCAS —** Ela veio pedir um nome.
>
> **MIREN —** O trem já tem nome.
>
> **LUCAS —** O projeto tem nome! O trem precisa de identidade. Personalidade. Elegância. Brannik quer chamar a primeira composição de Martelo Voador.
>
> Miren ficou em silêncio, olhando a pequena locomotiva.
>
> **MIREN —** Por favor, não deixe.
>
> Lucas riu.

Assistant editorial comparison (not human blind grading): A is direct, clear and already has strong humor and a shared domestic ritual. B foregrounds the city and lets the visual detail precede the same joke; adds no new geopolitical event or physical trait. B does not establish a new factual relationship or capability. The difference is modest; do not pad all scenes. The subsequent lines 48–72 must remain intact in a full adaptation. Emotion, epic scale, and romantic progression are not meaningfully testable from this short excerpt. No automatic grade.

## Pending release
- Confirm actual full R32 vector persistence and retrieval benchmarks; independent threshold remains a release blocker.
- Complete semantic reconciliation of all character dossiers and unknown attributes, historic item acquisitions/transfers/losses and current inventory (do not infer missing quantities).
- Complete GÊNESE progression beyond recovered benchmarks and power usage candidates.
- Expand causal edges only from explicit reviewed evidence; R29 plan remains conditional.
- Human comparative review of complete parts and actual rendered chat; no literary quality claim based only on structure.
- Check main divergence and merge only after acceptance. Preserve P01–P109, R30 and old archives.
