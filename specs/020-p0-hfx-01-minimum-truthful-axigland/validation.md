# P0-HFX-01 Validation Record

**Status:** Implementation and local proof complete; exact-head remote proof
pending. Human visual acceptance is still required before merge.

**CTO repair supersession:** Human Visual QA subsequently failed the previous
presentation and rejected the earlier `UNAUTHORIZED_VISUAL_DELTAS=0` assertion.
The pre-repair visual statements below are historical evidence only; they are
not accepted as fidelity closure. The repair record at the end of this file and
the paired screenshot evidence supersede them. Human acceptance remains
pending.

## Reentry and authority

- Repository: `RafaLopezCode/Axignal`; origin refresh succeeded.
- `main`, `origin/main`, and the feature branch base were all
  `26f298425d88c67551cd432ab35da99d975c6a7a` at reentry.
- The worktree was clean before the authorized feature branch changes.
- Work branch: `feature/p0-hfx-01-minimum-truthful-axigland`.
- Manifest V1 precheck and postcheck: PASS; 27 inputs;
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- GO: YES. The existing `AuthorizedXeed`, authorized Organization reader,
  and authorized FAXT collection reader support the minimum slice. Subject
  kind/resolution, object reference semantics, semantic relationships,
  cardinal assignment, epistemic strata, provenance, and historical graph
  remain `UNKNOWN_UNSUPPORTED` or unavailable.

## Implementation and browser evidence

- Subscriber Projection is in `application/subscriber_projection/axigland.py`.
  It requires one `AuthorizedXeedOrganization` and an immutable tuple of
  `AuthorizedXeedFaxt` from that exact authorized context. Canonical IDs are
  retained; UI keys include the identity kind so equal raw IDs cannot collide.
- The demo authority and loopback server are test/dev-only under
  `tests/support/`; the server binds only `127.0.0.1`, accepts no caller-chosen
  Xeed/Tenant IDs, and labels all returned content as synthetic in-memory data.
- The browser surface is `apps/web/subscriber/`. It renders only the returned
  projection. The context boundary is presentation containment; the browser
  draws no semantic Organization–FAXT edges. Serialized memberships retain
  the canonical `XeedId → FaxtId` pair.
- Browser E2E used the already-installed Playwright and Chrome, with outbound
  non-localhost requests blocked. No project dependency was added. Script:
  `C:\Users\usuario\.codex\visualizations\2026\09\26\01a0dc72-5baf-7563-a5ca-d4f57d9f6243\hfx01-e2e.mjs`.
- Results: authorized context, only referenced FAXTs, cross-Xeed isolation,
  selected identity / Bottom Context / AXENT synchronization, Back/Forward/
  Home/branching, no semantic edges, UNKNOWN-neutral state styling, unassigned
  epistemic axis, sidebar collapse/expand, camera, pan/zoom, minimap,
  empty/unavailable states, keyboard selection, reduced motion, narrow viewport
  without horizontal overflow, and zero console errors: PASS.
- Captures are outside the repository in the same evidence directory:
  `hfx01-golden-master-1280x720.png`, `hfx01-root-1280x720.png`,
  `hfx01-faxt-selected-1280x720.png`, `hfx01-back-restored-1280x720.png`,
  and `hfx01-narrow-640x900.png`.
- Visual deltas classified: `REQUIRED_BY_CANON`—no semantic edges, no
  unsupported Xeed-switch/write affordances, explicit unknown/unavailable
  states, and disabled historical view; `REAL_DATA`—synthetic direct-field
  content with permanent test/dev disclosure; `ACCESSIBILITY`—keyboard focus,
  reduced motion, narrow-layout root-label omission to prevent overlap, and
  sidebar collapse; `CTO_AUTHORIZED`—Golden Master LogoMark adapted inline.
  Desktop root/selected/back and narrow states were visually inspected; no
  unauthorized delta was identified in those captures. Human visual acceptance
  remains pending.

## Local gates

Final local results on the implementation worktree; pytest temporary files
and package build outputs are outside the repository.

- `uv sync --frozen`: PASS.
- `uv run --offline ruff format --check .`: PASS; 329 files already formatted.
- `uv run --offline ruff check .`: PASS; all checks passed.
- `uv run --offline mypy`: PASS.
- `uv run --offline pytest`: PASS; 266 passed.
- `uv run --offline architecture-guard --root .`: PASS.
- `uv run --offline axignal-governance`: PASS.
- `node --check apps/web/subscriber/app.js`: PASS.
- `git diff --check`: PASS.
- `uv build --offline --out-dir <external evidence directory>`: PASS; source
  distribution and wheel built successfully under `build-hfx01-final2`.
- Graphify update/check: PASS; 4,579 nodes and 7,537 edges. Diagnostics report
  zero unverified nodes, zero missing-endpoint edges, and no post-build error;
  six dangling-endpoint edges and three self-loops remain visible in the
  diagnostic output.
- Golden Master Manifest V1 verification: PASS before and after; exact digest
  above.
- Local changed-path credential-pattern scan: PASS. Gitleaks CLI is not
  installed locally; remote CI Gitleaks remains required. `.env`, environment
  values, keychain contents, and credentials were not read.
- Frontend typecheck/build/test scripts: not applicable; no canonical frontend
  package manifest, TypeScript config, or frontend test/build convention exists
  in this repository. JavaScript syntax and real-browser E2E were executed.
- Dependencies added: none.

The canonical Python gates were rerun after the final implementation changes.
The governance gate was rerun after this validation record was written.

## Scope and safety

Only the HFX-01 projection, browser demo, deterministic support/tests, feature
spec artifacts, and evidence-backed HFX integration-matrix rows are in scope.
No Golden Master input, manifest, package/dependency file, runtime provider,
production store/writer, other slice, or deployment target was modified.

`A01–A35=NO`: Golden Master unchanged; no redesign or fixture fallback; no
authorization bypass, raw-Xeed authority, cross-tenant/global FAXT leakage, ID
conflation, subject/object resolution, fake semantic edges/cardinal categories/
strata/provenance/history, UNKNOWN promotion, React domain interpretation,
AXENT transcript, label identity, dependency, production persistence/writer,
model call, secret access, deployment, unrelated VPS access, weakened gate,
skipped browser interaction, unsupported visual/production claim, or future
slice start.

## Lossless Golden Master fidelity repair

- Reentry resumed on the existing branch at `8d5c740db580e55b2566673a76525c8baa44fe0b`;
  the three in-progress browser files and the pre-change delta register were
  preserved and inspected before continuation.
- Canonical authorization, readers, Subscriber Projection, and domain contracts
  remain unchanged. The visual repair changed the browser surface and its
  evidence/tests; the later brand-source follow-up adds only allowlisted local
  asset serving, deterministic build-time generation, and asset provenance.
- The adapted stylesheet begins with the complete Golden Master `v2.css`
  source byte content after normalizing its CRLF/LF line-ending difference;
  presentation overrides follow it. The Golden Master itself remains
  read-only.
- CSP evidence: the browser served the subscriber app with `style-src 'self'`.
  Static inline style attributes were removed; the depth stops now render at
  their Golden Master positions. Browser console errors for the HFX runtime:
  zero.
- Real-browser E2E in Chrome used 1280×720 and 640×900, reduced motion, and a
  route that aborted all non-localhost requests. V01–V18 passed. AXENT
  structure, disabled capabilities, active canonical identity, empty
  transcript, unavailable composer/moves, history/camera behavior, unknown
  preservation, no semantic edges and empty/unavailable responses passed.
- At 640×900, document scroll width was 640 px; the composer remained inside
  the viewport. Reduced-motion focus caused zero `requestAnimationFrame`
  calls.
- Paired screenshots are stored outside the repository in the existing task
  evidence directory. They include Golden Master and HFX default, AXENT,
  selected-node and Bottom Context at 1280×720, plus HFX narrow at 640×900.
- Golden Master Manifest V1 postcheck: 27 files, digest
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`, PASS.
- Full local suite after the presentation test was added: 268 passed. Pytest
  temporary files were directed to the task evidence directory because the
  default Windows temp/cache locations are not writable in this sandbox.
- Ruff format, Ruff check, mypy, Architecture Guard and AXIGNAL governance:
  PASS. `uv sync --frozen`: PASS. `uv build --offline` built the sdist and
  wheel outside the repository. Graphify structural update/check passed;
  diagnostics report six dangling-endpoint edges and four self-loops, with no
  missing endpoints or post-build errors.
- Changed-path credential-pattern scan: no hits. Local Gitleaks executable is
  unavailable; exact-head remote Secret scanning remains required.
- Browser screenshots, scripts and build outputs remain outside the Git
  worktree. Human Visual QA is still `PENDING`; automated browser evidence does
  not close human acceptance.

## Authoritative brand assets

- Read-only source inventory: five SVGs in `D:\AXIGNAL\LOGOS`. SHA-256 values
  and visual classification are recorded in
  `docs/design/BRAND_ASSET_AUTHORITY_V1.md`; source files were re-hashed after
  generation and remain unchanged.
- The former inline approximation is replaced in the same Golden Master logo
  slots by the official horizontal light logo and official isotope. The
  official horizontal dark logo is included for dark-background readiness;
  no dark theme was introduced. Header/sidebar geometry is unchanged.
- Seven assets are copied/generated in `apps/web/subscriber/assets/brand/`.
  `brand-assets.v1.json` records source/output SHA-256, output dimensions and
  format and transformation. SVG derivatives normalize line endings and
  trailing horizontal whitespace only; vector paths, colors, viewBox, and
  artwork remain unchanged. The two PNGs were rasterized directly from the
  authoritative SVG by Chrome Canvas; ICO embeds the 32×32 PNG. No
  raster-to-raster resizing or image dependency was added.
- Browser favicon and all seven allowlisted asset URLs returned HTTP 200 with
  the expected media types. Chrome rendered the light and dark wordmarks,
  shared gold isotope, and 16×16/32×32 favicons without clipping or distortion;
  the subscriber header uses the light logo at the Golden Master slot ratio.
  Runtime console errors: zero; browser requests stayed on loopback.
- Final full validation after this update: `uv sync --frozen`, Ruff format,
  Ruff check, mypy, Architecture Guard, AXIGNAL governance, deterministic
  build, and Manifest V1 all PASS; pytest: 270 passed. Graphify: 4,634 nodes,
  7,613 raw edges, zero missing endpoints, six dangling endpoints, five
  self-loops, no post-build error. `git diff --check` PASS.
- No manifest/PWA, Apple touch icon, Open Graph image, public URL, social
  profile, SEO metadata, or structured data was added: the repository has no
  such consumer or canonical public routing to support those claims.

## Human-First presentation semantics repair

This section supersedes earlier copy-state descriptions and test counts above
for the final precommit worktree. It does not supersede the canonical authority
or Golden Master evidence.

- `apps/web/subscriber/presentation.js` is the single subscriber-copy
  authority. Canonical predicate/state identifiers map to semantic keys, then
  to localized messages. Static labels, accessible names, titles, placeholders,
  metadata and dynamic copy are bound to catalog keys; the UI does not derive
  labels by editing machine tokens.
- English is the only populated locale. Locale selection canonicalizes BCP-47
  tags and falls back to English without changing any canonical field. No i18n
  dependency was added.
- `MAINTAINS_STANDARD` remains unchanged in the projection and maps to
  `predicate.maintainsStandard` / “Maintains a standard”. Unrecognized
  predicates use a neutral “Information” label. Presentation labels do not
  determine identity.
- Currentness `UNKNOWN` is rendered as “How current this information hasn't
  been verified.” `subjectKind` and `subjectResolution` remain
  `UNKNOWN_UNSUPPORTED` in the serialized projection and are omitted from the
  primary UI because they are not actionable there. Neither state is collapsed
  into the other or into false/absence.
- Non-actionable empty Connections and missing fields are quiet. A load failure
  has plain user-facing copy. The demo indicator says “DEMO · EXAMPLE DATA”;
  test/dev and authorization-contract wording is not emitted to subscribers.
- `presentation-copy-leakage-register.v1.md` records the source value,
  previous render, surface, meaning, desired user copy, localization need and
  repair. The visual-delta register records this as a copy-only supersession.
- Dedicated Chrome regression: raw `UNKNOWN_UNSUPPORTED` visible NO; raw
  `UNKNOWN` enum visible NO; canonical `UNKNOWN` preserved YES;
  canonical `UNKNOWN_UNSUPPORTED` preserved YES; the raw
  `MAINTAINS_STANDARD` token remains internal. Currentness, empty and load
  failure copy pass. Browser errors: zero; requested hosts: loopback only.
- Chrome V01–V18 pass at 1280×720 and 640×900, with reduced motion and
  non-localhost requests blocked. The presentation-copy audit and paired
  screenshots remain external evidence. Human Visual QA remains PENDING.
- Final Python validation: `uv sync --frozen`, Ruff format check, Ruff check,
  mypy, 273 pytest tests, Architecture Guard, AXIGNAL governance, and
  deterministic source/wheel build all PASS. Build outputs are outside the
  worktree.
- Graphify update/check PASS: 4,650 nodes, 7,382 edges; zero unverified nodes,
  missing endpoints, dangling endpoints, or post-build errors; five self-loops.
  Semantic community labels were not refreshed because that step invokes an
  LLM and is not required for structural checks.
- Golden Master Manifest V1 PASS: 27 inputs; digest remains
  `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51`.
- Changed-path credential-pattern screen PASS with zero matches across 21
  intended paths; `.env` and credentials were not read. Gitleaks is not
  installed locally; exact-head remote Gitleaks remains a required gate.
- Brand generator was rerun against the authoritative local source with output
  directed outside the worktree; SHA-256 matched all seven assets and the
  derivative manifest exactly.

## Remote proof

This is the precommit validation record. It intentionally does not embed the
final commit SHA or its exact-head CI result: changing this file after remote
validation would create a new, unvalidated HEAD. Record commit/branch SHA, PR
identity/state, exact-head CI, deterministic validation, Graphify CI checks,
and Gitleaks in the PR and final delivery ledger. The PR must remain open and
unmerged. Human visual acceptance is still required; HFX-02 is not authorized.
