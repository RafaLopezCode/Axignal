# Implementation Plan: P0-ADMIN-01 Observability Contracts

**Branch**: `feature/p0-admin-01` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Reconcile the existing AXIGNAL Admin product specification with the V1/V2/V3
authority model, define a proposed Admin observability architecture reference,
and provide a Spec Kit contract catalogue. This plan is for a documentation and
contract deliverable only; it is not a runtime implementation plan.

## Technical context

**Language/Version**: Markdown documentation\
**Primary dependencies**: None\
**Storage**: None; conceptual observation/projection contracts only\
**Testing**: Documentation and repository deterministic validation\
**Target platform**: Repository documentation\
**Project type**: Product/architecture specification\
**Constraints**: MASTER, Constitution, accepted ADRs, Atlas and no-runtime order\
**Scale/scope**: One semantic observability model with bounded Admin projections

## Constitution check

- One canonical AXIGLAND; Admin does not own or write public economic truth.
  **Pass.**
- User, source, provider, JEV, trigger and Admin inputs do not directly
  canonicalize truth; canonical writes remain behind evidence admission and
  owning-domain policy. **Pass.**
- Unknown, contradictory, stale, private/unobservable and operational failure
  states remain distinct; unknown cost is not zero. **Pass.**
- Provider-neutral `CognitiveProvider`/`ModelRouter` policy is preserved; no
  Luna SDK/model lock-in or universal JEV threshold is introduced. **Pass.**
- Business & Customer Operations remains first-party AXIGNAL service state;
  no CRM or workflow authority is added (ADR-0008). **Pass.**
- V3 private content remains tenant-scoped and distinct from operational
  metadata; no private-content browser is specified. **Pass.**
- No persistence, transport, telemetry vendor, API, dependency, migration,
  runtime, production or infrastructure decision is selected. **Pass.**

## Architecture and boundaries

The contract flow is:

```text
Owning domain events / observations
→ versioned observability contracts
→ explicit metric and attribution definitions
→ authorized, minimized Admin Projection
→ human, export and future read-only internal agent projections
```

The architecture reference explains ownership, event/observation distinctions,
time, causal references, completeness, metrics, cost/knowledge/reuse, privacy,
projection and first-runtime emission requirements. The contract catalogue
defines all 26 required semantic contracts in one file to avoid artificial
one-file-per-contract sprawl. `data-model.md` names concepts only; it does not
define database tables, wire schemas or persistence.

## Documentation structure

```text
docs/product/AXIGNAL_ADMIN_PRODUCT_SPEC.md
docs/architecture/AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md
specs/004-p0-admin-observability/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/observability-contracts.md
└── tasks.md
```

## Risks and rollback

- Risk: readers mistake contracts for runtime evidence or accepted architecture.
  Mitigation: `PROPOSED / PRE_IMPLEMENTATION`, explicit authority hierarchy,
  source-evidenced status and no-implementation statements.
- Risk: telemetry becomes a shadow store for private/customer content.
  Mitigation: metadata-first envelope, data minimization, separate
  authorization/audit for any future content inspection, and private-content
  exclusion by default.
- Risk: cost and reuse metrics imply false precision or savings.
  Mitigation: named definitions/policies, explicit unknown states, separation of
  observed cost, attributed cost, shared cost and counterfactual reuse.
- Rollback: revert the documentation-only PR. No runtime, data or deployment
  migration is involved.

## Complexity tracking

No service boundary, third-party dependency, event-sourcing model, infrastructure
vendor or persistent schema is introduced. Exact metric formulae and cost
allocation methods remain evidence-backed, versioned follow-on decisions.
