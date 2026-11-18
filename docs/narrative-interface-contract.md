> **ADENDO EDITORIAL R16:** Design rico é necessário mas não suficiente; não usar blocos, painéis ou diálogos para repetir descobertas semânticas já encerradas. Antes do Livro VI aplicar o baseline privado de continuidade e separar editor/narrador/consciência dos personagens; a palavra 'fim do livro' é metadado, não saber de Lucas.

# Narrative interface contract — WORLDROOT

**Status:** technical design standard on the draft development branch; this file contains **no story content**. It governs rendering and user-facing receipts, not canon or world simulation.

## Visual hierarchy
1. Small centered eyebrow: project and runtime.
2. Book title, chapter/part and cinematic scene title, visually distinct. A short italic epigraph is optional, never mandatory.
3. A compact opening scene plate with **verified** story date, local time and place. Show only what is safe for the chosen point of view.
4. Full literary scene with scene breaks and natural paragraph variation; dialogue consistently identified by character name and em dash. Do not present an operations report as literary prose.
5. End-of-part scene conclusion, then a compact player-visible state panel, then interactive choices.
6. Save/audit receipt in a separate secondary panel only **if** external persistence was actually verified.

## State labels: no invented conclusions
- If a part closes but a chapter/book is still open, display `FIM DA PARTE`, never `FIM DO LIVRO`.
- `FIM DO LIVRO` is legal **only** after an explicitly author-approved and narrated book-close event that has been committed through the release gate.
- The interface must not announce the next chapter/part as narrated before the author selects it.
- Story-facing checkpoints and editor-only operational data must not be merged.

## Choice contract
- Four numbered options, the fourth clearly identified as **ESPECIAL**; fifth free-form action.
- Numbered alternatives describe a meaningful path, upside and honest uncertainty without forcing failure or creating an unfair penalty for option 4.
- Free-form command always accepts user decisions outside the presented alternatives.
- Controls must submit a real message or callback; do not render decorative `Escolher` buttons. When interactivity is unavailable, present options as plain text.
- Never make the user choose twice after the selection is already available.

## Character and spoiler boundaries
- Distinguish `AUTHOR_EDITORIAL`, `READER_SEEN`, `CHARACTER_KNOWS`, `PUBLIC_FACT`, `UNKNOWN`, `PLANNED`.
- A future surprise may be visible to author/editors but must not accidentally enter protagonist thoughts, a public encyclopedia or a choice label.
- Describe offstage information only when the point of view and narrative reveal permit it; communication between locations must be logged with a route and plausible delivery time.
- Do not export hidden plot or character confidences into public GitHub, HTML, JSON, previews or client bundles.

## Style and rhythm
- Third-person immersive narrative, dialogue, humor, emotional specificity, autonomous characters and occasional purposeful silence.
- Avoid repetitive filler openings/closings or one-sentence lines that turn every gesture into a separate paragraph.
- Epic powers retain established capability; no arbitrary cooldown, disabling or surprise resource cost.
- Events have visible consequences; world responses obey visibility, travel time, institutional interests and reader-vs-character knowledge.
- Keep technical metrics/checkpoint outside the story, but searchable separately.

## Persistence truth table
| Runtime proof | Visible receipt |
| --- | --- |
| Rendered prose, no save attempt | `AINDA NÃO SALVO EXTERNAMENTE` |
| Local prepared/validated/written only | `SALVAMENTO EXTERNO PENDENTE` |
| Remote file uploaded, no downloaded hash check | `UPLOAD NÃO CONFERIDO` |
| Downloaded identical original bytes from authenticated Drive adapter | `DRIVE CONFERIDO` with grounded URL, SHA-256 and timestamp |
| Canon head published with explicit approval and verified dependency updates | `CÂNONE PUBLICADO` with validated release |
| One dependency update failed | `SINCRONIZAÇÃO PARCIAL`, leave prior HEAD official and provide recovery ID |

An arbitrary local data field called `receipt` is not evidence of authenticated Drive readback.

## Test matrix (future implementation)
- Correct chapter/part/book end labels.
- Five real choices, accessible keyboard focus and fully functional free input.
- Same part rendered on mobile and desktop without clipping.
- No spoilers in public DOM/data bundles.
- Different protagonist knowledge from reader knowledge in the same timeline.
- No save badge without connector readback.
- Preserve exact chapter prose in source; rendering must never silently rewrite it.
