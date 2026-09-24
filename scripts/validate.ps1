# Run the full deterministic validation suite locally.
# Mirrors .github/workflows/ci.yml (minus secret scanning).

$ErrorActionPreference = "Stop"

Write-Output "== uv sync --frozen =="
uv sync --frozen

Write-Output "== governance =="
uv run axignal-governance hygiene terminology docs spec deps no-generated-data

Write-Output "== format =="
uv run ruff format --check .

Write-Output "== lint =="
uv run ruff check .

Write-Output "== typecheck =="
uv run mypy

Write-Output "== tests =="
uv run pytest

Write-Output "== architecture guard =="
uv run architecture-guard --root .

Write-Output "== build =="
uv build

Write-Output "All deterministic gates passed."
