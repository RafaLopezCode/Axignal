# Human First Cognitive UX Doctrine

**Status:** Accepted product doctrine, pre-implementation  
**Authority:** MASTER §55; Engineering Constitution; ADR-0016 and ADR-0017  
**Scope:** Subscriber-facing AXIGNAL projections and contextual AXENT navigation  
**Evidence class:** Product requirements and hypotheses; no AXIGNAL user-study results are claimed.

## North star

> **AI makes intelligence abundant. Human attention remains scarce. AXIGNAL
> turns persistent machine intelligence into persistent human understanding.**

> **The sophistication of AXIGNAL must be experienced as simplicity, and that
> simplicity must never be purchased by hiding truth, uncertainty or evidence.**

Human First is a core product capability coupled to Memory/Time and the Economic
Brain. It is not a style layer, “beginner mode,” chatbot, or generic dashboard.
Its job is to reduce unnecessary integration, recall, comparison and context
restoration work while preserving inspectability and the one canonical truth.

## Evidence and authority labels

Use these labels when discussing HFX claims:

| Label | Meaning |
|---|---|
| **Empirical HCI evidence** | A published result for the study's participants, task and method. It constrains design but does not prove an AXIGNAL result. |
| **Established guidance** | A standard, guideline, heuristic or professional recommendation; not necessarily a causal result. |
| **CTO hypothesis** | A proposed AXIGNAL value mechanism that still needs product research. |
| **Architectural recommendation** | A target boundary or technical direction to evaluate before implementation. |
| **Canonical AXIGNAL decision** | Binding product/engineering requirement recorded in the MASTER, Constitution or accepted ADR. |

The HCI source synthesis and its limitations are in
[`HFX_COGNITIVE_PSYCHOLOGY_AND_HCI_RESEARCH.md`](../research/HFX_COGNITIVE_PSYCHOLOGY_AND_HCI_RESEARCH.md).
AXIGNAL-specific effectiveness is unvalidated until representative users are
tested using the protocol in
[`HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md`](../research/HFX_USER_RESEARCH_AND_VALIDATION_PROTOCOL.md).

## Core concepts

- **Cognitive Compression:** AXIGNAL presents the smallest truthful meaning
  that supports the user's present task while keeping material scope, epistemic
  state, temporal context, denominator, contradictions and evidence reachable.
- **Semantic Zoom:** the user examines the same object at different semantic
  depths without losing identity or context.
- **Cognitive Navigation:** the user moves by meaningful relationship and
  question, rather than remembering AXIGNAL's ontology or where a module lives.
- **Cognitive Continuity:** AXIGNAL can restore what the user was investigating,
  what remained open and what changed since a meaningful checkpoint.
- **Cognitive Provenance:** AXIGNAL can trace why an investigation actually
  entered attention, when that origin was recorded.
- **Human Cognitive Amortization:** do not require repeated reconstruction of
  understanding AXIGNAL can validly preserve.
- **Interpretation Debt:** AXIGNAL's product term for mental work unnecessarily
  transferred to a person to turn available information into understanding. It
  is not a validated psychometric construct or AXIGNAL metric.
- **Expertise Tax:** the domain vocabulary and professional knowledge someone
  must already have before software becomes useful. Product objective:
  minimize required vocabulary while keeping analytical depth available.
- **Cognitive Jevons:** CTO hypothesis that cheaper and more abundant machine
  analysis may increase human integration and verification work if output is
  unmanaged. It is not an established economic law or a measured AXIGNAL effect.

These definitions express canonical AXIGNAL product intent. Claims that a
particular pattern reduces time, workload, errors or cost remain hypotheses
until AXIGNAL-specific evaluation.

## Semantic depth and navigation

```text
GLANCE       What is this? What matters?
UNDERSTAND   What changed? Why does it matter? Compared with what?
REASON       How is this derived? Which inputs, limits and blockers matter?
PROVE        Which observations, FAXTs, instruments, sources and dates support it?
```

Depth is conceptual, not a mandatory wizard or four-screen funnel. A person may
jump from a summary to evidence, evolution, comparison or AXENT. Preserve the
selected object, relevant scope and a route back to its surrounding context.
Relationship is the horizontal movement; semantic depth is the vertical
movement. The existing subscriber modes remain Today, Explore, Evolution,
Evidence and Ask AXENT.

### Hard interaction principles

1. **Meaning before metrics.** Explain what is happening and why before relying
   on a specialist number. A professional measure retains its plain meaning,
   technical definition and interpretation boundary where material.
2. **No mental joins.** When AXIGNAL already governs the relevant connection, it
   should present the combined meaning and preserve the dependencies that
   support it. Do not invent a join when evidence or comparability is missing.
3. **Evidence on demand.** A material output provides a direct path from human
   meaning through derivation and canonical references to permitted evidence.
   This is persisted provenance, not generated post-hoc storytelling.
4. **Same truth, different density.** Non-specialists may stop at the meaning;
   specialists can inspect method, sample, denominator, instrument, scope,
   comparison and evidence without receiving a different epistemic conclusion.
5. **Attention is a projection.** Prioritization explains why something is
   surfaced. Attention does not create economic truth or canonical relevance.
6. **Return is a task, not a page list.** Restore the question, why it began
   when known, what was unresolved, what AXIGNAL knew then, what changed and how
   to resume.

## Human-level information taxonomy

These families organize human questions. They do not map one-to-one to domain
packages, canonical node types, routes or tables.

| Semantic family | Human question |
|---|---|
| Identity | Who is this? |
| Capabilities | What can it do? |
| Products & Services | What does it offer? |
| Markets & Economic Reach | Where could it participate, and under what constraints? |
| Relationships & Ecosystem | What is it connected to? |
| Economic Activity | What is happening? |
| Demand | What is needed or sought? |
| Projects & Procurement | Where is demand materializing? |
| Opportunities | What potential economic relevance emerges? |
| Digital Representation | How is it represented on observed digital surfaces? |
| Public Experience | What public experience signals were observed? |
| Competitive Context | How does it differ under comparable conditions? |
| Temporal Change | What changed, when, and against which state? |
| Evidence & Provenance | Why should I believe this? |

Search, Generative, Social/Public Conversation, and Public Reputation/Experience
remain the four DRI families established by MASTER §54 and ADR-0014. Temporal
Change and Evidence & Provenance cut across other families. Composite outputs
such as Opportunity, Gap, Change, Comparison, Path, Anomaly and Signal are
human-facing projections; their presentation does not create a FAXT.

## Independent output dimensions

Material output can be described along independent axes:

```text
SEMANTIC FAMILY        what economic subject is represented
EPISTEMIC STATE        what AXIGNAL's governing state says it knows
TEMPORAL STATE         observation/validity time and change/currentness
ATTENTION PROJECTION   why this item is surfaced for attention
OUTPUT ARCHETYPE       state, change, signal, gap, opportunity, comparison,
                       path, anomaly or evidence
```

These axes are not a unified status scale. Preserve the exact governing
semantics, including `OBSERVED`, `DECLARED`, `INFERRED`, `CORROBORATED`,
`CONTRADICTED`, `STALE`, `UNKNOWN`, and graph-level `POTENTIAL` or `HISTORICAL`
where applicable. `UNKNOWN != FALSE`, `POTENTIAL != OBSERVED`, and
`HISTORICAL != CURRENT`. A human-friendly phrase may simplify vocabulary only
when its mapping is deterministic and cannot change meaning. `NEW_TO_AXIGNAL` is
not `NEW_IN_THE_WORLD`.

Candidate attention progression:

```text
BACKGROUND → CHANGED → RELEVANT → MATERIAL → DESERVES ATTENTION
```

This is a projection, not canonical truth or a frozen score. Surface the
inspectable reasons and source state when the system elevates an item.

## Human Output Contract (conceptual, not a runtime schema)

Every material output should support the following meaning and inspection
responsibilities. Exact fields, serialization and runtime classes are deferred.

```text
IDENTITY      stable output/subject reference and human output family
GLANCE        headline, one-sentence meaning, why it matters
STATE         canonical epistemic, temporal, change and attention states
MEASURE       useful measure, unit, denominator, scope, period/comparison
UNDERSTAND    concise context, principal drivers/blockers, what changed
REASON        derivation summary, dependencies, contradictions and unknowns
PROVE         evidence summary and permitted FAXT/observation/source/instrument refs
NAVIGATION    related objects, evidence/evolution/compare targets, AXENT context
CONTINUITY    investigation and checkpoint references when this is a return
PROVENANCE    actual attention origin when known; UNKNOWN otherwise
```

Not every field belongs in the first view. A material output fails HFX if a
representative user cannot determine what it means, why it matters, whether it
is observed/derived/uncertain, what materially changed, or how to inspect the
support. An expert must be able to reach the method and evidence without losing
the parent object or comparison context.

## Epistemic and visual grammar

- Meaning is expressed in language and hierarchy before decorative code.
- Epistemic/currentness state never depends on color alone. Pair any future
  visual cue with text or another perceivable channel and an accessible name.
- `UNKNOWN` is not zero or a negative finding; `POTENTIAL` is not good/bad by
  itself; `CONTRADICTED` is not automatically false or adverse.
- Separate epistemic unknown, stale support, source conflict, statistical
  uncertainty, incomplete coverage and model/measurement variability.
- A chart supports a statement; it does not replace the insight (`CHART !=
  INSIGHT`). Representation must fit the question: temporal trend, exact
  symbolic comparison, relational path, or evidence trace are different tasks.
- Exact colors, icons, patterns, layout, animation and adaptive density are
  design hypotheses. Graph is only one projection and requires an accessible
  non-graph complement under ADR-0009.
- Treat cognitive accessibility as part of comprehension. Future production
  surfaces target WCAG 2.2 AA and include COGA-informed research and manual
  assistive-technology evaluation. WCAG conformance does not prove complete
  cognitive usability.

## Three context authorities and AXENT

```text
AXIGLAND                  shared canonical economic truth
XEED GERMINATION CONTEXT  tenant/client/Xeed process and authorized private refs
PRIVATE COGNITIVE STATE   user/client/Xeed attention and investigation continuity
```

These authorities are related but not interchangeable. Xeed process state is
not a second company truth. Private attention cannot mutate AXIGLAND. Any
public FAXT/relationship still requires the existing evidence-admission path.
Private cognitive memory represents task/context, not a personality,
intelligence, mental-health, political or protected-trait profile. Retention,
deletion, client offboarding and derived embedding deletion follow source
rights and governed privacy policy.

AXENT is a contextual cognitive navigator, not the only interface. It can
conceptually focus, expand, compare, explain, show evidence/evolution and
restore an investigation. It does not create its own tenant/client scope, have
direct database access, issue arbitrary SQL, or decide truth. A deterministic
context broker returns only the minimum authorized structured context.

For consultancies, private scope resolves:

```text
TENANT → CLIENT_CONTEXT → XEED → INVESTIGATION_THREAD / OBJECT
```

Default scope is the active client. Portfolio-wide retrieval requires explicit
request, permission and clear user-visible scope. Similarity is only a locator;
it cannot authorize retrieval or silently switch clients.

## Validation boundary

P0-HFX-00 canonizes principles and defines research. It does not prove that
semantic zoom, compression, continuity, provenance, AXENT navigation, cognitive
amortization or adaptive density improves AXIGNAL outcomes. The benchmark
protocol, representative user groups, repeatable tasks, metrics, limitations
and accessibility requirements live in the HFX research protocol. No
production UI, schema, migration, embedding, AXENT runtime or deployment is
authorized here.
