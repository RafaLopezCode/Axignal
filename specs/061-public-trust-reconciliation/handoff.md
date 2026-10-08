# 061 CTO handoff

Reconciled from preserved Codex backend commit
5476ab70febc1f8806feae265d69819219061ba3 after Claude spec 060 became canonical.

## Preserved value

application/public_requests, pipeline/public_requests, private SQLite persistence,
validation, idempotence, rate limiting, retention, governed provider authorization and
SMTP transport were retained.

## Reconciliation changes

- Renumbered from conflicting spec 060 to spec 061.
- Added status-first Contact/GDPR contracts.
- Added notice-version capture.
- Public success is status=received + requestId; provider delivery state stays private.
- Public failures are status=rejected + stable reason.
- Disabled/unapproved channels fail closed before persistence.
- Added only exact public edge routes for Contact/GDPR.
- Controller boundary is AXIGNAL / Spain; public email remains nullable and is never invented.

## Production

No provider was configured, no email was sent, no feature/public-launch/Stripe/AXENT/
scheduler flag was changed and production was not deployed by this slice.
