# AXIGNAL Repository Hygiene Reconciliation — 2026-10-02

**Status:** DONE

## Purpose

Establish a clean, explicit repository baseline before AO-16. This reconciliation separates technical debt from deliberate blockers, historical evidence and planned product work. It does not weaken architecture, tests, governance or product doctrine.

## Canonical Git state

The authoritative local repository is `D:\AXIGNAL\Axignal` and the authoritative branch is `main`.

After repair:

- `main == origin/main` at `315d96a6f5a30e4989c89c938d8f3782e84acddd` before this hygiene slice;
- local divergent branches: none;
- local unmerged branches: none;
- only intentional non-main remote branch: `research/p0-jev-04a-golden-corpus-authority` for PR #18;
- fresh-clone and repaired-canonical `git fsck --full`: PASS.

PR #18 is not branch debt. Its research contract explicitly records `BLOCKED_NO_VALID_CORPUS` and requires the work to remain open/unmerged until rights, privacy, source-independence and corpus-feasibility gates are resolved. It must not be merged or closed merely to make the branch list visually empty.

## Git corruption incident and recovery

A full `git fsck --full` during this hygiene pass exposed severe corruption in the previous local object database: missing/corrupt loose objects, invalid Codex checkpoint refs and stale worktree metadata. GitHub `origin/main` remained healthy and the latest PR CI was green.

During an earlier attempt to clean Windows ACL-broken pytest temporaries, a malformed `cmd.exe` quoting boundary escaped the intended target. The command was terminated immediately. A later inventory showed that the canonical working tree had been partially removed while Git metadata was already unhealthy.

Recovery was fail-safe:

1. no production or GitHub state was changed;
2. a completely fresh clone was created from `https://github.com/RafaLopezCode/Axignal.git`;
3. the fresh clone matched `origin/main` exactly and passed `git fsck --full` with zero errors;
4. the canonical working tree and Git metadata were reconstructed from that verified clone;
5. `git reset --hard origin/main` restored tracked content;
6. the repaired canonical repository passed `git fsck --full` again.

No canonical code was lost because GitHub/main remained the source of truth throughout the repair.

## Executable-code debt scan

A scan over `application/`, `domain/`, `pipeline/`, `cognition/`, `tools/`, `apps/`, `tests/` and `.github/` found no executable-code `TODO`, `FIXME`, `HACK` or `XXX` markers.

Occurrences of `BLOCKED`, `UNKNOWN`, `TEMPORARY` and `NOT_STARTED` are not automatically debt: many are explicit product/runtime states or historical evidence.

## Workspace hygiene

Task-local artifacts had accumulated under names such as:

- `.codex-uv-cache-*`;
- `.pytest-*` basetemp directories.

The two AO-18 pytest directories have Windows ACL anomalies that prevent normal traversal/deletion and previously caused filesystem walkers to fail before reaching source code.

Permanent remediation:

- `.codex-uv-cache-*/` and `.pytest-*/` are explicitly ignored by Git;
- Ruff explicitly excludes the same patterns;
- no source/test/gate is weakened;
- physically inaccessible historical temporaries may remain until Windows releases or repairs their ACLs, but they are not repository inputs.

Standard `.venv` and `node_modules` directories remain local development dependencies and are not classified as debt. `graphify-out/` is generated/rebuildable and already ignored.

## Production alignment

The last directly verified production functional SHA before this reconciliation was `9822c4b0d4a352633b320a2d250d964a746efd39`.

A Git comparison from that SHA to `main` showed no changes under production-sensitive paths:

- `application/`;
- `domain/`;
- `pipeline/`;
- `cognition/`;
- `tools/`;
- `apps/`;
- `deploy/`;
- `pyproject.toml`;
- `uv.lock`.

Subsequent changes were governance, research, experiment and test evidence. Therefore repository reconciliation itself does not require a production deployment.

## Canonical status reconciliation

The Admin roadmap remains the live execution-status authority for AO work:

- AO-12: DONE;
- AO-15: DONE;
- AO-16: next execution task;
- AO-10: BLOCKED until remaining real billing/live evidence is completed;
- AO-11, AO-13, AO-14 and later unexecuted slices remain NOT_STARTED unless separately evidenced.

Older validation/spec documents containing `NOT_STARTED` or historical blockers are evidence snapshots. They are not rewritten to impersonate current status.

## Deliberate blockers / planned work, not cleanup debt

The following remain intentionally outside repository hygiene:

- PR #18 / P0-JEV-04A corpus-rights blocker;
- temporary Xeed bootstrap architecture governed by ADR until its replacement slice exists;
- future AO capabilities;
- Obscura v0.2.3 production rejection and future-release watch gate;
- Stripe AO-10 external/live completion gate.

## Final local validation evidence

On the repaired clean worktree:

- `git fsck --full`: PASS;
- `uv lock --check`: PASS;
- `uv sync --frozen`: PASS;
- `uv run ruff format --check .`: PASS, 709 files already formatted;
- `uv run ruff check .`: PASS;
- `uv run mypy`: PASS, 210 source files;
- `uv run architecture-guard --root .`: PASS;
- `uv run axignal-governance`: PASS for architecture, deps, docs, graphify, hygiene, no-generated-data, spec and terminology;
- `git diff --check`: PASS;
- full pytest: 883 PASS in 279.41 seconds.

GitHub CI #318 passed (Secret scanning, Graphify structural checks and Deterministic validation), and PR #134 merged successfully. Repository hygiene reconciliation is therefore CLOSED.

## Exit criteria

Repository hygiene is closed only when:

1. canonical `main` is clean and equals `origin/main` after merge;
2. only intentional remote research branches remain;
3. full Ruff traversal no longer fails on task-temp directories;
4. `uv lock --check` and `uv sync --frozen` pass;
5. Ruff format/check, mypy strict, Architecture Guard, governance and `git diff --check` pass;
6. full pytest passes;
7. GitHub CI is green on the hygiene PR;
8. no unrelated production deployment is performed.
