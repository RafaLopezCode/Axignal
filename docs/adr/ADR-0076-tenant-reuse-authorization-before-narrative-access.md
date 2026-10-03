# ADR-0076 — Tenant/Reuse Authorization Before Narrative Access

**Status:** ACCEPTED
**Date:** 2026-10-04
**Scope:** AUD-05; EvidenceNarrative; Observation Memory access; tenant-private evidence presentation
**Derives from:** MASTER §§2.1A, 54.4, 55; Engineering Constitution XXI; ADR-0050; ADR-0055; ADR-0075

## Context

Observation reuse authority already governed whether an observation could be reused by subject, tenant, purpose, rights, access, scope, provenance and currentness. EvidenceNarrative did not consume that authority. It could resolve an observation for the same economic subject and then expose its material even when the current Xeed belonged to a different tenant.

That violated the distinction between shared world identity and private observer context.

## Decision

Subscriber evidence narrative applies reuse authorization before any private narrative material or artifact is retrieved.

### Narrative access context

NarrativeAccessContext binds:
- canonical subject;
- authorized Xeed;
- tenant;
- target scope;
- reuse purpose;
- as-of time.

The context must match the AuthorizedXeedOrganization that authorized the read.

as_of is carried now so presentation has an explicit temporal reference. AUD-05 consumes the stored currentness authority; dynamic age/currentness recomputation from as_of remains AUD-06.

### Metadata-first authorization

SqliteObservationMemory exposes an authorization-only access_metadata lookup containing ObservationRecord plus ObservationReuseAuthority. It deliberately excludes raw_content, raw_artifact_ref and normalized fields.

The narrative order is:
1. obtain considered observation IDs without narrative content;
2. load metadata only;
3. evaluate reuse authority;
4. reject unless the decision is ALLOW;
5. only then resolve full GovernedObservation and NarrativeMaterial;
6. only then verify immutable artifact integrity.

Therefore a different tenant, prohibited/unknown rights or restricted scope cannot cause private material or CAS data to be loaded by the narrative path.

### Reuse policy

The existing deterministic ADR-0050 gate remains authoritative. AUD-05 does not create a second rights engine.

Rejected states include:
- PRIVATE_SCOPE_MISMATCH;
- PRIVATE_SCOPE_GLOBAL_LEAK;
- RIGHTS_PROHIBITED;
- RIGHTS_UNKNOWN;
- RESTRICTED_SCOPE;
- INACCESSIBLE;
- PROVENANCE_MISSING;
- subject/purpose mismatch;
- currentness states rejected by the selected purpose.

### Public and private presentation

Evidence narrative marks rendered evidence steps explicitly as GLOBAL_PUBLIC or TENANT_PRIVATE.

A TENANT_PRIVATE observation may be presented only inside the owning tenant's private target scope and only for an allowed purpose. It cannot be projected to GLOBAL_WORLD.

Tenant-private presentation is contextual evidence only. It does not create, promote or mutate canonical AXIGLAND truth.

PRIVATE_REUSE != GLOBAL_WRITE

### FR-30

FR-30 now assigns explicit reuse authority when its governed public homepage observation is ingested: PERMITTED, ACCESSIBLE, GLOBAL_PUBLIC, provenance-bound, CURRENT and applicable to the exact subject/current-state purpose.

The system-wide default remains restrictive. Missing explicit authority is still UNKNOWN/RESTRICTED and fails closed.

### Payload safety

Subscriber narrative never serializes raw_content, raw_artifact_ref or CAS references. Private evidence is identified by TENANT_PRIVATE scope without exposing storage internals.

## Non-goals

AUD-05 does not derive effective currentness from observation age at presentation time and does not reproject cached read models as time advances. Those are AUD-06.

## Consequences

- Same organization identity does not imply same private evidence access.
- Reuse denial and narrative denial are now the same governed decision boundary.
- Private material is not touched before authorization.
- Correct private owner + allowed purpose may receive an explicitly tenant-private explanation.
- Private evidence cannot be promoted to global AXIGLAND truth.
- Public evidence remains reusable only when its explicit authority permits it.