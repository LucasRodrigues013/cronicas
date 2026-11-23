# CRÔNICAS — R24 | Direção literária do Livro VI sem retcon

**Natureza:** proposta editorial executável para novas Partes, com medidores consultivos. **Não modifica** capítulos, status, escolhas, HEAD, personagens, magia ou política permanente v14. A criação deste documento não aprova automaticamente novas regras de cânone. A decisão final permanece com o autor.

## Fonte real a cada nova Parte

1. Recuperar o HEAD atual do ramo privado story-archive/canon/HEAD.json, não datas impressas em README/políticas históricas; conferir canon/CONTEXT.json, ops/RESUME.json e a última narrativa integral, distinguindo o último rascunho.
2. Consultar últimas aparições, locais, vozes, conhecimento e relações *com evidência*; atualizar esse contexto somente com fatos que os personagens efetivamente viveram.
3. Respeitar a ação real do autor; sem decidir por Lucas, promover draft ou insinuar aprovação de acontecimento proposto.
4. Conduzir cinco Partes com progressão dramática e quatro escolhas mais ação livre, sem número fixo de cenas e sem obrigação artificial de que a guerra ou reunião ocorra em data pré-fixada.

## Problemas encontrados e suas intervenções

### LIT01 — Informação de bastidores vazando para a prosa

**Sinal real:** a menção a "contagem inventada de mortes" no Capítulo 3 remete à auditoria do escritor, não à percepção das pessoas. Dados ainda não confirmados pertencem ao registro de produção. Na narrativa, mostrar as informações parciais, a incerteza e as pessoas reagindo.

**Exemplo demonstrativo (NÃO CANÔNICO):**
- Expositivo: "Não havia uma contagem inventada; nenhum evento fora declarado sem confirmação."
- Narrativo: "Ysol conferiu pela terceira vez os nomes na prancha. Uma mãe se aproximou; ela ainda não tinha uma resposta e não fingiu ter."

Não cortar negacões esteticamente importantes por regex. O alerta LIT01 é pedido de leitura humana, não proibição cega.

### LIT02 — Fragmentação e ritmo de fórmula

O Capítulo 1 tem predominância de linhas de narração muito curtas; os capítulos posteriores variam mais. O número de seções não deve estabilizar em dezoito por conveniência de um molde. **Uma cena começa porque algo muda, não porque o contador exige outro cabeçalho.** Variar período, parágrafo e corte conforme impacto.

Uma corrida e uma perseguição podem precisar de cortes rápidos. Uma conversa de Miren com uma testemunha pode precisar de páginas, cheiros, dúvidas e pequenas ações. Uma despedida não exige cliffhanger barulhento para ter valor.

### LIT03 — Carisma de Lucas sem repetição mecânica

**Manter:** extraordinário, corajoso, exageradamente criativo, caloroso, apaixonado, engraçado, impulsivo, capaz de ser severo contra ameaças. **Evitar:** arrogância involuntária, anunciar cargos como se a vontade de outros fosse irrelevante, gritar em praticamente toda resposta ou reduzir cada diálogo a uma disputa de punchlines com NÓX/SISTEMA.

Prática: em cada encontro significativo, conferir se Lucas escuta a necessidade de alguém, é afetado por uma resposta inesperada, reage como pessoa e escolhe uma ação coerente. Sua bondade aparece por gestos e decisões, não discursos de que é bondoso. O humor deve continuar ácido e espontâneo; o silêncio não precisa ser imposto como virtude.

**Exemplo demonstrativo (NÃO CANÔNICO):**
- Achatado: "EU ORDENO QUE VOCÊ COMANDE A CIDADE!"
- Mais fiel: "Eu confio em você para liderar isso. Mas só serve se também for o que você quer. E, por favor, me diga que a primeira ordem será proibir Brannik de instalar foguetes na prefeitura."

### LIT04 — Estrutura repetida e conflito sem oposição

Antes de elaborar uma cena, escrever em registro privado cinco campos: **desejo**, **resistência**, **ação vivida**, **virada**, **consequência**. Não apresentar esses campos ao leitor. Conflito não precisa ser violento: um povo pode rejeitar uma proposta de Lucas, um companheiro pode preferir outra missão, uma descoberta pode refutar a hipótese favorita de Miren.

Capítulo 3 é o padrão *de consequência humana*, não um comando de criar guerra a cada capítulo. Capítulo 5 é referência *de maravilhamento e aventura cultural*; o livro seguinte pode alternar silêncio, diplomacia, batalha, intimidade, investigação e festa genuína.

### LIT05 — Vozes distintas e arcos pessoais

Para cada personagem relevante, conferir: intenção atual, medo/contradição, maneira específica de falar, vínculo que mudou desde sua última cena, decisão que pode tomar sem Lucas e custo humano do resultado.

- Miren/Astra: perguntas e inferências científicas próprias, não dependência de revelação dada pelo protagonista.
- Naira/Forja: domínio técnico com capacidade de dizer "ainda não pode voar" de modo fundamentado.
- Kael/Lysa: visão política, iniciativa independente e discordância sem teatralidade repetida.
- Varo/300: liderança e vidas individuais; não voltar a provar o direito de existir como se fosse novidade.
- NÓX/Rumo/SISTEMA: três personalidades com agendas e tonalidades diferentes, não um coro de piadas idênticas.
- Oponentes: meios, informações, custos, falhas e capacidade de adaptação; não conhecer decisões secretas sem canal de informação.

### LIT06 — O brief rápido não pode voltar ao Capítulo 1

A política P81 contém um checkpoint D539 **histórico**. Não pode definir o episódio vigente. O utilitário build_live_brief recebe o HEAD recém-lido, identifica C/Parte/Dia/episódio/sequência e cria um resumo sem reinstalar datas passadas. A falta de HEAD vivo gera alerta no preflight para texto identificado como Livro VI. Os arquivos de política permanecem intactos e auditáveis.

## A experiência de alta fantasia isekai

1. Uma maravilha deve provocar diferentes reações legítimas: medo, fé, curiosidade, inveja, interesse comercial, ciência e espanto. Lucas NÃO precisa deixar de ser poderosíssimo.
2. Povos, línguas, seres, rituais, comidas, fauna, clima e história anterior precisam afetar decisões concretas. Não são apenas descrições no Atlas.
3. A ligação com a Terra deve produzir contraste e emoção pessoal, não apenas inventários de carros, aparelhos e arquitetura.
4. Impérios e antagonistas operam por rotas e informações; vitórias não evaporam no episódio seguinte e resgates não anulam trauma automaticamente.
5. O mistério tem hipóteses e evidências acumuladas; revelação não deve ser dada por um narrador onisciente à pessoa errada.

## Operação e critérios de aceite do novo episódio

1. Ler literalmente HEAD/último episódio/última escolha e últimos eventos relevantes; marcar rascunho como NÃO CANÔNICO.
2. Preparar cartões de cenas privados opcionais com review_scene_cards(...); não antecipar ações irreversíveis de Lucas.
3. Escrever a Parte inteira, priorizando momentos vividos; sem obrigatoriedade de comprimento ou dezessete/dezoito cenas.
4. Executar quick_preflight(prose, head=head), review_episode(prose), inspeções de foco, dias e interface. Em avaliação de várias Partes, usar review_series_structure([...]) apenas para localizar repetição de quantidade.
5. Fazer uma revisão humana final: voz de Lucas, contraponto de Miren, dilemas, novidade, variedade, ritmo, consequência e leitura prazerosa. Alertas do utilitário **nunca** são nota literária ou licença automática para retcon.
6. Arquivar texto integral/5 escolhas e ler de volta hashes reais no story-archive, sem promover o HEAD antes da escolha subsequente do autor.

### Critérios técnicos verificáveis

- Tests sintéticos do módulo passam em CI; sinais LIT01–LIT06 surgem apenas quando dados compatíveis são fornecidos.
- O intake de rascunho entrega os indicadores como informação consultiva, usando HEAD vivo; não altera pacotes já imutáveis.
- A avaliação de prosa preserva o texto byte a byte e não toca em canon/HEAD.json, decisões ou armazenamento Drive.
- Nenhuma nota 9/10, redução de risco narrativo ou melhoria de qualidade é declarada como resultado automático do software.

**Escopo do PR R24:** código de medição/brief, integração de intake, testes, documentação e precedência dinâmica. Alterações de novas políticas permanentes serão propostas apenas após aprovação autoral específica.
