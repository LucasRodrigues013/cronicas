# WORLDROOT r16 — auditoria semântica de fechamento Livro V e prontidão para Livro VI

**Solicitação autoral:** 18/11/2026. Depois da imposição de volume longform, houve perda de fidelidade a arcos e à ordem semântica das conquistas. Comparar Capítulo 15, especialmente Parte II, com Capítulo 16 Parte V. **Não reescrever o Livro V. Não iniciar o Livro VI nesta auditoria.**

## Fontes literais consultadas

- `story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md` (SHA256 `5b2a269fa91ca1c3869d59a3b6e5fe3cccef3f226f3f7a4624597fe1dc29bea9`) e Partes III–V do Capítulo 15.
- `story-archive/episodes/LV-C16-PI-D532-AUTHOR-SOURCE` a `LV-C16-PV-D537-AUTHOR-SOURCE`, textos literais em `draft/` e fontes de encerramento em `canon/episodes/`.
- Fechamento `LV-C16-PV-D537-AUTHOR-SOURCE` SHA256 `34d2fa4ce224182f3bc407b17d6ad89cc7e6a239e58fa97cecd72d46c874a01b`. A escolha do autor por terminar gloriosamente Livro V foi registrada na `choices/LV-C16-PIV-D537-AUTHOR-SOURCE/option-5.json`.
- `canon/HEAD.json` e `canon/CONTEXT.json` lidos antes da correção; estado final: **Livro V fechado, Capítulo 16 Parte V, Dia 537 23h46, Casa do Jardim Branco, sequência 9**. Livro VI **não iniciado**. Google Drive `NAO_SINCRONIZADO`.

A Parte I do Capítulo 15 é a linha-base D528 preservada em `episodes/bootstrap`; esta auditoria compara as Partes II–V disponíveis no arquivo de episódios do GitHub, não afirma ter um pacote independente `LV-C15-PI`.

## Métricas (mesmo contador aproximado, interface não é prosa)

| Indicador | C15 Parte II — referência aprovada | C16 Parte IV | C16 Parte V — final |
| --- | ---: | ---: | ---: |
| Arquivo integral, palavras aproximadas | 10.046 | 13.376 | 12.558 |
| Campo bruto de prosa, palavras | 9.417 | 12.677 | 11.931 |
| Cenas | 9 | 15 | 9 |
| Dias atravessados | 1 (D529) | 4 (D534–537) | 1 (D537) |
| Tempo de cena, eixo | Presentes e encontros voluntários | Preparação técnica/voo | Epílogo cívico e íntimo |

A Parte V reduziu a fragmentação temporal da Parte IV, e seu total de palavras não é, por si, um problema. **Regressão principal é temática/semântica**, não cronologia ou ausência de cenas. Cenas fortes C16 PV: conversa íntima pós-voo com Naira, presente de Brannik, caminhada e Miren, humor com Halden, Rumo e o casal.

## Comparação semântica com referências imutáveis

1. **Káiron:** em C15 II, a carta afirma literalmente `*Mas gosto da minha vida.*`, descrevendo casa, planta e livre escolha. C16 PV traz nova caixa de pedras/pena/barbante e a descoberta verbal `**LUCAS —** Uma vida.`. A nova lembrança é válida, mas apresentá-la como primeira descoberta de identidade pode reencenar sem avanço um arco já consolidado. **Próximo livro:** escolhas e relações concretas novas, sem reensinar autonomia inicial.
2. **Varo e os trezentos:** C15 II entrega relatos voluntários, histórias de vidas civis e profissões, com `**VARO —** São histórias.`; C16 PV retoma em extensão o reconhecimento de que não são um número e incluem carpinteiro/novas ocupações. **Próximo livro:** consequências de suas identidades diversas, não segundo discurso de emancipação.
3. **Miren:** C15 II já contém `Também quero que você saiba que às vezes vou escolher caminhos meus.` C16 V repete muitas vezes a tese de autonomia, embora também mostre investigação das pedras e afeto concreto. **Próximo livro:** decisões científicas reais, mistério não resolvido, dilemas próprios e relação viva, sem repetir a mesma declaração.
4. **Lucas, a Cidade Livre e o trono:** a inscrição no Observatório em C15 II já diz `Aqui, o Criador não veio governar.`; C16 V multiplica negações de coroa, rei, trono, e termina com novo discurso comunitário. É um eco legítimo para um final solicitado como glorioso, mas deixa o clímax excessivamente explicativo. **Próximo livro:** demonstrar esse valor por atos difíceis e novas situações, não proclamação repetitiva.
5. **Estrutura emocional:** a carta de Miren e a caixa de histórias transformam relações durante cenas integrais de C15 II. C16 PV apresenta bons momentos, mas os reúne numa cadeia de confirmações de conquistas anteriores e num símbolo coletivo de constelações, em vez de deixar novas consequências inesperadas protagonizarem o desfecho. Uma nova grande cena é permitida quando nascer de causalidade própria.
6. **Fonte de futuro ainda aberta:** pico de 1.462 km/h em ARGOS 005 foi MEDIDO, não máximo. Planejamentos e três horizontes continuam com proveniências distintas; posição atual de Saira Venn/Jardim Errante e a estrada ao norte ainda não verificadas; a sétima nota e Talis sem resolução comprovada. Não promover hipóteses a fatos.

**Não encontrado:** inversão geral de dias em C16 PV, perda integral dos poderes de GÊNESE ou fechamento de Livro V sem autorização. **Encontrado no arquivo derivado:** CONTEXT contradiz HEAD: texto estático `Livro V remains open without the author's explicit closure` apesar de `book_closed=true`. Também agrupava um registro BASTIDORES de encerramento de livro entre o `explicit_character_knowledge["Lucas"]`, criando risco de o narrador atribuir a Lucas consciência editorial do formato de livro. O journal original não precisa de retcon; reparar só `write_context` e rederivar `CONTEXT.json`.

## Correção do motor antes do Livro VI

**P31–P34, política editorial v7:** exigir progressão semântica, não redescoberta de lições; épico conquistado por causalidade, não cerimônia extra; dados/consciência editorial separados; qualidade acima de quota. `compact_brief` coloca esse compromisso em destaque.

**Longform:** 10.000 palavras seguem objetivo editorial, nunca limite rígido. O piso 8.800 do r14 deixa de bloquear arquivamento; menos palavras completas, com uma boa cena, são preferíveis a alongamento artificial. Arquivo, SHA, fonte literal, escolha real, UX e prova de evento continuam obrigatórios. Não confundir aviso de volume com qualidade certificada.

**Memória:** `write_context` calcula a condição de livro aberto/fechado pelo HEAD real, separa `backstage_events_not_character_knowledge` dos eventos legíveis e exclui BASTIDORES das listas de conhecimento de personagens. Dados arquivados permanecem imutáveis; só projeção derivada será reparada. A introdução Livro VI deve consumir a projeção regenerada, não a antiga.

**Transição:** baseline privado `story-archive/editorial/transitions/lv-to-lvi-semantic-baseline.json` armazena 13 itens com SHA/âncoras do texto literal e estados ESTABELECIDO / EM_ABERTO / NAO_CONFIRMADO / EDITORIAL. `worldroot/transition_baseline.py` verifica que a referência existe e bate com journal e HEAD; não valida qualidade artística nem gera capítulo. O autor mantém direito de abrir Livro VI quando desejar.

### Checklist de edição humana ANTES de cada novo episódio

- O personagem já viveu/aprendeu este tema? O que é comprovadamente novo hoje: decisão, custo, relação, descoberta ou repercussão?
- Quais frases são observação sensorial/diálogo e quais são mera explicação do narrador reiterando liberdade, poder, autonomia, ausência de rei, origem dos trezentos?
- Há motivo dramático para a cena? Acontece por desejo do personagem ou para alcançar quota de palavras/data de missão?
- Está claro quem sabe qual informação, quando, por qual fonte e com que incerteza?
- Causas e deslocamentos continuam plausíveis; eventos sem solução continuam sem solução?
- O final deixa espaço para o mundo e personagens mudarem de verdade, em vez de recitar todos os feitos do livro anterior?

**Aceite técnico:** testes sintéticos do código verde, `CONTEXT.json` regenerado com HEAD fechado, não conter regra de Livro V aberto, não apresentar livro como conhecimento de Lucas, baseline privado com 13 âncoras verificadas. Somente após isso considerar r16 pronto em GitHub. Nenhum teste determinístico promete uma nota de excelência literária. Livro VI permanece não iniciado.
