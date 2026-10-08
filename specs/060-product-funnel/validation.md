# 060 — Validation

Verified on 2026-10-08 against `origin/main` `1775382` plus this branch.

## Deterministic gates

| Gate | Result |
| --- | --- |
| `uv sync --frozen` | ok |
| `uv run ruff format --check .` / `ruff check .` | ok / ok |
| `uv run mypy` | Success, 432 source files |
| `uv run architecture-guard --root .` | OK |
| `uv run axignal-governance` | 8/8 PASS (after `graphify update .`) |
| `uv run pytest` (full suite) | 1881 passed, 5 skipped (POSIX-only, already on `main`) |
| `npm test` | 133/133 (adds `tests/funnel.test.ts`, 9 tests) |
| `npm run typecheck` | ok |
| `npm run check:i18n` | 1,365 entries, 0 missing (es, en, de, pt, fr, it) |
| `npm run build` | ok (528 knowledge pages localized) |
| `npm audit` | 0 vulnerabilities |
| `tools/route-audit.mjs` | 24 routes, 17 literal internal links, 0 missing |

## Browser QA (local `next dev`, headless Chrome over CDP)

- `capture.mjs`: 28 full-page captures (7 pages × 1440/1024/768/390). No horizontal
  overflow, exactly one `h1` per page, no unnamed controls. Header links raised to 44px
  targets; remaining sub-24px links are inline links inside sentences (WCAG 2.5.8
  exception).
- `funnel_e2e.mjs`, 11/11 steps at 1440, 1024, 768 and 390: promise (5 s) → three steps
  (30 s) → open the one example → it says it is an example and what the organization
  does → its economic world first → a change → why it matters → its evidence (source,
  date) → back to AXIGNAL → pricing (what I pay, what one organization is) → sign-up
  says the next steps → no prototype language on the way.
- Mobile first visit (390): promise and both CTAs above the privacy notice.

## Edge 404 (isolated container on the server, `--network none`, `--rm`)

Both nginx configs pass `nginx -t`. Serving the real static files: `/pricing`, `/demo`,
`/admin`, `/es`, `/design` → 404 (branded `404.html`, noindex); `/legal/`,
`/legal/aviso-legal/`, `/robots.txt`, `/404.html` → 200. Temporary files removed.

## Production

Read-only throughout. `current` and `DEPLOYED_SHA` = `1775382`, unchanged.
Acquisition events and the weekly brief report `enabled:false`; Google sign-in
`AVAILABLE`; nothing was activated.
