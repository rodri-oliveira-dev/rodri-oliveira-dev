[Português](README.md) | **English**

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Professional portfolio">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Software Architect · Distributed Systems · .NET · Cloud**

I have more than 20 years of experience developing and evolving enterprise systems, with a focus on software architecture, integrations, and application modernization. I aim to balance business needs, technical decisions, and the operational realities of existing systems.

Here I share tools, libraries, and experiments that help turn architectural decisions into code, tests, and automation.

**Professional links**

- [Professional portfolio](https://rodri-oliveira-dev.github.io/)
- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [DEV.to](https://dev.to/rodri-oliveira-dev)
- [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Selected projects

Tools, libraries, and labs that connect architecture decisions with implementation and operations.

### [ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)

*Architecture governance tool*

Helps teams keep decision records consistent and traceable. Its .NET CLI creates, validates, and indexes ADRs; optional impact and drift analysis works from bounded evidence without replacing architectural judgment. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/adr-guard/) examines the underlying decisions and trade-offs.

### [Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

*.NET library*

Handles mappings between .NET objects and database columns when Dapper's conventions are not enough, without adding attributes to domain models. Its evolution balances a fluent API, extensibility, and compatibility with existing applications, showing long-term public API stewardship and incremental modernization. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/dapper-fluentmap/) discusses the boundaries of that abstraction.

### [Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)

*Architecture documentation tool*

Reduces drift between code and diagrams by turning bounded evidence from .NET repositories into reviewable C4/LikeC4 documentation. Its workflow separates observations from hypotheses and requires explicit writes, demonstrating static analysis, deterministic generation, and MCP-based agent integration.

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

*Distributed-systems lab*

Makes decisions around eventual consistency, failure handling, and traceability reproducible in a .NET microservices foundation. It implements DDD, asynchronous Kafka integration with Outbox, tests, and runbooks while keeping proposals without code evidence explicitly marked as pending.

### [ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)

*.NET integration library*

Addresses failure, concurrency, and duplication in outbound webhook delivery. Stable IDs make enqueueing idempotent, while leases and retries support at-least-once delivery with a durable store supplied by the application; receivers must still tolerate duplicates. The [case study](https://rodri-oliveira-dev.github.io/en/case-studies/reliable-webhooks/) examines these guarantees and their limits.

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)

*Static analysis tool*

Surfaces costly patterns and complexity regressions before runtime. The Roslyn analyzer estimates Big-O when evidence is sufficient, enforces configurable metrics in builds and IDEs, and reports an unknown result rather than inferring beyond what the code can support.

Other work remains available through [Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard), a dashboard for repository CI, releases, security, and health, and the [full repository list](https://github.com/rodri-oliveira-dev?tab=repositories).

---

## Open-source contributions

Selected merged contributions that demonstrate correction, maintenance, and security work in existing codebases:

- **Ocelot — [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420):** corrected downstream timeout mapping to HTTP 504 under RFC 9110 while preserving client cancellation and QoS behavior, with unit and acceptance tests.
- **MySqlConnector — [PR #1675](https://github.com/mysql-net/MySqlConnector/pull/1675):** removed retired Azure MySQL Single Server detection while preserving the AWS RDS Proxy path and simplifying connection logic.
- **OpenCNPJ — [PR #75](https://github.com/Hitmasu/OpenCNPJ/pull/75):** centralized external downloads behind timeouts, size limits, temporary files, and failure cleanup, backed by tests and CI validation.

The [full open-source contribution catalog](docs/open-source-contributions.en.md) keeps the remaining Pull Requests and their statuses automatically reconciled.

## Governance as code

The **[.github](https://github.com/rodri-oliveira-dev/.github)** repository brings together reusable policies and automation: contribution and security standards, a .NET project inventory, secret scanning, and controlled distribution of agent skills. Changes go through Pull Requests, and individual repositories retain control over their own rules.

## How I work

I start by understanding context, dependencies, and operational constraints. I discuss alternatives and trade-offs with teams, document significant decisions in ADRs, and stay close to implementation through tests, observability, and automation.

## Writing and technical content

I write about software architecture, DDD, and .NET development, focusing on decisions and problems encountered in practice.

- **[DEV.to](https://dev.to/rodri-oliveira-dev)** — articles about software architecture and engineering.
