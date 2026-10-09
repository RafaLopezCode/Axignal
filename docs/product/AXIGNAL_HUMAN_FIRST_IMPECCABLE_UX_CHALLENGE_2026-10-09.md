# AXIGNAL — HUMAN FIRST EXPERIENCE · OPEN DESIGN CHALLENGE

**Responsable:** Claude Opus 5.5 — Frontier Product Design / UX Engineering
**Herramienta especializada:** Impeccable `C:\Users\usuario\.claude\skills\impeccable\SKILL.md`
**Estado:** objetivo preparado para ejecutar, no implementado.
**Base:** PR #175 integrado en main (`987ca91`). Worktree exclusivo de esta rama.

## La ambición

Diseña y construye una experiencia AXIGNAL tan inteligible, intuitiva, fluida y distintiva que el suscriptor descubra la inteligencia económica sin tener que comprender la complejidad del motor.

El usuario debe percibir, explorar y aprovechar **qué observa AXIGNAL; qué merece atención; qué ha cambiado; qué no consigue comprender; qué se comunica bien; qué podría mejorarse; por qué; y qué fuentes lo sustentan**. La crítica constructiva y la incertidumbre explicada son valor de producto, no notas al pie.

**Sí quiero el mejor dashboard o workspace del suscriptor que podamos imaginar:** un lugar donde apetezca entrar, orientarse, investigar y descubrir. No impongo el dashboard convencional de cuadrículas, un dossier, un grafo, un chatbot ni ningún otro formato concreto. **Elige o inventa la mejor gramática de interfaz para AXIGNAL**. Puedes combinar paradigmas, crear interacciones originales y cuestionar decisiones visuales anteriores. No quiero limitar tu creación a embellecer pantallas.

La complejidad del motor debe transformarse en inteligencia humana accionable sin carga cognitiva, ni pérdida de rigor.

## Ambición estética y emocional: profesional, sorprendente y divertida

**La belleza, el disfrute y el factor WOW son requisitos de producto, no extras decorativos.** AXIGNAL debe emocionar por su elegancia visual y dar ganas de explorarlo. Buscamos un dashboard vivo, profesional, distintivo y memorable; una herramienta de trabajo que provoque curiosidad, placer y descubrimiento. No basta con que sea clara, correcta y usable si resulta fría, plana, gris, estática o aburrida.

Tienes libertad creativa para emplear a fondo el potencial de la marca: **colores de la paleta AXIGNAL, tipografías, luces y contrastes, composición editorial, mapas y grafos cuando procedan, profundidad, capas, iconografía, microinteracciones, movimiento, transiciones y animaciones cinematográficas sutiles o expresivas**, siempre que su combinación mejore el carácter y la experiencia. No presupongas que menos movimiento, menos color o más austeridad constituyen mejor UX.

Explora y ejecuta, según tu criterio, cambios de vista con continuidad espacial, reordenación animada de cards, aparición de hallazgos, revelación gradual de evidencia, relaciones que se despliegan, timelines vivos, feedback al seleccionar organizaciones, estados de investigación, transiciones de enfoque y microinteracciones que recompensen una exploración. **Puedes inventar interacciones nuevas** si resultan naturales y atractivas. Estos son ejemplos inspiradores, no una checklist ni una solución prescrita.

**El movimiento puede informar y también deleitar.** El color puede codificar significado y también aportar emoción, ritmo y personalidad. Una interacción bella no necesita defenderse únicamente por reducción de clics: la satisfacción de uso, la calidad percibida y la curiosidad sostenida también cuentan. Evita solo el espectáculo que oscurezca significado, falsee estados, ralentice tareas o dificulte el uso continuado.

Aplica Impeccable para explorar direcciones visuales e interactivas realmente diferentes. Busca una dirección artística reconocible de AXIGNAL: **WOW de alta gama, no efectos de plantilla SaaS, ni infantilización, ni decoración arbitraria**. Cuida ritmos, easing, timing, escalas tipográficas, jerarquía del color, coherencia de transición y acabado fino hasta el nivel de detalle.

Garantiza que el movimiento sea opcional para quien solicita reducción de animaciones; conserva contraste, accesibilidad, rendimiento, legibilidad, control del usuario y respeto por batería/dispositivos. El mismo producto debe ser disfrutable con y sin animaciones. Ajusta el despliegue visual a las capacidades de cada dispositivo, sin crear otra UX distinta.

**La aceptación visual incluirá una pregunta explícita: «¿Es un dashboard en el que apetece estar, explorar y volver mañana, además de comprender mejor el negocio?»**. Demuestra esa cualidad con navegación real, transiciones funcionando y capturas o vídeo, no con descripciones de intenciones.

## Punto de partida constatado, NO un mandato de preservación

Hoy conviven experiencias distintas:

- `/panorama`: ejemplo de producto con sidebar de organizaciones/familias, Today/Panorama, navegación contextual, evidencia y AXENT. Su composición es rica, pero utiliza datos de ejemplo y no demuestra el flujo real del suscriptor.
- `/account`: suscriptor autenticado en `PublicShell`, cartera y lectura extensa bajo un header público. Primera Observación y spec 064 llegan ahí como paneles/dossier; AXENT aparece como un `details` contextual y no hay un workspace unificado equivalente al ejemplo.
- `customer-zero.tsx`: RuntimeExperience operativo con composición y posible shell embebido.
- `subscriber-reading.tsx`, `runtime-lens.tsx`, `public-understanding.tsx`: capacidades reales de investigación, evidence y presentación semántica que conviene aprovechar.

**Esa divergencia es un problema real a resolver**. No presupongas que el paradigma de `/panorama` es el correcto ni que el dossier de `/account` debe continuar. Tú decides qué conservar, transformar o reemplazar mediante evidencia y juicio creativo.

No elimines funcionalidades válidas bajo la apariencia de simplificación; si una experiencia se rediseña, el usuario debe seguir pudiendo profundizar en la misma evidencia y navegar por sus capacidades.

## Libertad creativa: la máxima compatible con un producto responsable

Tienes plena autoridad para redefinir, si mejora sustancialmente el resultado:

- La arquitectura de información, estructura y orientación del producto.
- El concepto visual del workspace, dashboard, canvas, dossier, cards, galerías, mapas, timelines y demás patrones.
- La navegación global/local/contextual, selección de organizaciones y rutas de exploración.
- El papel de AXENT: presencia, emplazamiento, activación contextual y relación con la evidencia; evita obligar a escribir prompts para entender un resultado.
- Los niveles de abstracción: lectura inmediata, comparación, investigación causal, evidencia e historia; no es obligatorio representarlos como cuatro pantallas.
- Densidad, tipografía, motion, interacción, recorridos de primer uso y retorno, composición responsive, microcopy y agrupación de hallazgos.
- Un lenguaje de cards de alta semántica, incluyendo patrones distintos para familias que tengan necesidades distintas, sin perder coherencia.
- Qué merece aparecer, qué se oculta progresivamente, cómo se accede y qué debe recordarse al cambiar de foco, tema o fecha.

Puedes realizar exploraciones radicales en un worktree, comparar enfoques y descartar los peores. No te conformes con justificar la mejora solo por reducción de clics: demuestra claridad y acceso al valor, y defiende además la dirección artística, el placer de exploración, la personalidad AXIGNAL y el carácter memorable de la interacción.

**No estás obligado a conservar Today/Explore/Evolution/Evidence como etiquetas, tabs ni menús.** Esas capacidades cognitivas deben seguir existiendo y ser encontrables; la mejor forma de organizarlas queda a tu criterio.

## Lo que SÍ es innegociable

La autoridad precede a la estética:
`docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` →
`.specify/memory/constitution.md` → ADRs aceptados →
`docs/product/HFX_HUMAN_FIRST_COGNITIVE_UX_DOCTRINE.md` y especificaciones.

Lee también:
`docs/product/AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md`,
`docs/product/AXIGNAL_BIDIRECTIONAL_INTELLIGENCE_EXECUTION_GOAL_2026-10-09.md`,
specs 063 y 064,
`.agents/skills/axignal-design-director/SKILL.md` si está disponible, y el sistema visual vigente.

Invariantes: AXIGLAND canónico único; EvidenceAdmission; `CLAIM ≠ WRITE`; `FAXT ≠ INXIGHT`; `OBSERVED ≠ POTENTIAL`; `UNKNOWN ≠ FALSE`; JEV no es autoridad de verdad; AXENT investiga, no escribe canónico; provenance, derechos, currentness, incertidumbre e identidad de entidad conservados; tenant/client_context/Xeed aislados.

No inventes resultados, fuentes, scores de verdad o señales. No conviertas AXIGNAL en un CRM, suite de tareas ni un chatbot como única interfaz. Privacidad, seguridad, accesibilidad y eficiencia son obligaciones, no preferencias visuales.

Respetar la identidad AXIGNAL —no SaaS genérico— y el Golden Master aceptado como baseline; puedes **proponer un cambio material de diseño** si lo justificas y lo demuestras, pero requiere aceptación CTO antes de sustituir el diseño aprobado.

## Impeccable — ACTIVACIÓN OBLIGATORIA, no solo inspiración

**Carga y aplica realmente la skill instalada de pbakaus/impeccable v4.5.2 en tu sesión de Claude Code**, no basta con mencionar su nombre en un informe. La ruta es `C:\Users\usuario\.claude\skills\impeccable\SKILL.md`. Lee `SKILL.md` entero y sigue su protocolo, los playbooks y los límites de iteración.

1. Abre una sesión desde el worktree exclusivo. **Ejecuta una vez `C:\Users\usuario\.claude\skills\impeccable\scripts\impeccable.cmd context`** con el directorio del proyecto como cwd; en entornos no Windows utiliza el launcher que describe la skill. Lee las directivas. Si falla el launcher, sigue expresamente el fallback indicado por `SKILL.md`; no inventes contextos ni afirmes que se cargó.
2. Antes de decidir la dirección artística, inspecciona `reference/new-work.md` y `reference/operate.md`; antes de editar UI, lee `reference/craft-floor.md`. Reconcilia cualquier PRODUCT.md/DESIGN.md con MASTER, HFX y Golden Master. No sustituyas su autoridad. Si la skill exige `init` para una superficie nueva, ejecútalo solo de manera subordinada a la doctrina, sin introducir una segunda visión canónica del producto.
3. **Utiliza de forma explícita las herramientas creativas de Impeccable**, seleccionadas por necesidad y con evidencia: `/impeccable shape` para arquitectura/experiencia; `/impeccable critique` y `/impeccable audit` para evaluación; **`/impeccable overdrive`, `/impeccable bolder`, `/impeccable colorize`, `/impeccable animate` y `/impeccable delight`** para explorar un lenguaje visual vivo, excepcional y memorable; `/impeccable layout`, `/impeccable typeset`, `/impeccable clarify`, `/impeccable distill`, `/impeccable onboard`, `/impeccable adapt`, `/impeccable harden`, `/impeccable optimize` y `/impeccable polish` donde corresponda. `/impeccable live` y `/impeccable generate` sirven para explorar variantes visuales si el entorno y la herramienta las soportan.
4. Respeta la **verificación acotada que exige Impeccable**: implementación completa, una ronda agrupada de inspección desktop + móvil, una tanda focalizada de reparaciones, como máximo otra comprobación para confirmar. No gastes la sesión en una sucesión infinita de prompts/pulidos.
5. **Muéstranos qué parte del resultado surgió de Impeccable**: decisiones visuales concretas, patrones de interacción, transiciones funcionando, uso expresivo y semántico de paleta, motion, estética WOW, reducción real de fricción y evidencia en navegador.

**Modo Operate**, por tratarse del dashboard del suscriptor, pero Operate no significa gris, plano ni rígido. Puede ser hermoso, alegre, divertido, sofisticado y profesional al mismo tiempo. El movimiento puede informar **y deleitar**; aprovecha efectos, transiciones y colores a fondo con criterio. Protege `prefers-reduced-motion`, dispositivos modestos, rendimiento y accesibilidad. La skill es una herramienta poderosa al servicio del producto, nunca autoridad sobre MASTER.

No dispares comandos indiscriminadamente, no permitas que un score automático decida la UX y no actives hooks ni instales dependencias sin necesidad.

## Cómo crear una gran solución

1. **Observa el producto real**, código y navegador. Contrasta explícitamente el ejemplo de `/panorama` con la experiencia autenticada `/account`. Revisa Customer Zero, onboarding, familias económicas, AXENT, cards, historial, evidencias, estados parciales y móvil. Identifica dónde se pierde comprensión o continuidad.
2. **Explora con libertad** direcciones de producto realmente distintas (no simples variaciones cromáticas). Elige la más convincente por valor humano y coherencia, no por familiaridad con el dashboard existente. Si tienes una idea mejor que cualquier brief, ejecútala en una superficie aislada y demuéstrala.
3. **Construye software real**: un recorrido subscriber E2E de gran calidad, unificando donde corresponda la experiencia y conservando funcionalidades. Itera con Impeccable y navegador; no gastes toda tu ventana en un informe previo.
4. **Generaliza con criterio** sobre la gramática de UI, sin refactors oportunistas ni un gran framework especulativo. La especialización por familia puede ser necesaria; sigue las fronteras de arquitectura.
5. **Entrega evidencia de producto**, no declaraciones de estilo. Antes/después verificable, demos operables de escritorio, tablet y 390/320px, y límites claros.

## Lo que el usuario debe poder hacer sin esfuerzo

- Primera visita: comprender el propósito, escoger/asignar la primera organización y recibir valor sin cursillo ni prompt.
- Regreso: encontrar qué cambió y recuperar el hilo.
- Hallazgo económico: entender qué significa, qué podría hacer y qué sigue siendo hipótesis.
- Autocrítica: reconocer fortalezas, gaps de comunicación, causas alternativas, evidencia y posible mejora, sin atribuciones falsas.
- Inspección: llegar de una conclusión a su fuente, instrumento y fecha y volver sin perder el contexto.
- Cartera: cambiar entre organizaciones/cliente sin mezclar permisos ni desorientarse.
- Investigación: explorar familias, relaciones, evolución y oportunidades sin memorizar la arquitectura interna.
- Estados difíciles: UNKNOWN, sin evidencia, fallo de instrumento, fuente revocada, demasiadas señales, idiomas largos, mobile y conectividad lenta.
- Accesibilidad: teclado, lector de pantalla, foco, contraste, reflow, reduced motion y seis idiomas.

Son pruebas de resultado; **no fijan el diseño**. Define métricas de éxito y fricción. No simules haber observado usuarios humanos; distingue E2E con fixtures de estudio de usabilidad real.

## Entrega y fronteras de ejecución

Tu unidad de éxito es **un producto real comprensible, navegable y agradable, no un mockup brillante**.

Trabaja solo en el worktree exclusivo `human-first-impeccable-claude`, desde main ya integrado, sin sobrescribir worktrees ajenos ni la carpeta canónica local con cambios pendientes. Puedes crear subramas/experimentos para tus alternativas.

Tests frontend, i18n es/en/fr/de/it/pt, tipos, build, accesibilidad, navegación, datos reales o equivalentes fieles, Architecture Guard y governance según cambios. Abre PR con capturas/videos y QA en navegador. No merge ni producción sin aceptación CTO.

Declara IMPLEMENTADO, PROBADO, INTEGRADO, DESPLEGADO y VERIFICADO E2E por separado.

**Reto:** sorprendernos inventando un dashboard/workspace de inteligencia económica que sea simultáneamente extraordinariamente fácil de comprender y extraordinariamente bello, vivo y divertido de navegar. Que apetezca explorar sus hallazgos y volver mañana. No preservar un dashboard por nostalgia ni crear un dossier por inercia. Crea la mejor interfaz posible para este producto.
