# WORLDROOT R36 — Unified Living Engine
Status: PROPOSTA ARQUITETURAL, não implantação. Data: 2026-11-26.
Escopo exclusivo CRONICAS_DE_UM_NOVO_MUNDO. Não altera P01–P130, escolhas, prosa, identidade ou poderes.

## Decisão proposta
Monólito modular Python com autoridade canônica de escritor único, especialistas desacoplados por contratos internos, eventos imutáveis e projeções de leitura SQLite/FTS5/grafo/índice semântico. GitHub story-archive permanece fonte operacional exclusiva; main código; Drive legado. Não introduzir microserviços, bancos concorrentes ou Supabase nesta fase. Distribuir tarefas de leitura/revisão, nunca autoridade de escrita. Um único manifesto de release vincula commit do motor, esquemas, políticas, fonte, registro e compatibilidade; implantação distinta de merge.

## Baseline verificável
- main: 9b34bc491275028fe32fff018b405ab94dcc5c8a
- PR 74 aberta: d99f240f7e876be052094748879a31f4ccf471c4
- regressão sintética 45887348247 aprovada; auditoria privada corrigida 45887365418 aprovada; replay/restore 45887241154 aprovado (1256 registros, 0 eventos tipados).
- R32/R33 falhas push sem jobs, diagnóstico incompleto; não apagar regressões históricas.
- Livro I V1–V4 preservados; 307 alvos/236 contextos, 142 candidatos (2 linhas em comum), 14 identidades pendentes, 30 dimensões representadas não exaustivas. Ledger 9229 alvos/6368 tarefas globais. Nenhuma certificação independente simulada.
- HEAD D579 seq50, RESUME vigente; aprovação explícita D580 22h37 registrada author-approvals/LVI-C09-PII-D580-RATIFICATION-20261126.json, sem escolha de continuação. D580 tem 22 eventos e 22 registros de conhecimento revisados, fonte SHA256 fbbd336838b3f039196eaa13037e109c49dcf4bd596d30ca48cea8995b3c04b5. Ratificação atômica pendente, sem inventar opção. Não narrar D581.

## Contratos
1. Authority: journal, fontes literais, aprovação e escolha como comandos distintos; aprovação ratifica prosa e efeitos revisados, escolha posterior vinculada ao menu imutável; sem escolha fictícia. Idempotência, compare-and-swap HEAD, hashes, validação temporal, publicação atômica Git.
2. Registry: ID estável por entidade, aliases e ambiguidades, 30 dimensões, relações tipadas e evidência por campo; desconhecido explícito; distinguir fato, relato, hipótese, proposta, segredo, conhecimento de personagem e estado atual. Validade temporal e data de registro; sem retcon.
3. Memory: live_codex/natural_codex como adaptador integrado após gates; FTS5, busca semântica e grafo reutilizados; uma API de consulta, resultados ligados a fonte e escopo, fallback literal sem presumir identidade; projeções descartáveis, sem dupla escrita.
4. World: agenda/frentes/NPCs/recursos/viagem/causalidade; simulação produz candidatos, não acontecimentos canônicos automáticos; sem onisciência, sem nerf GÊNESE.
5. Narrative: recuperar contexto mínimo por cena, expandir sob demanda; planejamento e revisão R33–R35, cinco partes, qualidade literária, voz, autonomia, opções e escolha livre originais; preservar pisos R35 e exceções autorais.
6. Arquiteto: tarefas existentes agrupadas por fonte, revisão de papéis e atribuição, executor genuinamente separado local/privado quando disponível; sem credencial paga/remota não autorizada; não exigir certeza fictícia nem design retroativo.
7. Operations: entrada única status/prepare/review/ratify/choose/commit/recover/audit; adapters compatíveis aos CLIs legados; fila persistente, retomada por checkpoint; CI de código + privado + replay/restore + comparação de fontes e políticas. Sem log de prosa privada.

## Migração incremental
A. Congelar baseline, inventário de módulos, testes, versões, hashes, schemas e fluxos. Mapear P01–P130 e feedback a capacidades e testes; sem exclusões.
B. Corrigir gatilhos R32/R33 e reproduzir em snapshots históricos; validar PR74 e integrar em branch R36 sem merge prematuro. Criar mecanismo explícito de ratificação sem escolha, teste positivo D580 e negativos de duplicação/alteração/conflito, antes de avanço autorizado HEAD.
C. Criar contrato de eventos e identidade unificados sobre estruturas existentes; converter dados em cópia descartável; preservar proveniência e distinguir candidatos. Testar eventos tipados reais com D580 revisado, sem produzir fatos extras.
D. Migrar catálogo/ledger e filas V1–V4 + 9229 globais sem perda de IDs; homologar progressivamente livros, preservar gate do Livro I antes do II. Revisão semântica independente real, não rótulos. A narrativa atual pode ser preparada com evidências confirmadas; não certificar lacunas.
E. Orquestrador único, projeções reproduzíveis, integração por cena; executar comparação sombra com R35, regressões reais, backup/restore e rollbacks.
F. Release somente com zero regressões críticas, 100% de preservação de fontes/regras/IDs/menus, 100% de referências críticas, >=95% requisitos de memória conforme R33, comparação literária R35, eventos tipados verificados, testes privados aprovados e autorização de ativação. Medir p95, recuperação, duplicações, cobertura semântica real. Rollback de motor/projeções, nunca apagar evento aprovado.

## Referências técnicas
https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs
https://www.sqlite.org/whentouse.html
https://martinfowler.com/bliki/MonolithFirst.html
https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

Decisão de nome, arquitetura e implantação sujeita à aprovação do autor; este documento não ativa R36.
