# TASK 4 — runtime subscriber UX unification: validation

CURRENT_TASK = AO-24A

## Problem and root cause

The previous AO-24A proved real FR-30 execution but its shared renderer was a
linear inspector. The incumbent Panorama shell and AXENT remained fixture-bound.
Customer Zero therefore shared truth without sharing the product experience.

## Implemented architecture

`/panorama` and compatibility `/panorama/live` render RuntimePanorama →
RuntimeExperience → RuntimeProductProjection. `/admin/customer-zero` renders
CustomerZero → RuntimeExperience with optional Staff controls → the **same**
RuntimeProductProjection. Customer Zero has no surrounding private Admin shell,
no second product reader and no subscriber-view hop. Legacy Admin hash entry
redirects to the canonical route.

Existing product shell/sidebar/topbar/timeline classes, design tokens, Brand,
Badge, LocaleToggle, Dialog, AXENT identity/composer and focus-navigation controls
are reused. The illustrative Panorama is isolated at `/design/panorama`.
Its fixtures are never imported by the real experience.

The canonical experience provides a spatial canvas of actual runtime signals,
Today, reversible focus/back/forward/home, evidence journey, observation dates,
dimension navigation and contextual AXENT. Mobile starts in Today. No economic
edges, dimension assignments or historical snapshots are fabricated. IDs and
technical runtime diagnostics are third-layer disclosures.

The existing `/api/axent` endpoint supports an authorized runtime reading mode.
It retrieves current subscriber-safe context server-side using AO-01 authority;
browser input supplies only a prompt and optional signal reference. Every
economic passage is selected from runtime-authored fields. Research tools are
explicitly unavailable. This is a bounded explanatory reader, not autonomous
research, model synthesis or another Brain.

## Real browser execution

Compiled `next start`, actual local FR-30 service, isolated persisted stores at
`D:/AXIGNAL/.ao24a-unified-proof`. Existing `.ao24a-real-proof` user history was
preserved. Credentials/private databases remain outside Git.

1. Missing/foreign session refused; existing QA session connected through AO-01.
2. Actual empty store produced NO_XEED. Observe AXIGNAL invoked canonical
   `POST /api/xeeds` attention target `https://axignal.com/`.
3. Acquisition was visible without a fake progress conclusion. Real public HTTP
   acquisition produced OBSERVED/CURRENT signal
   `xignal:d265352b44bec63c396a3be2350e2e05` at
   `2026-10-04T10:48:07.145891+00:00`.
4. Today → focus → EvidenceNarrative exposed actual signal/observation/source/
   uncertainty, verified artifact, public source and currentness. The supported
   claim is homepage observability only; commercial conclusions remain unknown.
5. Reobserve appended a second record, context `xeed:production-first-proof:2`,
   signal `xignal:737c35e849d6393e23cf067ce1141940` at
   `2026-10-04T10:49:17.137943+00:00`. The first record remains intact.
6. Browser reload and full FR-30 process restart returned exactly that second
   signal and timestamp. SQLite inspection confirmed two records with the
   canonical target; negative QA scenarios appended no successful record.
7. Subscriber `/panorama` displayed the same actual signal and canonical shell,
   with Staff utility absent. Customer Zero showed only optional Staff utility.
8. Back/forward/home, focus selection, single authorized organization dialog,
   reading/spatial mode, unknown dimensions, timeline limitations, evidence
   disclosure, mobile navigation and Escape were exercised.
9. AXENT answered from real authorized passages. Research request displayed the
   actual uncertainty and unavailable tools. Mobile Enter submitted a question;
   closing/reopening retained the contextual transcript. Shift+Tab originally
   escaped to browser chrome; explicit modal wrap repaired it. Final Tab and
   Shift+Tab stayed inside; Escape restored the opener.
10. Controlled QA acquisition outcomes exercised insufficient evidence (422),
    runtime failure (502) and governed rejection (400), with recovery by reading
    the persisted projection. These are negative scenarios, not evidence of a
    real public-source insufficiency. The successful observations were real.

All six requested widths were exercised: 1440×1000, 1280×720, 1024×900,
768×900, 390×844 and 320×900. Document width equalled viewport width; main scroll
width equalled its client width. No Norte/Atlas/demo/private operational text in
the real product main. This is targeted interaction/responsive QA, not a claim
of a comprehensive accessibility certification.

Machine-readable evidence:
`apps/web/experience/qa/037-customer-zero/unification-evidence.json`.
Screenshots: `apps/web/experience/qa/037-customer-zero/unification-screenshots/`.
Screenshots supplement interactions and persistence checks; they are not E2E alone.

## Validation actually executed

- `uv sync --frozen`: PASS (17 packages).
- `uv run ruff format --check .`: PASS (823 files).
- `uv run ruff check .`: PASS.
- `uv run mypy`: PASS (258 source files; cache outside repository).
- `uv run pytest`: **1,035 PASS**, 139.60 seconds; temporary directory outside Git.
- `uv run architecture-guard --root .`: PASS, no violations/suppressions.
- `uv run axignal-governance`: PASS all eight gates.
- `npm run test`: **29 PASS**, including real-shell SSR equivalence, reversible
  presentation navigation, read-only runtime explanations, forbidden economic
  input/foreign-origin rejection and retained AO-01/FR-30 guards.
- `npm run typecheck`: PASS.
- `npm run check:i18n`: PASS, 976 entries, no missing translations across six locales.
- `npm run build`: PASS, 34 routes. Initial sandbox EPERM cache failure resolved
  by running the identical command with permitted host cache access.
- Frontend lint: **NOT RUN**; this package has no lint script/configuration.
- Graphify query/affected/path inspection and AST-only `graphify update .`:
  executed successfully, no LLM labeling or gate weakening.

Implementation commit: `5ccd6a08080637a02e4b44179098bab536857ec3`.
Dialog repair: `3eec376` (compiled and interaction-verified afterward).
The persisted runtime SHA records the implementation used for acquisition;
reload does not rewrite historical SHA or timestamps.

## State and real remaining debt

IMPLEMENTED + PROVEN + BROWSER E2E PASS locally on main. Not pushed or deployed.
HUMAN_VISUAL_ACCEPTANCE_PENDING. AO-24A remains IN_PROGRESS for this visual gate.

FR-30 currently exposes one authorized focus, current observation signals and
Today. It does not expose economic dimension classifications, relationships,
historical snapshot browsing or autonomous AXENT research tools. The UI states
these boundaries truthfully. General external subscriber authentication is not
silently replaced by this operator-authorized Customer Zero harness. Production
composition/deployment and human visual acceptance remain separate work.
