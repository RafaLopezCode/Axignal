# Private Design Partner Pilot — execution evidence

## Scope

Reuses ADR-0085 backend and the subscriber experience branch. No Billing activation or Stripe mutations. Public test organization: AXIGNAL, https://axignal.com/. Google test accounts A/B are deliberately blank in the private Admin dashboard. The fields are an in-memory operator draft, not identity, entitlement or invitation delivery authority.

## Local verification

- Python focal pilot, composition, HTTP, portfolio and FR-26: 41 passed.
- Full deterministic Python suite: 1637 passed (303.57 seconds).
- Experience: 115 passed; TypeScript passed; production build passed.
- Ruff formatting/lint, mypy (387 files), Architecture Guard and governance: passed. Graphify structural index generated offline.
- Browser: private Admin A/B fields initially blank, editable and clearable; neither sends invitations or changes authority. Unauthenticated account shows sign-in requirement and no private output.
- Windows default pytest temporary directory denied access; tests passed using a new explicit basetemp. No tests or gates weakened.

## Invitation transport corrections

The invite fragment is removed before storage, retained only across the OIDC redirect for at most 30 minutes, and cleared after terminal redemption or logout. Blocked browser storage fails closed. Locale rerenders no longer abort a single-use redemption; responses from an earlier session cannot update the current account. Successful redemption requires the backend contract capacity exactly one.

## FR-26 attribution boundary

Existing FR-26 projects LearningEvent by xeed_id and explicit private/shared allocations, leaving missing costs UNKNOWN. The subscriber adaptive research execution appends events with the authorized Xeed. Autonomous observation records requests, due times and recomputation outcomes in its persistent runtime store. LunaResponsesProvider reports measured input/output tokens and latency, but the subscriber AXENT composition does not durably attribute those provider usages to FR-26. The current observation-loop path, JEV calls, acquisition fees and storage also do not form a complete per-tenant monthly cost ledger. This is not a missing entitlement adapter: adding a complete provider/accounting ledger would exceed this integration slice. No monthly cost or margin is claimed or invented.

## Production and real E2E

Production verification is recorded separately after the exact green main SHA is deployed. Real Google login, invitation redemption, tenant A/B isolation, real Xeed observation and autonomous enrollment remain unexecuted until the operator selects the blank Google accounts and completes verified sign-in. No synthetic principal, focus, market or source rights will stand in for that evidence.
