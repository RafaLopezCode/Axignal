# AO-18 implementation plan

## Constitution check

- Admin state is private AXIGNAL business/operational state under MASTER §2.1A and ADR-0055; it cannot create AXIGLAND truth.
- Preserve separate owners for registry definitions, credential material and provider runtime observations.
- Reuse AO-01 scopes and AO-07 append-only audit; do not create a second authorization or audit authority.
- Keep provider SDKs and external connections out of this slice.

## Architecture

Add a narrow `domain/admin_integrations` contract, `application/admin_integrations` governed operations and read projection, and `pipeline/admin_integrations` SQLite metadata store. Add the store to runtime composition and the existing `/admin/integrations` scope-checked shell projection. The projection is read-only. A future runtime adapter may resolve an opaque credential reference from deployment-managed secret storage, but the value is never passed into the Admin projection/store.

## Failure handling

Invalid/unknown integration identifiers, missing credentials, revoked/disabled entries, environment mismatch and stale/failed checks remain unavailable and fail closed. SQLite initialization is additive and idempotent. No production database is migrated in this implementation turn.

## Validation

Focused AO-18 contract tests; all deterministic repository gates; production Admin stays closed by default. Browser QA uses a local authorized session only and does not introduce a bypass or real provider credential.
