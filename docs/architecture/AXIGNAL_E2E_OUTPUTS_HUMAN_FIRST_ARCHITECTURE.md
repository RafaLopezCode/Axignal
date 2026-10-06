# AXIGNAL â€” Arquitectura E2E de outputs, evidencia y comprensiÃ³n humana

**Estado:** PROPUESTA ARQUITECTÃ“NICA / PRE_IMPLEMENTATION, preparada para revisiÃ³n y posteriores slices Spec Kit. **Fecha:** 2026-10-05, Europe/Madrid. **Snapshot de cÃ³digo:** `27c4bb71f6839813d2172dbbad775ed708867454`. **Autoridad:** subordinada a MASTER, ConstituciÃ³n, ADRs aceptados y Atlas. Las responsabilidades aceptadas se conservan; las extensiones de contratos aquÃ­ propuestas no se convierten en autoridad por publicarse. **Resultado de este trabajo:** diseÃ±o, investigaciÃ³n y handoff; no implementaciÃ³n E2E ni despliegue.

El usuario ha fijado el propÃ³sito: outputs que permitan entender una OrganizaciÃ³n con lenguaje y UX Human First, fundamentados en evidencia. Para presencia escasa eligiÃ³ ambas salidas: brecha documentada con recomendaciones condicionadas y diagnÃ³stico despuÃ©s de investigar contexto. Se combinan en el mismo objeto, con distinta madurez, conservando las versiones anteriores.

**AclaraciÃ³n del usuario, 2026-10-05:** Customer Zero interno es AXIGNAL usando AXIGNAL para probar y aprovechar sus outputs, incluida la observaciÃ³n de AXIGNAL. El E2E de producciÃ³n empieza cuando un suscriptor registra 1, 2 o 100 Organizaciones para observaciÃ³n persistente. Nombre/URL son pistas de identificaciÃ³n de cada alta; el formulario interno no es la definiciÃ³n de la entrada de producciÃ³n. Cada alta crea o recupera el Foco de observaciÃ³n correspondiente â€”Xeed en los identificadores internos existentesâ€”, ligado a una OrganizaciÃ³n canÃ³nica cuando se resuelve su identidad.

**ValidaciÃ³n de la entrega, incluida la aclaraciÃ³n Customer Zero:** `uv run axignal-governance` pasÃ³ architecture, deps, docs, graphify, hygiene, no-generated-data, spec y terminology. Se verificaron 94 destinos locales, las veinte secciones consecutivas y los bloques de cÃ³digo de los tres documentos nuevos. `git diff --check` pasÃ³. El inventario conserva hashes del corpus previo a la entrega; `docs/README.md` es el Ãºnico archivo inventariado cambiado por este trabajo. No se repitiÃ³ la suite de producto para esta ediciÃ³n documental. Design mode: EXTEND arquitectÃ³nico; browser QA, Golden Master delta y human visual acceptance no se activaron porque no se cambiÃ³ una superficie visual.

Se indexaron 388 documentos Markdown de `docs/` y `specs/` para navegaciÃ³n. Indexar no equivale a leer Ã­ntegramente cada documento. La revisiÃ³n profunda se concentrÃ³ en MASTER Â§Â§1â€“2, 14â€“23, 53â€“56; HFX; las especificaciones Subscriber, DRI, Admin, V2 y V3; Atlas/continuidad/interacciÃ³n; brief generativo; ADRs y fuentes de cÃ³digo citadas. El [inventario con hashes](D:/AXIGNAL/Axignal/docs/research/e2e-outputs-2026-10-05/document-inventory.json) permite identificar el corpus; el [registro de decisiones y fuentes](D:/AXIGNAL/Axignal/docs/research/e2e-outputs-2026-10-05/DECISIONES_Y_EVIDENCIA.md) distingue evidencia, prestaciones externas y propuestas.

## 1. Objetivo: comprar comprensiÃ³n persistente

La unidad de valor es entender quÃ© puede saberse de una OrganizaciÃ³n, quÃ© ha cambiado, por quÃ© merece atenciÃ³n y quÃ© lo respalda. El usuario dirige atenciÃ³n; el sistema observa, recuerda, contrasta y explica. Â«OaaSÂ» se usa aquÃ­ en el sentido expresado por el usuario: servicio que entrega outputs Ãºtiles y evidencia. No establece otra unidad de facturaciÃ³n, una garantÃ­a de resultado comercial ni una modificaciÃ³n de los precios del MASTER. Las SeÃ±ales siguen sin ser unidades facturables.

El objetivo arquitectÃ³nico es conservar correcciÃ³n, procedencia y privacidad mientras mejora comprensiÃ³n, frescura y economÃ­a de observaciÃ³n. No existe una tecnologÃ­a que maximice todas esas dimensiones a la vez. Â«MejorÂ» debe demostrarse con la misma informaciÃ³n, los mismos lÃ­mites y tareas humanas representativas.

Un output puede tener valor sin una gran cantidad de datos: Â«No podemos describir todavÃ­a esta capacidadÂ», Â«Las fuentes discrepanÂ», Â«Tu organizaciÃ³n no apareciÃ³ en estas consultasÂ», o Â«Hay una posible conexiÃ³n y faltan estos requisitosÂ». Estos resultados no rellenan artificialmente el panorama ni convierten ausencia de conocimiento en ausencia empresarial.

## 2. Soluciones que debe entregar el sistema

| Pregunta humana | Output y valor | Evidencia/requisitos | LÃ­mite que sobrevive a la UX |
|---|---|---|---|
| Â¿QuiÃ©n es esta organizaciÃ³n? | Identidad resuelta o desambiguaciÃ³n comprensible | Identificadores, nombres, dominios y fuentes pertinentes | Marca, sede y entidad legal pueden diferir |
| Â¿QuÃ© ofrece y dÃ³nde puede actuar? | Productos/capabilities y alcance por capability | Declaraciones atribuibles, certificaciones/reach cuando existen | Sede no define mercado total; capacidad declarada no acredita capacidad operativa disponible |
| Â¿CÃ³mo la encuentran y describen? | Estado de representaciÃ³n por superficie y condiciones | Instrumento, consultas/prompts, detecciÃ³n de sujeto, muestra, raw permitido | API y UI son instrumentos distintos; representaciÃ³n no es realidad econÃ³mica |
| Â¿QuÃ© podrÃ­a mejorar? | Brecha explicada y diagnÃ³stico condicionado | Estado econÃ³mico, contexto de uso, representaciÃ³n comparable, alternativas | No atribuir automÃ¡ticamente mala comunicaciÃ³n o pÃ©rdida de ventas |
| Â¿Con quiÃ©n estÃ¡ conectada? | Relaciones observadas, hipÃ³tesis y caminos separados | Partes, direcciÃ³n, predicate, tiempo y admisiÃ³n para observadas | Similaridad/capability match no crea cliente, lead ni relaciÃ³n observada |
| Â¿DÃ³nde hay una necesidad pertinente? | Oportunidad POTENTIAL con motivos, bloqueos y preguntas | Oferta, necesidad, reach, restricciones y estado suficiente | No probabilidad de venta ni score universal |
| Â¿QuÃ© cambiÃ³? | Cambio material frente a un corte identificado | Versiones compatibles, effective currentness y dependencias | Nuevo para AXIGNAL no significa nuevo en el mundo |
| Â¿QuÃ© experiencias se han declarado? | Patrones pÃºblicos por producto/sede/ventana | Observaciones permitidas, deduplicaciÃ³n, escalas nativas | Review no prueba el hecho narrado ni la calidad global |
| Â¿Por quÃ© deberÃ­a creerlo? | Prueba navegable desde el output | Material exacto, provenance, contradicciones y reglas | Una cita decorativa no fundamenta cualquier frase |
| Â¿DÃ³nde lo dejamos? | InvestigaciÃ³n restaurada y cambios desde el checkpoint | Memoria privada de pregunta/origen/corte | El origen ausente sigue UNKNOWN |

V1 ofrece observaciÃ³n viva y estas proyecciones segÃºn cobertura real. V2/AEAP interroga recursivamente ese conocimiento para un informe ejecutivo; V3 lo cruza con evidencia privada autorizada. V2/V3 son especificaciones propuestas, no capacidades desplegadas. Las slices internas no constituyen por sÃ­ mismas un producto de valor completo para vender. [Subscriber](D:/AXIGNAL/Axignal/docs/product/AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md), [V2](D:/AXIGNAL/Axignal/docs/product/AXIGNAL_V2_DEEP_REPORT_EXECUTIVE_ANALYSIS_SPEC.md), [V3](D:/AXIGNAL/Axignal/docs/product/AXIGNAL_V3_PRIVATE_CROSS_INTELLIGENCE_SPEC.md).

## 3. Arquitectura lÃ³gica y bucles

```mermaid
flowchart TD
  U[Suscriptor: aÃ±ade 1 o N Organizaciones] --> C[Contexto autorizado y atenciÃ³n privada por OrganizaciÃ³n]
  C --> P[Prime: plan, frontier, derechos, presupuesto y parada]
  P --> S[Source Router e instrumentos: observar o investigar]
  S --> O[Observation Memory: raw permitido, intentos y tiempo]
  O --> R[RepresentaciÃ³n, identidad y estado suficiente]
  R --> J[Determinismo o juicio tipado reemplazable]
  J --> I[InterpretaciÃ³n econÃ³mica Python y dependencias]
  R --> A[EvidenceAdmission exacta cuando corresponde]
  J -. soporte auxiliar .-> A
  A --> K[AXIGLAND: mundo canÃ³nico temporal]
  K --> I
  I --> F[Frontier: preguntas materiales pendientes]
  F --> P
  I --> H[Human Output Compiler y verificaciÃ³n]
  H --> Q[ProyecciÃ³n autorizada: significado, incertidumbre y prueba]
  Q --> G[UI Plan gobernado + registry + layout estable]
  G --> V[Panorama, Evidence, Evolution y AXENT / AI SDK 7]
  V --> C
  O --> T[Temporalidad y detecciÃ³n de cambio]
  T --> P
  T --> I
  P -. ejecuciÃ³n y costes .-> M[Learning Memory / Admin]
  H -. calidad y entrega .-> M
  C --> CM[Continuidad cognitiva privada]
  CM --> Q
  X[Evidencia privada opcional V3] --> XP[Plano analÃ­tico privado autorizado]
  K --> XP
  XP --> H
```

Es un sistema de bucles, no una cadena que obliga a pasar por LLMâ†’Jevâ†’admisiÃ³n. Una fuente directamente atribuible puede evitar retrieval; un cÃ¡lculo exacto evita modelo; una INXIGHT POTENTIAL puede ser Ãºtil sin crear nuevos FAXT. Una pregunta sin contexto provoca investigaciÃ³n o abstenciÃ³n. La presentaciÃ³n no reentra como evidencia del mundo.

Los seis Ã¡mbitos son: percepciÃ³n; conocimiento/tiempo; razonamiento econÃ³mico; outputs humanos; interacciÃ³n generativa; operaciones del proveedor. Son lÃ­mites de responsabilidad, no seis microservicios obligatorios. [Atlas](D:/AXIGNAL/Axignal/docs/architecture/AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md), [doctrina de discovery](D:/AXIGNAL/Axignal/docs/product/AXIGNAL_ECONOMIC_DISCOVERY_ENGINE_DOCTRINE_2026-09-30.md).

## 4. Autoridades y aislamiento

| Ãmbito | QuÃ© conserva | QuÃ© puede decidir |
|---|---|---|
| AXIGLAND compartido | Identidad y conocimiento econÃ³mico canÃ³nico, historia y provenance | Estado admitido y derivaciones gobernadas |
| Observation Memory | Lo adquirido bajo derechos, condiciones y tiempo | Registro de observaciÃ³n; no convertir claims en hechos |
| Contexto privado de observaciÃ³n | Foco, trabajo, permisos y referencias de un tenant/client | AtenciÃ³n y ejecuciÃ³n autorizada |
| Continuidad cognitiva privada | Preguntas, origen real, checkpoints y navegaciÃ³n significativa | RestauraciÃ³n y densidad de explicaciÃ³n |
| Plano privado V3 | Datos concedidos y anÃ¡lisis contextual por tenant/client | Hallazgos privados; nunca una copia privada de AXIGLAND |
| Admin de AXIGNAL | OperaciÃ³n, costes, billing, CRM interno y fiscalidad del proveedor | Comandos del servicio propietario bajo autoridad de staff |

La autorizaciÃ³n se evalÃºa antes de recuperar contenido y de nuevo al liberarlo. Un ID de organizaciÃ³n, una URL, una elecciÃ³n de modelo o una suscripciÃ³n no concede acceso a datos privados. Client A y Client B siguen separados aunque observen la misma OrganizaciÃ³n. El cambio de cliente invalida requests/streams anteriores mediante context version.

El CRM interno autorizado por ADR-0055 opera AXIGNAL; no gestiona el negocio del suscriptor ni acredita relaciones de AXIGLAND. El registro AO-24 de medidas es privado Admin/advisory: reutilizar su patrÃ³n de contratos no lo convierte en autoridad universal de mediciÃ³n pÃºblica DRI. [ADR-0055](D:/AXIGNAL/Axignal/docs/adr/ADR-0055-admin-private-business-operations-separation.md), [ADR-0071](D:/AXIGNAL/Axignal/docs/adr/ADR-0071-governed-measurement-registry.md), [ADR-0076](D:/AXIGNAL/Axignal/docs/adr/ADR-0076-tenant-reuse-authorization-before-narrative-access.md).

## 5. Entrada, investigaciÃ³n y primera entrega

1. Un suscriptor registra una o varias Organizaciones para observaciÃ³n persistente, mediante altas individuales o un lote autorizado. El servidor autentica y resuelve tenant/client/membresÃ­a y los derechos/cupos del servicio que procedan. El alta no acredita propiedad ni representaciÃ³n de la empresa.
2. Por cada entrada valida las pistas disponibles de identidad, conserva idempotency key y devuelve aceptaciÃ³n, duplicado, desambiguaciÃ³n o rechazo con su causa. La identidad puede quedar pendiente sin fingir un sujeto resuelto; un homÃ³nimo pendiente no impide procesar las otras entradas.
3. Persiste o recupera el foco privado de cada OrganizaciÃ³n y su intenciÃ³n; devuelve su estado real. Una OrganizaciÃ³n canÃ³nica puede ser observada por varios suscriptores mediante focos privados distintos, sin duplicar la verdad compartida.
4. Comprueba conocimiento reutilizable por sujeto, purpose, derechos y effective currentness. Conserva el motivo de reuse o rechazo y agrupa trabajo pÃºblico compartible cuando corresponde.
5. Prime selecciona preguntas y observaciones suficientes por foco dentro del presupuesto del servicio, del tenant y de la operaciÃ³n. Una cola con concurrencia acotada y reparto de capacidad impide que cien altas bloqueen a otros suscriptores o multipliquen adquisiciones equivalentes.
6. Worker durable adquiere fuentes autorizadas, registra todos los outcomes, genera representaciÃ³n verificable y calcula dimensiones answerable. La adquisiciÃ³n no mantiene un lock del catÃ¡logo ni exige que el navegador espere el scan completo.
7. Compone outputs parciales Ãºtiles por OrganizaciÃ³n: identidad, descripciÃ³n sustentada, limitaciÃ³n de cobertura, brecha o pregunta pendiente. Readiness depende de utilidad y suficiencia declaradas para cada familia, no de un cronÃ³metro o porcentaje decorativo.
8. Publica revisiones de proyecciÃ³n por OrganizaciÃ³n y una vista de cartera autorizada. La UI puede mostrar resultados disponibles sin esperar a las cien; cada elemento mantiene scope, estado y ruta a evidencia. El panorama se amplÃ­a conservando sujeto y continuidad.

### 5.1 Customer Zero interno

Customer Zero significa **AXIGNAL como usuario de su propio producto**. Puede usar el mismo Brain y la misma proyecciÃ³n de producto para testar y aprovechar informaciÃ³n real. Observar AXIGNAL tiene la misma carga de evidencia que observar otra OrganizaciÃ³n. No es un mock ni una fuente alternativa de verdad.

El formulario interno Â«nombre y URLÂ» y la autorizaciÃ³n de staff pertenecen a esa entrada operativa. Su existencia no prueba que estÃ©n implementados identidad comercial, membresÃ­as, entitlements, altas masivas o aislamiento de suscriptores. Esas capacidades necesitan su propio recorrido y validaciÃ³n de producciÃ³n. Reutilizar el motor no equivale a reutilizar un grant administrativo como permiso del suscriptor. [Appendix Customer Zero](D:/AXIGNAL/Axignal/docs/governance/AXIGNAL_ADMIN_CUSTOMER_ZERO_APPENDIX_2026-10-04.md), [spec AO-24A](D:/AXIGNAL/Axignal/specs/037-admin-customer-zero/spec.md).

### 5.2 Contrato de entrada de 1, 2 o 100 Organizaciones

La cardinalidad describe atenciÃ³n persistente del suscriptor; no implica cien bases de datos, cien entidades nuevas o cien llamadas simultÃ¡neas. Conservar estado por entrada y por foco; permitir reintento de fallos sin repetir las aceptadas; mantener pendientes de identidad separadas de observaciones econÃ³micas; y deduplicar el trabajo compartible sin mezclar datos privados.

Â«Lote de altas de OrganizacionesÂ» y Â«batch de preguntas Jev sobre un estadoÂ» son optimizaciones distintas. No reunir estados de cien empresas en un batch semÃ¡ntico por el mero hecho de haber sido registradas juntas. La vista de cartera tampoco amplÃ­a permisos por sÃ­ misma: sÃ³lo agrega outputs de focos autorizados.

Â«Primera entregaÂ» y FIRST_MAP_WOW no justifican inventar nodos. En el caso de presencia escasa, la entrega puede ser una limitaciÃ³n informativa acompaÃ±ada de una pregunta Ãºtil. Exponer un mapa vacÃ­o sin explicaciÃ³n transfiere trabajo cognitivo al humano; rellenarlo con hipÃ³tesis no etiquetadas rompe doctrina.

## 6. PercepciÃ³n: fuentes e instrumentos

Un registro propuesto de fuentes/capabilities declara purpose, canal, superficie, sujeto/resoluciÃ³n, cobertura geogrÃ¡fica/idiomÃ¡tica, derechos, lÃ­mites, retenciÃ³n, borrado, transmisiÃ³n a proveedores, coste/unidad y estado operacional. Un instrumento de mediciÃ³n declara pregunta, protocolo versionado, queries/prompts congelados, detector de sujeto, conditions, rÃ©plica, muestra informativa y comparabilidad.

Fuentes distintas cubren preguntas distintas: registros para identidad legal; web atribuible para oferta declarada; documentos corporativos para estructura/resultados; contrapartes para relaciones; proyectos/procurement para actividad y necesidad; superficies digitales para representaciÃ³n; reviews para declaraciones pÃºblicas de experiencia. Un proveedor no define la semÃ¡ntica de ninguna familia.

HTTP condicional, fingerprints y comprobaciÃ³n de cambio reducen trabajo repetitivo cuando el canal lo permite. Discovery/research obtiene fuentes nuevas; sensores industrializan observaciÃ³n estable. Un browser se aÃ±ade sÃ³lo para un requerimiento demostrado y autorizado. La instalaciÃ³n de un MCP no autoriza automÃ¡ticamente todas sus herramientas.

Cada intento registra al menos run/parent, instrumento/version, condiciones, inicio/final, outcome, coste conocido/UNKNOWN, source ref y artifact permitido. Timeout, bloqueo, 403, error de detector, falta de permiso y ausencia en un resultado completo son estados distintos. La ausencia requiere conservar tambiÃ©n el protocolo y el conjunto examinado, no sÃ³lo una lista vacÃ­a.

## 7. Presencia escasa: un output con dos niveles

### 7.1 Nivel inmediato: hallazgo y brecha documentada

La primera cuestiÃ³n es Â«Â¿Encontramos al sujeto en las superficies y consultas que medimos?Â», no Â«Â¿La empresa hace mal marketing?Â». Se distinguen branded findability, representaciÃ³n de categorÃ­a/capability, cobertura geogrÃ¡fica, atribuciÃ³n correcta y disponibilidad del canal. No se suman para fabricar un score digital universal.

Ejemplo **sintÃ©tico**, no mediciÃ³n de una empresa real: se planifican doce ejecuciones de bÃºsqueda bajo un instrumento; ocho completan de forma informativa y cuatro fallan. En las ocho no aparece la entidad correctamente resuelta. El output puede decir:

> No encontramos a esta organizaciÃ³n en las ocho bÃºsquedas que pudimos completar bajo estas condiciones. Cuatro consultas quedaron sin medir. Esta muestra no permite concluir que carezca de presencia pÃºblica.

Las condiciones, consultas, lÃ­mites del detector, fechas y resultados estÃ¡n accesibles en Evidence. El denominador es ocho, no doce. Un cero en la muestra es vÃ¡lido sÃ³lo si el instrumento lo define y la muestra es informativa; NOT_MEASURED/INSUFFICIENT llevan valor null. Un hallazgo de ausencia acotada se conserva como observaciÃ³n del instrumento; una RepresentationGap que cruza ese hallazgo con capacidad o relevancia econÃ³mica es derivada y necesita basis.

Una recomendaciÃ³n inicial es condicional: Â«Si estas bÃºsquedas corresponden a cÃ³mo tus compradores buscan esta capacidad, conviene revisar su representaciÃ³nÂ». No afirma daÃ±o comercial ni una causa. Objetivos proporcionados por la empresa son contexto privado declarado, no verdad canÃ³nica.

### 7.2 Nivel investigado: diagnÃ³stico y recomendaciones

AXENT abre preguntas materiales: Â¿estÃ¡ bien resuelta la identidad/marca?, Â¿son pertinentes las consultas y geografÃ­as?, Â¿quÃ© capability estÃ¡ sustentada?, Â¿es el canal relevante para sus compradores?, Â¿hay una explicaciÃ³n alternativa?, Â¿las condiciones son comparables?, Â¿quÃ© evidencia permitirÃ­a discriminar hipÃ³tesis?

La investigaciÃ³n puede contrastar aliases/rebrand, indexabilidad observable, atribuciÃ³n, contenido sobre capabilities, canal de adquisiciÃ³n, mercado y referencias comparables. Una empresa con canal B2G especializado o distribuciÃ³n indirecta puede no necesitar la misma estrategia de presencia que un servicio local. Un bloqueo del sensor requiere reparar cobertura, no recomendar marketing.

El diagnÃ³stico entrega: brecha y alcance; hipÃ³tesis contrastadas; soporte y contradicciones; restricciones; recomendaciones condicionadas; evidencia que falta; y un protocolo para verificar posteriormente cambios. No atribuye causalidad a SEO/GEO por un simple antes/despuÃ©s. La agencia o empresa actÃºa fuera de AXIGNAL; AXIGNAL reobserva con independencia.

### 7.3 CÃ³mo saber quÃ© nivel aporta mÃ¡s valor

Conservar ambos sobre el mismo output_id, con revisiones, fecha y estado. El resumen inicial sigue accesible; el diagnÃ³stico amplÃ­a o corrige la interpretaciÃ³n sin reescribir el pasado. Abrir PROVE directamente sigue siendo posible antes del diagnÃ³stico.

Comparar con usuarios: comprensiÃ³n correcta y tiempo del nivel inicial; mejora de decisiÃ³n y utilidad del diagnÃ³stico; esfuerzo humano; coste incremental de investigaciÃ³n; correcciones; voluntad de recibir/financiar el nivel adicional. Un experimento con datos fijos puede aislar efecto de presentaciÃ³n. Otro debe medir valor de evidencia adicional; no atribuirle a la UX un efecto de haber aportado mÃ¡s informaciÃ³n. No declarar vencedor antes de esa evaluaciÃ³n.

## 8. OpenSEO y Utopia: adopciÃ³n por mecanismo

**OpenSEO:** candidato de sensor/laboratorio, especialmente para SERP, footprint, auditorÃ­a y comparaciÃ³n de presencia. Su MCP incluye lecturas y tambiÃ©n operaciones de proyecto/publicaciÃ³n; la integraciÃ³n propuesta permite Ãºnicamente capabilities explÃ­citas que cumplen los contratos de AXIGNAL. GSC permanece privado. El coste de datos y derechos del canal son distintos de la licencia del software. [MCP oficial](https://openseo.so/docs/mcp).

Comparar un adapter directo con OpenSEO como intermediario usando la misma pregunta: Â¿preserva parÃ¡metros, raw permitido, task/run IDs, muestra, errores, coste y versiones?, Â¿aporta funciones que compensan otro servicio y otra autoridad operacional? Un dato SEO transformado sin trazabilidad suficiente puede ser Ãºtil para exploraciÃ³n, pero no se convierte en mediciÃ³n comparable. Â«AI VisibilityÂ» requiere inspeccionar el instrumento concreto antes de asignarle semÃ¡ntica GEO. La propuesta no instala OpenSEO ni declara su integraciÃ³n ejecutada.

**Utopia:** referencia para tiempo, queries tipadas, provenance y correcciones. No se adopta como autoridad canÃ³nica o modelo de datos alternativo. Su documentaciÃ³n MCP distingue world time y record time y reconoce lÃ­mites del proof histÃ³rico/export; esas limitaciones deben formar parte del bakeoff, no ocultarse por la presencia de un grafo temporal. [Contrato MCP](https://github.com/deeplethe/utopia/blob/main/web/src/docs/mcp.md).

Los detalles de integraciÃ³n, incompatibilidades, versiones y experimentos estÃ¡n en el [registro tÃ©cnico](D:/AXIGNAL/Axignal/docs/research/e2e-outputs-2026-10-05/DECISIONES_Y_EVIDENCIA.md). La arquitectura funciona sin que un proveedor concreto estÃ© disponible; informa de la cobertura que pierde.

## 9. Jev como motor semÃ¡ntico econÃ³mico

El activo de AXIGNAL es su catÃ¡logo versionado de preguntas, information requirements, choice spaces/rÃºbricas y polÃ­ticas de composiciÃ³n. Jev es candidato reemplazable para ejecutar dimensiones answerable sobre estado pertinente: oferta, compra, tipo de necesidad, relaciÃ³n/direcciÃ³n, correspondencia funcional, soporte contextual, conflicto o relevancia. Noul para proposiciones independientes; Choice para alternativas excluyentes; Score para rÃºbricas ordinales. [Primitivas TypeSafe](https://docs.typesafe.ai/primitives).

Supplier y customer pueden coexistir. Identidad exacta, fechas, montos, counters, permissions y lÃ­mites se calculan en Python. Se preservan raw answers/distributions, leyenda, model version, state/question/answer-space fingerprints, coste/latencia observados y disposiciÃ³n. Falta material se resuelve antes del proveedor; UNKNOWN no se vuelve un Noul false.

Preguntas independientes con el mismo estado pueden agruparse; un segundo ciclo obtiene datos que dependan de una respuesta anterior. Batch es transporte, no unidad indivisible de cache ni corroboraciÃ³n entre respuestas. Reuse/invalidaciÃ³n es por dimensiÃ³n y sus inputs. [Fan-out](https://docs.typesafe.ai/patterns/fan-out).

El adapter local aÃºn construye `[definition]` por llamada. La propuesta requiere variantes neutrales Noul/Choice/Score y un request-set con gate por dimensiÃ³n; no forzar todo al puerto Choice existente. La selecciÃ³n productiva requiere corpus, derechos y comparaciÃ³n real. El [estudio Jev](D:/AXIGNAL/Axignal/docs/audits/brain-2026-10-04/JEV_ARQUITECTURA_Y_POTENCIAL_AXIGNAL_2026-10-05.md) desarrolla economÃ­a, defectos del lab y evaluaciÃ³n.

## 10. Memoria, identidad, tiempo y canonizaciÃ³n

Identity Resolution conserva candidatos, aliases, scope y merges reversibles; la semejanza no es autoridad. Entity legal, marca, producto y sede se distinguen antes de atribuir ausencia o experiencia. Un sujeto ambiguo retiene UNRESOLVED y puede requerir desambiguaciÃ³n humana como atenciÃ³n, sin conceder ediciÃ³n de verdad.

Observation Memory conserva observaciones valiosas aunque no sean admisibles como FAXT. EvidenceAdmission autentica contenido y proposiciÃ³n exactos, autoridad por predicate, sujeto, valor, observaciÃ³n y policy. Factories/replay no aceptan una decisiÃ³n para otro tuple. Un structured verdict aporta soporte auxiliar, nunca permiso de write. [ADR-0072](D:/AXIGNAL/Axignal/docs/adr/ADR-0072-proposition-bound-evidence-admission.md), [ADR-0073](D:/AXIGNAL/Axignal/docs/adr/ADR-0073-canonical-materialization-relationship-admission.md).

La extensiÃ³n temporal propuesta distingue observed/retrieved time, valid time cuando estÃ© sustentado y recorded time. Fecha de publicaciÃ³n no es fecha de inicio econÃ³mico. Un dato tardÃ­o puede alterar quÃ© sabemos ahora sobre el pasado, conservando quÃ© sabÃ­amos entonces. El valor temporal permanece UNKNOWN si la fuente no lo establece.

Effective currentness se calcula al consumir y proyectar, con as_of y policy version. Raw/history no se reescribe al envejecer. Una reobservaciÃ³n fresca no refresca silenciosamente el soporte de una seÃ±al vieja. Cambios de fuente, derechos, mÃ©todo, contrato o modelo invalidan las derivaciones pertinentes; el borrado puede dejar una referencia no disponible y limitar el replay. [ADR-0077](D:/AXIGNAL/Axignal/docs/adr/ADR-0077-temporal-currentness-propagation-at-consumption.md), [ADR-0079](D:/AXIGNAL/Axignal/docs/adr/ADR-0079-immutable-legacy-evidence-identity-replay-conflict.md).

## 11. Economic Reasoner y polÃ­tica de investigaciÃ³n

La oportunidad cruza capability, necesidad, roles, reach por capability, tiempo, restricciones y evidencia. Filtros duros rechazan sÃ³lo incompatibilidades demostradas; missing material no equivale a rechazo. Jev puede tipar correspondencia o actividad; Python compone disposition POTENTIAL, INVESTIGATE o abstenciÃ³n. Precio, certificaciÃ³n, disponibilidad, incumbente y acceso no aparecen por inferencia conveniente.

Research Value Gate controla derechos/capability, materialidad informativa, presupuesto, deadline y progreso. Una evaluaciÃ³n de relevancia es input reemplazable, no gobierno. El plan limita hops, nÃºmero de tareas y concurrencia; la expansiÃ³n del neighbourhood responde a valor informativo, no a completitud infinita.

Paradas explÃ­citas: pregunta contestada con suficiencia; falta privada sin acceso; fuente no autorizada; reserva insuficiente; no progreso tras intentos delimitados; ambiguity irreducible; o deadline. Preservar pregunta, exploraciones y motivo de parada evita volver a pagar la misma investigaciÃ³n. Los outputs describen esa frontera sin fingir que el anÃ¡lisis terminÃ³ el mundo econÃ³mico.

AXENT propone queries/fuentes, investiga huecos, contrasta alternativas y explica el basis. No posee SQL arbitrario, credenciales de base de datos o un escritor canÃ³nico. Sus tools son operaciones de un Context Broker autorizado y acotado. [Continuidad/contexto](D:/AXIGNAL/Axignal/docs/architecture/HFX_COGNITIVE_CONTINUITY_AND_MEMORY_ARCHITECTURE.md).

## 12. Human Output Compiler: la frontera que faltaba en la tesis E2E

Â«Human Output CompilerÂ» es nombre de responsabilidad **propuesta**, no paquete implementado ni tÃ©rmino canÃ³nico nuevo. Consume derivaciones y observaciones autorizadas; construye una representaciÃ³n semÃ¡ntica verificable antes de elegir componentes. Lo dirige application/subscriber_projection y preserva Human Output Contract de HFX.

Un contrato de wire candidato contendrÃ­a:

```text
HumanOutput (propuesta v0.1)
  identity: output_id, revision, subject_ref, semantic_family, archetype
  context: authorized_scope_ref, context_version, locale, as_of
  state: epistemic_state, temporal_state, completeness, attention_reason_refs
  meaning: headline, one_sentence_meaning, why_it_may_matter
  basis: proposition_refs, derivation_ref/version, considered_evidence_refs
  measure?: definition_ref/version, value|null, unit, denominator,
            window, instrument_ref/version, conditions, uncertainty
  limits: unknowns, contradictions, withheld_claims, coverage_limits
  understand: context, drivers, blockers, comparison_ref?
  prove: authorized_evidence_targets, observation_refs, instrument_targets
  navigate: related_refs, evidence_target, evolution_target, research_question_ref?
  continuity?: investigation_ref, checkpoint_ref, recorded_origin_ref|null
```

Son ejes independientes: familia, estado epistÃ©mico, temporalidad, atenciÃ³n y arquetipo. No un estado combinado Â«bueno/maloÂ». El modelo puede proponer palabras; el contrato exige referencias y conserva limitaciones materiales. La variante sin modelo usa copy determinista y mantiene utilidad.

VerificaciÃ³n previa a publicaciÃ³n: resolver sujeto y revisiÃ³n; autorizar metadata antes de material; validar basis contra representaciÃ³n/extracciÃ³n exactas; incluir contradicciones consideradas; comprobar cÃ¡lculo/unidades/denominador/instrumento; resolver relaciones/caminos; verificar alcance de cada afirmaciÃ³n; preservar UNKNOWN y effective currentness. Material narrativo rechazado no se sustituye por una historia plausible. [ADR-0075](D:/AXIGNAL/Axignal/docs/adr/ADR-0075-exact-explainable-basis-narrative-verification.md), [HFX](D:/AXIGNAL/Axignal/docs/product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md).

Persistir output y versiÃ³n de su basis permite replay, explicaciÃ³n y export coherentes. No es una segunda base de hechos: es proyecciÃ³n con refs a las autoridades originales. Markdown/JSON/Product MCP y UI consumen la misma revisiÃ³n autorizada.

## 13. UI generativa gobernada con AI SDK 7

Se conserva el brief: LEFT navegaciÃ³n estable; CENTER canvas de observaciÃ³n adaptable; RIGHT AXENT contextual; BOTTOM tiempo global; TOP recorrido/back/forward. Today, Explore, Evolution y Evidence siguen siendo modos de comprensiÃ³n. La experiencia bÃ¡sica entrega valor sin prompt. [Brief aceptado](D:/AXIGNAL/Axignal/docs/design/AXIGNAL_FRONTEND_BRAND_GENERATIVE_EXPERIENCE_MASTER_BRIEF.md).

AI SDK 7 es la direcciÃ³n solicitada y ya estÃ¡ instalado (`ai` 7.0.127, `@ai-sdk/react` 4.0.130). La documentaciÃ³n oficial permite componentes propios asociados a salidas tipadas y streaming de data parts. La arquitectura aprovecha AI SDK UI; no presupone que Generative UI signifique JSX libre o un nuevo framework visual. [Generative UI](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces), [custom data](https://ai-sdk.dev/docs/ai-sdk-ui/streaming-data).

La propuesta E2E es:

```text
Authorized HumanOutput snapshot
 â†’ task/depth/locale + optional semantic presentation hints
 â†’ UIPlan proposal referencing existing outputs
 â†’ deterministic validation against scope/revision/component registry
 â†’ stable responsive layout
 â†’ AI SDK typed stream / UI parts
 â†’ React component render + accessible equivalent
```

UIPlan sÃ³lo selecciona refs y arquetipos disponibles: resumen, estado, cambio, comparaciÃ³n, oportunidad, gap, timeline, mapa, relaciÃ³n, tabla, warning y proof. Cada componente declara props, lÃ­mites, accessibility, navegaciÃ³n y quÃ© datos exige. Si no estÃ¡n, se usa unknown/insufficient/researching, no una variante con nÃºmeros inventados. Las medidas las calcula el productor; el modelo no las recompone desde texto.

Python conserva cognition/router + CognitiveProvider; SDK concretos productivos quedan en cognition/providers. Next/BFF transporta proyecciones y streams autorizados. AI SDK UI puede consumirlos sin mover el control del Brain al frontend. Cualquier ejecuciÃ³n generativa en un runtime TypeScript separado necesitarÃ­a adapter/puerto neutral revisado que conserve esa frontera; no introducir un segundo router de proveedores por conveniencia. Este diseÃ±o inicial no necesita esa duplicaciÃ³n.

La guÃ­a oficial considera AI SDK RSC experimental para producciÃ³n estable y recomienda AI SDK UI. Por tanto, no basar el target en el histÃ³rico streamUI/createStreamableUI. Instalar el SDK no exige desplegar en Vercel. [GuÃ­a RSCâ†’UI](https://ai-sdk.dev/docs/ai-sdk-rsc/migrating-to-ui).

## 14. Streaming, continuidad y estabilidad cognitiva

Separar ObservationRun del stream de presentaciÃ³n. El worker durable es dueÃ±o del trabajo econÃ³mico; desconectar el navegador cancela o detiene su suscripciÃ³n de UI segÃºn policy, no pierde el run. Cancelar una investigaciÃ³n es un comando explÃ­cito, versionado y presupuestado; no un efecto implÃ­cito de cerrar una pestaÃ±a.

Envelope propuesto por evento: request_id, context_version, subject_ref, projection_revision, output_id/revision?, event_id, sequence, kind y payload tipado. Eventos de progreso describen trabajo real. Una narrativa material sÃ³lo llega al estado publicable tras validaciÃ³n; las data parts de progreso pueden transmitirse antes. Una interrupciÃ³n nunca deja una afirmaciÃ³n incompleta presentada como verificada.

La reconstrucciÃ³n tras reconnect parte de una revisiÃ³n persistida y secuencia; reautoriza. Ignorar respuestas de otro context_version y revalidar refs al recuperar historial. El SDK proporciona herramientas de protocolo, no el modelo de continuidad ni autoridad. Su guÃ­a recomienda validateUIMessages para tool/data/metadata antes de procesar mensajes; eso complementa la validaciÃ³n de scope/semÃ¡ntica propia. [Persistencia oficial](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-message-persistence).

Visual hysteresis y claves estables evitan que un cambio menor de prioridad reordene el canvas mientras la persona lee. Las actualizaciones materiales son visibles y reversibles; conservar foco, selecciÃ³n y breadcrumb. GLANCEâ†’UNDERSTANDâ†’REASONâ†’PROVE permite acceso directo a cualquier profundidad. Densidad cambia con tarea/elecciÃ³n, no con una inferencia de rasgos psicolÃ³gicos.

Checkpoint privado guarda pregunta, refs al entonces, pendientes y origen cuando existe; el transcript AXENT y el UI navigation log siguen separados. Borrar memoria privada o retirar derechos propaga a Ã­ndices derivados y limita restauraciÃ³n; el sistema lo declara. El usuario puede revisar la versiÃ³n que vio y la vigente, sin falsa continuidad temporal.

## 15. Acceso privado y diagnÃ³stico contextual

La primera brecha no exige conectar cuentas. Si una pregunta concreta necesita datos privados, una solicitud contextual explica quÃ© se quiere discriminar, recurso/property, ventana, alcance mÃ­nimo, read-only, propÃ³sito, duraciÃ³n, destinatarios/proveedores y quÃ© puede concluirse sin acceso. Aprobar intenciÃ³n no sustituye OAuth ni verificaciÃ³n de permisos del proveedor.

Rechazar conserva el output pÃºblico y bloquea sÃ³lo la rama dependiente. La conexiÃ³n persistente muestra scope, estado, Ãºltimo uso y revocaciÃ³n; revocar corta futuros accesos y aplica retention/deletion de derivados. Scope no se amplÃ­a por contenido leÃ­do de una web. Credenciales no pasan por prompts ni transcript.

Search Console es evidencia privada contextual, no representaciÃ³n pÃºblica canÃ³nica. Su API advierte que devuelve top rows y no garantiza todas las filas: falta de una fila no acredita cero impresiones globales. [API oficial](https://developers.google.com/webmaster-tools/v1/searchanalytics/query). La propia GSC de AXIGNAL en Admin y GSC concedida por un suscriptor son autoridades privadas distintas.

Se aplicaron los principios de scoped grant, progressive scope, receipt y revocaciÃ³n de la [skill agent-consent-patterns](C:/Users/usuario/.codex-clean/plugins/cache/openai-curated-remote/agent-consent-patterns/0.1.1/skills/agent-consent-patterns/SKILL.md), subordinados a V3 Â§44 y contratos de interacciÃ³n. No se instalÃ³ su librerÃ­a ni se creÃ³ una conexiÃ³n.

## 16. TopologÃ­a fÃ­sica y economÃ­a

**RecomendaciÃ³n de arranque:** monolito modular Python con lÃ­mites existentes, web Next/React existente y ejecuciÃ³n de workers separable del HTTP interactivo. Puertos de storage, queue y provider permiten evoluciÃ³n. No empezar con Kafka, graph DB, vector DB y varios agentes con ledgers duplicados por considerarlos Â«arquitectura avanzadaÂ».

Actual: SQLite/CAS y adapters delimitados. Candidato para multiworker/producciÃ³n futura: PostgreSQL + almacenamiento de objetos permitido, queue/outbox transaccional y search derivado. Es hipÃ³tesis fÃ­sica, no selecciÃ³n aceptada ni migraciÃ³n ejecutada. Medir concurrencia, locking, deduplicaciÃ³n, filtered recall, path queries, aislamiento, restore y coste antes de fijar infraestructura. Sigma/Graphology mantiene la elecciÃ³n inicial del renderer de ADR-0009; no decide almacenamiento canÃ³nico.

La semÃ¡ntica de delivery es at-least-once con idempotencia y replay, no una promesa de exactly-once sobre red/modelos. Estado+outbox se escriben juntos cuando corresponda; lease expiry, fencing token, retry acotado y unique work key previenen trabajo/commits de workers obsoletos. La idempotencia de efectos no garantiza que un proveedor no facture un request repetido; intentos y reconciliaciÃ³n lo registran.

Reservar coste/deadline antes de dispatch para fetch/search/model/storage significativo. UNKNOWN permanece incompleto junto a lower bound conocido; no se recupera como cero. Usage por run/operation/dimension alimenta Learning Memory y proyecciÃ³n unit economics existente. Distinguir coste compartido real de asignaciones privadas; moneda y tipo de conversiÃ³n fechados. Batch y reuse por cambio reducen costes sin dispensar derechos ni frescura.

La escalabilidad depende de fuentes Ãºnicas pertinentes, tasa de cambios y fan-out, ademÃ¡s de nÃºmero de Organizaciones. Dos tenants que observan un sujeto reutilizan evidencia pÃºblica autorizada; sus preguntas privadas y prioridades pueden diferir. No ejecutar todas las superficies DRI todos los dÃ­as por empresa sin valor informativo y envelope financiero.

## 17. Seguridad, calidad y operaciÃ³n como parte del output

| Riesgo | Control target | Resultado humano correcto |
|---|---|---|
| HomÃ³nimo/brand mismatch | ResoluciÃ³n multiclave y sujeto por observaciÃ³n | DesambiguaciÃ³n; diagnÃ³stico withheld |
| Canal bloqueado o indisponible | Attempt tipado y coverage explÃ­cita | Â«No pudimos medir esta superficieÂ» |
| Prompt injection en web/MCP | Datos separados de instrucciones, allowlist de tools, scopes mÃ­nimos | No acciÃ³n/autoridad adquirida por una fuente |
| Juicio malformed o fuera de rubric | ValidaciÃ³n por primitiva y replay exacto | DimensiÃ³n no disponible; no false por defecto |
| Hallazgo stale | Effective currentness al consumo y deps | HistÃ³rico/stale; propuesta de reevaluaciÃ³n |
| Cambio de instrumento | Comparability gate y bridge sÃ³lo validado | Discontinuidad; no trend ficticio |
| Otra persona/cliente en stream | Context version + reautorizaciÃ³n/release gate | Respuesta descartada antes de render |
| Narrativa omite contradicciÃ³n | Considered-evidence ledger y verificaciÃ³n | Conflicto visible o output rechazado |
| Research sin progreso/presupuesto | Research Value Gate y stops con receipt | Pregunta pendiente y motivo explÃ­cito |
| Fallo de modelo | ComposiciÃ³n/copy determinista y estado unavailable | Acceso a evidencia y panorama bÃ¡sico conservado |
| Retirada de derechos/raw | Tombstone/ref restringida y invalidaciÃ³n | Prueba no disponible; lÃ­mites de replay visibles |

La observabilidad une trace_idâ†’source attemptsâ†’representationsâ†’judgmentsâ†’derivationsâ†’outputsâ†’delivery. Registrar pÃ©rdidas por boundary distingue source miss, parser loss, retrieval miss, state insufficiency, evaluator error, policy error, admission rejection y fallo de comprensiÃ³n. Una mÃ©trica UX no sustituye correcta evidencia; un gate tÃ©cnico verde no demuestra comprensiÃ³n.

Admin pregunta si el servicio entrega outputs actuales y fundamentados, cuÃ¡nto cuesta, quÃ© familias carecen de cobertura, quÃ© research se repite y quÃ© quedÃ³ bloqueado. Mantiene sus propias mÃ©tricas y permisos; no ofrece editar una organizaciÃ³n del mundo econÃ³mico.

## 18. FotografÃ­a actual y delta hacia el target

InspecciÃ³n de cÃ³digo, no nueva verificaciÃ³n runtime E2E. Los documentos de septiembre contienen estados histÃ³ricos que pueden quedar por detrÃ¡s de ADRs/cÃ³digo posteriores; no tratar todo el gap ledger como fotografÃ­a actual.

| Pieza | Evidencia local actual | Delta target |
|---|---|---|
| UI / AI SDK | [package](D:/AXIGNAL/Axignal/apps/web/experience/package.json), [stream](D:/AXIGNAL/Axignal/apps/web/experience/app/api/axent/route.ts), [plan validator](D:/AXIGNAL/Axignal/apps/web/experience/lib/governance.ts) | SDK7 y composiciÃ³n limitada existen; generalizar desde contexto/demo a outputs del Brain autorizado sin fixture fallback |
| UX runtime | [runtime AXENT](D:/AXIGNAL/Axignal/apps/web/experience/lib/runtime-axent.ts), [projection contract](D:/AXIGNAL/Axignal/apps/web/experience/lib/runtime-projection.ts) | ExplicaciÃ³n determinista e intents regex; faltan investigaciÃ³n/evaluaciÃ³n semÃ¡ntica y continuidad completa |
| Primera fuente | [FirstProof](D:/AXIGNAL/Axignal/tools/runtime/first_proof.py) | Homepage/persistencia/proyecciÃ³n acotadas; capabilities y markets aÃºn vacÃ­os en ese read model; no demostrar con ello un Brain econÃ³mico completo |
| Proveedores | [router](D:/AXIGNAL/Axignal/cognition/router/router.py), [protocol](D:/AXIGNAL/Axignal/cognition/providers/base.py), [Jev lab](D:/AXIGNAL/Axignal/experiments/decision_lab/providers/typesafe.py) | Router explÃ­cito bÃ¡sico; Jev single-question experimental, no vector productivo compuesto |
| Contratos de Brain | [brain_contracts](D:/AXIGNAL/Axignal/application/economic_discovery/brain_contracts.py), [Prime execution](D:/AXIGNAL/Axignal/application/economic_discovery/prime_execution.py) | Reusar dimensiones/deps/control; completar mixed-primitive batch, persistencia/replay y ejecutores reales |
| Memoria | [observations](D:/AXIGNAL/Axignal/pipeline/observation_memory/sqlite_store.py), [learning](D:/AXIGNAL/Axignal/pipeline/learning_memory/sqlite_store.py) | Existen stores delimitados; composiciÃ³n durable/scheduler/output revisions requieren trabajo |
| Evidence / narrative | [admission](D:/AXIGNAL/Axignal/domain/evidence/admission.py), [narrative verification](D:/AXIGNAL/Axignal/application/subscriber_projection/narrative_verification.py), [access](D:/AXIGNAL/Axignal/application/subscriber_projection/narrative_access.py) | Hardening posterior al audit ya tiene contratos/cÃ³digo; preservar y extender, sin declarar vigentes todos los P0 histÃ³ricos |
| Tiempo | [currentness](D:/AXIGNAL/Axignal/application/economic_discovery/temporal_currentness.py), FirstProof + ADR-0077 | Aging al consumo y refs concretas existen; scheduler y rederivaciÃ³n general no quedan demostrados |
| Medidas | [AO-24 model](D:/AXIGNAL/Axignal/domain/admin_measurements/model.py), [service](D:/AXIGNAL/Axignal/application/admin_measurements/service.py) | PatrÃ³n implementado en plano privado; instrumento DRI y primera definiciÃ³n pÃºblica requieren su propio contrato |
| Oportunidad | [market entry](D:/AXIGNAL/Axignal/application/economic_discovery/market_entry.py), [explanation](D:/AXIGNAL/Axignal/application/economic_discovery/explanation.py) | Contratos de razonamiento Ãºtiles; falta vertical real desde necesidad/capability hasta comprensiÃ³n humana |

La anterior auditorÃ­a sigue siendo evidencia de su snapshot, no permiso para repetir conclusiones obsoletas. Esta propuesta no declara que existan integraciones OpenSEO/Utopia ni resultados de precisiÃ³n/latencia con Jev.

## 19. ImplementaciÃ³n incremental y demostraciÃ³n E2E

Orden por dependencia de valor; detalle en el [handoff](D:/AXIGNAL/Axignal/docs/research/e2e-outputs-2026-10-05/IMPLEMENTATION_HANDOFF.md). Cada feature no trivial sigue specifyâ†’clarifyâ†’planâ†’architecture reviewâ†’tasksâ†’implementâ†’converge. Este documento es entrada a ese proceso, no reemplazo de sus gates.

| Slice | Entrega verificable | Dependencias / criterio de salida |
|---|---|---|
| E0 â€” Contratos y baseline | Output contract, instrumentos, scope, dataset y pÃ©rdidas por boundary | Congelar fixtures rights-cleared/sintÃ©ticas; ninguna UI inventa truth o progreso |
| E1 â€” Run durable y presupuesto | AtenciÃ³n rÃ¡pida, worker/recovery, intentos completos, reserva/reconciliaciÃ³n | Deadline/cancel/crash/replay; cero double commit y costes incompletos honestos |
| E2 â€” Primera brecha | Identidad+presencia acotadaâ†’hallazgoâ†’HumanOutputâ†’Evidence | Denominadores y fallos correctos; UNKNOWN/coverage en la misma UI; adapter de fuente reemplazable |
| E3 â€” Jev econÃ³mico | Batch mixto, vector por dimensiÃ³n, coste/replay/reuse | Sanidad lab; corpus autorizado; roles coexistentes; comparaciÃ³n real y abstenciÃ³n |
| E4 â€” DiagnÃ³stico contextual | Research sobre brechaâ†’alternativasâ†’recomendaciones condicionadas | Stops/value gate; contraste de canal/objetivos y explicaciÃ³n ligada a fuentes |
| E5 â€” UI generativa/continuidad | Plan de componentes sobre outputs reales y checkpoint | Context switching seguro, layout estable, proof directo, accessible complement |
| E6 â€” Oportunidad y evoluciÃ³n | Capabilityâ€“need/reachâ†’POTENTIALâ†’nueva observaciÃ³nâ†’reevaluaciÃ³n | Procurement no cliente; inferencia visible; cambio limitado a deps; historial conservado |
| E7 â€” V2/V3/advisory | AnÃ¡lisis recursivo y privado cuando su scope se implemente | AEAP/full-value release; firewall y consentimiento; no contaminar AXIGLAND |

Una slice no obliga a comprar APIs ni desplegar. Tests contractuales y transport stubs prueban fallos deterministas; ensayos live posteriores exigen proveedor/datos/corpus autorizados y usage real. Human visual acceptance aplica sÃ³lo cuando se cambie materialmente una superficie; aquÃ­ no se altera el Golden Master.

## 20. QuÃ© significa que la arquitectura funciona

La verificaciÃ³n E2E de producciÃ³n comienza con suscriptor autenticado y alta de 1, 2 y 100 Organizaciones. Probar aceptaciÃ³n parcial, duplicados/reintentos, identidad pendiente, presupuesto, reparto de capacidad, aislamiento entre suscriptores y conocimiento pÃºblico compartible. Customer Zero prueba uso interno del producto y no sustituye estos casos.

Sobre esas altas exige cuatro recorridos conectados con traces y evidencia: organizaciÃ³n desconocida con cobertura suficiente; presencia escasa y cobertura incompleta; capability+necesidad con oportunidad POTENTIAL; y regreso posterior con cambio real/currentness. AÃ±adir variantes contradictorias, homÃ³nimos, cliente cambiado durante stream, proveedor caÃ­do, instrumento cambiado y presupuesto agotado.

Gates de verdad/seguridad son independientes del modelo: no canonical bypass; no leakage; permisos antes de payload; UNKNOWN sin conversiÃ³n; clocks/replay Ã­ntegros; errores de mediciÃ³n sin cero inventado; cada afirmaciÃ³n material con basis autorizado. Los gates requeridos del repo permanecen deterministas y offline.

Gates de servicio se fijan antes del piloto con baseline: time-to-first-useful-output; age/delivery lag; recovery; complete cost coverage; coste por output Ãºtil/reutilizable; pÃ©rdida de candidatos por capa; precisiÃ³n/riskâ€“coverage por dimensiÃ³n e idioma. No prometer p95, throughput, coste global o proveedor ganador sin workload medido.

Gates humanos siguen el [protocolo de diez segundos](D:/AXIGNAL/Axignal/docs/design/FIRST_VIEW_10_SECOND_COMPREHENSION_PROTOCOL.md) y [HFX research](D:/AXIGNAL/Axignal/docs/research/HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md): identificar significado, relevancia, certeza, cambio, lÃ­mites y ruta a evidencia; acceso experto sin perder contexto; restauraciÃ³n sin origen inventado. Today respeta su mÃ¡ximo actual de tres Ã­tems primarios. Una UX atractiva sin comprensiÃ³n epistÃ©mica falla.

La hipÃ³tesis competitiva es que memoria econÃ³mica y memoria de comprensiÃ³n se amortizan juntas: observar una vez cuando procede, componer muchas preguntas, explicar a distintas profundidades y recordar dÃ³nde estaba la persona. El valor acumulativo debe demostrarse en utilidad y coste, conservando independencia de la observaciÃ³n. Esa es la tesis E2E que este diseÃ±o convierte en responsabilidades, contratos y slices revisables.
