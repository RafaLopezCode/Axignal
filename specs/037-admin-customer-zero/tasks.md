# AO-24A organization attention implementation tasks

CURRENT_TASK = AO-24A

- [x] T001 Persist attention attempts and per-principal selected focus in FR-30.
- [x] T002 Reuse exact canonical resolver; unresolved input never creates truth.
- [x] T003 Reuse acquisition/Prime/Basis/Xignal/Narrative/Today for resolved target.
- [x] T004 Require runtime read/command authority; strict HTTP/browser commands.
- [x] T005 Shared add/select/retry dialog, scope reset and persisted success read.
- [x] T006 Tests for duplicates, unknown/ambiguous, failure, revocation and restart.
- [x] T007 Browser desktop/mobile interaction and runtime restart verification.
- [x] T008 Run all gates and document evidence and limitations.

## Convergence: remaining boundaries

- [ ] T009 Human visual acceptance of this extension and prior AO-24A work.
- [ ] T010 A separately authorized canonical identity admission/discovery contract
  for organizations absent from the existing server catalog. An attention request
  remains IDENTITY_UNRESOLVED until that authority exists; this is not a manual
  Admin edit or frontend-derived identity.
- [ ] T011 Separate external subscriber identity, tenant membership and commercial
  entitlement journey before claiming post-onboarding commercial completion.

## Follow-up UX opportunities — non-blocking for AO-24A

- [ ] T012 Move "Read persisted state" out of the primary organization-management
  journey into Staff/diagnostics progressive disclosure. The persisted read remains
  available for operators, but should not compete with normal product actions.
- [ ] T013 Scale the organization selector for larger inventories with search/filter
  and a clear separation between observable/available organizations and pending or
  unresolved attention requests. Do not infer commercial entitlement from the
  inventory and do not turn the selector into a CRM/company editor.
- [ ] T014 Replace generic "Review and retry" recovery copy with cause-specific,
  actionable recovery for IDENTITY_UNRESOLVED, INSUFFICIENT_EVIDENCE and
  RUNTIME_FAILURE while preserving the prior valid reading and epistemic state.

T012-T014 are recorded dogfooding improvements, not AO-24A closure blockers.
T010/T011 remain explicit follow-on capability boundaries; no second real
organization was requested or admitted in this slice. AO-24A remains IN_PROGRESS.
