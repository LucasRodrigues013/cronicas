# WORLDROOT R25 — Restaurar a experiência literária aprovada

**Autorização autoral:** 22/11/2026, pedido explícito para executar as seis correções. **Escopo:** novos rascunhos, sem retcon, sem mudança do HEAD, sem promoção automática da Parte V D563.

## Contratos separados

**Integridade:** HEAD vivo, SHA, cronologia, locais, informação, escolhas, autonomia, GÊNESE e cinco opções. **Experiência:** o leitor vive cenas com Lucas; a narrativa deixa os demais personagens agir; o controle operacional fica invisível.

## Seis medidas reais

1. **UX04 rígida para novos episódios:** diálogo direto começa com nome destacado e travessão, por exemplo **LUCAS —**; a violação impede novo arquivo. Episódios anteriores mantêm bytes originais e são lidos no modo legado.
2. **Revisão de experiência vivida:** ao menos dois momentos com trechos literais distintos (em cenas distintas quando há duas ou mais; numa única cena longa quando só existe uma), experiência, virada e consequência descritas, registradas no inbox v2. Não basta citar o número de palavras.
3. **Separação de bastidores:** frases inequívocas como 'não declarou uma evolução inventada' são detectadas antes do arquivamento; o motor as impede em novas histórias. Ciência, incerteza e gestão ainda podem ser dramatizadas naturalmente.
4. **Diretor narrativo privado:** planejamento sintético com escolha autoral, HEAD, promessa ao leitor, foco vivido por Lucas, virada, mundo independente e incógnitas. Jamais despejar o briefing no capítulo.
5. **Gates conectados à publicação:** novos rascunhos do Livro VI precisam de schema worldroot-draft-inbox-v2 e passam pela validação R25; provas literais são arquivadas como review/experiencia_r25.json. Falas sem nome não são classificadas falsamente como silêncio de Lucas.
6. **Regressões reais e sintéticas:** testes de formato, evidência, direção, imersão, fontes e retrocompatibilidade; comparador somente leitura do corpus integral. Passagem no teste não garante qualidade artística.

## Comparação histórica que motivou a correção

| Fonte verificada | Cenas por parte | Falas rotuladas | Falas diretas sem nome |
|---|---:|---:|---:|
| LV C15 Parte II D529 | 9 | 448 | 0 |
| LVI C04 D554–558 | 18 em cada uma das 5 | 937 | 16 |
| LVI C05 D559–563 | 18 em cada uma das 5 | 10 | 1673 |

Contagens obtidas diretamente do ramo privado story-archive; C05 Parte V ainda é rascunho. Cenas abaixo de 650 palavras: LV C15 II 2/9, C04 90/90 e C05 78/90. Esses são sinais de forma, não notas de literatura.

## Instruções para novos episódios do Livro VI

1. Ler story-archive/canon/HEAD.json, última escolha REAL, última narrativa literal, fichas e regras. Não usar P81 D539 como atual.
2. Preparar payload narrative_direction: schema worldroot-narrative-direction-v1; source_episode_id exatamente o HEAD; author_choice; reader_promise; lucas_lived_focus; central_change; independent_world entre 1 e 3 itens; unknowns_preserved não vazia; does_not_choose_for_lucas true.
3. Escrever em estilo de romance imersivo sem número fixo de cenas, nomes destacados nas falas e sem explicações sobre o próprio motor.
4. Preparar reader_review: schema worldroot-reader-review-v1; decision REVISADO_COM_EVIDENCIAS; scene_evidence com duas evidências de momentos distintos (uma única cena longa é permitida), cada entrada com scene em numeral romano, literal_anchor texto exato da cena, felt_experience, scene_turn, lasting_consequence. Se houver padrão excessivamente fragmentado, pacing_decision deve explicar a decisão da cadência.
5. Usar schema worldroot-draft-inbox-v2 para criar novos rascunhos; o inbox v1 antigo permanece válido somente no readback de históricos e nos testes legados do Livro V.
6. Após arquivar com SHA e revisar experiência, entregar ao leitor cinco escolhas. Apenas nova escolha autoral pode canonizar a Parte que ficou pendente.

## Auditoria visual e comparação do corpus

Com os arquivos literais do story-archive disponíveis localmente, executar: python -m worldroot.corpus_regression REFERENCIA C04_I C04_II C04_III C04_IV C04_V C05_I C05_II C05_III C05_IV C05_V.

Fonte referência: episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md. C04: episódios da Parte I D554 até Parte V D558. C05: Parte I D559 R2, PII D560, PIII D561, PIV D562 e PV D563 (a última ainda não canônica).

## Limitações e critério de aceite

Uma evidência textual formalmente válida não garante uma cena emocionante. A revisão humana/autor deve continuar avaliando voz, humor, autonomia, consequências, ritmo e prazer de leitura. A R25 mantém esse julgamento separado das verificações automáticas.

**Não modificar capítulos antigos, decisões passadas ou cânone em nome do novo estilo.**
