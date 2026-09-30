# ADR-0043 — Learning Events From Real Execution

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0027, ADR-0029, ADR-0030.

## Context

Learning Memory already had an append-only store and the Prime composition root already emitted several operational events. The remaining weakness was that execution evidence was still incomplete and partially ambiguous:

- source acquisition and Observation Memory ingestion were conflated into one event;
- bootstrap application did not automatically write Learning Memory;
- reused-observation count was supplied by callers despite being derivable from RichSubjectState provenance;
- same-timestamp events were not guaranteed to sort in causal execution order;
- some yield values that are derivable from execution state were still accepted from lower-level results.

FR-17 closes that gap without giving Learning Memory authority over truth or production policy.

## Decision

### Bootstrap

Applying a governed BootstrapPlan now requires:

- a LearningMemory port;
- an execution_id;
- a code SHA.

Successful application appends one BOOTSTRAP event automatically.

The event uses the same execution identity as later Prime work and the causal phase prefix `00-bootstrap`.

Bootstrap reuse is derived from distinct observation ids already present in RichSubjectState. `build_bootstrap_plan()` no longer accepts a caller-provided reuse count.

### Source acquisition and observation ingestion

Prime execution emits two distinct events:

1. `01-source` — external acquisition produced an observation artifact;
2. `02-ingestion` — the governed observation was appended/replayed into Observation Memory.

Acquisition carries the immutable artifact reference as its activity_ref and the source policy fingerprint as policy_version.

Ingestion derives:

- whether an observation was added;
- exact state-field delta;
- before/after ObservationState fingerprints;
- NO_CHANGE when replay or ingestion produces no state mutation.

Acquisition, ingestion and validation failures are retained before re-raising.

### Representation and answerability

Representation remains `03-representation`.

The number of dimensions that became answerable is derived by comparing deterministic dimension assessment before and after the real RichSubjectState change. It is not supplied by a caller.

### Semantic and Prime work

Semantic extraction remains `04-semantic`.

Prime work uses `05-prime:<item-index>` and emits the routed mechanism kind:

- DETERMINISTIC_EVALUATION;
- STRUCTURED_EVALUATION;
- ADAPTIVE_RESEARCH.

For adaptive research, one successful Prime work item resolves at most the one governed research objective represented by that item. `research_objectives_resolved` is therefore derived from route + made_progress rather than accepted from PrimeMechanismResult.

Budget stops retain the exact governed stop reason and measured execution-budget state through the existing ADR-0029 contract.

### Causal ordering

Within one execution, Learning Event ids use causal phase prefixes:

`00-bootstrap → 01-source → 02-ingestion → 03-representation → 04-semantic → 05-prime`

Prime work items add a zero-padded item index.

This preserves causal ordering even when all events share the same occurred_at timestamp and the durable store orders by `(occurred_at, event_id)`.

A retry uses a new execution_id and therefore creates distinct append-only failure/success evidence rather than colliding with a prior attempt.

### Unknown cost

`LearningCost()` continues to mean UNKNOWN cost. No zero cost is fabricated when the runtime has no measurement.

## Invariants

LEARNING_MEMORY != CANONICAL_TRUTH

LEARNING_MEMORY != SELF_MODIFYING_POLICY

SOURCE_ACQUISITION != OBSERVATION_INGESTION

CALLER_REUSE_COUNT != AUTHORITY

DERIVABLE_YIELD != CALLER_ASSERTION

RETRY != EVENT_OVERWRITE

UNKNOWN_COST != ZERO_COST

EVENT_ORDER == EXECUTION_ORDER_WITHIN_RUN

FAILED_EXECUTION => FAILURE_EVENT_BEFORE_RERAISE

## Consequences

One first-Xeed/Prime execution can now be reconstructed from Learning Memory itself in causal order, including bootstrap, source acquisition, ingestion, representation, optional semantic extraction, routed evaluation/research and budget stop/failure outcomes.

This creates the operational evidence substrate required by FR-18 replay-reference completeness and later source/unit-economics work.

## Non-goals

This ADR does not make Learning Memory a truth authority, does not authorize automatic policy promotion, does not define complete replay metadata, does not change EvidenceAdmission, and does not deploy any production runtime.
