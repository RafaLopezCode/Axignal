# Local review
From apps/web/experience:
```powershell
npm ci
npm run dev
```
Open http://127.0.0.1:3810 . Production: npm run build; npm run start.
Routes /, /panorama, /admin, /design; state samples available in /design.
Validate: npm run typecheck; npm test; npm run build. Repository: uv sync --frozen; uv run ruff format --check .; uv run ruff check .; uv run mypy; uv run pytest; uv run architecture-guard --root .; uv run axignal-governance.
Browser journey: landing lens; interactive demonstration; Panorama family; signal reasoning; evidence source; past snapshot; back; organization switch; AXENT question/component; mobile sheet; Admin domain/details/action boundary; state gallery/retry; reduced motion/keyboard.
All economic and operational examples are illustrative. AXENT demonstration is deterministic. No production auth, model provider or financial operation is claimed. Human visual acceptance pending.
