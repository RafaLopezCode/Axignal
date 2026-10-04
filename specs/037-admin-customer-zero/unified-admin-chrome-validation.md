# AO-24A: unified Admin framing, typography and recovery

Date: 2026-10-04. CURRENT_TASK = AO-24A. Main implementation; local only.

## Problem and cause

The initial embedded product retained its own branded sidebar and topbar inside
the Admin shell. That repeated application framing and made the actual subscriber
experience feel like a second dashboard. Local CSS also assigned different
font sizes and weights to equivalent navigation and AXENT controls.

## Implementation

The product owns one canonical menu, toolbar, focus controller, reader and AXENT
conversation. Standalone subscribers render them in the product shell. Admin
provides placement slots via React portals: the same menu goes into its sidebar
and the same toolbar goes into its single header. Admin operations remain in a
separate collapsible group. Switching operational domains keeps the product
mounted and retains its focus/conversation; mobile navigation closes after a
selection. No Admin data enters the economic renderer or explanation request.

`typography.css` defines shared semantic roles and is imported after public and
product styles. Controls are Manrope 13px/500, reading 14px/400, secondary metadata
11px/400, labels IBM Plex Mono 10px/400, panel titles Fraunces 24px/400. Active
navigation uses 600. Browser computed styles confirm matching left/right roles.
See `docs/design/TYPOGRAPHY_ROLES.md` for persistent implementation guidance.

No backend, datastore, acquisition contract or economic writer was added.
The frontend does not author Xignals, dates, currentness or EvidenceNarrative.

## Recovery-page audit

The existing 404 was textual. It now has AXIGNAL branding, a unique full-body
Observer reading a route map, and working home/Knowledge exits. Its generated
asset has provenance and remains pending human visual acceptance.

Missing route-error and root-error boundaries were added. The route boundary
has translated recovery and retry actions; it never displays exception contents
or repeats an economic operation. Root recovery is independent of locale and
runtime providers. An isolated `/design/recovery` harness exercises the actual
route boundary and successful retry without touching product data.

The route inventory found no missing literal internal destinations. HTTP checks
covered 28 routes, with no 5xx; unknown top-level, Knowledge and source routes
returned 404. Existing public, login/signup, policies/GDPR, subscriber and Admin
routes remain present. Missing service capabilities are not solved by inventing
checkout, password-reset or billing-success pages that would claim unsupported
operations. The inventory does not prove every possible dynamic URL or API.

## Validation actually executed

- `uv sync --frozen`: PASS.
- Ruff format/check: PASS; mypy: PASS (258 files).
- Final complete pytest: **1035 passed**, 128.96s, isolated basetemp.
  The first full run had one staff-authority test failure. Without changing its
  code or test, a focal rerun passed and the final full suite passed. Its initial
  cause was not established; this report does not conceal or reinterpret it.
- Architecture Guard and governance: PASS.
- Frontend typecheck: PASS; tests: **31 passed**; i18n: **981 entries**, no missing
  translations; production build: PASS, 35 pages generated.
- No frontend lint script exists; no frontend lint result is claimed.
- Graphify AST update and diff whitespace check: PASS.

## Browser QA

Actual compiled UI, not screenshots alone: single logo/sidebar/header; Today to
signal to EvidenceNarrative/source dialog; actual official source link and
uncertainty; backward/forward product navigation; Admin operations and return
without losing product context; AXENT authorized explanation; mobile drawer,
selection and dialog dismissal; standalone `/panorama/live` regression.

Computed final typography is saved in `qa/037-customer-zero/unified-admin-chrome/`.
Final 768/390/320px checks show no document overflow and one sidebar/header.
Desktop and mobile screenshots accompany the measurements. Branded 404 verified
at desktop and 390px, including its Knowledge exit. Route error was triggered
through the isolated harness and retry recovered the page. Root-layout failure
was **not forced in the browser**; the independent global boundary is build and
typecheck verified only.

## Real observation and persistence

The existing governed acquisition of `https://axignal.com/` produced the real
public-homepage observation. Current projection:
`xignal:737c35e849d6393e23cf067ce1141940`, observed
`2026-10-04T10:49:17.137943+00:00`. Reload fetched the same persisted projection.
EvidenceNarrative, official sourceRefs, CURRENT and explicit UNKNOWN limits were
inspected again after framing/typography changes. This establishes only public
homepage observability; no opportunity, reputation or other surface is inferred.
No additional planting was needed for this presentation correction and no prior
observation was edited. Original acquisition/reobservation and process-restart
evidence remains in the earlier unification reports.

## State

Implemented and locally validated. AO-24A remains IN_PROGRESS pending explicit
human visual acceptance. No production deployment or push.
