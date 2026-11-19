> **ATUALIZAÇÃO DO MOTOR EDITORIAL — v14, 19/11/2026:** `main/worldroot/editorial_policy.json` P01–P81 é a fonte das preferências aprovadas. `main/worldroot/story_dynamics.py` inclui dez módulos consultivos e preflight de cinco partes, integrado ao recibo de `draft_inbox`. A base de pré-produção **aprovada como ideias, não como cenas** está em `planning/book-vi/world-pulse-and-five-arcs-v1.json`. Em próximos capítulos, explorar espionagem, confrontos, Tharvek/Elyrien, GÊNESE e reações externas com escala e causalidade; culminar quinta Parte com clímax ou transformação significativa. O estado canônico continua no HEAD vivo; Cap.1 Parte IV D540 já é draft e não deve ser narrada novamente nem promovida por esta atualização. Google Drive continua LEGADO.

# WORLDROOT · OPERAÇÃO GITHUB-ONLY | Crônicas de um Novo Mundo

> **VIGENTE — CICLOS 1–3 (19/11/2026):** em cada retomada, consultar primeiro `canon/HEAD.json` e `ops/RESUME.json` **vivos**, depois a fonte literal do último episódio, o feedback de Lucas e `docs/WORLDROOT-THREE-CYCLES-v1.md`. O snapshot `ops/WORLDROOT-GITHUB-ONLY-STATE-20261119.json` é APENAS histórico datado. O HEAD é Livro VI C01 Parte III D539, sequência 12; Parte IV D540 foi arquivada como rascunho íntegro, sem nova escolha de fechamento. Memória: `memory/deltas/` e `memory/canon/`; Livro V C16 tem selo `chapters/LIVRO-V-C16/CANONICAL_SEAL.json`. Nunca inferir fatos ou escolhas a partir de um README antigo.

**Autor — decisão de infraestrutura de 19/11/2026:** GitHub privado é a única fonte operacional para motor, história, cronologia, eventos, conhecimento, fichas, escolhas, auditoria e backup dos capítulos. **Google Drive passa a LEGADO:** links e documentos antigos continuam como referência histórica, mas o motor NÃO exige nem executa novas sincronizações para Drive. Nenhum documento existente do Drive é apagado.

## Onde está cada componente

| Fonte | Ref | Conteúdo |
|---|---|---|
| Motor e contratos de qualidade | `main/worldroot/*` | Python, regras P01–P81 v14, UX01–UX12, testes, templates |
| História literal e provas | `story-archive/episodes/*/draft/*` | Texto completo, opções, eventos, metadados, fontes e SHA |
| Contexto e cânone | `story-archive/canon/HEAD.json`, `canon/CONTEXT.json`, `canon/episodes/*`, `canon/state.sqlite` | HEAD único, journal e projeção reconstituível |
| Escolhas autorais | `story-archive/choices/*` | A escolha real arquivada, não uma inferência do assistente |
| Históricos anteriores | `story-archive/history/sources/*`, `history/LITERAL_INDEX.sqlite` | Fontes dos intervalos nominais D001–D528 e busca; fonte literal não é automaticamente cânone |
| Export literal recente | `story-archive/history/source_exports/ChatGPT-CRONICAS_DE_UM_NOVO_MUNDO_9-20261119-1028.txt` | Fonte apresentada pelo usuário das Partes I–III do Livro VI; renderizada TXT, não DIL original |
| Planejamento v18 | `story-archive/planning/book-vi/*`, `author-approvals/*` | Livro VI AS COROAS PARTIDAS, grande trama e decisões ratificadas |
| Auditoria semântica | `story-archive/editorial/*`, `episodes/*/review/*` | Rejeições, continuidade e eventos literais, incluindo retenção Caedren D539 |
| Capítulos em 5 partes | `story-archive/chapters/<LIVRO-CXX>/*` | Quando as cinco partes estiverem elegíveis, cópia integral, manifesto e ZIP comprometidos diretamente no Git |
| Provas de entrega | `story-archive/delivery/reader_receipts/*` e `delivery/github_chapters/*` | SHA para recuperar texto do GitHub; recibo local de pacote NÃO é liberação canônica |

## Fluxo obrigatório daqui em diante

1. **Antes de produzir:** ler HEAD real, último cânone literal, novo draft, escolhas, fontes de personagens e planejamento. O último texto narrado e HEAD canônico é **D539 C01 Parte III**, próximo **D540 C01 Parte IV**. A ratificação autoral extraordinária das três partes anteriores foi concluída em 19/11/2026.
2. **Criar prosa:** Lucas expressivo, GÊNESE plena sem nerf, Miren/Astra autônomas, Sistema/NÓX presentes, romance e humor, ação de alta fantasia, antagonistas e povos autônomos. Manter cenas completas e tempo vivo; a meta de palavras serve à literatura, não a relatórios.
3. **Pré-entrega:** a resposta preparada deve ser gravada **literalmente** em `story-archive/inbox/<id>.json` mediante **chamada real à conexão GitHub**. A Action `worldroot-draft-inbox.yml` cria seis artefatos imutáveis e revisões, executa gate, depois publica `delivery/reader_receipts/<id>.json`.
4. **Leitura para o usuário:** **somente depois da Action concluir**, o assistente reabre o recibo e `narrativa_integral.md`, confere hash, reconstrói a apresentação aprovada (sem fingir que export TXT é código DIL), e apresenta escolhas funcionais. GitHub Actions não injeta mensagens espontâneas em uma conversa ChatGPT.
5. **Escolha seguinte:** uma escolha **real** fecha apenas a Parte anterior selecionada e validada, sequencialmente contra HEAD, na Action `git-canon-cycle.yml`. Nenhum comentário de auditoria vira seleção, nenhuma geração promove novo texto.
6. **Capítulo completo:** quando a quinta Parte chega como draft e as I–IV estão efetivamente fechadas, o **mesmo workflow de inbox** executa `chapter-github-publish`, validando as cinco partes, hashes, exclusão de rejeições e flags de continuidade. Comita cópia integral, JSON manifesto, ZIP de sidecars/provas e recibo, diretamente em `story-archive/chapters/*` e `delivery/github_chapters/*`. **Nenhum Drive token, conta ou pasta é usado.**
7. **Recuperação em nova conversa:** priorizar `ops/WORLDROOT-GITHUB-ONLY-STATE-20261119.json` como fotografia inicial **datada**, mas consultar o `canon/HEAD.json` vivo e o draft mais recente; não congelar a história nesse snapshot. Ler primeiro as regras vigentes na `main`.

## D538–D539 — conferência do arquivo atual

| Parte | Dia | SHA-256 | Situação |
|---|---:|---|---|
| Livro VI C01 Parte I (R2, reautorizada) | 538 | `fd6aa23fa1ea5e929d81e0aaebc7776ca30a697120f20d310f9b3fd1f25f98ee` | **CANÔNICO** (sequência 10–12; fonte literal inalterada) |
| Livro VI C01 Parte II | 538 | `69be6e8eb86e68718c3eccdb823456a0e913816f94e1ca607ff44dc37d9eb740` | **CANÔNICO** (sequência 10–12; fonte literal inalterada) |
| Livro VI C01 Parte III | 539 | `74bb2ae185f21262a292d1a48e2c75e703d8ee92659f43f97c39d0174c2fd2e7` | **CANÔNICO por ratificação literal** (sequência 12); flag histórica Caedren e afiliação/rota NÃO comprovadas |

Os textos têm **81.190 / 93.587 / 78.749 bytes UTF-8**, respectivamente, e 5 alternativas cada. Verificar por `python tools/verify_lvi_original.py --root . --require-all`. O export foi apresentado pelo usuário como TXT visível, não como serialização exata de DIL: a próxima interface deve aplicar a política UX, preservando integralmente a prosa e escolhas, mas não prometer reprodução pixel a pixel. Não apagar o antigo D538 rejeitado: ele permanece somente no histórico editorial de auditoria.

### Pendência narrativa crítica que NÃO pode ser tratada como fato de mundo

Em D539 a narrativa original pôs Caedren no pátio da Legião e em posição relacionada a Varo sem deslocamento ou adesão militar documentados. **Caedren é o Herói das Sete Estradas, amigo livre de Lucas, não legionário automaticamente.** A fonte literal deve permanecer inalterada; não inventar uma viagem e não reconhecer cargo/cidadania com base nesse trecho. A presença literal de Caedren em D539 já foi ratificada pelo autor em `editorial/recovery/reconciliations/LVI-C01-PIII-D539-AUTHOR-SOURCE.json`; isso **não autoriza inferir rota de viagem, patente ou comando**. Interlúdios de Tharvek, Elyrien e Velkar não concedem a Lucas conhecimento instantâneo.

As escolhas 4 das Partes I e II foram ratificadas com fonte real; D539 Parte III foi ratificada excepcionalmente como cânone sem escolha futura inventada. A Parte IV D540 está arquivada como rascunho e ainda não recebeu uma nova escolha de fechamento. **Não tentar fechar D539 novamente** nem promover D540 por auditoria.

## Qualidade, planejamento e escopo

**Preservar integralmente:** a saga `A ERA DAS NOVE COROAS`, Livro VI `AS COROAS PARTIDAS`, plano v18, cidade e Horizonte Aberto, três marcos D538–540, 40.000 moradias e capacidade futura para 100.000 habitantes (não ocupação instantânea), Casa dos Três Poderes em estruturação, Conselho e poderes autônomos, AERÚN, Forja, 3.600 autômatos e Vértice, Costura de Dados, ARGOS, irmandade e mistérios de Miren/Talis, mundos ainda desconhecidos, ritmo de cenas e opções 1–3/4 especial/5 livre. **Nenhum roteiro de batalha, resultado ou destino é determinado artificialmente pela migração.**

As políticas v14/P01–P81 e UX01–UX12 **não são reescritas** por esta mudança de infraestrutura. As decisões criativas continuam prevalecendo sobre ferramentas e checklists, sem retirar consequências do mundo.

## Limites reais e verificações

- Não existe interceptação automática universal da mensagem final do ChatGPT. O conector GitHub deve ser efetivamente chamado em cada episódio. Sem chamada, a Action não o recebe.
- Para capítulos novos, a publicação automática GitHub está encadeada no mesmo workflow de inbox, pois um commit feito com `GITHUB_TOKEN` normalmente **não dispara outra Action via `push`**. Fonte: https://docs.github.com/en/actions/concepts/security/github_token
- GitHub Actions Artifacts **não** são o backup histórico permanente; os conteúdos versionados são comitados como blobs da branch privada. Fonte: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts
- Arquivos históricos grandes permanecem fragmentados no Git; um único blob Git excedendo 100 MiB é recusado pela plataforma. Fonte: https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits
- `verify_lvi_original.py` verifica fonte original, hashes e fonte dos eventos; `worldroot_canon_selection_guard.py` valida a Parte que de fato recebeu escolha; `test_github_chapter_publisher.py` comprova idempotência e impossibilidade de retroagir para um episódio rejeitado. A CI não é uma inspeção literária humana.
- Respostas finais e arquivos independentes de GitHub ainda exigem GET/readback para declarar armazenamento confirmado. Um teste verde em outra Action não é recibo de entrega do capítulo futuro.

**Política de migração:** sem escrita ou exclusão no Google Drive; `main/worldroot/drive_bridge.py` e templates antigos são preservados como código legado, mas o workflow ativo de capítulo não contém job de Drive. Sem solicitações de secrets OAuth.

## Contrato técnico adicional do próximo episódio Livro VI

O `worldroot/draft_inbox.py` da main aceita os campos **`reviewed_events` e `reviewed_knowledge`**. Para um Livro VI novo, o mesmo `inbox/<episode_id>.json` deve trazer **`character_preflight`** (lista não vazia de fichas de presença) e, se necessário, **`continuity_flags`**. Cada personagem requer `name`, `last_physical_appearance_source`, `location_at_scene`, `affiliation_at_scene` e `knowledge_at_scene`. O campo é preparado pelo narrador antes da escrita final a partir de fontes; nenhum valor é inferido pelo GitHub.

Após o arquivamento principal, `tools/lvi_predelivery.py` confere o mesmo texto literal em inbox e draft e salva, **na mesma transação GitHub**, `editorial/recovery/originals/<episode_id>.txt`, `episodes/<episode_id>/draft/source_proof.json` e `review/continuity_review.json`. A prova deve declarar `ASSISTANT_PREDELIVERY_EXACT_TEXT` e `ui_parity=NOT_INDEPENDENTLY_VERIFIED`, **nunca** alegar que o texto da interface ChatGPT foi exportado independentemente. `tools/verify_lvi_original.py` aceita os eventos já referenciados em `review/eventos_revisados.json` quando a main gera `eventos_e_consequencias.json=[]`; para os três episódios recuperados, continua exigindo a fonte exportada e seus eventos reais. Se falta personagem, origem ou âncora, o job falha antes de publicar um recibo.

Essa etapa não certifica semanticamente uma viagem não narrada nem substitui uma revisão humana. Caedren D539 integra a cena literal ratificada; a origem da viagem, a patente e o eventual serviço na Legião continuam sem comprovação e não devem ser inventados.


## Ratificação autoral extraordinária confirmada — 19/11/2026

As Partes I e II do Dia 538 e a Parte III do Dia 539 são **CANÔNICAS**, registradas nas sequências 10, 11 e 12 em `canon/episodes/`, HEAD `LVI-C01-PIII-D539-AUTHOR-SOURCE`, commit `feefa5fa2c1513d0cab918f59f86325b6fbbe949`. A Action reproduziu os originais exatos, validou fontes/eventos/continuidade, reconstruiu SQLite e conferiu o journal. As duas primeiras opções 4 correspondem aos prompts reais do TXT; a Parte III foi ratificada diretamente pelo autor, sem inventar escolha de continuação. Esta exceção pontual NÃO modifica o protocolo normal de novos episódios. Originais e manifestos continuam imutáveis.
