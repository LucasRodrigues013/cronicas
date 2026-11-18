# WORLDROOT — Contrato visual e literário de capítulo (UX r10)

**Diretriz expressa do autor — 18/11/2026.** A Parte III apresentou regressão visível de design em relação ao estilo aprovado. Este contrato rege a apresentação das próximas partes. Não reescreve eventos nem obras anteriores.

## Fontes efetivamente comparadas
- Exemplar rico: story-archive/episodes/LV-C15-PII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md — cabeçalho centralizado, hierarquia de títulos, epígrafe, calendário em painel, cenas cinematográficas com local/hora, diálogos destacados, checkpoint em painel e opções interativas.
- Regressão: story-archive/episodes/LV-C15-PIII-D529-AUTHOR-SOURCE/draft/narrativa_integral.md — sete cenas e diálogos presentes, mas texto em Markdown simples, nenhum painel ou controle de escolha, ausência de checkpoint visual.
- Direção autorizada no Drive: documento “PROMPT OFICIAL PARA NOVO CHAT · D528 → D529 · DESIGN E MOTOR PRESERVADOS”, seção 4. Os prints citados não estavam disponíveis para comparação pixel a pixel. Não afirmar fidelidade exata a imagens não inspecionadas.

## Linguagem visual obrigatória nas próximas partes
1. Identidade: selo CRÔNICAS DE UM NOVO MUNDO · WORLDROOT; Livro; Capítulo; Parte; título principal; epígrafe opcional. Centralizado, com hierarquia tipográfica elegante e moderada.
2. Calendário: painel separado e neutro “CALENDÁRIO DO HORIZONTE” com Dia acumulado, Ano/Mês/Dia e horário/local da retomada. Não fazer dashboard com números inventados.
3. Cenas: I, II, III etc.; títulos cinematográficos, timestamp e geografia precisos; prosa literária rica, cenas completas, humor, emoção e aventura. Não fragmentar frases artificialmente para simular profundidade.
4. Diálogos: nome do personagem destacado e travessão. Preservar vozes singulares e autonomia de Miren, Kael, Lysa, Brannik, Káiron, Varo, NÓX e SISTEMA; não reduzir ninguém a figurante.
5. Checkpoint: bloco WORLDROOT separado **depois da prosa, antes das escolhas**, apenas fatos confirmados, situação atual, pendências e segredos conhecidos por quem. Nunca apresentar dados de bastidores como conhecimento geral.
6. Cinco escolhas: 1–3 alternativas significativas; 4 ESPECIAL visualmente distinguível; 5 AÇÃO LIVRE com campo e envio funcional. Controles reais, não botões decorativos. Alternativa textual sempre compreensível.
7. Estética: caixas discretas, bordas neutras, espaços confortáveis, separadores sutis; sem excesso de cor, badges decorativos, imagens, planilhas, cards repetitivos ou técnicas de dashboard no corpo narrativo.

## Classificação técnica
A fonte versionada é “worldroot/presentation_policy.json”, regras UX01–UX12, com níveis OBRIGATORIO / PREFERENCIAL / PROIBIDO. “worldroot/presentation_guard.py” testa, em tempo linear, a presença do cabeçalho rico, painel de calendário, checkpoint, ordem final, opções e controles funcionais. “worldroot/draft_inbox.py” aplica o gate a **novos capítulos**. Episódios antigos permanecem imutáveis: um reprocessamento idempotente não poderá adulterar a Parte III existente.

A validação estrutural não mede qualidade literária, não garante renderização fiel e não substitui conferência visual do chat. Não inventar conteúdo de screenshots; quando houver material acessível, complementar o contrato com evidência explícita.

## Pipeline de execução
Consultar o HEAD e CONTEXT reais; resgatar contexto literário e a referência rica; criar cenas e conteúdo visual sem imagens; revisar no chat; executar presentation_preflight(full_text) para a estrutura visível (não só a prosa); executar quick_preflight(prose) para estilo; registrar eventos com evidência; arquivar a parte via inbox GitHub e verificar readback. Nenhum ponto altera a regra de escolha real -> fechamento canônico anterior -> nova parte em rascunho.

**Regressão obrigatória:** python -m unittest discover -s tests -v. Um caso rico passa; um caso simples no estilo da regressão da Parte III é bloqueado. Teste verde não significa pixel-perfect nem homologação humana da narrativa.
