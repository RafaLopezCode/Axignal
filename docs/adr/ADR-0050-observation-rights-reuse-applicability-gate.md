# ADR-0050 — Observation Rights, Reuse and Applicability Gate

**Status:** Accepted  
**Date:** 2026-10-01  
**Authority:** MASTER §§14, 20, 46.14, 53–54; ADR-0015, ADR-0030, ADR-0044, ADR-0049.

## Context

AXIGNAL amortizes observation cost through shared Observation Memory. Before FR-24, persistence and reuse were too close semantically: a GovernedObservation could exist in memory and a caller could place its observation_id into RichSubjectState; bootstrap then counted it as reused without independently proving source rights, provenance, currentness, applicability or private/public scope.

That makes shared memory economically useful but epistemically unsafe. Public visibility alone does not grant collection, retention, redistribution or reuse rights. Private first-party state must not leak into the global world. Stale or inaccessible evidence remains historical evidence; it does not become FALSE.

FR-23 already established that identity redirects do not silently migrate historical observations. FR-24 adds the orthogonal reuse authority.

## Decision

### Observation reuse authority travels with the observation

GovernedObservation now carries immutable ObservationReuseAuthority metadata:

- rights status;
- access status;
- reuse scope;
- optional private-scope owner;
- provenance reference;
- currentness snapshot;
- applicable canonical subjects;
- applicable purposes.

The default authority is deliberately restrictive:

- rights = UNKNOWN;
- access = ACCESSIBLE;
- scope = RESTRICTED;
- provenance = absent;
- currentness = UNKNOWN;
- applicability = empty.

Therefore an old or newly acquired observation does not become reusable merely because it exists.

OBSERVATION_EXISTS != OBSERVATION_REUSABLE

### Rights

Rights are PERMITTED, PROHIBITED or UNKNOWN. Only PERMITTED can pass reuse.

RIGHTS_UNKNOWN != PERMITTED

PUBLIC_VISIBILITY != REUSE_RIGHT

### Access

Access is ACCESSIBLE or INACCESSIBLE. INACCESSIBLE rejects reuse but does not negate the observation or delete its history.

INACCESSIBLE != FALSE

### Scope

Reuse scope is GLOBAL_PUBLIC, TENANT_PRIVATE or RESTRICTED.

A TENANT_PRIVATE observation may be reused only inside the same tenant's private cognitive context. A TENANT_PRIVATE observation presented to a GLOBAL_WORLD target is rejected with PRIVATE_SCOPE_GLOBAL_LEAK. A different tenant receives PRIVATE_SCOPE_MISMATCH.

PRIVATE_SCOPE != GLOBAL_SCOPE

PRIVATE_REUSE != GLOBAL_WRITE

### Provenance

Reuse requires an explicit provenance reference. Rights without provenance are insufficient.

RIGHTS_PERMITTED + NO_PROVENANCE != REUSE_ALLOWED

### Applicability

Reuse authority binds exact canonical subject ids and exact purposes. Current FR-24 purposes are CURRENT_STATE and HISTORICAL_REFERENCE.

If the current subject or requested purpose is absent from the authority's applicability set, reuse is rejected.

REUSABLE_SOMEWHERE != APPLICABLE_HERE

### Currentness

FR-24 consumes the existing Currentness state but does not implement the FR-25 temporal lifecycle.

For CURRENT_STATE: CURRENT may pass; STALE is rejected as STALE_FOR_CURRENT_USE; UNKNOWN is rejected as CURRENTNESS_UNKNOWN.

For HISTORICAL_REFERENCE: CURRENT may pass; STALE may pass; UNKNOWN is rejected.

A stale observation remains valid historical evidence when rights/scope/provenance/applicability permit it.

STALE != FALSE

STALE_CURRENT_USE != STALE_HISTORICAL_REFERENCE

FR-25 will govern deterministic CURRENT/STALE/UNKNOWN/HISTORICAL transitions and reobservation. FR-24 only consumes the currentness supplied to the observation-reuse authority.

### Deterministic decision

evaluate_observation_reuse() returns an explicit ObservationReuseDecision with observation id, ALLOW/REJECT, reason code, reuse-policy id/version and exact reuse-context fingerprint.

The reuse context binds canonical subject, Xeed, tenant, target scope and purpose. There is no opaque reuse score.

### Shared-memory selection

select_reusable_observations() evaluates the complete Observation Memory history for the exact subject.

Rejected observations remain in memory and remain inspectable. Selection removes them only from the current reuse set.

REUSE_REJECTED != OBSERVATION_DELETED

### Bootstrap enforcement

A non-empty prior RichSubjectState is treated as reused state. build_bootstrap_plan() now requires Observation Memory plus a versioned ObservationReusePolicy.

For every referenced observation_id, bootstrap requires exact presence in governed memory, an ALLOW decision for the current Xeed/tenant CURRENT_STATE context, source reference equality and observation-time equality.

Only after those checks is the observation counted in reused_observation_count.

CALLER_SUPPLIED_OBSERVATION_ID != REUSE_PROOF

### Prime enforcement

execute_prime_source_slice() applies the same boundary to non-empty prior_rich_state. This prevents a caller from bypassing bootstrap and injecting ungoverned prior state directly into Prime.

### Source acquisition

ingest_source_observation() accepts an optional explicit ObservationReuseAuthority. When none is supplied, acquisition creates the restrictive default authority.

SOURCE_ACQUIRED != SOURCE_REUSABLE

For an exact replay of an already stored observation, if the caller supplies no new reuse authority, the existing immutable authority is preserved. Replay cannot silently upgrade or downgrade reuse rights.

### Durable persistence and migration

SqliteObservationMemory persists the reuse authority as deterministic JSON alongside the observation.

When opening a legacy Observation Memory schema without reuse metadata, the adapter adds the new column and assigns the restrictive default authority to existing rows.

Migration never upgrades legacy observations to globally reusable state.

LEGACY_OBSERVATION != IMPLICIT_PUBLIC_REUSE

### EvidenceAdmission remains independent

FR-24 does not admit truth and does not create FAXTs.

An observation may be allowed for cognitive reuse and still fail EvidenceAdmission. Conversely, an evidence source category being admissible in principle does not grant reuse rights for an Observation Memory artifact.

REUSE_ALLOWED != TRUTH_ADMITTED

CLAIM != WRITE

## Reuse rejection reasons

The deterministic gate exposes SUBJECT_MISMATCH, RIGHTS_PROHIBITED, RIGHTS_UNKNOWN, INACCESSIBLE, PROVENANCE_MISSING, RESTRICTED_SCOPE, PRIVATE_SCOPE_GLOBAL_LEAK, PRIVATE_SCOPE_MISMATCH, SUBJECT_NOT_APPLICABLE, PURPOSE_NOT_APPLICABLE, STALE_FOR_CURRENT_USE and CURRENTNESS_UNKNOWN.

These are operational/epistemic reuse states, not truth booleans.

## Invariants

OBSERVATION_EXISTS != OBSERVATION_REUSABLE

PUBLIC_VISIBILITY != REUSE_RIGHT

RIGHTS_UNKNOWN != PERMITTED

INACCESSIBLE != FALSE

STALE != FALSE

PRIVATE_SCOPE != GLOBAL_SCOPE

PRIVATE_REUSE != GLOBAL_WRITE

REUSABLE_SOMEWHERE != APPLICABLE_HERE

CALLER_SUPPLIED_OBSERVATION_ID != REUSE_PROOF

REUSE_REJECTED != OBSERVATION_DELETED

SOURCE_ACQUIRED != SOURCE_REUSABLE

LEGACY_OBSERVATION != IMPLICIT_PUBLIC_REUSE

REUSE_ALLOWED != TRUTH_ADMITTED

## Consequences

AXIGNAL can continue amortizing public and governed observations across Xeeds, but reuse is now an explicit decision rather than a side effect of persistence.

Private first-party observations can assist the owning tenant's private cognitive context without becoming globally reusable. Public observations require explicit rights/provenance/applicability/currentness authority before reuse.

Bootstrap and Prime can no longer silently consume arbitrary prior RichSubjectState.

## Non-goals

FR-24 does not implement temporal aging/reobservation transitions (FR-25), rights acquisition, provider licensing negotiations, retention deletion workflows, EvidenceAdmission changes, canonical truth promotion or automatic migration of historical observation subjects.
