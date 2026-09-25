# Implementation Plan: P0-JEV-03 First Live Jev Empirical Pilot

**Branch**: `experiment/p0-jev-03-first-live-pilot` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Add a lab-only, explicitly invoked pilot runner that performs a one-request smoke against existing synthetic assets, then permits exactly the existing `claim-wording-ab@0.1.0` run only when the smoke is reviewed as passing. Preserve safe provider Choice fields and metadata, create immutable results and a dated report, and verify offline replay. No production runtime, dependency, migration, canonical write, or CI provider access is introduced.

## Technical Context

**Language/Version**: Python 3.11+ (repository package)
**Primary Dependencies**: Existing core dependencies; pinned optional `decision-lab-live` group with `typesafe-sdk==0.7.1`
**Storage**: Create-only JSON research artifacts under `docs/research/p0-jev-03/`
**Testing**: Existing pytest suite plus offline Decision Laboratory checks; tests must not make provider calls
**Target Platform**: Local operator environment
**Project Type**: Python research tooling and documentation
**Performance Goals**: Sequential bounded requests; no performance claim
**Constraints**: One smoke request; only after pass, ten experiment requests; one question per experiment request; concurrency one; retries zero; no provider calls in CI
**Scale/Scope**: One synthetic case for smoke and the five already predeclared synthetic cases for the single controlled experiment

## Constitution Check

- **Authority boundary**: Pass. Jev produces a typed experimental judgment only; deterministic AXIGNAL code retains all composition and evaluation authority.
- **Canonical-write boundary**: Pass. Runner only writes create-only research artifacts; it has no AXIGLAND/domain write path.
- **Provider abstraction**: Pass. The optional SDK remains behind the experimental TypeSafe adapter; no provider becomes a production dependency.
- **Deterministic CI**: Pass. Offline tests use fakes/fixtures and never load `.env` or contact TypeSafe.
- **Secrets**: Pass by design. The optional runner reads only the expected credential entry into process memory, emits booleans/categories, and never serializes it.
- **Scope**: Pass. No production architecture, schema, policy, grammar, model, threshold, or product changes.

## Architecture and Execution

1. Retain the current immutable experiment definition, Golden labels, grammar locks, compiler, state variant registry, provider adapter, budget evaluator, pricing policy, artifact digest, and outcome evaluator.
2. Add a lab-only pilot entry point with explicit `smoke` and `experiment` phases. It validates exact source assets and budget before provider access. The smoke phase selects only `CES-01-clear-positive`, `CES.SUPPORT.v1`, `minimal@0.1.0`, and `jev-1.13.0`.
3. Resolve `TYPESAFE_API_KEY` from the process or ignored `.env` without a dotenv dependency. Reject ambiguity or absence before constructing the client. Never print values or exception text.
4. Extend the adapter's safe metadata with explicitly whitelisted typed Choice fields returned by the SDK so replay retains the source judgment alongside the normalized judgment. Do not persist the SDK response object, HTTP payload, request headers, or errors.
5. Record the smoke result with create-only artifact semantics. The operator inspects authentication, schema, normalization, metadata, replay safety, budget, and authority isolation before invoking phase `experiment`.
6. Phase `experiment` uses the unmodified existing CLI/evaluator for the full locked sample; it cannot select or remove cases, alter variants, repeat, change wording, or use a mutable model alias.
7. Improve offline result replay only as required to verify the recorded source experiment's composition, supported metrics, formal outcome, and digest. No live fixture regeneration.
8. Store only reviewed, non-secret synthetic observations and results in the new research path; write the report with observation/configuration/derivation/interpretation/unknown labels.

## Data Model

See [data-model.md](data-model.md). The smoke record holds case/question/state identity, requested and optional resolved model, primitive, safe raw Choice fields, normalized judgment, usage as reported (including unknown), local latency, retry count, adapter/SDK versions, timestamp, source SHA, safe failure category, and a content digest. Controlled-run records remain in the established Decision Laboratory result shape.

## Contracts

See [contracts/pilot-run.md](contracts/pilot-run.md) and the unchanged P0-JEV-02 `claim-wording-ab@0.1.0` definition. There is no production API or CLI registration.

## Validation Strategy

- Validate the smoke manifest selects exactly one approved case and one existing versioned Choice question and estimates one request/one question within byte limits.
- Verify `.env` ignore/tracking and credential-presence booleans without printing the value.
- Run offline unit/contract/replay and complete deterministic repository gates.
- After one live smoke only, record and inspect its immutable result. Continue only if every smoke gate passes.
- If eligible, run the complete ten-request experiment once, replay offline, calculate only supported metrics, and verify no credential/network dependency in replay or CI.
- Scan changed files and history for secret exposure, check working tree and exact PR head, and open a new PR without merging.

## Project Structure

```text
experiments/decision_lab/
├── pilot.py                         # Explicit, bounded P0-JEV-03 runner
├── providers/typesafe.py            # Safe whitelisted SDK answer fields
└── ...                              # Existing compiler, evaluator, artifacts, experiment
tests/decision_lab/
└── test_p0_jev_03_pilot.py           # Offline-only pilot contract and replay tests
docs/research/p0-jev-03/
├── empirical-report.md
├── smoke-result.json                # Created only after the single smoke request
├── claim-wording-ab-result.json     # Created only after smoke passes
└── replay-result.json               # Offline replay evidence
specs/007-p0-jev-03-first-live-pilot/
└── ...                              # Spec Kit governance artifacts
```

**Structure Decision**: Keep all provider-specific behavior under the existing experimental Decision Laboratory boundary; add only one unregistered, explicit pilot entry point and research evidence files.

## Risks and Rollback

- **Provider failure or mismatch**: Preserve its safe category and stop; no automatic retry. No contract mutation or retry is allowed.
- **Credential parsing ambiguity**: Fail before request; use no fallback or new credential source.
- **Unexpected SDK response**: Store no unsafe object; record a safe schema failure and stop.
- **Artifact collision or unsafe content**: Create-only write fails. Review the artifact and secret scan before commit.
- **Undo**: Revert the P0-JEV-03 branch/PR as a unit. The optional SDK group remains pinned and unchanged; no production state requires rollback.

## Complexity Tracking

No constitution violations.
