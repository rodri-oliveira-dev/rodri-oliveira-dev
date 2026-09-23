# Coleta de contribuições externas

Esta etapa do [roadmap #12](https://github.com/rodri-oliveira-dev/rodri-oliveira-dev/issues/12) implementa apenas a coleta e validação dos dados. Não altera o README e não publica estatísticas automaticamente.

## Escopo dos dados

A fonte editorial é [external-contributions.json](external-contributions.json). Somente projetos externos selecionados nesse arquivo entram na coleta. A busca retorna PRs públicos de autoria de rodri-oliveira-dev nesses repositórios, incluindo PRs que não estão destacados manualmente no README. Não são métricas de toda a conta do GitHub.

- PR integrado: campo de data de integração não nulo e estado fechado.
- PR aberto: estado aberto e sem data de integração.
- PR fechado sem integração: estado fechado e sem data de integração.
- Projetos próprios (rodri-oliveira-dev/*) são rejeitados na configuração.
- O array reference_prs no JSON de saída contém somente os PRs destacados na curadoria, na ordem editorial. As contagens consideram todos os PRs públicos do perfil encontrados em cada repositório selecionado.
- O campo latest_merged_at é a data da integração mais recente dentre esses PRs, não a data da última atividade do usuário.
- O campo collected_at indica o instante UTC da consulta, não a data de cada PR.

## Execução

Python 3.10 ou superior, apenas biblioteca padrão, com GITHUB_TOKEN disponibilizado pelo GitHub Actions durante a execução. A futura automação pode usar permissions: contents: read e não precisa de METRICS_TOKEN nem de um PAT pessoal para consultar os repositórios públicos selecionados.

~~~bash
GITHUB_TOKEN=... python3 scripts/external_contributions.py \
  --config .github/external-contributions.json \
  --output build/external-contributions-snapshot.json

python3 -m unittest discover -s tests -v
~~~

Não inclua o token em arquivos versionados, argumentos de linha de comando, logs ou prints do workflow.

## Garantias e limitações

A busca paginada usa a API pública GET /search/issues com os qualificadores is:pr, author e repo, com até 100 itens por página. O limite da API é de 1.000 resultados por consulta: quando esse limite é ultrapassado, a pesquisa indica incompletude, o total varia entre páginas, uma referência curada não aparece ou ocorre erro da API, o coletor falha integralmente, sem atualizar o snapshot anterior nem inventar zeros. Itens duplicados por paginação são desduplicados pelo número do PR; respostas contraditórias são recusadas.

O status vem do campo pull_request.merged_at retornado pelo GitHub Search, e não é inferido do fato de um PR estar fechado. Resultados podem sofrer atraso de indexação ou mudanças durante a paginação; as verificações de completude reduzem, mas não eliminam, essas limitações. Somente dados públicos e somente os repositórios curados estão no escopo.

O JSON é escrito de forma atômica apenas quando todos os projetos terminam com sucesso. A etapa de renderização do Markdown e a política de atualização via PR pertencem às issues #16 e #17.


## Renderização bilíngue, sem publicação automática (issue #16)

O renderizador [render_external_contributions.py](../scripts/render_external_contributions.py) consome **somente** a configuração editorial e o snapshot completo do coletor. Não consulta a API, não exige token e não sobrescreve o README inteiro.

~~~bash
# Primeiro, executar o coletor (GITHUB_TOKEN disponível no ambiente).
python3 scripts/external_contributions.py \
  --config .github/external-contributions.json \
  --output build/external-contributions-snapshot.json

# Prévia: valida ambos os READMEs e informa quais arquivos mudariam, sem escrita.
python3 scripts/render_external_contributions.py \
  --config .github/external-contributions.json \
  --snapshot build/external-contributions-snapshot.json

# Edição explícita em cópias locais antes de uma alteração real:
cp README.md /tmp/profile-pt.md
cp README.en.md /tmp/profile-en.md
python3 scripts/render_external_contributions.py \
  --config .github/external-contributions.json \
  --snapshot build/external-contributions-snapshot.json \
  --readme-pt /tmp/profile-pt.md \
  --readme-en /tmp/profile-en.md \
  --write
~~~

A versão definitiva do GitHub Actions e o mecanismo de atualização por PR estão reservados à issue #17. O workflow temporário de desenvolvimento **apenas testa cópias dos READMEs em RUNNER_TEMP**; não faz commit, não publica artefato nem altera main.

### Contrato e limites

- Os blocos são substituídos exclusivamente entre um par único e ordenado de marcadores EXTERNAL_CONTRIBUTIONS:START / EXTERNAL_CONTRIBUTIONS:END em cada README. A validação de ambos os arquivos ocorre **antes** de qualquer escrita; marcadores ausentes, repetidos ou invertidos interrompem o processo.
- Projetos, nomes e descrições em português e inglês são curados em external-contributions.json; o coletor fornece somente os estados e totais verificados. Uma atualização automática não modifica a parte editorial fora dos marcadores.
- O renderer verifica perfil, escopo, ordem e identidade dos projetos, PRs destacados, links canônicos, estados, carimbos UTC, totais por projeto e totais agregados. Snapshot inválido, incompleto ou ausente impede qualquer atualização. O escopo da contagem permanece restrito **a todos os PRs públicos de autoria do perfil nos projetos externos selecionados**, incluindo os que não estão destacados na tabela. Não são totais históricos da conta.
- A data exibida é a **data da última alteração do painel**, não uma promessa de atualização diária. Uma coleta posterior com estados, totais e conteúdo editorial idênticos não muda a data nem os READMEs. Mudanças substantivas nos estados, totais ou textos editoriais atualizam a seção e a data.
- Executar novamente com os mesmos dados não produz diferenças; o modo padrão é somente prévia. As escritas explícitas usam arquivos temporários nos diretórios de destino e somente ocorrem após o preparo completo das duas versões. Caso a segunda gravação em disco falhe depois da primeira, é possível restaurar pelo controle de versão: a operação entre os dois arquivos não constitui uma transação do sistema de arquivos.
- A validação de desenvolvimento cobre 25 testes offline (coletor e renderizador), coleta real de dados públicos, invariantes do snapshot, renderização nas duas cópias e repetição sem alterações.
