# ADR-0055: Admin Private Business Operations Are Separate From AXIGLAND

- **Status:** Accepted
- **Date:** 2026-10-01
- **Source doctrine:** MASTER §2.1, §2.1A, §39, §46.2, §46.37, §48; Constitution §§II, IV, VI, XII, XIV, XVIII, XX–XXI
- **Supersedes:** the absolute Admin-level CRM prohibition in Admin V0.1 / P0-ADMIN-01 only for AXIGNAL's own first-party internal business operations. ADR-0008 remains fully authoritative for subscriber-facing product/core scope.

## Context

AXIGNAL must not drift into a CRM, workflow suite, ERP or editable company-profile product for customers. That prohibition protects the epistemic independence of AXIGLAND and keeps observable economic truth separate from user-controlled commercial state.

AXIGNAL nevertheless needs internal systems to operate AXIGNAL itself as a business: staff/admin identity, its own CRM, customer accounts, subscriptions, payments, billing, marketing, analytics, integrations, accounting, fiscal operations and premium advisory delivery. Treating those records as if they were AXIGLAND would be an authority violation; forbidding them entirely would make AXIGNAL operationally dependent on disconnected backoffice tools and prevent the governed Admin roadmap.
## Decision

AXIGNAL MAY implement first-party private business-operation domains inside Admin for the sole purpose of operating AXIGNAL as a provider.

These domains are separate authorities from AXIGLAND and the subscriber product.

```text
AXIGNAL_INTERNAL_CRM_STATE != AXIGLAND_ECONOMIC_TRUTH
COMMERCIAL_RELATIONSHIP_WITH_AXIGNAL != OBSERVED_ECONOMIC_RELATIONSHIP
CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE
STRIPE_STATE != AXIGLAND_TRUTH
ACCOUNTING_STATE != AXIGLAND_TRUTH
TAX_STATE != AXIGLAND_TRUTH
ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH
```

An Admin record, payment event, invoice, private analytic, CRM note, accounting entry or tax status MUST NOT create or mutate Organization, FAXT, Relationship, Xignal, INXIGHT, PATHX or canonical AXIGLAND state by implication.

If private operational data is ever proposed as economic evidence, it requires a separately authorized observation/admission contract with explicit tenant, rights, provenance and epistemic semantics. Admin presence alone confers no evidence authority.
## Consequences

- ADR-0008 continues to forbid CRM/workflow/invoicing as subscriber-facing AXIGNAL core capabilities.
- Internal CRM means **AXIGNAL's CRM for operating AXIGNAL**, never the customer's CRM.
- Admin may orchestrate bounded commands through owning business services, but Admin UI/projection is not the data authority.
- Private operational domains require their own authorization, retention, audit and privacy rules.
- GSC/web analytics, Stripe, accounting and fiscal data remain private operational state unless separately admitted under another governed contract.
- Internal commercial success/failure never changes epistemic truth.
- Admin agents/models receive only scoped projections and never unrestricted database or canonical-write authority.

## P0-ADMIN-01 disposition

The existing Admin observability architecture and contracts are **retained** for event envelopes, metric lineage, Admin Projection, exports, agent-safe reads and observability semantics.

The statements that Customer Operations cannot contain CRM objects or sales workflow are **superseded narrowly** for first-party AXIGNAL internal operations by MASTER §2.1A and this ADR.

They remain valid for:
- AXIGLAND and canonical economic state;
- subscriber-facing product capabilities;
- organizations observed by AXIGNAL;
- customer-owned CRM/workflow data;
- any attempt to infer a public economic relationship from AXIGNAL's private commercial relationship.
## Enforcement

- Admin V0.2 hard invariants encode the authority split.
- AO roadmap tasks AO-01, AO-03, AO-08, AO-09 and AO-27 require authorization and projection boundaries.
- Contract tests must prove internal CRM operations cannot mutate canonical Organization/FAXT/Relationship/Xignal state.
- Architecture Guard continues to reject CRM/workflow packages in the canonical economic domain core.
- Any future subscriber-facing CRM/workflow proposal requires a new MASTER-level product decision; this ADR does not authorize one.
