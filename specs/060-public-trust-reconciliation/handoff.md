# CTO handoff — backend closure and coordination boundary

Branch: codex/public-trust-reconciliation.
Base: 1775382f2340bb3c9af5749dc0c6f9f30be38910.

Shared frontend changes are quarantined in a separate commit/branch:
`b20a8a90e88ad13c1c81484c435955f855afbd89`
`codex/public-trust-shared-ui-review`

**SHARED_UI_CONFLICT — DO NOT INTEGRATE BEFORE CLAUDE REVIEW**

The backend PR contains no Landing/PublicShell/Trust/pricing/auth presentation,
Panorama/dashboard/navigation/translations or Next public-form wiring changes.
The original 1,445-line public-copy inventory remains in the preserved UI commit.
Its rendered audit (48 route/viewport captures plus real request/error screenshots)
is historical evidence of that preserved work, not acceptance of Claude's final UX.
No further shared UI edits or visual redesign were made after the coordination stop.

## Functional backend

POST /api/contact and /api/privacy/request validate exact keys, locale, email,
category and control characters. Only POST writes; PUT/PATCH reject. Exact Origin
validation and 16 KiB body limit apply. Requests are durable private operations in
public-requests.sqlite3, separate from tenant and canonical economic stores.
Public response contains opaque reference, time, RECEIVED status and actual delivery
status; no sender, subject, email or body is returned. An equal requestRef replay
returns the same receipt without a second send; mismatched content rejects.

Limits: three requests per email/hour, 100 requests global/hour. Content is bounded
15–3000 characters and retained for 90 days. Intake and periodic runtime maintenance
purge expired records. There is no AI legal resolution, subscriber entitlement,
newsletter consent or canonical evidence admission.

ContactDeliveryPort is replaceable. The SMTP adapter verifies TLS, plain-text email,
server-owned recipients, header injection rejection and bounded timeout. Existing
AO-18 integration authorization/health/credential resolution/email:send scope must
pass before reading the password file or opening transport. Failed or absent delivery
keeps the receipt. Invalid infrastructure configuration does not discard valid requests.
Operational retrieval is a protected store operation, not a public inbox or new CRM.

## External configuration and deferred wiring

PUBLIC_CONTACT_CHANNEL = EXTERNAL_DECISION_REQUIRED.
No approved public Contact/privacy destination was found in the earlier read-only
production config/docs/infra/secret-filename/DNS investigation. No email was invented.

The adapter is ready for private AXIGNAL_CONTACT_SMTP_HOST, PORT (465 default), SENDER,
CONTACT_RECIPIENT, PRIVACY_RECIPIENT, USERNAME, PASSWORD_FILE and INTEGRATION_ID.
Use existing integration governance; no browser-supplied destination or credential.
No SMTP email was sent in tests. Controlled transports exercise success/failure/TLS.

Approved identity is controller=AXIGNAL, holder=AXIGNAL, country/domicile=Spain,
NIF=EMPTY / NOT PUBLISHED. These values do not authorize presentation edits here.
No lawyer review, certification, postal address, VAT, registry, DPO or phone was invented.

Public frontend and canonical edge wiring are deliberately deferred. Once CTO merges
Claude's work, rebase onto actual origin/main, inspect the resulting UX and connect
these private request APIs only where necessary. This backend PR does not claim the
public product closure is fully integrated. Newsletter reuses existing AO-15/16;
its flags and implementation are untouched.

## Verification

Final backend-only gate results, exact candidate SHA, image/container/network/data
and production invariant comparison are in the PR evidence. Prior combined-tree
verification passed 1,901 tests (5 POSIX skips) and 129 frontend tests; these historical
results are not substituted for validation of the backend-only candidate.

Preserve Product MCP: /mcp, /oauth/*, /.well-known/*, /account/connect, PilotGrant/
Billing entitlement, read-only tools, tenant isolation and zero Luna for MCP reads.
No production flag, scheduler, current symlink, DEPLOYED_SHA or canonical container
is modified by candidate testing or this PR. Production remains at base SHA.
