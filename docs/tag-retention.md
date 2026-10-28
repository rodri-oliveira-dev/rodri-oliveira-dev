# Política de retenção de tags do perfil

O repositório publica tags incrementais `vMAJOR.MINOR.PATCH` por meio de `.github/workflows/release.yml`.

## Funcionamento

- O workflow `tag-retention.yml` é executado **semanalmente, às segundas-feiras, 04:17 UTC**.
- O prazo de retenção é de **três meses de calendário**, calculado a partir da data atual em UTC. Exemplo: em 28/10/2026, o corte é 28/07/2026.
- O critério de idade utiliza `published_at` da GitHub Release correspondente, que é mais confiável do que o horário do commit de uma tag leve.
- Apenas tags estáveis no formato `vX.Y.Z`, que possuem uma Release publicada e uma referência Git existente, entram na limpeza.
- **A tag estável de maior versão é sempre preservada**, mesmo após três meses sem publicações, para evitar reiniciar a numeração no workflow de release.
- Releases imutáveis, drafts, tags sem Release correspondente e tags fora desse padrão não são apagadas automaticamente.
- A exclusão remove **somente a referência Git da tag**. As GitHub Releases e seus metadados são preservados. Atenção: links de download do código-fonte baseados nas tags removidas podem deixar de funcionar. Caso também seja necessário remover releases antigas, isso deve ser tratado separadamente.

## Execução manual

Em **Actions > Prune old profile tags > Run workflow**, escolha a branch `main`.

O parâmetro `dry_run` é `true` por padrão: lista os candidatos no resumo da execução, sem deletar nada.

Para efetuar a exclusão manual, altere `dry_run` para `false`. As execuções agendadas realizam a limpeza automaticamente.

## Segurança e testes

A rotina usa apenas a API de tags do repositório corrente, restringe a remoção a versões validadas e não faz `force push`, exclusão de branches ou modificação de Releases.

Os testes em `tests/test_tag_retention.py` cobrem datas-limite, anos bissextos, retenção da versão mais recente, tags ignoradas, paginação, pré-visualização e exclusão.
