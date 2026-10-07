# Implementation plan

## Constitution and architecture review

Root reviewed MASTER, Constitution, ADR-0016/0017/0018/0021/0061/0084,
Graphify query and existing runtime/web contracts before implementation.
The design preserves one canonical Organization world, attention-only input,
admission, UNKNOWN, provider neutrality and separate private/payment authority.
**Disposition: PASS for this bounded composition.**

## Composition

The Python HTTP host composes 049/047/050 through a new subscriber facade.
It validates request schemas, authenticated sessions and write-origin/transport
policy, delegates authoritative operations, bounds body size, and emits only
redacted no-store payloads. Existing Admin and Customer Zero routes retain their
original authority. New routes use `/subscriber/` internally and
`/api/subscriber/` in the first-party web proxy.

The host explicitly loads a whitelisted subscriber settings file only through
`AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE`; it does not source a shell env file or
enable legacy Stripe ingress using partial subscriber settings. Subscriber
composition is attached when explicitly enabled. Default missing plans are
NOT_READY and default missing billing configuration is NOT_CONFIGURED.
Public observation currentness uses the declared `051-v1` read policy: stale
after 30 days and historical after 90 days, retaining UNKNOWN and already stale
or historical states. This is a conservative presentation/reuse policy for
public records; it establishes neither source completeness nor guaranteed
current business truth. It grants no billing, identity, rights or model
authority. Billing snapshots have a separate five-minute freshness policy.

Signed billing ingress forwards bounded exact raw bytes to the independent
subscriber webhook verifier; no session, browser return, metadata or JSON
reserialization can replace signature and provider readback. Output reads
remain free of external billing mutation. Fiscal prerequisites stay explicit;
exclusive prices do not by themselves calculate applicable VAT.

Next server routes forward opaque cookies to the trusted backend, validate
response shapes and provider-host redirects, and set secure first-party cookies.
PKCE/state/session credentials never reach client state, local storage or logs.
The new portfolio UI consumes the actual subscriber projection and billing
state, uses incumbent brand tokens/components, and permits evidence inspection.
AI SDK 7 remains a bounded typed-presentation layer; a missing model cannot
invent knowledge or prevent deterministic evidence-backed reading.

## Pilot preparation extension: plan and architecture review, 2026-10-07

Direct human clarification: blank A/B, explicit Save, changeable authorization
for testing only. Graphify and AO-01 session/proxy boundaries were inspected.
Use an application snapshot/store contract and append-only SQLite adapter,
separate from subscriber identity, PilotGrant, Billing and AXIGLAND. One bounded
internal Admin endpoint checks CUSTOMERS_READ/WRITE and optimistic revision;
one same-origin Next proxy uses the existing HttpOnly Admin session. No public
Admin route is added. Preserve panel geometry; add Save and saved/draft/error
receipt. General Admin mutation denials remain intact.

Constitution/architecture review: PASS. Private operational preparation is
neither economic truth, an email allowlist, paid capacity nor a messaging flow.
No Brain geography/provider change. Validate durable save/replacement/clear,
restart/conflict/authority negatives, bounded proxy, rendered desktop/mobile/
keyboard and required deterministic gates.

## Paths

- `tools/runtime/config.py`, `tools/runtime/service.py`,
  `tools/runtime/subscriber_http.py`.
- `tests/integration/test_subscriber_http.py` and
  `tests/contracts/test_subscriber_e2e_composition.py`.
- `apps/web/experience/lib/subscriber-contracts.ts`,
  `subscriber-server.ts`, new subscriber/auth routes and component/styles.
- Existing login component and public-auth start/status contracts only where
  necessary to connect configured identity. Existing unavailable-mode tests
  remain valid; new connected-mode negative tests are added.
- Deployment env examples and operations runbook: names/configuration only,
  no credential values and no deployment.

## Validation

Use the already verified 1,404-test candidate as the pre-change baseline.
Focused services/HTTP/web tests precede full frozen sync, Ruff, mypy, pytest,
Architecture Guard, governance and build. Browser render compares adjacent
accepted grammar on desktop and narrow view. Full pytest runs without parallel
heavy jobs because the earlier concurrency timing failure is recorded.

## CTO integration boundary (2026-10-07)

Reconcile this extension against origin/main containing Product Web MCP (PR #156). Preserve /mcp, /oauth/*, /.well-known/*, /account/connect, OAuth/PKCE, tenant isolation, PilotGrant/Billing entitlement, read-only behavior and zero Luna calls for MCP reads. Implementation ends at tested PR, isolated candidate/preflight and CTO handoff. No merge, main push, current-link change or canonical production container replacement is authorized. Google test accounts remain blank until explicitly saved by the operator; no real Google/A/B E2E is claimed before that selection.
