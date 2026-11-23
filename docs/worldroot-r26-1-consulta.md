# Consulta do Grimório R26.1

Após obter o repositório autorizado, na raiz rode:

- python -m worldroot.r26_magic_catalog — total, escolas, Círculos e estado.
- python -m worldroot.r26_magic_catalog --list --school VELATH_METEOROS --limit 50 — cinquenta possibilidades da Grande Torre.
- python -m worldroot.r26_magic_catalog --list --school AERUN_ESTUDOS --limit 50 — cinquenta linhas candidatas do instituto.
- python -m worldroot.r26_magic_catalog --list --circle 9 --limit 100 — propostas do Círculo IX.
- python -m worldroot.r26_magic_catalog --list --search maré --limit 50 — busca de nomes ou efeitos.
- python -m worldroot.r26_magic_catalog --list --school FORJA_AURORA_ESTUDOS --format json --limit 50 — detalhes para editores.

A busca consulta os **1.020** feitiços, incluindo os **120 da R26 original**. Não consulta automaticamente o conhecimento de um personagem: **candidato** não é **aprendido**. Ao selecionar uma magia, verificar seu ID, a origem, o caminho de aquisição, o episódio e a evidência literal. Sem isso, não pode ser registrada como uso canônico.

Consulte a Bíblia completa em docs/worldroot-r26-1-atlas-milenar.md.
