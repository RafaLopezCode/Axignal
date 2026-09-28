# Plan: P0-CORE-05 Canonical Subject / Entity Authority

**Base:** `2775d196d6942537f46c2a52a0e6ecb573d1f5ad`
**Branch:** `architecture/p0-core-05-canonical-subject-authority`
**Spec:** [spec.md](spec.md)

## Work units

1. Reconcile MASTER, Constitution, applicable ADRs, domain/application
   contracts, deterministic tests and the existing HFX matrix.
2. Trace current FAXT subject and object/value representations, Organization
   and Xeed identity boundaries, and Observed/Potential Relationship authority.
3. Preserve `FAXT.subject_id: str` and record
   `SUBJECT_KIND=UNKNOWN_UNSUPPORTED` and
   `SUBJECT_RESOLUTION=UNKNOWN_UNSUPPORTED`; add no speculative domain type.
4. Update the HFX integration matrix only with conclusions supported by that
   reconciliation.
5. Run focused contracts, canonical repository gates, Graphify structural
   checks/update, deterministic build, Golden Master manifest verification,
   secret safety, and scope/self-audit.

## Architecture

No runtime/domain architecture change is justified. The slice is a governed
reconciliation record and matrix clarification. FAXT remains an evidence-backed
global object with an opaque subject string; Organization relationships remain
independent canonical domain objects; private Xeed membership does not supply
either subject identity or relationship authority.

## Exclusions

No FAXT migration, subject/entity abstraction, resolver, ontology registry,
relationship reader, Subscriber Projection, UI, Golden Master source change,
production persistence, database, AXENT, provider/model/JEV integration,
deployment, or HFX-01.
