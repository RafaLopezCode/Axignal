# Public product functional closure — CTO handoff

Base: canonical `origin/main` at `203bc3d19c291720286b487b7914d1fc5c68dea3`.
Scope: finish Spec 060/061 functional wiring while preserving Claude's accepted funnel, navigation, pricing and fictional guided Panorama. No changes to Jev, cognition providers, semantic contracts, projection wiring or decision lab. Historical work remains on its original branches.

## Delivered behavior

| Surface | Runtime contract | Actual behavior |
| --- | --- | --- |
| Contact | GET `/api/contact/status`, POST `/api/contact` | Verified disabled channel has no form/mailto; enabled channel validates and persists private request, returns reference, supports idempotent retry and rejects a fourth request within the rate window. |
| GDPR | GET `/api/gdpr/status`, POST `/api/privacy/request` | Same channel boundary; all seven canonical categories exercised in a browser. Registration is not legal acceptance, resolution or evidence admission. |
| Existing brief/newsletter | GET `/api/weekly-brief/status`, POST `/api/weekly-brief/requests` | Hidden when unavailable. Existing AO-15/AO-16 request ledger is used. Processing notice and optional unchecked newsletter consent are separate. Only explicit consent creates CONSENT_GRANTED. No newsletter platform or automatic delivery added. |
| Login/signup | GET `/api/auth/status`, POST `/api/auth/start` | Loading/unknown distinguished from unavailable; each provider independently gated. Synthetic Google AVAILABLE + ChatGPT UNAVAILABLE exercised; real canonical start generated an approved provider redirect without creating a session. Both unavailable also browser-verified. |
| Trust/policies/privacy | Existing routes/modal | Approved controller AXIGNAL / Spain; no invented NIF, email or address. Actual 90-day private requests and identity cookies described; receipt/delivery/resolution distinguished. |
| Funnel/example/knowledge/404 | Existing accepted routes | CTA to signup/example/Contact and Knowledge navigation exercised; Panorama remains labelled fictional. Unknown route HTTP 404 + noindex, with branded recovery links. |

The backend previously compared a governed `secret://` credential locator to the filesystem path, making valid SMTP authority impossible. The locator now comes from `AXIGNAL_CONTACT_SMTP_CREDENTIAL_REFERENCE`, independently of `AXIGNAL_CONTACT_SMTP_PASSWORD_FILE`. Both must be present, match the fresh AO-18 registry authority/environment/scopes and resolve the private file. Authorization is checked before reading a credential or attempting delivery. Production remains unconfigured and disabled.

## Browser evidence and boundaries

Product Design Audit applied with AXIGNAL Design Director PRESERVE mode. Actual screenshots and DOM checks at 1440, 1024, 768 and 390; no horizontal overflow in the changed request/receipt/auth surfaces. GDPR receipt exercised in ES/EN/DE/PT/FR/IT. Privacy modal Escape returns focus. Empty validation, real rate-limit rejection, closed channels and connection-error retry exercised.

Enabled tests used an isolated development registry, SQLite data and `.invalid` identities. SMTP transport was replaced only in the preview harness with a controlled sink; AO-18 authority checks, request admission and persistence were real. No email was sent externally. Seven GDPR records, three admitted rate-window Contact records and one recovered Contact retry are present in the synthetic ledger. Brief ledger demonstrates the first request had no newsletter consent and only the second created the versioned optional consent event.

No external identity exchange or production account session was completed. Real provider credentials/configuration and production E2E are CTO deployment responsibilities, not claimed here.

## Validation

- Python full suite: **1907 passed, 5 skipped** (525.68s); the skips are the five POSIX-only filesystem/scheduler checks to exercise in the exact-SHA Linux preflight.
- Public request backend contracts: **26 passed**.
- Frontend suite: **141 passed, 0 failed/skipped**; includes real request proxy/receipt/origin/limits/notice/optional consent coverage.
- TypeScript: passed. i18n: **1370 entries, missing []**. Production frontend build: passed, including localized Knowledge prerendering.
- Production npm audit: **0 vulnerabilities**.
- Ruff format/check, mypy (**438 source files**), Architecture Guard and governance: passed.
- Graphify update: AST-only, no model/API cost; generated ignored outputs do not enter the diff.
- An initial Windows run could not use the default temporary directory. The full suite was rerun with an owned writable basetemp and passed; no gate was weakened.
- Exact candidate SHA/image labels, Linux POSIX results and isolated preflight results are recorded in the PR, after the immutable commit exists.

Product MCP routes `/mcp`, `/oauth/*`, `/.well-known/*`, `/account/connect`, PilotGrant/Billing entitlement, tenant boundaries and read-only semantics are unchanged from canonical main. Full regression gates include their existing tests; this slice introduces no MCP cognition calls or Luna reads.

## Prototype residue

Removed local draft/download submission and its obsolete contract/tests; productive copy claiming requests are never sent or authentication remains planned; false unpublished-controller/country disclaimers; always-enabled unavailable Google affordance; raw rejection codes and cramped receipt layout.

Deliberately retained: labelled fictional guided Panorama and prepared Axent explanations; editorial Knowledge language; historical unused translation entries; internal conservative prepared-provider fallback; closed payment launch notice. These are not mistaken for delivered production sessions, purchases or live observation.

## Production and integration

No merge, push to main, cutover, production data/configuration mutation or feature activation. Canonical current and DEPLOYED_SHA stay `1775382f2340bb3c9af5749dc0c6f9f30be38910`. Production runtime/experience/landing container identities are unchanged. Stripe, contracting, PUBLIC_LAUNCH, AXENT and scheduler are unchanged. Candidate uses its own exact-SHA directory, images, names and empty private data; never canonical current or secrets.

After CTO review: merge, deployment with governed provider configuration, then production E2E. Unconfigured Contact/GDPR/brief/auth remain honestly unavailable until their owning authority enables them.
