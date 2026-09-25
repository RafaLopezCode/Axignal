# Implementation Plan: P0-JEV-01 Structured Decision Intelligence

**Branch**: `architecture/p0-jev-01-v3` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

## Summary

Complete a documentation/specification slice: reconcile AXIGNAL authority,
document current TypeSafe facts and limitations, define structured decision
architecture/grammar/state/composition, specify an offline Decision Laboratory
and its adversarial corpus, and establish governance for future grammar
evolution. No runtime, data store, SDK, API call or schema migration is needed
to make these boundaries concrete.

## Technical context

**Language/Version**: Markdown; synthetic contract examples only
**Runtime dependencies**: None added
**Storage**: Conceptual; no persistent schema selected
**Testing**: Repository deterministic documentation/architecture/governance gates
**Target**: AXIGNAL Python domain, pipeline and cognition boundaries, future lab
**Constraints**: MASTER, Constitution, ADR-0001 through ADR-0010, Atlas, Brain,
Knowledge Frontier/Research Planner, source, subscriber, V2/V3.1 and Admin authorities.

## Constitution check

- One AXIGLAND; model/provider judgment is not truth. **Pass.**
- Provider abstraction is preserved; proposed future adapter is Python, but no
  provider SDK is added. **Pass.**
- Exact mechanics remain Python; typed judgment is bounded; open-ended work
  remains with the existing cognitive layer. **Pass.**
- Evidence admission remains the canonical firewall; `UNKNOWN` is never false.
  **Pass.**
- Knowledge Frontier and Research Planner are reused, not duplicated. **Pass.**
- Private V3.1 remains tenant-scoped; no OAuth/private access or public write
  is enabled. **Pass.**
- No thresholds, migrations, external service, production deployment, CRM or
  workflow capability is introduced. **Pass.**
- Required CI remains deterministic/offline; mock output is not a quality
  claim. **Pass.**

## Deliverable structure

```text
docs/architecture/AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md
docs/research/AXIGNAL_P0_JEV_01_TYPESAFE_RESEARCH.md
docs/research/AXIGNAL_P0_JEV_01_COMMUNITY_PATTERNS.md
docs/research/AXIGNAL_P0_JEV_01_OPPORTUNITY_MAP.md
specs/005-p0-jev-01-structured-decision-intelligence/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  tasks.md
  contracts/decision-contracts.md
```

The contract catalogue groups related concepts to avoid needless type/file
proliferation. No persistence or HTTP schema is frozen.

## Risks and rollback

- Readers mistake a proposed architecture or synthetic case for implemented
  behavior. Mitigation: repeat status labels and identify the absence of
  provider calls, observed output and production tests.
- Raw probabilities are mistaken for canonical confidence. Mitigation:
  preserve typed judgments internally, distinguish probability from confidence,
  and retain MASTER §19 product boundary.
- Private/customer content leaks to a provider or fixture. Mitigation: no
  runtime call and synthetic examples only; future processing needs review.
- A changed alias silently changes behavior. Mitigation: record resolved model
  and test version candidates before explicit promotion.
- Rollback is a documentation/tooling revert; no data/runtime migration is
  involved.

## Complexity tracking

No service, SDK/runtime dependency, queue, DB, schema, external deployment,
model training system or generic workflow engine is added. The Skill is
project-local agent tooling. This plan specifies conceptual contracts only.
