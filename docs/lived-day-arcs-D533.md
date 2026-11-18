# WORLDROOT r13 — Ciclo diário vivido e encerramento orgânico

**Direção autoral aprovada:** 18/11/2026. O autor observa que as partes ainda encenam muitas atividades num dia, mas frequentemente não vivem o período completo; quer começar e fechar os dias, sem sacrificar qualidade, humor, romance, consequências, protagonismo e poder de escolha.

**Fonte imutável (GitHub privado):** `story-archive/episodes/LV-C16-PII-D533-AUTHOR-SOURCE/draft/narrativa_integral.md`.
**Referências:** C16 PI (`LV-C16-PI-D532-AUTHOR-SOURCE`) e padrão aprovado C15 PII (`LV-C15-PII-D529-AUTHOR-SOURCE`).
**Regra ativa:** `worldroot/editorial_policy.json` v4, P24–P25. **QA técnico:** `worldroot/day_arc_audit.py` consultivo.

## Dados auditados e limites da medição

| Indicador | C15 PII · referência | C16 PI | C16 PII |
|---|---:|---:|---:|
| Palavras de arquivo integral, aproximadas | 10.373 | 7.138 | 7.730 |
| Cenas com cabeçalho `## I —` etc. | 9 | 9 | 10 |
| Mediana de palavras nas seções de cena (pode incluir fecho/UI) | 1.019 | 874 | 696 |
| Falas identificadas por `**PERSONAGEM —**` | 448 | 246 | 298 |
| Cenas com fala de Lucas | 7/9 | 9/9 | 10/10 |
| Âncora cronológica | D529 06h42 → 20h42 | D531 18h34 → D532 18h19 | D533 06h43 → 17h29 |
| Janela de relógio | 14h00 | 23h45 (cruza data) | 10h46 |
| Dia da última cena encerrado literalmente? | **Não**: festa ainda continua | Lucas adormece, seguido de próximo despertar em D533 | **Não**: deixa a noite de D533 aberta |

**Conexão causal:** C16 PII cumpriu sua escolha livre de rotina de Lucas, conversa com Miren sobre AERÚN, ida ao Campo pela porta dimensional, rede limitada Campo/Forja/AERÚN/Casa Cívica, testes de metadados e recolhimento de detrito de pista sem Lucas fazer tudo. 15 eventos candidatos e 14 entradas de conhecimento foram revisados e arquivados, **não fechados canonicamente**: ainda não existe uma escolha para C16 PII.

**Problema editorial:** ao distribuir 7.730 palavras por dez cenas, boa parte das interações dura pouco. Cenas I (382), IV (454), VII (503) são especialmente sucintas. Cena VIII tem 1.498, mas trata principalmente da conferência regional, com risco de parecer coordenação/reunião em vez de aventura; o romance e o mistério ficam sub-representados. A despedida da cena X às 17h29 encerra a **parte**, não o **dia**.

## O que significa 'viver um dia inteiro' daqui em diante

Não é narrar 24 horas de atividades e **não** é obrigar uma parte a cobrir o dia todo. A unidade de experiência é o **arco de um dia**; ele pode ocupar uma, duas ou mais partes, e pode atravessar a madrugada apenas se a história realmente acontecer à noite. Se o autor escolher uma ação que não cabe no dia, preservar sua escolha e os deslocamentos. Não acelerar artificialmente.

Uma sequência plausível, **flexível**:
1. **Começo:** despertar/retomada, estado emocional, relações, objetivos e o mundo concreto que Lucas percebe.
2. **Vivência:** cenas demoradas o suficiente para ações, conversas, contraste, imprevistos e escolhas de Lucas; um ou dois focos dramáticos, não todos os projetos em paralelo.
3. **Virada:** consequência prática ou emocional, descoberta ou pista que altera o significado do dia; leitor pode saber algo que Lucas ignora, sem transferência automática de conhecimento.
4. **Fechamento:** noite, jantar, descanso, diálogo íntimo, consequências sociais ou outro acontecimento final significativo. Se necessário, terminar uma parte e prosseguir no **mesmo dia** até chegar lá.
5. **Próximo dia:** só após transição explicitamente narrada e escolha autoral real; o resumo identifica o dia aberto ou já encerrado. Nunca inventar repouso, atravessar noites sem indicação ou fechar o livro por conveniência.

## Situação prática — D533

- **06h43:** Lucas acorda após dormir no Dia 532.
- **07h04–08h12:** corrida, casa, café e conversas com Miren, com iniciativa própria de ambos.
- **09h21–16h17:** deslocamento dimensional e atividades técnicas no Campo, engenharia de informação, reunião regional e resolução local de FOD.
- **17h26–17h29:** Lucas despede-se de Rumo e entra na Casa dos Horizontes, indo rumo à residência.
- **Ainda não narrados:** noite de D533, jantar e convivência posterior, eventuais acontecimentos íntimos ou uma pista nova. Não assumimos que ocorrerão automaticamente: são oportunidades da próxima **escolha**.

A continuação pode explorar a noite de D533, inclusive a opção 3 da parte III já oferecida, e só depois passar a D534. **Nenhuma escolha foi feita por esta auditoria.** O próximo turno não deve obrigar o usuário a selecionar um caminho específico; ele pode escolher qualquer opção ou ação livre.

## Teste rápido: não criar empecilhos

`inspect_day_arc(prose)` coleta apenas cabeçalhos de cena e relógios explícitos. Informa primeiro/último dia e horário, minutos decorrido(s), dias tocados e alerta caso uma parte vá do amanhecer ao fim da tarde deixando a noite disponível. Não altera cânone, não força um fechamento de dia, não julga literatura. Um episódio íntimo curto pode ser ótimo; um episódio noturno que termina ao amanhecer é válido.

O `draft_inbox` apresenta o sinal no **recibo**, junto do QA de densidade. É **não bloqueante**: qualquer avaliação literária é do autor e do editor, não de um regex.

## Critérios de aceitação na próxima narrativa

- HEAD fechado e rascunho recuperados dinamicamente do GitHub.
- A escolha do autor determina o próximo avanço; não inferir que 'vamos fechar dias' equivale a escolher 3, 4 ou 5 da história.
- Uma passagem de tempo maior precisa de transição compreensível (descanso, trabalho, viagem, festa, montagem explicitamente intencional).
- Priorizar Lucas, Miren, SISTEMA e relações humanas; os NPCs continuam com autonomia.
- Preservar GÊNESE, consequências reais e mistérios que progridem.
- Manter design UX rico, cinco escolhas e capítulos integralmente arquivados.
- Somente escolha real fecha a parte anterior; **'FIM DA PARTE II' não significa 'FIM DO DIA' nem 'FECHADO_GITHUB'**.
- Não avançar HEAD, Drive ou Atlas por editar diretrizes.
