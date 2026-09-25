# Implementation Plan: Source Acquisition Bakeoff

## Constitution check

The work is research-only and introduces no product semantics or canonical
write path. It preserves epistemic neutrality, source/evidence authority
boundaries, provider independence, and deterministic merge gates. Experiment
code is under `experiments/`; test coverage only checks that isolated artifact.

## Affected systems

- `docs/research/`: documentary bakeoff and limits.
- `experiments/source-acquisition-bakeoff/`: standard-library offline harness,
  synthetic corpus, persisted results and fixture bytes.
- `tests/experiments/`: deterministic experimental contract tests.
- `specs/002-source-acquisition-bakeoff/`: lifecycle record.

No runtime package, `pyproject.toml`, `uv.lock`, domain model, evidence
admission, source router, graph runtime or application surface changes.

## Architecture

Use an explicitly named experimental request/observation pair and a loopback-
only HTTP fixture adapter. Keep browser, candidate and policy behavior
unimplemented; label those as gaps. Persist raw synthetic fixture bytes and
JSON observations containing their hashes and request lineage. Decision stays
deferred because candidate engines were not independently executed.

## Failure/rollback

The experiment is additive and removable by reverting its docs/spec/test/
experiment files. It has no external service or production data side effect.
The local test runner may write its fixture output under the experiment result
directory only.

## Validation

- Experiment tests and three-iteration raw fixture run.
- Ruff format/check, mypy, full pytest, architecture guard, governance,
  Graphify refresh, build and secret scan.
- Candidate runtime benchmark remains explicitly unvalidated and blocks an
  engine decision, not the correctness of this documentation-only evidence
  boundary experiment.
