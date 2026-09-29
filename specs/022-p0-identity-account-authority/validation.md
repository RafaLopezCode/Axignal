# Validation — P0 Identity Authority Reconciliation

**Base:** `7d30966a68168a372ce25ab48d757c6887883adf` (`origin/main`)
**Scope:** Documentation-only authority proposal. Results below record commands run against the reconciled working-tree bytes before PR publication; remote CI must validate the exact published head.

## Reconciliation evidence

- Source branch: `codex/p0-identity-account-authority`, HEAD `f1d4d8776c012c0b72862aeff8576e3089fce74b`, one commit beyond historical base `26f298425d88c67551cd432ab35da99d975c6a7a` and five modified spec files.
- Source worktree is preserved: no reset, rebase, checkout, or file write was performed there.
- Settings PR #31 was inspected read-only; it remains open, draft, and unchanged at `d054879746a9056bf01a60084b83eb1d8f2be98f`.
- Current source contracts inspected: `domain/identity.py`, `domain/tenancy/model.py`, `domain/xeed/model.py`, `application/xeed_access/reader.py`, ADR-0017, ADR-0018, and ADR-0021.
- Q2 changes only this feature-spec directory. No code, database, provider, runtime, Golden Master, HFX, Settings PR, or Landing file is changed.

## Old proposal delta disposition

| Old delta | Classification | Reconciliation |
|---|---|---|
| Principal/Tenant/membership/AuthorizedXeed/Xeed/Organization inventory | ALREADY_CANONICAL | Re-state current main contracts and test/dev boundary; no new model. |
| One canonical Organization, private Xeed reference, no subscriber edit/claim | ALREADY_CANONICAL | Preserved under MASTER and ADR-0001/0004/0018/0021. |
| User account/subscription/preferences concept, without schema or cardinality | ALREADY_CANONICAL | Keep concept distinct; Principal owns a durable UI-locale preference if authorized. |
| Safe external identity mapping and verified linking | VALID_CARRY_FORWARD | Adapter maps issuer+subject to PrincipalId; email equality alone never links. |
| Google primary, email/password secondary, verified email, provider-owned TOTP/recovery | VALID_CARRY_FORWARD | Preserve and apply current mandatory password-path TOTP policy. |
| Password TOTP left as `PRODUCT_DECISION_REQUIRED` and Google assurance `UNRESOLVED` | SUPERSEDED | Current Q2 instruction requires mandatory password-path TOTP and Google external assurance for P0, without AXIGNAL-managed TOTP. |
| Dated provider comparison and conditional Clerk candidate | VALID_CARRY_FORWARD | Retained as non-authoritative, dated research. No provider selected; recheck before procurement. |
| Payer, billing, Principal/Tenant/subscriber cardinalities, profile lifecycle, retention | DEFERRED | No current authority resolves them; no generic Account/Workspace is inferred. |
| Current source gate results and 2026-09-28 base metadata | SUPERSEDED | Historical evidence only; current gates are rerun on this branch before PR. |

## Required validation results

| Gate | Result |
|---|---|
| `uv sync --frozen` | PASS; 14 locked packages checked. Used a task-scoped temporary `UV_CACHE_DIR` after the default user cache returned Access Denied. |
| `uv run ruff format --check .` | PASS; 353 files already formatted. |
| `uv run ruff check .` | PASS. |
| `uv run mypy` | PASS; no issues in 63 source files. |
| `uv run pytest` | PASS; 293 passed. Pytest emitted one non-failing cache warning because the sandbox denied writes to `.pytest_cache`. |
| `uv run architecture-guard --root .` | PASS; no violations. |
| `uv run axignal-governance` | WORKSPACE EXCEPTION; all checks pass except hygiene reports the 15 pre-existing untracked Landing source PNGs over 2 MiB. No suppression or Landing change was made. |
| Graphify update/check | PASS; `graphify update .` rebuilt the graph and `graphify check-update .` exited successfully. |
| Golden Master manifest | PASS; included in the full pytest run (`tests/governance/test_golden_master_manifest.py`, 11 passed). |
| Secret scan | NOT RUN LOCALLY; neither `gitleaks` nor `trufflehog` is installed. Remote CI secret scanning remains required. |
| Remote CI | PENDING PR creation; must be checked against the exact published head. |

## Scope and preservation

The local Landing files are a known valid untracked work item. They must remain present and unchanged; the known governance exception is not caused by this Identity proposal. The Contextual Explanations worktree, Identity source worktree, Settings worktree, and stash remain outside this reconciliation branch.
