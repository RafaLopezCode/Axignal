# AXIGNAL SUBSCRIBER EXPERIENCE & ASK AXENT — PRODUCT / INTERACTION PLAN

**Version:** 0.2\
**Status:** PROPOSED\
**Implementation status:** PRE_IMPLEMENTATION\
**Document class:** PRODUCT_INTERACTION_SPECIFICATION\
**Date:** 2026-09-26\

---

## 0. Purpose

This document defines the Human-First subscriber experience for AXIGNAL: the product surface through which a subscriber observes the germination, current state, evolution, evidence, economic map and explainable intelligence of their Xeed.

It also defines **Ask AXENT — by AXIGNAL** as the contextual cognitive assistance layer for the subscriber.

This document does **not** define AXIGNAL's internal Admin console. The internal Admin remains a separate operational, economic, epistemic and governance surface.

AXIGNAL is an observing economic brain, not an economic index. The map is
cognitive substrate; explainable Economic Opportunity Intelligence and
Compounding Economic Intelligence are the product. This subscriber plan must
make opportunity and reuse legible without converting potential demand into
customers, leads or observed relationships.

The central product objective is:

> **Expose the maximum economically useful intelligence AXIGNAL can produce while minimizing the cognitive effort required to understand it.**

The experience must not simplify AXIGNAL by deleting intelligence. It must simplify comprehension through hierarchy, progressive disclosure, contextual explanation and representation appropriate to the user's question.

---

# 1. Product doctrine

## 1.1 Human First

The subscriber must receive substantial value without writing a prompt, learning AXIGNAL's ontology or understanding graph theory.

The primary experience is therefore not a chatbot.

It is a visual, temporal, evidence-backed intelligence product.

> **HUMAN FIRST. AXENT WHEN NEEDED.**

The UI must answer, in order:

1. What is happening?
2. What matters?
3. What changed?
4. Why am I seeing this?
5. What does AXIGNAL know?
6. What does AXIGNAL not know?
7. What evidence supports this?
8. What else should I examine?

Only after the product has made these answers legible should conversational intelligence be required.

## 1.2 Complexity belongs to AXIGNAL

> **UI_COMPLEXITY != DOMAIN_COMPLEXITY**

> **THE USER MUST NOT LEARN AXIGNAL'S INTERNAL ONTOLOGY TO RECEIVE VALUE**

> **AXIGNAL SHOULD REVEAL COMPLEXITY PROGRESSIVELY, NOT REMOVE INTELLIGENCE TO ACHIEVE SIMPLICITY**

> **THE UI MUST EXPLAIN THE WORLD BEFORE THE USER HAS TO ASK THE AI**

FAXT, INXIGHT, PATHX and other internal concepts may exist as canonical domain objects, but the default UX should use human language first and expose technical semantics when useful.

## 1.3 One world, multiple projections

There is one canonical AXIGLAND.

The subscriber UI, Ask AXENT, portable Xeed exports and Product MCP are projections over the same canonical world.

```text
                        AXIGLAND
                           |
                 SUBSCRIBER PROJECTION
                           |
        +------------------+------------------+
        |                  |                  |
   HUMAN-FIRST UI       ASK AXENT        PORTABILITY
                                           |
                                      MD / JSON / MCP
```

No projection becomes a competing source of truth.

---

# 2. Canonical cognitive model decision

AXIGNAL does not canonize a foundation model, provider or API as its brain.
AXIGNAL's economic brain is the complete governed system: observation,
AXIGLAND memory, deterministic computation, bounded typed judgment when
needed, AXENT research, deterministic composition/policy and provenance.

An evaluator is a replaceable component for bounded judgment classes where
deterministic computation cannot answer. AXENT orchestrates contextual
investigation, missing-information research and explanation; neither an
evaluator nor AXENT is canonical truth authority. Model identity is policy,
not domain semantics. Provider live use requires separate authority, rights,
quality and operational gates. This product specification grants no such
authorization.

Routing is answerability-aware and deterministic-first:

```text
DETERMINISTIC ANSWER
    → use deterministic computation
BOUNDED JUDGMENT NEEDED AND ANSWERABLE
    → use replaceable structured evaluator, then deterministic composition
MISSING ANSWER-REQUIRED CONTEXT
    → AXENT research loop, then reevaluate
STILL INSUFFICIENT
    → preserve UNKNOWN / abstain
```

Only the minimum relevant, authorized, structured context is available to a
future evaluator or contextual response. Model output cannot write canonical
truth, serve as evidence admission, or override AXIGNAL policy.

---

# 3. Subscriber experience architecture

The subscriber product has five primary cognitive modes.

## 3.1 TODAY

Purpose: answer **"What matters now?"**

This is the default returning-user surface.

It should emphasize:

- material changes since last visit;
- newly observed relationships;
- materially changed relationships;
- new representation signals;
- representation anomalies;
- new or changed economic paths;
- important currentness changes;
- meaningful contradictions;
- newly resolved questions;
- discoveries deserving attention.
- materialized economic activity and newly relevant demand/projects;
- explainable potential opportunities with their temporal and epistemic state;
- why a capability may or may not reach the activity's geography.

The page must not become a generic KPI dashboard.

The hero should communicate change and significance in human language.

Example:

```text
ACME                                      OBSERVING

Your economic world changed while you were away.

3 material changes

01  New potential relationship
02  Competitive movement
03  Representation anomaly

Explore what changed
```

## 3.2 GERMINATION

Purpose: turn the construction of the first Xeed into a truthful product experience.

Germination must never be represented as fake percentage progress.

The UI is a projection of real domain/operational events.

Candidate human stages:

1. Resolving organization
2. Reconstructing observable economic identity
3. Discovering capabilities
4. Identifying markets
5. Exploring corporate structure
6. Mapping economic neighbourhood
7. Investigating open questions
8. Verifying relationships
9. Building economic paths
10. Evaluating representation
11. Testing map readiness
12. First Map Ready

Each stage may expose discoveries as soon as they are safe to display with their epistemic state.

The UI must distinguish:

- DISCOVERING
- VERIFYING
- SUPPORTED
- CONTRADICTED
- UNRESOLVED
- STALE
- UNKNOWN

Progress must be derived from actual state/events.

> **GERMINATION_UI = PROJECTION(REAL_GERMINATION_STATE)**

## 3.3 EXPLORE

Purpose: allow the subscriber to investigate the observable economic world around the Xeed.

Explore is not synonymous with graph.

Explore includes markets, projects, procurement/demand signals, observed
capabilities, capability-specific Economic Reach, derived opportunities and
Opportunity PATHX explanations. Procurement and project signals are economic
activity, not customer or lead records. An opportunity is `POTENTIAL` by
default and cannot imply commercial fit.

The representation must match the cognitive question.

| Human question | Preferred representation |
|---|---|
| What is happening? | Feed / discoveries |
| Who matters? | Economic map |
| How are they connected? | Graph |
| What changed? | Timeline |
| Why is this here? | Evidence trail |
| How does A connect to B? | PATHX |
| Who owns/controls what? | Corporate tree |
| What is uncertain? | Knowledge / observability |
| What looks unusual? | Representation anomalies |

Graph rendering is one projection, not the product itself.

## 3.4 EVOLUTION

Purpose: make the Xeed visibly alive over time.

Core questions:

- What changed since my last visit?
- What changed this week/month/quarter?
- Which relationships appeared, weakened, became stale or disappeared?
- How has observable economic identity evolved?
- Which capabilities/markets became newly visible?
- Which contradictions were resolved?
- Which evidence became stale?
- What did AXIGNAL know at a prior point in time?

Evolution should support historical reconstruction rather than silently overwriting the present.
It also shows how demand, projects, potential opportunities, capability reach
and the supporting knowledge changed, including what was reused, revalidated,
or newly researched.

## 3.5 EVIDENCE

Purpose: allow the subscriber to audit AXIGNAL rather than merely trust it.

Progressive drill-down:

```text
DISCOVERY
   |
EXPLANATION
   |
DERIVATION
   |
FAXTs
   |
EVIDENCE
   |
SOURCE
```

Every material or surprising economic signal or projection should expose:

> **WHY AM I SEEING THIS?**

For a derived opportunity, its persisted explanation trace must expose the
activity/demand signal, relevant capability, geography/reach reasoning,
temporal context, typed judgment dimensions, composition and policy, supporting
evidence/provenance, missing context and uncertainty. No post-hoc generative
justification may invent a rationale.

Evidence views should expose source, observation time, currentness, derivation, supporting/contradictory evidence and relevant epistemic state without overwhelming the default experience.

---

# 4. First Map WOW

The first map must not begin with a hairball.

Before exposing the complete map, AXIGNAL should present three concise human-readable surfaces:

## What AXIGNAL learned

A compact reconstruction of the organization's observable Economic DNA.

## What AXIGNAL found

The highest-value evidence-backed discoveries.

## What AXIGNAL did not expect

Non-obvious economic paths, representation anomalies, unexpected neighbourhoods or other inspectable surprises.

Then:

> **Explore your economic world**

The target reaction is:

> **"I know my company from the inside. AXIGNAL is showing me how my company exists from the outside — and why."**

The WOW is not raw data volume.

> **THE WOW IS HOW QUICKLY A HUMAN CAN TURN AXIGNAL'S DATA INTO UNDERSTANDING.**

---

# 5. Progressive disclosure

Every major subscriber object should support multiple levels of depth.

Example:

```text
NEW MARKET SIGNAL
      |
      v
HUMAN EXPLANATION
      |
      v
WHY?
      |
      v
SUPPORTING RELATIONSHIPS / CAPABILITIES / PATHXs
      |
      v
FAXTs
      |
      v
EVIDENCE
      |
      v
ORIGINAL SOURCE
```

The default view optimizes comprehension.

The deepest view optimizes inspectability.

The product must support both without forcing either mode on every user.

---

# 6. Ask AXENT — by AXIGNAL

## 6.1 Role

Ask AXENT is AXIGNAL's contextual cognitive interface.

AXENT does not replace the UI.

AXENT extends what the user can understand from it.

> **ASK AXENT EXISTS TO EXTEND HUMAN UNDERSTANDING, NOT TO COMPENSATE FOR POOR INFORMATION DESIGN.**

Ask AXENT should be available both as a dedicated analysis surface and as a contextual action attached to meaningful objects.

Examples:

- Ask AXENT about this organization
- Ask AXENT about this relationship
- Ask AXENT about this change
- Ask AXENT about this PATHX
- Ask AXENT about this anomaly
- Ask AXENT about this evidence
- Ask AXENT about this time range
- Ask AXENT about this map selection

## 6.2 Contextual architecture

```text
USER QUESTION
      +
CURRENT VIEW
      +
SELECTED OBJECTS
      +
AUTHORIZED XEED PROJECTION
      |
      v
AXIGNAL QUERY / CONTEXT BUILDER
      |
      v
MINIMAL RELEVANT STRUCTURED CONTEXT
      |
      v
REPLACEABLE CONTEXTUAL COGNITION / STRUCTURED EVALUATOR WHEN AUTHORIZED
      |
      v
GROUNDED EXPLANATION / ANALYSIS
      +
INSPECTABLE AXIGNAL REFERENCES
```

The LLM must not receive the entire Xeed by default.

Context should be assembled from the smallest useful set of:

- organization state;
- selected graph elements;
- FAXTs;
- INXIGHTs;
- PATHXs;
- evidence references;
- temporal state;
- currentness;
- contradictions;
- representation signals;
- knowledge gaps;
- user-selected scope.

## 6.3 Interaction classes

### EXPLAIN

Explain an already materialized AXIGNAL object.

Example:

> Why does AXIGNAL connect us to this market?

### ANALYZE

Reason across a bounded structured projection.

Example:

> What pattern do you see across these five changes?

### COMPARE

Compare selected organizations, relationships, periods or paths using AXIGLAND evidence.

### EXPLORE

Help the user notice potentially meaningful patterns or areas for investigation within the authorized projection.

### DEEP RESEARCH REQUEST

If answering requires evidence AXIGNAL does not currently possess, AXENT must not fabricate it.

Instead:

```text
ASK AXENT
   |
"NEW EVIDENCE REQUIRED"
   |
INVESTIGATE
   |
ResearchObjective
   |
AXENT CLOSED RESEARCH LOOP
   |
NEW EVIDENCE
   |
JEV / POLICY
   |
AXIGLAND
   |
UPDATED ANSWER
```

The user may direct attention.

The user may not direct conclusions.

> **USERS MAY DIRECT AXIGNAL'S ATTENTION, BUT NEVER ITS CONCLUSIONS.**

---

# 7. Ask AXENT epistemic rules

Hard invariants:

- `LLM_EXPLANATION_IS_NOT_CANONICAL_TRUTH`
- `LLM_ANALYSIS_IS_NOT_FAXT`
- `LLM_CONTEXT_IS_MINIMIZED_TO_RELEVANT_PROJECTION`
- `LLM_MAY_NOT_SILENTLY_FILL_EVIDENCE_GAPS`
- `UNKNOWN_IS_NOT_FALSE`
- `DISPUTED_IS_NOT_FALSE`
- `USER_PROMPT_IS_NOT_CANONICAL_EVIDENCE`
- `EXTERNAL_MODEL_KNOWLEDGE_IS_NOT_AXIGLAND`
- `AXENT_MUST_DISTINGUISH_EXISTING_KNOWLEDGE_FROM_NEW_RESEARCH`
- `NEW_RESEARCH_REQUIRES_THE_RESEARCH_LOOP`
- `AXENT_OUTPUT_CANNOT_DIRECTLY_MUTATE_AXIGLAND`
- `CANONICAL_WRITE_REQUIRES_AXIGNAL_POLICY`
- `EVERY_MATERIAL_EXPLANATION_SHOULD_BE_INSPECTABLE_TO_SUPPORTING_AXIGNAL_STATE`

If AXIGLAND cannot support an answer, AXENT should say so clearly.

---

# 8. Selection intelligence

Explore should allow users to select one or more economic objects and invoke AXENT over that bounded set.

Examples:

- three organizations;
- two relationships;
- a PATHX;
- a group of competitors;
- a geographic cluster;
- a time interval;
- a market neighbourhood.

Possible questions:

- What connects these organizations?
- What do these companies have in common?
- Show the strongest evidence-backed economic paths between them.
- Which part of this hypothesis is unsupported?
- What changed in this cluster over the last quarter?
- Which relationship here is least current?
- What am I likely overlooking in this selection?

This transforms the map from visualization into an interactive research surface.

---

# 9. Subscriber navigation

The information architecture should remain deliberately small.

Candidate top-level navigation:

1. **Today**
2. **Explore**
3. **Evolution**
4. **Evidence**
5. **Ask AXENT**

Germination temporarily replaces/augments Today until First Map Ready.

Internal ontology should not become navigation merely because it exists in the domain model.

---

# 10. Returning-user loop

AXIGNAL must create a recurring reason to return.

Primary returning-user message:

> **Your economic world changed while you were away.**

The product should summarize only material changes first and permit progressive expansion.

This creates the recurring loop:

```text
OBSERVE
   |
CHANGE
   |
SURFACE WHAT MATTERS
   |
UNDERSTAND
   |
EXPLORE
   |
ASK AXENT
   |
RETURN LATER
```

First-map WOW drives acquisition/activation.

Evolution drives retention.

---

# 11. Subscriber cognitive cost architecture

The subscriber UI should require zero LLM cost for normal reading.

Deterministic subscriber read models should provide:

- counts;
- timelines;
- changes;
- relationship state;
- graph projection;
- corporate structure;
- currentness;
- evidence;
- PATHXs;
- filters;
- sorting;
- deterministic attention candidates where policy allows.

AXENT cognition is invoked when natural-language contextual reasoning adds
value and a deterministic response is insufficient. Provider selection remains
replaceable policy and is not authorized by this product spec.

Three conceptual levels:

## Level 1 — Deterministic UI

No LLM required.

## Level 2 — Contextual Ask AXENT

Bounded contextual cognition over a minimal authorized projection, behind
provider interfaces and governed by AXIGNAL policy.

## Level 3 — New investigation

Research request enters AXENT's governed research loop; any future provider
selection requires separate authority and evaluation.

This prevents the subscriber chatbot from becoming an uncontrolled research agent.

---

# 12. Replaceable cognition and execution policy

## 12.1 Contextual / interactive

Future interactive contextual cognition must remain behind replaceable
provider interfaces, use minimal authorized context and return inspectable
references to deterministic AXIGNAL retrieval. An API and provider are not
selected by this doctrine.

Such requests must optimize:

1. groundedness;
2. comprehension;
3. latency;
4. minimal relevant context;
5. cost.

## 12.2 Background / asynchronous

Background research or evaluation is selected by AXENT and AXIGNAL policy
according to task boundaries, answerability and authorization. No batch API,
provider or model is canonized here.

## 12.3 Reasoning effort

Reasoning effort must not be globally fixed.

Candidate policy:

- `none` / `low`: concise explanation, summarization, classification of already structured context;
- `medium`: cross-object analysis and normal contextual reasoning;
- `high+`: only when evaluation demonstrates material quality benefit for bounded difficult tasks.

Quality, groundedness, latency and cost must be evaluated by bounded
interaction class before any provider/model policy is authorized.

## 12.4 Context discipline

Provider-specific context limits are mutable policy and are not canonized by
this spec. Context size is capacity, not a target.

> **AVAILABLE_CONTEXT != REQUIRED_CONTEXT**

Ask AXENT should retrieve narrowly rather than routinely sending enormous Xeed contexts.

This improves cost, latency, signal-to-noise and epistemic control.

---

# 13. Cognitive-provider governance

The domain must reference roles rather than model IDs.

Examples:

- `BACKGROUND_COGNITIVE_PROVIDER`
- `SUBSCRIBER_COGNITIVE_PROVIDER`
- `DEEP_RESEARCH_COGNITIVE_PROVIDER`

Any initial provider mapping requires a separate explicit, evidence-based
policy decision; this document does not map these roles to a provider.

Model-policy changes require:

- representative AXIGNAL eval set;
- quality comparison;
- groundedness evaluation;
- latency;
- token use;
- cost per useful task;
- tool/structured-output reliability;
- regression check;
- explicit policy version.

Do not change models merely because a new model exists.

---

# 14. UX states

Every important screen must define explicit states:

- initial;
- loading;
- partial;
- streaming;
- empty;
- unknown;
- stale;
- contradictory;
- unavailable;
- permission denied;
- degraded;
- failed;
- retrying;
- completed.

For germination specifically:

- queued;
- resolving;
- researching;
- interpreting;
- verifying;
- insufficient evidence;
- targeted reinvestigation;
- map-readiness evaluation;
- first-map ready;
- continuing observation.

The UI must never convert an epistemic state into a cosmetic success state.

---

# 15. Visual hierarchy

AXIGNAL should optimize for information density without cognitive overload.

Principles:

## Attention before completeness

Surface the few objects most deserving attention before exposing the complete universe.

## Semantic zoom

As the user moves deeper, increase information density and precision.

## Visual quiet

Do not use animation, glow, color or motion merely to make the system look intelligent.

Motion should communicate:

- change;
- germination;
- temporal evolution;
- focus;
- graph transition;
- causal/provenance traversal.

## Evidence confidence must not become decorative certainty

Visual treatment should distinguish epistemic class/currentness without presenting an opaque universal "truth score."

## Graph hairballs are product failures

A technically correct graph that cannot be cognitively parsed is a failed projection.

---

# 16. Subscriber review / challenge

Every material claim should be challengeable.

Action:

**Request review**

The review flow captures:

- wrong organization;
- outdated;
- wrong market;
- source incorrect;
- relationship disputed;
- optional explanation;
- optional submitted source/evidence.

Submission creates a review signal, not canonical truth.

```text
USER CHALLENGE
   |
CLAIM REVIEW REQUEST
   |
INDEPENDENT REINVESTIGATION
   |
STRUCTURED STATE
   |
JEV / POLICY
   |
UPHELD | REVISED | RETIRED | UNRESOLVED
```

> **A REVIEW REQUEST TRIGGERS INVESTIGATION, NOT MODIFICATION.**

---

# 17. Portability

The subscriber should be able to take a temporal projection outside the UI.

## Xeed.md

Human/agent-readable projection.

## Xeed.json

Machine-readable structured projection.

Both should include at minimum:

- schema/projection version;
- generated_at;
- organization/Xeed identity;
- scope;
- currentness;
- selected FAXTs;
- INXIGHTs;
- relationships;
- PATHXs;
- evidence references;
- epistemic states;
- fingerprint/hash.

They are projections, not canonical authority.

## Product MCP

External agents may query AXIGLAND through bounded read/query tools.

MCP is not canonical write authority.

---

# 18. Metrics

Avoid opaque UX/WOW scores.

Measure interpretable behaviors.

## Comprehension / activation

- `TIME_TO_FIRST_UNDERSTANDING`
- `TIME_TO_FIRST_DISCOVERY`
- `TIME_TO_FIRST_EVIDENCE_INSPECTION`
- `TIME_TO_FIRST_MAP_INTERACTION`
- `FIRST_MAP_OPEN_RATE`
- `DISCOVERY_OPEN_RATE`
- `EVIDENCE_DRILLDOWN_RATE`

## Germination

- `GERMINATION_WATCH_RATE`
- `GERMINATION_DISCOVERY_OPEN_RATE`
- `FIRST_MAP_READY_TO_OPEN_LATENCY`
- `FIRST_MAP_RETURN_RATE`

## Ask AXENT

- `ASK_AXENT_OPEN_RATE`
- `ASK_AXENT_QUERY_RATE`
- `ASK_AXENT_CONTEXTUAL_QUERY_RATE`
- `ASK_AXENT_FOLLOWUP_RATE`
- `ASK_AXENT_EVIDENCE_OPEN_RATE`
- `ASK_AXENT_DEEP_RESEARCH_REQUEST_RATE`

## Retention

- `RETURN_TO_XEED_7D`
- `RETURN_TO_XEED_30D`
- `CHANGE_FEED_OPEN_RATE`
- `EVOLUTION_OPEN_RATE`

## Cognitive economics

- `SUBSCRIBER_AI_COST_PER_XEED_MONTH`
- `SUBSCRIBER_AI_COST_PER_ACTIVE_USER`
- `COST_PER_AXENT_QUERY`
- `TOKENS_PER_AXENT_QUERY`
- `CACHED_CONTEXT_RATIO`
- `CONTEXT_REUSE_RATE`
- `COST_PER_USEFUL_AXENT_INTERACTION`

Metrics must preserve lineage and must not be interpreted as causation without supporting analysis.

---

# 19. Ask AXENT telemetry

Each cognitive request should record operational telemetry such as:

```text
request_id
subscriber_id [protected/private]
xeed_id
xignal_id

interaction_class
selected_object_types
context_object_count
context_tokens
cached_tokens
output_tokens

model
model_policy_version
reasoning_effort
processing_mode
latency

estimated_cost
actual_cost

evidence_reference_count
grounding_status
followup
research_escalation
outcome
```

Secrets and unnecessary PII must never enter model context or exported telemetry.

---

# 20. Cost doctrine

Low model pricing is an advantage, not permission for waste.

> **CHEAP_TOKENS_DO_NOT_JUSTIFY_BAD_CONTEXT_ARCHITECTURE**

The system should minimize context because narrow relevant context usually improves:

- grounding;
- latency;
- cost;
- inspectability;
- privacy;
- cognitive signal.

Normal contextual Ask AXENT should initially be treated as an included product capability unless measured economics prove otherwise.

Expensive future Deep Research may be governed separately if necessary.

Do not introduce arbitrary visible query quotas before real usage data demonstrates a need.

---

# 21. Security and privacy boundaries

Subscriber context must be authorization-scoped.

Hard rules:

- a subscriber may access only projections authorized for that account/Xeed;
- private subscriber state cannot silently become public AXIGLAND truth;
- model context is minimized;
- secrets never enter model context;
- unrelated subscriber data never enters another subscriber's context;
- Ask AXENT output cannot bypass AXIGLAND authorization;
- external agent access through MCP follows separate explicit authorization;
- exports are scoped temporal projections.

---

# 22. Relationship to AXIGNAL internal Admin

Do not confuse:

```text
AXIGNAL SUBSCRIBER EXPERIENCE
```

with:

```text
AXIGNAL INTERNAL ADMIN
```

Subscriber Experience is the customer-facing intelligence product.

Internal Admin is AXIGNAL's own operational/economic/epistemic/commercial observatory.

They may consume shared domain events/read models where appropriate, but they have different authorization, purposes and projections.

Neither UI is canonical AXIGLAND authority.

---

# 23. Architectural contracts required before implementation

P0-INTERACTION-01 should specify at least:

1. Subscriber Projection Contract
2. Germination Projection Contract
3. Evolution / Temporal Projection Contract
4. Attention / Material Change Contract
5. Evidence Drill-down Contract
6. Graph / Map Projection Contract
7. PATHX Presentation Contract
8. Ask AXENT Context Contract
9. Ask AXENT Response Contract
10. Ask AXENT Research Escalation Contract
11. Subscriber Authorization Contract
12. Portable Xeed Contract
13. Product MCP Read Contract
14. Cognitive Provider Policy Contract
15. Subscriber Cognitive Telemetry Contract

The UI should be built after these contracts are sufficiently stable.

---

# 24. Suggested implementation slices

## INTERACTION-01A — Subscriber projection semantics

Define what the subscriber may read and how canonical objects become human-facing read models.

## INTERACTION-01B — Germination experience

Define event-to-UX projection, states, discoveries and First Map reveal.

## INTERACTION-01C — Today / Attention

Define material-change and returning-user experience without opaque scoring.

## INTERACTION-01D — Explore

Define map/graph/corporate/economic-neighbourhood representations and semantic zoom.

## INTERACTION-01E — Evolution

Define temporal reconstruction and change projections.

## INTERACTION-01F — Evidence

Define explanation/provenance/source drill-down and Claim Review entry points.

## INTERACTION-01G — Ask AXENT

Define contextual retrieval, provider-agnostic grounding, response structure,
research escalation and telemetry.

## INTERACTION-01H — Portability

Define Xeed.md, Xeed.json and Product MCP.

## INTERACTION-01I — UX validation

Prototype and test comprehension, information density, navigation, germination and Ask AXENT with realistic high-density Xeed fixtures.

---

# 25. Hard invariants

```text
HUMAN_FIRST=YES
AXENT_WHEN_NEEDED=YES

ONE_CANONICAL_AXIGLAND=YES
SUBSCRIBER_UI_IS_PROJECTION=YES
ASK_AXENT_IS_PROJECTION_AND_ANALYSIS=YES

UI_IS_NOT_CANONICAL_AUTHORITY
LLM_IS_NOT_CANONICAL_AUTHORITY
MODEL_OUTPUT_IS_NOT_FAXT
USER_PROMPT_IS_NOT_CANONICAL_EVIDENCE

USER_MUST_NOT_LEARN_INTERNAL_ONTOLOGY_TO_RECEIVE_VALUE
LLM_ASSISTANCE_IS_NOT_REQUIRED_FOR_BASIC_COMPREHENSION
LLM_ASSISTANCE_IS_CONTEXTUAL_AND_ON_DEMAND
LLM_CONTEXT_IS_MINIMIZED_TO_RELEVANT_PROJECTION

GERMINATION_PROGRESS_MUST_REFLECT_REAL_STATE
LIVE_DOES_NOT_MEAN_DONE
UNKNOWN_IS_NOT_FALSE
UNKNOWN_PRIVATE_IS_NOT_RESEARCH_FAILURE
NOT_OBSERVABLE_IS_A_VALID_OUTCOME

EVERY_MATERIAL_ELEMENT_SHOULD_BE_EXPLAINABLE
EVERY_MATERIAL_EXPLANATION_SHOULD_BE_INSPECTABLE
CLAIM_REVIEW_TRIGGERS_INVESTIGATION_NOT_MODIFICATION

ECONOMIC_BRAIN_IS_GOVERNED_SYSTEM_NOT_PROVIDER
STRUCTURED_EVALUATORS_ARE_REPLACEABLE
DETERMINISM_FIRST_AND_ANSWERABILITY_GATED
MISSING_CONTEXT_ROUTES_TO_RESEARCH_OR_ABSTENTION
EXPLANATION_TRACE_REQUIRED_FOR_DERIVED_OPPORTUNITY
COMPOUNDING_REUSE_PRESERVES_PROVENANCE_AND_CURRENTNESS
MODEL_SELECTION_IS_POLICY_NOT_DOMAIN_AUTHORITY
PROVIDER_LIVE_USE_REQUIRES_SEPARATE_AUTHORITY

HUMAN_UI_AND_AGENT_SURFACES_READ_THE_SAME_AXIGLAND
PORTABLE_XEED_IS_PROJECTION_NOT_AUTHORITY
PRODUCT_MCP_IS_QUERY_SURFACE_NOT_CANONICAL_AUTHORITY

DATA_DENSITY_MUST_INCREASE_INSIGHT_NOT_COGNITIVE_LOAD
GRAPH_HAIRBALL_IS_NOT_SUCCESS
```

---

# 26. Provider and model policy boundary

Provider identity, model IDs, APIs, context limits and prices are mutable
operational policy, not product doctrine. They must not be stated as canonical
defaults here. Any future provider decision requires explicit authorization,
applicable rights, representative evaluation and a versioned policy. The
provider receives no canonical authority and no live use is authorized by
this spec.

---

# 27. Final product statement

The subscriber should not experience AXIGNAL as a database, a graph viewer or a chatbot.

They should experience:

> **an observing economic brain that reveals what activity may matter, what changed, which capabilities may be relevant, where the activity occurs, why AXIGNAL surfaced it, what evidence supports the explanation and what remains uncertain — then remembers valid knowledge so future investigations can build on it.**

The map makes the connected world inspectable; it is not the complete
customer value. Today surfaces relevant activity and change, Explore supports
demand/project/opportunity investigation, Evolution preserves temporal
comparison and reuse/revalidation, and Evidence provides the explanation trace.

The desired product relationship is:

```text
READ
  |
UNDERSTAND
  |
EXPLORE
  |
QUESTION
  |
ASK AXENT
  |
INSPECT EVIDENCE
  |
RETURN WHEN THE WORLD CHANGES
```

Human First is not a limitation on AXIGNAL's intelligence.

It is the mechanism by which that intelligence becomes economically useful.

---

# Public representation and experience (proposed)

When governed observations become available, Today, Explore, Evolution and
Evidence may connect economic reality, digital representation, demand,
opportunity, temporal memory and explanation. Search, generative, social/public
conversation and public reputation/experience remain distinct observation
families. This is future product semantics, not a claim that any surface or
feature is implemented.

Conceptually, Today may surface recent representation or experience changes;
Explore may inspect sources, recurring themes and affected products/locations;
Evolution may compare compatible periods and show instrument discontinuities;
Evidence may trace each derived signal to permitted observations and source
references. These are product-area responsibilities, not a committed
navigation or screen design.

Public-experience projections may explain recurring praise, issues, themes,
products/locations, company responses, anomalies and representation/experience
gaps. Every percentage is bounded to eligible observed reviews and a period;
source population, sample, classification coverage, uncertainty, instrument
and method version remain inspectable. A platform rating is shown as
source-reported, and a platform verification marker does not establish
authenticity. Reviews, classifications and gaps do not become FAXT.

Ask AXENT may answer questions such as “What are customers complaining about?”,
“Which products are involved?”, “Which sources and reviews support this?”,
“How did public experience change?”, “What was observed versus classified?”,
“How was this metric calculated?”, “Could this indicate a market need?” and
“What remains uncertain?”. It must trace answers to permitted source
references, observation times, instruments, classification versions and
deterministic formulas. It cannot invent reviews, decide reviewer honesty,
declare fraud, imply that a response solved a problem, or turn a review sample
into all customers. Further questions may ask why reputation changed, which
issues became more frequent, how experience compares with competitors, whether
a change is broad or source-specific, what remains a reviewer claim rather than
a business fact, and which part was evaluator-classified. Every answer remains
bounded to the observed sample and cannot assert customer-population
representativeness without independent evidence.

Public observations may be reused across relevant Xignals without being
counted more than once. Private first-party analytics remain tenant-private.
Review history, removal/currentness, raw-text rights, personal-data
minimization, subject resolution and uncertainty stay visible in the design
contract. No review response automation, reviewer profiles, CRM workflows,
provider integrations, UI implementation or score is authorized here.
