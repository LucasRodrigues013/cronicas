> **ADENDO R16 (18/11/2026):** `longform_floor` não bloqueia mais a entrega porque ocasionava incentivo à inflação repetitiva. `longform_measured` registra contagem, e a meta ~10 mil é conselho editorial. Todos os outros itens de liberação — manifesto, SHA, opção/fechamento autorizados, fonte literal, sidecars, UX e readback — continuam obrigatórios. A história jamais é certificada semanticamente por uma fórmula. Ver `docs/bookv-bookvi-semantic-transition-r16.md`. O texto antigo abaixo conserva as regras históricas do r14.1 e não prevalece no tema da extensão.

# WORLDROOT r14.1 — Entrega travada por evidência, sem episódios-fantasma

**Aprovação autoral: 18/11/2026.** Correção após a Parte IV do Livro V, Cap. 16, ter sido apresentada no chat sem existir no GitHub e sem recibo longform r14. O erro foi operacional na etapa ChatGPT → inbox → Action → readback, não uma falha do fechamento da escolha da Parte III.

## Contrato obrigatório para uma nova parte

**ANTES de publicar como parte COMPLETA e antes de exibir as cinco escolhas:**

1. Reabrir o HEAD operacional do story-archive, CONTEXT, escolha real, último rascunho literal, metadados, eventos, conhecimento e SHA. Não confundir HEAD fechado com draft novo.
2. Planejar um eixo dramático vivido e até um secundário, alinhados à escolha; preservar autonomia, consentimento, humor, GÊNESE plena e cenas completas. Não trocar cenas por atas.
3. Produzir em uma ou várias respostas conforme necessário, **na mesma Parte**. Na saída intermediária declarar **EM PRODUÇÃO — SEM ESCOLHAS**, sem encerrar ou antecipar próximo menu.
4. Para longform repartido, gravar cada trecho real em story-archive/production/EPISODE/segments/01.md etc. (2–6 partes), SHA-256 imutável, verificável por worldroot/longform_segments.py; segmento não é cânone nem capítulo completo.
5. Montar inbox/EPISODE.json com prose como prefixo literal de full_text, metadados RASCUNHO, cinco escolhas, fontes literais de eventos e conhecimento temporal; sem inventar anexos nem SHA.
6. A Action do GitHub, com código da main fixado em commit imutável, deve executar o arquivador e passar piso de **8.800 palavras narrativas**, guards de apresentação e evidência semântica.
7. **Após arquivamento e readback**, executar python -m worldroot.delivery_gate --archive-root ARQUIVO --episode-id EPISODIO. Exigir release_allowed=true, status ARCHIVED_DRAFT_VERIFIED_FOR_READER, story_sha256 real e campos de prova. Conferir a Action, manifesto, história e hashes do GitHub antes de declarar ARQUIVADO.
8. Só apresentar parte e cinco opções assegurando que o texto exibido corresponde ao arquivado. Sem prova, não declarar entrega certificada.

**Meta:** 9.400–11.000 palavras de prosa de cena, referência 10.000. Piso 8.800 é mínimo técnico e não licença para achatar o texto. Contar apenas cenas, não calendário, checkpoint e controles.

## Estados

- EM_PRODUCAO: planejamento ou segmentos; nenhum capítulo novo no cânone; nenhuma escolha nova.
- RASCUNHO_ARQUIVADO: texto imutável, sidecars e SHA existem; ainda não fechado.
- BLOQUEADO: falta conteúdo, profundidade, UX, evidência, cronologia, inbox, sucesso da Action ou readback; não apresentar como concluído.
- FECHADO_CANONICO: só após escolha posterior REAL do autor e novo HEAD confirmado.

**Limite:** não existe hook universal para interceptar a resposta final do ChatGPT. O guard GitHub não impede texto enviado sem conector; barreira técnica e ordem obrigatória precisam coexistir.

## Correção narrativa autorizada — ARGOS

- A Parte IV anteriormente mostrada no chat sem arquivar é tentativa NÃO canônica. Não transferir acontecimentos de voo 005, 1.034 km/h, ocupantes, destinos ou descobertas automaticamente.
- ARGOS é aeronave arcana **única**, não conversão em jato, Harrier, turbojato ou modelo militar da Terra.
- Explorar de maneira criativa o **Coração de Voo**, a **Matriz de Compensação** e o fluxo energético/controle próprios, com GÊNESE plena quando relevante, sem declarar números de desempenho não medidos.
- Lucas tem a intuição; **não precisa anunciar o espetáculo antes**. Surpresa deve nascer do movimento, dos sentidos, da reação espontânea de Naira, Rumo, Miren, Brannik, observadores e instrumentos.
- Não bloquear arbitrariamente o poder de Lucas nem declarar certificação instantânea. Naira conserva autoridade operacional; equipe e AERÚN são autônomas.
- Três horizontes distintos: ruínas dos Arquitetos, Planalto das Pedras Cantantes (encontro com Saira Venn e Jardim Errante D208), e corredores históricos de Seral/Calderva. Localização atual de Saira, distâncias e licenças não conhecidas.
- A escolha livre opção 5 da Parte III permanece válida. Reescrever Parte IV **desde D534 18h11**, em cenas vividas; convidar Miren sem obrigar, coordenar voluntários, vídeo e mapa, depois descoberta real de ARGOS sem salto automático a D537.

## Regressão

- tests/test_delivery_gate.py: faltando arquivo, prosa curta, SHA corrompido, inbox ausente.
- worldroot/delivery_gate.py: readback, SHA, longform, UX e eventos.
- worldroot/draft_inbox.py: métricas retornadas na primeira execução e em idempotência.
- CI Safe public-code tests: python -m unittest discover -s tests -v.

Este contrato não prova que a Parte IV foi escrita ou arquivada.