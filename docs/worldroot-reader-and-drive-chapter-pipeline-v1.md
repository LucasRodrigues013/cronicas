# WORLDROOT · Entrega auditada ao Chat + backup automático por capítulo

**Estado de implantação:** código e workflow só ficam ativos depois do merge desta alteração em `story-archive`. **Sem autorização OAuth do Drive, backup remoto fica BLOQUEADO e reporta falha, sem simular salvamento.** Não modifica HEAD, episódios nem decisões do autor.

## Fluxo de uma Parte

1. O ChatGPT constrói uma Parte completa com prosa literal, cinco escolhas, eventos, conhecimento temporal e checkpoint. Durante a geração não é permitido declarar que foi gravada.
2. O ChatGPT deve invocar **explicitamente o conector GitHub** e criar o `story-archive/inbox/<EPISODE_ID>.json` integral e de origem autoral verdadeira. Não existe interceptação automática universal de mensagens do chat.
3. `worldroot-draft-inbox.yml` valida a entrada, arquiva o pacote imutável e executa `delivery_gate`. Se liberado, grava também `delivery/reader_receipts/<EPISODE_ID>.json`, com SHA-256 e caminho literal. Um recebimento no GitHub não substitui essa prova.
4. Só depois de o workflow terminar e o ChatGPT buscar **de novo** o recibo e `episodes/<EPISODE_ID>/draft/narrativa_integral.md`, comparando SHA-256, o texto poderá aparecer ao autor como Parte concluída. **GitHub Actions não injeta mensagens autonomamente numa conversa ChatGPT aberta.** A etapa de leitura é executada pelo assistente dentro de um turno ativo.
5. A escolha real do autor continua a fechar o episódio anterior por `choices/<EPISODE_ID>/option-*.json` e atualizar HEAD com o workflow canônico próprio. A existência do recibo do leitor **não promove cânone**.

## Ao chegar à quinta Parte

O mesmo workflow de inbox aciona o job `chapter-drive-backup` com o ID do novo episódio. Ele ignora novas Partes I–IV. Para a Parte V, verifica:

- Partes **I, II, III, IV e V** do mesmo Livro e Capítulo, sem duplicatas ou rejeições editoriais.
- Cada narrativa, opções, eventos e checkpoint contra seu manifesto SHA-256 e tamanho; correspondência com `episode_draft.json`.
- Registro `FECHADO_GITHUB` nas Partes I–IV, com SHA literal coerente. A Parte V pode permanecer como draft até a escolha autoral.
- Geração de três arquivos: `LIVRO-...-INTEGRAL.md` (as cinco Partes literais sem reescrita), `LIVRO-...-MANIFESTO.json` (hashes e sequência) e `LIVRO-...-ARQUIVO.zip` (todas as narrativas, manifests, eventos, opções, checkpoints, reviews, escolhas registradas e journals existentes).
- Upload para um único diretório configurado no Drive pessoal via OAuth; consulta posterior da metadata **e download independente dos bytes de cada arquivo**. Em caso de erro, falha e não registra sucesso.
- Após confirmação remota, commit de `delivery/drive_chapters/LIVRO-...-CXX.json` com os três IDs de arquivo, SHA-256, tamanho e data. O **HEAD não é modificado**.

As Partes anteriores a esta implantação não são sincronizadas retroativamente em silêncio; o gatilho automático é a entrada validada da nova Parte V.

## Configurar o Google Drive pessoal (uma vez)

A conexão do Google Drive dentro do ChatGPT **não pode ser emprestada** à Action. É preciso OAuth próprio para a Action.

1. Criar projeto no **Google Cloud Console**, habilitar **Google Drive API** e configurar a tela de consentimento OAuth. Usar conta destinada ao backup, se preferir isolar riscos.
2. Criar credenciais **OAuth 2.0** de aplicativo desktop. Autorizar acesso ao Drive com refresh token válido para a conta que efetivamente terá os arquivos. O script usa o escopo `https://www.googleapis.com/auth/drive` (amplo, para poder localizar o diretório e conferir arquivos). Evite conceder este escopo à conta principal sem considerar o risco; um OAuth App em modo *Testing* pode gerar refresh tokens de curta duração.
3. Criar a pasta de destino no Drive dessa conta e guardar seu ID exato.
4. Em **GitHub → repositório `cronicas` → Settings → Secrets and variables → Actions**, registrar **somente como secrets**, nunca em arquivo ou mensagem no chat:
   - `WORLDROOT_GOOGLE_CLIENT_ID`
   - `WORLDROOT_GOOGLE_CLIENT_SECRET`
   - `WORLDROOT_GOOGLE_REFRESH_TOKEN`
   - `WORLDROOT_DRIVE_CHAPTER_FOLDER_ID`
5. Fazer o fluxo de um novo Capítulo com Parte V. Verificar o job `chapter-drive-backup` e o recibo em `delivery/drive_chapters/`.

**Importante:** Uma service account via OIDC é mais indicada para Google Workspace com *Shared Drive*. Contas de serviço não possuem cota de armazenamento pessoal no My Drive; por isso este primeiro adaptador para Drive pessoal usa OAuth do proprietário. Não publicar refresh tokens em Issues, logs, PRs ou arquivos.

## Limites reais

- Testes de integridade e fechamento de capítulo não garantem por si só que Caedren, Varo ou outros personagens tenham a localização correta; o ChatGPT ainda precisa executar auditoria de continuidade literária contra fontes e fichas antes do inbox.
- GitHub não publica automaticamente mensagens no chat. O `reader_receipt` documenta o arquivo **apto a ser recuperado**, não um push ao usuário.
- Falha nas credenciais do Drive **não apaga nem altera o episódio já arquivado**; o job de backup falha separadamente, sem declarar o espelhamento concluído.
- O workflow usa o mesmo job de inbox para iniciar o backup: commits realizados com `GITHUB_TOKEN` geralmente não disparam outro workflow por `push`.
- Backup de capítulo não é a mesma coisa que sincronização de `Base Viva`, `Atlas`, `HEAD` ou Google Docs nativos. Essas integrações permanecem distintas.

## Auditoria sem credenciais

A CI `worldroot-chapter-backup-qa.yml` executa:
`python -m unittest discover -s tools -p 'test_chapter_drive_publisher.py' -v`

E audita o capítulo real já arquivado, sem escrever no Drive:
`python tools/chapter_drive_publisher.py --archive-root . --book 'Livro V' --chapter 16 --check-only`

Não registrar o Livro VI rejeitado como episódio novo, nem mudar D537 em virtude deste backup.
