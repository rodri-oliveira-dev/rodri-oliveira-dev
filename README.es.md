[Português](README.md) | [English](README.en.md) | **Español (Latinoamérica)**

<p align="left">
  <a href="https://rodri-oliveira-dev.github.io/" aria-label="Portafolio profesional">
    <img src="assets/brand/ro-architect-mark.png" alt="RO Architect" width="64" />
  </a>
</p>

# Rodrigo de Oliveira

**Arquitecto de Software · Sistemas Distribuidos · .NET · Cloud**

*Experiencia práctica en .NET, sistemas distribuidos, plataformas en la nube, gobernanza de arquitectura y herramientas de código abierto.*

Mi trayectoria comenzó en el desarrollo de software y, a lo largo de más de 20 años, pasó por la integración y modernización de sistemas empresariales hasta llegar a la arquitectura. Actualmente trabajo en la arquitectura de soluciones para los sectores financiero y asegurador, con responsabilidad arquitectónica sobre dos equipos de ingeniería y en colaboración con responsables de producto, líderes técnicos y otros arquitectos.

He participado en la modernización de funcionalidades heredadas hacia microservicios, desde el análisis inicial hasta su puesta en producción, y contribuyo a la gobernanza mediante revisiones técnicas en el Centro de Excelencia de Arquitectura. También he ejercido el liderazgo técnico y he trabajado como Career Advisor, acompañando el desarrollo profesional de colegas, además de participar en la adopción de herramientas de IA para desarrollar nuevos sistemas.

Aquí comparto bibliotecas, herramientas y laboratorios de código abierto que desarrollo para explorar cómo las decisiones de arquitectura se reflejan en el código, las pruebas y la automatización.

<p align="center">
  <picture>
    <source
      media="(max-width: 767px)"
      srcset="assets/profile/software-architecture-in-practice.es.mobile.png"
    />
    <img
      src="assets/profile/software-architecture-in-practice.es.png"
      alt="Arquitectura de software en la práctica: negocio, equipos, organización y evolución orientan las decisiones arquitectónicas, apoyadas en código, pruebas, observabilidad y automatización. Proyectos destacados: ADR Guard, Repo2C4, Complexity Analyzers, Dapper.FluentMap y POC Arquitectura."
      width="100%"
    />
  </picture>
</p>

**Enlaces profesionales**

- [Portafolio profesional](https://rodri-oliveira-dev.github.io/)
- [Currículum](https://rodri-oliveira-dev.github.io/es/curriculo/)
- [Servicios de consultoría](https://rodri-oliveira-dev.github.io/es/servicios/)
- [LinkedIn](https://www.linkedin.com/in/rodri-oliveira-dev)
- [Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)
- [NuGet](https://www.nuget.org/profiles/rodri-oliveira-dev)

---

## Proyectos destacados

Herramientas, bibliotecas y laboratorios que conectan las decisiones de arquitectura con la implementación y la operación.

### [ADR Guard](https://github.com/rodri-oliveira-dev/adr-guard)

*Herramienta de gobernanza de arquitectura*

Ayuda a los equipos a mantener registros de decisiones arquitectónicas (ADR) consistentes y rastreables. Su CLI en .NET permite crear, validar e indexar estos registros. Los análisis opcionales de impacto y desviaciones arquitectónicas se basan en evidencia verificable, sin reemplazar el criterio profesional. Un [servidor MCP independiente y de solo lectura](https://github.com/rodri-oliveira-dev/adr-guard/blob/main/docs/mcp.md) ofrece herramientas a agentes compatibles, mientras que las [Agent Skills](https://github.com/rodri-oliveira-dev/adr-guard/blob/main/docs/skills/README.md) orientan su uso sin delegar decisiones arquitectónicas. El [estudio de caso](https://rodri-oliveira-dev.github.io/es/case-studies/adr-guard/) explica las decisiones tomadas y sus implicaciones.

### [Dapper.FluentMap](https://github.com/rodri-oliveira-dev/Dapper-FluentMap)

*Biblioteca .NET*

Resuelve el mapeo entre objetos .NET y columnas de bases de datos cuando las convenciones de Dapper no son suficientes, sin agregar atributos a los modelos. Su evolución busca combinar una API fluida y extensible con la compatibilidad de las aplicaciones existentes, preservando los contratos públicos durante una modernización gradual. El [estudio de caso](https://rodri-oliveira-dev.github.io/es/case-studies/dapper-fluentmap/) analiza los límites de esta abstracción.

### [Repo2C4](https://github.com/rodri-oliveira-dev/Repo2C4)

*Herramienta de documentación de arquitectura*

Reduce el riesgo de que el código y los diagramas pierdan consistencia al convertir evidencia verificable de repositorios .NET en documentación C4/LikeC4 que se puede revisar. El proceso distingue las observaciones de las hipótesis y requiere aplicar los cambios de forma explícita. Combina análisis estático, generación determinista e integración con agentes mediante MCP.

### [POC Arquitetura](https://github.com/rodri-oliveira-dev/poc-arquitetura)

*Laboratorio de sistemas distribuidos*

Permite explorar decisiones sobre consistencia eventual, manejo de fallas y trazabilidad mediante escenarios reproducibles con servicios distribuidos en .NET. Reúne DDD, integración asíncrona con Kafka y el patrón Outbox, pruebas y guías operativas (runbooks). Las propuestas que todavía no cuentan con evidencia en el código se identifican como pendientes.

### [ReliableWebhooks](https://github.com/rodri-oliveira-dev/ReliableWebhooks)

*Biblioteca .NET para integraciones*

Aborda las fallas, la concurrencia y las entregas duplicadas de webhooks salientes. Los identificadores estables permiten agregar eventos a la cola de forma idempotente. La asignación temporal del trabajo (leases) y los reintentos respaldan una entrega de al menos una vez (at-least-once), siempre que la aplicación proporcione almacenamiento duradero y que el sistema receptor tolere duplicados. El [estudio de caso](https://rodri-oliveira-dev.github.io/es/case-studies/reliable-webhooks/) examina estas garantías y sus límites.

### [ComplexityAnalysis.Analyzers](https://github.com/rodri-oliveira-dev/complexity-analyzers)

*Herramienta de análisis estático*

Identifica patrones de alto costo computacional y posibles regresiones de complejidad antes de ejecutar el código. El analizador basado en Roslyn estima la complejidad Big-O cuando hay suficiente evidencia, aplica métricas configurables durante la compilación y en el IDE, y devuelve un resultado indeterminado cuando el código no permite una conclusión fundamentada.

Otros proyectos incluyen [Repo Control Center](https://github.com/rodri-oliveira-dev/repo-status-dashboard), un panel para consultar la integración continua (CI), las versiones publicadas, la seguridad y el estado general de los repositorios. También puedes explorar la [lista completa de repositorios](https://github.com/rodri-oliveira-dev?tab=repositories).

---

## Contribuciones de código abierto

Estas son algunas de mis contribuciones incorporadas en proyectos de terceros, centradas en correcciones, mantenimiento y seguridad:

- **Ocelot — [PR #2420](https://github.com/ThreeMammals/Ocelot/pull/2420):** corrigió el mapeo de los tiempos de espera del servicio de destino a HTTP 504, conforme a la RFC 9110, sin alterar la cancelación del cliente ni el comportamiento de QoS. Incluyó pruebas unitarias y de aceptación.
- **MySqlConnector — [PR #1675](https://github.com/mysql-net/MySqlConnector/pull/1675):** eliminó la detección obsoleta de Azure MySQL Single Server, conservó la compatibilidad con AWS RDS Proxy y simplificó la lógica de conexión.
- **OpenCNPJ — [PR #75](https://github.com/Hitmasu/OpenCNPJ/pull/75):** centralizó las descargas externas e incorporó tiempos de espera, límites de tamaño, archivos temporales y limpieza ante errores, con pruebas y validación en CI.

El [catálogo completo de contribuciones de código abierto](docs/open-source-contributions.es.md) reúne los demás pull requests y actualiza automáticamente sus estados.

## Gobernanza como código

En el repositorio **[.github](https://github.com/rodri-oliveira-dev/.github)** reúno políticas y automatizaciones reutilizables: estándares de contribución y seguridad, inventario de proyectos .NET, detección de secretos y distribución controlada de skills para agentes. Los cambios se revisan mediante pull requests y cada repositorio conserva la autonomía para adoptar sus propias reglas.

## Mi visión de la arquitectura

Mi manera de entender la arquitectura se formó a lo largo de más de dos décadas trabajando en desarrollo de software. Esa experiencia me enseñó que no basta con que una solución sea técnicamente correcta. También debe tener sentido para el negocio, adaptarse a la forma de trabajar de la organización y servir a quienes van a construirla y mantenerla.

No creo en una arquitectura que se define de manera aislada y luego se impone a los equipos. Prefiero comprender primero el contexto de la empresa, la experiencia de los equipos, las limitaciones que enfrentan y los objetivos que buscan alcanzar. A partir de ahí, busco construir las decisiones en conjunto, atendiendo las necesidades actuales sin perder de vista la evolución futura.

Para mí, ser arquitecto no consiste solo en diseñar soluciones. También implica ayudar a los equipos a tomar buenas decisiones técnicas, compartir conocimiento y facilitar que los sistemas evolucionen de manera sostenible.

## Publicaciones y contenido técnico

Escribo sobre arquitectura de software, DDD y desarrollo .NET, a partir de decisiones y problemas que surgen en la práctica.

- **[Café com código](https://www.linkedin.com/newsletters/caf%C3%A9-com-c%C3%B3digo-6880618748047314945)** — boletín sobre arquitectura e ingeniería de software.
