# WORLDROOT R28 — Mundo vivo

Complemento incremental a R24–R27; política v15 P82–P88. Não altera cânone, rascunhos, escolhas, workflows de publicação ou requisitos existentes.

## Operação

- `python -m worldroot.living_world --archive-root /path/story-archive project`: projeção dinâmica dos episódios fechados, SHA-256 das fontes, seed editorial com ativos/personagens/tramas; alerta cobertura incompleta. Referência textual não equivale a uso/presença; o estado anotado exige revisão se houver referência posterior. Seed inicial não é inventário exaustivo.
- `... review --literal /path/episode.md`: profundidade relativa, variação de cenas, motivos recorrentes e sinais de fantasia, exclusivamente consultivos. Usa até cinco partes canônicas anteriores. Integrado aos dois retornos do intake, sem tocar artefatos imutáveis.
- `... legacy --query Káiron`: reaproveita o FTS5 verificado D001–D528, recupera trechos históricos, não os promove. Cruzar aliases e fonte literal; não presumir localização.
- Entity resolution: aliases explicitamente registrados, ambiguidade preservada (AERÚN dragão versus Instituto). Não reescreve CONTEXT.
- Novas anotações no seed precisam de episódio fechado e trecho exato; edição do registro é revisão editorial, não novo evento. Dados ausentes permanecem desconhecidos. Para ativos e tramas não catalogados, procurar fontes antes de propor.

## Direção narrativa

Aplicar P82–P88. Cenas com desejo, resistência, ação, virada e consequência. Menos reafirmações de consentimento já estabelecido; preservar consentimento real. Variar humor e encerramentos; não obrigar todas as frentes por Parte. Recuperar antigos personagens e mostrar magia, cultura, fauna, lugares e criações efetivamente vividos. Especial não é agregador automático. O C08 II–V segue plano autoral no story-archive, sem resultados, mortes, aliança ou promoção predeterminada.

## Testes

`python -m unittest discover -s tests -p 'test_living_world.py'`; suíte existente permanece obrigatória. A projeção não executa o replay criptográfico completo do journal; a validação do motor existente continua autoridade. Não há gancho automático do ChatGPT: ler fontes e executar comando quando houver checkout, ou consultar registros literais no conector.
