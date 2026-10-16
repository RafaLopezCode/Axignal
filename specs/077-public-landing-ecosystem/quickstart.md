# Local preview and validation

Use the isolated managed checkout on `codex/public-landing-ecosystem`; leave the dirty original checkout untouched. No production deployment is authorized for this feature.

Frontend: `apps/web/experience`, existing Node/npm dependencies. Start a task-owned Next preview on a free loopback port; preserve user-owned services. Inspect home, family hub, industry hub, every industry route, pricing, example and signup/contact exits. Use the host browser automation only, desktop and narrow mobile, keyboard and reduced motion; capture valid evidence to `.impeccable/review/`.

Required checks before merge proposal: `uv sync --frozen`; Ruff format/check; mypy; full pytest with a fresh task-owned Windows basetemp; architecture guard; governance; frontend tests/typecheck/i18n/build and relevant Admin HTTP boundary tests. Run Graphify AST update after source changes. Run Impeccable detector once on changed UI targets at finish, followed by the shipped independent finish review and documenter.

Current preview: http://127.0.0.1:3847/es (task-owned production build).

To reproduce from `apps/web/experience`:

```powershell
npm run build
npx next start --hostname 127.0.0.1 --port 3847
```

In a separate terminal, run the real public journey checks:

```powershell
$env:AXIGNAL_MARKETING_TEST_ORIGIN='http://127.0.0.1:3847'
node --test tools/check-marketing-http.mjs
```

Routes: `/es` (and en/fr/de/it/pt); `/<locale>/data`; `/<locale>/industries`; six allowlisted case slugs (`industry`, `construction`, `energy`, `logistics`, `professional-services`, `agencies`); `/<locale>/pricing`. Unprefixed catalog aliases redirect to English. Existing `/pricing`, `/demo`, signup, contact and Knowledge remain real destinations.

Implementation and deterministic gates are complete. The first independent finish review requested two bounded fixes; both were applied, recaptured and scored resolved by the same reviewer. The shipped documentation handoff records the actual public token scope. Human final visual acceptance remains pending. The user authorized direct Next.js review in place of the incompatible intermediate HTML-only checkpoint; `.impeccable/build/state.json` is deliberately not falsified.
