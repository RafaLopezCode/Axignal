# Implementation Plan

1. Add an application-layer ObservationMemory persistence port and governed observation/state value objects.
2. Add deterministic state compilation over append-only history.
3. Add an ingestion operation returning a StateChange only when current selected state changes.
4. Add a pipeline-layer SQLite adapter using only the Python standard library.
5. Enforce idempotent replay and conflicting-ID rejection.
6. Test persistence across adapter recreation, history retention, temporal supersession, provenance-sensitive fingerprints, shared subject reuse and separation from canonical evidence admission.
7. Run targeted tests, then full deterministic repository gates and Graphify update.

## Dependency direction

application/economic_discovery owns the port and deterministic semantics.
pipeline/observation_memory owns the SQLite adapter.
domain remains unaware of storage and gains no new outward dependency.
