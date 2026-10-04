# AO-24A persistent internal organization attention — validation

CURRENT_TASK = AO-24A

Date: 2026-10-04. Implementation on canonical main. Human requested function
implementation but explicitly requested no second real organization now.

## Problem and root cause

The organization dialog previously explained an unavailable Add button. FR-30
had one global latest projection for allowlisted AXIGNAL, no saved internal
attention inventory or per-principal selected focus. A UI button alone could
not provide persistent, authorized multi-organization use.

## Implemented boundary

Existing POST /api/xeeds now accepts strict add/select/reobserve commands.
GET /api/organizations exposes authorized internal inventory and canObserve;
GET /api/subscriber-context reads the principal's persisted selected projection.
AO-01 requires XEEDS_READ for reads and RESEARCH_OPERATE for commands. No billing
or checkout grants observation authority. No operational financial/account data
enters the economic pipeline.

The same first-proof.sqlite3 stores append-only attention attempts and private
per-principal selection. The same sensor, observation memory, Prime, explainable
basis, Xignal, EvidenceNarrative and Today build successful projections. No React
Xignal builder, alternate backend/database/Brain or production fixture is added.
Execution sequence reservations survive failed runs, preventing event-ID reuse.

Canonical source catalog bindings are server-owned and reference already-existing
identity authority. Default configuration contains AXIGNAL only. Additional
approved bindings may be loaded through AXIGNAL_ORGANIZATION_CATALOG (JSON array
of organizationId, canonicalName, targetUri, identityAuthorityRef). A missing or
ambiguous canonical identity saves IDENTITY_UNRESOLVED without acquisition or
canonical Organization creation. This configuration is not an admission API and
must not be populated from browser input. Autonomous canonical identity admission
and external commercial membership/entitlement remain separate follow-on tasks.

Shared organization dialog adds, selects, retries and rereads persistence after
success. Duplicate additions reuse the prior projection without acquiring again.
Failures preserve the previous reading. Selection changes remount transient
product/Axent scope; runtime Axent rejects stale supplied contextId and foreign
signal references, reading its projection through authorized runtime transport.

## Deterministic checks actually executed

- uv sync --frozen: PASS.
- Ruff format/check: PASS after correcting harness/test import formatting.
- mypy: PASS, 259 source files.
- Focused FR-30/AO-24A contract suites: 29 PASS.
- Complete pytest: 1,051 PASS in 216.37 seconds (final run, including process-interruption coverage).
- Architecture Guard: PASS, no violations.
- axignal-governance: all eight checks PASS after removing only a generated
  mypy cache accidentally created in the repository; explicit cache-dir validation also passed with its cache outside the repository.
- Frontend typecheck: PASS; npm test: 37 PASS; check:i18n: 1,004 entries,
  no missing translations; production Next build: PASS, including /api/organizations.
- Graphify AST update: completed; no LLM labeling/network gate added.

Initial sandbox build mkdir was denied; the authorized local-cache build passed.
No failing gate was weakened. No lint script exists in this frontend package.

## Browser interaction evidence

An isolated loopback QA runtime (8766) and compiled frontend (3811) exercised
controlled sources/canonical candidates, outside the normal runtime store. QA
harness imports test support only under qa/, never from runtime/application code.
Controlled observations prove the pipeline contract, not real-world company facts.

1. Admin -> Customer Zero -> authorized session -> NO_XEED.
2. Observe AXIGNAL -> visible planting -> persisted governed projection.
3. Shared selector -> Controlled second -> verifying identity/evidence -> new
   reading and Axent context. No checkout, alternate shell or client-side signals.
4. Axent "Qué sabes" returned runtime-authored narrative for the selected scope.
5. Unknown request -> durable IDENTITY_UNRESOLVED, no signal; existing reading held.
6. Insufficient case -> durable INSUFFICIENT_EVIDENCE; previous reading held.
7. Failure case -> durable RUNTIME_FAILURE and recovery explanation; previous
   reading held. Browser reread displays actual persisted attempt states.
8. Duplicate Controlled second -> same projection. SQLite confirms only two
   completed sessions, no extra attempt/acquisition for that duplicate.
9. Switch back to AXIGNAL -> prior projection; previous Axent conversation cleared.
10. Select Controlled second, restart runtime with same SQLite, reload browser:
    same context xeed:production-first-proof:2, same observation time 18:51:49
    Europe/Madrid (16:51:49 UTC), source https://controlled.example/, currentness and uncertainty retained.
11. Signal -> How AXIGNAL knows: narrative steps, artifact verification, safe source,
    observation date, currentness and unknown surfaces inspected (04-evidence.png).
12. Narrow390x844: Admin navigation -> selector -> form -> duplicate command ->
    return. Document width390, dialog width370 inside viewport, vertical scroll
    accessible, no horizontal overflow (05-mobile.png, 06-mobile-form.png).
13. Normal localhost3810 restored to its real runtime8765. Default inventory
    contains AXIGNAL only; previous real observation remains unchanged. Functional
    form left open for review (07-real-admin.png). No second real company added.

Artifacts: apps/web/experience/qa/037-customer-zero/attention/01-unresolved.png,
02-insufficient.png, 03-failure.png, 04-evidence.png, 05-mobile.png,
06-mobile-form.png, 07-real-admin.png, 08-real-admin-form.png. Screenshots accompany interactions; they
are not the sole E2E evidence. Read-only/support command denial, revoked catalog,
ambiguous identity, unsafe targets and per-principal selection isolation were
verified in deterministic tests, not all repeated in browser.

## Result and remaining work

Internal persistent multi-focus function implemented and locally verified for
already-canonical authorized targets. Unknown organizations remain saved requests
until separate identity authority resolves them. The previously inspected real
AXIGNAL Xignal remains xignal:90740fa6582e8e841c93f619180d89e7, backed by the public
homepage observed at 15:41:26 Europe/Madrid; no new real acquisition was requested.

AO-24A stays IN_PROGRESS pending human visual acceptance. External subscriber
onboarding/membership/entitlements and autonomous new canonical identity admission
are not asserted complete. No production deployment was performed.
