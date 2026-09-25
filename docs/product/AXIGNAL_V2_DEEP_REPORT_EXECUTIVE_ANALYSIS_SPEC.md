# AXIGNAL V2 --- DEEP REPORT & EXECUTIVE ANALYSIS

**Document version:** 1.0\
**Product generation:** AXIGNAL V2\
**Spec status:** PROPOSED\
**Implementation status:** PRE_IMPLEMENTATION\
**Document class:** PRODUCT_SPECIFICATION\
**Release doctrine:** FULL_VALUE_ONLY\
**Core protocol:** AXIGNAL Executive Analysis Protocol (AEAP)\
**Initial price hypothesis:** €49.95 per report\
**Authority:** AXIGLAND remains canonical. The report is an
evidence-bound analytical projection.

This candidate specification describes a proposed product generation. It
does not establish implementation, production readiness, or authorization to
begin implementation.

------------------------------------------------------------------------

# 0. Product definition

**AXIGNAL V2** turns a living Xeed into a systematic executive
investigation.

V1 observes and reconstructs the externally observable economic world
around an organization. V2 does something fundamentally different with
that accumulated knowledge: it **interrogates it**.

The customer is not buying a generic AI report, a prettier Xeed export,
a summary of public information, or access to a particular language
model.

The customer is buying:

> **A systematic, recursive and evidence-bound interrogation of the
> organization's observable economic world.**

Its intellectual core is **AEAP --- AXIGNAL Executive Analysis
Protocol**.

AEAP encodes what AXIGNAL must ask, what dimensions it must cross, what
answers deserve further questions, which alternative explanations must
be tested, when contradictions must be investigated, what evidence is
sufficient, when analysis must stop, and which findings deserve
executive attention.

The product promise is simple:

> **AXIGNAL does not just summarize what it knows. It asks the questions
> the evidence deserves.**

The intended reaction is:

> **"AXIGNAL has connected things about my economic environment that I
> had not connected myself --- and I can inspect why."**

------------------------------------------------------------------------

# 1. Full-value doctrine

AXIGNAL V2 will not be commercially released as an analytically
amputated MVP.

Engineering may proceed incrementally. Commercial value may not.

Internal slices are implementation units, not customer products.

``` text
INTERNAL ENGINEERING
    ↓
DeepReportProjection
    ↓
Deterministic Analytical Substrate
    ↓
AEAP
    ↓
Recursive Analysis
    ↓
Contradiction / Alternative Explanation
    ↓
Red Team
    ↓
Evidence Binding
    ↓
Executive Findings
    ↓
Executive Questions
    ↓
Premium Report
    ↓
FULL_VALUE_RELEASE_GATE
    ├── FAIL → NOT_PRODUCTION_READY
    └── PASS → AXIGNAL V2 RELEASE
```

**Full-value does not mean final forever.** AEAP will evolve. New
analytical modules will appear. Models will improve. V2.1 may outperform
V2.0.

Full-value means that the version sold to a customer must deliver the
complete proposition advertised for that version.

AXIGNAL will not use paying customers as substitutes for unfinished
product engineering.

------------------------------------------------------------------------

# 2. Relationship with AXIGNAL V1

V2 does not create a second company database.

``` text
AXIGLAND
    ↓
XEED
    ├── V1 Human Experience
    ├── Ask AXENT
    ├── Evolution
    ├── Evidence
    ├── MCP / portable projections
    └── V2 Deep Report
```

V2 reuses the canonical world already accumulated by V1.

V1, V2 and V3 are product generations and analytical surfaces over one public
canonical AXIGLAND. V2 is a report projection; it does not create a second
AXIGLAND or duplicate canonical Organization, Evidence, Relationship, FAXT,
INXIGHT or PATHX authority. V3's future private analytical plane is separately
tenant-scoped and is not a private AXIGLAND.

Ask AXENT — by AXIGNAL is a separate subscriber interaction layer, not V2.
Any future explanation of V2 findings through Ask AXENT remains subject to the
existing interaction and authorization contracts. Product MCP remains a
read/query projection and gains no canonical write authority from this spec.

This creates an important economic property:

> **The analytical value can grow faster than marginal research cost
> because V2 reuses knowledge already materialized in AXIGLAND.**

A mature Xeed can therefore produce a stronger report at lower
duplicated research cost than a newly discovered organization.

------------------------------------------------------------------------

# 3. Product boundaries

V2 may analyze:

-   observable economic identity;
-   capabilities;
-   markets;
-   economic neighbourhood;
-   observed relationships;
-   potential relationships;
-   corporate structure;
-   competitors and substitutes;
-   demand and supply signals;
-   temporal changes;
-   Representation Signals;
-   Representation Anomalies;
-   FAXTs;
-   INXIGHTs;
-   PATHXs;
-   contradictions;
-   currentness;
-   Knowledge Frontier;
-   observable structural dependencies;
-   observable concentrations and adjacencies.

V2 must not silently infer:

-   profit;
-   margins;
-   private sales pipeline;
-   private contract terms;
-   private churn;
-   internal strategy;
-   private customer profitability;
-   internal costs;
-   cash flow;
-   unobserved operational facts.

Those remain `UNKNOWN_PRIVATE` unless a future authorized private
product supplies them. That future product is AXIGNAL V3, not V2.

------------------------------------------------------------------------

# 4. Epistemic invariants

``` text
AXIGLAND_IS_CANONICAL_AUTHORITY

DEEP_REPORT_IS_A_PROJECTION

AEAP_IS_ANALYTICAL_POLICY_NOT_DOMAIN_TRUTH

MODEL_PROVIDER_IS_NOT_DOMAIN_AUTHORITY

MODEL_OUTPUT_IS_NOT_CANONICAL_TRUTH

EXECUTIVE_FINDING_IS_NOT_AUTOMATICALLY_FAXT

REPORT_NARRATIVE_CANNOT_MUTATE_AXIGLAND

USER_FEEDBACK_CANNOT_DIRECTLY_MUTATE_AXIGLAND

POTENTIAL_IS_NOT_OBSERVED

UNKNOWN_IS_NOT_FALSE

UNKNOWN_PRIVATE_MUST_NOT_BE_INFERRED_AS_FACT

CURRENTNESS_IS_INTRINSIC

CONTRADICTION_MUST_NOT_BE_SILENTLY_ERASED

MATERIAL_FINDINGS_REQUIRE_TRACEABLE_SUPPORT

NEW_EVIDENCE_REQUIRES_GOVERNED_RESEARCH_AND_CANONICALIZATION
```

------------------------------------------------------------------------

# 5. The analytical moat

A customer can buy access to a powerful frontier model and still obtain
poor analysis if the wrong questions are asked.

AXIGNAL's moat is therefore not:

> "We use the most expensive model."

It is:

``` text
AXIGLAND
+
TEMPORAL EVIDENCE
+
GRAPH STRUCTURE
+
XEED
+
DETERMINISTIC DATA ENGINEERING
+
AEAP
+
RECURSIVE QUESTION GRAPH
+
CONTRADICTION ANALYSIS
+
COUNTER-HYPOTHESIS TESTING
+
RED TEAM
+
EVIDENCE BINDING
+
EVALUATION HISTORY
```

A model is cognitive machinery inside this system.

The system decides what deserves cognition.

------------------------------------------------------------------------

# 6. Model policy

The analytical provider must be abstracted:

``` text
ExecutiveAnalysisProvider
    analyze(question, context, policy)
        → StructuredAnalysis
```

The current cognitive policy maps background work to OpenAI / GPT-6 Luna via
Batch where appropriate. V2 may use that current default policy for background
and deep analysis through `CognitiveProvider` / `ModelRouter` and the
provider-neutral `ExecutiveAnalysisProvider` contract. Model selection is
operational policy, not domain authority or a permanent dependency; it may
change through evaluated policy. Batch is appropriate for asynchronous work,
not a required architecture for every task. Interactive Ask AXENT remains a
separate subscriber role using the current Standard Responses policy in the
[Subscriber Experience specification](AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md).

The product must not be coupled semantically to Luna.

The preferred architecture is:

``` text
AEAP
 ↓
Many bounded analytical tasks
 ↓
Default cognitive provider
 ↓
Cognitive Escalation Gate
 ├── sufficient → continue
 └── justified → stronger provider/model
```

A stronger model is used only when evaluation demonstrates material
incremental value for the task class.

No model becomes canonical authority.

------------------------------------------------------------------------

# 7. Cognitive escalation

Potential escalation reasons:

-   unresolved competing hypotheses;
-   high-materiality synthesis with substantial ambiguity;
-   contradictory evidence that bounded passes cannot resolve;
-   instability across repeated analyses;
-   complex third-order graph synthesis;
-   Red Team exposes unresolved weaknesses;
-   structured evaluation indicates insufficient reasoning quality;
-   benchmark evidence shows a stronger provider materially improves
    this class.

Conceptual contract:

``` text
CognitiveEscalationDecision {
  task_id
  task_class
  materiality
  ambiguity
  contradiction_state
  stability
  evidence_coverage
  expected_incremental_value
  expected_incremental_cost
  decision
  target_policy?
  reason_codes[]
}
```

Escalation must be inspectable and measurable.

------------------------------------------------------------------------

# 8. DeepReportProjection

The model must never receive an indiscriminate AXIGLAND dump.

`DeepReportProjection` creates the bounded analytical state required by
AEAP.

Potential contents:

## Economic DNA

-   resolved organization identity;
-   observable economic identity;
-   capabilities;
-   products/services where observable;
-   markets;
-   geographies;
-   certifications;
-   public economic positioning;
-   observability.

## Graph state

-   observed relationships;
-   potential relationships;
-   historical relationships;
-   corporate relationships;
-   economic neighbourhood;
-   graph proximity;
-   relevant PATHXs;
-   material graph changes.

## Evidence state

-   FAXTs;
-   evidence bundles;
-   provenance;
-   source diversity;
-   observation timestamps;
-   currentness;
-   contradictions;
-   stale evidence;
-   unresolved evidence.

## Derived state

-   INXIGHTs;
-   Representation Signals;
-   Representation Anomalies;
-   economic-position features;
-   competitive overlap;
-   capability-demand compatibility;
-   market adjacency;
-   concentration;
-   structural dependencies;
-   temporal momentum where supported.

## Knowledge state

-   Knowledge Frontier;
-   gaps;
-   unresolved questions;
-   `UNKNOWN`;
-   `UNKNOWN_PRIVATE`;
-   `NOT_OBSERVABLE`;
-   exhausted research branches;
-   weak-evidence areas.

Every material object must retain stable references for later evidence
binding.

------------------------------------------------------------------------

# 9. Deterministic analytical substrate

The model should not perform work that deterministic computation can
perform more reliably.

Before cognitive analysis, AXIGNAL should compute where relevant:

-   canonical IDs;
-   deduplication;
-   temporal normalization;
-   relationship typing;
-   evidence grouping;
-   source diversity;
-   currentness features;
-   graph distances;
-   neighbourhood extraction;
-   meaningful graph features;
-   capability overlap;
-   market overlap;
-   demand/capability compatibility features;
-   temporal deltas;
-   concentration measures;
-   path enumeration and pruning;
-   contradiction candidates;
-   missing-data masks;
-   representation features;
-   reusable cross-dimensional tables.

Principle:

> **Python and graph logic construct the analytical substrate. Cognitive
> models interpret economic meaning.**

------------------------------------------------------------------------

# 10. AEAP --- AXIGNAL Executive Analysis Protocol

AEAP is not a prompt.

It is a versioned analytical program, for example:

`AEAP/1.0`

It defines:

-   analytical domains;
-   mandatory questions;
-   cross-data joins;
-   derived-question rules;
-   analytical depth;
-   materiality;
-   contradiction tests;
-   counter-hypotheses;
-   alternative explanations;
-   evidence sufficiency;
-   stopping conditions;
-   escalation;
-   Red Team requirements;
-   evidence binding;
-   report inclusion;
-   composition.

------------------------------------------------------------------------

# 11. Recursive analytical loop

``` text
OBSERVATION
    ↓
QUESTION
    ↓
RELEVANT STRUCTURED STATE
    ↓
ANALYSIS
    ↓
ANSWER / PATTERN / GAP / CONTRADICTION
    ↓
DOES IT GENERATE A MATERIAL QUESTION?
    ├── NO → CLOSE BRANCH
    └── YES
          ↓
       DERIVED QUESTION(S)
          ↓
       CROSS OTHER DIMENSIONS
          ↓
       TEST CONTRADICTIONS
          ↓
       TEST ALTERNATIVE EXPLANATIONS
          ↓
       MATERIAL?
       ├── NO → discard from executive layer
       └── YES
             ↓
          RED TEAM
             ↓
          EVIDENCE BINDING
             ↓
          EXECUTIVE FINDING CANDIDATE
```

The report is the result of a controlled analytical search tree, not a
single generation.

------------------------------------------------------------------------

# 12. Analytical Question Graph

``` text
AnalyticalQuestion {
  question_id
  protocol_version
  domain
  parent_question_id?
  triggering_object_refs[]
  required_input_types[]
  materiality
  expected_information_gain
  analysis_mode
  result_state
  derived_question_ids[]
  contradictions[]
  alternative_explanations[]
  evidence_refs[]
  stopping_reason?
}
```

The graph allows AXIGNAL to know:

-   why a question was asked;
-   what triggered it;
-   what it consumed;
-   what it found;
-   what questions followed;
-   why the branch stopped.

This trace becomes an asset for improving AEAP.

------------------------------------------------------------------------

# 13. AEAP analytical domains

The initial full-value V2 analytical surface should include, where
relevant and evidence-supported:

1.  **Observable Economic Identity**
2.  **Capability Structure**
3.  **Capability × Demand**
4.  **Market Position**
5.  **Economic Neighbourhood**
6.  **Observed Relationships**
7.  **Potential Relationships**
8.  **Corporate Structure**
9.  **Competitive Structure**
10. **Supply / Observable Dependency Structure**
11. **Representation Analysis**
12. **Representation Anomalies**
13. **Temporal Change**
14. **PATHX / Non-obvious Connections**
15. **Concentration**
16. **Adjacency**
17. **Contradiction Analysis**
18. **Alternative Explanation Analysis**
19. **Blind-Spot Analysis**
20. **Cross-Domain Synthesis**
21. **Executive Question Generation**
22. **Red Team**

Modules may conclude `NOT_APPLICABLE` or `INSUFFICIENT_EVIDENCE`. They
must not manufacture content to fill report sections.

------------------------------------------------------------------------

# 14. Cross-domain synthesis

This is one of V2's highest-value stages.

Required cross-analysis candidates include:

``` text
capability × demand
capability × competitor
market × relationship
relationship × time
corporate structure × relationship
representation × graph position
representation × capability
PATHX × demand
anomaly × source diversity
concentration × temporal change
knowledge gap × executive materiality
```

The objective is not to create more observations.

It is to discover evidence-supported patterns invisible from a single
dimension.

------------------------------------------------------------------------

# 15. Contradictions and counter-hypotheses

For each material candidate finding, AEAP must ask:

> **What is the strongest plausible alternative explanation supported by
> the available evidence?**

Then:

> **What evidence distinguishes the competing interpretations?**

Explicit contradiction searches include:

-   source disagreement;
-   temporal inconsistency;
-   entity-resolution conflict;
-   incompatible relationship states;
-   inconsistent capability/market representation;
-   observations contradicting the candidate conclusion.

Contradiction is an analytical object, not noise to suppress.

------------------------------------------------------------------------

# 16. Red Team

Every high-materiality candidate finding must survive adversarial
analysis.

Red Team attempts to identify:

-   correlation presented as causation;
-   weak evidence;
-   stale evidence;
-   doubtful entity resolution;
-   alternative explanations;
-   hidden private assumptions;
-   overgeneralization;
-   unsupported recommendation;
-   dependence on one weak source;
-   contradictions omitted by synthesis.

Outcomes:

``` text
SUPPORTED
PARTIALLY_SUPPORTED
INSUFFICIENT
CONTRADICTED
```

Only findings satisfying inclusion policy enter the executive headline
layer.

------------------------------------------------------------------------

# 17. ExecutiveFinding contract

``` text
ExecutiveFinding {
  finding_id
  title
  executive_statement
  why_it_matters
  epistemic_class
  support_state
  materiality_factors
  supporting_faxt_ids[]
  supporting_relationship_ids[]
  supporting_pathx_ids[]
  evidence_refs[]
  contradictory_evidence_refs[]
  alternative_explanations[]
  currentness
  unknowns[]
  red_team_result
  protocol_version
  analytical_trace_refs[]
}
```

Narrative is generated from structured findings, not the reverse.

------------------------------------------------------------------------

# 18. Materiality

AXIGNAL should not hide materiality behind a single opaque AI score.

Materiality may use inspectable factors such as:

-   economic relevance;
-   evidence strength;
-   novelty;
-   temporal relevance;
-   graph significance;
-   corroboration breadth;
-   potential executive consequence;
-   contradiction state;
-   representation impact;
-   uncertainty.

The system should be able to explain why a finding entered the report.

------------------------------------------------------------------------

# 19. Stopping conditions

Recursive analysis is bounded.

A branch stops when:

-   evidence is sufficient;
-   no materially new question emerges;
-   expected information gain is below policy threshold;
-   evidence is insufficient and no new research is authorized;
-   the question is `UNKNOWN_PRIVATE`;
-   the question is `NOT_OBSERVABLE`;
-   maximum analytical depth is reached;
-   compute budget is reached;
-   repeated passes add no material insight;
-   source/research space is exhausted.

A stopped branch may end in uncertainty. That is a valid result.

------------------------------------------------------------------------

# 20. Research escalation

Analysis of existing knowledge and acquisition of new evidence are
separate operations.

``` text
AEAP ANALYSIS
   ↓
MATERIAL RESOLVABLE GAP
   ↓
RESEARCH OBJECTIVE
   ↓
AXIGNAL RESEARCH LOOP
   ↓
NEW EVIDENCE
   ↓
GOVERNED CANONICALIZATION
   ↓
UPDATED AXIGLAND
   ↓
RESUME AEAP
```

AEAP cannot directly write truth.

------------------------------------------------------------------------

# 21. Report readiness

V2 must not compensate for a weak Xeed with eloquent prose.

Potential states:

``` text
REPORT_READY
REPORT_READY_WITH_LIMITATIONS
RESEARCH_REQUIRED
INSUFFICIENT_OBSERVABLE_EVIDENCE
```

Readiness should consider:

-   root identity;
-   Economic DNA;
-   capability coverage;
-   market coverage;
-   corporate structure where relevant;
-   relationship coverage;
-   evidence diversity;
-   currentness;
-   entity resolution;
-   representation coverage;
-   contradiction state;
-   analytical data sufficiency.

------------------------------------------------------------------------

# 22. Report architecture

The report must optimize comprehension rather than page count.

## Executive layer

1.  Executive Brief
2.  What AXIGNAL sees
3.  What AXIGNAL found
4.  What AXIGNAL did not expect
5.  Key Executive Findings
6.  Questions Your Leadership Team Should Be Asking

## Analytical layer

7.  Observable Economic Identity
8.  Economic Position
9.  Capabilities
10. Markets and Demand
11. Economic Neighbourhood
12. Observed Relationships
13. Potential Relationships
14. Corporate Structure
15. Competitive Environment
16. Observable Dependencies
17. PATHX / Non-obvious Connections
18. Representation Analysis
19. Representation Anomalies
20. Temporal Evolution
21. Concentrations and Adjacencies
22. Contradictions and Alternative Explanations
23. Blind Spots / What AXIGNAL Does Not Know

## Audit layer

24. Methodology
25. Epistemic Legend
26. FAXT / Evidence Appendix
27. Sources and Currentness
28. Analytical Limitations
29. Protocol and generation metadata

Sections appear only when justified.

------------------------------------------------------------------------

# 23. Signature section --- Questions Your Leadership Team Should Be Asking

This is a core V2 output.

Questions must be organization-specific and generated from evidence.

Each question includes:

-   why AXIGNAL is asking;
-   supporting FAXTs/relationships/PATHXs;
-   epistemic state;
-   contradictions;
-   currentness;
-   what AXIGNAL does not know;
-   what evidence could resolve it.

The desired reaction:

> **"I would not have thought to ask that."**

------------------------------------------------------------------------

# 24. Finding UX

Each material finding should expose:

**Executive interpretation**\
What AXIGNAL can responsibly conclude.

**Why this matters**\
Executive relevance.

**Why AXIGNAL sees this**\
Derivation.

**Evidence**\
FAXTs, observations, sources and graph objects.

**What could make this interpretation wrong**\
Alternative explanation / contradiction.

**Currentness**\
Current, historical, stale or unknown.

**Epistemic state**\
Observed, derived, potential, unresolved, etc.

**Explore in AXIGNAL**\
Deep link when supported.

------------------------------------------------------------------------

# 25. Premium PDF doctrine

The PDF is a first-class product surface.

It must provide:

-   excellent typography;
-   executive hierarchy;
-   high data density without overload;
-   meaningful whitespace;
-   deterministic charts;
-   graph/map views only when they answer a cognitive question;
-   PATHX diagrams;
-   timelines;
-   corporate trees;
-   evidence callouts;
-   currentness;
-   epistemic states;
-   concise provenance;
-   excellent screen and print rendering.

The model must not control arbitrary layout.

Structured report state feeds a deterministic report composer and
renderer.

------------------------------------------------------------------------

# 26. Product funnel

``` text
CUSTOMER REQUESTS V2
    ↓
RESOLVE / SELECT XEED
    ↓
GERMINATE OR REFRESH IF REQUIRED
    ↓
REPORT READINESS
    ↓
AEAP
    ↓
FULL-VALUE REPORT
    ↓
CUSTOMER EXPLORES FINDINGS
    ↓
LIVING XEED RETAINED / ACTIVATED
```

Core proposition:

> **The report is a deep analytical snapshot. The Xeed remains alive.**

------------------------------------------------------------------------

# 27. Recurring extension --- Executive Intelligence

A future recurring analytical product should focus on change:

> **What changed, why might it matter, and what questions should
> management now be asking?**

``` text
REPORT T-1
+
AXIGLAND T-1
+
AXIGLAND T
+
NEW EVIDENCE
+
CHANGED RELATIONSHIPS
+
NEW / RETIRED PATHXs
+
REPRESENTATION CHANGES
+
RESOLVED / NEW CONTRADICTIONS
    ↓
EXECUTIVE DELTA ANALYSIS
```

Do not repeatedly recompute unchanged analysis without information gain.

------------------------------------------------------------------------

# 28. Economics

Initial commercial hypothesis:

**€49.95 per AXIGNAL V2 Deep Report.**

This is a pricing hypothesis, not an architectural ceiling.

Track:

``` text
DEEP_REPORT_VARIABLE_COST
AEAP_COGNITIVE_COST
AEAP_COST_PER_ANALYTICAL_BRANCH
AEAP_COST_PER_SUPPORTED_FINDING
SUPPORTED_EXECUTIVE_FINDINGS_PER_EURO
NOVEL_SUPPORTED_FINDINGS_PER_EURO
REPORT_EVIDENCE_REUSE_RATIO
FRONTIER_ESCALATION_RATE
FRONTIER_ESCALATION_INCREMENTAL_VALUE
DEEP_REPORT_GROSS_MARGIN
```

Do not price from token cost alone.

Price from demonstrated customer value while preserving healthy unit
economics.

------------------------------------------------------------------------

# 29. Evaluation

The product must maintain a benchmark corpus of rich Xeeds.

Compare configurations such as:

-   AEAP + default model;
-   AEAP + stronger model;
-   AEAP + default model + selective escalation.

Evaluate:

-   non-obvious supported findings;
-   material usefulness;
-   unsupported claims;
-   contradictions detected;
-   alternative explanations;
-   second-/third-order connections;
-   evidence binding;
-   stability;
-   latency;
-   cost.

The benchmark decides model policy.

------------------------------------------------------------------------

# 30. AEAP learning

AEAP evolves through evidence.

Potential learning signals:

-   branches repeatedly producing no value;
-   branches yielding high-value supported findings;
-   useful cross-dimensional joins;
-   recurring contradiction patterns;
-   findings strengthened/weakened by later evidence;
-   executive questions repeatedly explored;
-   model disagreements;
-   escalation outcomes;
-   expert review.

Versions must be reproducible:

``` text
AEAP/1.0
AEAP/1.1
AEAP/2.0
```

Every report records its protocol version.

------------------------------------------------------------------------

# 31. FULL_VALUE_RELEASE_GATE

AXIGNAL V2 may be sold only when the advertised V2 contract passes E2E.
The following are future release requirements. None is asserted as passed or
implemented by this proposed specification.

``` text
AXIGNAL_V2_FULL_VALUE_RELEASE_GATE

CANONICAL_XEED_INPUT                 REQUIRED_NOT_YET_VALIDATED
REPORT_READINESS                     REQUIRED_NOT_YET_VALIDATED
DEEP_REPORT_PROJECTION               REQUIRED_NOT_YET_VALIDATED
DETERMINISTIC_ANALYTICAL_SUBSTRATE   REQUIRED_NOT_YET_VALIDATED
AEAP_CORE                            REQUIRED_NOT_YET_VALIDATED
RECURSIVE_QUESTION_GRAPH             REQUIRED_NOT_YET_VALIDATED
CROSS_DOMAIN_SYNTHESIS               REQUIRED_NOT_YET_VALIDATED
CONTRADICTION_ANALYSIS               REQUIRED_NOT_YET_VALIDATED
ALTERNATIVE_EXPLANATIONS             REQUIRED_NOT_YET_VALIDATED
RED_TEAM                             REQUIRED_NOT_YET_VALIDATED
EVIDENCE_BINDING                     REQUIRED_NOT_YET_VALIDATED
EXECUTIVE_FINDINGS                   REQUIRED_NOT_YET_VALIDATED
EXECUTIVE_QUESTIONS                  REQUIRED_NOT_YET_VALIDATED
EPISTEMIC_DISCIPLINE                 REQUIRED_NOT_YET_VALIDATED
CURRENTNESS                          REQUIRED_NOT_YET_VALIDATED
RESEARCH_ESCALATION                  REQUIRED_NOT_YET_VALIDATED
COGNITIVE_ESCALATION                 REQUIRED_NOT_YET_VALIDATED
REPORT_COMPOSER                      REQUIRED_NOT_YET_VALIDATED
PREMIUM_OUTPUT                       REQUIRED_NOT_YET_VALIDATED
COST_OBSERVABILITY                   REQUIRED_NOT_YET_VALIDATED
E2E_REALISTIC_VALIDATION             REQUIRED_NOT_YET_VALIDATED
```

Any critical failure:

`AXIGNAL_V2 = NOT_PRODUCTION_READY`

No public "MVP" substitutes for this gate.

------------------------------------------------------------------------

# 32. Proposed future implementation sequence

This sequence is a planning aid only. It authorizes no implementation work.
Engineering may be incremental; customer release remains full-value only.

``` text
V2-00  Authority reconciliation
V2-01  DeepReportProjection
V2-02  Deterministic analytical substrate
V2-03  Analytical Question Graph
V2-04  AEAP core modules
V2-05  ExecutiveFinding contract
V2-06  Contradiction / counter-hypothesis
V2-07  Red Team
V2-08  Research escalation
V2-09  Cognitive escalation
V2-10  Model bakeoff / eval harness
V2-11  Structured report composer
V2-12  Premium PDF renderer
V2-13  Security / privacy / export validation
V2-14  Full E2E evaluation
V2-15  FULL_VALUE_RELEASE_GATE
V2-16  Production release
```

No slice is itself a customer product.

------------------------------------------------------------------------

# 33. Success criteria

V2 succeeds when:

1.  material findings are traceable;
2.  it finds supported non-obvious connections;
3.  it asks organization-specific questions;
4.  it explicitly represents uncertainty;
5.  executives understand important findings quickly;
6.  analysts can inspect why;
7.  the report is visually premium;
8.  variable cost supports healthy economics;
9.  customers want to keep the Xeed alive;
10. quality comes from AEAP, not lucky prompting.

Conceptual quality function:

> **V2 VALUE = EVIDENCE × CONNECTION × NOVELTY × MATERIALITY ×
> EXPLAINABILITY**

------------------------------------------------------------------------

# 34. Product language

Preferred:

> **AXIGNAL doesn't just summarize your Xeed. It interrogates it.**

> **The value is not having more data. It is knowing what to ask of
> it.**

> **A systematic interrogation of your observable economic world.**

> **Evidence-bound executive analysis, built from a living Xeed.**

Do not sell:

> "Powered by the most expensive AI model."

The model is replaceable. The analytical system is the product.

------------------------------------------------------------------------

# 35. Canonical V2 thesis

> **AXIGNAL V2 converts a living Xeed into a systematic, recursive and
> evidence-bound executive investigation. Its primary intellectual
> property is AEAP: the analytical protocol that knows what to ask,
> which economic dimensions to cross, which answers deserve new
> questions, which hypotheses must be challenged, what evidence supports
> each finding, and when AXIGNAL does not know enough.**

And:

> **A frontier model can be purchased. A mature analytical protocol
> built on a living economic graph must be learned.**
