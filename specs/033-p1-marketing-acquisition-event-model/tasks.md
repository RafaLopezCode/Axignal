# AO-12 closure tasks

- [x] Define private first-party MarketingEvent domain and OBSERVED_TOUCH_V1 methodology.
- [x] Add append-only replay-safe marketing persistence to admin_acquisition.
- [x] Implement privacy-minimized public ingestion service.
- [x] Reject person/company/request PII on anonymous telemetry endpoint.
- [x] Reduce landing URL to path and referrer to origin before persistence.
- [x] Add independent acquisition feature gate, closed by default.
- [x] Instrument landing with sessionStorage-only opaque session refs and stable event classes.
- [x] Link accepted AO-15 request submission to prior anonymous session without identity merge.
- [x] Extend Admin projection with event/session/source/campaign and request touch lineage.
- [x] Add exact Nginx routes; no generic /api/ proxy.
- [x] Focused AO-12/AO-15 contracts, Ruff and mypy.
- [x] Browser QA: enabled mode persists minimized landing/chapter observed-touch events; disabled mode persists zero events.
- [x] Full deterministic repository validation: 877 PASS; Ruff, mypy, Architecture Guard, governance and diff checks PASS.
- [x] GitHub CI #310 PASS and PR #130 merged to main at `9822c4b0d4a352633b320a2d250d964a746efd39`.
- [x] Production deploy/E2E PASS with AO-12 collection disabled: exact SHA healthy, external status false, POST 404, deployed browser artifact verified, zero telemetry persisted after external UTM visit, persistence continuity and logs clean.
