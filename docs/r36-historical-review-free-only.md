# R36 · Revisão histórica Free-Only

O GitHub privado é o registro dos lotes. A homologação roda em Bash com Git, Python 3.12, SQLite da biblioteca padrão, GNU `timeout` e `sha256sum`, em máquina autorizada. O fluxo preserva a sequência do Livro I de revisão com fontes, validação nativa, aprovação autoral, incorporação editorial e evidência de leitura do arquivo.

## Preparar e validar um lote

1. Comece pelo último checkpoint oficial em `audit/r36-semantic-reconciliation` e confira o commit de arquivo que ele referencia em `story-archive`. Use o cursor e os grupos do inventário desse checkpoint.
2. Registre o delta do lote, o validador `tools/r36_incremental_historical_review.py` e a solicitação `editorial/codex-staging/r36-native-review-request.json` no branch privado de revisão. A solicitação fixa os commits do motor, arquivo e checkpoint, os blobs de fonte, os hashes de transferência e os limites do lote. Use `READ_ONLY_CANDIDATE` com `production_hold: true`.
3. A partir de um checkout confiável que contenha este procedimento, execute `bash tools/r36_free_only_historical_review.sh <SHA_DO_COMMIT_DE_REVISAO>`. O SHA deve identificar a revisão conferida, pois o script executa código desse commit e do motor que ele fixa. Use acesso Git de leitura previamente configurado e um diretório temporário privado e sem sincronização.
4. O procedimento valida o candidato em worktrees isoladas, roda a regressão integral, verifica a restauração do arquivo de projeção SQLite e confere os quatro blobs de registro. Uma execução bem-sucedida deixa os recibos, os logs, os candidatos originais e o manifesto `SHA256SUMS` na pasta exibida pelo script. Guarde os originais em armazenamento privado até a incorporação.

## Registrar e incorporar

1. No branch privado de revisão, registre o recibo nativo, as evidências detalhadas, o log integral de regressão, o recibo de integridade e o manifesto SHA-256. Preserve os bytes dos recibos. Registre a aprovação autoral vinculada ao commit, ao hash do recibo e ao lote exato.
2. Antes da atualização remota, compare os caminhos do commit com os eventos, branches e filtros dos workflows aplicáveis. Registre os branches cobertos pela verificação das integrações do repositório, como o Cursor, e reutilize essa configuração nos lotes seguintes enquanto ela continuar aplicável. Revise a cobertura quando mudar um branch, workflow, integração ou regra de automação. Se um caminho de atualização puder disparar um runner hospedado ou serviço pago, pause o envio até resolver essa condição. O script realiza somente leituras GitHub e validação local. A rotina dispensa dispatch, runners e armazenamento de artefatos do Actions.
3. Após a aprovação, confira os hashes SHA-256 e Git Blob dos candidatos originais. Incorpore somente os quatro arquivos de registro aprovados em `story-archive`. Confirme no GitHub o commit de arquivo e os quatro blobs, além do HEAD narrativo e dos campos protegidos.
4. Registre o checkpoint em `audit/r36-semantic-reconciliation` com a referência ao arquivo confirmado, à aprovação e às evidências. Atualize o cursor histórico nesse checkpoint. Mantenha o bloqueio de produção, as reservas de certificação independente e o HEAD narrativo.
