# ADR-0058: Admin Observability Projection Runtime

- **Status:** Accepted
- **Date:** 2026-10-01
- **Source doctrine:** MASTER §2.1A, Admin V0.2, P0-ADMIN-01 contracts C01–C04, ADR-0055, ADR-0056
- **Implementation:** AO-03

## Context

P0-ADMIN-01 defined semantic observability contracts before runtime, including a shared metadata envelope, operational-event semantics, temporal observations and versioned Admin projections. Those contracts intentionally deferred transport, persistence and read-model implementation.

AO-03 must make Admin projections durable and replayable without creating an event-sourcing authority over AXIGLAND or duplicating owning-domain truth.

## Decision

AXIGNAL implements a metadata-first, append-oriented Admin observability substrate.

```text
OWNING DOMAIN / SERVICE
  -> emits governed AdminEventEnvelope metadata + stable references
ADMIN OBSERVABILITY STORE
  -> append-only record history
ADMIN PROJECTION RUNTIME
  -> deterministic temporal reduction
ADMIN PROJECTION SNAPSHOT
  -> versioned read model with source refs + fingerprint
```

`AdminEventEnvelope` is not a canonical domain event and does not contain a generic raw payload field. It carries identity/version, owning domain, record class, temporal fields, outcome/completeness, scope/privacy and stable references. Raw source bodies, credentials, model prompts/responses, hidden reasoning and arbitrary private content are excluded by design.

## Record classes

AO-03 preserves distinct classes for operational events, economic observations, epistemic transitions, provider usage observations, Admin metric observations, governance/security events, logs and traces. A log or trace does not become an operational/economic event merely by ingestion.

## Idempotency

`record_id` is the replay identity. Re-ingesting the exact same record is an idempotent no-op. Reusing the same ID for different semantic content is a conflict and fails closed.

## Corrections and time travel

Corrections are new append-only records using `supersedes_record_id`; prior records are never updated or deleted.

Projection at an `as_of` instant sees only records whose `recorded_at <= as_of`. A correction recorded later therefore does not rewrite an earlier historical projection. At a later `as_of`, the superseded record is excluded from the effective set and the correction participates instead.

A correction must reference an existing earlier record and preserve `owning_domain` and `record_type`. This prevents Admin from using correction mechanics to transfer authority between producers.

## Projection semantics

Every snapshot has stable projection ID, schema version, scope, `as_of`, generation time, completeness, exact source-record IDs, typed key/value data and deterministic content fingerprint.

The projection fingerprint excludes generation time and is deterministic for the same projection definition, scope, `as_of`, effective source records and output data. Rebuilding the same historical state therefore yields the same fingerprint.

Projection snapshots are read models only. They are never accepted as owning-domain writes or canonical AXIGLAND evidence.

## Persistence

AO-03 selects SQLite only for this current Admin projection substrate, matching existing local/production persistence patterns. The decision does not require a queue, event bus, metrics vendor or global event-sourcing platform.

The durable record ledger uses an append sequence independent of random IDs. Projection snapshots are also durable and versioned. Exact replay does not double-count records.

## Failure isolation

Admin projection availability does not participate in owning-domain mutation. Producers own their records before/independently of Admin ingestion; a failed projection write or reduction cannot roll back or mutate the producer's domain state.

## Consequences

- P0-ADMIN-01 T011 is now implemented for the shared event/projection substrate.
- AO-04→AO-07 must build purpose-specific read models on this runtime rather than route-local aggregation.
- P0-ADMIN-01 T012 remains partially open: AO-02 implemented the shell/API presentation boundary, but exports/Admin MCP/operational commands remain later tasks.
- Telemetry transport, queues and provider-specific instrumentation remain out of AO-03.
- Admin observations still do not authorize canonical writes.

## Enforcement

- `domain/admin_observability/` owns envelope/snapshot semantics.
- `application/admin_observability/` owns ingest, correction validation, temporal replay and deterministic projection.
- `pipeline/admin_observability/` owns SQLite persistence.
- AO-03 tests prove exact idempotency, conflicting replay rejection, correction history, historical `as_of`, record-class separation and deterministic snapshot replay.
