# ADR-0077 — Temporal Currentness Propagation at Consumption

**Status:** ACCEPTED  
**Date:** 2026-10-04  
**Scope:** AUD-06; Observation reuse; EvidenceNarrative; Bootstrap/Prime; FR-30 subscriber read model  
**Derives from:** MASTER §§20, 53.4, 56.15; ADR-0050, ADR-0051, ADR-0076

## Context

AXIGNAL already stored immutable observation-time currentness and had deterministic temporal aging rules, but reuse and visible subscriber projections consumed the stored snapshot as if it remained current forever.

A GovernedObservation recorded as CURRENT could therefore still support CURRENT_STATE reuse and remain visibly CURRENT after the temporal policy classified the same evidence as STALE or HISTORICAL.

Mutating the stored observation is not acceptable because historical observations and historical as-of views must remain reproducible.

## Decision

Currentness used for a decision or presentation is derived at consumption time.

```
stored currentness
+ observed_at
+ as_of
+ TemporalCurrentnessPolicy
→ effective currentness
```

The stored observation and its original reuse authority remain immutable.

### Effective currentness

`evaluate_effective_currentness()` is the deterministic primitive shared by temporal evaluation and reuse. It requires timezone-aware observation/as-of times and rejects evaluation before the observation existed.

A stored CURRENT observation can age to STALE and then HISTORICAL. UNKNOWN remains UNKNOWN. HISTORICAL never becomes fresh merely because time advances.

### Reuse provenance

ObservationReuseContext can bind an explicit `as_of`.

When a TemporalCurrentnessPolicy is supplied, ObservationReuseDecision records:

- effective currentness;
- evaluated as-of;
- temporal policy id/version;
- normal reuse policy/context provenance.

CURRENT_STATE rejects effective STALE, HISTORICAL and UNKNOWN according to the existing ADR-0050 reasons. HISTORICAL_REFERENCE may consume stale/historical evidence when all other rights/scope/purpose gates allow it.

The immutable `ObservationReuseAuthority.currentness` is not rewritten.

### Bootstrap and Prime

Reused RichSubjectState is a current-state operation. When reused observations exist:

- Bootstrap requires Observation Memory, reuse policy, temporal policy and as-of;
- Prime requires reuse policy and temporal policy and uses execution `occurred_at` as as-of.

A 120-day-old observation under the 30/90 test policy is rejected before Prime mechanisms execute even if observation ids, source refs and fingerprints still match.

### Evidence narrative

NarrativeAccessContext already carries `as_of`. AUD-06 makes that timestamp authoritative by applying the TemporalCurrentnessPolicy during metadata-first authorization.

Observation/source narrative steps and the Xignal root expose effective currentness, not the persisted snapshot.

Historical-purpose narrative remains reproducible for the same as-of and policy.

### FR-30 read model

FirstProofService uses a versioned 30/90 temporal policy for the first-proof vertical.

`current_projection(as_of=...)`:

1. loads the persisted subscriber-safe snapshot;
2. copies it without mutating storage;
3. resolves the exact observationSupportRefs that sustain each visible node;
4. derives effective currentness for those dependencies;
5. updates only affected node/narrative currentness;
6. removes non-current Xignals from Today.

`FirstProofStore.latest()` remains unchanged.

A fresh reobservation restores CURRENT only through a new projection bound to that fresh observation. It does not freshen the previous observation or silently transfer semantic support to an old Xignal.

### Projection time

Source retrieval can complete after an execution starts. Post-source evaluation must not predate its evidence.

FR-30 therefore distinguishes execution start from:

```
projection_as_of = max(started_at, observation.retrieved_at)
```

Basis evaluation, Xignal emission, narrative authorization and post-source lifecycle events use `projection_as_of`.

### Dependency invalidation

Existing `temporal_dependency_change()` and `affected_temporal_dimensions()` remain the deterministic dependency-level invalidation mechanism.

Temporal aging emits only `source.currentness` as the changed dependency. Dimensions that do not depend on it are not invalidated.

FR-30 likewise updates only nodes carrying affected observation support references.

## Invariants

```
STORED_CURRENTNESS != EFFECTIVE_CURRENTNESS_FOREVER
STALE != FALSE
HISTORICAL != FALSE
OLD_OBSERVATION + NEW_CLOCK != MUTATED_OBSERVATION
NEW_REOBSERVATION != SILENT_REFRESH_OF_OLD_XIGNAL
CURRENT_STATE_REUSE requires effective CURRENT
HISTORICAL_VIEW preserves original observation
```

## Non-goals

AUD-06 does not invent automatic research scheduling, mutate historical Observation Memory, or globally rebuild every downstream product projection. Reobservation orchestration and broader dependency-driven reprojection remain consumers of the temporal invalidation contracts.

## Consequences

AXIGNAL can preserve immutable history while preventing stale evidence from masquerading as current truth.

The same historical observation remains available for authorized historical explanation, while current product surfaces and cognitive reuse are evaluated against the clock and the exact versioned temporal policy.
