# WORLDROOT R30 — Literary Experience

Incremento da R29, não gerador autônomo. P99–P105; nenhum episódio reescrito. O roteador REST valida Git SHA-1 e tamanho em Contents, tenta blob identificado quando formato/bytes falham; 404 continua ausência da rota, não prova de inexistência histórica. Em ChatGPT, usar manifesto e blob API verificado quando o conector retorna vazio. Nunca buscar dados privados por web pública.
 
O cache LRU limitado reutiliza normalização e conjunto de falantes por texto dentro do processo. SHA de cada fonte continua verificado a cada projeção; alterações de texto não reutilizam entrada antiga. Não é cache persistente entre processos nem prova de semântica.

`python -m worldroot.literary_experience --archive-root <checkout> registry` valida âncoras únicas em transcrições reconstruídas pelo manifesto, role Prompt/Response e SHA; episódios fechados via R29. Identidade e corpus são anotações editoriais, não inferência de estado presente. Campos ausentes desconhecidos; fontes conflitantes exigem revisão.
 
`... review --literal <arquivo>` retorna sinais sensoriais, emocionais, diálogo e linguagem editorial, sem impor metas. Intake integra dois recibos. Cartões causais opcionais: cause_anchor anterior ao effect_anchor ou prior_source fechado, consequence; não certificam causalidade semântica. Revisão de romance e epicidade exige leitura. A função choice_prompt constrói comando R30, choice_review sinaliza versão antiga/combinação especial; não reescreve controles existentes, não registra escolha, não altera gates. Narrador usa helper para novas escolhas; versões antigas são preservadas. 

A referência de regressão distingue elogio literal recuperado do autor de seleção editorial. Comparar o efeito da cena, não sua forma mecânica. Não exigir que cada cena contenha todos os sentidos ou emoções. Testes sintéticos + auditoria privada real separada. 

## Preparação e comparação antes da prosa

- `... brief --character miren --character lucas --scene observatorio --scene romance`: seleciona fontes verificadas e declara lacunas sem inventar estado atual.
- `... compare --literal episode.md --scene aeldric --scene romance`: compara sinais e critérios editoriais, não notas ou metas.
- Cartões opcionais de experiência (schema worldroot-r30-experience-review-v1, source_episode_id = HEAD vigente, cards), dimension em romance/sensory/emotion/voice/epic, campos EXPERIENCE_DIMENSIONS e draft_anchor literal. romance declara reciprocal_agency=true, epic artificial_weakening=false; prior_source opcional é validada. Integra recibo de intake; ausência fica explícita, não equivale a aprovação. As decisões literárias continuam humanas/editoriais.
