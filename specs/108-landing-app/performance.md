# Lighthouse: resultados reales de laboratorio

## Entrega optimizada · 20 de octubre de 2026

Código `4b2a7fbc7937d01f81efa8820315b6755ab9f8dc`, integrado con main hasta #355 (`c2bda9644c50b1f0b2e00b96d30cf6f30a5494f2`). Tres ejecuciones móviles consecutivas y una de escritorio, seriales, navegador frío, build de producción Node 22.23.3, Lighthouse 13.5.0. Misma configuración predeterminada de Lighthouse, sin bloquear solicitudes ni cambiar throttling. [Configuración completa y selección](evidence/performance-3/metrics.json).

| Ejecución | Rendimiento | Accesibilidad | LCP | CLS | TBT | Informe |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| final-mobile-1 | 96 | 100 | 2.65 s | 0.00000 | 45.0 ms | [HTML](evidence/performance-3/final-mobile-1.html) · [JSON](evidence/performance-3/final-mobile-1.json) |
| final-mobile-2 | 97 | 100 | 2.64 s | 0.00000 | 36.0 ms | [HTML](evidence/performance-3/final-mobile-2.html) · [JSON](evidence/performance-3/final-mobile-2.json) |
| final-mobile-3 | 92 | 100 | 3.30 s | 0.00000 | 43.0 ms | [HTML](evidence/performance-3/final-mobile-3.html) · [JSON](evidence/performance-3/final-mobile-3.json) |
| final-desktop | 100 | 100 | 0.70 s | 0.00008 | 0.0 ms | [HTML](evidence/performance-3/final-desktop.html) · [JSON](evidence/performance-3/final-desktop.json) |

Se selecciona **final-mobile-1**, la muestra con LCP mediano; se conservan sus demás métricas y las tres muestras completas. Rango móvil: 2.64–3.30 s. Las cuatro ejecuciones finales no contienen advertencias de Lighthouse. Best Practices: 96. SEO: 69 por el `noindex` deliberado del laboratorio; no se retira para inflar la nota.

El resultado mejora la revisión móvil de 79 puntos / 4,64 s, cuyos originales se conservan debajo. **No se declara perfecto**: el LCP móvil mediano sigue por encima de 2,5 s y existe variabilidad entre ejecuciones. Son datos de laboratorio, no un aprobado de Core Web Vitals de campo. **INP real: no disponible**; TBT no es su sustituto.

### Cambios de entrega comprobados

- Catálogos por idioma y selección comercial en servidor: la landing no entrega los catálogos de todos los idiomas ni el workspace del suscriptor. Las 90 vistas sintéticas precomputadas son profundamente idénticas a la proyección existente; no se inventa evidencia.
- Una sola hoja CSS para el laboratorio; la superficie existente conserva las siete fuentes CSS, byte por byte y en su orden original. Grupos de precedencia estables durante navegación Next.js.
- Cuatro fuentes cacheables, 101.112 bytes frente a 221.196: conserva ejes, alternativos y contornos. Cero diferencia de coordenadas en la [verificación de glifos](evidence/performance-3/font-outline-verification.json). No se sustituyen por fuentes aproximadas.
- SVG oficial del logo externo e idéntico; ilustración del Observador con prioridad baja; GSAP diferido y sin bloquear el CTA.
- Estado de adquisición con plazo acotado y distinción ENABLED / DISABLED / UNAVAILABLE. No se convierte un timeout en `false` ni se fabrica un backend disponible.
- Núcleo de diálogo y utilidades públicas separados mediante reexportaciones compatibles. No se cambia el producto del suscriptor.

Se descartaron pruebas de CSS/fuentes embebidas, `content-visibility` en capítulos y cambio de bundler porque no aportaban mejora o alteraban anclas. También se descartó fijar el eje de Fraunces: producía deriva en los contornos. La implementación final conserva el bundler habitual y navegación nativa.

Los JSON se mantienen exactos y los ZIP conservan los HTML/JSON originales. Las vistas HTML sólo normalizan espacios finales por higiene del repositorio. Ningún informe histórico se presenta como prueba del código actual.


## Revisión 2 · registro histórico, sustituido

Código `d236a3e3b0b7411c95dba1fe243b77e8c214cf87`. Una ejecución final por dispositivo, serial, después de las suites y Graphify. [Condiciones y datos](evidence/revision-2/metrics.json). No se equipara una sola muestra con las medianas anteriores.

| Perfil | Rendimiento | Accesibilidad | LCP | CLS | TBT | Informe |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| mobile | 79 | 100 | 4.64 s | 0.00000 | 172.5 ms | [HTML](evidence/revision-2/lighthouse-mobile.html) · [JSON](evidence/revision-2/lighthouse-mobile.json) |
| desktop | 99 | 100 | 0.91 s | 0.00002 | 3.5 ms | [HTML](evidence/revision-2/lighthouse-desktop.html) · [JSON](evidence/revision-2/lighthouse-desktop.json) |

Se conservan las advertencias originales de tiempo límite. LCP móvil pendiente de mejora; no se afirma superar Core Web Vitals de campo. No hay INP real. El primer diagnóstico móvil coincidió con el final de Graphify y se conserva [por separado](evidence/revision-2/diagnostic.json).

## Primera propuesta · registro histórico

Código final: `77f8f04e9f8f7d0cf3db3cfb659012c9d288a65f`; base revisada `637ba6542debf1b6ba610b4d85bb35410bed98ab`. Chrome headless local, Next 16.3.8 compilado con Node 22.23.3. Lighthouse 13.5.0, presets móvil/escritorio, almacenamiento frío por ejecución y parámetros completos en [metrics.json](evidence/metrics.json). Las suites de CPU y Graphify habían terminado antes de estas mediciones.

| Superficie | Perfil | Rendimiento | Accesibilidad | LCP | CLS | TBT | Informe |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Anterior | mobile | 77 | 100 | 4.89 s | 0.00019 | 177.0 ms | [HTML](evidence/lighthouse-mobile-old.html) · [JSON](evidence/lighthouse-mobile-old.json) |
| Nueva | mobile | 80 | 100 | 4.55 s | 0.00006 | 149.0 ms | [HTML](evidence/lighthouse-mobile-new.html) · [JSON](evidence/lighthouse-mobile-new.json) |
| Anterior | desktop | 99 | 100 | 1.02 s | 0.00014 | 2.5 ms | [HTML](evidence/lighthouse-desktop-old.html) · [JSON](evidence/lighthouse-desktop-old.json) |
| Nueva | desktop | 99 | 100 | 0.94 s | 0.00000 | 3.0 ms | [HTML](evidence/lighthouse-desktop-new.html) · [JSON](evidence/lighthouse-desktop-new.json) |

En móvil se ejecutaron tres muestras por versión sobre el mismo build; la tabla selecciona la muestra con LCP mediano y conserva sus demás métricas. En escritorio hay una ejecución por versión. No se elige el mejor resultado.

Anterior móvil, LCP por ejecución: [4.89 s](evidence/lighthouse-mobile-old-run1.json), [4.89 s](evidence/lighthouse-mobile-old-run2.json), [4.89 s](evidence/lighthouse-mobile-old-run3.json); mediana 4.89 s.

Nueva móvil, LCP por ejecución: [6.96 s](evidence/lighthouse-mobile-new-run1.json), [4.55 s](evidence/lighthouse-mobile-new-run2.json), [4.48 s](evidence/lighthouse-mobile-new-run3.json); mediana 4.55 s.

La tabla usa los valores numéricos del JSON antes del redondeo de la interfaz Lighthouse: por ejemplo, 3 ms de TBT pueden aparecer como 0 ms en el resumen visual.

Originales sin normalizar: [móvil anterior](evidence/lighthouse-mobile-old-original.zip), [móvil nueva](evidence/lighthouse-mobile-new-original.zip), [escritorio anterior](evidence/lighthouse-desktop-old-original.zip), [escritorio nueva](evidence/lighthouse-desktop-new-original.zip). Las vistas HTML y logs del repositorio tienen normalizado únicamente el espacio final; los JSON de medición se conservan íntegros.

**INP:** no se han obtenido datos de campo de esta ruta local. No se usa TBT como sustituto de INP.

## Interpretación y advertencias

El LCP móvil mantiene margen de mejora. Esta tabla no certifica Core Web Vitals de campo ni una mejora causal de conversión. Las repeticiones móviles muestran variabilidad: no justifican afirmar una mejora causal o un LCP de campo. El historial conserva también las revisiones intermedias.

Las ejecuciones conservan el aviso: «The page loaded too slowly to finish within the time limit. Results may be incomplete.» La advertencia se conserva en los informes originales; no se han cambiado los timeouts de Lighthouse ni bloqueado peticiones para ocultarla.

Best Practices: 92 en ambas superficies. La instalación standalone devuelve 404 en `/api/acquisition/status`, que en el entorno público resuelve el proxy de adquisición. Chrome también informa un issue sobre la CSP existente en modo Report-Only. La landing anterior presenta además la newsletter sin backend local. No se inventa un estado habilitado ni se cambia la política de seguridad para obtener una puntuación.

SEO: 69 en el laboratorio aislado y 92 en la homepage anterior. La diferencia corresponde al `noindex` deliberado: el CTO debe aprobar la nueva experiencia antes de promoverla. Las demás comprobaciones SEO de Lighthouse pasan. Los checks HTTP verifican canonical, idiomas, JSON-LD y OG/Twitter en las seis rutas. No se afirma indexación pública ni resultados en sistemas generativos.

## Correcciones comprobadas

- El motor GSAP deja de competir con la primera lectura: sólo se carga al comenzar a explorar, tras las fuentes y su primer render. No aparece en los scripts iniciales; sí después del gesto.
- Dos funciones puras y el componente de fuentes evitan importar el workspace del suscriptor en la presentación pública. El incremento medido de JavaScript inicial es aproximadamente 13 KB gzip frente a la homepage actual; véase [inventario](evidence/initial-js-final.json).
- La variante latina de Bic Notes pasa de 173.748 a 85.384 bytes. Se comprobaron métricas y contornos descompuestos idénticos para 411 caracteres retenidos; mantiene las ligaduras y la licencia original. [Proveniencia](evidence/font-optimization.json).

No se ha añadido un presupuesto universal ni se han relajado gates. Se mantiene separada la medición de laboratorio de cualquier medición real posterior a la aprobación.
