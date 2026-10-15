# Admin technical debt — 2026-10-15

## Confirmed defects and repairs

| Debt | Evidence before repair | Change |
| --- | --- | --- |
| Marketing commands buffered before checking a character count | A schema-valid Unicode command below 1024 JavaScript characters exceeded 1024 UTF-8 bytes and still reached the service | Incremental byte cap, cancellation and 413 before owner-service writes |
| Unbounded upstream JSON in Admin proxies | Oversized successful responses were accepted by marketing, customer and staff handlers | Shared 1 MiB response cap; no raw JSON body is fully buffered before checking its byte count |
| Request/upstream error conflation | Malformed successful service JSON returned user-input 400 in three routes; malformed denial bodies could lose their 403 status | Request syntax/size errors remain 400/413; invalid successful service bodies return 502; known denial statuses remain denied |
| Arbitrary upstream error details forwarded to the browser | Marketing returned an arbitrary `reason` verbatim | Exact allowlist of documented runtime refusal codes, generic fallback |
| Frontend absent from CI | Existing workflow ran Python, Graphify and secrets but no npm checks | New frontend job: locked install, all tests, TypeScript, i18n, build and actual Next HTTP regressions on Node 22 |

Three duplicated bounded-read loops and the projection migration adapter now
use `lib/admin-json.ts`. It counts actual bytes without trusting Content-Length,
rejects malformed UTF-8, retains the prior JSON BOM rejection, releases reader
locks on every path and cannot let failing/non-settling cancellation mask the
original rejection. A dedicated regression caught a non-settling cleanup during
implementation; it was corrected before final validation.

## Regression evidence

The first 20 HTTP cases ran against the preceding production build: **9 failed,
11 passed**. Its affected handler sources are identical to this branch's base
`50f43fb` (the intervening merged changes do not touch these handlers). The same
20 cases pass after repair; expanded coverage has **28/28 passing**.

The HTTP suite boots the actual production Next build with a temporary loopback
upstream. It checks valid reads and writes, request rejection before owner
commands, existing primary/step-up pairing, absent-step-up denial, error reason
allowlisting, 401/403 continuity, bounded successful responses and JSON/legacy
projection compatibility with UNKNOWN intact. Credentials are plainly marked
non-issued test strings, providers/databases are absent, and no production
mutation or mail can occur. This is transport evidence, not a test of the
owning service's domain authorization.

`tests/admin-json.test.ts` supplies eleven focused cases, including all split
positions of a multibyte payload, exact byte boundaries, early stop before later
chunks, lying Content-Length, failed/never-settling cancellation, transport
failure, malformed/truncated UTF-8, empty/BOM JSON and invalid configuration.
The full frontend suite has **326 passing tests** (315 existing + 11 new).
Production build, TypeScript and the 2413-entry six-language inventory pass.
Local Node is 24.14.1; Node 22 execution is assigned to the new CI job, matching
the experience Dockerfile. Local Node 24 is not claimed to prove Node 22 parity.

Local diagnostic logs are under `D:/AXIGNAL/_tmp/admin-debt-*.log`; no private
payload, production credential or raw store is committed with these changes.
Complete local validation: frozen sync, Ruff format (1563 files), lint, mypy
(559 source files), Architecture Guard, all governance gates and diff whitespace
checks pass. The full Python suite has **2408 passed, 7 skipped, 2 existing
warnings**, 815.52 seconds. It used a fresh verified child of
`D:/AXIGNAL/_tmp` as pytest's temporary directory. AST-only Graphify update:
21948 nodes, 60880 edges; generated output remains ignored and no model/API was
used. No required gate was removed, suppressed or weakened.

## Scope and limits

Branch `codex/admin-technical-debt` reuses the attached worktree, based on
canonical main `50f43fb`. The original dirty checkout is untouched. No shared
AXIGNAL tool/canvas, subscriber/demo source, client component, domain policy,
credential, role, scope, model, dependency version or production data changed.
Existing authorization remains server-owned; this codec grants no authority.
The sixteen missing executive source projections remain a separate coverage gap.

The existing real-data preview still uses the original operator BFF. A proposed
extra read-only bridge was rejected by automatic approval review because it
would convert a bearer into an Admin cookie and create a new credential path.
It was never run and its scratch source was removed. No workaround, new runtime
tunnel or extracted credential was used. The repaired BFF is verified using the
compiled isolated HTTP harness; the preview is not misrepresented as exercising
that new BFF against production data.

Regression risk cannot be mathematically eliminated. Tests cover the reproduced
defects and preserved contracts; finite payload caps intentionally reject
oversized responses rather than presenting partial or invented operational data.
GitHub branch protection and production deployment are outside this change.
