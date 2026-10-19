# Revisión de los PR fusionados antes de continuar

Fecha: 2026-10-19. Base final revisada y fijada: `637ba6542debf1b6ba610b4d85bb35410bed98ab`.
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
