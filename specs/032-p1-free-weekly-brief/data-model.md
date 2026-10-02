# AO-15 data model

## BriefRequestEvent

Append-only event identified by stable event/request IDs, occurred_at, actor and bounded payload.

Kinds:
- REQUEST_SUBMITTED
- CLARIFICATION_REQUIRED
- COVERAGE_ACCEPTED
- COVERAGE_DECLINED
- CONSENT_GRANTED
- CONSENT_WITHDRAWN
- SUPPRESSED
- WITHDRAWN

## BriefRequestSnapshot

Derived state:
- company/domain/email/purpose;
- review state;
- coverage state;
- newsletter consent state;
- request/newsletter notice versions;
- timestamps;
- optional subject reference and review reason.

Delivery eligibility is derived only when review=ACCEPTED, coverage=SUFFICIENT and consent=GRANTED.

Admin projection intentionally omits email and free-text purpose.
