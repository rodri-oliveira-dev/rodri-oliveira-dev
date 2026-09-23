[Português](README.md) | **English**

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Professional portfolio">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Software Architect | Distributed Systems | .NET | Cloud | DDD | Governance as Code**

I'm a software architect with 20+ years of experience building, modernizing, and evolving enterprise systems.

I work where **business constraints, architecture, and implementation meet**. My role is to turn quality attributes, operational constraints, and product needs into technical decisions that teams can build, run, observe, and evolve.

I prefer architecture that stays close to engineering: **decisions should show up in code, contracts, guardrails, and automation**, so their assumptions can be tested instead of living only in diagrams or documents.

**[Professional portfolio](https://rodri-oliveira-dev.github.io/)** · [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev) · [DEV.to](https://dev.to/rodri-oliveira-dev) · [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Selected impact

Some results from enterprise systems I worked on include **30% lower response time** in a critical .NET/HANA flow, **40% lower average incident detection and response time**, and new integrations completed in **about one third of the previous time** after API and boundary redesign.

These quantitative outcomes come from projects delivered in **2020–2021**. **[See the context and engineering decisions in my portfolio →](https://rodri-oliveira-dev.github.io/en/#practice)**

---

## Architecture in practice

My open-source work shows how I approach engineering in practice. Each project captures a problem, the constraints around it, and a decision that can be inspected in code, infrastructure, or automation.

| Project | Problem, decision, and evidence |
| --- | --- |
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | A distributed-systems reference covering DDD, bounded contexts, Kafka, Outbox/Inbox, idempotency, sagas, OpenTelemetry, ADRs, and runbooks. Failure modes and trade-offs are part of the design rather than afterthoughts. |
| **[dotnet-observability-lab](https://github.com/rodri-oliveira-dev/dotnet-observability-lab)** | A runnable .NET 10, Aspire, and OpenTelemetry lab for reliable asynchronous processing, Outbox/Inbox, at-least-once delivery, and idempotency. ADRs and LikeC4 form a versioned architecture that is validated in CI and published as interactive documentation. |
| **[ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)** | Treats webhook delivery as a reliability problem, with at-least-once delivery, leases, bounded concurrency, deterministic retries, HMAC-SHA256, observability, and destination policies modeled as explicit responsibilities. |
| **[Terraform GCP .NET Blueprint](https://github.com/rodri-oliveira-dev/terraform-gcp-dotnet-blueprint)** | A reproducible baseline for .NET workloads on Google Cloud using Terraform, Cloud Run, Jobs, Pub/Sub, DLQ, Redis, Secret Manager, VPC, IAM, Workload Identity Federation, CI, and observability. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | Brings ADRs into the engineering workflow through deterministic validation and indexing across the CLI, containers, and GitHub Action, plus AI-assisted drafting while keeping review and architectural acceptance with people. |
| **[DotNetRepoInspector](https://github.com/rodri-oliveira-dev/DotNetRepoInspector)** | Uses evaluated MSBuild metadata as the source of truth for inventory and governance, exposing the same deterministic contract through the CLI/.NET Tool, GitHub Action, and a local read-only MCP server. |
| **[.NET Library Template](https://github.com/rodri-oliveira-dev/dotnet-library-template)** | Packages recurring build, testing, security, packaging, and release practices into a reusable golden path, including package validation, NuGet Audit, CodeQL, OIDC-based Trusted Publishing, and software supply-chain controls. |
| **[ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)** | Moves complexity feedback closer to development with Roslyn analyzers for algorithmic, cyclomatic, cognitive, and structural complexity, using conservative behavior when an inference cannot be made safely. |

[Explore all repositories →](https://github.com/rodri-oliveira-dev?tab=repositories)

---

## Governance as code

Sustainable architecture also means turning recurring engineering rules into feedback and automation instead of relying only on documentation and process.

The **[.github](https://github.com/rodri-oliveira-dev/.github)** repository is the shared governance and automation layer for the projects I maintain. It centralizes contribution and security standards, cross-repository maintenance, .NET project inventory, reusable secret scanning, and a versioned agent-governance registry with upstream skill synchronization and PR-controlled distribution.

The automation follows **least privilege, PR-based writes, safe defaults, and repository-level ownership**. Changes that write to repositories go through review; read-only workflows do not receive mutation permissions.

The principle is straightforward: **when a rule can provide useful feedback automatically, I would rather encode the guardrail than add another manual gate**.

---

## Open-source maintenance

I also maintain projects with an established history, user base, and public contracts.

**[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** — I am the current maintainer of the fluent mapping library for Dapper, originally created by **Henk Mollema**. I am leading its revival and modernization while preserving compatibility with the existing ecosystem and evolving the runtime, tooling, CI/CD, quality, security, and distribution strategy.

That work comes with a different constraint: **move the project forward without breaking the contract built over the years with people who already depend on it**.

---

## Open-source contributions

Contributing to codebases I do not control exercises a different part of engineering: understanding existing decisions, respecting project conventions and contracts, discussing trade-offs, and making changes that fit the surrounding ecosystem.

**Selected contributions to third-party projects**, linking to proposed and merged work.

<!-- EXTERNAL_CONTRIBUTIONS:START -->

| External project | Contributions and reference PRs |
| --- | --- |
| **[Ocelot](https://github.com/ThreeMammals/Ocelot)** | [PR #2420 · merged](https://github.com/ThreeMammals/Ocelot/pull/2420): Mapped downstream timeouts to **504 Gateway Timeout**, aligned with RFC 9110.<br><br>[PR #2421 · open](https://github.com/ThreeMammals/Ocelot/pull/2421): Proposed regression coverage for `multipart/form-data` rerouting while preserving the body, boundary, and file metadata. |
| **[CrispyWaffle](https://github.com/guibranco/CrispyWaffle)** | [PR #980 · open](https://github.com/guibranco/CrispyWaffle/pull/980): Proposed YAML serialization using YamlDotNet, integrated with the existing abstractions, tests, and documentation. |
| **[Architecture Decision Record](https://github.com/architecture-decision-record/architecture-decision-record)** | [PR #115 · open](https://github.com/architecture-decision-record/architecture-decision-record/pull/115): Proposed a complete Brazilian Portuguese localization while preserving structure and references across equivalent content. |
| **[LikeC4](https://github.com/likec4/likec4)** | [PR #3179 · merged](https://github.com/likec4/likec4/pull/3179): Introduced the pt-BR README, documentation i18n support, and tutorial.<br><br>[PR #3236 · merged](https://github.com/likec4/likec4/pull/3236): Localized Guides and the DSL fundamentals.<br><br>[PR #3262 · merged](https://github.com/likec4/likec4/pull/3262): Localized the DSL Views documentation while preserving syntax, examples, and architecture terminology. |

*PR status verified on 2026-09-23. This selection is not a lifetime contributions total; open PRs are not counted as merged.*

<!-- EXTERNAL_CONTRIBUTIONS:END -->

**[Track contributions and work in progress →](https://github.com/users/rodri-oliveira-dev/projects/1/views/1)**  
I use this GitHub Project to track open-source issues, contributions, and initiatives I am working on, evaluating, or have worked on previously.

---

## How I think about architecture

A few principles guide my work:

- **Start with the problem, not the pattern.**
- **Treat constraints as part of the design.**
- **Make decisions and trade-offs explicit.**
- **Design for failure and operation from the start.**
- **Prefer guardrails over bureaucracy.**
- **Keep architecture close enough to the code to validate decisions.**
- **Automate standards when the automation creates useful feedback for teams.**

These principles also shape my [professional portfolio](https://rodri-oliveira-dev.github.io/), where I go deeper into software architecture, distributed systems, cloud, DDD, and engineering practice.

---

## Technical content

I write about software architecture, Domain-Driven Design, distributed systems, backend engineering, software quality, cloud, engineering governance, and technical decision-making.

- **[DEV.to](https://dev.to/rodri-oliveira-dev)** — articles on software architecture, Domain-Driven Design, distributed systems, backend engineering, software quality, and the trade-offs behind technical decisions;
- **[NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)** — published .NET libraries, tools, and templates;
- **[Portfolio](https://rodri-oliveira-dev.github.io/)** — a broader view of my professional work;
- **[LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)** — career history and professional presence.

---

## GitHub Activity

<p align="left">
  <img
    src="https://github-stats-extended.vercel.app/api?username=rodri-oliveira-dev&show_icons=true&theme=transparent&locale=en&show=prs_merged,prs_reviewed&hide_border=true&hide_title=true"
    alt="Rodrigo de Oliveira's GitHub statistics"
  />
</p>
