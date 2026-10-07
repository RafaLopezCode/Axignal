# 055-T10/T11 — CTO handoff (2026-10-08)

Implementation and isolated preflight complete. Canonical deployment, AXENT
activation and autonomous scheduler activation remain pending CTO authority.

## Git and scope

Branch: `codex/axent-feedback-055`.
Base: `460e2f3ca1e15664d1ca8e7b9af42e6b9d1c1b0e`.
The PR head is the exact release candidate; final SHA and final preflight
container identifiers are recorded in the PR description and delivery.
No main update, merge or canonical cutover was performed.

Only the existing AXENT research/observation seam and optional production
composition changed. Subscriber HTTP, Product MCP, OAuth, Organization
Admission, GLEIF, billing and Stripe implementations are unchanged.
The existing observation entry script now optionally mounts the subscriber
nonsecret configuration read-only to recheck entitlement. Timer, service,
scheduler authority and activation flag are unchanged.

## T10: attention through existing authority

- Schema: private request binds tenant, Focus, canonical Organization, family,
  geography, normalized intent, dependency fingerprint and creation time.
  Lifecycle persists status, attempts, last attempt, cooldown, outcome, linked
  lead IDs (including same-family descendants), evidence keys/fingerprints and
  compatible shared-work key. Append-only transition rows retain timestamp and
  existing tick token; no prompt or chain of thought is stored.
- Consumer: `application/axent/research.py`, composed by
  `tools/runtime/observation_daily.py`. Rechecks enrollment principal/tenant,
  PilotGrant or verified Billing entitlement, active authorized Focus, capacity
  and admitted Organization via the existing economic reader.
- Idempotency: tenant/Focus/Organization/scope/intent/dependency hash; read day
  and operational coverage gaps are excluded. The unchanged gap stays one
  request even on later days.
- Bounds: seven-day lifetime; three attempts; one-day cooldown; at most 40
  eligible rows per tick, one per Focus, four per tenant and four per
  Organization/family. Existing server-owned frontier ordering wins; no
  model-defined priority, source, target, retry or cadence reset.
- Budget: existing T12 action/HTTP/family/source limits. Unknown acquisition
  cost gives STOPPED/BUDGET_BLOCKED, zero child work and zero attempt increment.
  Budget/cadence deferrals wait without spending an attempt.
- Lease/fencing: existing T12 claim only. Lifecycle update and transition append
  use an attached-database BEGIN IMMEDIATE transaction checking token,
  completion and expiry. A restarted worker can reclaim; stale final writes
  fail. No second lease or queue.
- Shared work: reuse only existing compatible EB-07 work under live Prime
  authority and matching state fingerprint/public scope/family. Attach opaque
  requester reference; no private request text/tenant/Focus in shared payload.
  Pending shared work suppresses duplicate ordinary/follow-up dispatch.
- Outcomes: OBSERVATION_COMPLETED means acquired evidence, never truth;
  UNRESOLVED/NO_NEW_EVIDENCE is terminal; failures remain
  FAILED_RETRYABLE/UNAVAILABLE under cadence/attempt limits; rights/source/
  unsupported scope/expired/authorization stops are explicit. Superseded
  dependencies become OBSOLETE, without inferring the old question is answered.
- Feedback: unchanged evidence/admission/currentness/recomputation/Brain
  continuity path, then a later independent AXENT read. No direct Brain write
  by the consumer and no automatic AXENT/model requery.

The two-tenant HTTP E2E uses actual identity, PilotGrant, admitted canonical
Organization, configured access, governed recorded TED acquisition, shared
receipt reuse, separate continuity checkpoints and separate AXENT caches.
Model output is a deterministic provider fixture in CI. A separate EB-07 test
demonstrates two private requests attaching to one eligible public work item,
one existing batch authority and no private metadata leakage.

## T11: bounded, reversible composition

Model `gpt-6-luna` through `luna-responses` -> CognitiveProvider/ModelRouter.
Existing flag `AXIGNAL_AXENT_GROUNDED` defaults false. Runtime and experience
must receive the same flag using `compose.axent.override.yml` alongside
existing compose/subscriber overlays. No overlay was applied to canonical
production.

Key source: existing host `/etc/axignal/secrets/openai_api_key`, read-only at
`/run/secrets/openai_api_key`, group 1991. Only the concrete SDK reads it;
no copying into configuration, environment, Git, docs or logs. SDK dependency
comes from the existing frozen research-canary-live group; provider is lazy.

Route: existing POST `/subscriber/organizations/{focus}/axent`, via
`/api/subscriber/axent` in experience; authorization remains Principal ->
Tenant -> entitlement -> active authorized Focus. Anonymous calls fail before
provider dispatch.

One synthesis turn: <=1 attempt, no retries, 15-second timeout, 8,000 UTF-8
prompt bytes (including schema), 16,000 conservative input-token ceiling,
500 output tokens. No tools, response storage disabled, low reasoning effort.
No evidence/deterministic/cache/precheck/unknown-cost paths make provider calls.
Durable quota reservations: 50/tenant/day, 500 globally/day; concurrent workers
serialize reservations, crashes retain them. Observation ticks make zero model
calls; no cross-layer model cascade.

Example operator rates: USD 0.125/M input (includes cache-write ceiling), 0.50/M
output, configured max call cost 0.003. The theoretical reserved maximum is
0.00225 USD/turn, 0.1125/tenant/day and 1.125 globally/day. Audit cost is a
conservative estimate, not an invoice; prices must be revalidated before CTO
activation. No regional processing or Fast mode is requested.
Source: https://developers.openai.com/api/docs/models/gpt-6-luna (2026-10-08).

Audit: provider/model/purpose, hashed tenant/Focus/request correlation, unique
call reservation, usage, estimated cost, latency, outcome, redacted error
class, verified route (including abstention/extractive) and dropped claims.
Missing key/rates/usage, timeout, malformed output, bad references or failed
verification cannot manufacture an answer. Schema, evidence refs, epistemics
and currentness remain mandatory.

## Validation

- Frozen uv sync: passed.
- Focused final T10/T11 + real feedback E2E: 29 passed (11.54s).
  Includes 14 T10 cases, 14 T11 cases and one two-tenant integration case;
  loop prevention, budget, restart/fencing, obsolescence, privacy/shared work,
  provider quota/usage/key boundaries and offline preflight replay.
- Extended AXENT suites + grounded/feedback integration: 53 passed (11.58s).
- Full pytest: 1835 passed, 4 POSIX-only skipped on Windows (479.00s).
- The five scheduler deployment contracts, including all four Windows skips:
  passed in isolated Linux candidate (8.501s). Initial runner used Docker's
  default noexec tmpfs; rerun grants exec only to isolated test scratch so the
  existing fake Docker executable can run. No gate/code relaxation.
- Ruff format: 1236 files already formatted; Ruff check passed.
- mypy: 422 source files, no issues.
- Architecture Guard: OK, no suppressions.
- Governance: all eight gates pass (architecture/deps/docs/graphify/hygiene/
  no-generated-data/spec/terminology).
- Graphify AST-only update passed, 17135 nodes. Explain shows extracted
  observation_daily.run_once -> ResearchConsumer composition, with existing
  TickClaim/SharedObservationWorkMemory/ResearchRequest interfaces. Undirected
  path shares LeadOutcome with run_daily_tick. A directed path through the
  persisted ledger is not represented by AST extraction; functional chain is
  established by the real E2E and Architecture Guard, not invented graph edges.
- Frontend gates: not applicable; no apps/frontend file changed.

## Candidate proof and canonical preservation

Initial validated candidate: `d8dff89f4707dcc53eb57e0a7a9bf947186b8d05`.
Host: `axignal-production` / `187.124.220.48`.
Own release root:
`/srv/axignal/candidates/axent-feedback-055/<candidate-SHA>`.
Exact git archive -> frozen subscriber-runtime Dockerfile -> revision-labeled
`axignal-runtime:<candidate-SHA>`. No canonical compose command was executed.

Disabled/enabled runtime containers use network none, isolated <mode>-data,
read-only filesystem and secret bind, nonroot 33:33 + group 1991, no published
ports. Health reports exact candidate SHA and closed write surface. Flag false
configures no provider; flag true recognizes BudgetedReasoner. Both modes:
MCP anonymous 401, AXENT anonymous 403, Admin anonymous 401, OAuth metadata 200.
The /account/connect page belongs to the unchanged experience frontend;
runtime-only probe returns 404 and does not claim frontend navigation coverage.
Existing full MCP HTTP/E2E contracts cover OAuth flow and connection/read
authority, including PilotGrant/Billing isolation, revocation and model_calls=0.

Live oneshot uses only its own live-data and public synthetic corpus; network
axignal_prod_internal allows the bounded API attempt but no ports. Existing
host key is mounted read-only; no production databases/users mounted.
One provider call, one request, one controlled source result,
OBSERVATION_COMPLETED, one recompute callback, zero external source HTTP and
zero canonical writes. Initial measured usage: 405 input / 124 output tokens;
estimated USD 0.000112625, verified route MODEL, no error.
The controlled callback does not claim a real live Brain snapshot; actual
Brain continuity is proven in the deterministic two-tenant HTTP E2E.

Final head will be rebuilt and independently preflighted after this handoff
commit. Each candidate data root refuses any second live attempt, even on
failure. Final exact SHA/usage/container/data proof is recorded in the PR;
the initial candidate's evidence is never substituted for the final head.

Canonical baseline before/after must remain:
current release and DEPLOYED_SHA = 460e2f3ca1e15664d1ca8e7b9af42e6b9d1c1b0e.
Runtime ID a6282ae70566e566ec63ae18397b196bfffc9a1001b106acd8ea7232a5e51911;
experience ID 1c372aaeafcaf5ce7eb7eab3ecfd5c5e346defa26f8b3839e106415c461294c2;
landing ID ae167a3b4ce31d691ec7e3fb9176877128d9d64407b6e0f1e9b241030688aa9e.
AXENT absent/off; observation flag false; existing timer active/enabled.
Contracting/live Stripe/public launch flags are unchanged.

## CTO activation boundary

Review/merge and canonical deployment remain CTO decisions. Before activation:
revalidate tariffs and capacity, review secret permissions and egress,
apply existing optional composition with matching runtime/experience flag,
then separately authorize real scheduler enrollment/activation if desired.
Disable AXENT with the same flag on both services; no data migration rollback
or new daemon is required. This handoff does not authorize that cutover.

canonical production changed: NO
current changed: NO
DEPLOYED_SHA changed: NO
canonical containers changed: NO
AXENT production activation changed: NO
scheduler activation changed: NO
