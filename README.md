**Português** | [English](README.en.md) | [Español (Latinoamérica)](README.es.md)
<!-- cspell:words Español Latinoamérica -->

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Portfólio profissional">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Arquiteto de Software · Sistemas Distribuídos · .NET · Cloud**

*Software architect working hands-on with .NET, distributed systems, cloud, architecture governance, and open-source developer tooling.*

Há mais de 20 anos, trabalho no desenvolvimento e na evolução de sistemas corporativos, com foco em arquitetura de software, integrações e modernização de aplicações. Procuro equilibrar necessidades de negócio, decisões técnicas e a realidade operacional dos sistemas.

Aqui compartilho ferramentas, bibliotecas e laboratórios open source que ajudam a transformar decisões de arquitetura e governança em código, testes e automação.

**Links profissionais**

- [Portfólio profissional](https://rodri-oliveira-dev.github.io/)
- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)
- [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Projetos selecionados

Ferramentas, bibliotecas e laboratórios que conectam decisões de arquitetura à implementação e à operação.

### [ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)

*Ferramenta de governança arquitetural*

Ajuda equipes a manter registros de decisão consistentes e rastreáveis. A CLI em .NET cria, valida e indexa ADRs; análises opcionais de impacto e desvios arquiteturais trabalham com evidências delimitadas, sem substituir o julgamento humano. O [estudo de caso](https://rodri-oliveira-dev.github.io/case-studies/adr-guard/) detalha decisões e trade-offs.

### [Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

*Biblioteca .NET*

Resolve mapeamentos entre objetos .NET e colunas quando as convenções do Dapper não bastam, sem adicionar atributos aos modelos. A evolução da biblioteca combina API fluente, extensibilidade e compatibilidade com aplicações existentes, evidenciando manutenção de APIs públicas e modernização incremental. O [estudo de caso](https://rodri-oliveira-dev.github.io/case-studies/dapper-fluentmap/) discute os limites dessa abstração.

### [Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)

*Ferramenta de documentação arquitetural*

Reduz a divergência entre código e diagramas ao transformar evidências delimitadas de repositórios .NET em documentação C4/LikeC4 revisável. O fluxo separa observações de hipóteses e exige aplicação explícita, demonstrando análise estática, geração determinística e integração com agentes via MCP.

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

*Laboratório de sistemas distribuídos*

Torna decisões sobre consistência eventual, falhas e rastreabilidade reproduzíveis em uma base de serviços distribuídos em .NET. Implementa DDD, integração assíncrona com Kafka e Outbox, testes e runbooks, deixando propostas sem evidência marcadas explicitamente como pendentes.

### [ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)

*Biblioteca .NET para integração*

Trata falhas, concorrência e duplicidade na entrega de webhooks de saída. IDs estáveis tornam o enfileiramento idempotente, enquanto concessões temporárias e novas tentativas sustentam entrega at-least-once com armazenamento durável fornecido pela aplicação; o destinatário ainda precisa tolerar duplicatas. O [estudo de caso](https://rodri-oliveira-dev.github.io/case-studies/reliable-webhooks/) examina essas garantias e seus limites.

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)

*Ferramenta de análise estática*

Identifica padrões de custo e regressões de complexidade antes que cheguem à execução. O analisador Roslyn estima Big-O quando há evidência suficiente, aplica métricas configuráveis no build e na IDE e retorna resultado indeterminado em vez de inferir além do que o código permite.

Outros trabalhos: [Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard), painel de CI, releases, segurança e saúde dos repositórios, e a [lista completa de repositórios](https://github.com/rodri-oliveira-dev?tab=repositories).

---

## Contribuições open source

Algumas contribuições integradas que representam correção, manutenção e segurança em bases existentes:

- **Ocelot — [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420):** corrigiu o mapeamento de timeouts do serviço de destino para HTTP 504 conforme a RFC 9110, preservando cancelamento do cliente e comportamento de QoS, com testes unitários e de aceitação.
- **MySqlConnector — [PR #1675](https://github.com/mysql-net/MySqlConnector/pull/1675):** removeu a detecção obsoleta do Azure MySQL Single Server, preservando o caminho do AWS RDS Proxy e simplificando a lógica de conexão.
- **OpenCNPJ — [PR #75](https://github.com/Hitmasu/OpenCNPJ/pull/75):** centralizou downloads externos em um fluxo com timeouts, limites de tamanho, arquivos temporários e limpeza em falhas, acompanhado por testes e validação em CI.

O [catálogo completo de contribuições open source](docs/open-source-contributions.md) mantém os demais Pull Requests e seus estados atualizados automaticamente.

## Governança como código

No repositório **[.github](https://github.com/rodri-oliveira-dev/.github)**, reúno políticas e automações compartilháveis: padrões de contribuição e segurança, inventário de projetos .NET, verificação de segredos e distribuição controlada de skills para agentes. As mudanças passam por Pull Request e cada repositório mantém autonomia para adotar suas regras.

## Como trabalho

Procuro entender o contexto, as dependências e os limites operacionais antes de propor uma solução. Discuto alternativas e trade-offs com os times, registro decisões relevantes em ADRs e acompanho a implementação por meio de testes, observabilidade e automação.

## Publicações e conteúdo técnico

Escrevo sobre arquitetura de software, DDD e desenvolvimento .NET, principalmente sobre decisões e problemas encontrados na prática.

- **[Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)** — newsletter sobre arquitetura e engenharia de software.
