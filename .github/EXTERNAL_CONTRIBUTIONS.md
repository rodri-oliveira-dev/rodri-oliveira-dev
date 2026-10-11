# Catálogo automatizado de contribuições externas

Esta automação mantém um catálogo bilíngue de todos os Pull Requests públicos abertos por `rodri-oliveira-dev` em repositórios de terceiros. Os READMEs do perfil permanecem estáveis e apontam para os catálogos detalhados. Nenhuma execução escreve diretamente na `main`: alterações factuais são propostas por Pull Request.

## Arquitetura e fonte de dados

O fluxo possui quatro responsabilidades separadas:

1. `scripts/external_contributions.py` consulta a GitHub REST API, valida e normaliza os resultados, reconcilia o snapshot anterior e grava JSON atomicamente.
2. `.github/external-contributions-catalog.json` é o snapshot estruturado, versionado e factual usado como fonte comum dos dois idiomas.
3. `scripts/render_external_contributions.py` valida integralmente o snapshot e renderiza `docs/open-source-contributions.md` e `docs/open-source-contributions.en.md` sem consultar a rede.
4. `scripts/propose_external_contributions.py` cria ou atualiza o único PR automático permitido depois de validar a origem e a integridade dos artefatos.

`.github/external-contributions.json` contém apenas configuração técnica: versão do contrato, login consultado e uma lista opcional de exclusões explícitas. O comportamento padrão inclui toda contribuição pública externa. Uma exclusão exige justificativa técnica ou legal e não funciona como aprovação editorial.

O registro editorial e o relatório separado de candidatos da arquitetura anterior foram removidos. Eles não são mais necessários porque a descoberta global é a única fonte do catálogo.

## Busca global, paginação e particionamento

A consulta base equivale a:

```text
is:pr is:public author:rodri-oliveira-dev -user:rodri-oliveira-dev
```

O coletor acrescenta um intervalo `created:AAAA-MM-DD..AAAA-MM-DD`, cobrindo desde 1º de janeiro de 2008 até a data UTC da execução. Cada intervalo usa páginas de até 100 itens.

A Search API permite acessar no máximo 1.000 resultados por consulta. Quando um intervalo excede esse limite, o coletor divide o período ao meio, em dias inteiros e sem sobreposição, e repete recursivamente. Depois, verifica se a soma dos filhos coincide com o total declarado pelo intervalo pai. Se mais de 1.000 resultados caírem no mesmo dia, o intervalo não puder ser dividido, o total variar entre páginas, `incomplete_results` for verdadeiro ou a quantidade recebida divergir da declarada, a coleta falha. Um catálogo parcial nunca é publicado como completo.

Resultados repetidos são deduplicados por `(repositório, número do PR)`; duplicatas contraditórias são rejeitadas. O `id` global retornado pelo GitHub é preservado como identidade estável adicional. Autor, proprietário, nome do repositório, URL canônica, título, datas e estado são validados antes de qualquer escrita. Repositórios pertencentes ao próprio perfil são excluídos novamente após a busca, como defesa em profundidade.

## Reconciliação e classificação

Cada busca retorna o estado atual de todo o histórico público disponível:

- `open`: PR aberto e `merged_at` nulo;
- `merged`: `merged_at` preenchido e PR fechado;
- `closed_unmerged`: PR fechado e `merged_at` nulo.

O campo `merged_at`, e não apenas `state=closed`, determina a integração. Assim, PRs integrados, fechados sem merge ou reabertos mudam de classificação na sincronização seguinte. Novos PRs e novos repositórios entram sem configuração manual.

O snapshot anterior é usado como guarda de reconciliação. Um PR publicado que desapareça da resposta ou mude de identidade faz a execução falhar, em vez de ser removido silenciosamente. Isso protege contra falhas temporárias de indexação, mudanças de visibilidade e respostas parciais; uma remoção legítima requer investigação e uma alteração revisada.

Projetos são ordenados pela atividade mais recente e, em empate, alfabeticamente. PRs são ordenados pela data de abertura e número, do mais recente para o mais antigo.

## Geração bilíngue

Os catálogos PT-BR e EN são derivados do mesmo JSON validado. Cabeçalhos, rótulos, estados e datas são localizados; títulos de PR permanecem exatamente no idioma original do GitHub. Conteúdo não confiável é escapado para Markdown, e URLs são reconstruídas e validadas no formato canônico.

O renderizador prepara os dois arquivos antes de substituir qualquer um. Cada troca usa `os.replace`; uma falha tenta restaurar ambos a partir de backups locais. Falhas de validação não alteram arquivos existentes.

## Última consulta e última alteração publicada

Uma execução diária bem-sucedida pode confirmar que nada mudou. Nesse caso, o horário real da consulta aparece nos logs e no resumo daquela execução, mas não gera commit.

O campo versionado `last_successful_sync` e a data exibida nos catálogos representam a última sincronização bem-sucedida que produziu a versão factual publicada atual. Quando uma consulta posterior retorna exatamente os mesmos dados, a data versionada anterior é preservada. Isso evita commits causados somente pela passagem do tempo. Portanto:

- **última consulta bem-sucedida:** observável no run do GitHub Actions;
- **última sincronização publicada:** data do snapshot/catálogo que introduziu a versão factual atual.

## Workflow diário e proposta automática

`.github/workflows/external-contributions.yml` executa diariamente às `0 9 * * *` (09:00 UTC, 06:00 em São Paulo no UTC-3) e também por `workflow_dispatch`. Pull Requests que alteram a automação executam validação e testes.

Os jobs de validação, coleta e renderização têm somente `contents: read`. Apenas o job final recebe `contents: write`, `pull-requests: write` e `actions: write`. Ele roda exclusivamente na `main`, para agenda ou despacho manual com publicação habilitada.

A publicação usa a branch fixa `automation/external-contributions`:

- se não houver mudança factual, encerra sem commit;
- se não houver PR aberto, cria branch, commit e PR;
- se houver um PR válido, atualiza a mesma branch por fast-forward, sem force push;
- se a branch gerenciada existir sem um PR aberto, falha com orientação para revisão manual;
- nunca modifica uma branch de fork;
- reconhece somente PR aberto criado por `github-actions[bot]`, no repositório base e na branch exata;
- verifica que o head foi criado com a identidade esperada do bot e que o PR altera somente o snapshot e os dois catálogos;
- qualquer alteração manual inesperada bloqueia a atualização;
- confirma que `main` ainda aponta para o SHA renderizado antes das escritas;
- dispara os workflows obrigatórios de validação do perfil e ortografia.

O grupo de concorrência serializa execuções da mesma referência. Branch protection, rulesets e checks continuam sendo respeitados; não há merge automático.

## Falhas, retries e recuperação

O cliente usa timeout de 10 segundos, até três tentativas, espera acumulada máxima de 20 segundos e orçamento máximo de 50 segundos por requisição lógica. HTTP 408, 429, 500, 502, 503 e 504, timeout e falhas transitórias de rede podem ser repetidos com backoff e jitter. `Retry-After` e `X-RateLimit-Reset` são respeitados dentro do orçamento. Erros permanentes, TLS inválido, JSON malformado e dados inconsistentes falham imediatamente.

Tokens, cabeçalhos e corpos de resposta não são registrados. Uma falha de coleta impede renderização e proposta; o snapshot e os catálogos válidos anteriores permanecem intactos. Artefatos incompletos não chegam ao job com permissão de escrita.

## Execução local

Requer Python 3.10 ou superior e somente a biblioteca padrão.

```bash
python3 -m unittest discover -s tests -v

GITHUB_TOKEN=... python3 scripts/external_contributions.py \
  --config .github/external-contributions.json \
  --previous .github/external-contributions-catalog.json \
  --output build/external-contributions-catalog.json

python3 scripts/render_external_contributions.py \
  --snapshot build/external-contributions-catalog.json \
  --output-pt build/open-source-contributions.md \
  --output-en build/open-source-contributions.en.md \
  --write
```

Para reproduzir uma sincronização, compare o JSON e os dois Markdown gerados com os arquivos versionados. Execute o renderizador novamente e confirme que não há diferenças. Nunca passe o token por argumento, arquivo versionado ou saída de log.

## Limitações conhecidas

- A Search API pode ter atraso de indexação; as verificações de consistência reduzem o risco, mas não tornam o índice transacional.
- O limite de 1.000 resultados é contornado por partições diárias; mais de 1.000 resultados em um único dia causam falha explícita.
- Somente PRs públicos e atualmente visíveis à credencial do workflow pertencem ao escopo.
- Um PR publicado que deixe de ser público bloqueia a reconciliação até revisão humana, por segurança.
- O GitHub não oferece uma transação única para substituir vários arquivos; o renderizador usa staging, substituição atômica por arquivo e rollback de melhor esforço.
