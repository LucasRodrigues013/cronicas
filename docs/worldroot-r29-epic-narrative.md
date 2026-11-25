# WORLDROOT R29 — Narrativa épica

Complementa R28 e os diretores R24–R27. Política v16 P89–P98 aprovada. Os dez diretores são campos de revisão opcional, não dez motores geradores. Nenhum deles é árbitro de qualidade artística.

## Uso

- `python -m worldroot.epic_narrative --archive-root /path/story-archive brief`: carrega plano privado R29 e projeção R28, lista promessas associadas aos registros revisados, referências, sementes condicionais, elenco que merece recuperação e ativos já existentes.
- `... review --literal episode.md --cards review.json`: sinais e revisão de cartões opcionais; o arquivo de cartões usa schema `worldroot-r29-craft-review-v1`, source_episode_id = HEAD vivo, cards = lista de objetos com director, campos específicos definidos em DIRECTORS, draft_anchor literal dentro da narrativa, prior_source opcional {episode,anchor}. Promise/payoff e emotional legacy exigem fonte fechada anterior; todos os anchors prévios são verificados por SHA e journal dentro do HEAD. A origem anterior não prova conhecimento do personagem.
- Flags editoriais declaradas: preserve_full_authority, preserve_agency, no_predetermined_outcomes, no_retcon, no_copied_expression. Campos extras para poder (weakens_genese=false), antagonista (omniscient=false), arco (outcome_open=true, fixed_deadline=null), originalidade (borrowed_protected_expression=false). Validação é consultiva e não certificação semântica. Sem cartas, resultado NOT_SUPPLIED, não falha.
- Intake integra R29 nos dois recibos, sem modificar arquivos imutáveis, escolhas, HEAD, release gates ou schema anterior. Não existe comparação automática com obras externas nem certificação de ausência de cópia; Originality Guard orienta revisão humana.
- O plano privado mantém quinze sementes e macroarcos abertos; nenhuma é cronograma ou ordem de gerar episódio. A recuperação dinâmica depende das fontes R28 e não substitui a validação integral do journal.
- Testes: `python -m unittest discover -s tests -p 'test_epic_narrative.py'`, além da suíte existente.

## Contrato criativo

Promessa/progresso/recompensa; arcos pessoais; aventura e cultura com identidade; momentos épicos com consequência; aplicação de poderes sem nerf; antagonistas com vida própria; legado emocional; grandes arcos sem prazos artificiais; originalidade. Preservar Lucas carismático, Miren independente, NÓX/Rumo/Sistema distintos, Legião livre, Três Arcos civilização, vitória permanente, derrota consequente, cinco escolhas e mundo independente. Referências de literatura são técnicas abstratas; não são personagens ou regras do universo.
