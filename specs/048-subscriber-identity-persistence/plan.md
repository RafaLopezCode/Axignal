# Plan â€” Subscriber Identity Mapping and Private Authority Ports

**Branch**: `codex/production-closure`
**Date**: 2026-10-06
**Spec**: [spec.md](spec.md)
**Architecture status**: Root-reviewed and approved for the exact offline mapping/reuse boundary; the corrected documents were reviewed before implementation. Bounded implementation and final shared-candidate gates passed.

## Summary

Prepare a small provider-neutral seam to resolve a trusted external `(issuer, subject)` to an existing AXIGNAL `PrincipalId`, then pass the existing `Principal` into the already-established membership-first read boundary. Only a typed input, one identity-binding reader protocol, resolver service and deterministic offline contract tests are candidates for the first implementation slice. Reuse `PrincipalReader`, `MembershipReader`, `XeedReader` and `AuthorizedXeedReader` as-is; add no duplicate repository ports. No production store or adapter is included, so this slice cannot claim persistence durability.

This implements neither account provisioning nor the subscriber E2E. A first-time unknown identity stays unbound and cannot create a Principal/Tenant/membership/Focus. Onboarding authority, provider choice, payer scope, durable backend and real subscriber 1/2/100 journey remain separate gates.

## Technical context

**Language/version**: Python 3.11+
**Dependencies**: Standard library and existing domain/app contracts only
**Provider**: None selected or imported
**Persistence**: Protocol boundary only; no DB, schema, migration, adapter, transaction or durable-write implementation
**Tests**: Deterministic offline fixtures/fakes only; no network, provider, browser or production calls
**Initial consumer**: Existing `AuthorizedXeedReader`; preserve its current authority sequence and its current external-not-found contract obligation
**Scope**: One verified external identity resolution and one membership-first private Focus read per request; not a bulk/provisioning operation.

## Constitution check

| Gate | Result | Rationale |
|---|---|---|
| MASTER and Constitution precedence | PASS for reviewed offline implementation | One global Organization; private Observation Focus is attention/context, not ownership. User input never mutates canonical truth. |
| `UNKNOWN` remains non-authorizing | PASS | Unbound identity, absent/indeterminate membership, unavailable store and ambiguous binding cannot produce `AuthorizedXeed`. |
| Provider abstraction | PASS | A trusted outer auth adapter would supply a verified subject; no concrete provider, credentials, SDK or provider-specific field enters domain. |
| Membership-first authorization | PASS | Keep existing sequence: principal â†’ membership â†’ Focus â†’ Tenant ownership â†’ authorized wrapper. No caller-selected Tenant authority. |
| Persistence authorization | CONDITIONAL | Repository protocols can be designed and tested offline; production schema/store is still explicitly unselected and must not be smuggled in as a port decision. |
| Commercial scope | PASS | No payer, entitlement, principal/tenant cardinality or Xeed-capacity ownership is decided. Commercial subscriber onboarding and 1/2/100 E2E remain separate. |
| Code authorization | PASS for exact offline slice | Root approved the corrected documents and the three exact code paths. No auth/provider runtime, durable store, migration or onboarding command is authorized. |

## Reviewed bounded implementation proposal

Root's review approved this proposal subject to a documentation-review checkpoint before code. Scope is exactly the following three code paths and no others:

- `application/subscriber_identity/service.py` â€” typed verified issuer/subject value, `IdentityBindingReader` protocol returning binding IDs for the exact pair, explicit non-authorizing resolution failures, and resolver service that returns only an already-existing `Principal` confirmed via the current `PrincipalReader`.
- `application/subscriber_identity/__init__.py` â€” minimal exports only if needed by package/test imports.
- `tests/unit/test_subscriber_identity.py` â€” deterministic offline tests for exact issuer+subject mapping and error/no-authorization cases, including reusing the existing Xeed authorization reader for cross-Tenant and post-revocation denial.

Do not edit domain models, existing reader protocols, `TrustedRequestContext`, DB adapters, repository/store implementations, migrations, configuration, other tests, specs, or global `.specify/feature.json`.

1. **Verified identity value**: typed, non-empty opaque issuer and subject values supplied without normalization by a trusted auth boundary. A Python value type does not cryptographically prove verification; its caller must be the trusted outer adapter once such an adapter exists. Do not pass raw tokens or arbitrary claims into the mapper.
2. **Identity binding lookup**: `IdentityBindingReader` resolves the exact pair to zero, one or multiple binding rows/IDs. Zero is an explicit not-bound result; exactly one ID may continue; any duplicate is an integrity failure, even if IDs repeat; more than one binding never authorizes. The existing `PrincipalReader` must then find that exact Principal. No writer/link/merge operation.
3. **Private authority repositories**: add no identity/Tenant/membership/Focus persistence adapter. Reuse the current `PrincipalReader`, `MembershipReader`, and `XeedReader` unchanged. The existing Focus (`Xeed`) owns exactly one `TenantId` and references a global `OrganizationId`.
4. **Authorized read application**: preserve `AuthorizedXeedReader.read(context, xeed_id)` ordering. The new resolver returns an existing `Principal`; a caller may combine its ID with a separately selected Tenant scope and let the existing reader verify membership and Focus ownership. Identity claims must not select or authorize the Tenant. Do not create production context from test fixtures. Only the existing reader constructs `AuthorizedXeed`.
5. **No mutation authority**: no Principal/Tenant/membership/Focus create/update/delete, identity linking, invitation, role, label update or Organization rebind/write. A port does not grant an operation merely by being injectable.

There is no selected `PrincipalId` generator, Tenant bootstrap policy, membership grant actor, or Focus creation command. Initial subscriber provisioning cannot be implemented until those authorities and their idempotency/abuse behavior are reviewed.

## Architecture and data flow

```text
trusted AuthenticationPort (future, provider not selected)
        â”‚ VerifiedExternalIdentity(issuer_key, subject_key)
        â–¼
Identity binding lookup â”€â”€ not found / ambiguous / unavailable â”€â”€> no authorization
        â”‚ existing PrincipalId
        â–¼
TrustedRequestContext(PrincipalId, selected TenantId)
        â–¼
Principal lookup â†’ exact membership check â†’ Focus lookup
        â†’ verify Focus.TenantId == selected TenantId â†’ AuthorizedXeed
        â–¼
ADR-0021 Organization reader returns original global Organization
```

`TrustedRequestContext` is created only by the trusted outer boundary; its type alone is not authentication. Organization reads require `AuthorizedXeed` and resolve the original global entity. No subscriber state copies or owns canonical Organization facts.

## Offline acceptance design

If root confirms the documentation review, the bounded fake-backed tests should cover:

- exact issuer+subject to one pre-existing Principal;
- unknown, malformed, wrong issuer, duplicate (including duplicate rows to the same Principal), missing Principal and typed/unavailable/error result never return an actor or create authorization; identity-store failures must not be converted to `None`/not-bound or membership false;
- email/display-name equality cannot link two external subjects;
- no membership â†’ no Focus lookup; membership present â†’ Focus lookup; mismatched Focus tenant â†’ no `AuthorizedXeed`;
- membership revoked between reads â†’ subsequent read denied;
- two Tenants, two different Focus IDs, one shared Organization ID â†’ distinct private contexts and the same original Organization object;
- stale/exceptional repository response cannot be treated as an allow; no test fake may be represented as production durability.

Unit tests can establish local mapping and existing-reader fail-closed behavior. They cannot establish database uniqueness, crash atomicity, persistence after restart, revocation consistency under replication/cache, auth provider assurance, HTTP non-enumeration in an unimplemented API, or operational availability. Those require separately selected adapters and real environment evidence.

## Threat and failure handling

- **Issuer confusion / subject collision**: pair key includes both trusted verified values, compared exactly without normalization. Do not compare email. Future adapter authority supplies the issuer/subject; provider-specific verification remains outside this feature.
- **Identity linking/account takeover**: no automatic linking; control of both identities in a separate supported flow is mandatory.
- **Tenant spoofing**: request Tenant is scope input; membership check precedes private Focus lookup and Focus must independently match the Tenant.
- **Enumeration**: retain internal failure codes, but any external private route must not distinguish unknown Focus from cross-Tenant Focus.
- **Revocation staleness**: no indefinite positive membership cache. Once a revocation is committed and observed by the authority lookup, the read is denied. Production consistency/caching policy remains unselected.
- **Storage outage/corruption**: exceptions, duplicate bindings and indeterminate state yield no authorization. Never fall back to Customer Zero, Admin identity, a fixture, guessed membership or false/zero defaults.
- **Canonical poisoning/deletion**: private membership and Focus changes cannot write or delete AXIGLAND. Only independent evidence admission governs canonical facts.

## Migration and rollback

The offline slice has no data schema or production persistence to migrate. Its rollback is limited to removing the three new code paths and their offline tests while preserving existing `AuthorizedXeedReader` behavior and accepted ADR semantics. Do not alter production configuration, persisted data, or Customer Zero.

A later durable adapter is a separate architecture decision and change. Before that work: inventory any existing data/environment read-only; choose storage after explicit review; define uniqueness for `(issuer_key, subject_key)`, Tenant/membership/Focus references, atomic onboarding (if separately approved), revocation visibility, recovery and retention; plan compatible expand/contract migration; test backup/restore and rollback; and prove that rollback cannot re-enable revoked membership or duplicate identity bindings. No destructive backfill, automatic identity merge or canonical Organization migration is permitted by this proposal.

## Dependencies and sequencing

1. **Documentation review**: root reviews corrected spec, clarifications, this plan, tasks and checklist; code remains paused until root sends an explicit docs-review checkpoint.
2. **Offline identity-resolution slice**: implement only the three listed paths; add no new durable backing store, provider SDK, database/schema/migration or API route. Run the focused unit test and exact repository deterministic gates required for the implementation candidate.
3. **Authentication runtime**: separate provider/assurance/session/hosting decision and implementation; produces verified identity, not Tenant membership or payer.
4. **Provisioning**: separate approval for first Principal, Tenant and initial membership grant plus stable ID and idempotency policy. Unknown identity must stay unbound until this exists.
5. **Durable persistence**: separate architecture and migration plan for identity binding, Principal, Tenant, membership and Focus. Current read protocols and this mapping reader do not demonstrate durable persistence.
6. **Subscriber E2E**: separately implement subscriber registration for 1/2/100 Organizations, entitlement, independent observations, read model and recovery. Test two subscriber Tenants and real per-entry outcomes. Customer Zero is not substituted.

## References

- MASTER Product Model and Engineering Constitution, see [spec](spec.md).
- ADR-0018, ADR-0021; Spec 022 identity/account authority; Spec 047 billing boundary.
- Existing source: `domain/identity.py`, `domain/tenancy/model.py`, `domain/xeed/model.py`, `application/xeed_access/reader.py`, `application/xeed_access/organization_reader.py`.
- Offline baseline tests: `tests/contracts/test_xeed_authority.py`, `tests/contracts/test_xeed_organization_read.py`; test-only fake: `tests/support/xeed_authority.py`.

## Validation state

Implemented only the three approved code paths. Focused offline tests: 12 passed. Targeted Ruff check and format check passed; mypy passed for `service.py`. Root subsequently ran the shared candidate's full deterministic gates: 1,404 tests passed, with the earlier concurrency timeout retained in closure verification. No migration, authentication-provider access, production probe or deployment was performed for this feature. Graphify query/explain/affected was run against the existing structural graph; source and accepted documents verified its navigation results. Convergence found no remaining gap in this offline slice; production authentication and persistence remain deferred.
