# AXIGNAL: roadmap hacia la mejor herramienta global, con excelencia en todas sus familias

- **Estado:** objetivo de ejecución preparado por el CTO. No es canónico y está subordinado a la jerarquía `MASTER → Constitución → ADRs → specs → planes`. No reinterpreta el MASTER; si algo de aquí entra en conflicto con él, gana el MASTER.
- **Fecha:** 2026-10-13.
- **Autoridad:** MASTER §10, §11, §17–§21, §30–§31, §43, §45, §50–§51, §53, §54. ADR-0014/0015 (instrumentos de medición), ADR-0086/0095 (MCP del suscriptor).
- **Revisión:** cada fase termina con la pasada E2E multi-país (§2) y este documento se actualiza con el resultado.

---

## 0. Qué significa "la mejor herramienta global"

Una empresa de cualquier país, en cualquier idioma, recibe en cada una de las diez familias una lectura:

1. **Global por construcción.** Las fuentes globales van primero, después las regionales (UE) y después los paquetes por país. Nunca "España más extras".
2. **Con estado epistémico.** Cada lectura se marca como OBSERVED, DECLARED, POTENTIAL o UNKNOWN, con fuente, fecha, instrumento y limitación. UNKNOWN nunca se convierte en FALSE.
3. **Ordenada en el tiempo** (§20). Dice qué apareció, qué desapareció y cómo se movió, con fecha. Distingue evolución de regresión solo donde la dirección tiene sentido.
4. **Cruzada** (§18). Los INXIGHT son deterministas y trazables a sus hallazgos.
5. **Más barata de interpretar con AXIGNAL que sin él.** El agente del suscriptor, vía MCP, escribe un informe de valor y de evolución con menos coste y más rigor que investigando por su cuenta (§30.2, §44–§45).
6. **Que supera las pruebas existenciales** (§43): Wrapper, No-Model, 200-Subscription, Poisoning y Facebook.

La historia acumulada es el activo que un agente no puede reconstruir por sí solo (§43.4 y §43.5), así que cada familia emite métricas comparables en el tiempo desde el primer día.

---

## 1. Punto de partida (2026-10-13)

### 1.1 Pasada E2E en producción (10 empresas, 6 países: ES, DE, FR, UK, US, NO)

| Familia | Empresas con hallazgos | Diagnóstico |
|---|---|---|
| Presencia | 8/10 | Fuerte: auditoría web, GEO, CrUX, idiomas |
| Reputación | 0/10 | Solo 46 feeds de prensa; sin valoraciones ni notoriedad |
| Valor | 5/10 | Actividad sin establecer en 3/10; sin catálogo ni credenciales |
| Mercados | 5/10 | Solo sedes declaradas |
| Relaciones | 0 propias | Solo adjudicaciones públicas españolas |
| Demanda | 6/10 | Solo licitaciones (PLACSP, TED) |
| Actividad | 0/10 | Sin señales de operación |
| Economía | 1/10 | Registros oficiales con poca cobertura |
| Organización | 5/10 | Identificadores y razón social, con duplicados |
| Contexto | 4/10 | Titulares de sector; regulación 0 |

### 1.2 Entregado desde entonces

- **#229, columna temporal:** foto diaria de métricas por familia y cambios con fecha. Distingue EVOLUTION/REGRESSION de los cambios neutros.
- **#230, señales globales de la web propia:**
  - proveedores tecnológicos (OBSERVED);
  - clientes y partners mostrados, certificaciones, contratación, perfiles de opiniones y valoración propia (DECLARED);
  - deduplicación de direcciones y razones sociales.
- **#231:** esas señales entran en la línea temporal, sin falsos "nuevos" en lecturas anteriores al lector.
- **#232 / ADR-0095, MCP del suscriptor:**
  - panorama con observabilidad §21 y frontera §11;
  - cruces trazables y hallazgos con id estable;
  - historial con `since`.

### 1.3 Fallos P0 abiertos de la E2E

- **P0-1:** actividad sin establecer. Falta fallback por el NACE del registro y clasificación semántica. Hay un falso positivo "legal services".
- **P0-2:** redirección a otro dominio propio de la marca y webs que bloquean. Falta fallback a otras fuentes.
- **P0-3:** el INXIGHT de demanda usa el recuento mostrado (100) en vez del total real.
- **P0-4:** titulares de una palabra y el artefacto "cobertura desde 2008".
- **P0-5:** la ingesta de regulación corre dentro del bucle de observación y no guarda cursor de error, así que puede bloquear observaciones y reintenta en cada tick.
- **P0-6:** el vocabulario sectorial de regulación hace que la regulación salga vacía.

---

## 2. Cómo se mide: el arnés de excelencia (habilita todo lo demás)

Sin medición no hay excelencia, solo opinión. Este es el primer entregable y bloquea la declaración de cualquier fase como terminada.

- **Conjunto dorado global.** Unas 30 organizaciones en 8 países (ES, DE, FR, UK, US, NO, CA, AU), con tamaños, sectores y dificultades variados, incluidas webs que bloquean, grupos multinacionales y pymes sin registro rico. Es público, versionado y sin datos personales.
- **Métricas por familia:**
  - **cobertura:** porcentaje de organizaciones con al menos un hallazgo no UNKNOWN;
  - **observabilidad:** distribución STRONG / PARTIAL / LIMITED / UNKNOWN;
  - **precisión:** muestreo humano de hallazgos, con falsos positivos clasificados;
  - **fuentes distintas;**
  - **coste por organización** en tokens, euros y segundos.
- **Gate de regresión.** Ninguna métrica de una familia empeora más de un umbral entre versiones sin una decisión explícita.
- **Ejecución:** contenedor aislado con copia de datos (el `e2e_prod.py` actual, institucionalizado como herramienta del repo). Nunca escribe en producción.
- **Evaluación del agente (MCP):** un agente frontera escribe el informe de valor de cada organización:
  - **(a)** solo con el MCP de AXIGNAL;
  - **(b)** investigando por su cuenta.

  Se miden tokens, coste, tiempo, afirmaciones verificables, errores epistémicos y cobertura temporal. Este es el **argumento de venta** de €9,95 / €4,95.

---

## 3. Las diez familias: listón, fuentes y entregables

Para cada familia se indica la pregunta del suscriptor, el listón de excelencia, las fuentes por capas (G = global, R = regional, P = paquete país), las métricas temporales y los INXIGHT que habilita.

Solo se usan fuentes abiertas, APIs oficiales o datos con condiciones que lo permiten. Se respeta robots.txt. No hay scraping autenticado ni evasión anti-bot. Toda medición lleva instrumento y versión (ADR-0014/0015).

### 3.1 Presencia: ¿cómo se le encuentra y cómo le representan buscadores e IA?

- **Listón:**
  - cobertura de al menos el 95 %;
  - GEO medido en los idiomas de la organización y frente a sus competidores;
  - CrUX de usuarios reales;
  - auditoría de representación con causa y alcance.
- **G:**
  - web propia y auditoría;
  - CrUX;
  - GEO multi-idioma con instrumento congelado;
  - `sameAs` y perfiles enlazados.
- **Pendiente:**
  - **Representación en búsqueda** (§54.1). Solo con instrumento gobernado: consulta, geografía, idioma y superficie explícitos. Requiere ADR de instrumento y fuente autorizada; no se hace scraping de SERP.
  - **Comparación GEO con competidores:** "nombran a X e Y, no a ti", con la evolución.
- **Tiempo:** cuota GEO, LCP/INP, puntos de auditoría e idiomas (ya existen); posición relativa frente a competidores.

### 3.2 Reputación: ¿qué se dice de ella públicamente, dónde y con qué evidencia?

- **Listón:**
  - cobertura de al menos el 80 %;
  - prensa global multilingüe con fecha y medio;
  - notoriedad medible;
  - opiniones públicas de plataformas autorizadas, separando lo propio de lo independiente.
- **G:**
  - **GDELT:** eventos y menciones globales multilingües, abiertos;
  - **pageviews de Wikipedia** como notoriedad;
  - Wikidata;
  - perfiles de opiniones enlazados (ya existe) y lectura de la valoración pública solo donde la API o las condiciones lo permitan;
  - **Apple App Store** con la Search API pública, para las organizaciones con app.
- **R/P:** índice de prensa por país (existe, 46 feeds) ampliado por idioma.
- **INXIGHT:**
  - "el sector está en prensa y ella no" (existe);
  - notoriedad creciente sin presencia GEO;
  - valoración propia frente a la de plataformas independientes.
- **Tiempo:** menciones por mes, notoriedad, perfiles enlazados, valoración propia (existe).

### 3.3 Valor: ¿qué sabe hacer y qué ofrece?

- **Listón:**
  - actividad establecida en al menos el 95 %;
  - oferta concreta (productos y servicios) con cita;
  - credenciales verificables.
- **G:**
  - web propia: servicios/productos de JSON-LD y páginas de oferta;
  - certificaciones declaradas (existe);
  - **NACE/SIC del registro oficial** como fallback (P0-1);
  - clasificación semántica acotada (router cognitivo, nunca verdad);
  - Wikidata (productos e industria);
  - **patentes** de EPO OPS y USPTO PatentsView, como capacidad tecnológica observada.
- **Pendiente:**
  - verificación de certificaciones en registros de emisores abiertos (de DECLARED a OBSERVED) donde existan;
  - catálogo con evolución (productos nuevos y retirados).
- **Tiempo:** actividades, credenciales (existe), productos y patentes.

### 3.4 Mercados: ¿dónde actúa de verdad y dónde solo hay potencial?

- **Listón:**
  - mapa de mercados por evidencia en al menos el 85 % de los casos;
  - cada mercado con su base (sede, idioma, filial, contratación, venta, adjudicación);
  - observado y potencial separados.
- **G:**
  - hreflang y dominios por país;
  - países del grupo vía GLEIF (existe);
  - ubicaciones de sus ofertas de empleo;
  - `areaServed`, envío y precios en moneda;
  - adjudicaciones por país (§3.6).
- **INXIGHT:**
  - "opera en N países, vigila demanda en 1" (existe);
  - "contrata en un país donde no declara presencia" (expansión).
- **Tiempo:** países por base de evidencia, con aparición y retirada.

### 3.5 Relaciones: ¿con quién trabaja (clientes, partners, proveedores, competidores)?

- **Listón:**
  - relaciones propias en al menos el 80 %;
  - el tipo de cada relación con su base;
  - lo observado nunca se confunde con lo potencial (§16.5).
- **G:**
  - proveedores tecnológicos, clientes y partners mostrados (existe);
  - **GLEIF**: matrices y filiales (existe), ampliado a búsqueda de LEI por nombre;
  - **adjudicaciones públicas globales** (§3.6) para clientes públicos y socios en UTE;
  - competidores derivados de adjudicaciones y de GEO.
- **Nuevo, PATHX (§17)** (no existe): caminos explicables, por ejemplo `Organización → capacidad → sector comprador → comprador concreto`, o `matriz → filial → cliente`. Clasificados como direct, indirect, corporate, economic, potential o historical.
- **Tiempo:** proveedores, clientes y partners mostrados (existe); clientes públicos y competidores; relaciones que aparecen o se debilitan (§10).

### 3.6 Demanda: ¿dónde hay demanda plausible para lo que hace? (POTENTIAL por defecto)

- **Listón:**
  - demanda pública y privada en todos los países del conjunto dorado;
  - compradores recurrentes;
  - cadena de valor (quién compra a su sector).
- **G/R/P:**
  - **TED** (UE, existe);
  - **USAspending** y SAM.gov con clave oficial (EE. UU.);
  - **Find a Tender y Contracts Finder** (UK);
  - **CanadaBuys** (CA);
  - **AusTender** (AU);
  - PLACSP (ES, existe);
  - tablas input-output **OECD ICIO** en lugar de solo Eurostat, para la cadena de valor global.
- **Regla:** una oportunidad nunca es un cliente. Ninguna fuente nacional se trata como caso especial en la semántica del dominio.
- **Tiempo:** convocatorias abiertas y compradores recurrentes (existe); aparición de compradores nuevos.

### 3.7 Actividad: ¿qué está haciendo y qué ha cambiado?

- **Listón:**
  - al menos una señal de operación con fecha en el 85 % de los casos;
  - cambios detectados entre visitas.
- **G:**
  - ofertas de empleo de la web (existe) y de los **boards públicos de ATS** (APIs públicas de Greenhouse y Lever): número de vacantes por función y ubicación;
  - detección de cambios en la web propia (páginas, productos y noticias nuevas, por huella de contenido);
  - publicaciones propias y notas de prensa (existe);
  - cambios en registros oficiales (domicilio, administradores, cuentas depositadas);
  - eventos GDELT.
- **INXIGHT:** "contrata en X mientras su demanda observada está en Y"; "crece su plantilla pero no su presencia".
- **Tiempo:** vacantes por función, páginas nuevas y canal de selección (existe).

### 3.8 Economía: ¿qué magnitudes son observables y cuáles siguen siendo desconocidas?

- **Listón:**
  - magnitudes oficiales cuando existen (ingresos, empleados, ejercicio), con registro y fecha;
  - referencia sectorial y de país para interpretarlas;
  - UNKNOWN explícito cuando no hay datos.
- **G:**
  - GLEIF;
  - Wikidata (comunitaria y marcada así);
  - **OCDE / Banco Mundial / Eurostat** para tamaño y crecimiento del sector y del país.
- **P (registros abiertos):**
  - INSEE/RNE (FR), Brønnøysund (NO) y SEC EDGAR (US), que ya existen;
  - Companies House (UK), pendiente de la clave;
  - **CVR** (DK), **PRH/YTJ** (FI), **Bolagsverket** (SE) donde sea abierto y **ABN Lookup** (AU);
  - un paquete por país cada vez, priorizado por demanda de suscriptores.
- **INXIGHT:** "peso de los contratos públicos" (existe); comparación con la mediana del sector; crecimiento frente al sector.
- **Tiempo:** ingresos y empleados (existe), con ejercicios históricos del registro.

### 3.9 Organización: ¿quién es (identidad económica observable)?

- **Listón:**
  - identidad resuelta con identificadores verificados (LEI y registro);
  - grupo empresarial;
  - contradicciones detectadas y mostradas como CONFLICTING (§21).
- **G:** GLEIF, Wikidata, identificadores declarados en la web (existe, deduplicado en #230) y registros por país.
- **Pendiente:**
  - resolución de entidades (§50 P4) con alias, marcas y entidades jurídicas;
  - "la web y el registro discrepan" como INXIGHT.
- **Tiempo:** identificadores, estructura del grupo, cambios de razón social y domicilio.

### 3.10 Contexto: ¿qué regulación, entorno y tendencias hay que conocer para interpretarla?

- **Listón:**
  - regulación nueva y relevante para su actividad en su país en al menos el 70 % de los casos;
  - entorno macro sectorial.
- **G/R/P:**
  - EUR-Lex (UE), BOE (ES), Federal Register (US) y legislation.gov.uk (UK), que ya existen;
  - **Légifrance** (FR), **Lovdata** (NO) y el **Bundesgesetzblatt** (DE) con fuentes abiertas;
  - indicadores OCDE y Banco Mundial.
- **P0-5/P0-6:** hilo propio de ingesta con backoff, y vocabulario sectorial por actividad e idioma.
- **Tiempo:** normas nuevas y titulares de sector (existe).

---

## 4. Capacidades transversales (lo que convierte datos en el mejor producto)

| # | Capacidad | Por qué | MASTER |
|---|---|---|---|
| T1 | Arnés de excelencia y evaluación del agente | Medir antes de afirmar | §43, §50 P1 |
| T2 | Historial por eventos (estado actual más eventos con fecha), en sustitución progresiva del digest diario | "Cuándo apareció o dejó de observarse" | §20 |
| T3 | PATHX | Caminos explicables: el concepto central que falta | §17 |
| T4 | Comparativa con competidores por familia | El valor diferencial para agencias y consultoras | §22, §33 |
| T5 | Frontera de conocimiento que dirige a AXENT (prioridad por ganancia de información, reutilización, frescura y coste) | Investigar lo que más aporta, no a ciegas | §11 |
| T6 | Re-observación adaptativa (LIVE) y "Desde tu última visita" en la web | Que el suscriptor vea que su Foco está vivo | §10, §50 P10 |
| T7 | Resumen semanal de cambios por organización (email) | Retención; es el momento de valor recurrente | §10 |
| T8 | Webhooks y eventos (`RELATIONSHIP_DISCOVERED`, `INXIGHT_CREATED`…) | Integración fina sin convertirse en CRM | §38, §45 |
| T9 | Fiabilidad de ingesta: hilo, cursor y backoff por fuente; métricas de frescura por fuente en Admin | La calidad depende de fuentes vivas | §20 |
| T10 | Reutilización entre focos: lo observado de una organización abarata a otras (vecindario y sector) | Flywheel computacional | §8.3, §28 |

---

## 5. Fases, con criterios de salida

Cada fase termina con una PR desde `main` y gates verdes, el despliegue autorizado por el CTO y una pasada del arnés con la tabla actualizada en este documento.

### Fase A: fiabilidad y medición

- **Contenido:**
  - P0-1 a P0-6;
  - T1 (arnés y conjunto dorado de 30 organizaciones en 8 países);
  - T9 para regulación y prensa.
- **Salida:**
  - Valor, Organización y Contexto con cobertura de al menos el 80 % en el conjunto dorado;
  - ninguna familia sin medir;
  - informe de agente (a) frente a (b) sobre 10 organizaciones.

### Fase B: las familias en cero, globales

- **Contenido:**
  - Reputación (GDELT, notoriedad, App Store);
  - Actividad (boards ATS, cambios en la web propia, cambios en registros);
  - Mercados (hreflang, ccTLD, ubicaciones de empleo).
- **Salida:** Reputación, Actividad y Mercados con cobertura de al menos el 80 %, y precisión de al menos el 90 % en el muestreo humano.

### Fase C: demanda y relaciones globales

- **Contenido:**
  - USAspending, Find a Tender / Contracts Finder, CanadaBuys y AusTender;
  - OECD ICIO;
  - búsqueda de LEI por nombre;
  - T4 (comparativa con competidores).
- **Salida:**
  - Demanda y Relaciones con cobertura de al menos el 80 % en los 8 países;
  - comparativa con competidores en el panorama MCP y en la web.

### Fase D: la memoria que nadie puede copiar

- **Contenido:**
  - T2 (historial por eventos);
  - T3 (PATHX v1);
  - T6 ("Desde tu última visita") y T7 (resumen semanal).
- **Salida:**
  - las preguntas de §20 respondidas con fecha para cualquier organización con al menos 30 días observada;
  - PATHX explicables en el panorama.

### Fase E: economía e inteligencia profunda

- **Contenido:**
  - registros abiertos (DK, FI, SE, AU y UK con clave);
  - referencias sectoriales de OCDE y Banco Mundial;
  - patentes;
  - T5 (frontera que dirige a AXENT);
  - T8 (webhooks);
  - T10 (reutilización).
- **Salida:**
  - Economía con cobertura de al menos el 60 % (el límite real es la disponibilidad pública, y se declara);
  - todas las familias en STRONG o PARTIAL en al menos el 80 % del conjunto dorado.

**Excelencia global** se declara cuando las diez familias superan su listón en el conjunto dorado de 8 países, el agente con MCP supera al agente sin MCP en calidad a menor coste, y las pruebas §43 se pasan por escrito.

---

## 5bis. Refuerzo de SEO y GEO con fuentes gratuitas (aprobado por el CTO, 2026-10-18)

SEO y GEO son pilares que hay que reforzar mucho. Todo a coste cero, sin raspar buscadores y
con la misma ingeniería: la fuente propone o mide, AXIGNAL lee y verifica, Python decide.
Cada paso se mide sobre el panel de 20 clientes típicos de agencia antes de su PR.

| Orden | Entrega | Qué aporta | Familia |
|---|---|---|---|
| 0 | Spec 098: investigación web gobernada (DeepSeek Search) | Reseñas, reclamaciones, prensa y normativa verificadas (reputación 4/20 a 15/20) | Reputación, Contexto |
| 1 | Spec 099: texto principal y fecha (trafilatura + htmldate) | Menciones solo si están en el título o el texto principal; fecha de publicación | Reputación, Contexto |
| 2 | PageSpeed Insights API | Lighthouse: SEO, rendimiento, accesibilidad y buenas prácticas, móvil y escritorio, con su versión de instrumento | Presencia (SEO) |
| 3 | Índice de Common Crawl | Si su web está en el corpus que leen los modelos de IA, y con cuántas páginas | Presencia (GEO) |
| 4 | GDELT DOC 2.0 | Segunda fuente gratuita de noticias del motor de investigación (65 idiomas) | Reputación, Actividad |
| 5 | Wayback CDX | Historia de la web: antigüedad, versiones, rediseños | Actividad, Presencia |

Después: Mozilla Observatory y SSL Labs (confianza técnica); OpenAlex, PatentsView y SEC EDGAR
para los clientes en los que apliquen.

Descartado: Brave (de pago con tarjeta, y su índice no es Google); las API de resultados que
raspan Google; Search Console de los clientes por ahora, porque exige un flujo de alta
fricción (#308).

## 6. Dependencias de dirección (CTO/CEO)

- Desplegar 52fb35d+ y aceptar ADR-0095 (#232 ya mergeado).
- Claves oficiales gratuitas: Companies House (UK), SAM.gov (US) y EPO OPS (patentes).
- ADR de instrumento para representación en búsqueda (§54) antes de medir posiciones en buscadores.
- Monetización: datos legales y claves de Stripe en producción; buzón de Hostinger con SPF, DKIM y DMARC para el pool de marketing.

## 7. Fuera de alcance (doctrina)

- CRM, workflow, contenido patrocinado o rankings de pago.
- Edición de perfiles por la empresa.
- Ejecución de SEO/GEO o gestión de reputación.
- Un score universal.
- Scraping autenticado o evasión anti-bot.
- Tratar una oportunidad como cliente.
- Convertir una afirmación del usuario en evidencia.
- Fijar AXIGNAL a un proveedor de modelos.
