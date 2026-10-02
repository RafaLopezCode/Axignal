# AO-10 tasks

- [x] Reconcile AO-09 account/entitlement authority with AO-18 integration governance.
- [x] Define provider-neutral billing mapping/event/snapshot contracts.
- [x] Enforce canonical first-Xeed + additional-Xeed quantity; exclude Xignals from billing.
- [x] Implement append-only replay-safe billing persistence ordered by provider event time.
- [x] Verify Stripe webhook signatures and normalize Checkout/subscription/invoice/refund events.
- [x] Add provider-authenticated billing authority separate from Admin human identity.
- [x] Make Checkout mapping pending-only; require verified payment for Xeed entitlement/read.
- [x] Add dormant-by-default HTTP provider ingress with bounded payloads and secret-free errors.
- [x] Add duplicate and out-of-order webhook contracts.
- [x] Reconcile AO-09 regression contracts to the stronger AO-10 billing gate.
- [x] Run full local repository validation: 853 PASS; ruff, mypy, Architecture Guard, governance and diff checks PASS.
- [ ] Confirm GitHub CI for the completed slice.
- [ ] Execute real Stripe sandbox E2E before live enablement.
- [x] Record current BLOCKED status/evidence in AO roadmap at the highest state actually demonstrated.
