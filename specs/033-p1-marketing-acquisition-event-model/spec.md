# AO-12 — Marketing & Acquisition Event Model

## Goal

Measure AXIGNAL acquisition through first-party, privacy-minimized observed-touch events while preserving separate authorities for anonymous marketing telemetry, weekly-brief requests, CRM, customer accounts and AXIGLAND.

## Invariants

- ANONYMOUS_SESSION != PERSON.
- MARKETING_EVENT != CRM_IDENTITY.
- MARKETING_EVENT != AXIGLAND_TRUTH.
- OBSERVED_TOUCH != CAUSAL_ATTRIBUTION.
- UNATTRIBUTED != UNKNOWN_PERSON.
- REQUEST_LINK != IDENTITY_MERGE.
- TELEMETRY_FAILURE != REQUEST_FAILURE.

## Scope

- Landing view, chapter view, selected CTA activation, weekly-brief open and request-link events.
- Random session-scoped opaque reference; no cookie/fingerprint identity.
- Path-only landing location, referrer origin only, bounded UTM/source/campaign fields.
- Append-only replay-safe persistence in the existing admin-acquisition store.
- Versioned OBSERVED_TOUCH_V1 summary and request-level touch provenance.
- Private Admin projection with aggregate source/campaign/session/event counts.
- Exact, feature-gated public status/event routes.
- Disabled-by-default production configuration.

## Out of scope

- User/person identity resolution from anonymous telemetry.
- Automatic CRM prospect/contact creation.
- Cross-device tracking.
- Third-party analytics provider integration.
- Signup/Xeed/paid funnel analytics and causal models (AO-14/AO-17).
- Any AXIGLAND write.

## Acceptance

1. Anonymous events cannot carry email, company identity, purpose or principal/user IDs.
2. Referrer is stored as origin only and landing URL as path only.
3. Exact replay is idempotent; conflicting replay fails closed.
4. Attribution model is explicit and versioned.
5. BriefRequest may reference observed source/campaign lineage without claiming causality.
6. Marketing telemetry failure cannot break a valid AO-15 request.
7. Public ingestion is unavailable when the independent AO-12 feature gate is disabled.
8. Production proxy exposes only exact governed routes, never a generic /api/ proxy.
9. Admin projection remains PII-minimized.
10. Focused and full deterministic validation pass before integration.
