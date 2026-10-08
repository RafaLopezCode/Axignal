# 058 — Subscriber authority to observation materialization

Authority: MASTER §§5–7, 14–15, 20, 53.2–53.6; Constitution IV–VIII;
ADR-0018/0084/0087/0088; specs 049/051/052/054/055.

## Outcome and clarifications

Derive bounded enrollment/attention from existing subscriber authority; check
without writes/provider calls; execute exactly one existing T12 tick without
recurring activation. No manual identity/market arguments, new runtime/queue,
fake production identity or canonical activation.

Subscriber stores/admitted Organization/current entitlement are authority;
JSON files are disposable operational snapshots. Autonomous authority does not
depend on a browser session. Pilot uses its recorded redeemer while still an
identity-backed member; Billing uses the unique current identity-backed Principal
for its Tenant. Ambiguity fails closed, never select the first membership.
Capacity ordering remains (created_at, focus_id). Paused/removed/legacy or
noncanonical Focus never enrolls.

Attention uses current reusable public observations and explicit service area/
buyer audience, through existing MarketScope/capability/geography contracts.
No HQ/address/domain/country inference or default market. Narrow bootstrap may
consume schema.org Service areaServed NUTS identifiers and audience as POTENTIAL
attention, never reach truth. No usable scope/capability/adopted source gives
ATTENTION_NOT_READY. Economic Operating Model/Capability-Specific Reach is not
integrated at base 72f19d2; do not reimplement it. Its future contract can replace
this narrow adapter. Organization/site seed and market readiness stay separate.

## Acceptance

NO_ELIGIBLE_FOCUS creates no files/database/flags/provider work. Check is truly
read-only and redacted. Reconcile is deterministic, bounded (1000 identity
contexts, 100 Foci), restart-safe and idempotent, locally locked, with validated
staging/fsync/atomic replacement and a hash manifest committed last. POSIX
permissions: root:www-data 0640. A corrupted snapshot can be repaired only from
valid desired state. Revocation reconciles existing files to empty but pristine
no-Focus installations stay absent.

First Proof requires current ready materialization, runs one existing daily
tick and distinguishes technical execution from economic findings. Existing
day idempotency, budgets/fencing/source rights remain authoritative. Production
checks membership/entitlement/capacity/Focus/Organization before work and again
before acquisition/recompute; stale files and pending debt cannot bypass scope.

Real-shaped OIDC/Pilot/locator/admission/Focus E2E derives files, validates,
executes controlled T12, reaches Brain/continuity then independent AXENT read.
Two tenants, research feedback, revocation, capacity, unknown/source/cost,
atomicity/concurrency/restart and MCP model-zero are mandatory.

Development done differs from real First Proof executed. Exact isolated
candidate uses controlled providers, no ports/secrets/production DBs. CTO owns
merge/deployment/legitimate first Focus/manual proof and later activation.
