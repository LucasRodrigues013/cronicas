> **ADENDO r14.** A recomendação r12 de auditoria de profundidade apenas consultiva foi substituída, quanto ao volume de novos episódios, por solicitação autoral expressa de ~10.000 palavras de prosa com piso de arquivamento 8.800 (P26). Autonomia, cronologia, foco e qualidade permanecem critérios superiores ao preenchimento artificial de palavras. Detalhes: `docs/longform-10k-context-recovery.md`.

# WORLDROOT r12 — reparo temporal e direção literária profunda

**Autorização autoral:** 18/11/2026, solicitação de corrigir o motor e aprofundar narrativa.  
**Escopo:** corrigir exclusivamente o motor e a projeção derivada (SQLite/CONTEXT); preservar textos integrais, SHA, escolhas, eventos imutáveis, HEAD, Livro V e Google Drive.  
**Referência literária aprovada:** Livro V C15 Parte II (`story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md`).  
**Nova diretriz viva:** `main/worldroot/editorial_policy.json` v3 (P20–P23).

## Diagnóstico

O fechamento anterior gravava o dia final do capítulo em `events.day`, ignorando `events[].occurred_day`. A validação de `npc_knowledge[].acquired_day` exigia o mesmo dia do checkpoint, mesmo se o capítulo atravessasse a meia-noite. Assim, um evento do Dia 530 era consultado como Dia 531.

Não é erro da prosa literal; é erro da **projeção consultável**. Exemplos já observados:
- C15 Parte IV (D529→D530): 1 evento no dia errado na projeção.
- C15 Parte V (D530→D531): 5 eventos e 4 registros de conhecimento com data posterior à cena original.
- C16 Parte I (D531→D532): 5 eventos D531 e 7 conhecimentos D531 com carimbo errado no review candidato; esse episódio continua **rascunho**, sem escolha nova registrada no momento da implementação.

Os IDs e citações exatas das correções de conhecimento precisam constar na fonte privada `story-archive/canon/temporal-reconciliation.json`, nunca neste repositório público de código.

## Correções de engenharia

- `temporal_projection.event_day` lê `occurred_day` quando presente; para versões legadas sem o campo, mantém o dia final do capítulo, sem inventar datas.
- `review_deltas` aceita fonte e conhecimento do dia anterior quando ancorados, proíbe ganho de conhecimento anterior ao evento, e compara relógios somente quando são do mesmo dia; não aplica a hora de final de capítulo sobre dia anterior.
- `apply_closure_db` grava dia do evento e data efetiva do conhecimento; correções de legados são explícitas, com personagem, evento, dia de origem, linha, âncora e motivo, nunca inferidas em massa.
- `verify_db` confere cada projeção frente ao journal: cabeça, integridade SQLite, chaves estrangeiras, dia de evento e dia de conhecimento. Se divergirem, sinaliza **restore required**; `restore` reconstrói projeções sem reescrever journal.
- `draft_inbox` retorna alerta contextual de foco/volume de cena, não bloqueia a criatividade por uma cota de palavras.

## Direção literária — técnica de cena, não técnica de planilha

Padrão: **Lucas como principal experiência vivida, não um supervisor recebendo cinco relatórios por capítulo.**

Cada cena importante pergunta: qual desejo ou pergunta Lucas persegue? Que resistência, surpresa, tensão ou reação humana surge? O que a experiência transforma? Onde se revela a emoção? O que passa a importar para a próxima escolha?

Usar a sequência narrativa **intenção → experiência/obstáculo → mudança → reação/decisão**, sem engessamento. Esse é um princípio recorrente de *scene/sequel* em ensino de escrita, adaptado a uma história interativa. Referências externas:
- [Estrutura da cena: objetivo, conflito, consequência e reação](https://www.faustica.com/en/writing-academy/craft-of-writing/writing-scenes.html)
- [Cena e sequela em ficção interativa](https://pvliesdonk.github.io/gamebook/content/articles/structure-pacing/scene-and-sequel-in-interactive-fiction.html)

Critérios em cada nova parte: Lucas mantém protagonismo sem monopolizar os outros; Miren, Rumo, Vértice, Kael, Lysa, antagonistas e outros continuam agentes; momentos emocionais importantes recebem tempo; mistérios avançam com uma **pista verificável ou pergunta nova para o leitor**, sem confundir o que o leitor vê com o que os personagens conhecem. Um mundo que cresce não exige cinco cortes de cena para dar notícias simultâneas.

Não impor mínimo de 10 mil palavras. Parte II ≈10.373 palavras totais (inclui interface), C16 Parte I ≈7.138. Volume sozinho não equivale a narrativa boa. `story_focus_audit.py` sinaliza compressão estrutural apenas como alerta.

## Protocolo de reparo (preserva o cânone)

1. Atualizar motor na `main` somente com regressão verde.
2. Fixar runner de reparo privado ao SHA imutável auditado da nova `main`.
3. Criar no GitHub privado o registro de correções, ancorado em eventos existentes e no texto, sem alterar `canon/episodes/` nem `canon/HEAD.json`.
4. Runner reconstruir `canon/state.sqlite` + `canon/CONTEXT.json` **a partir dos closures originais**, aplicar somente correções explícitas e executar `verify`, `PRAGMA integrity_check` e `foreign_key_check`.
5. Registrar SHA dos dois arquivos derivados e confirmar que HEAD/journal/arquivos narrativos têm os SHA anteriores. Em falha, rollback via Git sem promover novo capítulo.
6. Refixar workflows normais de fechamento e inbox ao SHA auditado do motor, mantendo nenhum avanço de capítulo sem escolha real do autor.

Projeto Drive ainda não tem credencial de serviço OIDC confiável e permanece sem sincronização: não declarar sucesso em Base Viva/Atlas ou Drive.

## Desempenho e prioridades seguintes

A pesquisa de engenharia recomenda **reconstruir read models a partir de um log imutável** (event sourcing), em vez de alterar eventos antigos; fontes:
- [Microsoft Learn — Event Sourcing Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)
- [SQLite — integrity_check e foreign_key_check](https://www.sqlite.org/pragma.html)

`story_focus_audit` e a comparação com regras editoriais atuam em tempo linear no texto atual; não consultam 618 mil linhas por episódio. O leitor recebe só os acontecimentos que importam, enquanto o futuro World Pulse pode manter propostas temporais privadas para NPCs sem antecipar cânone. Prioridades abertas: reconciliação sistemática de 62 cadastros antigos e 47 relações incertas, unificação dos índices D001–D528, serviços Google autenticados, painéis de retomada dinâmicos e world-state causal com fontes.

## Critérios de conclusão

- CI main e testes temporais sintéticos verde.
- Correção de projeção real com readback posterior a um runner comprovado.
- Todos os registros de Dia 529/530/531 confirmados; nova parte C16 PI permanece rascunho.
- Sem escolha, HEAD, narrativa literal, eventos originais ou Drive alterados.
- Política v3 aplicada aos próximos capítulos por recuperação contextual e QA consultivo, não por reescrever os anteriores.
