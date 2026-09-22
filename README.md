**Português** | [English](README.en.md)

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Portfólio profissional">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Arquiteto de Software | Sistemas Distribuídos | .NET | Cloud | DDD | Governança como Código**

Sou arquiteto de software com mais de 20 anos de experiência construindo, modernizando e evoluindo sistemas corporativos.

Atuo na interseção entre **negócio, arquitetura e engenharia**, transformando necessidades, atributos de qualidade e restrições operacionais em decisões técnicas que os times conseguem implementar, observar, operar e evoluir.

Meu foco é transformar **decisões arquiteturais em código, contratos, guardrails e automação**, mantendo a arquitetura próxima o suficiente da engenharia para que suas premissas possam ser validadas na prática.

**[Portfólio profissional](https://rodri-oliveira-dev.github.io/)** · [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev) · [Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945) · [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Impacto selecionado

Além do trabalho open source, minha trajetória inclui resultados mensuráveis em sistemas corporativos: **30% de redução no tempo de resposta** de um fluxo crítico .NET/HANA, **40% de redução no tempo médio de detecção e resposta a incidentes** e novas integrações realizadas em **aproximadamente um terço do tempo** após o redesenho de APIs e fronteiras.

Os resultados quantitativos são de projetos realizados em **2020–2021**. **[Ver contexto, decisões e resultados no portfólio →](https://rodri-oliveira-dev.github.io/#practice)**

---

## Arquitetura na prática

Nos projetos open source, parte do meu raciocínio técnico fica visível no código. O que me interessa não é a tecnologia isolada, mas **o problema, as restrições, a decisão tomada e como essa decisão pode ser verificada na implementação, na infraestrutura ou na automação**.

| Projeto | Problema, decisão e evidência |
| --- | --- |
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | Explora consistência e rastreabilidade entre serviços distribuídos com DDD, bounded contexts, Kafka, Outbox/Inbox, idempotência, sagas, OpenTelemetry, ADRs e runbooks. Os trade-offs e modos de falha fazem parte do desenho. |
| **[dotnet-observability-lab](https://github.com/rodri-oliveira-dev/dotnet-observability-lab)** | Laboratório executável com .NET 10, Aspire e OpenTelemetry para processamento assíncrono confiável, Outbox/Inbox, at-least-once delivery e idempotência. ADRs e LikeC4 formam uma arquitetura versionada, validada no CI e publicada como documentação interativa. |
| **[ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)** | Trata entrega de webhooks como um problema de confiabilidade: at-least-once delivery, leases, concorrência limitada, retries determinísticos, HMAC-SHA256, observabilidade e políticas de destino são responsabilidades explícitas e testáveis. |
| **[Terraform GCP .NET Blueprint](https://github.com/rodri-oliveira-dev/terraform-gcp-dotnet-blueprint)** | Reúne uma baseline reproduzível para workloads .NET no Google Cloud com Terraform, Cloud Run, Jobs, Pub/Sub, DLQ, Redis, Secret Manager, VPC, IAM, Workload Identity Federation, CI e observabilidade. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | Torna ADRs verificáveis no fluxo de engenharia: valida e indexa decisões de forma determinística por CLI, containers e GitHub Action, e oferece drafting assistido por IA sem retirar das pessoas a revisão e a aceitação arquitetural. |
| **[DotNetRepoInspector](https://github.com/rodri-oliveira-dev/DotNetRepoInspector)** | Usa metadados avaliados pelo MSBuild como fonte de verdade para inventário e governança, expondo o mesmo contrato determinístico por CLI/.NET Tool, GitHub Action e servidor MCP local read-only. |
| **[.NET Library Template](https://github.com/rodri-oliveira-dev/dotnet-library-template)** | Consolida práticas recorrentes de build, testes, segurança, empacotamento e release em um golden path reutilizável, com package validation, NuGet Audit, CodeQL, Trusted Publishing via OIDC e controles de software supply chain. |
| **[ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)** | Leva análise de complexidade para perto do desenvolvimento com analyzers Roslyn para complexidade algorítmica, ciclomática, cognitiva e estrutural, usando uma abordagem conservadora quando a inferência não é segura. |

[Ver todos os repositórios →](https://github.com/rodri-oliveira-dev?tab=repositories)

---

## Governança como código

Arquitetura sustentável também depende de transformar padrões recorrentes em feedback e automação, em vez de depender apenas de documentação ou processo manual.

O repositório **[.github](https://github.com/rodri-oliveira-dev/.github)** funciona como uma camada central de governança e automação para os projetos que mantenho. Ele concentra padrões de contribuição e segurança, manutenção cross-repository, inventário de projetos .NET, secret scanning reutilizável e um registro versionado de governança para agentes, com sincronização de skills upstream e distribuição controlada por Pull Request.

As automações seguem **menor privilégio, mudanças via Pull Request, defaults seguros e autonomia local dos repositórios**. Operações de escrita passam por revisão; fluxos somente leitura não recebem permissões de mutação.

A ideia é simples: **quando uma regra pode gerar feedback útil automaticamente, prefiro um guardrail a mais uma etapa burocrática**.

---

## Manutenção open source

Também mantenho projetos que já possuem histórico, usuários e contratos públicos estabelecidos.

**[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** — sou o mantenedor atual da biblioteca de mapeamento fluente para Dapper, criada originalmente por **Henk Mollema**. Estou conduzindo sua retomada e modernização, preservando compatibilidade com o ecossistema existente enquanto evoluo runtime, tooling, CI/CD, qualidade, segurança e estratégia de distribuição.

Esse trabalho exige um tipo diferente de decisão: **evoluir o projeto sem ignorar o contrato construído ao longo dos anos com quem já depende dele**.

---

## Contribuições open source

Contribuir em bases de código que não controlo também expõe uma parte importante da engenharia: entender decisões existentes, respeitar contratos e convenções, discutir trade-offs e entregar mudanças que façam sentido dentro daquele ecossistema.

| Projeto | Contribuição |
| --- | --- |
| **[Ocelot](https://github.com/ThreeMammals/Ocelot)** | [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420): tratamento de timeout downstream como **504 Gateway Timeout**, alinhado à RFC 9110. [PR #2421](https://github.com/ThreeMammals/Ocelot/pull/2421): cobertura de regressão para roteamento de `multipart/form-data`, preservando body, boundary e metadados do arquivo. |
| **[CrispyWaffle](https://github.com/guibranco/CrispyWaffle)** | [PR #980](https://github.com/guibranco/CrispyWaffle/pull/980): suporte a serialização YAML com YamlDotNet, integração com as abstrações existentes, testes e documentação. |
| **[Architecture Decision Record](https://github.com/architecture-decision-record/architecture-decision-record)** | [PR #115](https://github.com/architecture-decision-record/architecture-decision-record/pull/115): localização completa para Português do Brasil, preservando estrutura, referências e identidade entre os conteúdos equivalentes. |
| **[LikeC4](https://github.com/likec4/likec4)** | Expansão da localização oficial para **Português do Brasil**: [PR #3179](https://github.com/likec4/likec4/pull/3179) introduziu o README em pt-BR, suporte de internacionalização e o tutorial; [PR #3236](https://github.com/likec4/likec4/pull/3236) traduziu Guides e os fundamentos da DSL; [PR #3262](https://github.com/likec4/likec4/pull/3262) completou a localização da documentação de Views da DSL, preservando sintaxe, exemplos e terminologia arquitetural. |

**[Acompanhar contribuições e trabalho em andamento →](https://github.com/users/rodri-oliveira-dev/projects/1/views/1)**  
Uso este GitHub Project para acompanhar issues, contribuições e iniciativas open source em que estou atuando, avaliando ou em que já atuei.

---

## Como penso arquitetura

Alguns princípios orientam meu trabalho:

- **Começar pelo problema, não pelo padrão.**
- **Tratar restrições como parte do design.**
- **Tornar decisões e trade-offs explícitos.**
- **Projetar para falhas e operação desde o início.**
- **Preferir guardrails a burocracia.**
- **Manter arquitetura próxima o suficiente do código para validar decisões.**
- **Automatizar padrões quando isso gera feedback útil para os times.**

Esse é também o fio condutor do meu [portfólio profissional](https://rodri-oliveira-dev.github.io/), onde apresento minha atuação em arquitetura, sistemas distribuídos, cloud, DDD e engenharia de software de forma mais completa.

---

## Conteúdo técnico

Escrevo sobre arquitetura de software, Domain-Driven Design, sistemas distribuídos, backend, qualidade, cloud, governança técnica e decisões de engenharia.

- **[Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)** — newsletter sobre arquitetura de software, Domain-Driven Design, sistemas distribuídos, backend, qualidade e os trade-offs por trás das decisões técnicas;
- **[NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)** — bibliotecas, ferramentas e templates .NET publicados;
- **[Portfólio](https://rodri-oliveira-dev.github.io/)** — visão consolidada da minha atuação profissional;
- **[LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)** — trajetória, experiência e presença profissional.

---

## Atividade no GitHub

<p align="left">
  <img
    src="https://github-stats-extended.vercel.app/api?username=rodri-oliveira-dev&show_icons=true&theme=transparent&locale=en&show=prs_merged,prs_reviewed&hide_border=true&hide_title=true"
    alt="Estatísticas do GitHub de Rodrigo de Oliveira"
  />
</p>
