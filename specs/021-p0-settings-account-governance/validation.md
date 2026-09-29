# Validation: P0 Settings / Account Governance Authority

## Scope

This is a documentation-only authority audit. No runtime behavior, schema,
provider or UI was added, so frontend typecheck/build, contract tests for
Settings writes and browser E2E are not applicable. They remain required for a
later implemented surface.

## Evidence checks

- Original proposal base: `26f298425d88c67551cd432ab35da99d975c6a7a`.
- Reconciled against `origin/main` `08f113c18e3025960cf0733b0a51efb2be23f71d`, which includes merged P0 Identity PR #36.
- PR #36 Identity authority was treated as the controlling lower-level feature authority for Settings identity dependencies.
- The Settings authority matrix is cross-linked from `spec.md` and covers the
  requested fields/scopes and unresolved lifecycle behavior.
- The code/spec audit finds Principal/Tenant/membership/Xeed/Organization contracts and P0 Identity authority for authentication methods, identity mapping boundaries, Principal-owned durable locale preference, and entitlements; it still finds no selected auth provider/runtime, billing provider, production preference persistence, Settings mutation service, avatar store or product Settings UI.
- Graphify code index was rebuilt offline; no directed edge path was found from
  `PrincipalTenantMembership` to `AuthorizedXeedReader`. Direct source remains
  the implementation authority.
- Golden Master, manifest and HFX/PR working trees were read-only in this task;
  no source was modified.

## Automated gates

| Gate | Result |
|---|---|
| `uv sync --frozen` | PASS — 14 locked packages checked |
| `uv run ruff format --check .` | PASS — 356 files |
| `uv run ruff check .` | PASS |
| `uv run mypy` | PASS — 63 source files |
| `uv run pytest -q -p no:cacheprovider --basetemp <dedicated temp>` | PASS — 293 tests |
| `uv run architecture-guard --root .` | PASS |
| `uv run axignal-governance` | PASS — architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology |
| Local changed-doc secret-pattern scan | PASS — 0 matches; Gitleaks CLI unavailable locally |
| Graphify offline update | PASS — AST index rebuilt without LLM |
| Graphify multigraph diagnostic | COMPLETED — 4,500 nodes, 7,262 raw edges, 6 dangling endpoints, 226 same-endpoint collapsed edges |
| Golden Master Manifest V1 | PASS — SHA-256 `1b4154dd152d9ecd20bfaeb7585daf78b4fbc79f182fce32a2f94ff017d6ad51` |
| Browser E2E | NOT APPLICABLE — no UI change |

The six dangling Graphify endpoints are repository-wide diagnostic output; no
code files changed in this slice. They are not presented as a clean structural
diagnostic. The structural GitHub workflow was not run because this branch was
not pushed and no PR was created.
