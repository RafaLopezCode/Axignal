# Requirements checklist â€” Subscriber Identity Mapping and Private Authority Ports

## Spec and authority

- [x] Feature is grounded in production-readiness TASK-01/TASK-02 and finding IDT-01/02.
- [x] MASTER/Constitution precede ADRs, specs, plan and implementation.
- [x] ADR-0018's Tenant â†’ private Focus ownership and membership-first authorization are preserved.
- [x] ADR-0021's Focus-scoped read returns the original global Organization; no tenant-owned Organization or mutation is introduced.
- [x] Spec 022's identity planes, provider-neutral issuer-scoped subject mapping, email non-linking, and unresolved payer/cardinality/lifecycle decisions are preserved.
- [x] Root architecture review approved only the typed identity lookup + existing reader reuse boundary and the exact new code paths.
- [x] Root docs-review checkpoint for corrected spec, clarifications, plan, tasks and checklist recorded before code begins.

## Identity mapping and failure semantics

- [x] Mapping key is the exact trusted `(issuer, subject)` pair; no normalization and no email/profile-derived identity.
- [x] Typed identity value does not claim to authenticate itself; caller must be a trusted outer adapter.
- [x] Resolver confirms the binding's exact `PrincipalId` through existing `PrincipalReader` before returning an existing `Principal`.
- [x] Not-bound, duplicate (including duplicate rows to same Principal), missing Principal, malformed value and unavailable/error are non-authorizing.
- [x] Errors are not converted to `None`, not-bound, membership false or a fabricated/default actor.
- [x] No Principal auto-creation, auto-link, merge, provider selection, session, account signup, Tenant or Focus provisioning.

## Existing private authority reuse

- [x] Reuse existing `PrincipalReader`, `MembershipReader`, `XeedReader` and `AuthorizedXeedReader`; add no `TenantReader` or duplicate authorization protocol.
- [x] Preserve membership-before-Focus lookup and Focus Tenant match.
- [x] Reuse existing readers for cross-Tenant denial, subsequent read after membership revocation, and shared global Organization tests.
- [x] No test context or fixture is described as production trusted identity/persistence.
- [x] Customer Zero stays internal; commercial subscriber registration of 1/2/100 remains a separate E2E.

## Scope and validation

- [x] New application code is limited to `application/subscriber_identity/service.py` and minimal `__init__.py`.
- [x] New tests are limited to `tests/unit/test_subscriber_identity.py` and are deterministic/offline.
- [x] No production store, schema, migration, provider SDK, network, HTTP route, UI, Landing or deployment is included.
- [x] No commits, global feature selection, existing domain/reader changes or unrelated project changes are included.
- [x] Focused and full deterministic tests are run after code approval and recorded with actual status: 12 focused identity tests; 1,404 full-suite tests. See root closure verification.
- [x] Final diff/path review confirms only approved files changed within this feature.

## Deferred, preserved as UNKNOWN

- [x] Provider selection and assurance/runtime evidence remain unresolved.
- [x] Principal ID generation and first-time account/Tenant/membership/Focus provisioning remain unresolved.
- [x] Principal/Tenant membership and payer/consumption cardinalities remain unresolved.
- [x] Roles, invitations, owner/admin semantics, identity linking and deletion/retention policies remain unresolved.
- [x] Durable persistence architecture, transaction/consistency/cache, migration/rollback and production revocation evidence remain unresolved.
