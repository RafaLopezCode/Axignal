# Implementation Plan: P0-JEV-02 Decision Laboratory

**Branch**: `experiment/p0-jev-02-decision-lab` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Implement a small, isolated, Python-based experimental laboratory under `experiments/decision_lab/`. It will validate synthetic cases and versioned questions; compile deterministic state; retain typed judgments; run controlled experiments through recorded or explicitly enabled live evaluators; calculate class-scoped metrics; create immutable results/reports; and prohibit production side effects. The optional official Python SDK is confined to one lab-only adapter and dependency group.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Standard library for offline lab; optional `typesafe-sdk==0.7.1` in dependency group `decision-lab-live`
**Storage**: Versioned JSON corpus, grammar and experiment definitions; immutable result JSON written to caller-selected external output directory
**Testing**: pytest; all tests offline, deterministic, synthetic
**Target Platform**: Developer workstation and GitHub Actions
**Project Type**: Research/developer tooling, excluded from product wheel
**Constraints**: No production runtime, customer/private data, network in default/CI mode, automatic retries, concurrent live calls, result overwrite, or policy promotion
**Scale/Scope**: V0.1, 42 synthetic cases (14 per initial family), 3 bounded live experiment definitions, no automatic sweep

## Constitution Check

- MASTER and Constitution remain unchanged; all evaluator outputs are experimental and noncanonical.
- SDK is excluded from `[project].dependencies` and default/dev dependency groups; only a separate optional lab group can install it.
- Lab code is outside `domain/`, `pipeline/`, `cognition/`, and wheel package list. It must not import production code, canonical writers, Knowledge Frontier, Research Planner, Source Router, or authorization.
- A narrow Architecture Guard exception may permit the exact TypeSafe SDK import only in `experiments.decision_lab.providers.typesafe`; all other provider imports outside `cognition/providers/` remain rejected. Production core imports of the lab are forbidden.
- CI remains offline; no credential is required or read by test fixtures.
- No migration, production configuration, UI, Luna, or source-acquisition work.

## Research Decisions

1. **SDK selection**: Python official TypeSafe SDK 0.7.1. AXIGNAL is Python-first; SDK provides typed Choice/Score/Noul response objects, usage/model metadata, and typed errors. JavaScript SDK 0.6.0 was reviewed but has no current AXIGNAL runtime target. The official SDK is not a production dependency.
2. **Retry/budget control**: Current Python SDK retries twice by default. Configure `RetryPolicy(max_retries=0)` and client timeout; the runner enforces request, question, state-byte, and encoded request-byte limits before each call. Bytes are not tokens, so preflight token count and monetary cost remain unknown. Concurrency is one. A failure is recorded by safe category only.
3. **Logging/privacy**: TypeSafe SDK docs/source state secret headers are redacted but bodies are not. The adapter suppresses verbose SDK logs, never prints exceptions/body, records only normalized judgments and safe metadata, and uses synthetic public-like fixture data.
4. **Cost**: The official model page reviewed on 2026-09-25 lists Jev 1.13 at USD 0.042 per million input tokens and zero output-token price. This is captured in a versioned pricing-policy record. It is applied only to provider-reported input-token usage after a response; invoice cost remains unknown. Preflight bytes never imply tokens or money.
5. **No calibration claim**: 42 synthetic cases and any small live sample support exploratory diagnostics only. No production threshold, calibration claim, model promotion, or active grammar results.
6. **Repository isolation**: Experiment package is under `experiments/decision_lab/`, not included in the hatch wheel. The live adapter is the only module allowed to import `typesafe_sdk`.

## Data and Experiment Design

- Corpus V0.1: 42 fully synthetic cases; 14 each for claim/evidence support, entity alignment, and economic relationship. Explicit label statuses and provenance distinguish known synthetic construction from designed ambiguity/contradiction/no-answer.
- Grammar V0.1: immutable question IDs/versions and family/primitive/state/exclusion metadata; includes claim wording variants, entity alignment Choice, relationship presence Noul, type Choice, time Choice, and contradiction Noul.
- State compiler V0.1: deterministic JSON-safe projection and SHA-256 fingerprint of semantic state only.
- Controlled definitions declare experiment type, one independent variable, controlled dimensions, policy version and predeclared evaluation criteria. Supported executable types are QUESTION_WORDING, STATE_ABLATION, ATOMIC_DECOMPOSITION, MODEL_COMPARISON, and REPEATABILITY. Other proposed types fail closed until implemented. Live budgets are predeclared; no calls occur unless invoked with `--live` and credentials are available.
- State variants use a versioned explicit registry. Unknown variants fail closed. Results preserve variant identity and fingerprint per evaluation. Outcome classification is deterministic and uses only predeclared criteria; the current small-sample criteria intentionally produce INCONCLUSIVE where they do not establish a justified effect threshold.
- Atomic relationship decomposition retains all four raw judgments and applies a versioned, experimental-only deterministic composer. Unresolved and contradictory signals remain explicit; the composer has no canonical admission path.
- Offline fixture replay validates ingestion/normalization/composition only; it never represents Jev quality or golden corpus correctness.

## Architecture

```text
synthetic Golden Corpus + immutable Grammar
                    ↓
            Lab State Compiler
                    ↓
recorded evaluator OR explicit live lab adapter
                    ↓
         normalized raw judgments
                    ↓
      experimental deterministic composer
                    ↓
 metrics, comparisons, immutable result/report
```

The package has no imports from production `domain`, `pipeline`, or `cognition` packages. It has no canonical, frontier, planner, source, authorization, or database handles. The TypeSafe SDK remains optional and lazily imported by the isolated lab adapter.

## Project Structure

```text
experiments/decision_lab/
├── __init__.py
├── __main__.py
├── cli.py
├── models.py
├── validation.py
├── corpus.py
├── grammar.py
├── state.py
├── judgments.py
├── evaluator.py
├── experiment.py
├── metrics.py
├── comparison.py
├── artifacts.py
├── report.py
├── providers/typesafe.py
├── corpus/v0.1/cases.json
├── grammar/v0.1/grammar.json
├── experiments/v0.1/*.json
└── fixtures/recorded/*.json

tests/experiments/test_decision_lab_*.py
docs/research/AXIGNAL_P0_JEV_02_TYPESAFE_REFRESH.md
docs/research/AXIGNAL_P0_JEV_02_SYNTHESIS.md
specs/006-p0-jev-02-decision-laboratory/
```

**Structure Decision**: Keep all lab code and datasets under the existing non-wheel `experiments/` area; only the isolated optional-provider import is admitted by a narrow architecture rule.

## Validation Strategy

1. Validate corpus/grammar/experiment schemas and label integrity.
2. Unit-test state serialization/fingerprints, question immutability, typed judgment normalization, errors, budget preflight, and experimental composition.
3. Replay normalized recorded fixtures offline; assert no network and no canonical/production imports.
4. Test metrics, confusion matrices, calibration infrastructure labels, critical regressions, immutable result writes, comparison and reports.
5. Run required repo gates, Graphify, build, secret scan, and explicit lab validations.
6. Live Jev is not attempted during implementation because `TYPESAFE_API_KEY` is absent; live mode remains opt-in and CI-independent.

## Risks and Rollback

- SDK transitive dependencies may be large or incompatible; keep them isolated in the optional group and remove that group/adapter if resolution or SDK isolation fails.
- Token counts and monetary costs are unknown before calls. UTF-8 request-byte budgets are a separate safety bound. Provider-reported input-token usage may be priced only through the dated, versioned policy record; invoice cost remains unknown.
- SDK/API shape may drift; typed normalization fails closed and records an operational/schema failure.
- Synthetic labels may be mistaken for empirical truth; reports must declare their authority and whether evaluator data are live, recorded, or fixture-only.
- Rollback is removal of this feature branch's lab files, optional dependency group/lock entries, guard exception/tests, and documentation links. No production data/schema needs rollback.

## Complexity Tracking

No Constitution violation. The isolated SDK exception and optional dependency group are limited to the CTO-authorized Decision Laboratory and are tested as boundaries.
