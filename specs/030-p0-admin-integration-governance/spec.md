# AO-18 — Admin Integration Registry and Credential Governance

## User story

As an authorized AXIGNAL operator, I need a private, inspectable registry of external capabilities and their configuration/health boundaries so that integrations can be operated without scattering credentials or implying provider state that has not been verified.

## Scope

- Model integration identity, provider, purpose, owning team, environment, direction, explicit authority boundary, requested scopes, credential reference/lifecycle metadata, webhook capability, quota posture, connection health and an explicit per-integration freshness window.
- Persist only non-secret integration metadata in a private SQLite registry. Credential bytes are supplied by a deployment secret boundary and are never resolved into or returned by Admin projections.
- Fail closed when an integration is disabled, revoked, unavailable in the active environment, or missing a usable credential.
- Render a scope-protected, read-only Admin projection. The existing browser transport has no authorized write session, so this slice does not add credential or integration mutation controls to the browser.
- Expose provider-neutral application operations for registration, lifecycle updates and health observations, each requiring the existing Admin scope and attributable audit context.

## Out of scope

- Provider SDKs, OAuth flows, webhook processing, Stripe/GSC/analytics/accounting business adapters, credential rotation execution, or secret-vault provisioning.
- Arbitrary provider requests or a browser credential viewer.
- Production Admin exposure or deployment.

## Contracts

- Admin integration state is AXIGNAL private operational state; it is not AXIGLAND truth, FAXT, Xignal or evidence.
- Credential references are locators only. Credential material never enters domain objects, SQLite, HTML/bootstrap, exports, logs or exceptions.
- Definition metadata, credential lifecycle metadata and provider runtime observations remain distinct.
- Missing/unverified data remains `UNKNOWN`; it is never rendered as false, zero or healthy.
- Provider and environment must match before a connection can be authorized.
- Health is selected by observation time within an `as_of` boundary, not arrival order. `STALE` is derived from the configured freshness window and cannot be recorded as a provider observation.
- A health observation later than its recorded time is rejected. Late-arriving older observations cannot replace newer health.
- Webhook endpoint locators are not sent to the browser; the Admin projection exposes only whether one is configured.
- Every material operation requires its existing Admin scope, a reason and an actor/session; registry state changes are audited and replay-safe.

## Acceptance criteria

1. Registry definitions and health observations persist across runtime restarts.
2. Replayed identical operation IDs are idempotent; conflicting replay is rejected.
3. Disabled, revoked, expired, wrong-environment, missing-credential and insufficient-scope integrations are denied before provider work.
4. Admin read projection is scope-checked and secret-free; Admin manage operations require `admin:integrations:manage` and step-up assurance.
5. Admin route remains unavailable when Admin security is not composed, and unauthorized roles cannot open `/admin/integrations`.
6. Unknown, unconfigured, stale and failed states are distinguished in UI copy and visible without color alone.

## Open items

- Production secret manager and browser Admin authentication transport remain deployment decisions. AO-18 provides a provider-neutral reference boundary; it does not mark absent credentials as active.
