# WORLDROOT — Ciclos 1, 2 e 3: fechamento rápido com integridade

## Fonte de verdade e guarda
GitHub privado mantém `main` (motor/política) e `story-archive` (texto, cânone, escolhas, provas, capítulos). Drive é somente legado. Esta melhoria **não** muda prosa anterior, GÊNESE, planejamento v18, decisões autorais ou HEAD. O último HEAD verificado antes da implantação era Livro VI Capítulo 1 Parte III D539 21h08 (sequência 12), com Parte IV D540 salva como draft.

## Ciclo 1 — transição consistente
- O comando `python tools/worldroot_transition.py --archive-root . --episode-id <ID> --option 4 --expected-head <HEAD_ID> --user-message 'mensagem real do autor'` é **simulação de rota, sem escrita**. Acrescentar `--record` para escrever o envelope de escolha **somente quando existe uma mensagem autoral real**. Não criar escolha automática durante auditorias ou geração.
- Se o ID já é o HEAD canônico, a seleção vai para `navigation/author_intents/<ID>.json`; NÃO fecha o cânone novamente. A intenção exige checagem de alinhamento com o próximo draft existente. Se o ID é o draft imediatamente adjacente, grava `choices/<ID>/option-N.json`, que dispara o workflow existente de canonização.
- `--expected-head` é um controle contra estado obsoleto; opção 5 exige texto real. Repetir o mesmo arquivo é idempotente; opção divergente falha.
- `git-canon-cycle.yml` passa a usar o motor `main@06ee3b5...`, que conhece a ratificação excepcional do Livro VI. O arquivamento e a canonização compartilham o mesmo grupo de concorrência `worldroot-story-write`, com `cancel-in-progress:false`. Ainda assim, push normal deve ser fast-forward, sem força, e verificações do HEAD seguem obrigatórias.

## Ciclo 2 — memória incremental literal
- Ao arquivar um episódio, gerar `memory/deltas/<ID>.json` dos eventos e conhecimentos revisados por evidências de linhas, fonte, hashes, localização de personagem e incertezas. O texto original é a referência; memória é projeção consultiva, não nova verdade.
- Ao fechar o episódio, **não alterar o delta anterior**: criar `memory/canon/<ID>.json` vinculado ao hash do jornal canônico. Dado inconsistente com a fonte bloqueia o fecho.
- `ops/RESUME.json` é o retrato **regenerável** do HEAD e último draft. O escritor sempre lê o HEAD vivo e as fontes, e não confia cegamente no retrato.
- Revisão de carisma de Lucas pelo `worldroot_voice_audit.py`: comparar sinal de diálogos em maiúsculas com a referência D529, mais pautas narrativas (afeto, simpatia, escuta, potência sem arrogância). O sinal mecânico **não substitui juízo literário**, não trava a história por métrica arbitrária nem torna a proposta de estilo uma regra de `main` sem aprovação.

## Ciclo 3 — encerramento de capítulo e recuperação
- Primeira etapa: pacote GitHub de cinco Partes quando I–IV são canônicas e V está integralmente arquivada. O ZIP, o manifesto e o texto integral não são modificados após a publicação.
- Segunda etapa: quando a Parte V se torna canônica, `worldroot_chapter_seal.py` verifica os cinco jornais sequenciais, hashes, arquivo ZIP, manifesto e fonte; escreve `chapters/<BOOK-CXX>/CANONICAL_SEAL.json` e `delivery/github_chapters/<BOOK-CXX>-SEAL.json`. **Não altera a narrativa, o HEAD ou o pacote anterior**.
- O caso Caedren D539 possui ratificação autoral literal de presença, mas afiliação, rota e comando permanecem *não demonstrados*: o editor não pode sanar com invenção. Capítulo preserva a incerteza em vez de rejeitar um fato já ratificado.
- Snapshot de recuperação `ops/RESUME.json` e backfill inicial em `ops/requests/three-cycle-bootstrap-20261119.json`, um único workflow seguro que não escreve escolhas, história ou HEAD.

## Testes e comandos

```bash
python -m unittest discover -s tools -p 'test_worldroot_three_cycles.py' -v
python tools/verify_lvi_original.py --root . --require-all
python tools/worldroot_memory_delta.py --archive-root . --mode draft --episode-id LVI-C01-PIV-D540-AUTHOR-SOURCE
python tools/worldroot_memory_delta.py --archive-root . --mode resume
python tools/worldroot_chapter_seal.py --archive-root . --book 'Livro V' --chapter 16 --check-only
```

A QA real confere o replay de 12 fechamentos por `python -m worldroot.git_cycle verify`, além de testes sintéticos de idempotência, opção divergente, HEAD antigo, âncora falsa e corrupção do ZIP.

## Limitações operacionais
- GitHub Actions não envia uma mensagem espontânea para o chat, nem intercepta a mensagem original sozinho. O ChatGPT conectado deve realmente enviar a fonte preparada à branch e verificar depois o recibo remoto.
- Um arquivo preparado antes da entrega não prova equivalência independente à interface renderizada.
- O GitHub privado funciona como histórico versionado, mas isso **não é cópia de segurança offsite independente do provedor**.
- Nenhum usuário escolheu uma opção narrativa nesta solicitação; portanto nenhum registro de escolha é gerado.
- O novo ciclo de Parte V com todas as etapas canônicas precisa de execução real futura. Testes sintéticos e replay atual não constituem prova de produção futura.

## Métrica de aceitação
Uma implantação só pode ser chamada **integrada** após: PR incorporado, CI do merge verde, workflows de backfill concluídos, leitura de volta de `memory/` e `ops/RESUME.json`, preservação comprovada de HEAD, original e 5 escolhas da Parte IV; sem criação de escolha autoral nem envio ao Drive.
