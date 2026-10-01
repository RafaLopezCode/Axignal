# ADR-0051 — Temporal Currentness and Append-Only Reobservation

**Status:** Accepted  
**Date:** 2026-10-01  
**Authority:** MASTER §§14, 20, 46, 53; ADR-0013, ADR-0015, ADR-0043, ADR-0050.

## Context

AXIGNAL already stored observation timestamps and exposed CURRENT / STALE / UNKNOWN, but it lacked one governed lifecycle that deterministically aged observations, expressed reobservation requirements, preserved historical evidence and connected temporal transitions to dependency-aware reevaluation.

FR-24 consumes currentness for reuse but intentionally left lifecycle authority to FR-25.

## Decision

### Currentness states

Canonical currentness is:

- CURRENT;
- STALE;
- HISTORICAL;
- UNKNOWN.

CURRENT != ETERNAL

STALE != FALSE

HISTORICAL != FALSE

UNKNOWN != STALE

### Versioned temporal policy

TemporalCurrentnessPolicy binds:

- policy id/version;
- stale_after;
- historical_after.

historical_after must be strictly greater than stale_after.

Currentness evaluation is a pure deterministic function of:

- immutable observation time;
- stored starting currentness;
- exact as_of time;
- exact policy version.

### Monotonic aging

For a CURRENT observation:

CURRENT -> STALE when age reaches stale_after.

STALE -> HISTORICAL when age reaches historical_after.

UNKNOWN remains UNKNOWN until new governed evidence changes what is known.

HISTORICAL never becomes fresher merely because time passes.

TIME_PASSAGE != NEW_EVIDENCE

### Reobservation requirement

ReobservationRequirement is explicit and versioned.

CURRENT => NOT_REQUIRED.

STALE / HISTORICAL / UNKNOWN => REQUIRED for recovering current-state evidence.

The requirement is a research obligation, not a truth value.

REOBSERVATION_REQUIRED != FALSE

### Subject planning

plan_subject_reobservations() evaluates the latest observation per source for one exact canonical subject.

Older observations remain in Observation Memory but do not create duplicate refresh work when a newer observation from the same source exists.

### Append-only reobservation

append_reobservation() requires:

- predecessor already present in Observation Memory;
- exact same canonical subject;
- exact same source identity;
- a new observation id;
- a strictly later observation time.

It appends through ingest_observation(). It never updates or deletes the predecessor.

REOBSERVATION != OVERWRITE

OLD_OBSERVATION => HISTORICAL_EVIDENCE_SURVIVES

### Dependency-aware reevaluation

A temporal transition emits a TemporalDependencyChange over the explicit dependency field:

source.currentness

affected_temporal_dimensions() reuses AXIGNAL's existing dependency graph and returns only TypingDimensionContracts whose declared dependencies intersect source.currentness.

TIME_CHANGE != REEVALUATE_EVERYTHING

### FR-24 interoperability

CURRENT_STATE reuse explicitly rejects STALE and HISTORICAL.

HISTORICAL_REFERENCE may use STALE or HISTORICAL when rights, scope, provenance and applicability otherwise permit.

FR-25 does not weaken FR-24 rights authority.

TEMPORAL_CURRENT != REUSE_PERMISSION

### Derived state, immutable history

Aging does not mutate persisted observations. Effective currentness is derived as-of a time under an explicit policy version. Reobservation is the mechanism that adds new evidence.

This preserves replayability and allows historical temporal state to be reconstructed.

## Invariants

CURRENT != ETERNAL

STALE != FALSE

HISTORICAL != FALSE

UNKNOWN != STALE

TIME_PASSAGE != NEW_EVIDENCE

REOBSERVATION_REQUIRED != FALSE

REOBSERVATION != OVERWRITE

TEMPORAL_AGING != HISTORY_MUTATION

TIME_CHANGE != REEVALUATE_EVERYTHING

TEMPORAL_CURRENT != REUSE_PERMISSION

## Consequences

AXIGNAL now has a deterministic temporal lifecycle rather than bare timestamps. Refresh obligations can be planned per latest source observation, reobservation preserves append-only history, and currentness changes invalidate only dependent cognitive dimensions.

## Non-goals

FR-25 does not schedule background jobs, negotiate source rights, delete retained evidence, change EvidenceAdmission, infer truth from freshness, or define source-specific freshness durations beyond the supplied versioned policy.
