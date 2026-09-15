[Português](README.md) | **English**

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Professional portfolio">
    <img src="assets/brand/ro-architect-mark.svg" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Software Architect | Distributed Systems | .NET | Cloud | DDD | Governance as Code**

I'm a Software Architect with more than 20 years of experience building, modernizing, and evolving enterprise software.

I work at the intersection of **business, architecture, and engineering**, turning needs, quality attributes, and operational constraints into technical decisions that teams can implement, observe, operate, and evolve.

My focus is turning **architectural decisions into code, contracts, guardrails, and automation**, keeping architecture close enough to engineering that its assumptions can be validated in practice.

**[Professional portfolio](https://rodri-oliveira-dev.github.io/)** · [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev) · [Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945) · [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Architecture in practice

My open-source projects make part of my engineering reasoning inspectable. The central point is not the technology in isolation, but **the problem, the constraints, the decision, and how that decision can be validated through code, infrastructure, and automation**.

| Project | Problem, decision, and evidence |
| --- | --- |
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | How to preserve consistency and traceability across distributed services: DDD, bounded contexts, Kafka, Outbox/Inbox, idempotency, sagas, OpenTelemetry, ADRs, and runbooks make trade-offs and failure modes explicit. |
| **[ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)** | How to deliver webhooks reliably in failure-prone environments: at-least-once delivery, leases, bounded concurrency, deterministic retries, HMAC-SHA256, observability, and destination policies make reliability and security explicit responsibilities. |
| **[Terraform GCP .NET Blueprint](https://github.com/rodri-oliveira-dev/terraform-gcp-dotnet-blueprint)** | How to turn infrastructure decisions into a reproducible baseline: Terraform, Cloud Run, Cloud Run Jobs, Pub/Sub, DLQ, Redis, Secret Manager, VPC, IAM, Workload Identity Federation, CI, and observability form a production-oriented reference for .NET workloads on Google Cloud. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | How to make architectural decisions verifiable and automatable: deterministic ADR validation and indexing, stable CI/CD rules, and AI-assisted drafting while keeping context, review, and architectural acceptance under human control. |
| **[DotNetRepoInspector](https://github.com/rodri-oliveira-dev/DotNetRepoInspector)** | How to apply governance to .NET repositories without fragile heuristics: evaluated MSBuild metadata is treated as the source of truth and exposed through deterministic contracts for CI/CD and automation. |
| **[.NET Library Template](https://github.com/rodri-oliveira-dev/dotnet-library-template)** | How to turn recurring build, testing, security, packaging, versioning, and release practices into a reusable golden path, including package validation, NuGet Audit, CodeQL, OIDC-based Trusted Publishing, and software supply-chain controls. |
| **[ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)** | How to turn code complexity into automated development feedback: Roslyn analysis for algorithmic, cyclomatic, cognitive, and structural complexity, with conservative behavior when an inference cannot be made safely. |

[Explore all repositories →](https://github.com/rodri-oliveira-dev?tab=repositories)

---

## Governance as code

Sustainable architecture also requires operational and engineering standards to become executable.

The **[.github](https://github.com/rodri-oliveira-dev/.github)** repository acts as a small **engineering control plane** for the projects I maintain: it centralizes contribution and security standards, automates cross-repository maintenance, inventories .NET projects from evaluated MSBuild metadata, provides reusable secret scanning, and governs the synchronization and distribution of instructions and skills for development agents.

The automations follow **least privilege, review-gated changes, safe defaults, and repository-local authority**. Write operations flow through reviewable Pull Requests, while read-only workflows remain isolated from mutation permissions.

This reflects one of the principles behind my work: **prefer automated guardrails over bureaucratic processes whenever a rule can provide useful feedback to engineering teams**.

---

## Open-source maintenance

I also maintain projects with an established history, user base, and public contracts.

**[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** — current maintainer of the fluent mapping library for Dapper, originally created by **Henk Mollema**. I am leading its revival and modernization, preserving compatibility with the existing ecosystem while evolving the runtime, tooling, CI/CD, quality, security, and distribution strategy for the project's next generation.

Maintaining an established project requires a different kind of engineering: **evolving the software without disregarding the contract built with its users over the years**.

---

## Open-source contributions

Contributing to codebases I do not control is another way to make my engineering verifiable: understanding existing decisions, respecting project contracts and conventions, discussing trade-offs, and delivering changes that fit the surrounding ecosystem.

| Project | Contribution |
| --- | --- |
| **[Ocelot](https://github.com/ThreeMammals/Ocelot)** | [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420): map downstream timeouts to **504 Gateway Timeout**, aligned with RFC 9110. [PR #2421](https://github.com/ThreeMammals/Ocelot/pull/2421): regression coverage for `multipart/form-data` rerouting while preserving the body, boundary, and file metadata. |
| **[CrispyWaffle](https://github.com/guibranco/CrispyWaffle)** | [PR #980](https://github.com/guibranco/CrispyWaffle/pull/980): YAML serialization support using YamlDotNet, integrated with the existing abstractions, tests, and documentation. |
| **[Architecture Decision Record](https://github.com/architecture-decision-record/architecture-decision-record)** | [PR #115](https://github.com/architecture-decision-record/architecture-decision-record/pull/115): complete Brazilian Portuguese localization while preserving structure, references, and identity across equivalent content. |

**[Track contributions and work in progress →](https://github.com/users/rodri-oliveira-dev/projects/1/views/1)**  
I use this GitHub Project to track issues, contributions, and open-source initiatives that I am working on, evaluating, or have previously worked on.

---

## How I think about architecture

A few principles guide my work:

- **Start from the problem, not the pattern.**
- **Treat constraints as part of the design.**
- **Make decisions and trade-offs explicit.**
- **Design for failure and operation from the beginning.**
- **Prefer guardrails over bureaucracy.**
- **Stay close enough to the code to validate architectural decisions.**
- **Automate standards when automation creates useful feedback for teams.**

These principles also shape my [professional portfolio](https://rodri-oliveira-dev.github.io/), where I present my work across software architecture, distributed systems, cloud, DDD, and engineering practice in more depth.

---

## Technical content

I write about software architecture, Domain-Driven Design, distributed systems, backend engineering, software quality, cloud, engineering governance, and technical decision-making.

- **[Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)** — newsletter about software architecture, Domain-Driven Design, distributed systems, backend engineering, software quality, and the trade-offs behind technical decisions;
- **[NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)** — published .NET libraries, tools, and templates;
- **[Portfolio](https://rodri-oliveira-dev.github.io/)** — consolidated view of my professional work;
- **[LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)** — career, experience, and professional presence.

---

## GitHub Activity

<p align="left">
  <img
    src="https://github-stats-extended.vercel.app/api?username=rodri-oliveira-dev&show_icons=true&theme=transparent&locale=en&show=prs_merged,prs_reviewed&hide_border=true&hide_title=true"
    alt="Rodrigo de Oliveira's GitHub statistics"
  />
</p>
