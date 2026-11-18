# WORLDROOT r8 — inventário de direção literária, sistemas e auditoria das 40 questões
**Referência:** 18/11/2026. Projeto isolado: CRÔNICAS DE UM NOVO MUNDO. Não importar outro universo.

## Fonte de verdade e atualização efetiva
- **HEAD operacional GitHub:** `story-archive/canon/HEAD.json`, Livro V C15 Parte I D528 23h06, `sequence=0`. A partir do r8, apenas eventos realmente fechados por escolha e workflow comprovados podem avançar o HEAD.
- **D529 Parte II:** pacote íntegro em `story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft` e revisão de 11 eventos + 6 registros de conhecimento. Status RASCUNHO; uma escolha do autor ainda não foi registrada.
- **Google Drive:** contém HEAD D528 homologado com ressalvas e extensos arquivos literais e estruturados, mas **não** é atualizado automaticamente no modo r8 GitHub-only.
- **Auditoria de 40 perguntas:** `story-archive/audit/qa40/worldroot-memory-2026-11-18.json`; Action `story-archive/.github/workflows/qa40-memory.yml`. Resultado obtido: 40/40 entradas com categorias de fonte e status formalmente válidas. O teste **não certifica interpretação literária** e fica HISTÓRICO quando o HEAD avançar.
- **Originais inspecionados:** `episodes/bootstrap/LV-C15-PI-D528/fonte_literal_drive_D528.txt` e `episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md`. Narrativa D529 não reescrita.

## CEO / Diretor-Geral / showrunner (editorial)
No design WORLDROOT v4.0, há exatamente **uma função CEO/Diretor-Geral literário (showrunner)**, `diretor_geral_showrunner`, que encaminha consultas e compõe uma voz narrativa. Não existe empresa, CEO real independente ou 37 agentes LLM que funcionem sozinhos. **O autor mantém a decisão final.** O diretório `worldroot/production_roles.py` agora implementa **cadastro e seleção consultiva**, sem criar agentes separados.

### Nove departamentos, trinta e sete especialidades
1. **Roteiro e Literatura (4):** `diretor_historia`, `diretor_aventura`, `diretor_interatividade`, `editor_literario`.
2. **Cânone e Continuidade (4):** `guardiao_canon`, `diretor_cronologia`, `supervisor_continuidade`, `diretor_conhecimento`.
3. **Personagens e Relações (4):** `diretor_personagens`, `diretor_vozes`, `diretor_vinculos`, `diretor_vidas_independentes`.
4. **Geografia e Memória (4):** `diretor_geografia`, `diretor_historiografia`, `diretor_cidades`, `diretor_exploracao`.
5. **Ecologia e Ambiente (4):** `diretor_clima`, `diretor_fauna`, `diretor_flora`, `diretor_fisica_natural`.
6. **Civilizações (4):** `diretor_politica`, `diretor_economia`, `diretor_cultura`, `diretor_genealogia`.
7. **Magia e Extraordinário (4):** `diretor_genese`, `diretor_sistemas_magia`, `diretor_tecnologia`, `diretor_misterios`.
8. **Cinema Sensorial (5):** `diretor_producao_visual`, `diretor_fotografia`, `diretor_figurino`, `diretor_som_musica`, `diretor_coreografia`.
9. **Engenharia e Publicação (4):** `diretor_causal`, `diretor_proveniencia`, `diretor_qa`, `diretor_publicacao`.

Quatro análises devem estar presentes no plano de revisão: `guardiao_canon`, `diretor_cronologia`, `diretor_conhecimento`, `diretor_qa`; até cinco especialistas contextuais podem ser consultados por `route(scene_tags)`. Trata-se de **regras de roteamento de pareceres**, não da execução de nove IAs diferentes. Fonte de nomenclatura: [Bíblia Técnica v4.0](https://docs.google.com/document/d/1WJmVr9NVIBBD161y-03Kb3_CdZ8NNJ8ewAKTY-eOOy8/edit).

## Sistemas técnicos efetivamente presentes na main
| Finalidade | Módulos | Escopo e ressalva |
|---|---|---|
| Cânone e eventos | `ledger.py`, `git_cycle.py` | Ledger, HEAD GitHub, fechamento e SQLite reproduzível; r8 inicia do D528, não representa todos os dias anteriores |
| Conhecimento temporal | `memory.py` | Grafo temporal com evidência e status; não presumir que a base histórica foi inteiramente migrada |
| Arquivos e episódios | `episode_pipeline.py`, `episode_handoff.py`, `draft_inbox.py` | Pacotes íntegros e ponte de rascunho/fechamento, verificações de hash, sem criação literária automática |
| Seleção autoral | `choice_intake.py`, `episode_cli.py` | Validação explícita da escolha; um campo JSON isolado não autentica identidade |
| Integridade e publicação privada | `private_github.py`, `archive_actions.py` | Arquivo isolado; espelho Google de r7 continua opcional e não ativado |
| Continuidade e estilo | `story_qa.py`, `narrative.py`, `semantic_gate.py` | Verificações sintéticas de tempo, cinco opções, evidência de fatos e falso salvamento; não certificam tudo semanticamente |
| Direção e fonte | `production_roles.py`, `provenance_audit.py` | Roteamento editorial declarativo, 40 perguntas e status; **implantados após auditoria** |
| Persistência e legado | `backup.py`, `legacy.py` | Backup/replay de SQLite e consulta legada, sem sincronização automática da história antiga |
| Integrações opcionais | `drive_bridge.py`, `sheets_index.py` | Requerem serviço Google autenticado; não demonstrar sync que não existe |
| Entrada e pacote | `cli.py`, `__init__.py` | CLI local e organização Python; não são agentes narrativos |

### Workflows GitHub
- `main/.github/workflows/tests.yml`: bateria sintética de código.
- `main/.github/workflows/worldroot-orchestrator.yml`: auditoria read-only do motor e do arquivo.
- `story-archive/.github/workflows/git-canon-cycle.yml`: bootstrap e fechamento após escolha real, com snapshot SQLite.
- `story-archive/.github/workflows/worldroot-draft-inbox.yml`: separa uma nova parte integral em arquivos imutáveis após chamada explícita do ChatGPT.
- `story-archive/.github/workflows/choice-intake-qa.yml`: validadores somente da escolha.
- `story-archive/.github/workflows/episode-archive-qa.yml`: verifica literal e manifesto.
- `story-archive/.github/workflows/worldroot-state-audit.yml`: teste de reconstrução de SQLite e D529.
- `story-archive/.github/workflows/qa40-memory.yml`: teste de 40 status/fontes, somente leitura.

## Inconsistências e riscos reais da revisão
1. **P0 — HEAD D528 ≠ draft D529.** Não promover aniversário ou memoria D529 sem escolha real. Fonte: GitHub HEAD + draft.
2. **P0 — Planejamento antigo ≠ tecnicidade recente.** Bíblia da Saga redigida em D519 dizia ARGOS sem voo livre; D528 confirma voos D520/D521/D524, incluindo tripulado. Um texto de planejamento desatualizado jamais suplanta a prosa narrada.
3. **P0 — Três camadas de conhecimento.** Leitor exclusivo D526 não transfere dados a Lucas; futuro Velkar/Ithran/emissários não constitui notícia recebida por protagonistas.
4. **P0 — Futuro é bloqueado.** Livro VI e Livro VII não começam por calendário; Velkar, identidades e capacidades propostas não viram cânone automaticamente.
5. **P0 — SQLite r8 seq0 não prova 528 dias individualmente indexados.** A história anterior é consultada nas fontes literais Drive/GitHub bootstrap e ainda precisa de migração/reconciliação auditada.
6. **P1 — AERÚN 72ha concluída ≠ campus plenamente operante.** MIREN DG, ASTRA vice, chefias vagas; Cidade Viva é intenção aprovada editorialmente, não programa municipal já votado.
7. **P1 — Prototipagem ≠ homologação.** ARGOS massa 39,86t última aferida, metas de 58t/8t/12 ocupantes ainda projetadas; suporte Brannik/Dorek em bancada; academia banco Beren/Tessa com trava pendente.
8. **P1 — Legião 300 pessoas ≠ Malha 3600 autômatos.** Os 3.600 não estão todos testados; Rumo/NÓX/SISTEMA não são confundidos.
9. **P1 — Misterios independentes.** TALIS, HZ1, Arquitetos, AETHRON/VELKAR, origem de Lucas e dragões não são resolvidos por coincidência ou imposição autoral.
10. **P1 — Papéis ≠ agentes.** 9 departamentos e 37 especialidades são conceitos de produção, com router consultivo implementado, não múltiplas execuções LLM automáticas.
11. **P1 — HEAD Drive e GitHub coexistem.** Ambos indicam D528 nesta auditoria; Drive não recebe os commits do r8 sem integração autenticada.
12. **P2 — Títulos provisórios.** A Bíblia da Saga contém título de trabalho para Livro V e nomes futuros; não renomear o livro narrado nem declarar títulos propostos canônicos sem decisão posterior.

Nenhum dos itens acima autoriza retcon ou avanço automático do enredo. Esta auditoria pode ensinar ao motor quais distinções verificar, mas novas mudanças editoriais e decisões autorais continuam sujeitas à aprovação do autor.
