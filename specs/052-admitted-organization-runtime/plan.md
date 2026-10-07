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

## T006 bounded provider implementation

Selection/rights/coverage decision: `registry-provider.md`. Reuse the existing
port, admission service, registry record builder, HTTP sensor/policy/pinned TLS
transport and content-addressed artifacts. Add only a pipeline GLEIF exact-LEI
adapter and root provider composition from existing subscriber settings. No
domain HTTP, source canonical writer, new dependencies, fuzzy lookup, website
authority or generic registry framework. Operational limits/cache are separate
from the unchanged canonical store. Constitution check: PASS for inward pipeline
→ application/domain direction and unchanged EvidenceAdmission authority.

Validate parser/absence/failure/rights/currentness/integrity; real adapter offline
E2E including configuration selection and simultaneous tenants; live read-only
public contract smoke; deterministic gates and isolated candidate preflight.
