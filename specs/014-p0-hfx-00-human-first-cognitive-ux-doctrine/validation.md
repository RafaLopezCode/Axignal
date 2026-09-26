# Validation Record: P0-HFX-00

**Base:** `18ff1aabe573cb0eb3532a499a64075e9f19dcfa`  
**Branch:** `product/p0-hfx-00-human-first-cognitive-ux-doctrine`  
**Validation date:** 2026-09-26

## Local quality gates

| Gate | Result | Notes |
|---|---|---|
| `uv sync --frozen` | PASS | Used task-specific `%TEMP%` uv cache after the global cache path denied access. |
| `uv run ruff format --check .` | PASS | 266 files already formatted. |
| `uv run ruff check .` | PASS | All checks passed. |
| `uv run mypy` | PASS | 48 source files; no issues. |
| `uv run pytest` | PASS | 154 passed. Used an external permitted `--basetemp` and disabled pytest's optional cache provider to avoid denied global/repository cache paths. Full test collection ran. |
| `uv run architecture-guard --root .` | PASS | No violations. |
| `uv run axignal-governance` | FAIL — local environment exception | `hygiene` and `no-generated-data` report that a local `.env` path is present. Its contents were not opened/read, and the file was not modified, staged, moved or deleted. This local gate is not represented as passing. Remote CI in a clean checkout must establish the repository gate. |
| `git diff --check` | PASS | No whitespace errors. |
| MASTER SHA-256 | PASS | Recorded checksum matches the current MASTER bytes. |
| Local Markdown links | PASS | Checked changed and new canonical/spec documents; all relative targets resolve. |

## Graphify

- Pre-change architecture query covered MASTER, Subscriber Experience,
  Design Doctrine, AXENT, Xeed Germination, AXIGLAND and DRI-00.
- `graphify update . --no-cluster`: PASS; structural graph rebuilt with 3,958
  nodes and 5,970 raw edges.
- `graphify diagnose multigraph --json`: no missing endpoints, 6 dangling
  endpoints, 3 self-loops and no exact duplicate edges. The diagnostic also
  reports 134 relation-variant groups and 12 heuristic producer-suppression
  sites. The result is recorded as a whole-graph observation; no before/after
  attribution is claimed.
- `graphify check-update .`: PASS.
- Generated Graphify outputs remain untracked/ignored and are not part of the
  proposed change.

## Scope and remote state

- Source pack was reviewed as reference-only input; it was not copied into the
  repository.
- PR #18 was rechecked through the GitHub connector: `OPEN`, unmerged, head
  `e877547f27a17f945df40ae546533fa68cf3ee79`; it was not touched.
- No `.env` contents or TypeSafe API key were accessed. No AXIGNAL runtime,
  Jev, OpenAI or other provider call was made. P0-JEV-04, P0-HFX-01,
  P0-DRI-01 and P0-EOI-01 were not started.
- PR #21 is open and unmerged. Its exact final head, green remote CI run and
  review-thread state are verified at closure and reported in the CTO ledger;
  this record avoids duplicating mutable PR/check metadata.
