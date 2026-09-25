# P0-JEV-01 Feature Research

This Spec Kit research companion summarizes the evidence relevant to feature
planning. The complete primary-source review is in:

- [Official TypeSafe / Jev research](../../docs/research/AXIGNAL_P0_JEV_01_TYPESAFE_RESEARCH.md)
- [AXIGNAL opportunity map and authority reconciliation](../../docs/research/AXIGNAL_P0_JEV_01_OPPORTUNITY_MAP.md)
- [Non-authoritative community patterns](../../docs/research/AXIGNAL_P0_JEV_01_COMMUNITY_PATTERNS.md)
- [Proposed architecture](../../docs/architecture/AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md)

## Decisions supported by evidence

1. Jev/System One is suitable as a proposed typed semantic evaluator for
   bounded judgments, but its output is not truth and requires domain testing.
2. Choice, Score and Noul have different typed meanings; AXIGNAL preserves
   response distributions and confidence only where the provider defines it.
3. Independent questions over the same state may be batched; no answer sees
   another answer. State minimization and explicitly independent premises are
   part of question design.
4. Python remains the proposed future adapter language because the current
   AXIGNAL domain/pipeline/cognition are Python. SDK is not added in this
   documentation slice.
5. A model alias can move. Record request alias and resolved returned model ID;
   no alias silently becomes calibrated production policy.
6. The official compatibility adapter can support later comparison with
   generative models but does not emulate/prove real Jev behavior.
7. Current AXIGNAL owners already exist for canonical admission, epistemic
   enums, Knowledge Frontier, Research Planner policy and provider abstraction.
   This feature composes with them rather than replacing them.

## Known unknowns

No AXIGNAL-labeled test corpus, target-domain calibration, validated threshold,
provider/data-retention approval, production version pin, real cost/latency
profile, durable ledger design, or private-analysis security review exists.
No official migration-to-v1 page was available from the current docs index and
direct reader access failed. These remain evidence tasks for an implementation
or evaluator-upgrade review, not invented contracts for this spec.
