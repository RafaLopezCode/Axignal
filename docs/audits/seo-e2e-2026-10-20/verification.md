# Verification — favicon delivery repair

Base: `ed1e1250ee0ddade4fbe46c2ffda052cf989dc51` (main includes merged PR #350).
Candidate: `codex/seo-e2e-indexability-20261020`. No main or production changes.

## Deterministic checks

| Check | Result |
| --- | --- |
| `uv sync --frozen` | PASS |
| `uv run ruff format --check .` | PASS, 1724 files |
| `uv run ruff check .` | PASS |
| `uv run mypy` | PASS, 602 source files |
| `uv run pytest` | 2723 passed, 7 skipped, 360.90 seconds |
| `uv run architecture-guard --root .` | PASS, no suppressions |
| `uv run axignal-governance` | PASS, all 8 checks |
| `npm run test` | 422 passed, zero failures/skips |
| `npm run test:admin-http` | 28 passed |
| `npm run typecheck` | PASS |
| `npm run check:i18n` | PASS, 2786 entries, zero missing |
| `npm run build` | PASS, repertoire/styles/SEO checks and static localization included |
| `graphify update .` | AST only, 23897 nodes, 65831 edges; no paid model extraction |

Frontend commands use Node 22.23.3. The initial dependency installation emitted
an npm engine warning under system Node 24; all final validation/build commands
were run with explicit Node 22 and Node 22 first on PATH. No lockfile changes.

Seven unchanged Python skips: two POSIX permission/ownership checks, four POSIX
scheduler deployment checks and one optional `typesafe_sdk` compatibility test
when that SDK is absent. None verifies public HTML metadata, image delivery,
favicon derivation or search canonicalization. These skips are disclosed, not
new exemptions. The Linux/optional dependency checks retain their normal gates.

## HTTP and browser evidence

- `public-crawl.json`: all 596 current production sitemap URLs, checked via
  unauthenticated HTTPS GET. Self canonical, language, H1, metadata, inbound
  HTML links and reciprocal sitemap hreflang checks passed for all entries.
- `assets-and-legacy.json`: current MIME types and PNG dimensions for the
  approved icons; sampled retired pages and public navigation destinations.
- `local-delivery.json`: 10 routes compared against the accepted preview from
  runtime commit a31e80c3 (merged unchanged into main). Body elements, attributes
  and text are exactly equal after excluding scripts/style bodies; canonicals
  and languages are equal. All 10 SSR documents expose six approved icons.
- Native in-app Chromium browser at `http://127.0.0.1:3824/es`: real DOM declares
  the 96x96 PNG, multi-size ICO, unchanged SVG, 180x180 Apple, 192x192 and 512x512
  icons with MIME types and sizes. No console errors were recorded in that
  browser session. `preview-desktop.png` is an unedited native viewport capture.
- Unit regression checks read PNG signature/IHDR, exact official provenance
  hashes, actual root metadata and the existing robots/ingress configuration.

No JSX/CSS, responsive styles, motion, canonical, robots, sitemap, private
authorization or artwork bytes changed. A fresh Lighthouse performance claim
is deliberately not made by this metadata-only repair. Existing noindex/lab
isolation remains intact.

## What remains outside this PR

Search Console account data and personalized search screenshots stay local and
are not published in this public repository. No request-indexing, sitemap
submission, validation workflow, account setting, permission, merge or deploy
was performed. Recovery of retired search intents requires an editorially
equivalent destination, not blanket redirects. Indexing, canonical selection,
brand ranking and favicon appearance must be checked after an approved release
and Google's subsequent processing; this PR does not guarantee those outcomes.
