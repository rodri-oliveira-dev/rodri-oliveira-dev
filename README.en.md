[Português](README.md) | **English** | [Español (Latinoamérica)](README.es.md)
<!-- cspell:words Español Latinoamérica -->

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Professional portfolio">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Software Architect · Distributed Systems · .NET · Cloud**
I started out as a software developer, mostly working with .NET. Over more than 20 years, I've worked with enterprise systems, integrations, and legacy modernization. Today I'm a software architect at CI&T, focused on lending and credit solutions. I support two engineering teams and work closely with product, tech leads, and fellow architects.

One project that shaped my approach was modernizing a system in the insurance sector. I defined the architecture for moving business rules out of stored procedures and into microservices, established the boundaries between services, and followed the implementation through production rollout. Monitoring showed fewer transactions ending in errors after the change.

I've also worked on high-volume, business-critical systems, investigated production integration issues, and helped fix problems with API contracts and communication. My experience includes implementing applications and services on Google Cloud and contributing to shared API and integration standards through the Architecture Center of Excellence. I've also served as a tech lead and Career Advisor, supported other engineers' growth, and taken part in adopting AI tools for software development.

This profile brings together the libraries, tools, and hands-on labs I maintain to test ideas and share what I learn. I like staying close to the code; it keeps architectural decisions grounded in real implementation.

<p align="center">
  <picture>
    <source
      media="(max-width: 767px)"
      srcset="assets/profile/software-architecture-in-practice.en.mobile.png"
    />
    <img
      src="assets/profile/software-architecture-in-practice.en.png"
      alt="Software architecture in practice: business, teams, organization, and evolution shape architectural decisions, supported by code, tests, observability, and automation. Featured projects: ADR Guard, Repo2C4, Complexity Analyzers, Dapper.FluentMap, and POC Arquitetura."
      width="100%"
    />
  </picture>
</p>

**Professional links**

- 🧭 [Professional portfolio](https://rodri-oliveira-dev.github.io/)
- 📄 [Resume](https://rodri-oliveira-dev.github.io/en/resume/)
- 🤝 [Consulting services](https://rodri-oliveira-dev.github.io/en/services/)
- 💼 [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- ✍️ [DEV.to](https://dev.to/rodri-oliveira-dev)
- 📦 [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Selected projects

Tools, libraries, and labs that connect architectural decisions to implementation and day-to-day operations.

### [ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)

*Architecture governance tool*

Helps teams keep architecture decision records (ADRs) consistent and traceable. Its .NET CLI creates, validates, and indexes ADRs. Optional impact and drift analyses rely on clearly scoped evidence and support, rather than replace, architectural judgment. An independent [read-only MCP server](https://github.com/rodri-oliveira-dev/adr-guard/blob/main/docs/mcp.md) offers tools to compatible agents, while [Agent Skills](https://github.com/rodri-oliveira-dev/adr-guard/blob/main/docs/skills/README.md) guide their use without delegating architectural decisions. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/adr-guard/) explores the decisions and trade-offs behind the tool.

### [Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

*.NET library*

Maps .NET objects to database columns when Dapper's default conventions fall short, without adding attributes to domain models. Its ongoing development balances a fluent API and extensibility with compatibility for existing applications. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/dapper-fluentmap/) explores the benefits and limits of this abstraction.

### [Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)

*Architecture documentation tool*

Helps keep architecture diagrams aligned with code by generating reviewable C4/LikeC4 documentation from clearly scoped evidence in .NET repositories. Its workflow separates observations from hypotheses and writes files only when explicitly requested. It demonstrates static analysis, deterministic generation, and MCP-based agent integration.

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

*Distributed-systems lab*

Provides a reproducible .NET microservices environment for exploring eventual consistency, failure handling, and traceability. It uses DDD and asynchronous Kafka integration with the Outbox pattern, alongside tests and runbooks. Proposals not yet supported by code are clearly marked as pending.

### [ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)

*.NET integration library*

Addresses failures, concurrent processing, and duplicate requests in outbound webhook delivery. Stable IDs make enqueue operations idempotent. Leases and retries support at-least-once delivery through an application-provided durable store, so receivers still need to handle duplicates. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/reliable-webhooks/) explains these guarantees and their limits.

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)

*Static analysis tool*

Flags potentially costly patterns and complexity regressions during development. When there is enough evidence, the Roslyn analyzer estimates Big-O complexity. It also enforces configurable metrics in builds and IDEs, and reports an unknown result when the code does not support a reliable estimate.

For a broader view, see [Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard), a dashboard for repository CI, releases, security, and health, or browse the [full repository list](https://github.com/rodri-oliveira-dev?tab=repositories).

---

## Open-source contributions

Selected merged pull requests showing bug fixes, maintenance, and security improvements in established codebases:

- **Ocelot — [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420):** fixed downstream timeout mapping to HTTP 504 in line with RFC 9110, while preserving client cancellation and QoS behavior, with unit and acceptance tests.
- **MySqlConnector — [PR #1675](https://github.com/mysql-net/MySqlConnector/pull/1675):** removed detection for the retired Azure MySQL Single Server service while preserving AWS RDS Proxy support and simplifying connection logic.
- **OpenCNPJ — [PR #75](https://github.com/Hitmasu/OpenCNPJ/pull/75):** added safeguards for external downloads, including timeouts, size limits, temporary files, and cleanup on failure, backed by tests and CI validation.

The [full open-source contribution catalog](docs/open-source-contributions.en.md) automatically tracks other pull requests and their current statuses.

## Governance as code

The **[.github](https://github.com/rodri-oliveira-dev/.github)** repository brings together reusable policies and automation, including contribution and security standards, a .NET project inventory, secret scanning, and controlled distribution of agent skills. Changes go through pull requests, and each repository retains control over its own rules.

## How I think about architecture

Years of software development have taught me that an architectural decision needs to work after deployment, too. It affects the people building, operating, and evolving the system.

That's why I prefer to start with the problem and the actual constraints. I discuss options with the teams, weigh trade-offs, and try to avoid complexity that doesn't bring value. I don't believe in designing architecture in isolation and handing it down as a set of rules.

I like staying close to the code and the people who maintain it. It helps me revisit my decisions and learn from what happens in production.

## Writing and technical content

I write about software architecture, DDD, and .NET development, drawing on real-world engineering decisions and challenges.

- **[DEV.to](https://dev.to/rodri-oliveira-dev)** — articles about software architecture and engineering.

[Accessibility statement](ACCESSIBILITY.md#english)
