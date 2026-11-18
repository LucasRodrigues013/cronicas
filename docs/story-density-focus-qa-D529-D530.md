> **ADENDO AUTORAL r14 (18/11/2026).** Este documento era consultivo antes do pedido posterior de Partes com ~10 mil palavras narrativas. O pedido novo cria `worldroot/longform_depth.py` com meta 10.000, janela 9.400–11.000 e piso mínimo de arquivamento 8.800 **apenas para novos drafts**. A regra não autoriza repetição de prosa nem obriga várias cenas/horas artificiais: a qualidade dramática ainda se avalia separadamente. Ver `docs/longform-10k-context-recovery.md`.

# WORLDROOT r11 — auditoria da densidade narrativa e foco dramático (D529–D530)

**Natureza:** análise comparativa, QA consultivo e plano de evolução.  
**Estado:** NÃO modifica episódios publicados/arquivados, HEAD, Livro V, escolha do autor, Drive ou banco canônico.  
**Fontes primárias imutáveis:** `story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md`, `LV-C15-PIII-D529-AUTHOR-SOURCE` e `LV-C15-PIV-D530-AUTHOR-SOURCE`.  
**Regra de autoria:** a Parte II é a referência de experiência literária aprovada; não é uma fórmula para reproduzir sua trama.

## Diagnóstico reprodutível

| Métrica aproximada | Parte II — referência | Parte III | Parte IV |
|---|---:|---:|---:|
| Palavras do arquivo total, incluindo interface e escolhas | 10.373 | 3.949 | 5.484 |
| Cenas principais | 9 | 7 | 8 |
| Palavras somadas nas seções de cenas (aprox.; pode incluir fecho) | 9.481 | 3.873 | 4.693 |
| Mediana aproximada por cena | 1.019 | 520 | 558,5 |
| Cenas com falas explícitas de Lucas | 7/9 | 7/7 | 5/8 |
| Intervalo diegético observado | D529 06h42–20h42 | D529 20h42–23h43 | D529 23h43–D530 18h02 |
| Design visual rico | Presente | Regressão para Markdown simples | Recuperado em r10 |

A Parte III teve cenas curtas, mas sua janela ficcional é restrita. O desvio decisivo está na Parte IV: em aproximadamente 18h19 de tempo diegético, aparecem cenas de convivência, transporte municipal, experimentação em AERÚN, oficina ARGOS, vida de Káiron, investigação cívica e uma possível estrada; o ponto de vista de Lucas torna-se intermitente. Não confundir o número de menções ao nome com prova de POV. A presença de falas de Lucas é apenas um indicador verificável.

### Ritmo por cena (palavras aproximadas)

| Cena | II | III | IV |
|---|---:|---:|---:|
| I | 1.011 | 566 | 529 |
| II | 667 | 517 | 517 |
| III | 625 | 412 | 588 |
| IV | 1.499 | 434 | 820 |
| V | 780 | 520 | 459 |
| VI | 1.019 | 648 | 442 |
| VII | 1.138 | 776 | 588 |
| VIII | 1.687 | — | 750 |
| IX | 1.055 | — | — |

*Contagem exploratória do arquivo integral com segmentação por títulos `## I —` etc.; não separar com precisão absoluta prosa de checkpoint e código da UI na última cena. Usar apenas para comparação, não para exigir quota.*

## Por que a Parte II funciona

1. **Lucas no centro:** acompanha a maior parte da experiência — vulnerabilidade, humor, presentes, relações e decisões. Os desvios de bastidores são exceções que valorizam o reencontro com ele.
2. **Respiração:** a carta de Miren e a caixa de histórias têm tempo de acontecer e produzir transformação emocional. Não trocam de núcleo assim que surge um novo assunto.
3. **Passagem orgânica de horas:** os intervalos de tempo acontecem com contexto, deslocamento, diálogo e momentos cotidianos; relógio não vira uma montagem de relatórios de projeto.
4. **Eventos concretos, não lembretes de pendência:** a cidade permanece viva sem transformar cada experiência técnica em uma reunião rápida.
5. **Mistério com propósito:** pistas e indícios orientam curiosidade, sem resolver tudo nem anunciar informação que Lucas desconhece.
6. **Design:** cabeçalho, calendário, cenas, checkpoint e escolhas interativas são ricos sem competir com a prosa.

## Direção literária para os próximos episódios

- **Centro dramático:** privilegiar Lucas como âncora principal e seu arco de decisões, humor, afeto, curiosidade e descoberta. Referência exploratória: aproximadamente 70–85% das cenas centradas na experiência de Lucas, **sem bloquear exceções legítimas**.
- **Fora de cena:** preferir zero a um interlúdio externo significativo por parte, quando agregar mistério, consequência ou tensão do leitor. Cenas externas adicionais precisam de propósito explícito e consequência futura; nunca impor uma cota.
- **Mundo vivo sem montagem frenética:** atividades simultâneas continuam no journal/World Pulse; só merecem cena completa quando dão avanço dramático. O mundo não para, mas o texto não precisa cortar para cada setor.
- **Mistério que o leitor vê, Lucas ainda não:** separar `READER_SEEN`, `CHARACTER_KNOWS` e `EDITORIAL`; um indício externo pode encerrar um interlúdio com suspense sem teletransportar conhecimento ao protagonista.
- **Ritmo e extensão:** usar Parte II como alvo sensível de densidade e imersão; não forçar enchimento, repetição ou uma contagem fixa. Um episódio íntimo pode ser menor; um episódio com muitos eventos exige mais tempo de cena ou menos tópicos.
- **Estrutura sugerida, nunca obrigatória:** desejo/ação de Lucas → situação vivida e interação → obstáculo/descoberta → consequência emocional ou prática → um ponto de mistério/reação do mundo quando cabível → escolha real do autor.
- **QA qualitativo pré-publicação:** antes de arquivar, perguntar: (a) Lucas viveu ou apenas recebeu relatórios? (b) cada cena transformou algo? (c) houve ritmo e espaço para diálogo? (d) ficou alguma questão intrigante para o leitor? (e) os personagens foram autônomos? (f) o encerramento se conecta a escolhas significativas?
- **Não reescrever retrospectivamente as Partes III e IV.** Aplicar somente aos próximos textos novos e a eventuais revisões explicitamente autorizadas.

## Seis frentes técnicas para WORLDROOT >9/10

| Ordem | Frente | Entrega concreta | Critério de aceite e cuidado |
|---|---|---|---|
| P0 | **QA narrativo focal** | `worldroot/story_focus_audit.py`; perfil Parte II e testes sintéticos | Advisory barato, com métricas de mediana e cenas com falas de Lucas; não confundir heurística com julgamento literário e não impor quota |
| P1 | **Reconciliação de personagens** | IDs imutáveis + alias com evidência + localização temporal + voz/objetivo/vínculo + visibilidade; reexaminar crosswalk 82 históricos/95 cadastros | Nunca unir 47 correspondências não seguras apenas por semelhança de nomes; revisão dirigida do elenco antes de habilitar consulta canônica |
| P1 | **História D001–D528** | Consulta à `history/LITERAL_INDEX.sqlite` r9, trilhas fonte/linha e verificação seletiva de trechos; converter candidatos somente após revisão | 6 fontes + 4.626 chunks são **busca literal**, não 4.626 fatos canônicos. Auditar 40 Q históricas de staging sem promoção automática |
| P1 | **World Pulse causal, não dispersivo** | Agenda temporal proposta de NPC/facção com ator, objetivo, canal, latência, impacto em Lucas/leitor, e status `PROPOSTO` | No máximo o que a cena merece, sem tick fictício automático, sem decisões autorais impostas; um interlúdio só com ganho dramático |
| P2 | **Drive–GitHub/Base/Atlas** | Credenciais confiáveis WIF/OIDC no executor autorizado, ID/revisão remota, SHA após readback, outbox/compensação, HEAD por último | Teste real com erro induzido e recuperação. Não confundir GitHub-only com confirmação no Drive; não sincronizar cegamente antes de revisar identidades |
| P2 | **Resumo de estado gerado** | Gerar documentação operativa a partir do `story-archive/canon/HEAD.json` e `CONTEXT.json` via comando/Action read-only | Apontar estado D529 PIII fechado + D530 PIV rascunho no momento da revisão; eliminar cabeçalhos estáticos envelhecidos e validar em CI |

## Gate de aceitação da próxima parte

1. Respeitar a escolha real do autor e HEAD/CONTEXT vigentes; sem avanço de data não explicado.
2. Priorizar a vivência de Lucas e interações longas suficientes para revelar caráter, escolhas e consequências.
3. Permitir interlúdios externos, mas verificar sua função e a causalidade; não transformar progresso paralelo em uma montagem automática.
4. Inserir ponto de mistério relevante para o leitor quando organicamente adequado, preservando segredos e conhecimento individual.
5. Preservar visual r10 (UX01–UX12), 1–3 alternativas + 4 especial + 5 ação livre.
6. Executar validações estruturais existentes + `inspect_installment` como *aviso editorial*. Não bloquear de modo mecânico um capítulo excelente por ser mais curto.
7. Arquivar literal e revisar SHA; fechar somente após escolha do autor. Drive não é atualizado pelo workflow GitHub-only.

**Regra de integração:** esta auditoria é proposta de aprimoramento editorial e métrica auxiliar, não aprovação silenciosa de mudanças irreversíveis de cânone ou de regras narrativas. Após aceitação do PR, manter histórico de feedback e registrar versão aprovada.
