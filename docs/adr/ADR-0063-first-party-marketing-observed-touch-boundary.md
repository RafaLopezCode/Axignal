# ADR-0063: First-Party Marketing Events Are Private Observed Touches, Not Identity or Causality

## Status

Accepted for AO-12.

## Context

AXIGNAL needs to measure acquisition performance across landing visits, chapters, CTAs, campaign/referrer context and later weekly-brief requests without turning analytics into identity, CRM truth or AXIGLAND truth.

The product already has separate first-party domains for weekly-brief request/consent (AO-15), internal CRM (AO-08), customer accounts (AO-09), billing (AO-10) and canonical observed-world memory (AXIGLAND). AO-12 must add acquisition evidence without collapsing those authorities.

## Decision

- AO-12 lives inside the existing private `admin_acquisition` boundary and adds append-only `MarketingEvent` records rather than a second acquisition database authority.
- Anonymous browser activity is represented only by a random opaque `AnonymousSessionRef` scoped to browser session storage. It is not a person, contact, account, customer, subscriber or organization identity.
- The initial attribution model is versioned as `OBSERVED_TOUCH_V1`. It records observed source/campaign/touch lineage and must not be described as causal attribution.
- Public telemetry accepts an explicit allow-list of fields. Name, email, professional email, company name/domain, purpose, user/principal IDs and other identity payloads are rejected.
- The runtime does not persist source IP, user-agent, fingerprint material, cookies or a full URL query. Landing path is reduced to path-only; referrer is reduced to origin-only.
- UTM/source/campaign tokens are bounded and validated. Missing source/campaign is `UNATTRIBUTED`, not inferred.
- A weekly-brief request may be linked after submission to a prior anonymous session by a separate `WEEKLY_BRIEF_REQUESTED` marketing event. This linkage does not retroactively convert earlier anonymous events into person identity.
- Marketing telemetry failure must never prevent a valid AO-15 request from being accepted.
- AO-12 public ingress has its own `AXIGNAL_ACQUISITION_EVENTS_ENABLED` feature gate. It is independent from the AO-15 request gate and remains disabled by default.
- Admin acquisition projection may expose aggregate source/campaign counts and request-level observed touch provenance, but professional email, free-text purpose and private request processing data remain excluded from the browser.
- `MARKETING_EVENT != CRM_IDENTITY != AXIGLAND_TRUTH`.
- `OBSERVED_TOUCH != CAUSAL_ATTRIBUTION`.
- AO-14 may later build product/funnel analytics on this substrate; AO-12 does not claim conversion causality.

## Consequences

- Acquisition can be measured before introducing a third-party analytics authority.
- A future provider can be added through AO-18 without replacing first-party event semantics.
- Requests can be traced to observed campaign/source touches without inventing causal certainty.
- Privacy risk is bounded by data minimization and disabled-by-default collection.
- No marketing event can write AXIGLAND or silently create a CRM person.
