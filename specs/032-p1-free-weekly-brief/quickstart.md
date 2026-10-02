# AO-15 runtime notes

Public request ingress is controlled by:

`AXIGNAL_WEEKLY_BRIEF_REQUESTS_ENABLED=false`

When false:
- status endpoint reports disabled;
- POST request ingress returns 404;
- no acquisition event is persisted.

When enabled, the public form can submit a request with or without newsletter consent. Admin review mutations require a valid Admin Bearer session with acquisition-write scope and STEP_UP assurance.

AO-16 will own issue generation/delivery and must re-check current delivery eligibility before every send.
