# WORLDROOT r15 — Auditoria de vivência: C16 Parte IV versus referência C15 Parte II

**Data:** 18/11/2026. **Tipo:** auditoria editorial sobre texto literal, não retcon. **Fonte primária preservada:** `story-archive/episodes/LV-C16-PIV-D537-AUTHOR-SOURCE/draft/episode_draft.json`, `narrativa_integral.md`; referência `LV-C15-PII-D529-AUTHOR-SOURCE`. **Instrução autoral:** manter o episódio, impedir que a meta de 10 mil palavras produza novas histórias com ritmo de relatório.

## Resultados medidos (contagem aproximada)

| Métrica | C15 PII referência | C16 PIV auditada |
| --- | ---: | ---: |
| Arquivo integral, palavras | 10.046 | 13.376 |
| Campo `prose` bruto, palavras | 9.417 | 12.677 |
| Cenas principais | 9 | 15 |
| Corpo médio por cena, palavras | 981 | 816 |
| Cenas abaixo de 650 palavras | 2/9 | 7/15 |
| Falas de Lucas identificadas | 185 | 109 |
| Total de falas identificadas | 459 | 325 |
| Dias encenados | D529 | D534, D535, D536, D537 |

Contagem reprodutível aproximada por corpo de cena `## I —` etc. Não usar como avaliação automática de prosa, POV, naturalidade ou qualidade. Um protagonista pode permanecer silencioso em cenas importantes. O arquivo original inclui interface, títulos e opções; não convertê-los em palavras narrativas.

**Correção de metadado importante:** o usuário citou anteriormente D537 **13h06**; a versão literal recuperada e seu manifesto encerram D537 **11h46**. Não harmonizar por suposição. O draft C16 PIV segue preservado; HEAD canônico após a escolha anterior é C16 PIII D534 18h11.

## Diagnóstico editorial

**O que preservamos:**
- O convite a Miren na cena III (cerca de 1.195 palavras): romance e agência própria sem obrigar a esposa a viajar.
- O café da manhã D535 (IV), Halden e Três Arcos (II), o jantar em casa (VIII) e refeição coletiva D536 (XI): humanidade e humor existentes; não eliminar isso porque a crítica é verdadeira.
- A reunião D535 (V) tem vozes próprias e participação de pessoas autônomas, mas dura tempo considerável na estrutura.
- GÊNESE permanece potente, ARGOS é aeronave arcana singular, Naira age independentemente; voo 005 observado e retornado conforme fonte, sem retcon.
- Após o pouso (XV), Brannik perde a fala, Rumo abraça Lucas, Miren reage: cena com bom potencial emocional.

**Desvio que produziu o efeito de relatório:**
1. O roteiro da Parte III já estabelecera D535–D536 como preparação e D537 como janela possível. A Parte IV passa a representar cada data do calendário como etapa da preparação/ensaio/execução. Uma data condicional virou eixo de ordenação de cenas. O autor NÃO pediu que o calendário inteiro coubesse na mesma parte.
2. As 15 cenas dão impressão de checklist de entregas: reunião e mapa → bancada e Forja → ensaios, inspeção, validação → pouso e relatório. A aventura é válida; a experiência humana foi diluída pela sequência de objetivos técnicos.
3. Sete cenas possuem menos de 650 palavras, contra duas na referência. A prosa cresceu cerca de 35%, mas a extensão média por cena recuou ~17%. Cumprir 10 mil palavras não garante imersão.
4. Depois do voo 005, somente a cena XV (~553 palavras no corpo) concentra grande parte da reação coletiva, alívio e retorno ao vínculo de Lucas. O deslumbramento acontece, mas a narrativa troca de cena e fecha logo depois.
5. A quantidade de formulações técnicas de contenção (autorização, ensaio, hipótese, prova, registro, inspeção) é recorrente. Não remover responsabilidade de Naira nem fatos; evitar reafirmar a toda cena que o resultado ainda depende de uma nova permissão. Consequência e segurança devem existir no mundo sem se tornar discurso defensivo repetitivo.

**Leitura:** volume bem sucedido; foco humano e tempo emocional parcialmente enfraquecidos. Há boas cenas, por isso não refazer nem apagar. O mundo não perdeu necessariamente coerência; a experiência do leitor perdeu continuidade afetiva.

## Novo padrão preventivo

**Produção ANTES de narrar** — usar três perguntas estruturais:
- Qual desejo concreto Lucas vive agora? Que pessoa o afeta e por quê?
- Qual mudança/conflito/revelação justifica dedicar uma cena, sem ser apenas item de projeto?
- Qual relação, pausa ou consequência merece tempo antes de avançar calendário?

**Estrutura flexível, sem quota:** um arco central vivido, secundário somente quando enriquece a experiência. Alternar decisão, surpresa, convivência e consequências. Cenas técnicas completas são bem-vindas, mas evitar uma cena por reunião e uma cena por ensaio. Um dia pode ocupar várias partes; vários dias podem caber numa só se a passagem for intencional e experimentada, não exigência por data-alvo.

**Clímax e depois:** se um capítulo apresenta voo extraordinário, descoberta ou confronto, reservar tempo narrativo real para o impacto nos personagens. Permitir que Lucas e seus companheiros conversem, reajam e tenham prazer, medo, humor, confiança, vergonha ou orgulho; não encerrar imediatamente com outro relatório e opções.

**Revisão antes da entrega** — efetuar readback literal e conferência do autor; usar `worldroot/lived_narrative_audit.py` como alerta estrutural barato. Marcadores LIFE01–LIFE04 avisam sobre múltiplos dias, cenas curtas, linguagem operacional e combinação de risco, sem proibir aventuras técnicas ou atestar qualidade artística. `worldroot/delivery_gate.py` e `worldroot/draft_inbox.py` incluem o parecer consultivo. Se sinalizar LIFE04, o narrador/editor deve reler o texto e corrigir a experiência antes de submetê-lo ao inbox, sem fabricar diálogos repetitivos nem alterar o cânone.

## Integridade

Não modificar `story-archive/episodes/LV-C16-PIV-D537-AUTHOR-SOURCE`, escolha registrada da Parte III, livro, dias, voo 005 ou conhecimentos históricos. Não promover C16 PIV ao HEAD sem escolha posterior. O texto arquivado pode ser bom em vários pontos e ainda precisar de melhor equilíbrio. Não afirmar qualidade literária automática em testes de regex. Não atualizar Drive/Base Viva sem autorização e ferramentas de ação explícitas.
