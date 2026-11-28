# WORLDROOT Literary Edition — Livro I
Status: contrato editorial aprovado em 2026-11-28; implementação inicial, não homologada.
Escopo: adaptação literária expandida, NÃO CANÔNICA para o RPG. Não é uma nova campanha nem uma continuação.

## Isolamento e fontes
- Branch exclusiva: literary-edition/book-i. Todo conteúdo novo fica sob literary-edition/.
- Base do motor (snapshot de main): 1b063d05c1acaa86b2f237f987804af59dbeccd6.
- Snapshot de leitura do arquivo original: story-archive @ 9dd632fb0bcd84dfce5b631013fdc67d7492ac5d. O arquivo é somente leitura para esta edição. Atualizações da fonte requerem comparação e novo pin explícito.
- Proibido publicar no RPG, alterar HEAD/RESUME, escolhas, estados, fichas, overlays, políticas, poderes, workflows, main ou story-archive. Não abrir PR de integração editorial nessas branches.
- Reutilizar recuperação histórica, evidência temporal, caracterização, revisão literária, causalidade e políticas existentes como ferramentas consultivas. Não usar publicação/ratificação de episódios nem importar fatos editoriais para o motor ativo. ChatGPT + GitHub, sem APIs pagas ou execução local exigida. Esta fundação não é um runtime integrado testado.
- Cânone RPG: fonte literal e escolha aprovada prevalecem sobre resumos, planos, candidatos e inferências. Não misturar com Eidoryn.

## Contrato autoral
Título: Crônicas de um Novo Mundo — Livro I: O Despertar do Criador.
Faixa de 120.000–150.000 palavras, aproximadamente 480–600 páginas; cinco atos, prólogo e cerca de 38 capítulos (contagem flexível). Metas incluem o prólogo.
Atos: I O nascimento do Criador (16–20 mil); II O preço da primeira vitória (20–25 mil); III A Legião que escolheu existir (24–30 mil); IV As fundações de uma nação (28–35 mil); V O legado dos trezentos (30–38 mil); prólogo (~2 mil). Fronteiras de eventos e desfecho sujeitos à reconciliação, sem impor cortes artificiais.
Terceira pessoa próxima de Lucas; perspectivas paralelas controladas; fantasia épica, isekai, aventura, LitRPG, progressão, construção de civilizações, drama, romance, humor, maravilhamento, exploração e mundo autônomo. Prosa contínua, diálogo natural, batalhas com emoção e consequências; sem menus de escolhas para leitor. Não antecipar a GÊNESE madura, não nerfar poderes, não transformar Lucas em onisciente.
Preservar acontecimentos e resultados do RPG como espinha dorsal. Expandir livremente cenas, interioridade, diálogos, cultura, vida cotidiana, conflitos paralelos e lacunas sob continuidade editorial; não substituir fatos do RPG. Mudança de resultado ou fato fundamental requer aprovação autoral expressa e fica somente na edição literária.

## Direção autoral para a abertura
Prólogo intenso: Lucas adulto em escritório na Terra, fones, cotidiano; morte em incidente (roubo seguido de ferimento fatal é uma alternativa autorizada); socorro/hospital; passagem. Em paralelo, batalha desproporcional em outro mundo, perspectiva anônima, dimensão da ameaça sem revelar personagens, identidades ou mistérios futuros. Uma pessoa pronuncia CREATION; convergência com a morte de Lucas; Sistema oferece cinco opções; Lucas escolhe CREATION. Chegada ao vale. Primeiros 300 orcs visíveis, memória do filme 300 (Esparta, visto na semana), decisão de criar 300 guerreiros de elite. A contagem inicial é expansão autoral; fonte histórica posterior descreve quase mil orcs no confronto total: tratar 300 como primeira força avistada, sem confirmar composição total até revisão. As cinco opções históricas registradas na preparação são Meteor, Time Stop, Dragon Lord, Creation, Infinite Treasury; apresentação original, sem copiar cenas externas. Nomeação final comercial sujeita a revisão de originalidade. Não usar nome de empregador real, detalhes biográficos privados ou copiar diálogos/estrutura de Tensura. A ligação entre a voz anônima e a passagem é premissa literária, não uma explicação cosmológica estabelecida.

## Processo de edição por capítulo
1. Recuperar as fontes fixadas e as escolhas reais; mapear lacunas e incertezas.
2. Preparar cenas e pontos de vista com registro de evidência.
3. Escrever prosa e marcar internamente elementos RPG_LITERAL, RPG_RECONCILED, AUTHOR_EXPANSION ou EDITORIAL_DRAFT. Tais rótulos não aparecem no livro.
4. Revisar causalidade, cronologia, geografia, identidade, limites de conhecimento, evolução de poder, ritmo, voz, emoção, originalidade e consequências.
5. Avaliação editorial em passagem separada; nota-alvo >9, não certificação automática. Bloquear contradições não autorizadas; preservar versões e decisão autoral. Aprovação literária nunca implica ratificação RPG.
6. Gerar formatos comerciais somente após revisão do manuscrito completo e verificação de originalidade/direitos da inspiração inicial.

## Evidências iniciais
- history/INDEX_SUMMARY.json (6 fontes, 4626 chunks, 13.928.807 bytes; intervalos nominais D001–D528, não homologação integral).
- history/sources/01_DIA_001_A_383_FONTE_LITERAL.txt.part-001, blob d64d5db0e33a1c0a6a6a6d14a8be44709a3bbac2: consolidação das 25 imagens, CREATION, 300, batalha, chefe orc vivo, 5%, armadura, mochila; capítulos 1 e 2.
- editorial/codex-staging/r35-book-i-reconciliation-cycle-01-v4.json: revisão parcial, não homologada.
- Capturas de tela originais da reencarnação e combate ainda precisam de recuperação/conferência para alegações de fidelidade literal.
- Prólogo e chegada são expansão autorizada; detalhes concretos de prosa permanecem rascunho para leitura do autor.
