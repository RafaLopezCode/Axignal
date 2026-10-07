# Tasks

- [x] T001 Read authorities, run Graphify query, review existing routes and specify the subscriber/Customer Zero separation.
- [x] T002 Record clarification and root architecture review, including explicit live-only human authority in ADR-0084.
- [x] T003 Implement Python subscriber HTTP composition through authoritative 049/047/050 services.
- [x] T004 Implement bounded Next proxy, auth callback/cookie/logout and strict subscriber payload/redirect validation.
- [x] T005 Extend the subscriber portfolio/purchase/output/evidence surface using accepted visual grammar.
- [x] T006 Test durable HTTP E2E 1/2/100, authorization negatives, purchase transitions and replay/continuity.
- [ ] T007 Run web gates and rendered desktop/narrow/keyboard/evidence/recovery verification.
- [x] T008 Record exact configuration/deployment/recovery and external-acceptance gaps; prepare reviewable launch artifacts.
- [x] T009 Run full deterministic gates and independent regression review; converge only evidenced in-scope work.

## Pilot preparation extension (2026-10-07)

- [x] T010 Specify/clarify blank defaults, explicit Save and replaceable test-only authorization; review architecture.
- [x] T011 Implement bounded Admin-authorized persistence and optimistic read/save proxy.
- [x] T012 Add Save, durable receipt and draft/error recovery in the accepted panel.
- [x] T013 Verify durability/conflict/authorization, browser desktop/mobile/keyboard and required gates.
- [x] T014 Reconcile with Product MCP in main, prepare PR and isolated preflight, and hand off to CTO without merge or cutover.

## Current evidence

Reconciled on 2026-10-06 against canonical `main` after
`5618744 feat(subscriber): close commercial e2e composition`.

- Focused Python subscriber HTTP/composition/paid-journey suites: **14 passed**,
  using an explicit external pytest basetemp because the default Windows pytest
  temp root is permission-blocked on this workstation.
- Web experience: **66 tests passed**, TypeScript typecheck passed, i18n inventory
  passed with **1142 entries / 0 missing**, and Next.js production build compiled
  successfully with **41 routes**.
- The coordinated closure record already retains the full deterministic-gate
  evidence and known environment limits. Configuration, deployment and recovery
  boundaries are captured in the subscriber runbook and production deploy
  artifacts.
- T007 remains open deliberately: current evidence does not include a fresh
  rendered-browser desktop/narrow/keyboard/evidence/recovery pass for this exact
  candidate. Component tests and a successful Next build do not substitute for
  browser or human visual acceptance.

External registration, legal data, completed live payment lifecycle, exact
production candidate, recovery drill, rendered-browser acceptance and human
visual acceptance are not automatically completed by these implementation
tasks.

2026-10-07 pilot preparation evidence: see [CTO handoff](pilot-preparation-handoff.md) and the PR validation/preflight record. T013/T014 close the preparation slice; real Google/A-B E2E, CTO integration/cutover and T007 are not implied by their completion.
