# EB-03 implementation plan

1. Version source dispatch/request/observation contracts.
2. Extend ObservationReuseAuthority with registry provenance and policy refs, backward-compatibly.
3. Add an immutable deterministic Source Registry that emits acquisition + reuse authority from one entry.
4. Integrate the registry into FirstProof so dispatch and reuse are no longer constructed independently.
5. Enforce policy-version continuity in sensor, ingestion and Prime Learning Memory.
6. Add fail-closed tests for rights/access/purpose/instrument/robots/version mismatch and persisted authority lineage.
7. Run full deterministic gates. No production deployment in this slice.

No new database, queue, crawler, model provider, graph store or external dependency is introduced.
