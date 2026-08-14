# Rodrigo de Oliveira

**Software Architect | Distributed Systems | Cloud | .NET | DDD**

Sou arquiteto de software com mais de 20 anos de experiência no
desenvolvimento, modernização e evolução de sistemas corporativos.

Atuo principalmente com sistemas distribuídos, backend, cloud e integrações,
transformando necessidades de negócio e atributos de qualidade em decisões
técnicas implementáveis. Procuro manter a arquitetura próxima do código,
da operação e dos times de engenharia.

## Projetos em destaque

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

Laboratório educacional de arquitetura de microserviços em .NET, criado para
demonstrar conceitos arquiteturais por meio de código executável e decisões
documentadas.

O projeto aborda DDD, Clean Architecture, contextos delimitados, Kafka,
Outbox, Inbox, idempotência, sagas, segurança com Keycloak, observabilidade,
contratos, testes automatizados, ADRs, especificações SDD e runbooks
operacionais.

**Principais tecnologias e práticas:**  
`.NET` · `PostgreSQL` · `Kafka` · `Docker` · `Keycloak` · `OpenTelemetry`  
`DDD` · `Outbox` · `Inbox` · `Sagas` · `ADRs` · `SDD`

---

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers/tree/main/analyzer)

Analyzer Roslyn para expor estimativas de complexidade algorítmica de código
C# durante a compilação e em IDEs, mantendo a análise como uma fronteira de
pacote independente.

O projeto implementa um modelo de Big-O, análise intra e interprocedural,
mapeamentos semânticos para operações selecionadas de BCL e LINQ e resolução
limitada de recorrências e recursão direta. Inclui diagnósticos acionáveis para
padrões como buscas lineares, materialização e ordenação dentro de iterações,
chamadas dependentes de entrada em loops e crescimento recursivo exponencial.
A análise adota uma abordagem conservadora: quando não há evidência suficiente,
o resultado permanece `Unknown` em vez de assumir uma complexidade incorreta.

**Principais tecnologias e práticas:**  
`.NET` · `C#` · `Roslyn Analyzers` · `Static Analysis` · `Big-O`  
`Interprocedural Analysis` · `Master Theorem` · `Akra-Bazzi`

---

### [Dapper.TypedParameters](https://github.com/rodri-oliveira-dev/Dapper.TypedParameters)

Biblioteca .NET para declarar explicitamente os tipos de parâmetros SQL Server
utilizados pelo Dapper, usando `Microsoft.Data.SqlClient`.

O projeto permite controlar metadados como tipo SQL, tamanho, precisão, escala
e direção dos parâmetros quando o schema esperado é conhecido, reduzindo a
dependência da inferência automática feita pelo provider. Inclui suporte a
strings, tipos numéricos, binários, temporais, parâmetros de saída e
Table-Valued Parameters (TVPs).

O pacote é distribuído no NuGet como `TypedParameters.Dapper.SqlServer`, com
suporte a .NET 8 e .NET 10, testes de integração reais com SQL Server,
validação de compatibilidade da API, SourceLink e publicação protegida por
Trusted Publishing via GitHub Actions.

**Principais tecnologias e práticas:**  
`.NET 8` · `.NET 10` · `Dapper` · `Microsoft.Data.SqlClient` · `SQL Server`  
`NuGet` · `Testcontainers` · `SourceLink` · `GitHub Actions`

---

### [Dapper FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

Biblioteca para configurar de maneira fluente o mapeamento entre objetos .NET
e colunas de banco de dados utilizadas pelo Dapper, mantendo preocupações de
persistência fora dos modelos de domínio.

O projeto evolui o Dapper.FluentMap com suporte a convenções, naming policies,
objetos imutáveis, value objects, objetos aninhados, perfis de mapeamento,
validação, analyzers Roslyn e source generators.

**Principais tecnologias e práticas:**  
`.NET` · `C#` · `Dapper` · `Roslyn Analyzers` · `Source Generators`  
`Native AOT` · `NuGet` · `GitHub Actions`

---

### [CSF.Analyzers](https://github.com/rodri-oliveira-dev/CSF.Analyzers)

Conjunto de analyzers Roslyn para transformar políticas contextuais de
engenharia em verificações automatizadas durante a compilação.

As regras estão organizadas em pacotes independentes para arquitetura,
confiabilidade operacional e qualidade de testes, permitindo adoção gradual
conforme as necessidades de cada solução.

**Principais tecnologias e práticas:**  
`.NET` · `C#` · `Roslyn` · `ASP.NET Core` · `DDD` · `NSubstitute`  
`FluentAssertions` · `GitVersion` · `GitHub Actions`

## Conteúdo e comunidade

### [.NET Interview Questions — PT-BR](https://github.com/rodri-oliveira-dev/dotnet_interview_questions_pt_br)

Tradução autorizada de uma coleção com 50 perguntas e respostas sobre .NET
e C#, organizada para apoiar estudos, entrevistas e revisão de fundamentos.

Também escrevo sobre arquitetura de software, sistemas distribuídos,
Domain-Driven Design, backend, cloud e engenharia de software.

- [Artigos e publicações](https://linktr.ee/rodri.oliveira.dev)
- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)

## Atividade no GitHub

<p align="left">
  <img
    src="https://github-stats-extended.vercel.app/api?username=rodri-oliveira-dev&show_icons=true&theme=transparent&locale=pt-br&show=prs_merged,prs_reviewed,reviews&hide_border=true"
    alt="Estatísticas do GitHub de Rodrigo de Oliveira"
  />
</p>

## Áreas de interesse

- Arquitetura de software e sistemas distribuídos
- Domain-Driven Design
- Arquitetura orientada a eventos
- Integrações e APIs
- Observabilidade e resiliência
- Modernização de aplicações
- Análise estática, qualidade e automação de políticas arquiteturais
- Desenvolvimento e manutenção de bibliotecas open source

## Tecnologias e práticas

`.NET` · `C#` · `GCP` · `AWS` · `Docker` · `Kubernetes` · `Terraform`  
`PostgreSQL` · `SQL Server` · `Redis` · `BigQuery` · `Kafka` · `Pub/Sub`  
`Roslyn` · `DDD` · `Event-Driven Architecture` · `Clean Architecture` · `CI/CD`

## Contato

- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [Links profissionais](https://linktr.ee/rodri.oliveira.dev)
