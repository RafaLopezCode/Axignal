# AO-15 implementation plan

Reuse AO-08 first-party business boundaries and AO-01 Admin access. Keep AO-15 independent from AO-12 attribution: campaign/source enrichment can attach later without being required for request/consent correctness.

Architecture:
- domain/admin_acquisition: immutable request events and reduced snapshot;
- application/admin_acquisition: public submission, Admin review/lifecycle and private projection;
- pipeline/admin_acquisition: append-only SQLite event store;
- tools/runtime: gated public ingress and authenticated Admin mutation endpoint;
- apps/web/landing: localized request UX;
- apps/web/admin: read-only operational projection.

Production activation remains disabled until legal-controller/contact details and privacy notice are production-ready.
