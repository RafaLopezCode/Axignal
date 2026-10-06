# Feature Specification: Subscriber Identity Mapping and Private Authority Ports

**Feature Branch**: `codex/production-closure`
**Created**: 2026-10-06
**Status**: Bounded offline identity-resolution slice implemented, reviewed and locally converged on 2026-10-06; no authentication runtime or durable persistence claim
**Input**: Production-readiness TASK-01/TASK-02, IDT-01/02, Spec 022, ADR-0018 and ADR-0021.

## Purpose

Specify the narrow provider-neutral boundary between a successfully verified external identity and AXIGNAL's existing `Principal`, reusing the existing Principal/Tenant/membership/Observation Focus reader ports. The preparable implementation slice is offline and contract-only: one identity-binding reader, a typed verified issuer/subject input and deterministic fixtures, after architecture review. It creates no provider integration and no production persistence claim.

This feature is a prerequisite slice for the commercial journey in which a subscriber registers 1, 2 or 100 Organizations (internal shorthand: Xeeds). It is not that journey: it does not define account onboarding, automatically create a Principal/Tenant/membership/Observation Focus, charge or grant entitlements, create an Organization, or deliver Brain output. AXIGNAL's Customer Zero remains internal AXIGNAL self-use under Admin authority and cannot satisfy subscriber E2E acceptance.

## Authority and current contract

Authority order is MASTER â†’ Constitution â†’ accepted ADRs â†’ this feature. MASTER Â§6.1 separates user/account concepts from global Organization; Â§Â§3â€“7 preserve one AXIGLAND and private attention boundaries; Â§Â§15.3â€“15.4 preserve evidence and epistemic state; Â§55 requires Human First meaning without changing truth. The Constitution requires fail-closed authorization, provider replacement, `UNKNOWN` preservation and no user-controlled canonical writes.

ADR-0018 fixes the current private authority: Tenant owns a private Observation Focus (legacy code identifier `Xeed`); `PrincipalTenantMembership` authorizes the Tenant; each Focus belongs to exactly one Tenant and references one global Organization; authorization resolves Principal, checks membership, resolves the Focus, verifies its Tenant, then returns `AuthorizedXeed`. ADR-0021 only resolves the global Organization from an already-authorized Focus. Neither ADR implements provider authentication, a production store, schema, migration, Focus creation or canonical-world writes.

Spec 022 remains in force: the external identity mapping key is issuer-scoped subject; verified provider identity maps to an internal Principal; matching email text never links identities; Tenant is not payer, legal customer or Organization; current membership is binary and has no role/invite/write semantics; payer and Principal/Tenant cardinalities and lifecycle remain deferred. Spec 022's no-runtime/no-persistence scope describes its authority-reconciliation slice. This proposal requests architecture review for a separate port-contract slice, without interpreting it as permission for a storage engine, provider, production adapter or mutation workflow.

Current source contracts are test/development only: `Principal`, `Tenant`, `PrincipalTenantMembership`, `Xeed`, `TrustedRequestContext`, `PrincipalReader`, `MembershipReader`, `XeedReader`, and `AuthorizedXeedReader` already exist. `TrustedRequestContext` does not authenticate. `tests/support/xeed_authority.py` is explicitly in-memory test/dev infrastructure. No verified external-identity binding store, durable Tenant/membership/Focus adapter or Principal provisioning use case exists.

## User scenarios and testing

### Story 1 â€” Resolve only a verified external identity

As a subscriber-facing application boundary, I need a verified issuer/subject pair to resolve to its previously established AXIGNAL Principal, so provider identifiers never become AXIGNAL actor IDs.

**Independent test**: Offline mapping fixtures resolve an exact known `(issuer, subject)` to one `PrincipalId`; unknown, invalid, duplicate/ambiguous, issuer-confused or unavailable mappings produce a non-authorizing outcome. Email, display name, avatar, email domain, provider organization, roles, and arbitrary caller IDs do not change the result.

### Story 2 â€” Preserve membership-first private Focus reads with repository seams

As a Principal acting in a selected Tenant, I need the existing application boundary to check Principal existence and authoritative Principalâ€“Tenant membership before it loads a private Observation Focus, and then verify that the Focus belongs to that Tenant.

**Independent test**: Offline fake repositories exercise call ordering, absent/unknown membership, missing Focus and known cross-Tenant Focus; the only successful result is `AuthorizedXeed` after all checks. A Focus's Organization reference resolves to the same global object and never creates Tenant-owned Organization truth.

### Story 3 â€” Isolate two subscribers observing one Organization

As two independent subscribers, we may each have a private Observation Focus referencing the same public Organization, while each Tenant's membership and private Focus metadata remain isolated.

**Independent test**: Two Tenant fixtures with distinct Focus IDs share one `OrganizationId`; authorized reads return different private Focuses and preserve one global Organization. Cross-Tenant access and spoofed Tenant context fail before private Focus data is returned.

### Story 4 â€” Revoke private access without deleting canonical truth

As the authority owner, I need a revoked/missing membership to deny the next authorized read, without deleting the global Organization, evidence, FAXT, relationship or other admitted AXIGLAND truth.

**Independent test**: Remove a membership in the offline authority fixture and repeat the same read; it is denied. Canonical Organization object and admitted truth fixtures remain untouched. This tests the read contract only; it does not authorize a production membership-removal command or choose the offboarding/retention policy.

## Functional requirements

- **FR-001**: The boundary MUST accept a typed identity value supplied by a trusted outer authentication adapter after its configured sign-in assurance has succeeded. The value type itself is not proof of authentication and is not a security boundary; its trusted caller is an adapter obligation. This feature MUST NOT implement authentication, sessions, account creation, OAuth, password/MFA flows, recovery or provider selection.
- **FR-002**: External identity lookup MUST use the exact, unnormalized `(issuer, subject)` pair supplied by that trusted adapter. Email, display name, avatar, domain, provider organization, role, login method, and unverified caller claims MUST NOT identify or authorize a Principal.
- **FR-003**: A verified external identity binding, when present, MUST resolve to exactly one internal `PrincipalId`, and the existing `PrincipalReader` MUST resolve that exact ID to an existing Principal before the service returns the Principal. An unknown mapping MUST remain non-authorizing. Any duplicate/ambiguous mapping is an integrity failureâ€”even when duplicate rows point to the same Principalâ€”and MUST remain non-authorizing. This feature MUST NOT auto-create a Principal, auto-link identities, or merge Principals.
- **FR-004**: Any later identity-link operation MUST be a separate provider-supported flow that establishes control of both identities. Email equality alone is never sufficient. Identity-link writes are outside this feature.
- **FR-005**: The proposed new provider-neutral port MUST be limited to resolving a verified issuer/subject binding to an existing Principal ID. The application MUST reuse the existing `PrincipalReader`, `MembershipReader`, `XeedReader` protocols and `AuthorizedXeedReader`; it MUST NOT duplicate or redefine those authority ports. Port/value types MUST preserve existing domain identifiers and meanings, and MUST not contain provider SDKs, unverified provider claims, storage-engine types, credential material, or secrets.
- **FR-006**: A future durable adapter MUST enforce uniqueness of the issuer/subject binding and stable identity of each stored Principal, Tenant, membership pair and Observation Focus. The offline slice MUST state only these adapter obligations; no schema, migration, SQL/NoSQL choice, storage implementation, transaction strategy or deployed durability claim is authorized here.
- **FR-007**: The existing read order MUST remain: verified outer identity â†’ mapped Principal â†’ authoritative membership for the selected Tenant â†’ Observation Focus lookup â†’ Focus Tenant match â†’ `AuthorizedXeed`. A caller-selected `TenantId` alone MUST NOT authorize access.
- **FR-008**: The implementation MUST preserve precise internal failure distinctions where the existing reader defines them. External private adapters MUST not reveal whether an unknown Focus exists in another Tenant; unknown and cross-Tenant outcomes must be externally non-enumerating, per ADR-0018.
- **FR-009**: An unavailable, corrupt, duplicate, stale or otherwise indeterminate identity-binding lookup MUST NOT create positive authorization. Typed lookup failures and exceptions MUST propagate or become an explicit non-authorizing identity-resolution failure; they MUST NOT be converted to `None`, an unknown identity, membership `False`, or another result that conflates infrastructure failure with a valid negative lookup. Existing membership-reader errors also MUST never become an allow.
- **FR-010**: A committed membership revocation, once an authorized read rechecks membership, MUST deny that read. This feature does not define the membership removal command, cache design, session revocation mechanism, final-member policy, or legal retention. These remain separate decisions; the port consumer may not cache a positive membership as indefinite authority.
- **FR-011**: Different Tenants MAY hold distinct Observation Focuses referencing the same global Organization. Focus labels are presentation data, never keys or authority. Focus persistence MUST NOT copy Organization facts, create tenant-owned Organization records, or authorize canonical writes.
- **FR-012**: Private Tenant, membership and Focus persistence lifecycle MUST remain separate from AXIGLAND canonical lifecycle. Deleting a private identity/context must not delete independently admitted Organization, FAXT, evidence or relationship truth.
- **FR-013**: No requirement in this feature establishes Principal-to-Tenant cardinality, Tenant member roles, invitations, administrator/owner semantics, payer identity/cardinality, subscriber-company identity, Xeed billing consumption, Tenant/Focus creation authority, or entitlement policy. Each remains `UNKNOWN`/deferred until separately approved.
- **FR-014**: Subscriber production E2E at 1/2/100 Organizations MUST be a later end-to-end acceptance using real subscriber authority, per-entry state, entitlements and observations. Customer Zero, Admin identity, synthetic test Tenants, and a port contract test MUST NOT substitute.
- **FR-015**: The initial offline implementation slice, if approved, MUST run without network, provider SDK, credentials, database or deployment. Deterministic contract tests MUST use injected fakes and prove mapping/isolation/fail-closed semantics only. Passing these tests MUST NOT be described as durable persistence or production authentication.

## Non-functional requirements and threats

| Threat / failure | Required protection | Evidence boundary |
|---|---|---|
| Identity collision or issuer confusion | Exact verified issuer-scoped subject binding; ambiguous/corrupt binding fails closed; do not normalize by email | Offline key-collision and wrong-issuer fixtures; live provider assurance remains unverified |
| Account takeover through email match or weak linking | No implicit merge; linking is a separately verified flow | Negative fixture with equal email/different subjects; no linking runtime |
| Spoofed `PrincipalId`/`TenantId`/Focus ID | Only server-trusted adapter constructs verified context; check membership before Focus lookup, then tenant ownership | Call-order and unauthorized-read tests |
| Cross-Tenant enumeration | Preserve precise internal results while external adapter collapses not-found/cross-Tenant outcomes as required | Adapter behavior is not implemented in this slice |
| Membership revocation race/stale positive cache | Recheck authority; a completed revocation cannot remain an indefinite allow | Offline subsequent-read test; production consistency/cache policy remains a decision |
| Persistence corruption, duplicate key, partial write | Durable adapter must fail closed and preserve uniqueness/atomicity across a binding record; no partial trusted context | Port contract tests cannot prove crash consistency or real database durability |
| Canonical-world poisoning/deletion | Private identity/focus may direct attention only; Organization truth changes only through EvidenceAdmission; subscriber deletion cannot delete canonical truth | Existing domain invariants plus offline non-mutation assertions |
| Availability or timeout | No fallback to Admin/CZ, synthetic authority or cached allow; return unavailable/unknown non-authorizing outcome | Offline exception fixtures; deployed availability is `UNKNOWN` |

## Success criteria

- **SC-001**: For seeded offline mapping records, exact verified issuer+subject resolves to the expected Principal; wrong issuer, unknown identity, duplicate mapping, malformed binding and ambiguous result never authorize.
- **SC-002**: A binding that is not found does not create a Principal, Tenant, membership or Focus; new-subscriber provisioning remains an explicit follow-up.
- **SC-003**: Contract tests prove membership is checked before Focus lookup, and cross-Tenant or revoked membership never returns `AuthorizedXeed`.
- **SC-004**: Two Tenant-scoped Focuses may reference one shared Organization and remain distinct; no canonical entity is copied or mutated.
- **SC-005**: A repository error, indeterminate result or invalid record produces no positive authorization.
- **SC-006**: Tests are deterministic and offline. No provider, network, database, session or production access occurs.
- **SC-007**: Documentation stays inside this feature directory. If root approves the offline implementation after review, new code is limited to `application/subscriber_identity/service.py`, a minimal `application/subscriber_identity/__init__.py`, and `tests/unit/test_subscriber_identity.py`; existing reader/domain protocols, global feature selection, ADRs/spec 022, Customer Zero, Landing and subscriber UI remain untouched.

## Out of scope

Provider choice/configuration/SDK and auth runtime; registration or account creation; Principal ID generation policy; identity linking; session/cookie/CSRF/recovery lifecycle; provider-specific assurance; Tenant/member/Observation Focus creation, update or deletion; membership roles/invitations/admin; payer/billing/entitlement; Organization creation or mutation; production database/schema/migrations/adapters; caching/replication choice; legal retention/erasure; UI/Settings; production deployment; Customer Zero changes; and the subscriber 1/2/100 E2E itself.

## Governing references

- MASTER Product Model Â§Â§3â€“7, 15.3â€“15.4, 36, 55; Engineering Constitution IV, VI, VIIIâ€“X, XIV, XVII, XXâ€“XXII.
- `docs/adr/ADR-0018-canonical-xeed-authority.md` â€” private Tenant/membership/Focus authority and membership-first read order.
- `docs/adr/ADR-0021-authorized-xeed-organization-context-read.md` â€” global Organization is read only from an already authorized Focus.
- `docs/adr/ADR-0017-private-cognitive-continuity-and-context-boundaries.md` â€” private context boundaries; not an auth or persistence selection.
- `specs/022-p0-identity-account-authority/spec.md` â€” identity planes, verified external subject mapping, and deferred provider/payer/cardinality/lifecycle.
- `specs/047-subscriber-billing-bridge/spec.md` â€” subscriber identity/scope remain unresolved and are not inferred from billing.
- `application/xeed_access/reader.py`, `domain/tenancy/model.py`, `domain/xeed/model.py`, `tests/support/xeed_authority.py`, `tests/contracts/test_xeed_authority.py`, `tests/contracts/test_xeed_organization_read.py`.
