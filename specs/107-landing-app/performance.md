# Lighthouse: resultados reales de laboratorio

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
