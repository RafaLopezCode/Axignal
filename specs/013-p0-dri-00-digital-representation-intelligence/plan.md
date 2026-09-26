# Plan: P0-DRI-00 Digital Representation Intelligence

## Objective and boundaries

Converge the product semantics, epistemic boundaries, measurement principles,
privacy/access rules and communication for the four DRI families, including
Public Experience Intelligence. Documentation only. Preserve one MASTER and
one existing branch/PR path. Do not begin P0-DRI-01.

## Workstreams

1. Update MASTER §54 in place, fold public experience into the four-family DRI
   model and refresh the pinned SHA-256.
2. Record observation and measurement decisions in ADR-0014/0015 and index.
3. Add compact Constitution and AGENTS invariants.
4. Align architecture overview, terminology, subscriber experience, Ask AXENT,
   communication, product index and graph-design guardrails.
5. Create the product specification, product-slice README and Spec Kit with
   frozen clarifications, architecture review, tasks, checklist and prior art.
6. Audit semantic convergence, score/epistemic boundaries, access/privacy,
   rights, duplication, temporality and EOI interaction.
7. Run deterministic gates and Graphify checks; verify documentation-only
   scope, zero external calls, and PR #18 remains untouched.
8. Commit/push the authorized branch, open one PR against updated `main`, wait
   for CI, and stop before merge.

## Affected surfaces

MASTER/hash pin, product specification/index, product-slice README, Constitution,
AGENTS, ADR index and ADR-0014/0015, architecture overview/terminology,
subscriber experience, communication strategy, graph-design skill/reference,
`specs/013-p0-dri-00-digital-representation-intelligence/**` and
`docs/README.md`.

## Risks and controls

- **Opinion becomes fact:** keep review claims, platform state, evaluator
  classification and FAXT separate.
- **Metric hides incompatibility:** preserve method/source/sample/coverage and
  withhold when incomparable or insufficient.
- **Privacy or rights drift:** classify by data and acquisition channel; public
  visibility is not automated-collection authority.
- **Double-counted experience:** reuse one authorized observation across
  projections but do not multiply evidence.
- **Documentation mistaken for implementation:** label every product/contract
  concept pre-implementation and prohibit runtime/provider changes.

## Rollback

Revert only this documentation slice and the corresponding MASTER checksum as a
reviewed change. Preserve unrelated local/ignored artifacts, PR #18, branches
and historical evidence. Never use reset/clean or inspect `.env`.

## Verification

Run the repository's frozen dependency sync, Ruff format/lint, mypy, full
pytest, Architecture Guard, governance, diff check, Graphify update with
`--no-cluster`, and multigraph diagnostics. Report the known local `.env`
hygiene exception without reading or touching `.env`. No runtime, provider,
platform account, live measurement or model call is permitted.

## Next slice boundary (not started)

P0-DRI-01 — Digital Observation Contracts & Sensor Economics — must precede
provider implementation. Its future scope includes DigitalObservation,
ReviewObservation, MeasurementInstrument and MeasurementRun contracts; search,
generative, social and public-experience semantics; ExperienceSignal and
classification contracts; deterministic metric composition; fingerprint and
deduplication; instrument comparability and uncertainty; public/private
authority; shared-observation reuse; deletion/currentness; UGC rights/retention;
sensor routing and cost economics; and candidate provider evaluation.
