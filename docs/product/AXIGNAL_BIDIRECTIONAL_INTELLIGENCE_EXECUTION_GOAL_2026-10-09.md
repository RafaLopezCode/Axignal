# AXIGNAL — Goal de producto: inteligencia bidireccional y autocrítica evidenciada

> **Estado:** PREPARADO PARA EJECUCIÓN FUTURA · NO INICIADO
> **Fecha:** 2026-10-09
> **Naturaleza:** contrato de resultado de producto / brief de CTO, **no** un nuevo MASTER, ADR, spec implementable ni autorización de despliegue.
> **Activación:** únicamente **después** del cierre verificable del trabajo vigente de Claude Opus 5.5 sobre First Observation / spec 063 y de una orden explícita del CTO.
> **Responsable de ejecución previsto:** Claude Opus 5.5, `FRONTIER_AGENT`, con autonomía sobre investigación, diseño y ejecución dentro de la autoridad vigente.
> **Ámbito:** AXIGNAL como observing economic brain; AXIGLAND único, canónico y gobernado; AXENT, evaluadores estructurados sustituibles (JEV entre ellos), Python y experiencia de suscriptor / agencia.

## 0. Cómo leer este documento y dónde reside su autoridad

Este documento **recupera el propósito funcional fundacional**, fija la experiencia que debe demostrarse y define criterios de aceptación. **No reescribe** la doctrina existente ni ordena comenzar la implementación ahora. Antes de ejecutar, contrastar la versión vigente de:

1. `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`: §§7–9, 13–16, 27–29, 42, 53–56, especialmente §§54, 55 y 56.13–56.19.
2. `.specify/memory/constitution.md` y `docs/adr/`.
3. `docs/adr/ADR-0014-digital-representation-intelligence.md` y `ADR-0015-digital-measurement-instruments-and-observation-reuse.md`.
4. `docs/adr/ADR-0011-jev-structured-decision-reconciliation.md`, `ADR-0047-provider-neutral-structured-evaluator-contract.md`, `ADR-0048-evaluator-decision-lab-bakeoff-governance.md`, `ADR-0090-semantic-judgment-layer.md`.
5. `docs/product/AXIGNAL_DIGITAL_REPRESENTATION_INTELLIGENCE_PRODUCT_SPEC.md` y `docs/product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md`.
6. Specs, código y tests vigentes de `062-semantic-judgment-layer` y `063-first-observation-loop`, cuando estén integrados.

**Precedencia:** MASTER > Constitution > ADRs > Feature Specs > Plans/Tasks > implementación; este brief no puede contradecir ningún elemento superior. Si existe conflicto, se identifica y escala antes de cambiar doctrina. Los ejemplos son aspiracionales; no constituyen métricas medidas, capacidades desplegadas ni evidencia sobre empresas reales.

## 1. La tesis del producto

**AXIGNAL observa dos direcciones inseparables:**

- **DEL MUNDO HACIA LA ORGANIZACIÓN.** Qué está ocurriendo en su mundo económico: actividad, capacidades, mercados, compradores, competidores, demanda, proyectos, reputación, relaciones potenciales, cambios y oportunidades que merecen atención.
- **DE LA ORGANIZACIÓN HACIA EL MUNDO.** Qué información pública ofrece sobre sí misma, cómo la representan distintas superficies y qué puede comprender un observador externo a partir de la evidencia efectivamente disponible.

Ninguna es secundaria. La primera muestra qué puede descubrirse **para** la organización; la segunda muestra qué pueden descubrir **sobre** la organización quienes la encuentran.

La segunda dirección debe producir **autocrítica constructiva respaldada por evidencia**, no solo un diagnóstico neutro de ausencia de datos. En AXIGNAL un hallazgo desfavorable puede ser tan útil o más que uno positivo. La experiencia debe explicitar fortalezas, déficits observados, interpretaciones ambiguas, contradicciones y oportunidades de mejora justificadas.

**Promesa humana:** «Esto se puede descubrir sobre tu organización y su entorno. Esto se entiende claramente de ti; esto no, según las superficies y condiciones examinadas. Éstas son las evidencias, las posibles razones y, cuando están suficientemente sustentadas, las mejoras que podrías considerar. Volveremos a observar para comprobar qué cambió».

**AXIGNAL no halaga, no castiga y no oculta críticas para producir una experiencia positiva.** La utilidad exige independencia y capacidad de mostrar resultados incómodos, siempre acotados por evidencia, derechos, instrumentos e incertidumbre.

La calidad de producto no se define por cantidad de hallazgos, puntuaciones altas, respuestas persuasivas, número de llamadas al modelo o First Proof barato. Se define por **comprensión económica útil, hallazgos verificables, autocrítica accionable justificada, continuidad temporal y reducción de trabajo humano**.

## 2. Experimento mental fundador: el transeúnte y el escaparate

Un transeúnte pasa a veinte metros de un local. Se le pregunta:

- ¿Percibiste un establecimiento? «Vi luces».
- ¿Sabes cómo se llama? «No».
- ¿Sabes qué ofrece? «No».
- ¿A qué público sirve? «No lo sé».

Su indecisión no es un dato inútil ni se corrige imponiéndole que responda «zapatería». **Es una observación de lo que el escaparate consiguió comunicar a ese observador, desde ese punto y bajo esas condiciones**.

Pero tampoco significa automáticamente que el escaparate esté mal diseñado: quizá hubo poca exposición, obstáculos, poca atención, diferencias de capacidad perceptiva o un error de medición. AXIGNAL debe diferenciar hipótesis y verificar antes de atribuir causas.

Traducción digital: un evaluador estructurado como JEV recibe una representación pública acotada y preguntas tipadas. Sus elecciones, distribuciones, abstenciones y ambigüedades describen **cómo ese instrumento interpretó ese estado**. Pueden revelar que una capacidad no se comunicó suficientemente **bajo las condiciones medidas**; no son la opinión estadísticamente representativa de la población ni el comportamiento demostrado de Google o ChatGPT.

Si la información es inequívoca, AXIGNAL reconoce una fortaleza. Si hay ambigüedad, no la borra: investiga si falta comunicación, si falta observación o si falla el instrumento. Si identifica una mejora plausible sustentada, la muestra. Si no puede resolver la causa, la presenta como `UNKNOWN` e informa qué prueba faltaría.

## 3. Los dos resultados de producto que deben convivir

| Pregunta del suscriptor/agencia | Resultado esperado |
| --- | --- |
| ¿Qué sabemos de esta organización? | Estado económico temporal: hechos admitidos, observaciones, hipótesis, relaciones, evidencias y límites. |
| ¿Qué sucede en su entorno? | Cambios, actores relevantes, demanda, competidores, mercados y oportunidades `POTENTIAL`. |
| ¿Cómo aparece representada públicamente? | Lectura por familia, superficie, idioma, mercado, fecha, muestra, instrumento y fuente. |
| ¿Qué puede comprender un observador externo? | Juicios tipados versionados, desacuerdos, distribución/confianza solo cuando correspondan, abstenciones y límites. |
| ¿Qué se comunica bien? | Fortalezas observadas que puedan demostrarse, sin convertirlas en elogios genéricos. |
| ¿Qué no se comunica, se confunde o contradice? | Hallazgos negativos o ambiguos visibles, trazables y proporcionados a la cobertura real. |
| ¿Por qué aparece la discrepancia? | Investigación de causas alternativas, con diferencia entre dato observado, hipótesis y causa demostrada. |
| ¿Qué podría mejorar? | Acciones sugeridas, específicas, proporcionadas, explicables y explícitamente no causales cuando no existe prueba de impacto. |
| ¿Cambió algo tras una mejora? | Comparación de observaciones compatibles, conservando versiones, series discontinuas e incertidumbre. |
| ¿Qué gano conectando un modelo frontera por MCP? | Acceso autorizado a la historia, las evidencias, las percepciones y la evolución, sin reconstruir toda la investigación. |

No se exige que cada resultado exista en toda empresa ni que toda familia devuelva una recomendación. **No encontrar un problema real también es un resultado legítimo**. Un resultado `NOT_MEASURED`, `NON_INFORMATIVE` o `UNKNOWN` no se transforma silenciosamente en un fallo de la empresa.

## 4. Semántica obligatoria: diez conceptos que no deben mezclarse

1. **Observación:** qué mostró efectivamente una fuente, dónde, cuándo, con qué derechos, cobertura e instrumento.
2. **Conocimiento canónico:** solo material admitido mediante las autoridades y fronteras de AXIGLAND. `CLAIM ≠ WRITE`.
3. **Representación pública:** lo que una organización declara o una superficie muestra; no es por sí solo realidad económica.
4. **Interpretación del evaluador:** respuesta no autoritativa sobre un estado y una pregunta con versión; no es `FAXT`.
5. **Distribución / confidence de JEV:** semántica del proveedor, cuando exista; ni verdad, ni una nota universal de empresa, ni necesariamente una probabilidad calibrada para este uso.
6. **Cobertura de observación:** lo efectivamente examinado; no es toda Internet ni todos los clientes potenciales.
7. **Brecha de representación:** derivación explicable y contextual; una ausencia de evidencia fuera del alcance no demuestra ausencia del hecho.
8. **Diagnóstico causal:** hipótesis investigada sobre por qué una interpretación fue limitada; requiere evidencia diferenciadora y puede continuar `UNRESOLVED`.
9. **Mejora sugerida:** propuesta al humano, no orden, atribución de culpa, garantía de ranking ni workflow de ejecución.
10. **Cambio de percepción:** comparación válida solo entre instrumentos y muestras compatibles, con versión, condiciones, tiempo y posibilidad de discontinuidad.

Reglas: `OBSERVED ≠ POTENTIAL`, `UNKNOWN ≠ FALSE`, `FAXT ≠ INXIGHT`, `RELATIONSHIP ≠ PATHX`, `MODEL_OUTPUT ≠ EVIDENCE`, `SIMILARITY ≠ FIT`, `JEV_PROBABILITY ≠ BASIS`, `SURFACE_REPRESENTATION ≠ ECONOMIC_REALITY`, `RECOMMENDATION ≠ CAUSAL_PROOF`.

## 5. Diagnóstico de incertidumbre: nunca culpabilizar por defecto

Toda indecisión material de un evaluador exige distinguir, cuando sea posible:

| Origen plausible | Ejemplo | Responsabilidad del motor | Mensaje legítimo |
| --- | --- | --- | --- |
| **Representación insuficiente** | La web no explica las líneas de servicio en las páginas examinadas. | Comprobar la cobertura y buscar evidencia corroboradora/contradictoria. | «En estas fuentes no se distingue la oferta; convendría explicitarla si se desea comunicarla». |
| **Observación insuficiente** | AXIGNAL solo leyó la home y omitió una página esencial. | Reorientar adquisición y completar fuentes elegibles. | «Nuestra observación aún no permite juzgarlo»; no atribuirlo al cliente. |
| **Evaluador insuficiente** | El texto contiene la respuesta pero JEV eligió una opción errónea. | Revisar contrato, pregunta, contexto, versiones y referencia independiente. | «La evaluación no es concluyente»; no recomendar cambiar una comunicación correcta. |
| **Superficie externa distinta** | Una API generativa y una interfaz de producto muestran resultados diferentes. | Mantener instrumentos separados y evitar extrapolación. | «Observamos resultados distintos en estas superficies»; no «todo GEO está mal». |
| **Información pública contradictoria** | Dos fuentes identifican servicios diferentes. | Preservar contradicción, fechas y procedencia; investigar actualidad. | «Estas fuentes discrepan»; no inventar un vencedor. |
| **Alcance público deliberadamente limitado** | Negocio por recomendación personal o con servicios no anunciados. | Describir la limitación de legibilidad pública sin juicio global de estrategia. | «Si la captación pública es un objetivo, esta información podría ayudar». |

**La incertidumbre es un disparador de investigación o una medición perceptiva informativa; no una sentencia automática de que el suscriptor «lo hace mal».** La autocrítica debe ser independiente y contundente cuando haya evidencias, pero jamás fabricada.

## 6. Familias de observación: rigor propio, no «un LLM para todo»

AXIGNAL necesita un sustrato común y una **disciplina especializada por familia**. Cada familia declara preguntas, fuentes legítimas, instrumento, semántica de medición, cobertura, dimensiones perceptivas, reglas de suficiencia, límites, investigación y cadencia de reobservación. El siguiente mapa expresa resultados, **no** exige implementar de golpe todos los proveedores o sensores.

### 6.1 Identidad, oferta y capacidad económica

- **Observar:** identidad pública y registral separadas; páginas de productos/servicios, especialidades, destinatarios, casos y alcance declarado; terceros pertinentes si el acceso está autorizado.
- **Preguntar a evaluadores:** ¿qué actividad interpretan?, ¿qué líneas de oferta diferencian?, ¿quién parece ser el comprador?, ¿qué capacidad es concreta y cuál genérica?, ¿qué permanece fuera de la evidencia?
- **Autocrítica posible:** oferta comprensible solo parcialmente, servicios indistinguibles, incoherencia entre páginas, promesa no sustentada, falta de alcance declarado.
- **Acción posible:** mejorar descripciones específicas o explicitar destinatarios y casos **si la organización quiere comunicar públicamente esos hechos y puede sustentarlos**.
- **Límite:** una ausencia de declaración no prueba ausencia de capacidad real; el input del suscriptor no se admite como `FAXT`.

### 6.2 SEO / Search Representation

- **Observar:** rastreabilidad e indexabilidad de páginas medidas, estructura y contenido pertinentes, resultados de consulta en motores/superficies elegibles y, cuando estén conectados, datos privados autorizados de Search Console.
- **Preguntar:** ¿aparece la organización para consultas relevantes en un idioma/mercado concreto?, ¿se presenta el servicio?, ¿qué ve un buscador en la muestra?, ¿qué problema técnico medido o brecha textual hay?
- **Autocrítica posible:** `noindex` observado, metadatos ausentes, oferta no expresada en páginas muestreadas, ausencia **medida** para una consulta concreta.
- **Acción posible:** revisar una configuración específica, completar información específica, contrastar una hipótesis con GSC/otra observación.
- **Límite:** JEV no es Google; claridad para un evaluador no es ranking real; GSC privada no pasa a memoria pública compartida.

### 6.3 GEO / Generative Representation

- **Observar:** respuestas **efectivamente producidas** por productos o APIs identificados; prompts/preguntas congelados, modo de grounding, idioma, mercado, versión, muestra, réplica, menciones y citas.
- **Preguntar:** ¿cómo describe la organización esta superficie?, ¿qué oferta menciona u omite?, ¿la cita está presente?, ¿la interpretación varía entre ejecuciones?, ¿hay errores repetibles?
- **Autocrítica posible:** ambigüedad demostrada en la respuesta observada, falta de cobertura para preguntas muestreadas o divergencia entre fuentes públicas y descripción generativa.
- **Acción posible:** clarificar información verificable en fuentes apropiadas, proponer nueva medición; **nunca** garantizar inclusión, ranking o cita de un modelo externo.
- **Límite:** una llamada API no representa por defecto la experiencia en UI comercial; instrumento distinto implica resultado distinto.

### 6.4 Comunicación, marketing y posicionamiento

- **Observar:** narrativa pública, diferenciación, consistencia entre canales accesibles, promesas, pruebas publicadas, especialización, destinatarios, casos, propuesta de valor.
- **Preguntar:** ¿qué entiende un observador acerca de la oferta y su diferencia?, ¿qué claims son vagos?, ¿se reconocen claramente los buyer jobs?, ¿hay contradicciones?
- **Autocrítica posible:** mensajes genéricos, propuestas imposibles de distinguir, casos sin evidencia, lenguajes inconsistentes en las superficies observadas.
- **Acción posible:** proponer una clarificación localizada en página/canal, diferenciando hipótesis de resultado comprobado.
- **Límite:** no inferir rendimiento de campañas o intención de clientes sin instrumentos/datos; no convertirse en gestor de campañas.

### 6.5 UX y experiencia pública accesible

- **Observar:** contenido y flujos públicos medibles, lenguaje, enlaces, acceso a información esencial, responsive y errores bajo dispositivos/condiciones identificados.
- **Preguntar:** ¿puede localizarse qué hace la empresa y cómo acceder a su oferta?, ¿qué bloqueos son reproducibles?, ¿qué confunde al evaluador de contenido?
- **Autocrítica posible:** acción esencial inaccesible, contenido ininteligible, incoherencia en una pantalla observada.
- **Acción posible:** corregir el bloqueo concreto y volver a comprobarlo en navegador.
- **Límite:** inferencia de JEV no demuestra usabilidad humana ni tasas de conversión; observación técnica ≠ estudio de usuarios.

### 6.6 Social, conversación pública y reputación/experiencia

- **Observar:** menciones, debates, reviews, valoraciones nativas, contexto, fechas, sujeto al que se refiere, respuestas de empresa; solo fuentes con derechos autorizados.
- **Preguntar:** ¿qué temas/experiencias reportan los autores?, ¿qué contradicciones y patrones existen?, ¿cuál es la cobertura y denominador?, ¿qué resulta incierto?
- **Autocrítica posible:** un patrón recurrente de quejas por entrega en una muestra identificada; mensajes contradictorios entre fuentes, sin declarar verdad de cada experiencia.
- **Acción posible:** recomendar revisar el aspecto de servicio señalado por la muestra, documentando tamaño, sesgo y límites.
- **Límite:** sentimiento no es hecho; anomalía no es fraude; no promediar plataformas indiscriminadamente; no diagnosticar «mala reputación general» desde una muestra parcial.

### 6.7 Entorno, mercados, relaciones y oportunidades económicas

- **Observar:** capacidades, proyectos, fuentes de demanda, señales de expansión, compras públicas, cambios regulatorios y conexiones públicas autorizadas.
- **Preguntar:** ¿qué oportunidades `POTENTIAL` merecen investigación?, ¿qué capacidad/reach no podemos establecer?, ¿qué actor/mercado sería plausible investigar?
- **Autocrítica posible:** el propio posicionamiento público no permite a terceros identificar una capacidad relevante para una oportunidad, **si** esa discrepancia está demostrada.
- **Acción posible:** investigar oportunidad y límites, mostrar información pública necesaria para comunicar mejor una capacidad legítima.
- **Límite:** ausencia de adjudicaciones no equivale a mala comunicación; demanda agregada no es comprador identificado; una asociación hipotética no es relación comercial real.

**Principio transversal:** cada familia debe mostrar sus resultados favorables y desfavorables **con el mismo estándar de evidencia**, aunque su salida visual, instrumento, decisión y presupuesto sean distintos. Se prioriza profundidad correcta por familia, no una puntuación monolítica ni una plantilla repetida.

## 7. JEV: instrumento de interpretación, no mero filtro

**Intención fundacional recuperada:** JEV puede funcionar como el «transeúnte digital»: un observador específico al que planteamos preguntas acotadas sobre lo que el mundo ha expuesto. El objeto de interés es también **su interpretación**, incluso cuando sea dudosa.

Su uso deseado (según pertinencia real de cada contrato):

- `Choice`: ¿qué interpreta como actividad / oferta / público / propósito? Incluir `UNKNOWN`, `OTHER`, `UNRESOLVED` o abstención donde corresponda; evitar universos cerrados artificialmente.
- `Noul`: presencia/ausencia de una propiedad semántica **en el estado proporcionado**, no existencia real universal.
- `Score`: niveles ordinales definidos por pregunta, con significado discriminante y versión. No inventar una «nota global de SEO» a partir de scorings parciales.
- Distribuciones y confianza: conservar cuando el proveedor las ofrezca legítimamente, junto con etiquetas/opciones originales, modelo/versiones/semántica y reference de replay. No fabricar probabilidades si un adaptador no las proporciona.
- Variación y disenso: cambios del mismo evaluador o entre instrumentos pueden motivar investigación; no equiparar desacuerdo con error de comunicación sin controles.

**Dos criterios de suficiencia independientes:**

1. **Suficiencia de extracción o routing económico:** Python ya identificó actividad, lugar, código u otra dimensión suficiente para una operación técnica.
2. **Suficiencia de observación de comprensión externa:** el instrumento perceptivo previsto fue realmente ejecutado, o existe un juicio idéntico, vigente y reutilizable bajo contrato/estado/modelo equivalentes; de lo contrario, indicar `NOT_MEASURED`, no «comprendido».

Nunca concluir que el segundo criterio está cubierto porque se cumplió el primero. Una heurística determinista puede satisfacer una clasificación sin haber entrevistado al «transeúnte».

**Calidad experimental:** JEV podría ser una opción diferenciada, pero no tiene monopolio de la percepción tipada. Comparar con evaluadores alternativos usando estados, preguntas, versiones y etiquetas independientes iguales, dentro de derechos y gates válidos. No usar resultados de JEV para destilación, calibración o entrenamiento de competidores si lo impiden sus términos; conservar límites del ADR-0090. Un LLM generativo podría responder tipos, pero ni él ni JEV crean verdad por voto o confianza.

**Rol de AXENT/LLM:** descubrir fuentes, investigar ambigüedades, formular hipótesis, investigar causas, contextualizar resultados y explicar con lenguaje comprensible. **No** sustituir las mediciones por una redacción plausible; no redactar `Explainable Basis` a posteriori. Python gobierna autorización, determinismo, identidad, currentness, trazas, políticas y `EvidenceAdmission`.

## 8. Ciclo de valor bidireccional: independiente de una implementación concreta

```text
FOCO DE OBSERVACIÓN / ATENCIÓN
    |
    +--> MUNDO: fuentes, cambios, necesidades, relaciones, demandas, mercados
    |
    +--> REPRESENTACIÓN: web, búsqueda, respuestas generativas,
         conversación, reputación, experiencia pública
    |
OBSERVACIONES ELEGIBLES + PROVENANCE + TIEMPO + DERECHOS
    |
COMPILAR ESTADOS / REUTILIZAR MEMORIA / MEDIR COBERTURA
    |
EVALUACIONES TIPADAS POR DIMENSIÓN E INSTRUMENTO (JEV u otros)
    |
INTERPRETACIÓN GOBERNADA: fortalezas, brechas, contradicciones,
                          incertidumbre, oportunidades potenciales
    |
INVESTIGACIÓN DIRIGIDA SI LA CAUSA / COBERTURA ESTÁ INDETERMINADA
    |
OUTPUT HUMANO: ¿qué se entiende?, ¿qué no?, ¿por qué?,
               ¿qué se puede mejorar?, ¿qué valor hay fuera?
    |
HUMANO ACTÚA O NO ACTÚA (AXIGNAL NO ES SU WORKFLOW)
    |
REOBSERVAR --> COMPARAR SERIES COMPATIBLES --> APRENDER / PRESERVAR HISTORIA
```

Este esquema expresa un ciclo cognitivo, **no** una cadena de herramientas obligatoria. Reutilizar primero datos públicos autorizados y juicios existentes es correcto; dejar de investigar **por mera minimización de tokens** cuando puede cambiar el valor de la información no lo es.

El bucle debe tener límites de investigación, cadencia, derecho de acceso, presupuestos, idempotencia, estados explícitos, backoff y salidas `UNKNOWN`. No crear bucles infinitos ni prometer investigación autónoma ilimitada.

El juicio de JEV debe poder sobrevivir como **observación de percepción condicionada**, con estado/instrumento/tiempo/versiones, sin promoverse a `FAXT`. El sistema debe preservar observaciones no admisibles para conocimiento canónico según el contrato de memoria de observación y sus derechos. Un cambio posterior no borra el estado anterior.

## 9. Human First: la autocrítica es un output de primera clase

Cada observación material debe poder presentar, cuando exista evidencia:

1. **Qué hace bien:** interpretación clara, presencia identificada, declaraciones coherentes u otra fortaleza realmente medida.
2. **Qué está fallando o qué no se comprende:** formulación crítica específica y fiel a la cobertura («en X no se encontró Y»), no un juicio sobre la empresa completa.
3. **Por qué AXIGNAL lo afirma:** instrumento, consulta/prompt, fuente, URL permitida, excerpt/ref, fecha, estado, comparabilidad y límites.
4. **Qué explicación es plausible:** causa apoyada o alternativas que siguen `UNKNOWN`.
5. **Qué acción podría emprender el suscriptor:** intervención concreta, proporcional y condicionada; no una garantía.
6. **Qué observar después:** medición futura capaz de comprobar si cambió la comunicación/interpretación, separada de resultados comerciales.

**Nunca ocultar una crítica útil** detrás de un código técnico, un panel secundario invisible o un mensaje genérico «no hay datos». Tampoco rellenar una pantalla vacía con recomendaciones especulativas. Hallazgos positivos y negativos conviven; no hay cuota artificial de críticos.

Para una agencia, el producto permite:

- reconocer el problema exacto en el contexto de un cliente y explicar qué evidencia lo revela;
- priorizar atención por impacto potencial justificado, incertidumbre, magnitud/cobertura y esfuerzo de investigación; no fingir una métrica universal;
- demostrar progreso mediante series comparables y fuentes externas, sin atribuir resultados de negocio no medidos;
- navegar cartera con aislamiento estricto `tenant → client_context → Xeed`, sin transferir información privada entre clientes.

**Gramática HFX:** `GLANCE → UNDERSTAND → REASON → PROVE`. Acceso directo a evidencia y evolución desde el mismo hallazgo; «Show me how AXIGNAL knows» usa la base persistida exacta, no razonamiento post-hoc. Vistas de producto `Today / Explore / Evolution / Evidence / Ask AXENT` cuando correspondan. Enlaces externos verificados en nueva pestaña con protecciones de seguridad; móviles, accesibilidad, idiomas y estados fallidos reales. Lenguaje humano antes que «Noul», «Choice», «JEV» o nombres internos.

**Ejemplo de copy honesto (hipotético):**

> «En las dos páginas examinadas se reconoce el nombre de la empresa y su sector, pero no se distinguen tres servicios que aparecen agrupados bajo “soluciones integrales”. El evaluador no puede separar sus prestaciones a partir de estos textos. No hemos verificado otras páginas ni podemos atribuir una causa de pérdida de tráfico. Si esos servicios son importantes para su captación pública, convendría describirlos individualmente; repetiremos esta evaluación con el mismo instrumento».

Lo contrario («SEO deficiente: 37/100; mejore su web») **no es** un resultado aceptable sin metodología específica y justificada.

## 10. Primera prueba, primer valor y continuidad

`FIRST_PROOF_READY` es un estado de adquisición / observación **limitado**, no prueba de que la organización se haya comprendido ni de que la experiencia bidireccional esté cerrada.

Tres condiciones no son intercambiables:

- **First Proof:** AXIGNAL observó algo y puede citar una fuente, o detectó un `UNKNOWN` fundado.
- **First Economic Understanding:** posee una interpretación económica suficientemente fundada para mostrar significado y límites.
- **First Constructive Insight:** puede mostrar una fortaleza o una crítica de representación **realmente evidenciada**, con siguiente investigación o mejora condicionada cuando proceda.

La UX debe representar honestamente cuál se ha alcanzado. FIRST_MAP_WOW no debe ser un efecto visual que oculte un juicio insuficiente. Una empresa de presencia mínima puede generar una experiencia valiosa si AXIGNAL demuestra de forma convincente qué información examinó, qué no permite interpretar y qué sería razonable aclarar. Una empresa muy bien comunicada puede no necesitar recomendaciones negativas; su resultado positivo es legítimo.

El progreso se mide con continuidad: una captura puntual no es seguimiento; una recomendación no es mejora probada; una mejora en claridad del instrumento no implica ventas ni ranking.

## 11. MCP y la defensa del moat: inteligencia que otro modelo puede aprovechar

AXIGNAL no debe competir por «ser un modelo más inteligente». El modelo frontera conectado a AXIGNAL debe poder razonar **sobre una memoria de observación/percepción que no tendría sin AXIGNAL**, dentro del aislamiento, derechos y evidencia apropiados.

Un futuro consumidor MCP autorizado debe poder preguntar conceptualmente:

- «¿Qué entendía el evaluador sobre esta organización hace seis meses y qué entiende ahora?».
- «¿Qué ambigüedad era observable, con qué preguntas/versión y fuentes, y qué cambió después?».
- «¿Qué evidencia sostiene una oportunidad potencial y qué parte no está comprobada?».
- «¿Qué mejoras de comunicación se sugirieron y qué mediciones posteriores permiten o impiden valorar su efecto?».
- «¿Dónde divergen la realidad económica admitida, la declaración propia y la representación por buscadores, agentes o conversación pública?».

No exponer SQL arbitrario, secretos, datos privados, documentos sin derechos ni capacidad de escritura canónica a un agente MCP. Un modelo conectado recibe contextos mínimos autorizados, observaciones/evidencias permitidas y explicaciones reconstruibles. Un MCP sin memoria útil y sin continuidad **no es moat**.

Hipótesis competitiva que hay que validar: mismo modelo/presupuesto con (A) investigación sin memoria, (B) memoria propia competente, (C) AXIGNAL vía MCP, (D) AXIGNAL completo. Comparar utilidad y coste, en especial en visitas recurrentes. No presentar como ventaja probada antes de esa prueba.

## 12. Economía de inteligencia y orquestación

- **Objetivo económico:** maximizar hallazgos económicos y perceptivos **materiales, verificables y reutilizables** por euro y por Focus, no minimizar indiscriminadamente llamadas LLM/JEV.
- **Reutilizar:** datos públicos con derechos y sujeto válidos, lectura web, resultados de fuentes y evaluaciones idénticas según fingerprints, versiones y currentness. Nuevo contexto o cambio material puede requerir reevaluación.
- **Asignar capacidades:** Python para mecanismos deterministas; JEV u otro evaluador especializado para preguntas tipadas; AXENT/modelos generativos para investigación adaptativa, hipótesis y explicación; ningún proveedor tiene autoridad canónica.
- **Presupuestar:** por resultado, familia, incertidumbre y valor esperado, sin bucles ilimitados ni supresión arbitraria de investigación valiosa.
- **Registrar:** coste real/estimado/desconocido, latencia, adquisición, herramientas, tokens, repetición evitada, decisiones de investigación, derivaciones y reutilización entre Foci.
- **Precio:** el MASTER vigente manda; este goal **no cambia 9,95 € base ni 4,95 € por Focus adicional**, no decide un tier de 19,95 € y no supone que el ahorro de tokens sea un objetivo del cliente.

Una optimización que reduce gasto pero empeora descubrimiento, crítica constructiva o calidad perceptiva se considera regresión **salvo evidencia contraria de valor**.

## 13. Escenarios obligatorios de aceptación de producto

Estas pruebas son **historias de resultado**, no scripts obligatorios ni contratos de campos. El agente elegirá fixtures, fuentes autorizadas, instrumentos y validación independiente adecuados.

| Caso | Entrada/contraste | Lo que debe demostrar AXIGNAL |
| --- | --- | --- |
| **A. Comunicación clara** | Empresa con servicios y público descritos explícitamente y corroboración accesible. | Interpretación competente, fortalezas observadas, referencias exactas; no inventar crítica para llenar una sección. |
| **B. Escaparate de Manolo** | Presencia pública mínima: «Hola, soy Manolo, zapatero». | Interpretación limitada, alternativas plausibles, alcance explícito, posibles mejoras condicionales; no inventar reparaciones, venta, ubicación ni ausencia universal en Internet. |
| **C. Clasificador suficiente; percepción insuficiente** | Lexicon/schema permiten detectar el sector, pero no se distinguen productos, buyer jobs ni especializaciones. | No marcar comprensión perceptiva completa ni suprimir un instrumento requerido por éxito de clasificación. |
| **D. Fallo de observación** | Existe información pública suficiente, pero el primer sensor no la encontró. | Reinvestigar/admitir cobertura insuficiente; no culpar a la empresa ni presentar déficit de comunicación falso. |
| **E. Error del evaluador** | Estado realmente informativo; JEV falla, otro evaluador / revisión independiente detecta el error. | Preservar juicio y error, no alterar verdad, no recomendar cambiar una comunicación válida; la mejora corresponde al instrumento/contrato. |
| **F. Contradicciones** | Oferta distinta en web, directorio autorizado y fuente antigua. | Exponer discrepancias y fechas; investigar currentness; no promediar certeza ni borrar observaciones históricas. |
| **G. SEO comprobado** | `noindex` observable en URL concreta y datos GSC privados autorizados opcionales. | Informar condición y alcance, justificar revisión; no traducirla sin prueba a pérdidas de tráfico o ranking. |
| **H. GEO realmente medido** | Dos ejecuciones comparables en una superficie autorizada, una con error u omisión. | Distinguir respuesta observada, versión, muestra, modo y citas; no declarar que «todas las IAs» conocen/desconocen la empresa. |
| **I. Reputación con muestra insuficiente** | Una queja aislada y varias menciones ambiguas. | Conservar testimonio y sesgo, sin inventar patrón, fraude, mala empresa o resultado estadístico. |
| **J. Antes y después** | Cambio público comprobado en la comunicación de un servicio. | Nueva observación, interpretación con instrumento comparable, diferencia explicada, límites de causalidad; si hay drift, serie discontinua. |
| **K. Negativo no oculto** | Un problema adverso medido junto a resultados favorables. | Mostrarlo de forma prominente y constructiva, con evidencia y recomendación cuando procede, sin relegarlo a logs. |
| **L. Sin información suficiente y sin culpa** | Fuente bloqueada por robots, caída de sitio o derechos desconocidos. | `UNKNOWN/UNAVAILABLE`, abstención y posible investigación elegible; jamás «la empresa no tiene presencia». |
| **M. Agencia con varios clientes** | Clientes y fuentes públicas reutilizables; elementos privados distintos. | Reutilización legítima, isolation tenant/client, vistas útiles por cliente, ninguna fuga entre clientes. |
| **N. MCP / cambio de modelo** | Mismo historial bajo diferentes proveedores cognitivos. | El modelo puede navegar bases/evidencias permitidas con continuidad y límites; sustitución de proveedor no reescribe AXIGLAND. |

**Criterio de falsación:** si AXIGNAL «entiende bien» una empresa solo porque extrajo un código ISIC, si un `UNCLEAR` desaparece sin explicación, si un déficit de adquisición se presenta como mala comunicación o si no puede mostrar una crítica relevante bien respaldada, **el objetivo bidireccional no está satisfecho**.

## 14. Evaluación de calidad: no confundir tests verdes con producto útil

La evaluación debe separar **mecánica implementada**, **calidad de instrumento**, **utilidad humana**, **valor económico** y **operación real**.

- **Calidad:** precisión/recall por pregunta cuando exista referencia independiente; errores de clase graves; falsa atribución de `OBSERVED`; tasa de abstención apropiada; falsos diagnósticos de «mala comunicación»; pérdida de hallazgos negativos.
- **Percepción:** claridad/ambigüedad por instrumento y dimensión; coherencia bajo estados equivalentes; continuidad entre versiones; distribución y confianza **solo si están disponibles y válidas**; no calibrar con intuiciones ni sobre scores inexistentes.
- **Adquisición:** cobertura por fuente y familia, first-loss attribution (`OBSERVATION_MISS`, `STATE_INSUFFICIENT`, `EVALUATOR_MISCLASSIFICATION`, etc.), derechos, temporalidad y citabilidad.
- **Autocrítica:** proporción de hallazgos negativos relevantes mostrados; evidencia accesible; corrección de la causa atribuida; utilidad y viabilidad de la recomendación; tasa de críticas falsas. No imponer una cuota de hallazgos desfavorables.
- **Experiencia:** tiempo hasta primer hallazgo significativo, comprensión de mensaje por usuario/agencia, facilidad de inspección y prueba, utilidad real de las acciones sugeridas.
- **Economía:** coste completo por hallazgo útil, coste incremental por Focus, amortización pública, fuentes/herramientas/modelos, tiempo de respuesta y margen bajo escenarios realistas.
- **E2E:** login/tenant, Focus, primera observación, reobservación, persistencia, navegación, evidencias enlazadas, estados degradados, responsive y acceso externo de producción tras despliegue autorizado.

No tomar corpus sintético, simulador de JEV, CI verde o una prueba HTTP como evidencia de calidad semántica en clientes reales. Separar desarrollo/calibración de evaluación sellada, respetando derechos de uso y corpus; **sin una referencia independiente válida, informar «NO DEMOSTRADO»**.

## 15. Baseline de implementación observado antes de este brief (NO es el cierre futuro)

**Inspección realizada en el worktree** `D:\AXIGNAL\.worktrees\first-observation` / `feat/first-observation-loop` el 2026-10-09. El estado puede cambiar mientras Opus sigue trabajando. Reconstruir la realidad vigente al activar.

| Componente | Evidencia concreta observada | Lectura de fidelidad |
| --- | --- | --- |
| First Observation | `application/first_observation/service.py`, `activity.py`, `contracts.py` | Adquisición, hipótesis de actividad, primeras pruebas y algunos checks web presentes. |
| Juicio tipado JEV | `application/semantic_layer/contracts.py`, `cascade.py`, `cognition/providers/typesafe_system_one.py` | Infraestructura adecuada para evaluaciones condicionadas, bajo límites de coste y provider. |
| Preguntas actuales | `plan_activity_batch()`: sector ISIC/CPV/NAICS, compradores, modo de entrega, sitio operativo, ubicación | **Clasificación económica ≠ medición de comprensión externa**. |
| Atajo determinista | `plan_activity_batch()` retorna `None` si no hay preguntas relevantes de routing; test explícito sin llamada a JEV | Válido para routing; no permite afirmar que se midió legibilidad/percepción. |
| Lectura web | `_web_representation()`: robots, sitemaps, canonical, noindex, título, schema, etc. | Checks técnicos útiles, no entrevista completa al «transeúnte». |
| Memoria de juicios | `pipeline/semantic_layer/sqlite_memory.py` conserva selected/distribution/confidence y fecha | Existe mecanismo de replay; **no está demostrado** un producto longitudinal perceptivo completo. |
| UX | `apps/web/experience/components/first-observation.tsx` y `subscriber-representation.tsx` | Evidencia y brechas técnicas visibles; no se ha verificado loop completo de autocrítica constructiva. |
| Familias | `specs/063-first-observation-loop/family-architecture.md` (borrador en worktree activo) | La propia matriz declara Search/Generative/Social/Reputation incompletas o diseñadas. |
| Estado en producción | Spec 063 declara activación independiente y off por defecto | No afirmar despliegue E2E de este nuevo objetivo. |

Una ejecución anterior de `tests/first_observation/test_first_observation_e2e.py` durante cambios activos obtuvo **14 passed, 1 failed**, con discrepancia entre retry inmediato esperado y backoff en modificación. Es una fotografía temporal del worktree, **no** certifica estado final ni prueba un defecto permanente. Opus debe cerrar o justificar la discrepancia sin modificar un gate para simular éxito.

## 16. Instrucción de orquestación para la futura ejecución

**Ahora NO ejecutar este goal:** Opus está cerrando First Observation y sus correcciones adversariales. No interferir en su rama, no tocar archivos dirty, no cambiar el MASTER, no modificar producción, no abrir procesos concurrentes sobre su worktree.

**Al activarse con orden CTO:**

1. Revisar estado real Git/local/worktrees, versión de MASTER, Constitution, ADRs, specs, gates, implementaciones y pruebas; reutilizar lo ya integrado, no replicar auditorías sin necesidad.
2. Presentar una **matriz de fidelidad**: resultado deseado → contrato doctrinal → código → test → UX → producción. Marcar `IMPLEMENTADO / PROBADO / INTEGRADO / DESPLEGADO / VERIFICADO E2E` por separado.
3. Determinar el **gap mínimo decisivo** que impide demostrar autocrítica constructiva real y la interpretación externa. Elegir vertical con fuentes/uso legales y evidencia representativa; no paralizarse por no poder implementar de inicio todas las superficies.
4. Construir o reparar una experiencia bidireccional **real**, no un informe o un stub que simule evidencia. Conservar juicio tipado, observación, incertidumbre, causa investigada, output accionable, reobservación y procedencia.
5. Probar contra los casos de §13, incluidos adversariales, y medición de calidad con etiquetas independientes donde aplique. Investigar y corregir regresiones.
6. Verificar en navegador la UX real (positivo y autocrítica negativa); comprobar persistencia, permisos, fuentes, costes, localización y estados de error.
7. Integrar y desplegar **solo conforme a autorización, gates y protocolo de producción**; preservar rollback y aislamiento de otros proyectos. Verificar E2E externamente antes de declararlo DONE.
8. Entregar evidencia de valor que permita decidir si ampliar a otras familias/instrumentos o ajustar la economía del producto.

**Autonomía del agente frontera:** este documento fija intención, fronteras y pruebas de resultado, **no** prescribe clases, tablas, endpoints, microservicios ni número de llamadas a JEV/Luna. El responsable investiga, decide y ejecuta la solución mínima suficiente, pudiendo justificar una solución distinta o una dependencia no prevista. Escala solo conflictos doctrinales, costes/riesgos materiales, cambios irreversibles, seguridad o política de despliegue. No pedir autorización por decisiones técnicas reversibles de bajo riesgo.

## 17. Definición de DONE del goal

Este objetivo se considera logrado únicamente cuando:

- Una organización real o una evaluación con fuentes reales autorizadas muestra **ambas direcciones** de inteligencia.
- Una **fortaleza** real, una **crítica** real y una **incertidumbre** real pueden llegar al suscriptor con su fuente/fecha/instrumento, sin fabricar casos positivos o negativos.
- La crítica adversa no se oculta ni se suaviza hasta volverse inútil; tampoco imputa un fallo de empresa por defecto.
- El resultado distingue adquisición insuficiente, representación insuficiente e interpretación insuficiente; si no es posible distinguirlas, admite esa limitación.
- Las propuestas de mejora están condicionadas por evidencia y permiten reobservación; comparaciones incompatibles se rechazan explícitamente.
- JEV, cuando sea usado, es un proveedor especializado cuya salida y semántica son inspeccionables y cuya sustitución no altera las reglas de verdad.
- La evidencia, memoria temporal, derechos, aislamiento, currentness y `EvidenceAdmission` siguen intactos.
- La calidad de los casos críticos supera evaluación independiente suficiente; los casos no medidos siguen identificados como tales.
- Implementación, validación, integración, despliegue y E2E se informan honestamente por separado.
- Una agencia puede explicar una mejora sugerida a un cliente y **mostrar por qué AXIGNAL la propuso**, sin necesitar conocer los mecanismos internos.

Un documento completo, un prototipo, un set de tests verdes, una demo sintética o una investigación generada por LLM **no sustituyen** esta evidencia.

## 18. Orden corta para activar posteriormente

**NO EJECUTAR HASTA QUE EL CTO LO ORDENE DESPUÉS DEL CIERRE DE SPEC 063.**

Cuando corresponda, el CTO puede enviar a Opus este texto exacto:

> Claude Opus 5.5: Primera Observación ya ha cerrado. Lee completo `docs/product/AXIGNAL_BIDIRECTIONAL_INTELLIGENCE_EXECUTION_GOAL_2026-10-09.md` desde el último `origin/main` y contrástalo con MASTER, Constitution, ADRs, specs y código actual. Asume la responsabilidad E2E de conseguir el resultado bidireccional y de autocrítica constructiva evidenciada aquí definido, reutilizando cuanto ya existe. Tienes autonomía técnica de agente frontera dentro de la autoridad vigente. No sustituyas implementación por más documentos ni inventes métricas, hallazgos o tests. Entrega la matriz de fidelidad, ejecuta el mínimo conjunto de cambios necesario, prueba, integra y solicita la autorización de despliegue cuando proceda. Demuestra comportamiento real y declara los límites aún abiertos.

---

**Síntesis ejecutiva:** el valor de AXIGNAL no consiste solo en decir «qué sé de ti» o «qué oportunidades veo fuera». Consiste también en decir **«qué se puede comprender de ti, qué estás comunicando bien, qué no llega a comprenderse, qué evidencia lo demuestra y qué podrías mejorar»**. La crítica constructiva evidenciada es una capacidad central, no una falta del motor ni un complemento de marketing.
