# Convergence — 2026-10-15

Implemented in `codex/axent-evidence-sheet`, based on `b15a8a7` of main.
Scope: EXTEND the canonical Observatory layout; preserve AXIGNAL semantics,
incumbent typography, color, proof and source contracts. No backend changes,
dependencies, provider changes or new synthetic operational data.

## Shared implementation and continuity

Account, DemoObservatory and CustomerZeroObservatory use
SubscriberPortfolioExperience → Observatory. They inherit the same AXENT rail,
canvas-local sheet and handwritten action. There are no per-dashboard copies.
DepthAxent and InsightBody remain unchanged. RuntimeAxent, its composer,
transport and authorization contracts are untouched.

Browser testing exposed two existing continuity faults: automatic landing did
not record the selected organization in the URL, and same-organization history
reloaded the reading, unmounting AXENT. Automatic landing now replaces its URL
entry with the authorized focus; same-reading history updates presentation
without rereading the source. Back/forward preserves the AXENT draft. Explicit
family/channel deep links retain precedence over demo landing defaults.

## Verification

- Frontend: 332 tests pass, zero failures; TypeScript passes; i18n inventory has
  2,446 entries with no missing translations; production build passes.
- Repository: frozen uv sync, Ruff format/check and mypy pass. Full pytest:
  2,420 passed, 7 skipped, 2 existing SyntaxWarnings. The first run encountered
  Windows Temp ACL errors; the successful run used a new workspace basetemp.
- Architecture Guard and governance pass; no suppressions or gates weakened.
- AST-only Graphify update completed without an LLM or API dependency.
- Admin browser: existing authorized real organization reads through the local
  preview, with no replacement payload. Desktop 1440×900: sheet docks inside
  the canvas, never overlaps AXENT, composer stays visible, rail geometry stays
  stable and opening full evidence preserves a local unsent draft. Finding
  proof retains its public source, date, instrument and uncertainty wording.
- Mobile 390×844: sheet stays inside its canvas with no horizontal overflow;
  AXENT opens in its existing responsive focus-contained presentation. Escape
  closes it and returns focus to the handwritten action. Shift+Tab stays in
  AXENT. The annotation uses the existing local Bic Notes font and focuses the
  composer on desktop.
- Demo browser: the same sheet/rail, inert covered canvas and preserved
  Back/Forward draft verified. Its pre-existing fictional-data notice remains.
  No new demonstration data or live observation/AXENT command was submitted.
- Account browser: anonymous access remains gated, with no invented fallback.
  Shared component parity is verified in code/tests; an authenticated private
  subscriber account was not available for live E2E verification.
- No Admin application console errors were recorded in the final inspection.
  Tool-host Statsig networking errors are external to the application.

Local browser evidence: `D:/AXIGNAL/_tmp/axent-ui-evidence/` contains
`admin-note.jpg`, `admin-desktop.jpg`, `admin-mobile.jpg` and
`demo-desktop.jpg`. These are local QA captures, not production artifacts.

## Review state and limits

Implementation and measured checks are complete. Human visual acceptance is
pending, as required by the AXIGNAL Design Director. No merge or deployment is
claimed. The executable Golden Master was unavailable; incumbent tokens and
baseline browser evidence governed the extension. Reduced-motion behavior is
covered by the existing Observatory media rule; runtime OS emulation was not
available through the browser capability. Desktop and mobile QA do not prove
the absence of every possible regression.
