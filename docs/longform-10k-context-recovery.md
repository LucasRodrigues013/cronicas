# WORLDROOT r14 — Longform 10 mil palavras e retomada por evidência

**Decisão do autor, 18/11/2026.** As partes precisam voltar à profundidade da referência Livro V C15 Parte II, preferencialmente alcançando cerca de dez mil palavras de **prosa narrativa**, sem contar interface. O pedido também identifica a necessidade de maior precisão na recuperação do contexto. Não tratar a hipótese como prova de falha técnica de memória: foram verificadas compressão de cenas e ausência de alvo operacional de extensão.

## Auditoria literal (18/11/2026)

Arquivos imutáveis e privados lidos diretamente de story-archive:
- C15 Parte II D529: cerca de 10.046 palavras no arquivo total; cerca de 9.417 no campo prose bruto (alguns elementos estruturais inclusos). Nove cenas, referência aprovada de densidade.
- C16 Parte I D532: cerca de 7.114 palavras de arquivo, nove cenas.
- C16 Parte II D533: 7.652 palavras de arquivo, 6.778 no campo prose bruto, dez cenas.
- C16 Parte III D534: cerca de 7.496 palavras de arquivo, 6.602 no campo prose bruto, nove cenas. Cenas VI, IV e VII perto de 314, 483 e 506 palavras no corpo segmentado; as transições de núcleos são rápidas demais para uma cena central completamente vivida. Nem todas as cenas curtas são defeitos.

**Estado verificado antes desta alteração:** HEAD GitHub Livro V C16 Parte II, D533 17h29, FECHADO; Parte III D534 18h11 possui prosa literal e eventos candidatos em RASCUNHO. Nenhuma escolha da Parte III foi registrada nesta auditoria. Nunca promover draft só porque seu texto foi lido. Drive e Bases não sincronizam por GitHub.

## Critério de produção e limites

- **Meta:** 10.000 palavras aproximadamente **no conteúdo narrativo das cenas**, não no arquivo integral, no cabeçalho, no calendário, no checkpoint ou nas cinco escolhas.
- **Janela ideal:** 9.400–11.000 palavras de narrativa, com liberdade editorial; o validador avisa fora da janela.
- **Piso de segurança para novos capítulos completos:** 8.800 palavras efetivas de cena. Abaixo disso o arquivo novo é recusado, evitando declarar como episódio longo uma resposta truncada. Episódios já arquivados são imutáveis e seu readback idempotente não é reprovado retroativamente.
- **Não é garantia literária:** alcance numérico não confere nota de qualidade. Um texto repetitivo de 10 mil palavras pode ser ruim. O autor mantém controle de ritmo, decisões e qualquer futura exceção editorial à meta, sem retcon silencioso.

A fonte do guardião é worldroot/longform_depth.py. worldroot/draft_inbox.py roda o guardião antes de criar um novo draft, junto de UX, revisão de eventos e cronologia. A Action deve executar a versão da main fixada por SHA após CI.

## Como atingir 10 mil com ritmo sem enchimento

1. **Planejar experiência, não agenda:** escolher 1 eixo dramático principal vivido por Lucas; no máximo 1 arco de apoio relevante e um pulso de mundo que realmente mude uma relação ou consequência. Não precisa visitar todos os projetos.
2. **Cenas organicamente completas:** abertura sensorial e intenção, interação/atrito, surpresa ou revelação, reação emocional, escolha ou consequência. Diálogo com subtexto, humor próprio, GÊNESE sem nerf, Miren/NPCs com limites e desejos próprios.
3. **Peso variável:** cenas centrais podem ter 1.000–1.700 palavras, cenas de transição podem ser breves. Evitar nove cenas de 500 palavras somente para atravessar nove endereços. Não existe quota de cenas ou de horas, e um dia pode atravessar partes.
4. **Ritmo que respira:** permitir jornadas, deslocamentos, tarefas corriqueiras, romance e silêncio quando necessários; não resolver tudo por sumário. Evitar parágrafos repetitivos, diálogos sem avanço e descrições artificiais.
5. **Pré-entrega de qualidade:** inspecionar contagem de prosa, mediana e cenas curtas, foco em Lucas, coerência do relógio, conhecimento temporal, segredos, projetos, experiência dramática e UI rica. Corrigir problemas de causa; jamais copiar/colar prosa para bater a meta.

## Recuperação de memória em três níveis

**QUENTE — ler a cada retomada, com chamada real autenticada:** story-archive/canon/HEAD.json, canon/CONTEXT.json, última escolha registrada quando houver, último episódio FECHADO, e **o draft imediatamente pendente**: narrativa_integral.md ou episode_draft.json.prose, manifesto, checkpoint, opções e sidecars de eventos/conhecimento. Verificar SHA/readback e distinguir fato fechado de candidato. A Part III C16 é atualmente draft, não fato canônico.

**MORNO — ler somente o relevante à escolha da vez:** uma ou duas partes literais anteriores, fichas de personagens participantes e seus conhecimentos, mapas e deslocamentos, pendências e objetos necessários; evitar usar a base inteira como prompt. Recuperar falas e efeitos da última cena, não apenas o resumo do HEAD.

**FRIO — buscar com prova de fonte:** história anterior a D528 e episódios distantes via FTS5 do arquivo privado history/LITERAL_INDEX.sqlite. Busca por nomes, acontecimentos, datas ou objetos específicos; conferir linhas da fonte literal e autoria do trecho antes de declarar cânone. Não converter respostas STAGING de QA em fatos certificados.

Organizar um **cartão de continuidade** compacto e contextual, com episódio, relógio, localização, escolha real, 8–15 fatos de relevância, conhecimento por pessoa/horário, vínculos e conflitos ativos, perguntas abertas, última emoção e linguagem visual. Não confundir tamanho da memória recuperada com qualidade; o texto final deve ter espaço para as dez mil palavras.

## Produção quando a saída de uma resposta não comportar a obra completa

**Modo padrão:** uma Parte completa com cerca de 10 mil palavras de narrativa + interface/5 escolhas, se a capacidade real de resposta permitir.

**Modo seguro em duas ou três entregas conversacionais:** manter o MESMO episódio, sem criar Parte V artificial nem oferecer escolhas no meio. A primeira resposta conta cenas do mesmo capítulo, encerra com indicação textual de CONTINUA NESTA PARTE, e salva explicitamente o trecho imutável em story-archive/production/<episode_id>/segments/01.md pelo conector GitHub. Na próxima mensagem do usuário ("continuar esta parte"), recuperar o segmento literal por ferramenta, conferir sua SHA256, escrever e salvar o segmento 02 etc. Só na entrega final unir os segmentos exatamente sem sobreposição nem lacunas, executar o QA sobre a **prosa integral**, acrescentar checkpoint e cinco escolhas, e criar inbox da parte completa. A escolha do autor para a Parte seguinte só é solicitada ao terminar essa Parte.

**Importante:** não há execução automática em segundo plano nem hook mágico do chat. Cada gravação e readback exige ferramenta real. Se a primeira resposta for apenas parcial e o estágio GitHub não for gravado, não afirmar proteção de persistência. O schema opt-in do inbox aceita longform_segments como lista ordenada (2–6), com part=1..N, path padrão production/<episode_id>/segments/01.md etc. e sha256 por segmento. worldroot/longform_segments.py valida arquivos e concatenação byte a byte antes de arquivar. Nenhum estágio avança HEAD; nenhum novo texto é canônico sem escolha real posterior.

## Critérios de aceite — próximos episódios

- Narrativa integral e visível, alvo 10 mil palavras reais, sem aparição de conteúdo resumido no lugar de cenas.
- História fiel à escolha do autor e ao último texto canônico, sem retcon, fuga de segredos ou nova limitação de GÊNESE.
- Design r10 com cinco escolhas **apenas no encerramento** da Parte completa.
- HEAD só avança após a escolha real e ação GitHub confirmada. Novo episódio permanece rascunho.
- Contagem verificável e recibo de QA, não notas fictícias de qualidade.
- Testes sintéticos verdes no CI; teste real do fluxo de capítulos em múltiplas mensagens depende de uso futuro com uma escolha real e stages salvos.

## Referências de código

worldroot/longform_depth.py — contagem e piso, inspeção de cenas, aviso de densidade.
worldroot/longform_segments.py — estágio opcional e integridade SHA256.
worldroot/story_focus_audit.py e day_arc_audit.py — sinais consultivos de foco e tempo.
worldroot/presentation_guard.py — UX.
worldroot/editorial_policy.json v5 — P26 e P27.
docs/instrucao-unica-projeto-chatgpt.md — instrução operacional de retomada atual.
