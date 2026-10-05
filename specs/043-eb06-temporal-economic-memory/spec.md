# EB-06 — Temporal Economic Memory

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER → Constitution → ADR-0051/0058/0077 → Economic Brain Execution Roadmap
**Roadmap slice:** EB-06

## Purpose

Close the temporal-memory delta by extending the existing append-only Observation Memory.
This slice does not create a second event store or truth authority.

## Authorized behavior

- Reconstruct subject state deterministically at an explicit timezone-aware `as_of`.
- Preserve append-only history while selecting only observations effective by `as_of`.
- Prove incremental ingestion and full replay produce the same state and fingerprint.
- Carry explicit temporal field states for measured absence, withdrawal, conflict and unknown.
- Derive typed temporal changes without coercing UNKNOWN or measured absence to FALSE.
- Preserve existing `StateChange.changed_fields` so dependency-aware planning reevaluates only affected dimensions.
- Persist temporal field state in the existing SQLite Observation Memory adapter with backward-compatible default VALUE.

## Invariants

- OBSERVATION MEMORY != AXIGLAND canonical truth.
- UNKNOWN != FALSE.
- MEASURED_ABSENCE != FALSE.
- WITHDRAWN != DELETED HISTORY.
- CONFLICTING != RESOLVED TRUTH.
- replay == incremental for the same effective history.
- Historical reconstruction never mutates stored observations.
- Canonical FAXT/Relationship writes remain outside this slice.

## Exit criteria

- As-of projection is reproducible across timezone representations.
- Incremental state equals full replay.
- Explicit VALUE_CHANGED / MEASURED_ABSENCE / WITHDRAWN / CONFLICTING transitions are typed.
- Unknown remains explicit.
- Only dependencies of changed fields are invalidated.
- Exact replay stays idempotent and conflicting observation-id reuse still fails closed.
