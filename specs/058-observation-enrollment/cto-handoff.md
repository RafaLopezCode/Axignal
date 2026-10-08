# 058 — CTO handoff

Base: 72f19d2103554dd1d841a0ffbbd0a9b549ef295c (Product MCP and 055 included).
Implementation candidate: 5dbff8ddbf3356f49e2aa9bc752a3d1ecc672df2.
The final review head is rebuilt and checked as an exact candidate;
its SHA/image/container evidence and final CI are recorded in the PR description.

## Reviewable result

`tools.runtime.observation_enrollment reconcile|check|first-proof` takes data,
config and optional nonsecret settings paths only. Its owner is tools/runtime;
subscriber identity/membership, existing Pilot/Billing entitlement/capacity and
canonical admission remain authority. No new principal or service-account model.
Pilot selects its existing redeemer; Billing requires one current identity-backed
member. Expired browser sessions do not stop autonomous authority. Ordering uses
the existing active portfolio policy. Ambiguous, revoked, paused, removed or
noncanonical contexts fail closed.

JSON is disposable private operational materialization. Attention uses current
authorized reusable public website observations and explicit Service/NUTS/audience
claims through existing contracts, POTENTIAL only. There is no HQ/default-country
inference, reach model or fabricated fit. Missing capability/scope/adopted source/
rights/known cost stays ATTENTION_NOT_READY. The currently wired TED source is the
only routable port in this bootstrap. A future integrated capability-specific
reach contract can replace the adapter. Unknown markets can leave enrollment
present and attention empty; they cannot authorize a successful First Proof.

Check opens existing SQLite stores in mode=ro, without directories/schema init,
provider calls or flags. Reconcile is bounded, deterministic and locally locked;
staged fsync/atomic replacement commits the hash manifest last. Interrupted pairs
are rejected and repair derives only from current authority. Linux files are
root:www-data 0640. No Focus/no previous snapshot means no files. Reconcile after
revocation removes entries rather than preserving stale authorization.

First Proof invokes one existing T12 tick, preserving its budgets, daily lease,
fencing, cadence, retrieval replay and zero-model scheduler. It does not enable
recurrence or AXENT. Production rechecks membership, current entitlement/capacity,
Focus and canonical Organization at each tick, again before source acquisition
and Brain recomputation. Pending debt cannot escape revoked scope. A manifest
generation must also match current derived state before the service enters T12.

The real-shaped fixture follows OIDC → Pilot redemption → product locator →
independent EvidenceAdmission/canonical Organization → private Focus → derived
files → T12 → real Brain/continuity → independent AXENT read. The feedback case
starts with an AXENT gap, consumes the private ResearchRequest in that tick,
updates continuity and verifies a later user-requested read. No auto-requery or
direct Brain publication. Revocation/forged context/capacity/expiry/ambiguity,
UNKNOWN, repair/concurrency/restart and read-only check are covered.

## Isolated evidence

Validation: frozen sync; ruff format/check; mypy (424 source files);
Architecture Guard and all governance gates; full suite **1856 passed, 5 skipped**
on Windows (all five POSIX checks pass in Linux candidate); frontend typecheck,
i18n (1414 entries, missing=[]), build (7 acquisition tests, 528 localized pages).
Graphify AST update/query/explain/affected/path/check-update/multigraph diagnosis
completed; extracted graph 17239 nodes/46767 edges. Product MCP E2E preserves
/mcp, /oauth/*, /.well-known/*, /account/connect, Pilot/Billing entitlement,
read-only/tenant isolation/revocation and model-zero reads. No Product MCP or
tools/runtime/service.py change relative to the base.

Own initial root:
`/srv/axignal/candidates/observation-enrollment-058/5dbff8ddbf3356f49e2aa9bc752a3d1ecc672df2/`.
Runtime image is built from git archive with its exact SHA label. A separate
validation derivative adds only locked pytest/dependency versions; application
imports use /app from the exact runtime image, fixtures/source inspection /src.
All executing containers have network=none, no published ports or mounted secrets.
Fixture data is separate from production. The only production-data mount is
kernel-enforced read-only for the new check command; config/settings are also RO.

Linux CI identified Windows-only msvcrt attributes absent from Linux type stubs.
Both platform-specific lock modules now load through import_module, preserving
the same OS APIs and locking behavior without type suppressions or gate changes.
The corrected Windows lock/MCP/runner regression is 24 passed, 5 POSIX skips;
Linux CI and the exact corrected candidate validate that final head.

Linux candidate: **29 passed**, including all four POSIX runner tests and the
root:www-data permission check. Initial test tmpfs was noexec; the validation
mount was corrected to exec for the existing fake executable runner. Application
and canonical deployment were unchanged by this correction.

Controlled First Proof: 2 tenants/Foci; 32 executed work items; 10 controlled
source calls; 36 evidence receipts; 6 new POTENTIAL candidates; 2 actual Brain
recomputations; 2 ResearchRequests OBSERVATION_COMPLETED; 2 independent controlled
AXENT model calls. Replay ALREADY_COMPLETED. **Real source calls 0, real model
calls 0, production canonical writes 0.** These are controlled fixtures, not
production economic findings. NO_ELIGIBLE_FOCUS check/reconcile/first-proof also
leave fresh empty data/config roots without files and calls.

## Canonical boundary and remaining human step

Read-only production check returns NO_ELIGIBLE_FOCUS, eligible=0, enrolled=0,
attention=0, model/provider=0, AXENT unavailable. attention.json/enrollment.json
remain absent. current and DEPLOYED_SHA remain base 72f19d2. Canonical runtime,
experience and landing container IDs/images stay unchanged and healthy. AXENT,
observation, contracting and Stripe live flags stay false. The already-existing
timer remains active/enabled with observation flag false; activation is unchanged.

Development closure is distinct from real First Proof executed. There is no
legitimate production subscriber Focus yet. Do not create a fake Focus, Principal,
Tenant, enrollment or market to change that result. After CTO review/merge and
authorized deployment, a human signs in, obtains entitlement and creates a real
Focus through the existing locator/admission flow. Reconcile/check can then report
whether current evidence permits one manual First Proof. The runbook in
deploy/production/README.md gives the CTO sequence and history-preserving kill
switch. AXENT and recurrent activation follow inspection, under CTO authority.

canonical production changed: NO
current changed: NO
DEPLOYED_SHA changed: NO
canonical containers changed: NO
AXENT production activation changed: NO
scheduler activation changed: NO
