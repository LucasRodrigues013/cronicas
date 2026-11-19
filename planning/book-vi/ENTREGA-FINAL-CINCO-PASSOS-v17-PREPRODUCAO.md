# ENTREGA CONSOLIDADA · CRÔNICAS DE UM NOVO MUNDO · LIVRO VI
## WORLDROOT r21 — ATLAS, POVOS, CIDADE VIVA, DOMINATO E ARQUITETOS
**Caderno executivo v17 | Data local: 18/11/2026 | Situação: PRÉ-PRODUÇÃO CONCLUÍDA NO NÍVEL DE DESENHO, PENDENTE RATIFICAÇÃO AUTORAL DE ELEMENTOS NOVOS.**
**NÃO É HISTÓRIA NARRADA. NÃO ALTERA CANON/HEAD.** Livro VI: **AS COROAS PARTIDAS**; saga **A ERA DAS NOVE COROAS**. Último estado canônico é Livro V fechado, Dia 537 às 23h46, id `LV-C16-PV-D537-AUTHOR-SOURCE`. O draft r17 da Parte I do Livro VI foi rejeitado pelo autor e permanece apenas para auditoria; 0 episódios aprovados.

### Resultado verificável

- Código `WORLDROOT r21` foi incorporado à `main` via PR #31, merge `e5535600950000403103945f6b0deaf4f79ed500`.
- Política `worldroot/editorial_policy.json` **v12 / 64 regras**; source S19 transcreve literalmente os cinco passos autorais; S20 registra C01 em 2–3 dias.
- CI da `main`: run #44439985268, **319 testes** em `validate-engine` e auditoria privada **7 testes** adicionais; run #44439985294, **319 testes** em `Safe public-code tests`; ambos SUCCESS.
- Gates de pré-produção `planning/book-vi/release-gates-v6-five-steps-research-audit.json` somam **50 verificações de fontes, hipóteses, cálculos, riscos e autorização**.
- `worldroot/bookvi_atlas.py` calcula rotas de grafo e tempos com rótulo obrigatório PROPOSTA, sem promover distâncias ao cânone. Espelhos numericamente verificáveis `worldroot/bookvi_atlas_PROPOSAL.json`, `worldroot/bookvi_dominato_PROPOSAL.json`.
- Google Drive foi CONSULTADO como fonte; nenhum documento foi editado.

## Passo 1 · ATLAS DE AVARENN E TRANSPORTE

**Âncoras canônicas:** Grande Avenida antiga **8 km**; Eixo Aurora **33,2 km** até Campo Aurora, incluindo **4,6 km** reaproveitados urbanos + **28,6 km** de corredor rural e cerca de **24 km** em reta; campus AERÚN **72 ha**; ARGOS voo005 alcançou **pico observado 1.462 km/h**, não cruzeiro certificado; comitiva de Três Arcos a Thalor percorreu **cerca de sete dias narrativos D423–D430**. Calderva é cidade costeira autônoma, com Casa **VARETH**, não Verath.

**Atlas PROPOSTO:** 18 localidades, 22 conexões de estradas e mar, coordenadas cartesianas relativas a Três Arcos; costa/posições sem certificação no mundo. Distâncias rodoviárias calculadas pelo grafo e tempos estimados de **carruagem 45 km/dia**, **caravana 28 km/dia**, **exército 22 km/dia**, **cavaleiro individual 48 km/dia**, **mensageiro com trocas de montaria 90 km/dia**. Ex.: Thalor **320 km / 7,1 dias**, Calderva **545 km / 12,1 dias**, Grande Torre Vélath **470 km / 10,4 dias**.

**ARGOS — hipótese operacional, não medição:** partida efetiva de **Campo Aurora**, cruzeiro usado para orçar **450 km/h**, desvio de rota de **12%**, mais 30min de operações. Até Thalor **71min**, Calderva **99min**, Vélath **83min** de bloco aéreo. **Não inclui deslocamento da cidade até Campo Aurora, espera, autorização nem aeroporto no destino**. Só o trecho Três Arcos→Campo via expresso futuro é planejado em cerca de **66–75min**. Sem pouso externo confirmado, os tempos são de voos hipotéticos/expedições, não serviços comerciais.

**Transporte municipal após criação:** VLT pela Grande Avenida **8km/~20min**; extremo da cidade antiga ao novo distrito **~16km/~40–48min**; Casa Cívica→AERÚN **~7km/~18–24min**; expresso Casa Cívica→Campo **33,2km/~66–75min**. Frota de **96 ônibus e 24 composições VLT** é PROPOSTA, não veículo existente em D537. Antigos 2 coletivos de 12 lugares D522 não equivalem a frota moderna já ativa. A rede de portais só afetará tempos depois de criada e autorizada, jamais retroativamente.

**Fontes externas de comparação verificadas**: Textron Grand Caravan EX cruzeiro máximo **343km/h**, https://cessna.txtav.com/en/turboprop/grand-caravan-ex ; Pilatus PC-12 PRO **537km/h**, https://www.pilatus-aircraft.com/en/pc-12 ; FHWA desempenho de transporte sobre trilhos e velocidades comerciais, https://www.fhwa.dot.gov/policy/23cpr/chap4.cfm ; estudo histórico de marcha e logística bizantina, https://deremilitari.org/2014/05/the-organisation-and-support-of-an-expeditionary-force-manpower-and-logistics-in-the-middle-byzantine-period/ . **Esses números reais NÃO limitam a magia de ARGOS nem demonstram o cruzeiro dele.**

**Arquivos-mestre:** `atlas-avaren-geografia-rotas-v11-PROPOSTA.json`; `atlas-avaren-visual-v11-PROPOSTA.svg`; `atlas-avaren-livro-rotas-e-transporte-v11-PROPOSTA.md`; API `main:worldroot/bookvi_atlas.py`.

## Passo 2 · REINOS, POVOS, CULTURAS E ELENCO

**Reaproveitar e não apagar** as Grandes Casas de bastidores v3.3: Morcant, Belvann, Auristel, Khorad, Haruin, Sennari, Nemareth, Valcer e Liga das Sete Quilhas, além de Khelen/Namaris/Orúndia/Selkara. Cada nome vem marcado como [EXISTENTE], [BASTIDOR] ou [NOVO]; não promover [NOVO] a memória de Lucas.

**Thalor** — Reino formal da rainha Althea; Caedren herói livre, não subordinado automático. **Vélath** — Grande Torre sob Thaeron e estudiosos, não declarar que já tem rei. **Calderva** — Cidade Livre marítima, Casa VARETH, Selda, Círan, Lira, Aeldric, Serenna, Yra e Nárei; não trono Vareth nem província imperial. **Anões** — casas/forjas de Kharum, Tharvek como candidato de pré-produção, diversidade de artesãs, juristas, agricultores, músicos. **Elfos** — Elyrien candidata, comunidades e conselhos autônomos, botânica, ciência, diferenças internas. **Orcs** — várias confederações, não um imperador racial; pastoreio, canto e legislação comunitária. **Khelen** — povo mineral consciente e cultura própria, não autômatos. **Seral/Halvern/Arvendell/Veyra** — regiões com histórias locais; nenhum governante inventado como fato.

**Heróis/figuras novas exemplares [NOVO]**: capitã Yrken Uld (gargantas anãs), Senira Esh (ressonância élfica), Kargan Vel-Uth e Hessa Murn (direitos e cura de clãs orcs), capitã Haredi Vossel (escolta marítima). Todos têm objetivo, contradição, poder, modo de falar e relações próprias; aparição depende de cena escrita.

**Arquivo:** `povos-reinos-elencos-v12-PROPOSTA.md`.

## Passo 3 · TRÊS ARCOS AVANÇA EM VELOCIDADE, NÃO POR BUROCRACIA

**C01, cinco partes, D538–D540 PROPOSTOS**: Lucas acorda, corre e observa cidade, recorda Terra, café e conversa com Miren → visita Kael/Lysa/conselho → reforma centro histórico e crea distrito novo → Costura de Dados passa de vídeo regional D533 a rede urbana de antenas/quiosques/alertas e transporte público 24h → inauguram cidade viva e anunciam oportunidades. **Dois/três dias são ritmo de cenas, não limite de GÊNESE**.

**Projeto de distrito:** área 15km², capacidade 100.000 habitantes, ~40mil moradias, parque central 160ha, fachadas renascentistas fantásticas e redes modernas invisíveis. Cidade antiga também é restaurada, não apagada; há saúde, água, esgoto, resíduos, energia, escolas, galerias, pontes, teatros e comércio.

**Malha Aurora:** 3.600 autômatos operacionais existentes D531, Vértice técnico; Rumo separado. Nova coorte de 1.500 unidades + frotas 96 ônibus/24 VLT são novas obras POSSÍVEIS, não canon. Kael dirige segurança/corredores/socorro, Lysa acolhimento/educação/serviços, Conselho e profissionais agem autonomamente; Miranda não é prefeita da cidade e Miren não vira sua funcionária.

**AERÚN** (instituição científica sob Miren/Astra) pesquisa Arquitetos, saúde, mapas, magia e educa novas equipes. **Forja Aurora** sob seus mestres e profissionais desenvolve transporte, autômatos, peças, arquitetura e ARGOS, depois colabora no LEVIATÃ. A cidade se enche de profissões e famílias que chegam POR VIAGEM/CONVITES; capacidade inicial não é ocupação inicial. A entidade dragão ancestral AERÚN mantém identidade separada da instituição de mesmo nome.

**Arquivo:** `tres-arcos-evolucao-rapida-aerun-forja-v13-PROPOSTA.md`.

## Passo 4 · VELKAR, AS NOVE COROAS E COMBATES DE ALTA FANTASIA

**Cenário imperial de PREPRODUÇÃO (não valor já observado):** NOVE lordes territoriais vassalos com 32,4 milhões de habitantes, mais 9,6 milhões no coração imperial = **42 milhões**; **260 mil efetivos permanentes + 190 mil reservistas = 450 mil mobilizáveis no papel**; a marinha de Varkhess tem **520 cascos** (30 grandes, 100 fragatas, 140 escoltas, 250 transportes), tripulação nominal 45.100 e cerca de 45mil marinheiros permanentes, diferença 100 por escala arredondada. O corpo arcano de 20 mil já está **DENTRO** dos 260 mil, não é bônus. Exército fixo terrestre 160mil; reconhecimento 15mil, engenheiros/guarnição 20mil. Não deslocar todos ao continente atual instantaneamente.

**Divisão existente de bastidores:** Velkar Draen inteligência imperial; Orelia Voss negociações, tratados e guerras de informação; Rhazek Korr campo/cerco; Serakh Il-Varenn rituais arcanos e contenção; Varkhess Serev frota e marés; seis subgenerais distribuídos nas três frentes. Novos nomes de nove lordes são *propostas* em `nine-crowns-vassal-lords-v8-PROPOSTA.md`, não fatos narrados. Outras aeronaves militares (6 barcaças,18 planadores,120 balões/plataformas) são somente TECH TREE proposta e não prova de que Velkar possui supersônicos.

**Como Velkar age de modo inteligente:** conquista pelo controle de pedágios, guarnições, produção, canais de comunicação, legitimidade e tributos; garante benefícios a parte das províncias, acumula ressentimento em outras, faz alianças e obtém informações por meios reais, com tempos de correio e perdas. Os vassalos não são nove cópias de vilão. O império domina ESTREITOS/ARMADAS/FRONTEIRAS, mas não possui alcance físico gratuito sobre toda Avarenn.

**Set pieces propostos, sem resultado fixado:** batalha anã nos desfiladeiros e forjas; defesa mágica élfica de raiz e cântico; perseguição à comitiva Tharvek/Elyrien por Ithran com Sombras/Varo capazes; batalha naval por Calderva contra Varkhess/Morvek; campanha multifrentes dos generais e nove coroas. O livro privilegia **confrontos militares visualmente ricos**, resgates, guerreiros com autonomia e riscos reais, sem reduzir GÊNESE para salvar antagonista.

**Arquivos:** `dominato-escala-militar-v14-PROPOSTA.json`, `dominato-forcas-generais-batalhas-v14-PROPOSTA.md`, `nine-crowns-vassal-lords-v8-PROPOSTA.md`.

## Passo 5 · AERÚN E OS ARQUITETOS, A GRANDE DESCOBERTA EM PARALELO

**CANON CONFIRMADO (história antiga):** Coração de Convergência sob Três Arcos está SELADO; ensaio periférico comprovou fluxo residual. A engenheira ancestral Tessa Arin documentou que Coração **recebe e redistribui mana; NÃO a gera infinitamente**, com canais residenciais isolados. Há Unidades A/B/C, nó secundário de VALIDAÇÃO já encontrado em investigação, e componentes Observação/Forma/Vínculo. ARQUIVO DAS MARÉS é instalação exterior de localização desconhecida, não comprovadamente em Calderva. Talis continua desaparecida no cânone.

**SEGREDOS NOVOS DE PRODUÇÃO A INVESTIGAR EM CENA:** hipótese de `Rede dos Meridianos Vivos` como arquitetura ancestral de energia, sinais e comunicação interurbana; possíveis corredores de travessia emparelhados, **não demonstrados canonicamente**; `Chave de Conferência dos Meridianos` hipotética para reconstituir validador ausente, **não requisito da GÊNESE**; causa proposta do isolamento: tentativa de reconexão sem validação secundária gerou risco aos canais civis, com Tessa interrompendo a rede. O arquivo exterior pode conter confirmação, outra estação e mapas perdidos, mas deverá ser ENCONTRADO por investigação/viagem de verdade. Nenhuma dessas hipóteses autoriza retcon de conhecimento de Miren.

**Cadência planejada:** C01 retoma perguntas e testes de campo em paralelo a Lucas, C02–10 diferencia medidas, protocolos e mapas, C11–15 descobre referências externas, C16–20 chega a uma resposta documentada sobre função/isolamento do Coração e talvez Arquivo das Marés; C21–30 integra benefícios e avança grandes mistérios. Isto não exige esconder informação sem motivo nem inventar fonte mágica que revela tudo a qualquer momento. AERÚN e Forja podem criar equipamento novo pela GÊNESE, mas a VERDADE histórica é objeto de prova.

**Conexão LEVIATÃ/PORTAIS:** Portais entre cidades são CRIAÇÃO NOVA de Lucas, com acordos civis entre os destinos, não comprovação automática de portal antigo. O LEVIATÃ passa à META de construção coletiva com Calderva/Forja no MEIO do Livro VI (janela editorial C11–15) se personagens e autor escolherem, **não o clímax**, a travessia do outro continente fica para Livro VII. ARGOS mantém relevância como expedição/exploração e fonte de informação.

**Arquivo reservado:** `aerun-coracao-rede-arquitetos-revelacoes-v15-SIGILOSO-PROPOSTA.md`.

## Mapa de capítulos e aceite

- `mapa-30-capitulos-epico-cinco-passos-v16-PROPOSTA.md` — 30 capítulos e 150 partes em seis movimentos é **MAPA REVOGÁVEL**, não roteiro de resultado fechado.
- C01 urbanismo/sci; C02–05 emissários/soldados; C06–10 Calderva/portais/batalhas; C11–15 LEVIATÃ/Conclave/ciência; C16–20 culturas/AERÚN/Arquivo; C21–25 generais/grandes batalhas; C26–30 Nove Coroas/confronto/pós-guerra. Cada parte abrange apenas UM DIA calendário, com dias repetidos quando necessário.
- **QUALIDADE DO LIVRO:** cenas completas, humor Lucas, amor Miren, escolhas 1–3+4 especial+5 livre, ARGOS voa, poder de GÊNESE livre, antagonistas competentes mas derrotáveis, conquistas perduram, Talis encontrada neste livro de modo investigado.

**Pendências HONESTAS antes de promover à história:** (a) ratificação autoral das coordenadas/costa e do mapa das distâncias; (b) aprovação dos nove nomes/cidades/populações/tecnologia aérea de Velkar, ou revisão; (c) nomes/fichas novos e culturas ficam candidatos até cena; (d) metodologia científica e explicação final do Coração ainda H-I-P-Ó-T-E-S-E; (e) portais/LEVIATÃ requerem decisões de Lucas/personagens e autorização de narração; (f) pista Campo Aurora e autorizações de pouso fora da cidade ainda não comprovadas; (g) equipe humana, população atual e densidade antiga não mensurados. Nenhuma lacuna justifica enfraquecer GÊNESE.

**VEREDITO:** o **projeto de planejamento em cinco passos está DOCUMENTADO, TESTADO e UTILIZÁVEL para construir a história** com fonte de verdade clara; o **atlas métrico e novos fatos do mundo NÃO ESTÃO CANONIZADOS** porque o usuário ainda precisa aprová-los. Não declarar a pré-produção 100% factual sem essas confirmações, e não iniciar a Parte I sem comando explícito.
