# WORLDROOT — fechamento por escolha (r7, implementação incremental)

> Documento técnico de execução. **Não** declara ativação de um robô no ChatGPT.

## Autoridades e privacidade

- **Drive restrito:** textos integrais, sidecars, checkpoints e HEAD.
- **GitHub PRIVADO (`LucasRodrigues013/cronicas`):** versões de código, arquivos integrais de episódios em `story-archive`, hashes, diffs e histórico de alterações.
- **SQLite privado:** estado de entrega, escolha, outbox, eventos e checkpoints operacionais.
- **ChatGPT:** conversa e invocação explícita do procedimento quando ferramentas estão disponíveis. Uma resposta por si só não dispara tarefa pós-turno garantida.

O repositório está **público enquanto o proprietário não mudar a visibilidade**. `PrivateGitHubArchive` lê a visibilidade usando API autenticada em cada envio e recusa todo upload de prosa se não houver `private: true` e `visibility: private`. O conector GitHub da conversa não expõe ação administrativa de privacidade.

## Fase A — depois de fechar a Parte e mostrar as escolhas

1. A IA prepara **todo o texto**, incluindo opções 1, 2, 3, 4 Especial e 5 Ação Livre, com seu ID estável.
2. `EpisodeDraft` faz preflight de calendário, marcações de encerramento, metadados, eventos candidatos e interface.
3. `EpisodeHandoff.stage_after_options()` arquiva **exatamente** o texto exibido, as opções, o JSON que permite reidratar a sessão, os eventos ainda não canônicos, checkpoint candidato e hashes.
4. Grava e lê de volta o blob no Drive; o GitHub emite commits imutáveis na branch `story-archive` **somente se o repositório for privado**.
5. Estado final: `RASCUNHO_ARQUIVADO`, sem alterar o HEAD.

Se uma plataforma falhar, preservar `RASCUNHO_LOCAL` e informar `PENDENTE`, sem chamar o conteúdo de salvo em ambos os sistemas. O algoritmo retoma uploads idempotentemente.

## Fase B — próxima mensagem do autor com escolha

1. Validar que é uma seleção **real do autor**, e que a escolha se refere às opções do episódio anterior (a alternativa 5 exige texto).
2. Recuperar o episódio original usando `episode_draft.json` do GitHub privado, ou a cópia local/Drive com mesmo SHA-256. Nunca reconstruir narrativa por resumo.
3. Revisar o **delta do episódio anterior**: eventos, pessoas que aprenderam informações, personagens presentes, mudanças em projetos, relações e consequências. Hipóteses não viram fatos.
4. Confirmar cópia integral **CANON** em Drive e GitHub privados, índices de Base Viva e Atlas com readback, e HEAD Google Docs usando `requiredRevisionId` e readback.
5. Somente depois do fechamento verificado, avançar a referência `HEAD`, persistir recibo `FECHADO` e liberar a geração da nova parte.
6. A **nova parte nasce RASCUNHO**, nunca nasce automaticamente canônica; o ciclo recomeça.

Falha em qualquer etapa: manter `FALHA_FECHAMENTO` ou `FECHANDO`, preservar a escolha original e impedir começo da próxima parte. Não trocar a escolha numa repetição da operação.

## Máquina de estados

```text
TEXTO COMPLETO + OPÇÕES
       ↓
RASCUNHO_LOCAL ──────────→ RASCUNHO_ARQUIVADO  (Drive + GitHub privados, readback)
                                   ↓ próxima ESCOLHA real
                               FECHANDO ───→ FALHA_FECHAMENTO ──→ retentativa
                                   ↓
                                FECHADO (Drive + GitHub + Base + Atlas + HEAD)
                                   ↓
                           GERAR NOVO RASCUNHO
```

## Execução em ambiente privado com credenciais

Requisitos: `python>=3.10`, `pip install .[drive]`, Google Application Default Credentials com permissão mínima para a pasta Drive/Docs/Sheets autorizada e `WORLDROOT_GITHUB_TOKEN` de escopo refinado (Contents read/write SOMENTE no repositório), fornecido via gerenciador de segredos. **Nunca cole tokens em mensagens, capítulos, planilhas ou scripts versionados**.

```bash
python -m worldroot.episode_cli check-private \
  --repo LucasRodrigues013/cronicas --archive-branch story-archive

python -m worldroot.episode_cli --root ./runtime stage-after-options \
  --draft ./private/episode_draft.json --drive-folder DRIVE_PRIVATE_FOLDER_ID \
  --repo LucasRodrigues013/cronicas --archive-branch story-archive

python -m worldroot.episode_cli --root ./runtime recover \
  --repo LucasRodrigues013/cronicas --archive-branch story-archive \
  --id EPISODE_ID --output ./private/episode_draft_restored.json

python -m worldroot.episode_cli --root ./runtime choose-and-close \
  --draft ./private/episode_draft.json --reviewed-events ./private/reviewed_events.json \
  --choice 4 --expected-release CURRENT_HEAD_RELEASE --expected-day LAST_HEAD_DAY \
  --head-revision VERIFIED_DOCS_REVISION --head-doc HEAD_DOC_ID \
  --drive-folder DRIVE_PRIVATE_FOLDER_ID --repo LucasRodrigues013/cronicas \
  --base-sheet BASE_VIVA_SHEET_ID --atlas-sheet ATLAS_SHEET_ID
```

O comando `choose-and-close` só deve ser invocado por um executor de confiança que tenha observado a mensagem do autor; o script **não verifica a identidade do autor de maneira independente**. Um token privado e uma política de aprovação não são equivalentes.

## Padrões de qualidade e pesquisa aplicada

- **Transactional outbox / saga:** serviços diferentes não fornecem uma transação ACID conjunta; HEAD deve ser o último passo e cada operação precisa de readback, idempotência, journal e possibilidade de reconciliação.
- **Optimistic concurrency:** comparar versão e `requiredRevisionId` antes de atualizar HEAD; bloquear publicações baseadas em referências desatualizadas.
- **GitHub API:** obter `private: true` no endpoint do repositório antes do upload; arquivos versionados só são imutáveis por convenção e verificação de hash. Usar branch dedicada; merges de código seguem revisão independente.
- **Confidencialidade:** após mudar público→privado, conteúdo anteriormente público pode ter sido copiado por terceiros; não transformar a alteração de visibilidade em prova de que o histórico nunca foi público.
- **Segurança CI:** `permissions: contents: read` e ações fixadas em SHA completo. O teste padrão nunca recebe dados narrativos privados nem token com escrita.

## Critérios de homologação ainda abertos

1. O proprietário deve transformar o repositório em **privado** e verificar que o conector mantém acesso.
2. Configurar a branch `story-archive` e credenciais do executor privado.
3. Testar a transferência real do primeiro **episódio sintético** entre Drive e GitHub privados e ler ambos de volta.
4. Testar fechamento real com Base/Atlas, revisão HEAD e falha/restart entre HEAD remoto e checkpoint local.
5. Reconciliar qualquer Parte narrada que ainda não tenha uma cópia literal verificada, sem reconstruí-la por resumo.
6. Integrar os eventos às fichas e relações das bases, não apenas adicionar índice de episódios.

### O que não muda

O último checkpoint oficial permanece intocado; não há retcon. Nenhuma cena fictícia deste módulo se transforma em capítulo. Toda Parte não arquivada deve ser recuperada a partir de sua prosa original.
