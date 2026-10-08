# Backend plan and architecture review

Graphify scoped queries inspected AO-15/16 and AO-18 before implementation.
Application public_requests owns validation, private receipts and delivery port.
Pipeline public_requests owns separate SQLite persistence and provider-neutral SMTP.
Runtime composes method/origin/body gates and existing integration authority.

No public frontend or canonical edge wiring is part of this coordinated backend PR.
Claude owns shared UX. Preserve earlier UI work on its separate review branch.
After CTO integration of Claude, rebase and inspect before any required wiring.

Constitution: UNKNOWN remains unknown; messages never become economic evidence.
Deterministic validation and transport; no AI legal authority, CRM, newsletter
consent, subscriber entitlement, billing or production activation.

Retention: 90 days, purged on intake and periodic runtime maintenance. Audit metadata
contains private receipt/time/type/status only; no unbounded extra telemetry.
SMTP requires current AO-18 authority/health/scopes before credential or socket access.

Validate server-side adversarial contracts, full backend suite, deterministic gates,
MCP and POSIX integration in isolated Linux candidate. Compare canonical production
identifiers read-only before/after. No production data mount is required by this slice.
