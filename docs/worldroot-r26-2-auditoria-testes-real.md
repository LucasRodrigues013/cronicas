# AUDITORIA R26.2 — TESTES REAIS, FALHAS, CORREÇÕES E PENDÊNCIAS

**Projeto:** CRÔNICAS DE UM NOVO MUNDO. **Escopo:** motor R26/R26.1, 1.020 magias e GÊNESE como Autoridade; continuação canônica NÃO escrita. **Fonte de verdade para a história:** `story-archive/canon/HEAD.json`, capítulos e episódios literais; planejamentos e pesquisas externos são material de produção.

**Evidência do RED inicial:** https://github.com/LucasRodrigues013/cronicas/actions/runs/45105572219 — 10 testes adversariais iniciais, seis falhando no motor anterior.
**Evidência GREEN final da rodada:** https://github.com/LucasRodrigues013/cronicas/actions/runs/45107394666 — 440 testes Python, execução 14,598 segundos, resultado OK; compilação estática e política de arquivos públicos também aprovadas. Executar novamente em cada alteração subsequente antes de mesclar.
**Plano:** PR https://github.com/LucasRodrigues013/cronicas/pull/58, mesclagem após verde e ativação dos workflows privados por SHA imutável.

## 1. Falhas REPRODUZIDAS — antes vs. depois

| Código | Cenário real de teste | Comportamento inicial RED | Comportamento corrigido |
|---|---|---|---|
| R26-F01 | Miren abre um livro com nome de magia | Tratava como uma conjuração sem livro de feitiços efetivamente lançado | Citação/volume não é lançamento |
| R26-F02 | Brannik lança uma magia, ficha atribui a Thaeron | Conjurador errado era aceito | Nome do conjurador deve constar do mesmo trecho ou contexto narrativo comprovado |
| R26-F03 | Narrador afirma que GÊNESE se esgotou por mana | Passava porque o campo de avaliação dizia `genese_unrestricted=true` | Bloqueio específico na prosa |
| R26-F04 | Narrador reduz GÊNESE a Círculo IX | Passava por falta de auditoria semântica básica | Bloqueio: Autoridade não é feitiço/rank |
| R26-F05 | Narrador decreta AERÚN anterior à criação do mundo | Passava sem qualquer evidência cosmológica | Bloqueio da declaração categórica; rumores e perguntas seguem válidos |
| R26-F06 | Narrador diz que Instituto AERÚN é o dragão AERÚN | Identidades podiam ser fundidas | Bloqueio e aviso para ocorrências ambíguas |

Nota: a diferença entre as colunas foi observada em execução REAL do GitHub Actions: testes foram incorporados *antes* dos reparos e falharam; depois passaram.

## 2. Novas proteções implementadas

**Poder do Criador:** `worldroot/r26/authority_creation.json` classifica CREATION/GÊNESE como Autoridade singular, sem escala, quantidade, energia, mana ou teto; a ignorância de Lucas é de origem, história, método e possibilidades imagináveis, não falta de potência. `worldroot/r26_authority_guard.py` verifica afirmações categóricas na prosa e mantém lendas, dúvidas e diálogos como hipóteses. O módulo nunca decide a cosmologia.

**Reuso de magias:** `verify_prior_spell_source` só admite arquivo individual de episódio em `episodes/<id>/draft/narrativa_integral.md`, com `canon/episodes/<id>.json` fechado e SHA256 do texto idêntico ao registro canônico. O trecho anterior deve citar a MESMA magia e evidenciar conjuração/ensino, não título de livro. Testes rejeitam caminho atravessado, capítulo agregado, arquivo sem ratificação, hash alterado e nome diferente. Em enumeração de metadados da branch, **33 dos 33 episódios canônicos indexados** possuem os textos literais individuais. Isso não comprova que todo o acervo antigo D1–D528 tem registros no mesmo formato.

**Diretores:** primeiro uso R26X regional com prova de origem; invenção institucional de Três Arcos exige inventor humano/autônomo realmente nomeado que não seja apenas Lucas. Grande magia regional de Círculo VII–IX requer `individual_scene_design` com assinatura cultural, mecanismo particular, escolha de personagem, reação sensorial e resposta do mundo em sequência dentro da cena. Combate continua sem vencedor programado. Cena íntima sem luta/magia permanece legítima.

**Auditoria da própria auditoria:** a verificação da origem histórica é uma prova textual, não uma autorização criativa automática; se houver algo ambíguo, não promover como conhecido por mera semelhança. O verificador da Autoridade é heurístico, não substitui leitura humana e não impede personagens de duvidar, errar ou mentir.

## 3. Lote de simulações

- **10 testes adversariais iniciais:** seis falhas reproduzidas, depois verdes.
- **39 simulações adicionais:** CREATION, dragões, Sistema, AERÚN duplo, catálogo de livros, casts, herança falsa, SHA adulterado, registros não ratificados, artista/inventor errado, tradições cívicas, origem cultural, GÊNESE sem custo, perguntas e lendas, efeitos de grande Círculo.
- **5 regressões de diversidade:** 900 variantes, 90 mecanismos distintos, total 1.020, risco de fórmula, segurança de autoridade e não alteração do cânone.
- **Suíte completa:** 440 testes verdes no SHA de diagnóstico citado; validação estática e auditoria pública aprovadas. Os 440 incluem regressões preexistentes; NÃO equivalem a 440 cenas reais produzidas nem a 440 episódios diferentes.

## 4. Lacunas NÃO RESOLVIDAS / REDUZIDAS, NÃO ESCONDIDAS

| Pendência | Gravidade editorial | Tratamento atual |
|---|---|---|
| 900 variantes da expansão derivam de somente 90 mecanismos e poucas fórmulas gerais | ALTA | `worldroot/r26_magic_quality.py` marca risco `ALTO`; estreias dos Círculos VII–IX exigem individualização real antes de passar |
| Círculos menores das 900 magias ainda podem soar muito parecidos em livro | MÉDIA/ALTA | Escolher e personalizar antes de usar; nenhum índice garante espetáculo por si |
| Origem de CREATION e data real dos dragões | MISTÉRIO PROTEGIDO | Não resolvido por catálogo, pesquisa externa ou IA; requer pistas, contraprova e decisão narrativa |
| AERÚN dragão e Instituto AERÚN | IDENTIDADE CRÍTICA | Monitorado em prosa, com bloqueio de fusão categórica e aviso se ambíguo |
| História anterior D1–D528 não possui necessariamente os mesmos `canon/episodes` fechados | ALTA DE PROVENIÊNCIA | Validação falha em modo fechado se o arquivo antigo não puder ser provado; validação histórica especializada futura sem criar falsa comprovação |
| 25 perfis da memória e 10 feitos canônicos do índice representam só parte da saga | MÉDIA | Ler fonte literal ao introduzir, viajar ou atribuir poderes; não proclamar memória mundial completa |
| Nenhum teste Python mede literalmente emoção, humor, aura ou espetáculo real de leitores | INERENTE | Releitura autoral humana de um episódio real permanece necessária |
| Uma nova Parte v3 REAL pós-implantação não foi criada por esta auditoria | OPERACIONAL | O teste do pipeline é sintético, com escrita descartável. Não declarar novo episódio aprovado |

## 5. Segredos protegidos, com possibilidade de enredo

Fontes antigas confirmam AERÚN como dragão ancestral consciente e Guardião das Marés. **Não está provado** que existiu antes do mundo ou que sabe a origem da Autoridade. Seis fios de investigação podem ligar mitos marítimos, encontro com dragão, instrumentos de Miren e Astra, a Torre e Thaeron, perguntas ao Sistema e cosmologias de povos distantes, preservando autonomia de culturas e opiniões conflitantes.

Informações sobre Coração de Convergência e Arquitetos não constituem causa de CREATION; Coração redistribui energia recebida, e origem do Sistema e chegada de Lucas permanecem desconhecidas. Em nenhum momento da atualização foi criado mapa cosmológico definitivo.

## 6. Testes reais versus canonização

Trabalhar numa branch de código e testes NÃO atualiza `canon/HEAD.json`. No início e na revisão da fonte oficial, o estado era Livro VI, Capítulo 5, Parte IV, Dia 562, sequência 33. Este desenvolvimento não publica D563 nem atribui uma nova magia a qualquer personagem.

**Limite do verificador:** padrões linguísticos são heurísticos e dependem de revisão; podem exigir mais exemplos de linguagem para evitar falsos positivos e negativos. Um autor não deve criar o texto pensando em como "enganar" o auditor. Ele deve escrever a melhor ficção possível e usar o auditor para localizar problemas.

## 7. Referências consultadas (com diferenças de autoridade)

- `story-archive/editorial/audits/LVI-C05-PIII-D561-SISTEMA-THAERON-CAEDREN-CREATION-2026-11-22.json`: poderes distintos, origem ainda não comprovada.
- `story-archive/author-approvals/LVI-WORLD-BASELINE-V18.json`: GÊNESE plena e separação do Coração antigo.
- `story-archive/planning/book-vi/aerun-coracao-rede-arquitetos-revelacoes-v15-SIGILOSO-PROPOSTA.md`: pesquisa de Miren e Astra, com partes explicitamente propostas.
- `story-archive/planning/book-vi/povos-reinos-elencos-v12-PROPOSTA.md`: distinções geográficas/institucionais e dragão AERÚN.
- Google Drive: [CRÔNICAS — PROJETO DE SAGA v1.0](https://docs.google.com/document/d/1JZPraHBCwvTT3uR5TLAUYH_D5Vw6KF6LCv9b8HBXFh8/edit): AERÚN Guardião das Marés; demais hierarquias dracônicas não comprovadas.
- Google Drive: [Grandes Casas, Povos, Religiões e História v3.3](https://docs.google.com/document/d/1xGPus7iJTzYV4UJqcM5dIRpMQrvpa8k3pQkinsntDtI/edit): tradição e religião não provam cronologia cosmológica.
- Google Drive: [AERÚN CIDADE VIVA](https://docs.google.com/document/d/1sBZF2Hdpur0fd34cA6rDVTFnN_ZS2cQ9LaqF5Do8_WI/edit): Instituto de Miren e Astra e autonomia cívico-científica.

## 8. Critérios de aceite operacional

1. CI do PR com os 440 testes e demais regressões segue VERDE no SHA exato de merge.
2. Repositório `main` com novo código, revisão contra a PR e auditoria pública sem dados privados indevidos.
3. Workflows privados `worldroot-draft-inbox.yml` e `git-canon-cycle.yml` fixados em SHA exato da R26.2, não branch móvel.
4. Documento privado de decisão e sumário de riscos preservados na story-archive, SEM alterar canon HEAD, episódios ou escolhas.
5. Ao escrever o próximo episódio, o autor terá controle de descoberta e de escolhas; testes e registros de bastidor não aparecerão como diálogos, relatórios nem desculpas técnicas na ficção.
