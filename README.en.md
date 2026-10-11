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
| **[POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)** | Demonstrates distributed-system decisions in a financial scenario using DDD, Kafka, Outbox/Inbox, sagas, and idempotency. Explores eventual consistency, observability, security, and failure modes through runnable examples, tests, and operational runbooks. |
| **[ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)** | Brings architectural decisions into engineering workflows with deterministic ADR creation, validation, and indexing. Integrates with the CLI, GitHub Actions, and VS Code, and offers optional AI assistance while preserving human review and approval. |
| **[Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)** | Reduces drift between code and diagrams by generating evidence-backed C4/LikeC4 documentation. Combines bounded inspection, CLI, MCP, and an optional agent with deterministic validation and explicit human approval before writing files. |
| **[Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)** | Evolves a public Dapper mapping library while preserving contract compatibility and separation between domain and persistence. Showcases versioning, testing, security, NuGet distribution, and runtime modernization without unnecessarily disrupting downstream consumers. |
| **[Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard)** | Consolidates repository CI, releases, security, and health signals in an Angular dashboard. Uses GitHub Actions collection and static snapshots, with a technology radar and explicit visibility into data coverage and limitations. |

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

The complete history of public pull requests in third-party projects is discovered and reconciled automatically, without relying on an editorial repository list.

**[Browse the complete open-source contributions catalog →](docs/open-source-contributions.en.md)**

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
