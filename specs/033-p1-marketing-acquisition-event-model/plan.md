# AO-12 implementation plan

Reuse the AO-15 admin_acquisition boundary and SQLite store. Extend it with a separate marketing-event table and application service; do not overload BriefRequestEvent with anonymous telemetry.

Browser instrumentation uses sessionStorage for one random opaque session reference and does not use cookies, localStorage, user-agent fingerprinting or person identifiers. Runtime strips query from path and path/query from referrer before persistence.

Public routes:
- GET /api/acquisition/status
- POST /api/acquisition/events

Both remain operationally independent from weekly-brief request collection. Admin reads the combined private projection with observed-touch methodology explicitly labeled non-causal.

Production deployment remains disabled by default until privacy/legal activation is authorized.
