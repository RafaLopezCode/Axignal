# Verificación técnica y límites de la entrega

Modo **EXPLORE**. La nueva composición vive en `/landing-lab` y `/{locale}/landing-lab`. La homepage aceptada sigue siendo la comparación y no se sustituye. Autoridad: MASTER, Constitución, ADRs y contratos indicados en la especificación, identidad oficial y Design System. La revisión visual humana sigue pendiente.

## Comprobaciones ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `uv sync --frozen` | PASS |
| Ruff format / lint | PASS; 1.709 archivos en format |
| mypy | PASS; 599 archivos |
| pytest | 2.708 PASS, 7 SKIPPED; 405,26 s |
| Architecture Guard | PASS; sin supresiones |
| AXIGNAL governance | Los ocho checks PASS; comprobados tras adjuntar la evidencia |
| Graphify | Actualización AST, sin API ni extracción semántica de pago |
| Frontend | 378 PASS, 0 omitidas |
| Transporte HTTP admin | 28 PASS |
| TypeScript e i18n | PASS; 2.721 entradas, ninguna ausente |
| Next build y localización estática | PASS; 663 páginas generadas, incluidas las rutas aisladas |
| HTML servido | Seis idiomas, H1 único, fuentes y FAQ en HTML inicial, JSON-LD canónico, OG/Twitter, noindex y exclusión del sitemap; 22 destinos públicos responden 200 |

Los logs seleccionados y resultados reducidos están en [evidence/](evidence/). No se ha alterado un gate para obtener estos resultados.

## Siete pruebas omitidas

Son omisiones explícitas del entorno Windows o de una dependencia opcional; no fallos silenciados. El frontend tiene cero pruebas omitidas.

| Prueba | Motivo | Alcance respecto de esta entrega |
| --- | --- | --- |
| `tests/contracts/test_ao184_step_up.py::test_factor_rejects_world_readable_and_symlinks` (skip en línea 210) | Contrato de modos de archivo POSIX | La landing no modifica factores de acceso, permisos ni enlaces simbólicos. |
| `tests/integration/test_observation_materialization.py::test_production_files_root_www_data_0640` (línea 466) | Propiedad de archivos de producción POSIX | No se modifica la materialización ni el despliegue. |
| `tests/observation_runtime/test_scheduler_deployment.py::test_one_wakeup_one_entry_and_safe_no_work` (117) | Despliegue POSIX | No se ejecuta ni modifica el scheduler desde la demostración. |
| `tests/observation_runtime/test_scheduler_deployment.py::test_disabled_or_missing_config_never_invokes_docker` (130) | Despliegue POSIX | No se cambia Docker ni la activación del runtime. |
| `tests/observation_runtime/test_scheduler_deployment.py::test_overlapping_wakeups_do_not_enter_the_runtime_twice` (140) | Despliegue POSIX | No se alteran los wakeups ni su exclusión mutua. |
| `tests/observation_runtime/test_scheduler_deployment.py::test_container_failure_and_bad_configuration_are_bounded` (164) | Despliegue POSIX | No se cambian contenedores ni límites de ejecución. |
| `tests/semantic_layer/test_providers.py::test_real_sdk_question_types_accept_our_shapes` (123) | `typesafe_sdk` opcional ausente | La landing no invoca evaluadores ni proveedores de IA. |

Estas siete omisiones no dejan sin comprobar un comportamiento añadido por esta PR: es presentación pública de solo lectura con fixtures existentes. No equivalen a una certificación de producción en Linux o del SDK opcional; esos contratos conservan sus requisitos para una promoción posterior.

## Fidelidad al producto y al precio

La demostración usa `projection.ts`, `landing-observatory.ts` y `exampleInsights`, con un adaptador que conserva los extractos completos, fechas e instrumento. No añade señales, relaciones, proveedores ni admisiones. La fuente ilustrativa permanece sin enlace externo y se identifica como ficticia. Una oportunidad sigue siendo POTENTIAL; una declaración observada de cliente no verifica un contrato; UNKNOWN no se convierte en negativo. Una fecha anterior nunca toma prestado el hallazgo futuro.

El Observatorio completo de `/demo` usa su snapshot sintético actual de siete organizaciones: es un caso diferente del ejemplo temporal de la landing. El puente lo explica. Se ha probado la entrada a AXENT por familia y a la guía MCP de #344; la investigación web real de #347 permanece fuera del ejemplo. No se han creado cuentas, conectado agentes, efectuado pagos ni enviado formularios reales.

El cálculo importa `EUR_REFERENCE`, `monthlyFixedPriceMinor` y `HUMAN_ADVISORY_EUR_MONTHLY_MINOR` de `commercial-prices.ts`, gobernados por MASTER §27 y su modificación de 2026-10-16:

| Organizaciones | Referencia mensual sin impuestos |
| --- | --- |
| 1 | 9,95 EUR |
| 5 | 29,75 EUR |
| 25 | 128,75 EUR |
| 100 | 500,00 EUR |

Organización adicional: 4,95 EUR/mes. Asesoría humana separada: 295 EUR/mes. El acceso sigue siendo por invitación y sin pago durante Design Partner. No se publica una nueva moneda, oferta ni checkout.

## Motion, accesibilidad y navegación

GSAP 3.15.0, @gsap/react 2.1.2 y ScrollTrigger se cargan cuando empieza la exploración, después de las fuentes y su primer render. La comparación del DOM de scripts antes y después del gesto confirmó la carga diferida. La animación usa transform/opacity; no hace pinning, scrub, scroll-jacking ni inventa progreso.

`useGSAP`, su scope y `matchMedia.revert` retiran timelines y triggers al desmontar o cambiar la preferencia. El control de movimiento reducido se verificó con `aria-pressed=true`, `data-motion=reduced` y cero transformaciones/opacidades inline de GSAP restantes. El código respeta además `prefers-reduced-motion`; no se sustituyó la preferencia del sistema durante las pruebas. El control manual usa el estado ya existente del LocaleProvider, sin crear un sistema de preferencias.

Se comprobaron menú móvil y Escape con retorno de foco, disclosures nativos, estados con texto y símbolo, navegación hacia el producto, fuentes, selector temporal, perfiles y precio. La matriz adjunta cubre los seis idiomas y tamaños entre 320 y 1920 px. La implementación conserva una lectura esencial sin JavaScript: enlaces, contenido inicial, fuentes y FAQ nativos.

## Límites explícitos

- [Lighthouse](performance.md) es laboratorio, con advertencias de tiempo límite conservadas. El LCP móvil mantiene margen de mejora; no se declara un aprobado de Core Web Vitals de campo. No hay INP real disponible.
- El Next standalone no incluye el reverse proxy público de adquisición: `/api/acquisition/status` devuelve 404 y la medición permanece desactivada. La homepage anterior tiene además la newsletter sin backend disponible. Las rutas comerciales se pueden recorrer; no se afirma verificación de adquisición, OAuth, cobro ni primera observación de producción.
- Chrome informa un issue de la CSP existente en modo Report-Only. No se ha relajado esa política para mejorar una puntuación.
- La [revisión de #341–#349](review-merged-prs.md) registra dos incidencias preexistentes de límites en #347; esta PR no las corrige ni las ejecuta.
- Las imágenes son evidencia de revisión, no Golden Masters aceptados ni material del briefing incorporado al producto. No se ha hecho merge a main ni despliegue.

Estado: **IMPLEMENTADO + PROBADO + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING**.
