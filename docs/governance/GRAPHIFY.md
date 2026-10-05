# Graphify in AXIGNAL

Graphify turns the repository into a queryable knowledge graph so agents can
inspect architecture before changing it. Scope is **this repository only**.
Graphify never touches other projects.

## What Graphify does here

- Indexes AXIGNAL code and docs into `graphify-out/graph.json`.
- Provides `query`, `path`, `explain`, `affected`, `god-nodes` for architecture
  questions.
- Installs git hooks (post-commit, post-checkout) and a `graph.json` merge
  driver so the graph follows the repository.

## Canonical vs generated

| Artifact | Status | Tracked? |
| --- | --- | --- |
| `graphify-out/graph.json` | Generated structural graph | **No** (gitignored) |
| `graphify-out/*.html`, reports, caches | Generated | **No** |
| `.graphifyignore` | Configuration | **Yes** |
| `.codex/skills/graphify/`, `.codex/hooks.json` | Codex project integration | **Yes** |
| Graphify git hooks | Local tooling | **No** (installed by script) |
| `docs/governance/GRAPHIFY.md` | Documentation | **Yes** |

The generated graph is not a source of truth and must not be committed. The
MASTER and code are the source of truth; the graph is a derived index. The
Logical Architecture Atlas records target architecture, while the P0-ARCH-01
gap ledger records evidence-backed current status. Graphify indexes these
documents but cannot promote target descriptions into implementation evidence.

## Install / verify

The official PyPI package is `graphifyy` (double-y); it installs the
`graphify` command. AXIGNAL uses an isolated `uv tool` installation so the
CLI is available to humans and coding agents without coupling it to the
application environment.

```powershell
uv tool install graphifyy
uv tool update-shell
graphify --version
graphify codex install --project
graphify hook install
graphify hook status
```

The project-scoped Codex install creates `.codex/skills/graphify/` and
`.codex/hooks.json`. These are tracked repository configuration; the generated
`graphify-out/` graph remains untracked.

Repository helper:

```powershell
pwsh -File scripts/install-graphify-hooks.ps1
```

## Initial and ongoing extraction

Run the initial structural extraction only after governance/docs exist (so it
indexes meaningful architecture):

```powershell
graphify update . --no-cluster
```

- **Structural (deterministic, no LLM):** `graphify update .`,
  `graphify diagnose multigraph`. Safe for required CI.
- **Semantic (LLM, external):** `graphify extract`, `graphify label`. Non-
  blocking; run explicitly. Never required for merge.

## Drift detection

- Blocking: `graphify check-update .`, `graphify update . --no-cluster`
  and `graphify diagnose multigraph --json` in CI.
- If these report problems, refresh locally with the commands above and
  investigate graph collapse risk.

## Agent usage

Before architectural changes an agent should:

1. `graphify query "<question>"` to locate the relevant nodes;
2. `graphify explain "<node>"` and `graphify affected "<node>"` to see impact;
3. `graphify path "A" "B"` to see dependency routes.

See `AGENTS.md`.
