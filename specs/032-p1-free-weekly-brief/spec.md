# AO-15 — Free Weekly Brief Request, Eligibility and Consent

## Goal

Provide a truthful public request surface for the free weekly observation brief and a governed private review lifecycle without creating a free AXIGNAL plan, Xeed entitlement or AXIGLAND truth.

## Product contracts

- REQUEST != CONSENT.
- ACCEPTED_COVERAGE != DELIVERY_ELIGIBLE unless newsletter consent is GRANTED.
- BRIEF_REQUEST != CUSTOMER != SUBSCRIBER != AXIGLAND_ORGANIZATION.
- No free Xeed or AXENT entitlement is created.
- Coverage review is based on resolvability/evidence coverage, not subjective company scoring.
- Consent withdrawal/suppression blocks later delivery.
- Public ingress is disabled by default.

## Scope

- public request form;
- request-processing acknowledgement;
- optional affirmative newsletter consent with version/timestamp;
- append-only request lifecycle;
- clarification, accept, decline and suppression operations;
- private Admin projection with PII-minimized view;
- authenticated STEP_UP Admin mutation endpoint;
- production feature flag and truthful privacy copy.

## Out of scope

- issue generation and email delivery (AO-16);
- campaign/UTM attribution (AO-12);
- engagement/conversion analytics (AO-17);
- subscriber/Xeed creation;
- browser-side Admin mutation session transport.

## Acceptance

1. Request may be submitted without newsletter consent.
2. Accepted coverage without consent is not delivery-eligible.
3. Consent/suppression states are versioned and replayable.
4. Public ingress is closed by default.
5. Admin read projection excludes email and free-text purpose.
6. Admin mutations require acquisition-write scope and STEP_UP.
7. No request flow creates Xeed/AXENT/account/canonical truth.
8. Landing links to privacy information and does not mislabel the brief as a free plan.
9. Runtime and browser QA pass before integration.
