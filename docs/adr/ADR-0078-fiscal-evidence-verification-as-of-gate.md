# ADR-0078 — Fiscal Evidence Verification and As-Of Gate

**Status:** ACCEPTED  
**Date:** 2026-10-04  
**Scope:** AUD-07; AO-22 SIF / VERI*FACTU operational compliance gate  
**Derives from:** ADR-0069; AO-18; AO-22; Engineering Constitution; adversarial audit 2026-10-03

## Context

AO-22 correctly chose an external SIF provider and required same-version evidence before live enablement, but the implementation could still treat a complete set of opaque evidence records as sufficient.

A record containing an evidence kind, provider version and plausible sha256 text did not prove that the referenced artifact existed or that it matched the declared fingerprint. Evidence observed after the projection time could also influence a projection. HUMAN_APPROVAL was represented as an evidence kind, which did not prove that a currently effective STEP_UP human approval existed for the exact deployed binding.

Integration registry version also cannot be treated as the provider's deployed regulated product version.

## Decision

Fiscal live enablement and compliance wording are derived only from a verified evidence set for an exact deployment binding and an effective human approval as-of the projection time.

### Deployment binding

FiscalProviderSelection binds independently:

- AO-18 integration id;
- AO-18 integration definition version;
- provider product/version;
- AXIGNAL fiscal adapter version;
- fiscal ruleset id.

These identities are not interchangeable.

In particular:

```
integration definition version != provider product version
registry metadata version != deployed SIF binary/product version
```

A change to any bound identity invalidates completeness until evidence and approval exist for the exact selected binding.

### Fiscal evidence

FiscalComplianceEvidence carries:

- evidence identity and kind;
- integration identity;
- provider product version;
- adapter version;
- integration definition version;
- ruleset id;
- observed_at;
- provenance source reference;
- content-addressed artifact reference;
- sha256 artifact fingerprint.

An evidence record is eligible only if:

1. `observed_at <= as_of`;
2. it matches the selected deployment binding exactly;
3. `artifact_ref == "cas:" + artifact_fingerprint`;
4. the CAS artifact resolves and passes integrity verification.

Invalid, future or differently-bound historical records remain stored for provenance but do not count toward completeness.

Historical drift records do not permanently poison a newly complete exact-binding evidence set.

### Required documentary evidence

The documentary gate requires verified:

- provider responsible declaration;
- provider technical/adapter contract;
- non-production integration/compliance test.

`FiscalEvidenceKind.HUMAN_APPROVAL` is retained as legacy/documentary metadata only. It is not approval authority.

### Effective human approval

Human approval is an append-only FiscalApprovalEvent ledger with APPROVED and REVOKED decisions.

Each event binds the same deployment identity as the evidence set and additionally records:

- actor_ref;
- occurred_at;
- decision_ref.

Mutation requires `admin:fiscal:write` plus STEP_UP assurance, and `actor_ref` must match the authenticated grant principal.

For an as-of projection, only approval events at or before `as_of` for the exact selected binding are considered. The latest such event is authoritative:

```
latest == APPROVED -> approval effective
latest == REVOKED  -> approval not effective
no event           -> approval not effective
```

This makes historical projections reproducible: a later revocation does not rewrite an earlier authorized historical view.

### Projection states

- NO_PROVIDER: no governed provider selection.
- EVIDENCE_INCOMPLETE: exact binding lacks required verified documents or the selected binding itself has drifted.
- EVIDENCE_READY: verified documents are complete but no effective human approval exists.
- LIVE_ENABLEMENT_ALLOWED: exact binding has complete verified evidence and effective approval.

Both `live_enablement_allowed` and `compliance_claim_allowed` are false unless the final state is LIVE_ENABLEMENT_ALLOWED.

### Drift and re-evidence

Evidence from a different provider product, adapter, integration definition or ruleset is retained but ignored for the selected binding and surfaced diagnostically.

Top-level selected-binding drift, such as an AO-18 integration definition changing after selection or a ruleset mismatch, blocks live enablement until a governed migration/reselection and exact re-evidence occur.

### Admin projection

The private Admin fiscal surface exposes:

- provider product version;
- adapter version;
- integration definition version;
- effective human approval;
- verified/missing evidence kinds;
- invalid/drift reasons.

It does not expose credential material or convert fiscal operational evidence into AXIGLAND truth.

## Invariants

```
OPAQUE_REFERENCE != VERIFIED_EVIDENCE
FUTURE_EVIDENCE != AS_OF_EVIDENCE
HUMAN_APPROVAL_EVIDENCE_KIND != EFFECTIVE_HUMAN_APPROVAL
REGISTRY_VERSION != PROVIDER_PRODUCT_VERSION
COMPLETE_OLD_BINDING != COMPLETE_SELECTED_BINDING
FISCAL_ADMIN_STATE != AXIGLAND_TRUTH
```

## Consequences

AO-22 remains provider-neutral and fail-closed while becoming materially stronger: positive fiscal state now requires real artifact integrity, exact version identity, temporal validity and authenticated human authorization.

Historical evidence and approvals remain append-only and reproducible instead of being rewritten when versions or approvals change.
