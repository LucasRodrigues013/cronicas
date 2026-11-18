> **ARQUITETURA HISTÓRICA r7 — substituída operacionalmente pelo WORLDROOT r8 sem OIDC.** A `main` já contém o motor, GitHub `story-archive/canon/HEAD.json` é o HEAD operacional, SQLite versionado e regenerável, e a integração GitHub-only possui Actions reais. Drive/Atlas/Base Viva continuam sem sincronização automática. Leia [ciclo atual](github-only-recoverable-cycle.md) e [instrução do Projeto ChatGPT](instrucao-unica-projeto-chatgpt.md) antes de aplicar qualquer orientação abaixo. Não interpretar pendências/PRs r7 abaixo como estado atual.

# WORLDROOT r7 — comando único da escolha, Actions e fechamento protegido

**Ponto observado em `2026-11-17/18`:** repositório privado; `main` ainda contém somente README; código de fechamento está no PR #6 em **draft**; fluxo `story-archive` de validação de pacote já passou com o episódio literal D529 Parte II. O capítulo está em RASCUNHO, o HEAD oficial permanece D528. **Este documento descreve a arquitetura desejada, não um deploy já concluído.**

## Contrato narrativo (o que o autor vê)

A pessoa escreve apenas `Escolha 4` (ou `5: ação livre...`). A interface conectada precisa:

1. Identificar episódio esperado pela referência fixa do último draft (sem adivinhar nomes). Enviar a seleção como ato do autor, nunca como decisão inferida do modelo.
2. Recuperar `episode_draft.json`, `narrativa_integral.md`, `opcoes.json`, `manifesto_imutavel.json` de `story-archive` **privado**; revalidar byte a byte, ordem do capítulo, cinco opções e SHA-256.
3. Verificar se já existe resultado para o mesmo `episode_id + choice_sha256`. Em caso afirmativo, retornar esse recibo — não duplicar fatos.
4. Revisar os eventos **a partir do texto narrado**, da origem literal e do relógio de cada personagem. Eventual plano ou bastidor mantém seu status. Aplicar `require_reviewed_event_evidence` a cada fato. A análise de significado continua uma decisão editorial; a evidência textual sozinha não a certifica.
5. Enviar ao serviço de fechamento um **comando autenticado** com idempotency key. Sem confirmação e readback de todos os destinos não se inicia outra parte como cânone já fechado.
6. Depois do sucesso: recuperar o novo HEAD e contexto de conhecimento, simular mundo autônomo dentro dos limites de informação, redigir Parte III com estilo WORLDROOT, apresentar cinco escolhas e arquivar novo draft **antes** de afirmar que está salvo.
7. A pessoa continua vendo cinco opções sem precisar copiar prompts repetitivos. Para um novo chat, as instruções permanentes do Projeto ChatGPT precisam apontar para o repositório/HEAD e exigir a operação explícita — editar o GitHub **não modifica automaticamente** as instruções do projeto ChatGPT.

## Topologia recomendada (preferir um workflow orquestrador com jobs `needs`)

```
ChatGPT — escolha expressa do autor
  -> commit autenticado de `choices/<episode_id>/<choice_sha>.json` OU chamada API de dispatch
     -> GitHub Actions: validar escolha e pacote literal
       -> restaurar snapshot SQLite versionado do LAST-CANON HEAD
         -> extrair e auditar deltas de eventos/conhecimento
           -> gravar literatura/sidecars no Drive restrito, reler e comparar
             -> registrar índices Base Viva e Atlas + conferir
               -> publicar HEAD com `requiredRevisionId` (CAS) por ÚLTIMO
                 -> salvar/revalidar snapshot SQLite e recibo durável
                   -> interface desbloqueia a nova parte
```

**Observação:** se o snapshot SQLite for salvo depois do HEAD, uma falha nesse passo deixa HEAD remoto à frente do estado local. O executor deve escrever o snapshot **pré-compromisso**, manter um outbox durável e reconciliar o HEAD após falha; não pode depender do disco efêmero do runner. Uma cópia do HEAD/registro de evento com sequência monotônica precisa existir fora do runner, e a verificação de recuperação deve ser testada antes da habilitação.

## Por que dois Actions independentes não bastam

- `workflow_run` depende de um arquivo de workflow na branch default (`main`) e a passagem de artefatos entre jobs privilegiados e não privilegiados aumenta a superfície de ataque.
- Um `push` feito pelo `GITHUB_TOKEN` dentro de Actions **não cria por padrão outro workflow de `push`**. Use `needs:` com jobs no mesmo workflow, ou `workflow_dispatch` autenticado e explícito, não um encadeamento presumido.
- GitHub Actions não observa automaticamente o final de uma resposta do ChatGPT. A gravação inicial é uma chamada real do conector/app; a ação do autor precisa ser transportada ao GitHub por uma integração ativa.
- Use `concurrency` por série/HEAD, `cancel-in-progress: false`, CAS do Docs, manifestos imutáveis, regras de branch, permissões mínimas e código fixado em SHA.

## Fonte da verdade / responsabilidades

| Sistema | Responsabilidade | O que NÃO fazer |
|---|---|---|
| Drive | Texto oficial, cópia imutável, base de documentos, HEAD canônico | Avançar HEAD antes de verificar as bases e provas |
| GitHub privado | Código versionado, story-archive, decisões do autor, recibos e CI | Usar aprovação de CI como promoção de cânone; expor segredos nos logs |
| SQLite | Eventos, knowledge graph temporal, outbox, snapshots reproduzíveis | Guardar a única cópia no disco temporário do Actions |
| Base Viva/Atlas/Wiki | Índices/visões derivados de eventos com fonte | Tratar ponteiro de capítulo como atualização de fichas e relações |
| ChatGPT | Interface, narração, revisão e operações em ferramentas disponíveis | Prometer gatilhos do Actions ou save automático após o fim do turno |

## Gates de ativação exigidos (os que estão abertos)

1. **Consolidar código validado na branch default com revisão**: PRs dependentes ainda não foram integrados; preferir merge com testes reais + branch protection.
2. **Identidade temporária Google**: WIF/OIDC restrito a este repo e workflow aprovado. Criar/autorizar service account e compartilhar somente arquivos/pasta Drive necessários. `drive.file` pode precisar de configuração de acesso explícita, inclusive Google Docs/Sheets já existentes. Não armazenar chaves permanentes.
3. **Restaurar estado do runner**: checkpoint durável do SQLite + event replay, teste de perda de ACK e de retomada sem gerar duas versões do HEAD.
4. **Conhecimento e semântica**: o draft D529 tem `eventos_e_consequencias.json=[]`. Os 11 candidatos ancorados no arquivo original precisam ser revistos e só então publicados; quem sabe cada fato é parte do evento, não inferência global.
5. **Sincronização real**: testar arquivo completo 72.650 bytes com download novo e hash, índices Base Viva/Atlas e Docs `requiredRevisionId`, sem sobregravar linhas alheias.
6. **Segurança/custos**: proteger branches de código e `story-archive`, limitar `GITHUB_TOKEN`, impedir execução de código não confiável em jobs com OIDC, logs sem texto privado, revisar retenção de Actions e minutos faturáveis em repo privado.
7. **ChatGPT como interface de um comando**: configurar uma instrução permanente de Projeto ou um pequeno conector/workflow que receba a escolha e faça o commit/dispatch; testar em outra conversa. GitHub não injeta automaticamente instruções no ChatGPT.

## Situação de hoje (não misturar com implantação)

- D529 Parte II integral: Drive e GitHub privado com readback e GitHub Actions QA **SUCESSO**. Episódio RASCUNHO.
- HEAD canônico: D528, não houve seleção da Parte III neste fluxo.
- Candidatos semânticos D529: 11 eventos e 6 relações de conhecimento em staging privado, não promovidos.
- Pipeline de fechamento, backup, memory e QA: código testado (146 testes locais após gate de evidência), PR #6 em **draft**.
- Espelho Drive pelo Actions: template preparado, identidade Google e testes de produção **PENDENTES**.

## Referências oficiais

- GitHub — GITHUB_TOKEN e eventos: https://docs.github.com/en/actions/concepts/security/github_token
- GitHub — workflow_dispatch e default branch: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- GitHub — workflow_run e riscos de segurança: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Google Cloud — WIF para pipelines CI/CD: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- Google Workspace — compartilhar arquivos com service account: https://developers.google.com/workspace/guides/create-credentials
- GitHub — custos de Actions em repositório privado: https://docs.github.com/en/billing/concepts/product-billing/github-actions
