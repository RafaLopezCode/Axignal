# Validation and convergence — 2026-10-11

IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING.

## Evidence

- Full Python suite: 2,112 passed, 7 skipped in 741.36 seconds (Windows/Python 3.12).
- After the full run, added expired-step-up/subscriber-credential and legacy-migration regressions:
  integration + administration: 10 passed; final administration including migration: 5 passed.
  These supplement the full run; they are not a second full-suite result.
- Frontend: 266 tests pass, typecheck passes, locale inventory 1,834 entries / no missing.
- Production Next build passes; 528 knowledge HTML pages localized.
- Frozen uv sync, Ruff format/check, mypy (481 files), Architecture Guard and all eight governance gates pass.
- Graphify AST update: 19,629 nodes / 58,431 edges; no semantic extraction/API.
- Real local Admin browser against Next, runtime HTTP and SQLite: PRIMARY write denied;
  paired independent step-up; create/copy fragment link; cancel/confirm revoke; desktop
  1440×1000 and mobile 390×844; no document horizontal overflow or page errors.
- Browser integration: private signup fragment → controlled Google redirect/exchange →
  existing subscriber identity/session → one-use pilot redemption → confirmed capacity 1 →
  organization attention → real authorized worker → first proof → visible Observatory →
  Admin reflects redeemed tenant and observation. Sources and evaluator are controlled.
- HTTP integration additionally checks an organization saved before access is automatically
  retryable after confirmed pilot capacity, tenant isolation, historical organization preservation
  after grant revocation, transactional audit rollback, durable quota and idempotency.

Read machine-readable evidence in evidence/browser-qa.json and
evidence/onboarding-browser-qa.json. Screenshots contain only disposable test state,
no invitation secret, digest, real customer or provider credential.

## Security and architectural assessment

Extends PilotAccessService and its existing SQLite store; no service, economic truth
store, MFA mechanism, provider integration or dependency is added. AO-01 authenticates
before tenant reads/input parsing. Existing customers:write and SENSITIVE risk require
fresh STEP_UP. Next pairs that proof with the primary identity for every mutation.
Support may read customers but cannot issue/revoke or obtain subscriber billing details
without billing:read. AO-09 retains its existing customer operational projection policy.

Issuance, digest persistence, success audit and receipt share a transaction. Retrying an
issued command returns its reference without a new secret; a lost response requires
explicit revocation and reissuance. Admin issuance quota is 20 successful commands per
actor/hour. Revocation and redemption serialize with BEGIN IMMEDIATE. Eight simultaneous
redeemers produce one grant. Duplicate redemption now rejects, as explicitly required,
without withdrawing the existing grant. Fixed pilot capacity and lifetime remain 1/60 days.

Read joins are bounded to 500 memberships, 500 invitations, 500 grants and 100 latest audit
events. This P0 does not introduce pagination or financial mutation. Missing evidence
remains unavailable/UNKNOWN. First proof can exist while legal identity is unresolved;
those states are shown separately.

## Convergence

FR-001–FR-007 implemented and covered; FR-008 respected by labeling controlled providers.
No unbuilt application requirement or known activation/capacity failure remains in the
validated local scope. Production cutover, provider/account participation, deployed version
inventory and human visual acceptance remain explicitly open. No merge or deployment
is claimed. PR #200 remains OPEN at 0f772022ca8198efeb5a61b91da0a09952d2e58f.

Seven skipped tests: six POSIX-specific contracts (including deployment/step-up file mode)
and the optional typesafe_sdk provider. Linux CI must verify its applicable gates.

