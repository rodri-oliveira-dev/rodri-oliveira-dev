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

A busca paginada usa a API pública GET /search/issues com os qualificadores is:pr, is:public, author e repo, com até 100 itens por página. O limite da API é de 1.000 resultados por consulta: quando esse limite é ultrapassado, a pesquisa indica incompletude, o total varia entre páginas, uma referência curada não aparece ou ocorre erro da API, o coletor falha integralmente, sem atualizar o snapshot anterior nem inventar zeros. Itens duplicados por paginação são desduplicados pelo número do PR; respostas contraditórias são recusadas.

O status vem do campo pull_request.merged_at retornado pelo GitHub Search, e não é inferido do fato de um PR estar fechado. Resultados podem sofrer atraso de indexação ou mudanças durante a paginação; as verificações de completude reduzem, mas não eliminam, essas limitações. Somente dados públicos e somente os repositórios curados estão no escopo.

## Retentativas da API e limites de espera (issue #22)

O cliente compartilhado `GitHubAPI` realiza **até 3 tentativas por consulta**, com timeout máximo de **10 segundos por requisição**, orçamento acumulado de **20 segundos de espera** e duração máxima de **50 segundos por consulta**. O número de tentativas pode ser configurado em código entre 1 e 4 sem alterar a autenticação, o escopo público ou o JSON de saída.

- **Retentativas:** HTTP 408, 429, 500, 502, 503 e 504, além de timeout e erro transitório de rede. Sem orientação do servidor, utiliza espera exponencial com jitter e teto de 10 segundos.
- **Restrições do servidor:** respeita `Retry-After` (segundos ou data HTTP) e, para HTTP 429 sem esse cabeçalho, `X-RateLimit-Reset`. Caso a espera exigida exceda o orçamento, interrompe a consulta **sem tentar antes do prazo pedido pelo GitHub**. Não transforma esse cenário em ausência de contribuições.
- **Falhas permanentes:** HTTP 400, 401 e 403, erro de TLS, formato inválido e JSON malformado não são repetidos. Não há registro de URL de requisição, corpo da resposta, token ou cabeçalhos sensíveis nas mensagens de erro.
- **Isolamento:** o retry é usado tanto pela coleta curada quanto pela descoberta global, sem reuni-las no mesmo job. Se o limite for esgotado durante a coleta curada, o snapshot anterior permanece intacto e a publicação é bloqueada. Uma falha apenas na descoberta mantém a atualização curada e sinaliza `unavailable` no relatório de candidatos.

Os limites foram definidos para caber no timeout de 10 minutos dos jobs em condições usuais. O GitHub Actions pode encerrar um job com muitas consultas lentas; nesse caso, os dados incompletos não são publicados. Os testes offline usam um relógio e uma conexão simulados para testar esperas e falhas sem acesso à rede nem atrasos reais.

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
- **Jobs visíveis:** (1) validar curadoria, testes offline e sintaxe dos workflows; (2) coletar dados de projetos curados; (3) descobrir opcionalmente novos projetos externos em job isolado; (4) renderizar ambos os READMEs em cópias e verificar a idempotência; (5) propor PR de atualização **apenas na main**, se houver mudanças e se não houver outra proposta automática aberta.
- **Prévia:** cada execução bem-sucedida produz external-contributions-preview com README.md, README.en.md, snapshot.json e candidates.json; external-contributions-data com o snapshot utilizado; e external-contributions-candidates com o relatório separado de novos projetos. Os artefatos são retidos por 7 dias. Os READMEs versionados não são alterados pelos jobs de validação, coleta, descoberta nem prévia. Se a descoberta falhar, candidates.json contém status unavailable e **não contém uma contagem falsa de zero candidatos**; as métricas curadas e a proposta revisável prosseguem.
- **Publicação:** o quinto job (`propose`) é o único que recebe `contents: write`, `pull-requests: write` e `actions: write`. Em uma execução elegível na main, ele verifica se já há um PR de atualização automática aberto; se não houver e as duas versões diferirem das atuais, cria uma branch exclusiva para a execução e abre um PR de revisão em direção à main. **Nunca faz push para a main, merge automático, nem cria branch/PR em execuções de push de desenvolvimento ou pull_request**.
- **Fallback:** algumas configurações de repositório bloqueiam a criação de PRs pelo GITHUB_TOKEN. Nesse caso, a branch gerada e o artefato de prévia permitem abrir o PR manualmente; o workflow emite aviso sem afirmar que houve publicação. Se também houver bloqueio de push, o job falha e o artefato gerado anteriormente permanece disponível.
- **Proteção da main:** o ruleset ativo exige PR, resolução de threads e os checks Check README links e Check spelling. PRs criados por GITHUB_TOKEN não iniciam automaticamente os workflows comuns de push/PR; após abrir um PR, o job com permissão actions: write dispara explicitamente os workflows existentes validate-profile.yml e spell-check.yml via workflow_dispatch na branch proposta. Caso a configuração do repositório impeça um desses disparos, o job registra aviso e um colaborador autorizado deverá fazer os checks serem executados antes do merge. Não contorne nem enfraqueça o ruleset.
- **Sem mudanças:** se os dados continuarem iguais, a data não é atualizada, o gerador não modifica os READMEs e o job não abre PR. Se já houver proposta automática aberta, o publicador confronta a prévia atual com os READMEs do SHA do PR e registra se ela está atual, defasada, contém edições editoriais fora dos marcadores ou exige atenção manual. Não reescreve a branch pendente nem cria duplicatas.
- **Falha da API:** uma falha na coleta **curada** impede renderização e proposta. A descoberta **opcional** executa em job isolado; se falhar, exibe um aviso e marca o relatório como indisponível, sem impedir a atualização dos READMEs curados. Tokens de consulta só aparecem nos passos que usam a API, e apenas o quinto job elegível recebe credenciais de escrita.
- **Migração do Metrics:** o workflow SVG experimental existe somente em branches separadas test/metrics-*, não na main. O PR experimental #11 continua independente. Ao aceitar a solução Markdown, encerrar ou arquivar o experimento de Metrics em uma etapa de manutenção separada, sem integrar seu workflow na main e sem excluir branches antes de conferir o histórico.

### Operação após integração

No GitHub, abra Actions > External open-source contributions > Run workflow, selecione **main** e deixe publish desmarcado para baixar e conferir o artefato de prévia. Marque publish somente quando quiser solicitar um PR revisável de atualização. A execução diária também proporá uma atualização se houver mudança e não existir outra proposta automática pendente. Revise os números, estados dos PRs, links, traduções e checks antes de integrar.

### Descoberta diária de novos projetos externos

Além de atualizar os PRs dos quatro projetos já selecionados, a coleta pesquisa **todos os PRs públicos de autoria de rodri-oliveira-dev em repositórios de terceiros**, usando `is:pr is:public author:rodri-oliveira-dev -user:rodri-oliveira-dev`. O script [discover_external_contributions.py](../scripts/discover_external_contributions.py) agrupa as contribuições por repositório, exclui os projetos já presentes na curadoria e repositórios pertencentes ao próprio perfil e informa os **novos projetos candidatos** no resumo da execução do Actions e nos artefatos `external-contributions-candidates` e `external-contributions-preview/candidates.json`.

A descoberta **não inclui automaticamente repositórios na tabela nem nas métricas do README**: antes disso, revise o projeto e adicione-o em `external-contributions.json`, com os PRs a destacar e descrições PT-BR/EN. A lista de candidatos reconhecidos e as decisões editoriais ficam em `external-contributions-review.json`. O resumo diário destaca **apenas projetos ainda não registrados e mudanças de atividade não reconhecidas**, não toda a lista histórica. O artefato `candidates.json` guarda os detalhes e a relação completa para revisão. A atualização das contribuições nos projetos já curados continua automática, sujeita ao PR de revisão. Quando a busca exceder os limites do GitHub Search (1.000 resultados), houver erro ou a paginação for incompleta, a execução falha sem publicar um relatório de ausência de novos projetos.

### Histórico versionado e decisões editoriais (issue #24)

O arquivo [`.github/external-contributions-review.json`](external-contributions-review.json) é o **histórico versionado de revisão**, separado dos quatro projetos selecionados em `external-contributions.json`. A linha de base de 24/09/2026 registra **12 projetos externos já encontrados, com 15 PRs públicos observados**, todos com status `pending`. Isso significa **identificado e aguardando decisão**, não aprovado nem inserido automaticamente no perfil.

Cada entrada inclui `repository`, `status`, `observed_at` (data da linha de base) e `observed_prs` (número do PR → `open`, `merged` ou `closed_unmerged`). Pode incluir `reason`, `decision_date` e `aliases` (nomes anteriores conhecidos para transferência/renomeação). Os estados editoriais são:

- `pending`: conhecido, ainda em revisão; sem mudanças no conjunto ou nos estados dos PRs observados, não reaparece no destaque diário.
- `ignored`: rejeitado após avaliação humana, com `decision_date` e motivo opcional; permanece no histórico completo, mas **não dispara alertas de atividade**.
- `selected`: aprovado editorialmente **e incluído simultaneamente** na configuração de projetos curados. A validação impede marcar `selected` sem configurar o projeto, ou declarar `pending`/`ignored` para um projeto já selecionado.

Para realizar a curadoria, baixe o artefato `external-contributions-preview/candidates.json` da execução recente; `review.new_candidates` mostra projetos ainda não registrados e `review.changed_candidates` lista PRs novos, mudanças de estado e PRs que deixaram de aparecer. Confira o projeto, links e estados e abra um PR revisável para editar `external-contributions-review.json`. Para reconhecer atividade nova, ajuste `observed_prs` e `observed_at` de acordo com o snapshot revisado; para ignorar, marque `ignored` e registre `decision_date` e, se quiser, `reason`. Para selecionar um projeto, adicione-o a `external-contributions.json` com descrições PT-BR/EN, marque `selected` no histórico e registre a data da decisão. Não há token permanente ou atualização automática de decisões humanas.

**Limite importante:** até um candidato inédito ou uma mudança de PR ser reconhecida em um commit revisado, continuará marcado como *não registrado* ou *mudança não reconhecida* nas execuções diárias. Isso não representa um novo evento a cada dia. Para transferências ou renomeações, registre manualmente o nome anterior em `aliases` após verificar a identidade do repositório: a busca não adivinha que dois nomes são o mesmo projeto. Se um projeto selecionado aparecer em novo endereço via alias, o relatório exige atualizar a configuração curada, sem incluir a nova URL automaticamente. Os nomes e aliases são comparados sem diferenciar maiúsculas/minúsculas; o mesmo PR não é contado duas vezes. O script recusa entradas inválidas ou conflitantes antes de buscar a API.

O agendamento utiliza 09:00 UTC diariamente, equivalente a 06:00 no fuso de São Paulo (UTC-3). Como cron do GitHub Actions opera em UTC, alterações futuras nas regras de fuso horário exigirão revisar o cron.

### Publicação testável e validação pós-merge (bugs #20 e #21)

O job de proposta executa `scripts/propose_external_contributions.py`, que também é exercitado nos testes offline. São verificados: elegibilidade para main/schedule/dispatch explícito, SHA do checkout, preservação de todo o texto fora dos marcadores, ausência de diff, PR automático já aberto, avanço concorrente da main, falha de push, recusa de criação de PR, autorização insuficiente e falha ao disparar os checks. O job **não executa** em PRs, pushes de desenvolvimento ou dispatch de prévia. Cada execução e tentativa usa uma branch diferente, `automation/external-contributions-<run_id>-<run_attempt>`; o GitHub incrementa `GITHUB_RUN_ATTEMPT` na reexecução, evitando colisão com a branch deixada por uma tentativa que fez push, mas não conseguiu abrir o PR. Branches sem PR podem permanecer após falhas e devem ser revisadas ou removidas manualmente.

A descoberta opcional utiliza `scripts/prepare_discovery_report.py` para preservar o relatório válido quando a consulta funciona e produzir status `unavailable` quando há erro, sem inventar zero candidatos. Os testes de contrato do workflow verificam que uma falha da descoberta não bloqueia renderização de dados curados; uma falha de coleta curada continua bloqueando qualquer proposta.

**Smoke test após integrar o PR #19 em main, com revisão humana:**

1. Abrir Actions > External open-source contributions > Run workflow, selecionar `main` e manter `publish=false`. Conferir logs dos jobs, relatório da descoberta, snapshot curado, README.md e README.en.md no artefato de prévia. Confirmar que nenhuma branch/PR foi criada.
2. Após conferir a prévia e quando houver uma diferença real nos READMEs, executar `workflow_dispatch` em `main` com `publish=true` de forma controlada, ou aguardar o agendamento. Confirmar que a proposta é feita **em uma branch de automação e por PR**, nunca via push em main. Se não houver diff, o resultado correto é `unchanged` sem PR.
3. Verificar permissão do `GITHUB_TOKEN`, ausência de PR duplicado, disparo de `validate-profile.yml` e `spell-check.yml`, checks obrigatórios e revisão humana antes de qualquer merge. Quando bloqueada pela configuração do repositório, a execução deve indicar falha ou aviso explícito e disponibilizar o artefato de prévia, sem declarar que criou um PR.
4. Para validar o caminho de erro opcional sem criar propostas em produção, usar os testes offline de `tests/test_prepare_discovery_report.py` e `tests/test_workflow_contract.py` e conferir no Actions que a descoberta não é dependência funcional da coleta curada. A falha real da descoberta ainda não foi injetada em uma execução agendada da main.

Nenhum desses passos de produção pode ser declarado aprovado apenas com os testes da branch de desenvolvimento. O intervalo de execução programada permanece diário às 06h de São Paulo (09h UTC), sujeito a atrasos do GitHub Actions.

### Proposta automática já aberta: revisão e reapresentação (issue #23)

**Política editorial:** não atualizar automaticamente uma branch com PR aberto. O novo snapshot gera uma prévia bilíngue, mas o publicador apenas **consulta** o PR pendente para não substituir alterações humanas, invalidar revisões ou interferir em comentários. O GitHub Actions publica o URL do PR e o estado no resumo da execução.

- **Atual:** os dois READMEs do PR coincidem com a prévia mais recente. Nenhum novo PR é aberto.
- **Defasado:** os arquivos do PR diferem da prévia nos blocos gerenciados. O workflow emite um aviso e solicita uma **reapresentação manual**: revisar o PR pendente, preservar os comentários e o trabalho necessário, fechá-lo e executar novamente o workflow em `main` com `publish=true` para gerar uma nova proposta. **Fechar o PR não copia alterações humanas para a nova proposta.**
- **Alterado manualmente:** o PR também modifica conteúdo fora dos marcadores. O workflow não sobrescreve essas edições e exige que um revisor as preserve ou reaplique antes de fechar e reapresentar.
- **Indisponível ou alterado durante a consulta:** branch removida, PR fechado, SHA alterado ou falha de leitura exigem inspeção humana. O workflow não cria outro PR quando não consegue confirmar o estado da proposta existente.
- **PR de um fork com nome de branch semelhante:** não é confundido com uma proposta da automação do próprio repositório. O publicador consulta e valida repositório de origem, número, branch e SHA antes de classificar um PR pendente.

A comparação consulta os dois READMEs pelo **SHA imutável** do PR e confirma a referência da branch, a existência do PR e a integridade do SHA antes e depois. O fluxo mantém as verificações da `main` para impedir uso de prévia renderizada de um commit antigo. O job de escrita continua restrito a execuções elegíveis na `main` e nunca faz merge ou force push.

**Rollout da entrega única:** as melhorias #22 e #23 integram a mesma branch e o mesmo PR #19. Após o merge de #19 na `main`, executar o smoke test de publicação real de #21 e validar a classificação do PR pendente em uma execução controlada; os testes da branch não substituem a validação de produção.
