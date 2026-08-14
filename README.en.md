[Português](README.md) | **English**

# Rodrigo de Oliveira

**Software Architect | Distributed Systems | Cloud | .NET | DDD**

I'm a software architect with more than 20 years of experience building,
modernizing, and evolving enterprise systems.

I work mainly with distributed systems, backend, cloud, and integrations,
turning business needs and quality attributes into implementable technical
decisions. I aim to keep architecture close to the code, operations, and
engineering teams.

## Featured Projects

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

An educational .NET microservices architecture lab built to demonstrate
architectural concepts through executable code and documented decisions.

The project covers DDD, Clean Architecture, bounded contexts, Kafka, Outbox,
Inbox, idempotency, sagas, Keycloak-based security, observability, contracts,
automated tests, ADRs, SDD specifications, and operational runbooks.

**Main technologies and practices:**  
`.NET` · `PostgreSQL` · `Kafka` · `Docker` · `Keycloak` · `OpenTelemetry`  
`DDD` · `Outbox` · `Inbox` · `Sagas` · `ADRs` · `SDD`

---

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers/tree/main/analyzer)

A Roslyn analyzer that exposes algorithmic complexity estimates for C# code
during compilation and in IDEs, designed as an independent package boundary.

The project implements a Big-O model, intra- and interprocedural analysis,
semantic mappings for selected BCL and LINQ operations, and limited recurrence
and direct-recursion solving. It includes actionable diagnostics for patterns
such as linear lookups, materialization and ordering inside iterations,
input-dependent calls inside loops, and exponential recursive growth. The
analysis is intentionally conservative: when there is not enough evidence, it
returns `Unknown` rather than assuming an incorrect complexity.

**Main technologies and practices:**  
`.NET` · `C#` · `Roslyn Analyzers` · `Static Analysis` · `Big-O`  
`Interprocedural Analysis` · `Master Theorem` · `Akra-Bazzi`

---

### [Dapper.TypedParameters](https://github.com/rodri-oliveira-dev/Dapper.TypedParameters)

A .NET library for explicitly declaring SQL Server parameter types used by
Dapper with `Microsoft.Data.SqlClient`.

The project provides control over metadata such as SQL type, size, precision,
scale, and parameter direction when the expected schema is known, reducing
reliance on provider type inference. It supports strings, numeric, binary, and
temporal types, output parameters, and Table-Valued Parameters (TVPs).

The package is distributed on NuGet as `TypedParameters.Dapper.SqlServer`,
supporting .NET 8 and .NET 10, with real SQL Server integration tests, API
compatibility validation, SourceLink, and Trusted Publishing through GitHub
Actions.

**Main technologies and practices:**  
`.NET 8` · `.NET 10` · `Dapper` · `Microsoft.Data.SqlClient` · `SQL Server`  
`NuGet` · `Testcontainers` · `SourceLink` · `GitHub Actions`

---

### [Dapper FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

A library for fluently configuring mappings between .NET objects and database
columns used by Dapper while keeping persistence concerns outside domain
models.

The project evolves Dapper.FluentMap with support for conventions, naming
policies, immutable objects, value objects, nested objects, mapping profiles,
validation, Roslyn analyzers, and source generators.

**Main technologies and practices:**  
`.NET` · `C#` · `Dapper` · `Roslyn Analyzers` · `Source Generators`  
`Native AOT` · `NuGet` · `GitHub Actions`

---

### [CSF.Analyzers](https://github.com/rodri-oliveira-dev/CSF.Analyzers)

A set of Roslyn analyzers that turns contextual engineering policies into
automated compile-time checks.

Rules are organized into independent packages for architecture, operational
reliability, and test quality, allowing gradual adoption according to each
solution's needs.

**Main technologies and practices:**  
`.NET` · `C#` · `Roslyn` · `ASP.NET Core` · `DDD` · `NSubstitute`  
`FluentAssertions` · `GitVersion` · `GitHub Actions`

## Open Source Contributions

### [DDD Crew — Welcome to DDD](https://github.com/ddd-crew/welcome-to-ddd/pull/11)

Brazilian Portuguese documentation contribution accepted and merged into the
DDD Crew project, adding a pt-BR README and linking it from the main
documentation.

### [DDD Crew — DDD Starter Modelling Process](https://github.com/ddd-crew/ddd-starter-modelling-process/pull/75)

Maintenance contribution accepted and merged into the existing Brazilian
Portuguese documentation, synchronizing terminology and references with the
current source material.

## Content and Community

### [.NET Interview Questions — PT-BR](https://github.com/rodri-oliveira-dev/dotnet_interview_questions_pt_br)

An authorized Brazilian Portuguese translation of a collection of 50 .NET and
C# questions and answers, organized to support study, interviews, and
fundamentals review.

I also write about software architecture, distributed systems, Domain-Driven
Design, backend, cloud, and software engineering.

- [Medium — technical articles](https://medium.com/@rodrigodotnet)
- [NuGet — published .NET packages](https://www.nuget.org/profiles/rodri-oliveira-dev)
- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [Professional links](https://linktr.ee/rodri.oliveira.dev)

## GitHub Activity

<p align="left">
  <img
    src="https://github-stats-extended.vercel.app/api?username=rodri-oliveira-dev&show_icons=true&theme=transparent&locale=en&show=prs_merged,prs_reviewed&hide_border=true&hide_title=true"
    alt="Rodrigo de Oliveira's GitHub statistics"
  />
</p>

## Technical Focus

- **Architecture:** distributed systems, Domain-Driven Design, event-driven architecture, Clean Architecture, APIs, and integrations
- **Backend & .NET:** C#, ASP.NET Core, Roslyn, analyzers, source generators, and reusable libraries
- **Cloud & Platform:** GCP, AWS, Docker, Kubernetes, Terraform, and CI/CD
- **Data & Messaging:** PostgreSQL, SQL Server, Redis, BigQuery, Kafka, and Pub/Sub
- **Engineering:** observability, resilience, testing, static analysis, and architectural policy automation

## Contact

- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [Medium](https://medium.com/@rodrigodotnet)
- [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)
- [Professional links](https://linktr.ee/rodri.oliveira.dev)
