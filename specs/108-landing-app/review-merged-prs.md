# Revisión de los PR fusionados antes de continuar

Revisión actualizada: 2026-10-20. Última base revisada: `c2bda9644c50b1f0b2e00b96d30cf6f30a5494f2` (#355). El primer bloque documenta la revisión inicial hasta #349; la ampliación e integración de #351–#355 figura al final.
Alcance: código, especificaciones y compatibilidad con la landing. Esta revisión no certifica el despliegue de esas capacidades ni reproduce sus mediciones comerciales.

| PR | Cambio contrastado | Consecuencia para esta entrega |
| --- | --- | --- |
| [341](https://github.com/RafaLopezCode/Axignal/pull/341) | Historial del dominio en Wayback; una falta de captura reciente sigue siendo desconocida. | Se conserva la observación de actividad y su incertidumbre. No se confunde la edad del dominio con la de la empresa. |
| [342](https://github.com/RafaLopezCode/Axignal/pull/342) | Pasos propios de cada hallazgo y traducción de muestras. | La extracción de fuentes conserva las nuevas acciones y la investigación del hallazgo. |
| [343](https://github.com/RafaLopezCode/Axignal/pull/343) | Contexto de AXENT por hallazgo, familia u organización. | Se conserva completo; el enlace al Observatorio abre la implementación actual. |
| [344](https://github.com/RafaLopezCode/Axignal/pull/344) | Guía de conexión MCP, cartera y preguntas para el agente. | La demo muestra una guía; la landing no autoriza conexiones ni promete acceso a datos privados. |
| [345](https://github.com/RafaLopezCode/Axignal/pull/345) | Identidad en directorios, contexto y nombres cortos. | Los indicios siguen siendo potenciales; un directorio no se presenta como identidad admitida. |
| [346](https://github.com/RafaLopezCode/Axignal/pull/346) | Ingresos reportados por terceros, con exclusiones conservadoras. | No se convierten en cuentas oficiales ni se inventan ejemplos económicos nuevos. |
| [347](https://github.com/RafaLopezCode/Axignal/pull/347) | Investigación web de preguntas, autorizada por organización. | Se mantiene excluida de la demo ilustrativa; las páginas no se convierten en hallazgos. |
| [348](https://github.com/RafaLopezCode/Axignal/pull/348) | Grado HTTP de Mozilla Observatory, condicionado al instrumento y sin grado ante fallos. | Se conserva como observación de representación, sin convertirlo en nota universal ni prueba de penetración. |
| [349](https://github.com/RafaLopezCode/Axignal/pull/349) | Canvas de familias con al menos dos hallazgos conocidos y trazabilidad. | La demo mantiene Visibilidad y omite canvas vacíos; no se añaden datos ficticios para rellenarlos. |

Ninguno modifica el MASTER ni `commercial-prices.ts`. El pricing de referencia sigue siendo 9,95 EUR/mes + 4,95 EUR por organización adicional; asesoría humana separada: 295 EUR/mes. Se mantiene el acceso por invitación y sin pago durante Design Partner.

## Incidencias preexistentes reproducidas en #347

1. **P2 — La cuota por tenant no se reserva de forma atómica.** En [WebResearchRunner.ask, líneas 241–265](https://github.com/RafaLopezCode/Axignal/blob/29de7a9ff323f8082c21de29dbbb97e64b0ba990/tools/runtime/web_research.py#L241), se consulta la cuota, se busca y después se incrementa en otra transacción. Dos peticiones que parten de nueve pasan ambas: el contador acaba en once, con dos respuestas DONE. Recomendación: reservar la plaza mediante actualización condicional atómica antes de investigar; probar concurrencia y política de devolución ante fallos.
2. **P2 — Quince segundos es un control entre lecturas, no un plazo máximo de la lectura.** [Línea 269](https://github.com/RafaLopezCode/Axignal/blob/29de7a9ff323f8082c21de29dbbb97e64b0ba990/tools/runtime/web_research.py#L269) comprueba el tiempo antes de `_check`, sin propagar el tiempo restante al lector. Una lectura bloqueante simulada de veinte segundos termina con DONE. Recomendación: propagar un deadline al buscador y al lector gobernado y comprobar cancelación/timeout, incluido robots.txt.

La reproducción utiliza el método `ask` extraído por AST del commit revisado, SQLite temporal y dependencias falsas sincronizadas; no hace peticiones de red, no usa claves y no altera producción. [Resultado reducido](evidence/merged-pr-review-probe.json).

Son incidencias del backend ya fusionado, fuera de los cambios de esta PR. No bloquean la landing aislada de solo lectura, que no llama a `/research`. Permanecen abiertas: esta entrega no afirma haberlas corregido ni haber verificado esos límites en producción.

## Integración

Se ha actualizado únicamente `codex/landing-app-conversion-20261019` mediante rebase. No se ha modificado main ni desplegado. Se conservaron todos los cambios de AXENT/MCP y las nuevas fuentes; la única extracción compartida de la landing sigue siendo la presentación de fuentes y dos funciones puras. La especificación nueva se mueve a 107 para respetar los identificadores 102–106 recién incorporados.

## Subsequent integration · #351–#355

Reviewed the changes and governing specification for the five later merges, then merged main into the isolated branch at `1470a2c81016f51cdd0a7c8fe680e068ed2a16ae`. Latest reviewed main: `c2bda9644c50b1f0b2e00b96d30cf6f30a5494f2`. The earlier #349 base remains a frozen visual comparison, not the final integration base. Main and production were not changed by this task.

| PR | Inspected behavior | Compatibility |
| --- | --- | --- |
| #351 | Reported market entries, specification 107 | Preserves reported claims and sources. Own landing spec moved to 108. Future-tense P2 below stays outside the synthetic demo. |
| #352 | Demand and economics family panels | Current subscriber demo retained. Corrected a UTC-vs-local-date test fixture around midnight; assertions and gates retained. |
| #353 | Relationships family graph panel | Existing graph and evidence boundaries retained; no renderer or relationship semantics invented. |
| #354 | Activity family panels | Current product panels retained. Temporal landing views still use existing synthetic projections. |
| #355 | Identity anchor refinements | Current identity presentation retained. Translation catalogs regenerated with all 46 new translations. |

MASTER, Constitution, ADRs, commercial prices and the landing projection fixture did not change across these merges. Full backend suite after integration: 2723 PASS / 7 explicit skips; final frontend: 413 PASS / zero skips.

**Inherited P2 in #351:** `Hawkers abrirá en México.` produces country `MX` although specification 107 excludes future announcements. The entry pattern accepts `abrira` without the future exclusion. [UTF-8 deterministic reproduction](evidence/performance-3/merged-pr-351-future.json). No network, provider or production mutation was used. This is not introduced by the landing and its demo does not invoke this extractor; the defect is reported rather than silently declared fixed.
