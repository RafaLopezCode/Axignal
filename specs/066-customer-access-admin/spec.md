# Feature Specification: Clients and access
**Branch**: codex/customer-access-admin | **Created**: 2026-10-11
**Input**: Human P0 Customer Operations and Design Partner Admin request.
## User Scenarios & Testing
### Story 1 (P1): Invitations
Staff with fresh independent step-up creates a private capacity-1 invitation,
copies a one-time link, lists lifecycle and explicitly revokes unused invites.
Expired, revoked and already consumed invites fail. A retry never creates
another secret. Secrets/digests never appear in lists, audit or logs.
### Story 2 (P1): Pilots
Staff reads tenant/principal, activation/expiry, capacity, organizations and
first observation state. Revocation removes rights, preserves history.
### Story 3 (P1): Clients
Consolidate identity/membership, AO-09 account, billing and pending activation
from their existing authorities. Unknown is explicit. No force-activation.
## Requirements
FR-001: Reuse PilotAccessService, existing pilot DB, AO-01/AO-09 and #200.
FR-002: customers:write + SENSITIVE for issuance/revocations; audit atomically.
FR-003: Cryptographic one-use secret; digest only; TTL 1 hour–30 days.
FR-004: Durable actor-scoped idempotency, replay protection and rate limit.
FR-005: Authenticated membership binds redemption to exact principal/tenant.
FR-006: No billing/canonical edits, arbitrary capacity or duplicate MFA.
FR-007: Existing Admin grammar, six-language copy, keyboard/mobile support.
FR-008: Controlled tests never described as real Google/Stripe/runtime E2E.
## Entities
Existing pilot invitation/grant; private audit/idempotency receipts; read-only
joins of identity, billing, AO-09 and portfolio.
## Success Criteria
Create/copy in one submission; one grant per invitation; no persisted secret;
security/regression gates pass; browser and production status evidenced.
## Assumptions
PR #200 OPEN at 0f772022; stacked branch. Pilot TTL 60 days, capacity exactly 1.
Lost secret response cannot be recovered. Production remains operator-gated.
