# FR-31 Audit-Base Validation Snapshot

**Audit base SHA:** `d78afb0f1acdfcb660fb1fb28d325b76ff65552d`
**Main CI:** `36872416171` — SUCCESS
**CI URL:** https://github.com/RafaLopezCode/Axignal/actions/runs/36872416171

## Clean detached-worktree validation

Executed against a detached worktree at the exact audit-base SHA, independent from local untracked Frontier Advisor documents.

```text
uv sync --frozen                         PASS
uv run ruff format --check .             PASS · 563 files
uv run ruff check .                      PASS
uv run mypy                              PASS · 139 source files
uv run pytest -q                         PASS · 689 tests
uv run architecture-guard --root .       PASS
uv run axignal-governance                PASS
```

The first governance invocation occurred after `mypy` had generated an untracked `.mypy_cache/3.11/cache.4.db` larger than the repository hygiene threshold. Governance correctly rejected that generated cache. The cache was removed and governance was immediately rerun against the same unchanged audit-base checkout; all governance gates passed. No repository file or gate was weakened to obtain green.

## Production snapshot

Direct VPS inspection at FR-31 preparation time:

```text
runtime_service        active
landing_service        active
runtime_code_sha       cb89cfe391a0ce6ba93bfc5e5b8a942795897769
landing_sha            d78afb0f1acdfcb660fb1fb28d325b76ff65552d
health                 ok
write_surface          closed
first_proof_sessions   1
observation_rows       1
learning_event_rows    6
```

`https://axignal.com/healthz` reported healthy Observation/Learning persistence and the exact runtime code SHA. The landing/runtime SHA split is intentional: the latest integrated change was landing-only directional pagination and did not change runtime code.

## Interpretation

This snapshot proves the repository/runtime state that the re-audit package points at. It does not prove FR-27 market validation, willingness to pay, or any capability not represented by the referenced evidence.
