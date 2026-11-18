# WORLDROOT r8 — ciclo recuperável SEM Google OIDC

## Estado de execução

O GitHub privado substitui **somente o HEAD operacional para novos episódios** durante a fase sem OIDC. O Google Drive original, suas fichas e o HEAD de D528 ficam preservados e **não são atualizados automaticamente por Actions**. Isso evita alegar uma sincronização que não existe. Uma futura reconciliação exige autenticação Google independente e readback.

O repositório privado possui duas branches complementares:

- \`main\`: código Python, regressão, contratos narrativos, ferramentas de restauração. Nenhum episódio privado deve ser copiado para a branch de código.
- \`story-archive\`: texto integral dos capítulos, opções e manifestos SHA256, decisões explícitas, \`canon/HEAD.json\`, \`canon/state.sqlite\`, \`canon/CONTEXT.json\` e \`canon/episodes/*.json\`. Cada fechamento é um único commit Git que contém os quatro artefatos atualizados.

A versão mais recente do código é implementada em \`worldroot/git_cycle.py\`. Não existe servidor fixo; o runner do GitHub Actions é efêmero. **Persistência** significa arquivos versionados no Git, replay verificável do journal e backup/restauração SQLite.

## Fluxo com uma escolha do autor

1. **Antes da escolha**, o texto integral da parte anterior, os cinco caminhos, os JSON laterais e o manifesto imutável já estão em \`story-archive/episodes/<id>/draft/\`. Esse pacote existe para D529 Parte II.
2. **Revisão antes de fechar**: \`review/eventos_revisados.json\` e \`review/conhecimento_revisado.json\` têm candidatos revisados, SHA do texto, linhas, status NARRADO, horário e visibilidade. Esses arquivos não são eventos canônicos até uma escolha efetiva.
3. Quando o autor diz \`Opção 4\` no ChatGPT, o conector GitHub deve **criar (nunca substituir)** \`choices/<id>/option-4.json\`, usando \`author_source: USER_MESSAGE\`. Nunca inferir escolhas de exemplos do modelo.
4. O Action \`.github/workflows/git-canon-cycle.yml\` no \`story-archive\` valida novamente o pacote, a escolha, cronologia, evidência e conhecimento; restaura/verifica SQLite e fecha o episódio com commit único (\`HEAD.json\`, \`state.sqlite\`, \`CONTEXT.json\`, \`episodes/<id>.json\`). \`GITHUB_TOKEN\` com \`contents:write\` **somente** neste workflow privado e revisado; nenhum segredo Google.
5. ChatGPT consulta o novo HEAD e o CONTEXT, e somente então escreve a próxima parte. A próxima parte deve ter prosa integral, as cinco opções e manifesto imutável arquivados via conector GitHub **antes** de dizer que ficou salva. A nova parte fica RASCUNHO até a seguinte escolha.

Esse ciclo é acionado por uma **chamada explícita** do ChatGPT ao conector; um prompt em GitHub não instala um hook invisível de fim de mensagem no ChatGPT. **GitHub Actions não gera prosa com GPT automaticamente** sem um runtime/modelo autenticado. A criação literária acontece no turno ativo do ChatGPT.

## Gatilhos e falhas

- \`canon/BOOTSTRAP_REQUEST.json\`: primeiro push em \`story-archive\` instancia SQLite e HEAD GitHub em **D528, C15, Parte I**. Confere bytes da fonte literal e o Git blob SHA da cópia histórica. Não avança Drive, não narra D529 nem promove o rascunho.
- \`choices/*/option-*.json\`: Action tenta fechar a escolha. Se faltar revisão, houver divergência de SHA, salto temporal, escolha repetida contraditória ou erro de SQLite, o job falha **antes do commit**, mantendo o HEAD GitHub anterior.
- \`GITHUB_TOKEN\` que faz commit não gera novo workflow de \`push\` automaticamente. Todo fechamento cabe no mesmo job; nenhum encadeamento ilusório.
- A origem do autor na mensagem é atestada pelo conector ChatGPT. O campo JSON isolado não prova identidade. GitHub deve restringir quem escreve no repositório/branch.
- \`git push\` é compare-and-swap via fast-forward: se o archive avançar enquanto um fechamento roda, o push é rejeitado; nova execução precisa recuperar o HEAD atualizado, nunca aplicar um force-push.
- O replay \`python -m worldroot.git_cycle restore --archive-root archive\` reconstrói \`state.sqlite\` por \`canon/episodes/*.json\` e a fonte D528. Verificação: \`python -m worldroot.git_cycle verify --archive-root archive\`.
- O índice legível \`canon/CONTEXT.json\` é **derivado** do SQLite: eventos narrados com proveniência e conhecimento temporal individual. Não confundir conhecimento de bastidores com conhecimento universal. O histórico anterior a D528 continua consultável no Drive e em seu índice v4.3 e precisa de reconciliação gradual.

## Habilitação final e restrições

[ ] Proteger \`main\` e \`story-archive\` contra pushes externos; permitir somente autor e bot necessário, configurar branch rulesets sem bloquear o próprio runner.
[ ] Confirmar permissões Actions que autorizem \`GITHUB_TOKEN\` escrever no \`story-archive\`.
[ ] Validar bootstrap real com leitura de retorno do commit e SQLite, seguido de restauração ensaiada.
[ ] Executar fechamento real somente após próxima escolha autoral (D529 Parte II ainda aguardando).
[ ] Confirmar que o ChatGPT consegue arquivar a próxima parte por chamadas reais ao GitHub; sem hook de fim de mensagem, o passo é explícito no turno.
[ ] Quando for possível, sincronizar Drive/Base Viva/Atlas por operação autenticada separada, sem preencher o HEAD do Drive com dados não homologados.

## Segurança e custos

Repositório privado não equivale a criptografia ponta a ponta. Pessoas com permissão de leitura podem acessar episódios e snapshots. Não registrar tokens, segredos, dados pessoais não relacionados ou prosa nos logs. \`contents:write\` é necessário apenas ao Action de fechamento; todo outro Actions deve continuar \`contents:read\`. Minutos do Actions e armazenamento Git podem variar segundo o plano; acompanhar faturamento e tamanho dos snapshots.

Fontes:
- https://docs.github.com/en/actions/concepts/security/github_token
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/reference/security/secure-use
- https://www.sqlite.org/backup.html
