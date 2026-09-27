# Implementation Plan: P0-CORE-01 Canonical Xeed Authority

**Branch**: architecture/p0-core-01-xeed-authority | **Date**: 2026-09-27  
**Spec**: [spec.md](spec.md)

## Summary

Introduce distinct typed identity values for Principal, Tenant, Xeed and
Organization; model the canonical private ownership relation; and implement a
small application reader that checks trusted Principal–Tenant membership
before resolving and authorizing a Xeed. Keep storage ports minimal and supply
only a deterministic in-memory test/dev adapter.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: None  
**Storage**: No production persistence; in-memory test/dev authority only  
**Testing**: pytest, mypy, Architecture Guard, repository deterministic gates  
**Target Platform**: Python package/application boundary  
**Project Type**: Domain and application library  
**Performance Goals**: No performance target; bounded constant-time test
authority lookups  
**Constraints**: Exact authorized base; no authentication provider, external
API, DB, migration, knowledge binding or HFX-01  
**Scale/Scope**: Identity, membership and authorized Xeed read only

## Constitution Check

- Organization remains global AXIGLAND identity; private state cannot mutate
  canonical Organization truth. **Pass.**
- Domain remains innermost; application may depend on domain and domain may
  not depend on application. **Pass; add an explicit guard.**
- Authorization precedes private context access; caller-selected Tenant alone
  is insufficient. **Pass; membership precedes Xeed resolution.**
- No authentication adapter or provider detail is introduced. **Pass.**
- Unknown, denial, and not-found outcomes remain distinct internally; future
  external private adapters conceal Xeed existence. **Pass.**
- No persistence subsystem, knowledge binding, Context Broker, Subscriber
  projection or UI is introduced. **Pass.**
- No dependency is added. **Pass.**

## Reconciliation Findings

- Organization is a global economic entity and has no owner/scope fields.
- ObservationSeed is an Organization observation assignment with an
  initiated_by string; it is not Xeed identity.
- Existing identity convention is string IDs. Distinct NewType aliases
  preserve that representation while giving mypy separate identity types.
- No principal, tenant, membership, Xeed, authentication, repository, API or
  production persistence implementation exists.
- ADR-0017's client/tenant/context design remains a target architecture;
  CTO now selects Tenant as current private boundary and reserves Client.

## Design and Boundaries

    domain identity / tenancy / Xeed
                     ↓
    application authorized-read authority
                     ↓
    future consumer (not implemented here)

Application ports resolve Principal, membership and Xeed. The reader performs
no knowledge retrieval. Its only successful result is an AuthorizedXeed
wrapper. Test support uses in-memory mappings and is not package runtime
persistence.

## Documentation Structure

    specs/015-p0-core-01-xeed-authority/
      spec.md
      plan.md
      research.md
      data-model.md
      tasks.md
      checklists/requirements.md
    docs/adr/ADR-0018-canonical-xeed-authority.md

**Structure Decision**: Add minimal domain and application packages, include
the application package in build/type-check configuration, and extend the
existing architecture guard so domain cannot import outward into application.

## Risks and Rollback

- A context object is not authentication. Future integration must construct it
  only from a trusted authenticated adapter.
- The in-memory test adapter must never be represented as production storage.
- External private endpoints must collapse not-found and cross-tenant denial.
- Rollback is a normal revert of this isolated branch; no data migration exists.

## Complexity Tracking

| Addition | Why required | Simpler alternative rejected because |
| --- | --- | --- |
| Application package | CTO requires one encapsulated authorized-read boundary | Putting authorization in the domain or a future UI would invert the required dependency/security boundary |
| Distinct identity aliases | Prevents accidental cross-plane ID substitution with the existing string-ID convention | Plain strings erase static distinctions |
