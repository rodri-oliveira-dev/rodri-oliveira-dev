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

## Arquitetura na prática

Nos projetos open source, parte do meu raciocínio técnico fica visível no código. O que me interessa não é a tecnologia isolada, mas **o problema, as restrições, a decisão tomada e como essa decisão pode ser verificada na implementação, na infraestrutura ou na automação**.

| Projeto | Problema, decisão e evidência |
| --- | --- |
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | Explora consistência e rastreabilidade entre serviços distribuídos com DDD, bounded contexts, Kafka, Outbox/Inbox, idempotência, sagas, OpenTelemetry, ADRs e runbooks. Os trade-offs e modos de falha fazem parte do desenho. |
| **[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** | Biblioteca de mapeamento fluente para Dapper da qual sou o mantenedor atual. O trabalho combina preservação de compatibilidade com modernização de runtime, tooling, CI/CD, qualidade, segurança e distribuição, tratando evolução de contrato público como uma restrição arquitetural explícita. |
| **[Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)** | Trata a divergência entre código e diagramas como um problema de evidência e revisão: transforma evidências verificáveis de repositórios .NET em documentação C4/LikeC4 revisável, com C1/C2, C3 seletivo, CLI e [MCP local via stdio](https://github.com/rodri-oliveira-dev/Repo2C4/blob/main/docs/mcp.pt-BR.md). Na evolução atual, adiciona um Agent baseado em Microsoft Agent Framework para orquestrar análise evidence-first, validação e correção limitada, mantendo aprovação humana antes de qualquer escrita. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | Torna ADRs verificáveis no fluxo de engenharia: valida e indexa decisões de forma determinística por CLI, containers e GitHub Action, e oferece drafting assistido por IA sem retirar das pessoas a revisão e a aceitação arquitetural. |
| **[DotNetRepoInspector](https://github.com/rodri-oliveira-dev/DotNetRepoInspector)** | Usa metadados avaliados pelo MSBuild como fonte de verdade para inventário e governança, expondo o mesmo contrato determinístico por CLI/.NET Tool, GitHub Action e servidor MCP local read-only. Está evoluindo para descobrir integrações externas — HTTP, mensageria multi-cloud, bancos, cache e storage — como fatos estruturados reutilizáveis por outras ferramentas. |
| **[Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard)** | Camada de observabilidade do portfólio de repositórios: consolida CI, delivery, releases, atividade, segurança, pacotes e sinais de saúde em um snapshot estático coletado por GitHub Actions e publicado em uma SPA Angular no GitHub Pages, com cobertura e confiança explícitas para dados parciais. |
| **[.NET Library Template](https://github.com/rodri-oliveira-dev/dotnet-library-template)** | Consolida práticas recorrentes de build, testes, segurança, empacotamento e release em um golden path reutilizável, com package validation, NuGet Audit, CodeQL, Trusted Publishing via OIDC e controles de software supply chain. |
| **[ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)** | Leva análise de complexidade para perto do desenvolvimento com analyzers Roslyn para complexidade algorítmica, ciclomática, cognitiva e estrutural, usando uma abordagem conservadora quando a inferência não é segura. |

**DotNetRepoInspector identifica fatos técnicos do repositório; Repo2C4 usa evidências verificáveis para interpretá-los arquiteturalmente e produzir documentação C4 revisável.**

[Ver todos os repositórios →](https://github.com/rodri-oliveira-dev?tab=repositories)

---

## Governança como código

Arquitetura sustentável também depende de transformar padrões recorrentes em feedback e automação, em vez de depender apenas de documentação ou processo manual.

O repositório **[.github](https://github.com/rodri-oliveira-dev/.github)** funciona como uma camada central de governança e automação para os projetos que mantenho. Ele concentra padrões de contribuição e segurança, manutenção cross-repository, inventário de projetos .NET, secret scanning reutilizável e um registro versionado de governança para agentes, com sincronização de skills upstream e distribuição controlada por Pull Request.

As automações seguem **menor privilégio, mudanças via Pull Request, defaults seguros e autonomia local dos repositórios**. Operações de escrita passam por revisão; fluxos somente leitura não recebem permissões de mutação.

A ideia é simples: **quando uma regra pode gerar feedback útil automaticamente, prefiro um guardrail a mais uma etapa burocrática**.

---

## Contribuições open source

Contribuir em bases de código que não controlo também expõe uma parte importante da engenharia: entender decisões existentes, respeitar contratos e convenções, discutir trade-offs e entregar mudanças que façam sentido dentro daquele ecossistema.

O histórico completo de Pull Requests públicos em projetos de terceiros é descoberto e reconciliado automaticamente, sem depender de uma lista editorial de repositórios.

**[Ver o catálogo completo de contribuições open source →](docs/open-source-contributions.md)**

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
