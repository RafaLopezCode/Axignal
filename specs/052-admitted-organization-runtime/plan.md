# Plan and architecture review

Graphify canonical identity/admission query and MASTER Â§15 were inspected first.
Reuse EvidenceAdmission, FAXT.create, ExactNameResolver, immutable CAS and existing
SqliteIdentityGovernanceStore. Adapter is under pipeline/entity_resolution; root
composition passes it to 049 resolution and 050 canonical-reader boundaries.
No HTTP canonical-write endpoint, new model SDK, provider hardwiring or CI network.
Architecture review: PASS for this bounded persistence, root CTO, 2026-10-06.

Paths: new `pipeline/entity_resolution/organization_store.py`, deterministic
contract tests, root subscriber composition. Validate focused evidence/identity
tests and all existing required gates before convergence.
