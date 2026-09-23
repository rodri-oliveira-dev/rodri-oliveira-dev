# Coleta de contribuições externas

A implementação do [roadmap #12](https://github.com/rodri-oliveira-dev/rodri-oliveira-dev/issues/12) coleta PRs públicos em projetos de terceiros selecionados, gera Markdown bilíngue e entrega uma prévia verificável para revisão. O workflow não altera diretamente a branch principal.

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

O JSON é escrito de forma atômica apenas quando todos os projetos terminam com sucesso. A renderização e a proposta de atualização revisável estão implementadas nas issues #16 e #17.

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

O workflow definitivo está em `.github/workflows/external-contributions.yml`. Na branch de desenvolvimento e em PRs, somente coleta e renderiza cópias dos READMEs e publica artefatos de prévia. A proposta automática de atualização é restrita a execuções agendadas ou disparadas explicitamente na `main`.

### Contrato e limites

- Os blocos são substituídos exclusivamente entre um par único e ordenado de marcadores EXTERNAL_CONTRIBUTIONS:START / EXTERNAL_CONTRIBUTIONS:END em cada README. A validação de ambos os arquivos ocorre **antes** de qualquer escrita; marcadores ausentes, repetidos ou invertidos interrompem o processo.
- Projetos, nomes e descrições em português e inglês são curados em external-contributions.json; o coletor fornece somente os estados e totais verificados. Uma atualização automática não modifica a parte editorial fora dos marcadores.
- O renderer verifica perfil, escopo, ordem e identidade dos projetos, PRs destacados, links canônicos, estados, carimbos UTC, totais por projeto e totais agregados. Snapshot inválido, incompleto ou ausente impede qualquer atualização. O escopo da contagem permanece restrito **a todos os PRs públicos de autoria do perfil nos projetos externos selecionados**, incluindo os que não estão destacados na tabela. Não são totais históricos da conta.
- A data exibida é a **data da última alteração do painel**, não uma promessa de atualização diária. Uma coleta posterior com estados, totais e conteúdo editorial idênticos não muda a data nem os READMEs. Mudanças substantivas nos estados, totais ou textos editoriais atualizam a seção e a data.
- Executar novamente com os mesmos dados não produz diferenças; o modo padrão é somente prévia. As escritas explícitas usam arquivos temporários nos diretórios de destino e somente ocorrem após o preparo completo das duas versões. Caso a segunda gravação em disco falhe depois da primeira, é possível restaurar pelo controle de versão: a operação entre os dois arquivos não constitui uma transação do sistema de arquivos.
- A validação de desenvolvimento cobre 25 testes offline (coletor e renderizador), coleta real de dados públicos, invariantes do snapshot, renderização nas duas cópias e repetição sem alterações.

## Workflow definitivo: execução e revisão (issue #17)

Arquivo: [.github/workflows/external-contributions.yml](workflows/external-contributions.yml).

- **Disparos:** push na branch de desenvolvimento (somente caminhos afetados); PR que modifica os arquivos envolvidos; agendamento **diário às 06:00 de São Paulo (09:00 UTC, cron `0 9 * * *`)**, **somente após o workflow existir na main**; e workflow_dispatch. Uma execução manual tem publish=false por padrão. A proposta automatizada é restrita a schedule ou workflow_dispatch com publish=true, executados na branch main. O horário programado é aproximado: o GitHub Actions pode atrasar execuções agendadas.
- **Jobs visíveis:** (1) validar curadoria, testes offline e sintaxe dos workflows; (2) consultar GitHub com GITHUB_TOKEN temporário e permissão contents: read; (3) renderizar ambos os READMEs em cópias e verificar a idempotência; (4) propor PR de atualização **apenas na main**, se houver mudanças e se não houver outra proposta automática aberta.
- **Prévia:** cada execução bem-sucedida produz external-contributions-preview com README.md, README.en.md, snapshot.json e candidates.json; external-contributions-data com o snapshot utilizado; e external-contributions-candidates com o relatório separado de novos projetos. Os artefatos são retidos por 7 dias. Os READMEs versionados não são alterados durante os três primeiros jobs.
- **Publicação:** o quarto job é o único que recebe contents: write e pull-requests: write. Em uma execução elegível na main, ele verifica se já há um PR de atualização automática aberto; se não houver e as duas versões diferirem das atuais, cria uma branch exclusiva para a execução e abre um PR de revisão em direção à main. **Nunca faz push para a main, merge automático, nem cria branch/PR em execuções de push de desenvolvimento ou pull_request**.
- **Fallback:** algumas configurações de repositório bloqueiam a criação de PRs pelo GITHUB_TOKEN. Nesse caso, a branch gerada e o artefato de prévia permitem abrir o PR manualmente; o workflow emite aviso sem afirmar que houve publicação. Se também houver bloqueio de push, o job falha e o artefato gerado anteriormente permanece disponível.
- **Proteção da main:** o ruleset ativo exige PR, resolução de threads e os checks Check README links e Check spelling. PRs criados por GITHUB_TOKEN não iniciam automaticamente os workflows comuns de push/PR; após abrir um PR, o job com permissão actions: write dispara explicitamente os workflows existentes validate-profile.yml e spell-check.yml via workflow_dispatch na branch proposta. Caso a configuração do repositório impeça um desses disparos, o job registra aviso e um colaborador autorizado deverá fazer os checks serem executados antes do merge. Não contorne nem enfraqueça o ruleset.
- **Sem mudanças:** se os dados continuarem iguais, a data não é atualizada, o gerador não modifica os READMEs e o job não abre PR. Se já houver proposta automática aberta, a execução produz novo artefato e aguarda revisão da proposta anterior, sem criar duplicatas.
- **Falha da API:** a coleta/renderização falha sem editar os READMEs e sem executar a proposta de PR. O token só é disponibilizado ao step de coleta e, no quarto job, às operações GitHub autorizadas.
- **Migração do Metrics:** o workflow SVG experimental existe somente em branches separadas test/metrics-*, não na main. O PR experimental #11 continua independente. Ao aceitar a solução Markdown, encerrar ou arquivar o experimento de Metrics em uma etapa de manutenção separada, sem integrar seu workflow na main e sem excluir branches antes de conferir o histórico.

### Operação após integração

No GitHub, abra Actions > External open-source contributions > Run workflow, selecione **main** e deixe publish desmarcado para baixar e conferir o artefato de prévia. Marque publish somente quando quiser solicitar um PR revisável de atualização. A execução diária também proporá uma atualização se houver mudança e não existir outra proposta automática pendente. Revise os números, estados dos PRs, links, traduções e checks antes de integrar.

### Descoberta diária de novos projetos externos

Além de atualizar os PRs dos quatro projetos já selecionados, a coleta pesquisa **todos os PRs públicos de autoria de rodri-oliveira-dev em repositórios de terceiros**, usando `is:pr author:rodri-oliveira-dev -user:rodri-oliveira-dev`. O script [discover_external_contributions.py](../scripts/discover_external_contributions.py) agrupa as contribuições por repositório, exclui os projetos já presentes na curadoria e repositórios pertencentes ao próprio perfil e informa os **novos projetos candidatos** no resumo da execução do Actions e nos artefatos `external-contributions-candidates` e `external-contributions-preview/candidates.json`.

A descoberta **não inclui automaticamente repositórios na tabela nem nas métricas do README**: antes disso, revise o projeto e adicione-o em `external-contributions.json`, com os PRs a destacar e descrições PT-BR/EN. Isso evita incluir projetos irrelevantes ou projetos de terceiros que você mantenha, mas que não estejam na sua conta. A atualização das contribuições nos projetos já curados continua automática, sujeita ao PR de revisão. Quando a busca exceder os limites do GitHub Search (1.000 resultados), houver erro ou a paginação for incompleta, a execução falha sem publicar um relatório de ausência de novos projetos.

O agendamento utiliza 09:00 UTC diariamente, equivalente a 06:00 no fuso de São Paulo (UTC-3). Como cron do GitHub Actions opera em UTC, alterações futuras nas regras de fuso horário exigirão revisar o cron.
