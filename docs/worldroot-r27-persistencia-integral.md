# WORLDROOT R27 — Persistência integral obrigatória

**Aprovação autoral: 23/11/2026.** Recuperação após falha de arquivamento do Livro VI C06 Partes IV e V. Esta regra se aplica ao processo de escrita, não altera o cânone nem fatos narrativos anteriores.

## Contrato de execução por Parte

1. **Antes de narrar**, consultar o HEAD real em story-archive, RESUME, a Parte anterior arquivada, manifesto e recibo do leitor. Executar ou reproduzir a auditoria R27 com ID da Parte anterior e exigir status PREVIOUS_FULL_EPISODE_VERIFIED.
2. Se houve escolha real do autor, primeiro enviar choices/EPISODE/option-N.json, aguardar o workflow canônico e verificar avanço de HEAD, journal e SHA. O novo episódio deve ter a cronologia correta.
3. Criar a prosa completa com cenas vividas, diálogos, datas, checkpoint, cinco escolhas. Não substituir narrativa por resumo. Se for extensa, salvar segmentos literais em production/EPISODE/segments/ e reconstituí-los exatamente.
4. Criar inbox/EPISODE.json com full_text integral, prose prefixo exato, character_preflight, eventos ancorados em linhas, conhecimento temporal, revisões R25/R26. Invocar o conector GitHub realmente, não apenas afirmar que será salvo.
5. Aguardar worldroot-draft-inbox Action com sucesso e reabrir do GitHub manifesto, arquivo integral, SHA, delivery/reader_receipts e RESUME. Exigir auditorias worldroot.delivery_gate e worldroot.turn_continuity aprovadas.
6. **Somente então apresentar a Parte como concluída** e mostrar as cinco opções. Se faltar confirmação, estado BLOQUEADO; relatar sem prometer salvamento futuro ou inventar provas.
7. A Parte recém-gravada permanece draft integral até a **próxima escolha autoral**, que fecha a Parte anterior no cânone. O HEAD nunca deve saltar uma Parte.

## Estados

- EM_PRODUCAO: prosa e segmentos ainda sem recibo.
- ARQUIVADO_VERIFICADO: narrativa integral e recibo SHA reais, ainda rascunho.
- BLOQUEADO: nenhuma alegação de conclusão/novo capítulo se a fonte integral não existir.
- FECHADO_CANONICO: escolha posterior real, journal e HEAD verificados.

## Limite incontornável

O GitHub **não observa as mensagens do ChatGPT**. Não existe hook universal que salve automaticamente toda resposta. É obrigatório que o assistente invoque a ferramenta GitHub no turno da criação. O R27 impede uma entrega *quando invocado* sem arquivos; não garante que o conector será invocado espontaneamente. A política e os testes reforçam a sequência, não simulam uma integração inexistente.

## Testes e comando

Testes: python -m unittest discover -s tests -p test_turn_continuity.py -v

Antes da parte seguinte: python -m worldroot.turn_continuity --archive-root archive --previous-episode-id EPISODE_ID

Para confirmar fechamento do episódio anterior por escolha real, adicionar a opção --require-canon-promotion.

## Separação de responsabilidades

- main: motor executável, regras e regressões.
- story-archive: canon/HEAD.json **apenas estado canônico**, não configuração; a política fica em ops/ENGINE_PUBLISHING_POLICY.json.
- Actions: fixar uma versão imutável do motor de main que já passou nos testes; revalidar o recibo durante a gravação e o cânone durante a promoção.
