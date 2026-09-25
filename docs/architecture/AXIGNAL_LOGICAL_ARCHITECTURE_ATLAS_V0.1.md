# AXIGNAL --- Logical Architecture Atlas

**Status:** Pre-implementation architecture doctrine / Graphify input\
**Version:** 0.1\
**Date:** 2026-09-25\
**Scope:** Logical architectures, authority boundaries, closed loops,
state transitions, contracts, events, invariants and dependency
directions required for AXIGNAL before implementation-specific
architecture is frozen.\
**Authority:** Subordinate to the AXIGNAL Master Product Model,
Engineering Constitution, accepted ADRs and explicit CTO decisions.\
**Purpose:** Give Codex a sufficiently explicit logical model to
represent AXIGNAL faithfully in Graphify without prematurely choosing
libraries, storage topology, queues, databases, source providers or
implementation details.

------------------------------------------------------------------------

## 0. Executive thesis

AXIGNAL should not be represented in Graphify as a linear application
pipeline.

Its target architecture is a **closed-loop, evidence-governed, temporal
economic intelligence system** whose persistent output is AXIGLAND: one
canonical, demand-materialized representation of the observable economic
world.

The essential distinction is:

``` text
OBSERVATION != INTERPRETATION
INTERPRETATION != EVALUATION
EVALUATION != CANONICAL WRITE
CANONICAL STATE != USER PROJECTION
TRIGGER != AUTHORITY
RENDERER != MAP
SOURCE != TRUTH
MODEL != TRUTH
CUSTOMER INPUT != TRUTH
```

The architecture therefore requires explicit logical boundaries between:

1.  customer observation intent;
2.  research triggers;
3.  Knowledge Frontier;
4.  research planning;
5.  source acquisition;
6.  evidence/provenance;
7.  deterministic preprocessing;
8.  model interpretation;
9.  deterministic postprocessing/canonicalization;
10. JEV bounded evaluation;
11. uncertainty diagnosis;
12. targeted research loops;
13. canonical admission policy;
14. AXIGLAND;
15. temporal observation and revalidation;
16. map readiness;
17. semantic cartography;
18. subscriber projections;
19. Claim Review;
20. telemetry, economics and governance.

Graphify should make these boundaries and dependency directions visible.

------------------------------------------------------------------------

# PART I --- FOUNDATIONAL WORLD MODEL

## 1. One canonical AXIGLAND

AXIGNAL has one canonical economic world.

``` text
                         AXIGLAND
              canonical economic world
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
    Subscriber A     Subscriber B     Subscriber C
      projection       projection       projection
```

A subscriber does not own a company node.

A Xeed does not create a private company profile.

A Xignal does not create a second copy of an organization.

Different users may observe different projections of the same canonical
economic state.

### Invariants

``` text
ONE_ORGANIZATION != ONE_ORGANIZATION_PER_USER
PERSPECTIVE != PERMISSION_TO_REWRITE
SUBSCRIPTION != CANONICAL_AUTHORITY
XEED != PROFILE
XIGNAL != OWNERSHIP
```

------------------------------------------------------------------------

## 2. Demand-materialized world

AXIGNAL has a global ontology but does not need to precompute the whole
economy.

``` text
GLOBAL ONTOLOGY
      +
CANONICAL REUSABLE KNOWLEDGE
      +
USER / SYSTEM DEMAND
      ↓
TARGETED MATERIALIZATION
      ↓
AXIGLAND EXPANDS
```

Core doctrine:

> Compute once, learn permanently, verify when necessary.

The logical architecture must distinguish:

-   what AXIGNAL could know;
-   what AXIGNAL already knows;
-   what is worth learning next;
-   what has been materialized;
-   what is stale;
-   what is unknowable/private;
-   what is currently too expensive to resolve.

------------------------------------------------------------------------

## 3. Canonical reusable objects

Graphify should represent these as distinct logical concepts, not
collapse them into a generic `document`, `fact`, `edge` or `embedding`.

``` text
Organization
Observation
Evidence
ClaimCandidate
FAXT
INXIGHT
Relationship
CorporateLink
Capability
Product
Market
EconomicPath / PATHX
RepresentationSignal
RepresentationAnomaly
TemporalEvent
KnowledgeGap
ResearchQuestion
ResearchTrigger
ResearchJob
CognitiveJob
DecisionState
Xeed
Xignal
MapProjection
ClaimReviewRequest
```

### Critical separations

``` text
Observation != Evidence
Evidence != ClaimCandidate
ClaimCandidate != FAXT
FAXT != INXIGHT
Relationship != PATHX
ObservedRelationship != PotentialRelationship
RepresentationAnomaly != Error
Current != Historical
Unknown != False
```

------------------------------------------------------------------------

# PART II --- AUTHORITY ARCHITECTURE

## 4. Authority ladder

AXIGNAL needs an explicit authority model.

``` text
PUBLIC / PERMITTED SOURCES
          │
          ▼
      OBSERVATION
          │
          ▼
       EVIDENCE
          │
          ▼
 MODEL INTERPRETATION
          │
          ▼
STRUCTURED CANDIDATE STATE
          │
          ▼
   JEV EVALUATION
          │
          ▼
 AXIGNAL POLICY GATE
          │
          ▼
  CANONICAL AXIGLAND
```

No lower layer obtains authority merely by existing.

### Hard invariants

``` text
SOURCE_CONTENT_HAS_INSTRUCTION_AUTHORITY=NO
MODEL_HAS_CANONICAL_WRITE_AUTHORITY=NO
JEV_HAS_UNBOUNDED_CANONICAL_AUTHORITY=NO
PYTHON_HAS_SEMANTIC_TRUTH_AUTHORITY=NO
CUSTOMER_HAS_CANONICAL_EDIT_AUTHORITY=NO
RESEARCH_TRIGGER_HAS_CANONICAL_WRITE_AUTHORITY=NO
RENDERER_HAS_CANONICAL_AUTHORITY=NO
```

AXIGNAL-owned policy remains the final admission authority.

------------------------------------------------------------------------

## 5. Epistemic firewall

Every path from external information to canonical state crosses an
epistemic firewall.

``` text
EXTERNAL WORLD
     ↓
OBSERVATION
     ↓
PROVENANCE
     ↓
EVIDENCE LEDGER
     ↓
INTERPRETATION
     ↓
STRUCTURED EVALUATION
     ↓
CANONICAL POLICY
     ↓
AXIGLAND
```

The firewall must prevent:

-   a web statement becoming a fact merely because it exists;
-   customer-submitted information becoming truth;
-   model confidence becoming truth;
-   absence of evidence becoming false;
-   stale evidence becoming current;
-   a potential relation becoming observed;
-   infrastructure failure becoming semantic falsehood.

------------------------------------------------------------------------

# PART III --- RESEARCH TRIGGER ARCHITECTURE

## 6. Research triggers are attention, not truth

Research can begin for several reasons.

``` text
ResearchTriggerType

XEED_GERMINATION
GRAPH_EXPANSION
KNOWLEDGE_GAP
INSUFFICIENT_EVIDENCE
CONTRADICTION
CURRENTNESS_DECAY
REPRESENTATION_ANOMALY
CLAIM_REVIEW
MANUAL_RESEARCH_REQUEST
SOURCE_CHANGE
MAP_READINESS_FAILURE
```

All triggers enter the same research architecture.

``` text
             RESEARCH TRIGGERS
                    │
       ┌────────────┼─────────────┐
       │            │             │
      XEED       TEMPORAL       REVIEW
       │          DECAY           │
       ├─ GAP                      │
       ├─ CONTRADICTION            │
       ├─ ANOMALY                  │
       └─ EXPANSION                │
       │            │             │
       └────────────┼─────────────┘
                    ▼
             KNOWLEDGE FRONTIER
```

### Invariant

> A trigger can direct AXIGNAL's attention. It cannot direct AXIGNAL's
> conclusion.

------------------------------------------------------------------------

# PART IV --- KNOWLEDGE FRONTIER

## 7. Knowledge Frontier as central AXIGNAL IP

The Knowledge Frontier is the boundary between current supported
knowledge and economically useful missing knowledge.

Conceptual state:

``` text
KnowledgeGap {
    subject
    question
    decision_class
    current_evidence
    missing_information
    contradictions
    uncertainty
    economic_relevance
    expected_information_gain
    expected_cost
    reuse_potential
    freshness_need
    candidate_sources
    prior_attempts
    priority
    stop_reason?
}
```

It should be queryable at least by:

-   Organization;
-   Relationship;
-   CorporateLink;
-   Capability;
-   Product;
-   Market;
-   PATHX;
-   Xeed;
-   map-readiness dimension.

------------------------------------------------------------------------

## 8. Research priority

Initial conceptual policy:

``` text
Priority(job) =

InformationGain
× EconomicRelevance
× ReusePotential
× FreshnessNeed

────────────────────────────

ExpectedComputeCost
```

The exact formula is not frozen.

Graphify should represent the **dependency of scheduling on these
concepts**, not hard-code this provisional equation as permanent
doctrine.

------------------------------------------------------------------------

## 9. Stop conditions

Research is not infinite.

``` text
STOP WHEN:

EVIDENCE_SUFFICIENT
OR EXPECTED_INFORMATION_GAIN < THRESHOLD
OR BUDGET_EXHAUSTED
OR SOURCE_SPACE_EXHAUSTED
OR MAX_RESEARCH_DEPTH_REACHED
OR QUESTION_CLASSIFIED_UNKNOWN_PRIVATE
OR QUESTION_CLASSIFIED_NOT_OBSERVABLE
OR ADDITIONAL_SOURCES_REDUNDANT
OR RIGHTS_POLICY_BLOCKS_ACQUISITION
OR ANOTHER_REUSABLE_JOB_ALREADY_COVERS_THE_GAP
```

`UNKNOWN` is a valid output.

------------------------------------------------------------------------

# PART V --- SOURCE ACQUISITION ARCHITECTURE

## 10. Source acquisition is a replaceable organ

The Brain decides **what evidence is needed**.

The Source Router decides **where/how permitted evidence can be
acquired**.

``` text
RESEARCH QUESTION
       ↓
SOURCE REQUIREMENTS
       ↓
SOURCE ROUTER
       │
 ┌─────┼──────────┐
 ▼     ▼          ▼
GENERAL SPECIAL  MANAGED/
 WEB   SOURCE    FALLBACK
 │      │          │
 └──────┼──────────┘
        ▼
 RAW OBSERVATION
```

Candidate technologies must remain adapters until bakeoff evidence
selects roles.

Potential candidates include Scrapling, Agent Reach, ScrapeGraphAI and
future alternatives.

No candidate is architectural truth authority.

------------------------------------------------------------------------

## 11. Source Capability Contract

Conceptual:

``` text
SourceCapability {
    source
    backend
    public_access
    authentication_required
    commercial_use_status
    automation_status
    rate_limit
    evidence_class
    reliability
    currentness
    marginal_cost
    latency
    legal_status
    operational_risk
}
```

Fail closed:

``` text
UNKNOWN_LEGAL_STATUS != ALLOWED
```

Selection objective may consider:

``` text
VerifiableEvidenceYield
────────────────────────────────────────────
monetary_cost + compute_cost + latency_cost + operational_risk
```

but evidence quality and rights dominate blind yield optimization.

------------------------------------------------------------------------

# PART VI --- EVIDENCE ARCHITECTURE

## 12. Evidence Ledger

Every material observation should preserve provenance before it can
influence canonical state.

``` text
SOURCE
  ↓
RAW OBSERVATION
  ↓
PROVENANCE
  ↓
NORMALIZED EVIDENCE
  ↓
ENTITY LINK
  ↓
CLAIM CANDIDATE
```

Evidence needs temporal identity.

At minimum, logical provenance should be able to answer:

``` text
WHAT WAS OBSERVED?
WHERE?
WHEN?
BY WHICH ACQUISITION PATH?
WHAT EXACT ARTIFACT SUPPORTED IT?
WHAT NORMALIZATION OCCURRED?
WHAT CLAIM USED IT?
WHAT DECISION USED THAT CLAIM?
```

------------------------------------------------------------------------

## 13. Provenance chain

Every material graph element should support:

``` text
GRAPH ELEMENT
      ↓
DERIVATION
      ↓
FAXTs / STRUCTURED STATE
      ↓
EVIDENCE
      ↓
SOURCE
      ↓
OBSERVATION TIME
```

This is the foundation of:

> WHY AM I SEEING THIS?

The explanation must derive from stored provenance, not post-hoc
generative storytelling.

------------------------------------------------------------------------

# PART VII --- COGNITIVE RESEARCH LOOP

## 14. The central closed loop

This is the core logical architecture of the AXIGNAL Brain.

It is not:

``` text
CRAWLER → LLM → GRAPH
```

It is:

``` text
RAW EVIDENCE
     │
     ▼
PYTHON — STAGE 1
deterministic intake
     │
     ▼
GPT-6 LUNA BATCH
semantic interpretation
     │
     ▼
PYTHON — STAGE 2
canonicalization / structured state
     │
     ▼
JEV
bounded decision evaluation
     │
 ┌───┴─────────────────────┐
 │                         │
 ▼                         ▼
SUFFICIENT          INSUFFICIENT /
                    CONTRADICTORY /
                    AMBIGUOUS
 │                         │
 │                         ▼
 │                  STRUCTURED GAP
 │                         │
 │                         ▼
 │                  PYTHON — STAGE 3
 │                 next-action computation
 │                         │
 │                         ▼
 │                  GPT-6 LUNA BATCH
 │                  targeted research
 │                         │
 │                         ▼
 │                    SOURCE ROUTER
 │                         │
 │                         ▼
 │                    NEW EVIDENCE
 │                         │
 │                         └──────────────↺
 ▼
CANONICAL POLICY GATE
     │
     ▼
AXIGLAND
```

This loop must be explicit in Graphify.

------------------------------------------------------------------------

## 15. Python Stage 1 --- deterministic intake

Responsibilities may include:

-   parse;
-   normalize;
-   deduplicate;
-   timestamp;
-   source identity;
-   domain/identifier normalization;
-   artifact fingerprints;
-   basic extraction;
-   provenance attachment;
-   deterministic schema validation;
-   preparation of model input.

Python must not invent semantic truth.

------------------------------------------------------------------------

## 16. GPT-6 Luna Batch --- semantic interpretation

The model is used for cognitive interpretation of unstructured evidence.

Responsibilities may include:

-   understand natural language;
-   interpret economic meaning;
-   identify candidate entities;
-   identify candidate relationships;
-   extract candidate claims;
-   connect context across evidence;
-   identify contradictions;
-   identify ambiguity;
-   identify missing context;
-   formulate candidate research hypotheses;
-   structure semantic output for deterministic processing.

The model does not directly write AXIGLAND.

Provider abstraction is mandatory.

------------------------------------------------------------------------

## 17. Python Stage 2 --- canonicalization and state construction

After model interpretation, deterministic processing resumes.

Responsibilities may include:

-   canonical IDs;
-   entity-resolution features;
-   date normalization;
-   units/currency;
-   temporal interval operations;
-   evidence fingerprints;
-   deduplication;
-   graph features;
-   relationship candidate features;
-   contradiction sets;
-   source diversity features;
-   currentness features;
-   structured JEV input;
-   invariant checks.

This is why the architecture is not merely `Luna → JEV`.

------------------------------------------------------------------------

## 18. JEV --- bounded decision evaluation

JEV receives structured state whenever possible.

Candidate decision classes:

-   entity identity/resolution;
-   relationship nature;
-   observed vs potential;
-   currentness;
-   corporate-link classification;
-   evidence sufficiency;
-   contradiction handling inputs;
-   map-readiness subdecisions.

No universal `80%` threshold is doctrine.

Thresholds should eventually be calibrated by decision class.

Possible result taxonomy:

``` text
SUFFICIENT
INSUFFICIENT_EVIDENCE
AMBIGUOUS
CONTRADICTORY
STALE
NOT_OBSERVABLE
UNKNOWN_PRIVATE
POLICY_BLOCKED
```

The exact API is not frozen; the logical distinctions are required.

------------------------------------------------------------------------

## 19. Structured uncertainty

A failed decision must produce useful state, not merely a low score.

Conceptually:

``` text
DecisionGap {
    decision_class
    missing_information[]
    contradictions[]
    currentness_gap?
    source_diversity_gap?
    entity_ambiguity?
    framing_problem?
    intrinsically_uncertain?
    possible_resolvers[]
}
```

Low determinism may mean:

-   missing information;
-   ambiguity;
-   contradictory evidence;
-   poor decision framing;
-   stale evidence;
-   intrinsic uncertainty.

These must not be collapsed.

------------------------------------------------------------------------

## 20. Python Stage 3 --- next-action computation

Before spending more model/source compute, deterministic policy should
evaluate:

-   missing evidence;
-   contradiction classes;
-   currentness;
-   source coverage;
-   previous attempts;
-   expected information gain;
-   economic relevance;
-   reuse potential;
-   freshness need;
-   source rights;
-   remaining Xeed budget;
-   remaining research-loop budget;
-   duplicate active jobs;
-   stopping conditions.

Output:

``` text
NEXT_BEST_RESEARCH_ACTION
```

or:

``` text
STOP_WITH_EXPLICIT_UNCERTAINTY
```

------------------------------------------------------------------------

## 21. Luna targeted-research stage

When more research is justified, Luna can transform the structured gap
into a precise research objective.

Example:

``` text
BAD:
"search ACME again"

GOOD:
"Determine whether ACME currently distributes XYZ products in Spain,
with preference for current manufacturer directories, distributor
catalogues and independently observable corroboration."
```

This new research objective returns to Source Router.

That closes the loop.

------------------------------------------------------------------------

# PART VIII --- CANONICAL ADMISSION ARCHITECTURE

## 22. Canonical Commit Gate

A successful JEV decision is not necessarily identical to canonical
admission.

``` text
JEV RESULT
    ↓
AXIGNAL POLICY
    │
    ├─ provenance sufficient?
    ├─ rights permitted?
    ├─ decision class allowed?
    ├─ epistemic state valid?
    ├─ temporal semantics valid?
    ├─ invariants preserved?
    ├─ stable identity?
    └─ idempotency?
    ↓
CANONICAL COMMIT
```

Potential canonical outputs:

-   FAXT;
-   Relationship;
-   CorporateLink;
-   Capability;
-   Product;
-   Market;
-   TemporalEvent;
-   RepresentationSignal;
-   RepresentationAnomaly;
-   explicit UNKNOWN state where applicable.

------------------------------------------------------------------------

## 23. Idempotency

Repeated Batch results, retries or duplicate observations must not
create duplicate canonical truth.

``` text
RETRY != NEW FAXT
REPLAY != NEW RELATIONSHIP
BATCH_ORDER != IDENTITY
```

Canonical identity/fingerprints must be based on semantic/observation
identity, not provider execution ordering.

------------------------------------------------------------------------

# PART IX --- TEMPORAL ARCHITECTURE

## 24. Time is part of knowledge

AXIGNAL is not a static directory.

Logical temporal fields may include:

``` text
first_observed_at
last_observed_at
last_verified_at
valid_from
valid_until
currentness
```

Unknown temporal endpoints must remain unknown.

------------------------------------------------------------------------

## 25. Observation Loop

The Research Loop reduces uncertainty during an investigation.

The Observation Loop keeps AXIGLAND alive over time.

``` text
CANONICAL STATE
      ↓
TIME
      ↓
CURRENTNESS DECAY
      ↓
REOBSERVATION TRIGGER
      ↓
KNOWLEDGE FRONTIER
      ↓
RESEARCH LOOP
      ↓
NEW EVIDENCE
      ↓
UPHOLD / REVISE / RETIRE / UNRESOLVED
      ↓
AXIGLAND
      ↺
```

This loop is logically distinct from the intra-investigation Research
Loop.

------------------------------------------------------------------------

## 26. Temporal change

Canonical state should be append-oriented/auditable rather than silently
overwritten.

AXIGNAL should be able to distinguish:

``` text
CURRENTLY_OBSERVED
HISTORICAL
STALE
UNKNOWN_CURRENTNESS
```

and record material changes as `TemporalEvent` where appropriate.

------------------------------------------------------------------------

# PART X --- CLAIM REVIEW ARCHITECTURE

## 27. Claim Review is a trigger, not an edit path

``` text
CLIENT CHALLENGES CLAIM
        ↓
CLAIM_REVIEW_REQUEST
        ↓
RESEARCH TRIGGER
        ↓
KNOWLEDGE FRONTIER
        ↓
ADVERSARIAL REINVESTIGATION
        ↓
RESEARCH LOOP
        ↓
CANONICAL POLICY
        ↓
UPHELD | REVISED | RETIRED | UNRESOLVED
```

There is deliberately **no edge**:

``` text
CLAIM_REVIEW_REQUEST → CANONICAL_WRITE
```

------------------------------------------------------------------------

## 28. Submitted evidence

Customer-submitted material can be retained as evidence
candidate/context.

It must carry source relationship semantics such as:

``` text
SUBJECT_SUBMITTED
```

It may influence what AXIGNAL investigates.

It cannot independently satisfy a requirement for independent
corroboration where policy requires independence.

------------------------------------------------------------------------

## 29. Claim Review invariants

``` text
CUSTOMER_DISPUTED != FALSE
CLAIM_REVIEW != EDIT
REVIEW_REQUEST != CANONICAL_AUTHORITY
SUBMITTED_EVIDENCE != INDEPENDENT_EVIDENCE
REVISED != CUSTOMER_WON
UPHELD != AXIGNAL_DEFENDED_ITSELF
```

AXIGNAL follows evidence.

------------------------------------------------------------------------

# PART XI --- ECONOMIC GRAPH ARCHITECTURE

## 30. Graph layers

AXIGLAND projections must preserve distinct graph layers:

``` text
OBSERVED GRAPH
POTENTIAL GRAPH
ORGANIZATIONAL GRAPH
HISTORICAL GRAPH
ECONOMIC PATHS
```

They must not collapse into one undifferentiated edge set.

------------------------------------------------------------------------

## 31. Relationship semantics

Relationship nature is separate from:

-   epistemic class;
-   currentness;
-   materiality;
-   direction;
-   evidence;
-   confidence/decision state;
-   temporal validity.

Candidate relationship natures may include:

``` text
SUPPLIES
DISTRIBUTES
MANUFACTURES_FOR
PARTNERS_WITH
CUSTOMER_OF
CERTIFIED_BY
```

Corporate relations are separately governed.

------------------------------------------------------------------------

## 32. Corporate structure

Candidate corporate-link semantics include:

``` text
PARENT_OF
SUBSIDIARY_OF
BRAND_OF
DIVISION_OF
CONTROLLED_BY
JOINT_VENTURE
AFFILIATED_WITH
```

Corporate structure must not be inferred from mere commercial proximity.

------------------------------------------------------------------------

## 33. PATHX

PATHX is an explainable multi-edge economic path.

``` text
A ─relationship→ B ─relationship→ C
             ↓
           PATHX
```

It must never be silently rewritten as:

``` text
A ─direct relationship→ C
```

PATHX should retain constituent edges and their evidence.

------------------------------------------------------------------------

# PART XII --- REPRESENTATION INTELLIGENCE

## 34. Observable vs intended economic identity

AXIGNAL reconstructs externally observable economic position.

``` text
INTENDED_ECONOMIC_IDENTITY
        !=
OBSERVABLE_ECONOMIC_IDENTITY
```

The former may be private/unknown.

The latter is AXIGNAL's legitimate observation domain.

------------------------------------------------------------------------

## 35. RepresentationSignal

Conceptual:

``` text
RepresentationSignal {
    organization_id
    concept
    source_evidence[]
    external_corroboration[]
    derivation
    epistemic_class
    first_observed_at
    last_observed_at
    currentness
}
```

------------------------------------------------------------------------

## 36. RepresentationAnomaly

An anomaly means:

> the observable representation appears unexpectedly positioned relative
> to other evidence/state.

It does **not** mean:

``` text
AXIGNAL_ERROR
```

An anomaly should become an investigation point and can trigger targeted
research.

------------------------------------------------------------------------

# PART XIII --- XEED / XIGNAL ARCHITECTURE

## 37. Xeed

A Xeed is a persistent observation objective.

Conceptual state:

``` text
Xeed {
    xeed_id
    organization_id
    initiated_by
    created_at
    observation_depth
    research_budget
    compute_budget
    knowledge_frontier
    expansion_budget
    monitoring_policy
    last_observed_at
    next_observation_at
    readiness_state
    status
}
```

Planting a Xeed authorizes autonomous compute.

It does not authorize canonical influence.

------------------------------------------------------------------------

## 38. Xignal

A Xignal is a persistent observation focus.

``` text
XIGNAL != DUPLICATE ORGANIZATION
XIGNAL != EDITABLE PROFILE
XIGNAL != PRIVATE COPY OF AXIGLAND
```

Exact Xeed/Xignal lifecycle semantics may remain open until product
architecture freezes them.

Graphify should therefore represent the concepts and their boundary
without inventing a premature one-to-one implementation contract.

------------------------------------------------------------------------

# PART XIV --- XEED GERMINATION

## 39. Germination state machine

``` text
XEED_PLANTED
    ↓
RESOLVING
    ↓
OBSERVING
    ↓
RESEARCH_PLANNING
    ↓
BATCH_PREPARING
    ↓
BATCH_QUEUED
    ↓
BATCH_PROCESSING
    ↓
INGESTING
    ↓
NORMALIZING
    ↓
VERIFYING
    ↓
EXPANDING
    ↓
MAP_READINESS_GATE
    ├── FAIL → KNOWLEDGE_FRONTIER → TARGETED_RESEARCH ↺
    └── PASS → LIVE → NOTIFY → CONTINUOUS_CULTIVATION
```

`LIVE != DONE`.

------------------------------------------------------------------------

## 40. Germination phases

Conceptually:

``` text
G0 — Resolve
G1 — Economic DNA
G2 — Context
G3 — Observed Network
G4 — Selective Expansion
G5 — Potential Layer
G6 — Readiness / First Map
G7 — Continuous Cultivation
```

The exact implementation sequence can evolve, but Graphify should
preserve the dependency logic.

------------------------------------------------------------------------

# PART XV --- MAP READINESS ARCHITECTURE

## 41. FIRST_MAP_WOW is a quality gate

The renderer being able to draw nodes does not mean the map is ready.

Readiness dimensions include at least:

``` text
ROOT_IDENTITY
ECONOMIC_DNA
CAPABILITIES
MARKETS
CORPORATE_STRUCTURE
OBSERVED_RELATIONSHIPS
POTENTIAL_RELATIONSHIPS
EVIDENCE_DIVERSITY
ENTITY_RESOLUTION
GRAPH_DENSITY
EXPLANATION_COVERAGE
```

Possible dimension states:

``` text
READY
PARTIAL
BLOCKED
UNKNOWN
```

A failed dimension creates targeted Knowledge Gaps.

------------------------------------------------------------------------

## 42. Readiness feedback loop

``` text
MAP READINESS
      │
  ┌───┴───┐
  ▼       ▼
 PASS    FAIL
  │       │
  ▼       ▼
 LIVE   GAP GENERATION
          │
          ▼
   KNOWLEDGE FRONTIER
          │
          ▼
    RESEARCH LOOP
          ↺
```

This is another consumer of the same research engine, not a separate
crawler pipeline.

------------------------------------------------------------------------

# PART XVI --- COMPUTE ARCHITECTURE

## 43. Batch-first cognition

Primary cognitive execution policy:

``` text
AXIGNAL COGNITIVE CONTRACT
          ↓
MODEL PROVIDER ADAPTER
          ↓
GPT-6 LUNA BATCH
```

Batch should be treated as asynchronous architecture, not merely cheaper
synchronous inference.

The lower unit cost is reinvested in:

-   corroboration;
-   contradiction search;
-   broader discovery;
-   temporal verification;
-   selective multi-hop exploration;
-   targeted uncertainty reduction.

------------------------------------------------------------------------

## 44. Cognitive jobs

Conceptual:

``` text
CognitiveJob {
    job_id
    decision/research purpose
    input evidence refs
    structured context
    model contract
    budget
    idempotency key
    state
    output artifact refs
}
```

Batch provider IDs must not become canonical business identity.

------------------------------------------------------------------------

# PART XVII --- BUDGET ARCHITECTURE

## 45. Xeed budget

Conceptual dimensions:

``` text
XeedBudget {
    max_monetary_cost
    max_batch_input_tokens
    max_batch_output_tokens
    max_source_cost
    max_source_requests
    max_expansion_depth
    max_candidate_relationships
    max_research_loops
    deadline
}
```

Subscription tier may alter depth/frequency/budget.

It must not lower canonical truth standards.

------------------------------------------------------------------------

## 46. Marginal-value stopping

``` text
CONTINUE WHILE:

ExpectedMarginalKnowledgeValue
>
ExpectedMarginalCost
```

subject to hard policy, rights and plan ceilings.

------------------------------------------------------------------------

# PART XVIII --- REUSE ARCHITECTURE

## 47. Shared knowledge reuse

If two Xeeds need equivalent research:

``` text
XEED A ─┐
        ├─→ SHARED RESEARCH JOB → CANONICAL KNOWLEDGE
XEED B ─┘                              │
                                      ├→ projection A
                                      └→ projection B
```

Reuse should reduce future marginal compute.

No subscriber gains canonical authority by funding the research.

------------------------------------------------------------------------

# PART XIX --- CARTOGRAPHY ARCHITECTURE

## 48. Accepted logical renderer boundary

``` text
CANONICAL AXIGLAND
        ↓
AXIGNAL GRAPH PROJECTION
        ↓
AXIGNAL SEMANTIC CARTOGRAPHY
        ↓
AXIGNAL RENDERER CONTRACT
        ↓
SIGMA ADAPTER
        ↓
SIGMA + GRAPHOLOGY
        ↓
WEBGL
```

Current accepted principles:

``` text
ARCHITECTURE_DECISION=HYBRID
FOUNDATION_FRAMEWORK=NONE
SEMANTIC_CARTOGRAPHY_OWNER=AXIGNAL
INITIAL_RENDERER=Sigma + Graphology
RENDERER_REPLACEABLE=YES
RENDERER_CANONICAL_AUTHORITY=NO
```

Sigma draws pixels.

AXIGNAL owns the map.

------------------------------------------------------------------------

## 49. Semantic LOD

Semantic level of detail is AXIGNAL-owned.

Conceptual hierarchy:

``` text
WORLD
 ↓
SECTOR / MACROECONOMIC CONTEXT
 ↓
ECOSYSTEM
 ↓
ECONOMIC NEIGHBOURHOOD
 ↓
ORGANIZATION
 ↓
RELATIONSHIP / PATHX
 ↓
EVIDENCE
```

Zoom may be an input.

Zoom is not semantic authority.

------------------------------------------------------------------------

# PART XX --- PROJECTION ARCHITECTURE

## 50. Canonical state vs subscriber projection

``` text
CANONICAL AXIGLAND
        +
PRIVATE SUBSCRIBER CONTEXT
        +
VIEW PARAMETERS
        ↓
SUBSCRIBER PROJECTION
```

Private context may affect:

-   what is displayed;
-   which gaps are relevant;
-   which PATHX is useful;
-   research priority within policy;
-   observation focus.

It must not silently mutate canonical FAXTs.

------------------------------------------------------------------------

## 51. Focus / recenter

Clicking or recentering another organization changes perspective and may
create a new research objective.

``` text
RECENTER != REWRITE WORLD
```

A node can become new Hop0 without changing canonical truth.

------------------------------------------------------------------------

# PART XXI --- PRIVACY / OBSERVABILITY BOUNDARY

## 52. Observable domain

AXIGNAL may legitimately reconstruct from permitted external evidence:

-   identity;
-   public economic identity;
-   capabilities;
-   products/services;
-   certifications;
-   technologies where observable;
-   geographies;
-   markets;
-   publicly addressed buyers;
-   observed relationships;
-   corporate structure;
-   competitive/economic neighbourhood;
-   external representation;
-   temporal changes.

------------------------------------------------------------------------

## 53. Private/unobservable domain

AXIGNAL must not fabricate:

-   profit;
-   margins;
-   internal P&L;
-   private contract terms;
-   internal sales pipeline;
-   internal churn;
-   internal costs;
-   department performance;
-   private strategy;
-   private email sentiment;
-   CRM state.

Represent as appropriate:

``` text
UNKNOWN_PRIVATE
NOT_OBSERVABLE
UNKNOWN
```

------------------------------------------------------------------------

# PART XXII --- EVENT ARCHITECTURE

## 54. Conceptual domain events

Graphify should model event flow independently of a future queue
implementation.

Candidate events:

``` text
XEED_PLANTED
ORGANIZATION_RESOLVED
RESEARCH_TRIGGERED
KNOWLEDGE_GAP_OPENED
RESEARCH_JOB_SCHEDULED
SOURCE_OBSERVATION_ACQUIRED
EVIDENCE_NORMALIZED
COGNITIVE_JOB_PREPARED
BATCH_SUBMITTED
BATCH_RESULT_INGESTED
CLAIM_CANDIDATE_CREATED
JEV_DECISION_COMPLETED
DECISION_GAP_OPENED
TARGETED_RESEARCH_REQUESTED
KNOWLEDGE_GAP_RESOLVED
FAXT_ADMITTED
RELATIONSHIP_ADMITTED
TEMPORAL_CHANGE_DETECTED
REPRESENTATION_ANOMALY_DETECTED
CLAIM_REVIEW_REQUESTED
CLAIM_REVIEW_RESOLVED
MAP_READINESS_EVALUATED
FIRST_MAP_READY
XEED_LIVE
REOBSERVATION_SCHEDULED
SUBSCRIBER_NOTIFIED
```

Events requiring replay should be idempotent/replay-safe.

------------------------------------------------------------------------

# PART XXIII --- FAILURE SEMANTICS

## 55. Operational failure != epistemic state

``` text
Source unavailable
    → acquisition failure

Batch transport failure
    → compute failure

Evidence absent
    → UNKNOWN

Evidence contradictory
    → epistemic conflict

JEV insufficient
    → decision uncertainty

Entity collision
    → resolution uncertainty

Map readiness fail
    → insufficient first-map quality

Notification failure
    → notification failure only
```

Never:

``` text
INFRASTRUCTURE_FAILURE → FALSE
```

------------------------------------------------------------------------

# PART XXIV --- INTERNAL OBSERVABILITY

## 56. Brain telemetry

Internal Brain observability is distinct from the customer-facing
Observatory.

### Economics

-   cost per Xeed;
-   cost per first map;
-   cost per verified FAXT;
-   cost per accepted relationship;
-   model cost;
-   source cost;
-   marginal maintenance cost;
-   reuse savings.

### Intelligence

-   evidence yield;
-   evidence diversity;
-   corroboration rate;
-   contradiction rate;
-   entity-resolution uncertainty;
-   JEV insufficient rate;
-   targeted-loop success rate;
-   map-readiness dimensions;
-   explanation coverage.

### Reuse

-   canonical reuse;
-   relationship reuse;
-   source reuse;
-   compute avoided;
-   percentage of a new Xeed already known.

### Temporal

-   stale-state backlog;
-   reobservation yield;
-   state-change rate;
-   currentness coverage.

------------------------------------------------------------------------

# PART XXV --- LOGICAL SERVICE BOUNDARIES

## 57. Conceptual modules

These are logical responsibilities, not frozen deployable services.

``` text
Xeed Service
Research Trigger Intake
Knowledge Frontier
Research Planner
Compute Scheduler
Budget Controller
Source Router
Evidence Ledger
Normalization Pipeline
Entity Resolver
Batch Planner
Model Adapter
Result Ingestor
Structured State Builder
JEV Decision Layer
Decision Gap Analyzer
Canonical Policy Gate
Canonical Knowledge Writer
Temporal Engine
Representation Intelligence
Claim Review
AXIGLAND Graph Projection
Semantic Cartography
Map Readiness Engine
Observation Scheduler
Notification Service
Brain Telemetry
```

Codex/Graphify must not assume each logical module is a separate
microservice.

------------------------------------------------------------------------

# PART XXVI --- PROVIDER ABSTRACTION

## 58. Three strategic replaceable organs

``` text
COGNITION
AXIGNAL Cognitive Contract
        ↓
Provider Adapter
        ↓
GPT-6 Luna Batch / future

OBSERVATION
AXIGNAL Source Contract
        ↓
Source Adapter
        ↓
Scrapling / Agent Reach / ScrapeGraphAI / future

CARTOGRAPHY
AXIGNAL Renderer Contract
        ↓
Renderer Adapter
        ↓
Sigma + Graphology / future
```

AXIGNAL's moat lives above provider adapters.

------------------------------------------------------------------------

# PART XXVII --- DEPENDENCY DIRECTION

## 59. Desired logical dependency direction

``` text
PRODUCT DOCTRINE
      ↓
CANONICAL DOMAIN
      ↓
AXIGNAL POLICIES / CONTRACTS
      ↓
APPLICATION / ORCHESTRATION
      ↓
ADAPTER PORTS
      ↓
PROVIDERS / LIBRARIES
```

Never:

``` text
SCRAPER API
   ↓
defines AXIGNAL domain

MODEL RESPONSE FORMAT
   ↓
defines canonical truth

SIGMA TYPES
   ↓
define AXIGLAND

JEV IMPLEMENTATION DETAIL
   ↓
defines product ontology
```

------------------------------------------------------------------------

# PART XXVIII --- GRAPHIFY REPRESENTATION REQUIREMENTS

## 60. What Graphify must represent

Graphify should be able to expose at least:

### Domains

-   Canonical AXIGLAND
-   Research
-   Observation/Acquisition
-   Evidence
-   Cognition
-   Decision/Evaluation
-   Temporal
-   Claim Review
-   Xeed/Xignal
-   Cartography
-   Projection
-   Telemetry/Governance

### Authorities

For each component:

``` text
READS
PRODUCES
MAY_TRIGGER
MAY_EVALUATE
MAY_WRITE_CANONICAL
MUST_NOT_WRITE_CANONICAL
OWNS_POLICY
PROVIDER_SPECIFIC
AXIGNAL_OWNED
```

### Loops

Graphify must explicitly surface:

1.  Research Loop;
2.  Observation Loop;
3.  Map Readiness Repair Loop;
4.  Claim Review-triggered Reinvestigation;
5.  Graph Expansion Loop;
6.  Reuse/Deduplication Loop.

### Epistemic transitions

Graphify should make illegal transitions detectable.

Examples:

``` text
POTENTIAL → OBSERVED
```

must require authorized evidence/decision path.

``` text
HISTORICAL → CURRENT
```

must require reobservation/reverification.

``` text
CLAIM_REVIEW → CANONICAL_WRITE
```

must be illegal.

------------------------------------------------------------------------

# PART XXIX --- ARCHITECTURAL LOOPS

## 61. Loop A --- Research Loop

``` text
GAP
 ↓
RESEARCH QUESTION
 ↓
SOURCE ACQUISITION
 ↓
PYTHON₁
 ↓
LUNA
 ↓
PYTHON₂
 ↓
JEV
 ├─ sufficient → canonical policy
 └─ insufficient → Python₃ → Luna → targeted acquisition ↺
```

Purpose: reduce uncertainty economically.

------------------------------------------------------------------------

## 62. Loop B --- Observation Loop

``` text
CANONICAL STATE
 ↓
TIME
 ↓
CURRENTNESS DECAY
 ↓
REOBSERVATION
 ↓
RESEARCH LOOP
 ↓
UPHOLD / REVISE / RETIRE / UNRESOLVED
 ↓
CANONICAL STATE
 ↺
```

Purpose: keep AXIGLAND alive.

------------------------------------------------------------------------

## 63. Loop C --- Map Readiness Repair

``` text
MAP READINESS
 ↓
FAIL DIMENSION
 ↓
KNOWLEDGE GAP
 ↓
TARGETED RESEARCH
 ↓
NEW CANONICAL STATE
 ↓
MAP READINESS
 ↺
```

Purpose: maximize FIRST_MAP_WOW without cosmetic success.

------------------------------------------------------------------------

## 64. Loop D --- Claim Review

``` text
CHALLENGE
 ↓
REVIEW REQUEST
 ↓
RESEARCH TRIGGER
 ↓
ADVERSARIAL REINVESTIGATION
 ↓
RESEARCH LOOP
 ↓
UPHELD / REVISED / RETIRED / UNRESOLVED
```

Purpose: permit challenge without surrendering canonical authority.

------------------------------------------------------------------------

## 65. Loop E --- Graph Expansion

``` text
HOP0
 ↓
HIGH-VALUE HOP1
 ↓
SELECTIVE HOP2
 ↓
NEW KNOWLEDGE GAPS
 ↓
EXPECTED INFORMATION GAIN
 ├─ high → research
 └─ low → stop
```

Purpose: demand-driven economic-neighbourhood expansion.

------------------------------------------------------------------------

## 66. Loop F --- Reuse

``` text
NEW QUESTION
 ↓
CANONICAL KNOWLEDGE CHECK
 ├─ VALID REUSABLE KNOWLEDGE → reuse
 └─ GAP / STALE → research
                    ↓
               AXIGLAND LEARNS
                    ↺
```

Purpose: make later Xeeds cheaper and/or smarter.

------------------------------------------------------------------------

# PART XXX --- HARD ARCHITECTURAL INVARIANTS

## 67. Canonical invariants

The following should eventually become tests/contracts where technically
possible:

``` text
NO_USER_CLAIM_DIRECT_TO_FAXT
EVERY_MATERIAL_CANONICAL_CLAIM_HAS_PROVENANCE
UNKNOWN != FALSE
POTENTIAL != OBSERVED
HISTORICAL != CURRENT
PATHX != DIRECT_RELATIONSHIP
MODEL_OUTPUT != CANONICAL_TRUTH
SOURCE_CONTENT != INSTRUCTION_AUTHORITY
CUSTOMER_DISPUTE != FALSE
CLAIM_REVIEW != EDIT
PRIVATE_CONTEXT != CANONICAL_STATE
PROVIDER_ID != CANONICAL_IDENTITY
RETRY != NEW_FACT
INFRA_FAILURE != SEMANTIC_FALSEHOOD
RENDERER != CANONICAL_AUTHORITY
TRIGGER != CANONICAL_AUTHORITY
LIVE != DONE
SURPRISE != ERROR
```

------------------------------------------------------------------------

## 68. Research invariants

``` text
EVERY_RESEARCH_JOB_HAS_PURPOSE
EVERY_RESEARCH_JOB_HAS_BUDGET
EVERY_LOOP_HAS_STOP_CONDITION
INSUFFICIENT_STATE_PRESERVES_REASON
CONTRADICTION_IS_NOT_ERASED
TARGETED_RESEARCH_ADDRESSES_A_GAP
DUPLICATE_RESEARCH_IS_DEDUPED_WHERE_SAFE
SOURCE_RIGHTS_FAIL_CLOSED
```

------------------------------------------------------------------------

## 69. Temporal invariants

``` text
UNKNOWN_END_DATE_REMAINS_UNKNOWN
STALE_DOES_NOT_MEAN_FALSE
REOBSERVATION_DOES_NOT_ERASE_HISTORY
CURRENTNESS_IS_EXPLICIT
MATERIAL_CHANGE_IS_AUDITABLE
```

------------------------------------------------------------------------

# PART XXXI --- WHAT MUST REMAIN OPEN

## 70. Evidence-producing decisions still required

This architecture deliberately does not freeze:

-   final Source Acquisition stack;
-   exact role of Scrapling;
-   exact role of Agent Reach;
-   exact role of ScrapeGraphAI;
-   exact JEV skill/repository selection;
-   exact JEV integration API;
-   exact Python libraries;
-   exact entity-resolution implementation;
-   graph/database storage topology;
-   queue/orchestrator implementation;
-   exact batch sizing;
-   exact Xeed compute budgets;
-   calibrated JEV thresholds;
-   map-readiness numeric thresholds;
-   observation refresh frequencies;
-   exact Source Router scoring;
-   exact event transport;
-   exact notification provider;
-   final public/commercial UI.

These require dedicated bakeoffs or ADRs.

------------------------------------------------------------------------

# PART XXXII --- GRAPHIFY IMPLEMENTATION DOCTRINE

## 71. What Codex should do with this document

Codex should use this document to improve the **architecture graph**,
not to implement all components.

The intended flow is:

``` text
ARCHITECTURE DOCTRINE
        ↓
CODEX READ-ONLY RECON
        ↓
GRAPHIFY CURRENT-STATE GRAPH
        ↓
COMPARE:
CURRENT STATE
vs
TARGET LOGICAL ARCHITECTURE
        ↓
ADD / REFINE ARCHITECTURAL KNOWLEDGE
        ↓
GRAPHIFY
        ↓
ARCHITECTURE GAPS BECOME EXPLICIT
        ↓
FUTURE SLICES IMPLEMENT THEM
```

Graphify must distinguish:

``` text
CURRENTLY IMPLEMENTED
PLANNED / REQUIRED
ACCEPTED ARCHITECTURE
OPEN DECISION
PROVIDER CANDIDATE
FORBIDDEN DEPENDENCY
```

A target architecture node must never be represented as implemented
merely because it appears in this document.

------------------------------------------------------------------------

## 72. Graphify anti-hallucination rule

For every architecture element Codex maps:

``` text
IMPLEMENTATION_STATUS ∈ {
    IMPLEMENTED,
    PARTIALLY_IMPLEMENTED,
    SPECIFIED_NOT_IMPLEMENTED,
    ACCEPTED_NOT_IMPLEMENTED,
    OPEN_DECISION,
    EXPERIMENTAL,
    RETIRED
}
```

Codex should derive `IMPLEMENTED` only from repository evidence.

Documentation can establish intended/accepted architecture, not
implementation existence.

------------------------------------------------------------------------

# PART XXXIII --- TARGET META-ARCHITECTURE

## 73. Complete logical view

``` text
                              ┌────────────────────┐
                              │   USER / SYSTEM    │
                              │     TRIGGERS       │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ KNOWLEDGE FRONTIER │
                              └─────────┬──────────┘
                                        │
                              priority / budget
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ RESEARCH PLANNER   │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │   SOURCE ROUTER    │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ RAW OBSERVATIONS   │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │  EVIDENCE LEDGER   │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │     PYTHON₁        │
                              │ intake/normalize   │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │ GPT-6 LUNA BATCH   │
                              │ semantic cognition │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │     PYTHON₂        │
                              │ canonicalize/state │
                              └─────────┬──────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │       JEV          │
                              │ bounded evaluation │
                              └─────────┬──────────┘
                                        │
                       ┌────────────────┴────────────────┐
                       │                                 │
                       ▼                                 ▼
                  SUFFICIENT                      NOT SUFFICIENT
                       │                                 │
                       │                                 ▼
                       │                        ┌─────────────────┐
                       │                        │ STRUCTURED GAP  │
                       │                        └────────┬────────┘
                       │                                 │
                       │                                 ▼
                       │                        ┌─────────────────┐
                       │                        │    PYTHON₃      │
                       │                        │ next best action│
                       │                        └────────┬────────┘
                       │                                 │
                       │                                 ▼
                       │                        ┌─────────────────┐
                       │                        │      LUNA       │
                       │                        │ targeted query  │
                       │                        └────────┬────────┘
                       │                                 │
                       │                                 └────→ SOURCE ROUTER ↺
                       │
                       ▼
              ┌────────────────────┐
              │ CANONICAL POLICY   │
              │       GATE         │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │      AXIGLAND      │
              │ canonical temporal │
              │  economic world    │
              └──────┬─────┬───────┘
                     │     │
          ┌──────────┘     └────────────┐
          ▼                             ▼
 ┌─────────────────┐           ┌─────────────────┐
 │ MAP READINESS   │           │ TEMPORAL ENGINE │
 └────────┬────────┘           └────────┬────────┘
          │                             │
     fail │                             │ decay
          ▼                             ▼
 KNOWLEDGE FRONTIER              RESEARCH TRIGGER
          ↺                             ↺

              AXIGLAND
                  │
                  ▼
        AXIGNAL GRAPH PROJECTION
                  │
                  ▼
        SEMANTIC CARTOGRAPHY
                  │
                  ▼
         RENDERER CONTRACT
                  │
                  ▼
         SIGMA + GRAPHOLOGY
```

Claim Review enters through `RESEARCH TRIGGER`, never through
`CANONICAL POLICY GATE`.

------------------------------------------------------------------------

# PART XXXIV --- GRAPHIFY ACCEPTANCE CRITERIA

## 74. Minimum architecture coverage

A Graphify representation based on this document is incomplete if it
cannot answer:

1.  What can write canonical AXIGLAND?
2.  What cannot write canonical AXIGLAND?
3.  What triggers research?
4.  Where is the Knowledge Frontier?
5.  Where are budgets applied?
6.  Where are source rights checked?
7.  Where is provenance created/preserved?
8.  What does Python do before Luna?
9.  What does Luna do?
10. What does Python do after Luna?
11. What does JEV decide?
12. What happens when JEV cannot decide?
13. How does targeted research return to acquisition?
14. What stops the loop?
15. How does canonical admission occur?
16. How does currentness decay trigger reobservation?
17. How does Claim Review enter without editing truth?
18. How does map-readiness failure create research?
19. How does reuse avoid recomputation?
20. How is PATHX kept separate from direct relationships?
21. How are observed/potential/historical layers separated?
22. How does subscriber context remain outside canonical truth?
23. How is semantic cartography isolated from Sigma?
24. Which decisions remain open?
25. Which components are specified but not implemented?

------------------------------------------------------------------------

# PART XXXV --- FINAL DOCTRINE

## 75. Compact architecture doctrine

``` text
AXENT DECIDES WHAT NEEDS TO BE KNOWN.

THE KNOWLEDGE FRONTIER REPRESENTS WHAT IS MISSING.

THE RESEARCH PLANNER DECIDES WHAT IS WORTH LEARNING NEXT.

THE SOURCE ROUTER DECIDES WHERE AND HOW TO OBSERVE IT.

SOURCES PROVIDE OBSERVATIONS, NOT TRUTH.

PYTHON MAKES DATA AND STATE DETERMINISTIC.

LUNA INTERPRETS ECONOMIC MEANING.

PYTHON CANONICALIZES THE INTERPRETATION INTO STRUCTURED STATE.

JEV EVALUATES BOUNDED DECISIONS.

WHEN INFORMATION IS INSUFFICIENT,
PYTHON COMPUTES THE NEXT RESEARCH ACTION,
LUNA FORMULATES TARGETED INVESTIGATION,
AND THE LOOP RETURNS TO SOURCES.

AXIGNAL POLICY DECIDES WHAT MAY BECOME CANONICAL.

AXIGLAND REMEMBERS AND CONNECTS.

TIME REOPENS QUESTIONS.

CLAIM REVIEW REOPENS QUESTIONS.

MAP READINESS REOPENS QUESTIONS.

NO TRIGGER CAN WRITE TRUTH.

NO PROVIDER OWNS THE DOMAIN.

SIGMA DRAWS PIXELS.

AXIGNAL OWNS THE MAP.

THE RESULT IS NOT A REPORT PIPELINE.

IT IS A CLOSED-LOOP ECONOMIC OBSERVATION SYSTEM.
```

------------------------------------------------------------------------

## 76. Recommended next architectural action

This document should first be committed as architecture doctrine, then
Codex should:

1.  inspect the repository and current Graphify graph;
2.  classify every documented logical component as implemented, partial,
    accepted-not-implemented, specified-not-implemented, experimental or
    open;
3.  update Graphify architecture knowledge without pretending future
    components exist;
4.  add deterministic architecture invariants where they can be checked
    without runtime implementation;
5.  produce a gap ledger;
6.  stop.

Only after that reconciliation should AXIGNAL begin the Source
Acquisition Bakeoff.

This preserves the intended development order:

``` text
DOCTRINE
  ↓
GRAPHIFY ARCHITECTURAL MODEL
  ↓
GAP MAP
  ↓
SOURCE ACQUISITION BAKEOFF
  ↓
SOURCE ADR
  ↓
JEV
  ↓
PYTHON
  ↓
LUNA / BRAIN
  ↓
INTEGRATED CLOSED LOOP
```

The purpose is not to make Graphify dictate AXIGNAL.

The purpose is to ensure that, as implementation grows, Graphify can
continuously detect whether the codebase is converging toward or
drifting away from AXIGNAL's intended logical architecture.
