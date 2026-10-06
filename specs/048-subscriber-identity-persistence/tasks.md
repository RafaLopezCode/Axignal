# Tasks â€” Subscriber Identity Mapping and Private Authority Ports

**Status**: Offline code tasks implemented; production authentication/persistence remains deferred.

## Preconditions

- [x] Root architecture review approved the narrow mapping lookup + existing reader reuse boundary and the exact new file paths.
- [x] Root reviewed the corrected documentation and sent the docs-review checkpoint before code.
- [x] Confirmed the three approved code targets did not exist before implementation; no concurrent work was overwritten.

## Offline implementation tasks

### T048-01 â€” Define verified identity value and mapping port

- [x] In `application/subscriber_identity/service.py`, define an immutable typed value for the exact non-empty issuer and subject supplied by a trusted outer adapter. Do not claim the value object proves authentication.
- [x] Define only `IdentityBindingReader`, with exact pair lookup returning the binding rows/IDs needed to detect 0, exactly 1, or duplicate matches. No provider/storage SDK, writer, Principal/Tenant/membership/Focus repository duplicate, or ID generator.
- [x] Export the minimum public surface from `application/subscriber_identity/__init__.py` if needed.

**Accept when** issuer and subject are required, compared without normalization, email is not present as a mapping key, and duplicate rows remain visible even when they contain the same Principal ID.

### T048-02 â€” Resolve an existing Principal fail-closed

- [x] Implement a provider-neutral resolver in `application/subscriber_identity/service.py` using `IdentityBindingReader` and the existing `PrincipalReader` from `application.xeed_access.reader`.
- [x] Return only an already-existing `Principal` for exactly one binding row and an exact Principal lookup.
- [x] Represent not-bound, duplicate/ambiguous binding and missing Principal as explicit non-authorizing outcomes/errors. Propagate or type authority unavailability; never convert errors into `None`, not-bound, membership false, a default Principal or trusted context.
- [x] Do not construct `TrustedRequestContext`, select Tenant from identity claims, call membership or Focus ports here, or produce `AuthorizedXeed`. The existing `AuthorizedXeedReader` remains the only membership-first private read boundary.

**Accept when** no unresolved or failed mapping can return a Principal. Identity resolution alone grants no Tenant, Focus, payer, entitlement or canonical-write authority.

### T048-03 â€” Add deterministic offline identity and reuse-boundary tests

- [x] In `tests/unit/test_subscriber_identity.py`, test exact issuer+subject match, missing binding, wrong issuer, subject collision under different issuer, duplicate binding (including same Principal ID twice), malformed value, missing Principal, and identity-port exception/unavailable outcome.
- [x] Reuse current test helpers and `AuthorizedXeedReader` to prove the resolved Principal still cannot read another Tenant's Focus and a membership removed between calls denies the next read.
- [x] Prove two Tenant-scoped Focuses may reference the same canonical Organization while the existing authorized readers return distinct private contexts and preserve the one shared Organization object.
- [x] Assert no lookup path synthesizes identity/member/Focus or mutates the canonical Organization. Keep all tests offline and deterministic.

**Accept when** the focused test file passes; no implementation outside the three approved paths is required or changed; no provider, network, DB, migration, UI, HTTP or production behavior is claimed.

## Verification after approved implementation

- [x] Run focused `pytest tests/unit/test_subscriber_identity.py` with `UV_CACHE_DIR=D:\AXIGNAL\.uv-cache` and basetemp outside the repository: 12 passed.
- [x] Run required repository deterministic gates for the shared candidate: `uv sync --frozen`, Ruff format/check, `mypy`, `pytest`, Architecture Guard and `axignal-governance`. Root owns these gates. Preserve the existing paths and don't rerun or rewrite global `.specify/feature.json`.
- [x] Review status and diff: implementation changes are limited to the three approved code paths. This feature directory contains only its spec, clarifications, plan, tasks and checklist.
- [x] Record any platform/sandbox-blocked command separately; do not mark its result as pass or failure. See root's `docs/audits/production-readiness-2026-10-06/closure-verification.md` for cache/temp/network limitations, approved reruns and the retained concurrency timeout.

## Deferred work â€” no checkbox is part of this implementation

- Provider/auth/session adapter; Principal creation/ID allocation; account onboarding; Tenant bootstrap/initial member grant; membership management/revocation command; Focus creation/lifecycle; identity linking; durable stores/database/schema/migrations; caching/replication; payer/billing/entitlement; subscriber 1/2/100 E2E; public API/HTTP error mapping; Customer Zero; production deployment.
