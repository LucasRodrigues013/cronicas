# WORLDROOT r9 — pesquisa literal histórica D001–D528, Drive → GitHub → SQLite FTS5

## O que foi verificado

Foram encontrados e lidos seis arquivos originais do Google Drive, exportações de conversas em TXT. Os nomes indicam intervalos D001–D383, D383–D431, D431–D457, D457–D469, D469–D496 e D497–D528. Os arquivos juntos somam 13.928.807 bytes. Os SHA-256 da cópia integral original foram verificados antes de aceitar o conteúdo; nenhum trecho foi resumido, editado ou deduplicado na origem.

Cada arquivo tem ID próprio no Drive. A cópia binária é versionada em **GitHub privado**, no branch \`story-archive/history/sources/\`, com inventário \`MANIFEST.json\`. O maior documento é armazenado como seis blocos de transporte: a reconstrução valida o SHA-1 de cada bloco Git e o SHA-256 do texto completo. A estrutura é intencionalmente privada, pois contém conversas literais.

| Nome | ID de origem Google Drive | Bytes | SHA-256 |
|---|---|---:|---|
| 01_DIA_001_A_383_FONTE_LITERAL.txt | 1TWkRZxskK2FnZE9UmuW0M5JDIjSl-7nK | 6.823.025 | bb43d493ef3c28391345af7cd319e62af2f99f4f51b417bebb129fad6786cc4b |
| 02_DIA_383_A_431_FONTE_LITERAL.txt | 1w-SbTdpDkXtwYDME8n3j9vwI8mCJzqGa | 1.720.637 | 468635338ce16b22fb9216589ea6c572597d313da70cae7b9e9c08b5689afb81 |
| 03_DIA_431_A_457_FONTE_LITERAL.txt | 17-rCCbdTCEmtes2b-I31juDDAVZtg3iH | 724.105 | c03918eac20e57762d4f182f6cf3e8562357e0942476369730773484ab46b242 |
| 04_DIA_457_A_469_FONTE_LITERAL.txt | 1bkwWc2LdaEEhm61wzD1XoBvft3wBHwja | 1.720.345 | 34de2eb03be4e10b829c125498c52b9f425d92946d62c958ac62e22057a1fa86 |
| 05_DIA_469_A_496_FONTE_LITERAL.txt | 1vdHyqLGxk5Qk06tFMOyfZ-h1iGwDmbb1 | 637.439 | 4162351007e7ccaaa22964d91cda7e0feba82aea48752a09522b9731a68f4385 |
| 06_DIA_497_A_528_FONTE_LITERAL.txt | 1ElwaEIZcQxTy4OhV2d5e_KF1AkaNsKdi | 2.303.256 | 9e09d84f6c80de7c81fbf3b4f3aa6edf4fc649801c80d25247668ba1c61b8ecd |

## Arquitetura de recuperação

**Motor aprovado:** \`main/worldroot/history_index.py\`.
**Fonte literal:** \`story-archive/history/sources/\`, versionada e imutável.
**Banco DERIVADO:** \`story-archive/history/LITERAL_INDEX.sqlite\`, FTS5 + mapa de trechos.
**Metadados públicos do índice (sem prosa):** \`story-archive/history/INDEX_SUMMARY.json\`.
**Cânone independente:** \`story-archive/canon/HEAD.json\` e \`canon/state.sqlite\`. **Nunca sobrescrever ambos a partir do índice textual.**

O banco de busca contém: documento fonte, link do Drive, SHA256, tamanho, intervalo NOMINAL do título, número de linha inicial/final de cada trecho, papel no export (\`AUTHOR_PROMPT\`, \`ASSISTANT_RESPONSE\` ou \`EXPORT_METADATA\`), texto literal e marcações de dia *mencionadas*, não certificadas.

Exemplo de consulta no runner/local com arquivos privados já autorizados:

\`\`\`bash
python -m worldroot.history_index build --archive-root story-archive
python -m worldroot.history_index verify --archive-root story-archive
python -m worldroot.history_index search --archive-root story-archive --query "Káiron Miren" --limit 6
python -m worldroot.history_index search --archive-root story-archive --query "ARGOS voo" --day-hint 528
\`\`\`

Sem shell local, a integração ChatGPT pode criar uma solicitação \`history/requests/<id>.json\` com \`{"schema":"worldroot-literal-search-request-v1","author_source":"USER_MESSAGE","query":"termo","limit":6}\` no \`story-archive\`. O Action privado \`.github/workflows/worldroot-history-index.yml\` procura fontes, valida hashes, recompõe o SQLite caso necessário, responde em \`history/results/<id>.json\` e grava o resultado no mesmo commit do banco. Lê-se o resultado via conector GitHub antes de afirmar que uma evidência foi encontrada.

Os arquivos de resultados exibem **apenas fragmentos**, sempre com fonte e linhas; para tomar decisões narrativas importantes, revisar o texto integral original. Busca não executa capítulos nem corrige o passado. O módulo é idempotente: manifestos idênticos não provocam reconstrução desnecessária, e a perda do SQLite é recuperável pelas fontes versionadas.

## Segurança, memória e limites de evidência

1. **Sem OIDC:** GitHub Actions não acessa automaticamente a conta Google. A sincronização Drive → GitHub foi feita por acesso autenticado explícito do conector no ChatGPT. Novas versões no Drive só entram após nova consulta, verificação e importação autorizada.
2. **Separação de status:** um fragmento literal de export pode conter comandos do autor, narrativa, sugestões, respostas com erro, antecipações, material de bastidores e recapitulações. Portanto, \`LITERAL_SOURCE_EVIDENCE_NOT_CANON_CERTIFIED\` jamais significa evento aprovado automaticamente. O guardião do cânone e revisão do autor continuam exigidos.
3. **Dias não certificados:** o nome D001–D528 não prova que cada dia tenha uma cena individual; há elipses, dias citados e intervalos repetidos nas fronteiras. A auditoria de continuidade histórica deve ser construída a partir de evidência textual, não do nome do arquivo.
4. **Privacidade:** arquivar fontes e trechos somente em branch privado; não registrar prosa integral em logs, commit de código público, issue ou PR. Os resultados de consultas também são privados.
5. **Conflito documental:** prosa integral aprovada e HEAD canônico prevalecem sobre interpretação de export, fontes antigas, índice, rumor ou planejamento.
6. **Custo:** binários SQLite e TXT geram aumento do histórico Git e armazenamento. Usar a branch de dados e evitar rebuild repetido; não copiar os 14 MB para cada PR.
7. **Novos episódios:** o material D529 continua rascunho; sua promoção segue o workflow de escolha no banco canônico, não este FTS.

## Aceite técnico

- Verificar seis arquivos × bytes × SHA-256 completos; exigir SHA-1 de cada bloco Git.
- Construir o FTS5, \`PRAGMA quick_check\`, contagem íntegra de fontes e trechos; confirmar pesquisa por uma palavra existente no corpus.
- Testar reconstrução do banco depois de remover a cópia SQLite num ambiente descartável.
- Confirmar busca real privada com referência de origem e linhas, e ausência de alterações em \`canon/HEAD.json\`.
- Registrar contagem real de trechos apenas depois de executar a Action com os documentos íntegros.

**Importante:** a busca responde “o que o arquivo diz e onde”; o cânone responde “o que foi reconhecido como realmente narrado e aprovado”. Não fundir as duas perguntas.
