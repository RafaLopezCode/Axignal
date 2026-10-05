# Economic Brain first vertical — implementation result

Historical candidate report for `a1c3519` on the older base. Its validation
results are not current-main integration evidence. See `INTEGRATION_REVIEW.md`
for the reconciled implementation, new gate results and integration verdict.

Branch: `codex/economic-brain-e2e`, based on `main@441b4d0`.
Authority: MASTER §§15–21, 53, 55, 56; Constitution; applicable ADRs.
Spec Kit specification, clarification, plan, architecture review and tasks are
recorded in `specs/038-economic-brain-first-vertical/`.

## Implemented

A read-only vertical joins one organization's normalized, evidence-backed
capability state with another organization's project announcement. Neither
synthetic source mentions the other organization. Six independent axes cover
supplier role, customer role, functional alignment, capability-specific delivery
reach, timing and certification eligibility. Roles can coexist; they never
establish a relationship between these organizations.

Applicability, evidence completeness, currentness and material contradictions
are checked before judgment. The existing Choice evaluator port receives actual
semantic state, the question contract and option meanings through a compatible
request extension. Python handles exact reach, date and qualification checks;
the evaluator handles the three bounded semantic questions. Full available raw
distributions, provider-defined confidence, identity/version and replay refs are
retained without inventing unavailable probabilities or using a confidence
threshold. DimensionEvaluation now compatibly retains choice and replay refs.

Python composes the vector into POTENTIAL/WARRANTED_ATTENTION or UNKNOWN with
INVESTIGATE/RETAIN. Missing material context, stale/expired support, contradiction
and evaluator failure cannot become positive opportunity presentation. Unverified
reach is UNKNOWN, not a market exclusion. Price, capacity, incumbent and commercial
access remain unassessed even when functional relevance warrants attention.

Explainable Basis and the Human-First JSON read model retain exact source and
evidence refs, excerpts, observation times, validity, effective currentness,
epistemic state, rights references, per-axis explanations and contradictions.
Advancing the consumption clock requires reevaluation; original inputs remain
immutable. OBSERVED capability input requires a matching existing admitted FAXT.
Reasoning and output compilation never invoke admission or canonical writers.

## Deliberately not implemented / production blockers

No live or paid provider, Jev SDK integration, extraction, acquisition, discovery
search, scheduler, infrastructure, canonical writes, tenant truth graph, UI or
deployment. The fake is a deterministic fixture evaluator, not a quality
benchmark. The corpus is wholly authored synthetic data with reserved `.example`
references; no URLs are fetched.

Production requires an authorized adapter behind cognition ModelRouter /
CognitiveProvider, independently adjudicated economic evaluations, governed
normalization/identity and exact evidence-span resolution, public rights/reuse
authorization, provider budget/deadline/usage controls, durable result/raw replay
storage, dependency-selective reevaluation, multiple capability/project identity,
subscriber authorization before evidence access and Human-First comprehension
validation. Admission/budget hardening from the parallel workstream must be
reconciled before productive ingestion or writes. All five excluded files remain
unchanged.

## Validation

Commands executed from this worktree:

| Command | Result |
| --- | --- |
| `uv sync --frozen` | PASS; 17 pinned development packages installed |
| `uv run pytest tests/economic_discovery tests/contracts/test_fr21_structured_evaluator_contract.py tests/contracts/test_faxt_requires_admission.py tests/contracts/test_evidence_admission.py tests/contracts/test_observed_vs_potential.py -q` | PASS; 210 tests, including all 29 vertical cases |
| `uv run pytest tests/economic_discovery/test_first_vertical.py -k end_to_end -s -q` | PASS; 1 example, 28 deselected; Human Output printed |
| `uv run pytest --basetemp $taskTestTempPath -q` | PASS; 1,083 tests in 76.12 seconds |
| `uv run ruff format --check .` | PASS; 848 files |
| `uv run ruff check .` | PASS; includes all changed Python |
| `uv run mypy` | PASS; 263 source files |
| `uv run architecture-guard --root .` | PASS; no violations |
| `uv run axignal-governance` | PASS; all eight checks |
| `git diff --check` | PASS |

For the final full run, `$taskTestTempPath` was the absolute external temporary
directory `%TEMP%\axignal-economic-brain-441b4d0\pytest-final`. Task-specific uv
and mypy caches were placed outside the repository for repository hygiene.
Frozen dependency installation required network access; all reasoning/tests
were offline and no model provider was called.

The initial full-suite run was interrupted after its Architecture Guard test
found deliberately invalid test fixtures in an in-repository pytest temp folder.
Removing that generated folder and using an external temp directory resolved
the issue without changing code or gates. A subsequent full run passed 1,079
tests; the final 1,083-test run includes four additional vertical checks.

Graphify CLI and `graphify-out/graph.json` are absent in this worktree.
`graphify update .` was attempted but the command was unavailable; governance's
optional Graphify check skips in this environment. Architecture review and
blocking Architecture Guard remain independent. Three required audit/E2E design
documents absent at the base were read from `D:\AXIGNAL\Axignal` without modifying
that checkout.

To observe the economic example and its exact per-axis evidence refs:

```powershell
uv sync --frozen
uv run pytest tests/economic_discovery/test_first_vertical.py -k end_to_end -s -q
```

## Files changed

- `application/economic_discovery/brain_contracts.py`
- `application/economic_discovery/economic_state.py`
- `application/economic_discovery/first_vertical.py`
- `application/subscriber_projection/economic_output.py`
- `tests/economic_discovery/fixtures/refrigeration-v1.json`
- `tests/economic_discovery/test_first_vertical.py`
- `specs/038-economic-brain-first-vertical/spec.md`
- `specs/038-economic-brain-first-vertical/plan.md`
- `specs/038-economic-brain-first-vertical/tasks.md`
- `docs/research/economic-brain-first-vertical/IMPLEMENTATION_RESULT.md`

The supplied untracked `CODEX_TASK.md` is not part of this implementation.
