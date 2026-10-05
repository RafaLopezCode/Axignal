# AXIGNAL — Economic Brain Execution Roadmap 2026-10-05

**Estado:** EXECUTION ROADMAP / subordinado a MASTER, Constitution y ADRs aceptados.
**Objetivo:** convertir la arquitectura ya definida en una primera capacidad económica E2E real y luego escalarla sin abrir roadmaps paralelos.
**Fuente reconciliada:** auditoría Brain 2026-10-04 (S01–S12), arquitectura E2E Human First (E0–E7), estudio JEV 2026-10-05 (J0–J4).

## 0. Regla de ejecución

Un slice no está terminado por existir código ni por pasar tests aislados. Para capacidades de producto la secuencia objetivo es:

IMPLEMENTADO → PROBADO → INTEGRADO → DESPLEGADO → VERIFICADO E2E

Este roadmap no autoriza despliegue por sí mismo.

## 1. Milestone nuclear

> ¿Puede AXIGNAL entender de verdad una Organización y descubrir algo económicamente útil que el humano no le haya dicho?

La primera prueba debe conectar, sin bypass de autoridad:

PUBLIC/EXTERNAL EVIDENCE
→ DISCOVERY / ACQUISITION
→ RAW / REPRESENTATION
→ ECONOMIC OBSERVATIONS
→ RICH SUBJECT STATE
→ APPLICABILITY / ANSWERABILITY
→ TYPED JUDGMENT VECTOR
→ PYTHON INTERPRETATION
→ EVIDENCE ADMISSION o DERIVED INXIGHT/POTENTIAL
→ EXPLAINABLE BASIS
→ HUMAN OUTPUT
→ PANORAMA / EVIDENCE / AXENT

## 2. Roadmap único

| Slice | Prioridad | Entrega verificable | Absorbe | Criterio de salida |
|---|---|---|---|---|
| **EB-00 — Truth & Cost Firewall** | P0 | Cerrar falsa atribución semántica en EvidenceAdmission y pérdida de lower-bound de coste | S01, S02(parcial), E0/E1 | F01 rechazado; 7→UNKNOWN→1 conserva lower_bound=8 e incompletitud; replay positivo válido; tests contractuales verdes |
| **EB-01 — Governed Run Envelope** | P0/P1 | Presupuesto antes de dispatch, deadline monotónico, Attempt completo, cancel/retry/lease idempotente y coste reconciliado | S02 resto, S03, S06, E1 | Ningún fetch/provider/storage significativo fuera de budget/attempt; crash/retry no duplica commit; UNKNOWN cost no se convierte en cero |
| **EB-02 — Identity & Representation Fidelity** | P1 | Identidad multiclave, Unicode-safe, representación precisa, spans/grounding verificables, ambigüedad explícita | S04, E0/E2, J1 prerequisitos | Homónimos/rebrand/idiomas no se fusionan silenciosamente; hidden text no equivale a visible; unsupported span se rechaza |
| **EB-03 — Source Rights & Reuse Registry** | P1 | Registro de fuentes/instrumentos con purpose, rights, scope, retention, rate/robots, currentness y reuse reason | S05, E0/E2 | Metadata auth antes de payload; cada observación tiene policy/version/scope; no reuse sin derecho |
| **EB-04 — First Economic Vertical** | P1 | Una Organización + capability + need/event + roles coexistentes → TypedJudgmentVector → POTENTIAL/UNKNOWN/WARRANTED_ATTENTION → Explainable Basis → Human Output | S08, E3/E4/E6, J0–J4 | Vertical determinista E2E con fake evaluator y provider-neutral port; supplier/customer coexistentes; missing context abstiene; contradicción bloquea atención positiva |
| **EB-05 — Live Semantic Evaluator Pilot** | P1 | Laboratorio multi-axis gobernado con JEV y comparador Luna/reglas sobre corpus autorizado | S08/S10/S11, E3, J0–J4 | Corpus rights-cleared; batch vs singles; quality/cost/risk-coverage medidos; provider swap; ningún model write; selección basada en evidencia |
| **EB-06 — Temporal Economic Memory** | P1 | Proyección incremental, change/dependency invalidation, absence/withdrawal/conflict tipados, as-of reproducible | S07, E6, J3 | replay==incremental; UNKNOWN no FALSE; sólo dimensiones afectadas se reevalúan; historial conservado |
| **EB-07 — Opportunity & Continuous Observation** | P1 | Capability×Need×Reach×Constraints → INXIGHT POTENTIAL + scheduler durable/shared observation | S09, S10, E4/E6 | Una oportunidad investigable real con basis y missing context; reobservación por cambio; shared work sin double count |
| **EB-08 — Human Product & Production Proof** | P1/P2 | Human Output Compiler sobre outputs reales, continuity/UI plan, 1/2/100 Organizations, load/recovery/ops | E2/E5/E7, S12, S11 donde aporte | FIRST_MAP_WOW real; proof directo; context isolation; recovery/backup/load medidos; producción sólo tras E2E externo |

## 3. Orden obligatorio y paralelización permitida

Camino crítico:

EB-00 → EB-01 → EB-02/EB-03 → EB-04 → EB-05/EB-06 → EB-07 → EB-08

Trabajo paralelo permitido:
- EB-02 y EB-03 pueden avanzar en paralelo tras EB-00 si no pisan los mismos contratos.
- EB-06 puede empezar en paralelo al final de EB-04 sobre contratos ya congelados.
- Operabilidad de EB-08 (health/recovery/load harness) puede prepararse pronto, pero no justificar migración de infraestructura.
- Parser/retrieval/DRI sólo entra cuando un benchmark demuestra ganancia sobre la vertical; no bloquea EB-04.

No permitido:
- dos AXIGLAND;
- model/JEV como truth authority;
- universal opportunity/sale score;
- UNKNOWN→FALSE;
- POTENTIAL→OBSERVED;
- infraestructura nueva por anticipación;
- UI fixture presentada como prueba del Brain.

## 4. EB-00 — estado de ejecución actual

### P0-A Semantic grounding / admission
Objetivo: una EvidenceAdmission no puede autenticar una tupla inicialmente mal atribuida sólo porque el texto y hash son estables.

Contrato target:
- Evidence conserva subject de observación;
- GroundedClaim versionado liga subject/predicate/object-value;
- menciones y supporting excerpt son explícitos;
- tuple solicitada debe coincidir con el grounding;
- valores no literales fallan cerrados hasta que EB-02 aporte un binding de identidad gobernado;
- digest incluye grounding;
- policy/source authority sigue independiente.

Repro bloqueante:
“ACME manufactures industrial pumps.” NO puede admitir subject=org:unrelated, predicate=manufactures, object=nuclear weapons.

### P0-B Cost lower-bound / completeness
Objetivo: coste desconocido no destruye gasto conocido.

Contrato target:
- amount conocido representa lower bound cuando hay incompletitud;
- cost_complete distingue total completo de lower bound;
- unknown delta mantiene gasto conocido e invalida completeness;
- gasto conocido posterior se suma al lower bound sin recuperar falsamente completeness;
- stop_on_unknown_cost puede fallar cerrado aunque exista lower bound.

Repro bloqueante:
7 known → UNKNOWN → +1 known = lower_bound 8, cost_complete=false.

## 5. EB-04 — primera vertical económica de referencia

Caso mínimo de producto:
1. Organización canónica resuelta.
2. Capability observable con provenance.
3. Need/event candidate independiente.
4. RichSubjectState con source/time/currentness.
5. Aplicabilidad y Answerability por dimensión.
6. Dimensiones mínimas: capability relevance; supplier role; customer role; need match; reach/constraint sufficiency; relationship state; contradiction; evidence support/currentness.
7. Evaluator replaceable devuelve juicios tipados, no verdad.
8. Python compone POTENTIAL, UNKNOWN, INVESTIGATE o WARRANTED_ATTENTION.
9. Explainable Basis conserva source refs exactos, incertidumbre y contradicciones.
10. Human Output se puede consumir por Panorama/AXENT sin inventar contenido.

No requiere todavía proveedor live, crawler masivo, graph DB, vector DB, Kafka, multi-agent framework ni producción.

## 6. EB-05 — política JEV/Luna

JEV se evalúa como Structured Semantic Evaluator reemplazable. Luna se evalúa como proveedor generativo/semántico alternativo cuando corresponda. Ninguno es arquitectura canónica.

Comparación mínima:
- reglas deterministas;
- JEV pinned;
- Luna/adaptador autorizado;
- batch vs singles;
- misma información, mismos DecisionContracts/ChoiceSpaces;
- precision/recall por dimensión cuando aplique;
- risk–coverage/abstention;
- latency/usage/cost;
- replay;
- severe-error rate;
- provider failure/degradation.

Promoción sólo tras corpus autorizado, resultados comparables y break-even medido.

## 7. Gates antes de integración

Para cada slice relevante:
- tests focalizados;
- uv run ruff format --check .
- uv run ruff check .
- uv run mypy
- uv run pytest o subconjunto justificado durante iteración + suite requerida antes de merge;
- uv run architecture-guard --root .
- uv run axignal-governance
- git diff --check

No se modifica un gate para conseguir verde.

## 8. Definición de éxito del milestone

El milestone Economic Brain First Vertical se considera VERIFICADO sólo cuando una ejecución reproducible muestra:

1. inputs públicos/sintéticos autorizados;
2. observaciones y provenance reales;
3. Rich State suficiente o abstención;
4. TypedJudgmentVector multi-axis;
5. interpretación Python;
6. oportunidad/atención POTENTIAL explicable o UNKNOWN;
7. ninguna escritura canónica indebida;
8. evidencia navegable;
9. salida Human First;
10. coste y tiempo medidos;
11. replay reproducible;
12. comportamiento visible E2E en la superficie de producto cuando se integre.

Ese resultado, y no la cantidad de contratos o documentos, es la prueba de que AXIGNAL empieza a funcionar como Economic Brain.