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

## Architecture in practice

My open-source work shows how I approach engineering in practice. Each project captures a problem, the constraints around it, and a decision that can be inspected in code, infrastructure, or automation.

| Project | Problem, decision, and evidence |
| --- | --- |
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | A distributed-systems reference covering DDD, bounded contexts, Kafka, Outbox/Inbox, idempotency, sagas, OpenTelemetry, ADRs, and runbooks. Failure modes and trade-offs are part of the design rather than afterthoughts. |
| **[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** | Fluent mapping library for Dapper that I currently maintain. The work combines compatibility preservation with modernization of runtime, tooling, CI/CD, quality, security, and distribution, treating public-contract evolution as an explicit architectural constraint. |
| **[Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)** | Treats drift between code and diagrams as an evidence-and-review problem: turns verifiable evidence from .NET repositories into reviewable C4/LikeC4 documentation, with C1/C2, selective C3, a CLI, and a [local stdio MCP server](https://github.com/rodri-oliveira-dev/Repo2C4/blob/main/docs/mcp.md). Its current evolution adds a Microsoft Agent Framework-based Agent to orchestrate evidence-first analysis, validation, and bounded correction while keeping human approval before any write. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | Brings ADRs into the engineering workflow through deterministic validation and indexing across the CLI, containers, and GitHub Action, plus AI-assisted drafting while keeping review and architectural acceptance with people. |
| **[DotNetRepoInspector](https://github.com/rodri-oliveira-dev/DotNetRepoInspector)** | Uses evaluated MSBuild metadata as the source of truth for inventory and governance, exposing the same deterministic contract through the CLI/.NET Tool, GitHub Action, and a local read-only MCP server. It is evolving to discover external integrations — HTTP, multi-cloud messaging, databases, caches, and storage — as structured facts reusable by other tools. |
| **[Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard)** | An observability layer for the repository portfolio: consolidates CI, delivery, releases, activity, security, package, and health signals into a static snapshot collected by GitHub Actions and published as an Angular SPA on GitHub Pages, with explicit coverage and confidence for partial data. |
| **[.NET Library Template](https://github.com/rodri-oliveira-dev/dotnet-library-template)** | Packages recurring build, testing, security, packaging, and release practices into a reusable golden path, including package validation, NuGet Audit, CodeQL, OIDC-based Trusted Publishing, and software supply-chain controls. |
| **[ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)** | Moves complexity feedback closer to development with Roslyn analyzers for algorithmic, cyclomatic, cognitive, and structural complexity, using conservative behavior when an inference cannot be made safely. |

**DotNetRepoInspector identifies technical facts in a repository; Repo2C4 uses verifiable evidence to interpret those facts architecturally and produce reviewable C4 documentation.**

[Explore all repositories →](https://github.com/rodri-oliveira-dev?tab=repositories)

---

## Governance as code

Sustainable architecture also means turning recurring engineering rules into feedback and automation instead of relying only on documentation and process.

The **[.github](https://github.com/rodri-oliveira-dev/.github)** repository is the shared governance and automation layer for the projects I maintain. It centralizes contribution and security standards, cross-repository maintenance, .NET project inventory, reusable secret scanning, and a versioned agent-governance registry with upstream skill synchronization and PR-controlled distribution.

The automation follows **least privilege, PR-based writes, safe defaults, and repository-level ownership**. Changes that write to repositories go through review; read-only workflows do not receive mutation permissions.

The principle is straightforward: **when a rule can provide useful feedback automatically, I would rather encode the guardrail than add another manual gate**.

---

## Open-source contributions

Contributing to codebases I do not control exercises a different part of engineering: understanding existing decisions, respecting project conventions and contracts, discussing trade-offs, and making changes that fit the surrounding ecosystem.

**Selected contributions to third-party projects**, linking to proposed and merged work.

<!-- EXTERNAL_CONTRIBUTIONS:START -->

**Public PRs authored by me in the 6 selected external projects:** 19 total, 14 merged, 5 open and 0 closed without merge. **Projects with merged PRs:** 4.

| External project | Contributions and reference PRs |
| --- | --- |
| **[Ocelot](https://github.com/ThreeMammals/Ocelot)** | [PR #2420 · merged](https://github.com/ThreeMammals/Ocelot/pull/2420): Mapped downstream timeouts to **504 Gateway Timeout**, aligned with RFC 9110.<br><br>[PR #2421 · open](https://github.com/ThreeMammals/Ocelot/pull/2421): Added regression coverage for `multipart/form-data` rerouting while preserving the body, boundary, and file metadata. |
| **[OpenCNPJ](https://github.com/Hitmasu/OpenCNPJ)** | [PR #75 · merged](https://github.com/Hitmasu/OpenCNPJ/pull/75): Hardened external downloads with size and time limits, safe partial files, and preservation of the last valid artifact.<br><br>[PR #76 · merged](https://github.com/Hitmasu/OpenCNPJ/pull/76): Exposed legal-nature codes additively through the API and BigQuery projection while preserving compatibility.<br><br>[PR #77 · merged](https://github.com/Hitmasu/OpenCNPJ/pull/77): Implemented safe interrupted-download resume using Range, ETag/Last-Modified, and If-Range.<br><br>[PR #78 · merged](https://github.com/Hitmasu/OpenCNPJ/pull/78): Exposed the Receita dataset update timestamp by reusing existing metadata without inflating data shards. |
| **[LikeC4](https://github.com/likec4/likec4)** | [PR #3179 · merged](https://github.com/likec4/likec4/pull/3179): Introduced the pt-BR README, documentation i18n support, and tutorial.<br><br>[PR #3236 · merged](https://github.com/likec4/likec4/pull/3236): Localized Guides and the DSL fundamentals.<br><br>[PR #3262 · merged](https://github.com/likec4/likec4/pull/3262): Localized the DSL Views documentation while preserving syntax, examples, and architecture terminology.<br><br>[PR #3276 · merged](https://github.com/likec4/likec4/pull/3276): Continued the pt-BR localization across DSL Styling and configuration.<br><br>[PR #3277 · merged](https://github.com/likec4/likec4/pull/3277): Continued the pt-BR localization across Deployment and model extension. |
| **[Bounded Context Canvas](https://github.com/ddd-crew/bounded-context-canvas)** | [PR #59 · merged](https://github.com/ddd-crew/bounded-context-canvas/pull/59): Added the complete Brazilian Portuguese v5 documentation while preserving the existing visual and editable resources. |
| **[CrispyWaffle](https://github.com/guibranco/CrispyWaffle)** | [PR #980 · open](https://github.com/guibranco/CrispyWaffle/pull/980): Proposed YAML serialization using YamlDotNet, integrated with the existing abstractions, tests, and documentation.<br><br>[PR #981 · open](https://github.com/guibranco/CrispyWaffle/pull/981): Proposed TOML serialization with Tomlyn while reusing the shared abstraction for text formats. |
| **[Architecture Decision Record](https://github.com/architecture-decision-record/architecture-decision-record)** | [PR #115 · open](https://github.com/architecture-decision-record/architecture-decision-record/pull/115): Proposed a complete Brazilian Portuguese localization while preserving structure and references across equivalent content. |

*Project selection and descriptions are editorial. Figures include all public PRs I authored in these projects, including those not highlighted in the table. Dashboard updated: 2026-10-09.*

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
