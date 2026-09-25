---
authority: Subordinate to AXIGNAL Master Product Model, Engineering
  Constitution, Accepted ADRs, and Logical Architecture Atlas
date: 2026-09-25
document_type: Product / Operational Governance Specification
implementation_status: PRE_IMPLEMENTATION
iteration_policy: Living specification; evolve by reviewed versioned
  changes as architecture and runtime evidence mature
status: PROPOSED
title: AXIGNAL Admin V0.1 --- Product & Governance Specification
version: 0.1
---

# AXIGNAL Admin V0.1 --- Product & Governance Specification

## 0. Executive definition

**AXIGNAL Admin is the operational, epistemic, economic and commercial
observatory of the machine that builds and evolves AXIGLAND.**

Its purpose is not merely to expose infrastructure telemetry or provide
a conventional backoffice. It is the human-first governance surface from
which AXIGNAL can be understood, operated, audited and economically
controlled end to end.

AXIGNAL Admin must make it possible to answer, without inspecting source
code, raw databases or a collection of unrelated third-party dashboards:

1.  Is AXIGNAL healthy?
2.  Is the business growing?
3.  Are customers receiving recurring value?
4.  Are Xeeds economically viable?
5.  Is AXIGLAND becoming more reusable and cheaper to extend?
6.  Is AXENT investigating the right questions?
7.  Is compute being converted into useful economic knowledge
    efficiently?
8.  Is AXIGLAND's observable knowledge sufficiently evidenced, current
    and explainable?
9.  What changed, when, why and with what impact?
10. Who or what changed AXIGNAL policy or operational state?
11. Can an authorized external agent understand the same administrative
    state without scraping the UI?

The governing product principle is:

> **AXIGLAND makes the observable economy inspectable. AXIGNAL Admin
> makes AXIGNAL itself inspectable.**

Admin is **Human First, Agent Ready**.

A human operator must be able to understand global health rapidly,
progressively drill into causes, and reach the underlying structured
observations. Agents must consume the same administrative projection
through bounded machine-readable interfaces rather than infer state from
screenshots.

------------------------------------------------------------------------

# 1. Scope and boundaries

## 1.1 What Admin governs

Admin V0.1 governs observability and controlled operations across:

-   AXIGNAL business performance;
-   first-party customer account and subscription observability for AXIGNAL's own service;
-   subscriptions and billing state;
-   Xeed lifecycle and economics;
-   AXENT research activity;
-   Knowledge Frontier;
-   cognitive compute;
-   source acquisition;
-   JEV evaluations when implemented;
-   AXIGLAND growth;
-   evidence and provenance quality;
-   currentness;
-   contradictions and epistemic state;
-   representation anomalies;
-   claim review;
-   infrastructure and provider health;
-   policies and budgets;
-   security and privileged actions;
-   alerts and incidents;
-   administrative exports and agent access.

## 1.2 What Admin is not

Admin is not:

-   canonical AXIGLAND authority;
-   a mechanism for manually writing economic truth;
-   authority over organizations represented in AXIGLAND or their private operational data;
-   evidence merely because an administrator entered something;
-   an LLM chat surface with unrestricted write access;
-   a substitute for domain services;
-   a source of public FAXTs;
-   a place where missing cost is silently represented as zero;
-   proof that a specified subsystem is implemented.

Customer Operations is limited to first-party operational state required to
run AXIGNAL as a service. It does not authorize CRM functionality or
representation of the private operations of organizations observed in
AXIGLAND.

## 1.3 Fundamental authority separation

``` text
AXIGLAND
= observable economic world

AXIGNAL ADMIN
= observable operational world of AXIGNAL
```

Therefore:

``` text
AXIGLAND FACT != ADMIN METRIC
ADMIN EVENT   != FAXT
ADMIN ACTION  != CANONICAL ECONOMIC TRUTH
```

------------------------------------------------------------------------

# 2. Human-first operating doctrine

Admin must optimize for comprehension before density.

Target interaction model:

-   **30 seconds:** determine whether AXIGNAL is healthy.
-   **2 minutes:** identify the subsystem or business dimension
    responsible for a material issue.
-   **5 minutes:** understand the causal chain and inspect supporting
    operational data.

Every major surface follows three levels:

### L1 --- Understand

What is happening?

### L2 --- Diagnose

Why is it happening?

### L3 --- Inspect

Show the underlying objects, events, measurements and lineage.

A material number must support the administrative equivalent of
AXIGLAND's "Why am I seeing this?":

> **WHY IS THIS NUMBER HERE?**

No material Admin metric should exist without inspectable lineage.

------------------------------------------------------------------------

# 3. Information architecture

Admin V0.1 is organized into eight primary domains plus one
cross-cutting projection layer.

``` text
AXIGNAL ADMIN
│
├── 01 COMMAND CENTER
├── 02 BUSINESS & CUSTOMER OPERATIONS
├── 03 XEED OBSERVATORY
├── 04 AXENT / RESEARCH
├── 05 AXIGLAND / DATA QUALITY
├── 06 ECONOMICS & UNIT ECONOMICS
├── 07 SYSTEM & PROVIDERS
├── 08 GOVERNANCE & AUDIT
│
└── ADMIN PROJECTION LAYER
    ├── Human UI
    ├── JSON
    ├── CSV
    ├── Markdown
    └── Agent Bridge / MCP
```

The UI is a projection, not the administrative data authority.

------------------------------------------------------------------------

# 4. Command Center

The Command Center is the default operational cockpit. It must surface
only the highest-value signals and material exceptions.

## 4.1 Business strip

At minimum:

-   MRR;
-   ARR;
-   paying customers;
-   active Xeeds;
-   average revenue per account;
-   average revenue per active Xeed;
-   MRR growth;
-   logo churn;
-   revenue churn;
-   Xeed churn;
-   expansion MRR;
-   contraction MRR;
-   failed/past-due revenue.

Time windows: 24h, 7d, 30d, 90d and custom where applicable.

## 4.2 Xeed strip

-   Xeeds planted;
-   resolving;
-   germinating;
-   researching;
-   map-readiness pending;
-   first-map-ready;
-   live;
-   reinvestigating;
-   stale;
-   degraded;
-   failed/blocked.

## 4.3 Economics strip

-   `COST_PER_ACTIVE_XEED_MONTH`;
-   average germination cost;
-   average maintenance cost;
-   variable cost ratio;
-   contribution per Xeed;
-   cognitive compute cost;
-   source acquisition cost;
-   JEV cost when available;
-   reuse ratio;
-   avoided recompute estimate with methodology/lineage.

## 4.4 Intelligence strip

-   research objectives created;
-   research runs completed;
-   useful research yield;
-   open Knowledge Frontier gaps;
-   gaps resolved;
-   new canonical FAXTs;
-   relationships added/updated;
-   currentness renewals;
-   contradictions opened/resolved.

## 4.5 Quality strip

-   evidence coverage;
-   provenance completeness;
-   explanation coverage;
-   currentness distribution;
-   contradiction rate;
-   entity-resolution ambiguity;
-   unsupported canonical writes --- expected invariant: **0**.

## 4.6 System strip

-   batch backlog;
-   source acquisition health;
-   provider health;
-   queue backlog;
-   error rate;
-   critical alerts;
-   open incidents.

------------------------------------------------------------------------

# 5. Business & Customer Operations

## 5.1 Purpose

Customer Operations exposes first-party AXIGNAL account and subscription
state needed to operate AXIGNAL as a service. This administrative
observability does not authorize CRM functionality.

Customer Operations must not become lead, prospect, opportunity, deal,
sales-stage, pipeline, salesperson-assignment, outreach, email-sequence,
follow-up-task, sales-intelligence, external-contact-enrichment, marketing
automation, customer-success workflow, arbitrary CRM-object, or external
company relationship management. Relationship notes must not become sales
intelligence. It does not represent a customer's own CRM and is not an
AXIGNAL customer-facing product capability. Any future CRM functionality
requires a separate explicit doctrine and ADR process; Admin V0.1 does not
authorize it.

## 5.2 Account model

``` text
ACCOUNT
├── identity
├── users
├── plan
├── subscription
├── Xeeds
├── billing
├── lifecycle
├── product usage
├── support
├── claim reviews
├── exports
├── MCP usage
└── commercial events
```

## 5.3 Customer 360

A customer view should expose:

-   account identity;
-   signup date;
-   plan;
-   subscription state;
-   MRR;
-   payment state;
-   active/cancelled Xeeds;
-   product activity;
-   first-map completion;
-   INXIGHT interaction;
-   evidence inspection;
-   PATHX interaction;
-   Ask AXENT — by AXIGNAL usage when implemented;
-   export usage;
-   product MCP usage;
-   Admin interactions only where relevant and authorized;
-   support events;
-   claim reviews;
-   total variable compute attributable;
-   contribution margin;
-   lifecycle events.

## 5.4 Product funnel

Canonical commercial funnel candidate:

``` text
VISITOR
→ SIGNUP
→ XEED PLANTED
→ GERMINATION COMPLETE
→ FIRST MAP VIEWED
→ FIRST INXIGHT VIEWED
→ EVIDENCE INSPECTED
→ ACTIVATED
→ PAID
→ RETAINED
→ EXPANDED
```

Exact activation semantics must be empirically calibrated and versioned.

## 5.5 Retention and cohorts

Track:

-   customer retention;
-   revenue retention;
-   Xeed retention;
-   cohort retention;
-   expansion;
-   contraction;
-   cancellation reasons;
-   time to cancellation;
-   reactivation.

Correlate, without confusing correlation with causation:

-   retention vs germination quality;
-   retention vs germination cost;
-   retention vs number/type of useful discoveries;
-   retention vs evidence inspection;
-   retention vs meaningful updates;
-   retention vs number of Xeeds.

## 5.6 FIRST_MAP_WOW instrumentation

Do not create an opaque WOW score.

Track interpretable behavioral proxies:

-   time to first map;
-   time to first understanding where measurable;
-   first INXIGHT opened;
-   evidence inspected;
-   map exploration;
-   node recenter;
-   PATHX inspected;
-   session depth;
-   return within 7/30 days;
-   Xeed retained;
-   additional Xeed planted;
-   explicit feedback when collected.

------------------------------------------------------------------------

# 6. Xeed Observatory

## 6.1 Xeed summary

Every Xeed should expose:

-   Xeed ID;
-   focal organization;
-   lifecycle state;
-   planted/germinated timestamps;
-   currentness;
-   last material change;
-   next observation;
-   map-readiness state;
-   open frontier;
-   contradictions;
-   representation anomalies;
-   FAXTs;
-   relationships;
-   INXIGHTs;
-   PATHXs;
-   evidence coverage;
-   monthly cost;
-   cumulative germination cost;
-   maintenance cost;
-   reuse contribution.

## 6.2 Lifecycle

``` text
PLANTED
→ RESOLVING
→ GERMINATING
→ RESEARCHING
→ MAP_READINESS
→ FIRST_MAP_READY
→ LIVE
↔ OBSERVING
↔ REINVESTIGATING
→ STALE / PARTIAL / DEGRADED where applicable
```

Lifecycle states must be explicit and machine-readable. A Xeed must
never appear healthy merely because an asynchronous job silently
stopped.

## 6.3 Xeed economics

Each Xeed requires a decomposable economic ledger:

``` text
XEED ECONOMICS
├── attributable revenue
├── germination cost
├── maintenance cost
├── refresh/currentness cost
├── research cost
├── source acquisition cost
├── cognitive compute cost
├── JEV cost
├── storage cost
├── delivery cost
├── triggered cost
├── attributed cost
├── shared cost
├── reused knowledge
└── avoided recompute
```

### Triggered cost

Cost caused by investigation initiated for the Xeed.

### Attributed cost

Cost economically attributed to the Xeed after reuse/allocation
semantics.

### Shared cost

Cost of knowledge or infrastructure serving multiple Xeeds.

### Avoided recompute

A methodologically explicit estimate of work avoided because reusable
AXIGLAND knowledge already existed.

Triggered cost and attributed cost must not be conflated.

------------------------------------------------------------------------

# 7. Economics & unit economics

## 7.1 Primary unit metric

The primary recurrent unit metric is:

`COST_PER_ACTIVE_XEED_MONTH`

Its denominator is an active customer-facing Xeed-month under a separately
governed activation definition. It must be decomposable by category, provider,
research run and Xeed. This Admin service-unit metric is distinct from MASTER
§42's `COST_PER_LIVE_XIGNAL`, which measures the cost of maintaining a
persistent Xignal observation allocation (MASTER §§4.4, 7). The metrics have
different units and scopes; no conversion or substitution is implied without a
separately governed mapping. See the [Admin Observability Architecture](../architecture/AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md).

Related metrics:

-   revenue per active Xeed;
-   contribution per active Xeed;
-   variable cost ratio;
-   marginal Xeed cost;
-   germination cost;
-   maintenance cost;
-   refresh cost;
-   cost per material update.

## 7.2 Cost taxonomy

``` text
COGNITIVE
  model batch
  synchronous model calls
  other cognitive providers

DECISION
  JEV

ACQUISITION
  HTTP
  browser
  proxy
  licensed/external data

COMPUTE
  application
  workers
  graph
  batch infrastructure

STORAGE
  database
  raw evidence
  objects
  logs

DELIVERY
  email
  CDN
  external APIs

PAYMENTS
  payment processor fees

OTHER VARIABLE
```

Each cost must also be classified where possible as:

-   VARIABLE;
-   SEMI_VARIABLE;
-   FIXED;
-   SHARED;
-   UNKNOWN.

**UNKNOWN COST != ZERO COST.**

## 7.3 Germination economics

Track:

-   germinations initiated/completed;
-   success rate;
-   median cost;
-   P50/P90/P99 cost;
-   median duration;
-   P50/P90/P99 duration;
-   map-readiness pass rate;
-   research iterations per Xeed;
-   sources per Xeed;
-   evidence per Xeed;
-   FAXTs per Xeed;
-   relationships per Xeed;
-   INXIGHTs per Xeed;
-   PATHXs per Xeed.

Analyze relationships between:

-   germination cost and retention;
-   germination depth and retention;
-   cost and evidence quality;
-   cost and graph density;
-   cost and useful product interaction.

Cheaper germination is not automatically better germination.

## 7.4 Knowledge economics

Track components rather than one opaque score:

-   new FAXTs;
-   corroborated FAXTs;
-   resolved gaps;
-   resolved contradictions;
-   discovered relationships;
-   verified relationships;
-   renewed currentness;
-   corporate links;
-   capabilities;
-   markets;
-   Representation Signals;
-   PATHXs enabled;
-   reusable evidence produced.

Derived operational metrics may include:

-   `KNOWLEDGE_GAIN_PER_EURO`;
-   `USEFUL_RESEARCH_YIELD`;
-   `EVIDENCE_REUSE_RATE`;
-   `COMPUTE_REUSE_RATE`;
-   `COST_PER_RESOLVED_GAP`;
-   `COST_PER_CANONICAL_FAXT`;
-   `COST_PER_MATERIAL_UPDATE`.

No aggregate knowledge score may hide its dimensions.

## 7.5 Flywheel Observatory

AXIGNAL must be able to test the hypothesis:

``` text
AXIGLAND KNOWLEDGE ↑
→ REUSE ↑
→ DUPLICATED RESEARCH ↓
→ MARGINAL COMPUTE ↓
→ COST / XEED ↓
→ MORE XEEDS ECONOMICALLY VIABLE
→ AXIGLAND KNOWLEDGE ↑
```

Track longitudinally:

-   canonical organizations;
-   FAXTs;
-   evidence objects;
-   relationships;
-   reusable evidence;
-   overlap between Xeeds;
-   reuse;
-   duplicate research avoided;
-   marginal compute;
-   marginal cost per Xeed;
-   research yield.

Key metric:

`AXIGLAND_REUSE_RATIO`

This measures how much knowledge required by a Xeed was already
available and reusable rather than newly recomputed.

------------------------------------------------------------------------

# 8. AXENT / Research Observatory

## 8.1 Purpose

Expose AXENT's structured operational reasoning state without exposing
hidden chain-of-thought.

A research run should make visible:

-   trigger;
-   Xeed;
-   objective/question;
-   reason for investigation;
-   expected information gain;
-   economic relevance;
-   reuse potential;
-   freshness need;
-   budget;
-   consumed cost;
-   attempts;
-   evidence acquired;
-   current decision state;
-   missing information;
-   contradictions;
-   stopping reason;
-   next structured action.

## 8.2 Research funnel

``` text
QUESTIONS GENERATED
→ QUESTIONS INVESTIGATED
→ EVIDENCE FOUND
→ STRUCTURED CLAIMS
→ JEV SUFFICIENT / STRUCTURED DECISION
→ POLICY ACCEPTED
→ CANONICAL KNOWLEDGE
```

Track conversion and loss between stages.

## 8.3 Research failure / stopping taxonomy

At minimum:

-   `SOURCE_UNAVAILABLE`
-   `SOURCE_POLICY_DENIED`
-   `ROBOTS_DENIED`
-   `FETCH_TIMEOUT`
-   `BROWSER_REQUIRED`
-   `ENTITY_AMBIGUOUS`
-   `INSUFFICIENT_EVIDENCE`
-   `CONTRADICTORY_EVIDENCE`
-   `UNKNOWN_PRIVATE`
-   `NOT_OBSERVABLE`
-   `BUDGET_EXHAUSTED`
-   `SOURCE_SPACE_EXHAUSTED`
-   `LOW_INFORMATION_GAIN`
-   `MODEL_FAILURE`
-   `JEV_UNRESOLVED`
-   `POLICY_REJECTED`
-   `DUPLICATE_KNOWLEDGE`

`FAILED` alone is insufficient.

## 8.4 Knowledge Frontier Observatory

Expose unresolved knowledge by:

-   domain;
-   Xeed;
-   economic relevance;
-   observability;
-   currentness;
-   contradiction;
-   expected information gain;
-   estimated research cost;
-   reuse potential.

Possible states include:

-   RESOLVED;
-   PARTIALLY_RESOLVED;
-   CONTRADICTED;
-   STALE;
-   UNKNOWN;
-   UNKNOWN_PRIVATE;
-   NOT_OBSERVABLE.

------------------------------------------------------------------------

# 9. AXIGLAND / Data Quality Observatory

## 9.1 No universal quality score

Data quality must be represented through independent dimensions.

## 9.2 Evidence coverage

Percentage/distribution of material graph elements supported by adequate
evidence.

## 9.3 Evidence diversity

Diversity and independence of sources supporting material claims.

## 9.4 Currentness

Track:

-   CURRENT;
-   AGING;
-   STALE;
-   UNKNOWN_CURRENTNESS.

Currentness policy must be explicit and versioned.

## 9.5 Contradictions

Track:

-   open contradictions;
-   contradiction age;
-   affected organizations/claims;
-   resolved contradictions;
-   resolution mechanism;
-   recurring source/domain patterns.

## 9.6 Entity resolution quality

Track:

-   unresolved candidates;
-   ambiguous resolutions;
-   duplicate organizations;
-   merges/splits;
-   reversals;
-   high-risk identity collisions.

## 9.7 Explanation coverage

Measure whether material graph elements can answer:

> **WHY AM I SEEING THIS?**

## 9.8 Provenance completeness

For material knowledge, verify reconstructability of:

``` text
GRAPH ELEMENT
→ DERIVATION
→ FAXT
→ EVIDENCE
→ SOURCE
→ OBSERVATION TIME
```

## 9.9 Epistemic distribution

Expose distribution and change over time across:

-   OBSERVED;
-   CORROBORATED;
-   INFERRED;
-   POTENTIAL;
-   CONTRADICTED;
-   STALE;
-   UNKNOWN;
-   UNKNOWN_PRIVATE;
-   NOT_OBSERVABLE.

Unexpected shifts, such as a sharp rise in inference relative to
observation, should be diagnosable.

## 9.10 Unsupported-claim protection

Track operational indicators such as:

-   canonical claims without evidence lineage;
-   inference without structured derivation;
-   unsupported relationships;
-   model outputs rejected by canonicalization;
-   later contradictions;
-   claim reviews ending REVISED/RETIRED;
-   entity-resolution reversals;
-   evidence mismatches.

Hard invariant target:

`UNSUPPORTED_CANONICAL_WRITE = 0`

------------------------------------------------------------------------

# 10. Claim Review & Representation

## 10.1 Claim Review Observatory

States:

-   OPEN;
-   INVESTIGATING;
-   UPHELD;
-   REVISED;
-   RETIRED;
-   UNRESOLVED.

Metrics:

-   volume;
-   age;
-   resolution time;
-   cost;
-   evidence added;
-   category;
-   source patterns;
-   outcome distribution;
-   recurring failure patterns.

A customer dispute is a research trigger, not a canonical correction.

## 10.2 Representation Observatory

Track, as the underlying product architecture supports them:

-   Representation Signals;
-   Representation Anomalies;
-   Human Web Representation;
-   Search Representation;
-   Agent Representation;
-   Structured Web Representation;
-   inconsistencies;
-   temporal evolution.

Authorized private sources must remain explicitly separated from public
canonical AXIGLAND reality.

------------------------------------------------------------------------

# 11. System & Provider Observatory

## 11.1 System health

Observe:

-   queues;
-   workers;
-   batches;
-   source adapters;
-   application services;
-   databases;
-   graph infrastructure;
-   evidence storage;
-   email;
-   payments;
-   scheduled observation;
-   background jobs.

Metrics:

-   health;
-   throughput;
-   latency;
-   error rate;
-   backlog;
-   P50/P90/P99 where meaningful.

## 11.2 Cognitive provider economics

Per provider/model:

-   requests/jobs;
-   batches;
-   tokens/usage;
-   measured cost;
-   failure rate;
-   latency;
-   useful output rate;
-   cost per useful resolved research objective.

Do not optimize solely for cost per token.

## 11.3 Batch Observatory

Track:

-   submitted;
-   pending;
-   running;
-   completed;
-   failed;
-   partial;
-   age;
-   cost;
-   research objectives;
-   Xeeds affected;
-   useful knowledge produced.

Support lineage:

`Batch → Research Runs → Evidence → Knowledge produced`.

## 11.4 Source Observatory

Per source/domain/adapter:

-   requests;
-   success;
-   denial;
-   policy/robots outcome;
-   timeout;
-   bytes;
-   evidence yield;
-   useful evidence;
-   cost;
-   currentness contribution;
-   duplicate evidence;
-   browser escalation;
-   policy violations prevented.

Sources provide observations, not canonical truth.

## 11.5 V2 / Deep Report observability

AXIGNAL V2 remains `PROPOSED / PRE_IMPLEMENTATION`. Future Admin projections
may expose report lifecycle, Xeed/report readiness, projection and AEAP versions,
analytical branch counts and stopping reasons, contradictions, alternative
explanations, Red Team outcomes, supported-finding counts, escalation, latency,
cost and evidence reuse. These are observability requirements, not runtime
claims. Admin does not author V2 findings or their epistemic state.

## 11.6 V3 private operational observability

AXIGNAL V3 remains `PROPOSED / PRE_IMPLEMENTATION`. Future Admin projections
may expose connection and adapter state, authorized capability/scope metadata,
revocation and retention/deletion state, private-operation cost, report
lifecycle and security events. Operational metadata does not grant access to
private observations, documents, prompts, model context or Private Findings.
Private-content inspection, if separately authorized in the future, is a
different capability with its own audit trail. Admin is not a private-data
browser.

------------------------------------------------------------------------

# 12. Governance, policies, security and audit

## 12.1 Policy Registry

Admin must expose versioned policy state for domains such as:

-   germination budget;
-   research budget;
-   currentness;
-   source acquisition;
-   JEV thresholds/decision policy when implemented;
-   canonical commit policy;
-   retention;
-   alerts;
-   provider budgets.

Every material policy change must record:

-   actor;
-   policy;
-   old value;
-   new value;
-   timestamp;
-   reason;
-   version.

Secrets remain outside policy display and exports.

## 12.2 Budget governance

Potential configurable controls:

-   `MAX_GERMINATION_COST`;
-   `MAX_RESEARCH_RUN_COST`;
-   `MAX_DAILY_COGNITIVE_COST`;
-   `MAX_MONTHLY_PROVIDER_COST`;
-   `MAX_REFRESH_COST`.

Budget exhaustion changes operational state, not epistemic truth.

`BUDGET_EXHAUSTED != FALSE`

## 12.3 Security & audit

Append-oriented audit for:

-   authentication events;
-   authorization failures;
-   privileged actions;
-   policy changes;
-   administrative actions;
-   exports;
-   agent access;
-   MCP access;
-   destructive operations;
-   incident lifecycle.

## 12.4 Admin actions

Legitimate future actions may include:

-   retry failed job;
-   pause Xeed observation;
-   trigger reinvestigation;
-   invalidate operational cache;
-   request claim review;
-   cancel batch;
-   change policy;
-   suspend account;
-   bounded billing operations.

Command path:

``` text
HUMAN ACTION
→ AUTHORIZATION
→ VALIDATED COMMAND
→ DOMAIN SERVICE
→ EVENT
→ AUDIT LOG
```

No direct database editing as the normal operational model.

Operational actions never directly assert AXIGLAND truth.

------------------------------------------------------------------------

# 13. Alerts and anomaly detection

## 13.1 Candidate anomaly classes

-   runaway Xeed;
-   research loop;
-   cost spike;
-   provider degradation;
-   low evidence yield;
-   stale-growth spike;
-   duplicate organizations;
-   relationship explosion;
-   unsupported canonical claim;
-   source concentration;
-   churn spike;
-   payment failures;
-   low reuse;
-   batch backlog;
-   quality regression.

Prioritization may use decomposable dimensions such as:

`SEVERITY × IMPACT × CONFIDENCE × SCOPE`

without turning this into an epistemic truth score.

## 13.2 Alert levels

-   P0 Critical --- integrity, security, canonical corruption;
-   P1 High --- material degradation or runaway economics;
-   P2 Medium --- operational anomaly;
-   P3 Informational --- material change requiring awareness.

Each alert should expose:

-   what;
-   why;
-   impact;
-   affected objects;
-   first observed;
-   current state;
-   supporting measurements;
-   recommended investigation.

Thresholds are policy, not hardcoded truth.

------------------------------------------------------------------------

# 14. Temporal comparison and evolution

Every material metric should support appropriate periods:

-   now;
-   24h;
-   7d;
-   30d;
-   90d;
-   custom;
-   previous-period comparison.

Admin should explain drivers of change, not only render charts.

Example conceptual decomposition:

``` text
COST / XEED
€0.93 → €1.17

Drivers:
+ browser acquisition
+ research depth
+ cognitive compute
- reuse improvement
```

Driver attribution must be based on structured measurements, not
invented narrative.

------------------------------------------------------------------------

# 15. Global search and navigation

Admin should provide a universal search/command surface across
authorized administrative entities:

-   organization;
-   Xeed;
-   research run;
-   FAXT reference;
-   batch;
-   customer;
-   invoice/payment reference;
-   source;
-   claim review;
-   alert;
-   incident.

Navigation should preserve context and allow drill-down across related
objects.

------------------------------------------------------------------------

# 16. Administrative explanation layer

A future `Explain` capability may answer questions such as:

> Why did cost per active Xeed increase this week?

The architecture must be:

``` text
ADMIN METRICS
+ UNDERLYING STRUCTURED EVENTS
+ RELATED OBJECTS
→ BOUNDED ADMIN QUERY
→ EXPLANATION
+ METRIC LINEAGE
```

The explanatory model does not become the source of the metric.

------------------------------------------------------------------------

# 17. Admin Projection Layer

## 17.1 Principle

Human UI and agents consume the same structured administrative truth.

``` text
OPERATIONAL DATA
ECONOMIC DATA
CUSTOMER DATA
RESEARCH DATA
QUALITY DATA
GOVERNANCE DATA
        ↓
ADMIN PROJECTION LAYER
        ├── HUMAN UI
        ├── JSON
        ├── CSV
        ├── MARKDOWN
        └── MCP
```

## 17.2 Admin read models

Admin should not construct every screen by joining arbitrary production
tables at request time.

Create purpose-built, versioned read models derived from authoritative
domain events and measurements.

------------------------------------------------------------------------

# 18. Downloadable Admin snapshots

## 18.1 Human/LLM-readable Markdown

Candidate artifact:

`AXIGNAL_ADMIN_SNAPSHOT_<timestamp>.md`

Suggested structure:

-   generated timestamp;
-   scope;
-   period;
-   schema version;
-   data fingerprint;
-   executive state;
-   revenue;
-   customers;
-   Xeed economics;
-   AXIGLAND growth;
-   research efficiency;
-   data quality;
-   providers;
-   incidents;
-   alerts;
-   material changes;
-   open risks.

Markdown is a portable projection, not authority.

## 18.2 Machine-readable JSON

Candidate artifact:

`AXIGNAL_ADMIN_SNAPSHOT_<timestamp>.json`

Minimum envelope:

``` text
schema_version
generated_at
period
scope
metrics
dimensions
alerts
anomalies
events
lineage
fingerprint
```

JSON should be preferred for agent computation because it avoids
extracting numerical state from prose.

## 18.3 CSV

CSV exports should be available for appropriate tabular scopes and never
used as the sole representation of hierarchical lineage.

------------------------------------------------------------------------

# 19. Admin Agent Bridge / MCP

## 19.1 Separation from product MCP

AXIGNAL should conceptually maintain two independent surfaces:

``` text
AXIGNAL PRODUCT MCP
→ queries AXIGLAND

AXIGNAL ADMIN MCP
→ queries AXIGNAL's private operational state
```

They require independent authorization boundaries.

## 19.2 V0.1 posture

Admin MCP V0.1 is **read-only**.

Admin MCP is an internal projection over authorized Admin observability. It is
not Product MCP and does not inherit Product MCP authorization. It has no
canonical write authority and no private customer-content access by default.

Candidate tools:

-   `get_admin_summary`
-   `get_business_metrics`
-   `get_customer_metrics`
-   `get_xeed_economics`
-   `get_xeed_health`
-   `get_research_metrics`
-   `get_research_run`
-   `get_knowledge_frontier`
-   `get_data_quality`
-   `get_axigland_growth`
-   `get_provider_metrics`
-   `get_source_metrics`
-   `get_cost_breakdown`
-   `get_incidents`
-   `get_alerts`
-   `get_policy_state`
-   `get_metric_timeseries`
-   `compare_periods`
-   `explain_metric_lineage`

Exact tool contracts require a later specification/bakeoff.

## 19.3 Agent permissions

Candidate scopes:

-   `admin:executive:read`
-   `admin:economics:read`
-   `admin:customers:read`
-   `admin:research:read`
-   `admin:quality:read`
-   `admin:system:read`
-   `admin:governance:read`

Apply least privilege.

## 19.4 Agent-safe exports

Export profiles may include:

-   EXECUTIVE;
-   ECONOMIC;
-   TECHNICAL;
-   RESEARCH;
-   FULL_PRIVILEGED;
-   AGENT_SAFE.

`AGENT_SAFE` excludes unnecessary PII, billing details, secrets,
credentials and tokens.

## 19.5 Agent authority

``` text
ADMIN DATA
→ AGENT
→ ANALYSIS / RECOMMENDATION
```

does not imply:

``` text
AGENT
→ ADMIN STATE MUTATION
```

Agent conclusions are not Admin truth and cannot mutate AXIGLAND.

Admin operations may read governed V3 operational metadata, but Admin and
Admin MCP do not gain private customer-content access through that metadata.

------------------------------------------------------------------------

# 20. Event and lineage architecture

Admin V0.1 should influence runtime design before Brain/Xeed
implementation so that required observability is not retrofitted later.

Candidate domain/operational events include:

-   `XeedPlanted`
-   `XeedGerminationStarted`
-   `ResearchObjectiveCreated`
-   `ResearchRunStarted`
-   `SourceRequested`
-   `SourceObserved`
-   `EvidenceProduced`
-   `CognitiveJobSubmitted`
-   `CognitiveJobCompleted`
-   `StructuredInterpretationProduced`
-   `JevEvaluationCompleted`
-   `KnowledgeGapResolved`
-   `CanonicalCommitEvaluated`
-   `FaxtCommitted`
-   `RelationshipCommitted`
-   `CurrentnessUpdated`
-   `RepresentationAnomalyDetected`
-   `MapReadinessEvaluated`
-   `FirstMapReady`
-   `XeedObservationScheduled`
-   `XeedReinvestigationStarted`
-   `ClaimReviewRequested`
-   `ClaimReviewResolved`
-   `KnowledgeReused`
-   `ComputeAvoided`
-   `CostObserved`
-   `CustomerActivated`
-   `SubscriptionChanged`
-   `XeedCancelled`
-   `PolicyChanged`
-   `AdminActionExecuted`

Events should support, where applicable:

-   event ID;
-   schema version;
-   occurred_at;
-   observed_at;
-   correlation ID;
-   causation ID;
-   actor/system;
-   Xeed/account/research identifiers;
-   provider;
-   cost observation reference;
-   outcome;
-   relevant provenance.

The proposed conceptual envelope and contract catalogue are specified in the
[Admin Observability Architecture V0.1](../architecture/AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md)
and [P0-ADMIN-01 contracts](../../specs/004-p0-admin-observability/contracts/observability-contracts.md).
Exact wire schemas, storage, transport, and provider-specific adapters remain
deferred to separately authorized implementation design.

------------------------------------------------------------------------

# 21. Metric lineage

A material metric must support drill-down.

Example:

``` text
€1.17 COST_PER_ACTIVE_XEED_MONTH
→ cost categories
→ providers
→ jobs
→ research runs
→ Xeeds
→ raw usage/billing observations
```

Financial and operational provenance must be treated as first-class.

Core invariant:

> **NO MATERIAL ADMIN METRIC WITHOUT LINEAGE.**

Parallel product invariant:

> **NO MATERIAL AXIGLAND CLAIM WITHOUT EVIDENCE LINEAGE.**

------------------------------------------------------------------------

# 22. Metrics deliberately avoided

Do not introduce opaque composite numbers such as:

-   `AI QUALITY = 93`;
-   `DATA TRUST = 87`;
-   `CUSTOMER HEALTH = 72`;
-   `AXIGNAL INTELLIGENCE = 91`;

unless their components, calibration and interpretation are explicit and
independently inspectable.

Prefer dimensions to magic scores.

------------------------------------------------------------------------

# 23. Internal strategic scorecard

AXIGNAL should be governed through multiple dimensions rather than one
North Star that hides tradeoffs.

## Customer value

-   first-map usefulness;
-   retention;
-   expansion;
-   meaningful recurring updates.

## Economics

-   contribution per Xeed;
-   marginal cost per Xeed;
-   variable cost ratio.

## Intelligence

-   useful knowledge gain;
-   evidence reuse;
-   gap resolution;
-   research yield.

## Quality

-   provenance;
-   currentness;
-   evidence coverage;
-   contradiction management;
-   entity-resolution quality.

## Efficiency

-   knowledge gain per euro;
-   cost per useful research objective;
-   duplicate research avoided.

------------------------------------------------------------------------

# 24. Architecture

Candidate architecture:

``` text
DOMAIN-OWNED EVENTS / OBSERVATIONS
          ↓
VERSIONED OBSERVABILITY CONTRACTS
          ↓
METRIC DEFINITION + ATTRIBUTION POLICIES
          ↓
AUTHORIZED ADMIN PROJECTION
          ├── HUMAN UI
          ├── JSON / CSV / MARKDOWN
          └── INTERNAL READ-ONLY ADMIN MCP
```

This is a semantic flow, not an event-sourcing mandate. Logs, metrics, traces,
domain events and canonical evidence remain distinct. The Admin Projection is
not an event store or source of domain truth. Exact persistence, transport,
metric computation and event infrastructure remain implementation decisions.

------------------------------------------------------------------------

# 25. Hard invariants

``` text
ADMIN_IS_NOT_CANONICAL_AXIGLAND_AUTHORITY

ADMIN_EVENT_IS_NOT_FAXT

ADMIN_METRIC_REQUIRES_LINEAGE

SPECIFIED_IS_NOT_IMPLEMENTED

DOCUMENTED_ARCHITECTURE_IS_NOT_RUNTIME_EVIDENCE

UNKNOWN_IS_NOT_ZERO

UNKNOWN_COST_IS_NOT_ZERO_COST

MISSING_COST_IS_NOT_FREE

FAILED_RESEARCH_IS_NOT_FALSE

BUDGET_EXHAUSTED_IS_NOT_FALSE

CUSTOMER_DISPUTE_IS_NOT_CANONICAL_CORRECTION

ADMIN_CUSTOMER_OPERATIONS_IS_NOT_CRM

ADMIN_CUSTOMER_OPERATIONS_IS_FIRST_PARTY_AXIGNAL_SERVICE_STATE_ONLY

ADMIN_CUSTOMER_OPERATIONS_DOES_NOT_AUTHORIZE_SALES_WORKFLOW

PRIVATE_CUSTOMER_DATA_NEVER_BECOMES_PUBLIC_AXIGLAND_TRUTH

AGENT_ANALYSIS_IS_NOT_ADMIN_TRUTH

ADMIN_MCP_V0_1_IS_READ_ONLY

ADMIN_EXPORT_IS_A_TEMPORAL_PROJECTION

UI_IS_NOT_ADMIN_DATA_AUTHORITY

HUMAN_AND_AGENT_SURFACES_READ_THE_SAME_ADMIN_PROJECTION

POLICY_CHANGES_ARE_VERSIONED_AND_AUDITED

NO_MATERIAL_METRIC_WITHOUT_LINEAGE

NO_SECRET_IN_EXPORTS

NO_SECRET_IN_AGENT_CONTEXT

TRIGGERED_COST_IS_NOT_ATTRIBUTED_COST

REUSE_MUST_NOT_BE_COUNTED_AS_NEW_KNOWLEDGE

SPECIFICATION_IS_NOT_RUNTIME_EVIDENCE

ADMIN_ACTION_DOES_NOT_ASSERT_AXIGLAND_TRUTH

ADMIN_OPERATIONAL_VISIBILITY_IS_NOT_PRIVATE_CONTENT_ACCESS

OBSERVABILITY_IS_NOT_A_SHADOW_CUSTOMER_DATA_WAREHOUSE

V2_V3_ADMIN_TELEMETRY_IS_NOT_A_RUNTIME_CLAIM

UNSUPPORTED_CANONICAL_WRITE_TARGET_IS_ZERO
```

------------------------------------------------------------------------

# 26. Implementation slices

Admin V0.1 may be implemented incrementally only after separate
implementation authorization and as underlying runtimes become real. P0-ADMIN-01
specifies observability contracts and does not authorize implementation.

## ADMIN-01A --- Observability Contracts

Event taxonomy, IDs, metric semantics, lineage and attribution
contracts.

## ADMIN-01B --- Economics

Costs, Xeed economics, providers, reuse and marginal economics.

## ADMIN-01C --- Intelligence

Research, Knowledge Frontier, AXENT and JEV observability.

## ADMIN-01D --- Quality

Evidence, currentness, provenance, contradictions and entity-resolution
quality.

## ADMIN-01E --- Business

Customer account operations, billing, cohorts, retention and product funnel.

## ADMIN-01F --- Human Console

Command Center and progressive drill-down surfaces.

## ADMIN-01G --- Portability

JSON, Markdown and CSV exports with schema/fingerprint.

## ADMIN-01H --- Agent Bridge

Read-only Admin MCP and authorization scopes.

## ADMIN-01I --- Governance

Policies, audit, RBAC, alerts and bounded administrative commands.

A slice must not pretend to observe a subsystem that has not been
implemented.

------------------------------------------------------------------------

# 27. V0.1 specification Definition of Done

This checklist defines specification completeness for a future, separately
authorized implementation-planning slice; satisfying it does not itself grant
implementation authorization. The spec must define and reconcile:

-   information architecture;
-   event taxonomy;
-   cost attribution model;
-   customer account and subscription model;
-   economic metrics;
-   Xeed economics;
-   research metrics;
-   knowledge metrics;
-   quality metrics;
-   epistemic metrics;
-   provider metrics;
-   system metrics;
-   policy model;
-   alert model;
-   audit model;
-   RBAC;
-   export contracts;
-   Admin Projection;
-   Admin MCP contract;
-   privacy boundaries;
-   human-first interaction rules;
-   temporal comparison;
-   metric lineage;
-   implementation phases.

Open decisions must remain explicit rather than silently resolved.

------------------------------------------------------------------------

# 28. Iteration policy

This document is intentionally **V0.1** and **PROPOSED**.

It is a living specification and should evolve as AXIGNAL discovers
better governance mechanisms, obtains runtime evidence, calibrates unit
economics, and validates how humans and agents use the administrative
surface.

Iteration rules:

1.  Higher authority always wins.
2.  Do not silently change product doctrine through an Admin iteration.
3.  Material architectural decisions should become ADRs where
    appropriate.
4.  Runtime evidence may invalidate assumptions in this specification.
5.  A new version must state what changed and why.
6.  The active repository surface should expose only the current living
    version; Git retains historical versions.
7.  `PROPOSED` must not be interpreted as `IMPLEMENTED`.
8.  Metrics should be added because they support decisions, diagnosis or
    governance --- not because they are easy to collect.
9.  Every new agent capability must preserve least privilege and human
    inspectability.
10. Every economic optimization must preserve epistemic integrity.

------------------------------------------------------------------------

# 29. Open decisions for future iterations

The following are intentionally not frozen in V0.1:

-   exact Admin frontend information architecture and visual system;
-   exact event transport/persistence technology;
-   exact metric storage engine;
-   exact cost allocation methodology for shared knowledge;
-   methodology for avoided-recompute valuation;
-   precise activation definition;
-   FIRST_MAP_WOW measurement/calibration;
-   knowledge-gain weighting, if any;
-   exact anomaly detection algorithms;
-   Admin MCP protocol contracts and pagination;
-   export retention;
-   RBAC implementation;
-   policy approval processes;
-   whether some operational actions require dual approval;
-   exact privacy/PII retention rules;
-   alert thresholds;
-   attribution of fixed/shared infrastructure;
-   exact source/provider cost ingestion mechanisms.

These should be resolved by evidence, implementation constraints and
explicit architecture decisions rather than by assumption.

------------------------------------------------------------------------

# 30. Canonical V0.1 outcome

Admin V0.1 succeeds when a human operator can rapidly determine:

-   whether AXIGNAL is healthy;
-   whether the business is growing;
-   whether customers receive value;
-   whether Xeeds are profitable at the unit level;
-   whether AXIGLAND reuse is increasing;
-   whether marginal compute is falling;
-   whether AXENT research is efficient;
-   whether evidence and provenance quality are being preserved;
-   whether currentness is degrading;
-   whether providers or sources are causing inefficiency;
-   what changed and why;
-   what policies govern the machine;
-   what requires human attention.

And an authorized agent must be able to inspect the same underlying
administrative projection through structured, read-only, least-privilege
interfaces.

The design objective is not a dashboard.

It is a **governance system for an evolving economic intelligence
machine**.

> **Human First. Agent Ready. Evidence and lineage all the way down.**
