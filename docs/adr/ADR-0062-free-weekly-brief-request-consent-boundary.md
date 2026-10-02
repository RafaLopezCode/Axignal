# ADR-0062: Free Weekly Brief Request and Consent Boundary

## Status

Accepted for AO-15.

## Context

MASTER §27.3 authorizes a free weekly observation brief under request and acceptance. It explicitly separates request, coverage acceptance, newsletter consent, withdrawal and paid conversion, and forbids treating the brief as a free AXIGNAL plan or Xeed entitlement.

AO-15 needs a public request surface and private Admin review without contaminating AXIGLAND or creating hidden commercial/customer identity shortcuts.

## Decision

- `BRIEF_REQUEST != NEWSLETTER_CONSENT != CUSTOMER != XEED_ENTITLEMENT`.
- A public request records only first-party AXIGNAL acquisition state. It never writes AXIGLAND.
- Request-processing acknowledgement is mandatory. Newsletter consent is a separate, optional affirmative state with its own notice version and timestamp.
- Coverage acceptance is an Admin decision about resolvability/public evidence coverage, never a score of company merit.
- Accepted coverage without affirmative consent is not delivery-eligible.
- Consent withdrawal or suppression fails closed for delivery.
- No AO-15 path creates a free Xeed, AXENT access, subscriber account or canonical Organization fact.
- Public ingress is disabled by default through `AXIGNAL_WEEKLY_BRIEF_REQUESTS_ENABLED=false`.
- The Admin projection excludes professional email and free-text purpose. Privileged mutations require `admin:acquisition:write` and STEP_UP assurance.
- Admin browser rendering remains read-only until a secure browser mutation-session transport exists; authenticated server-side mutation endpoints are the operational authority.
- AO-12 marketing attribution can later attach source/campaign observations, but AO-15 request/consent lifecycle does not depend on AO-12 for correctness.
- AO-16 owns evidence-backed issue composition and delivery; AO-15 only establishes lawful/eligible request state.

## Consequences

The newsletter can be piloted without inventing product entitlement, consent or AXIGLAND truth. Production activation remains gated by verified legal-controller/contact data and the explicit runtime feature flag.
