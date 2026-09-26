# ADR-0013: AXIGNAL Compounds Governed Economic Intelligence

**Status:** Accepted product doctrine; no implementation authorized by this ADR.\
**Date:** 2026-09-26\
**MASTER:** §14, §46, §53

## Context

Persistent observation creates value only if valid work remains useful over
time. AXIGNAL must not reconstruct the same economic context from zero for
every query, nor may reuse silently turn stale inference into truth. The moat
is durable governed knowledge and reusable reasoning infrastructure, not a
low token price or dependence on one model.

## Decision

1. Compounding Economic Intelligence is a core AXIGNAL pillar, inseparable
   from Economic Opportunity Intelligence. AXIGLAND is reusable governed
   economic memory; research should reuse valid knowledge rather than restart
   from zero.
2. Reuse preserves evidence/provenance, epistemic state, dependencies and
   currentness. Reuse is not trust forever. Verify, mark stale/unknown or
   reinvestigate when validity may have changed.
3. Temporal history is cumulative value. Upstream changes must support
   downstream reevaluation without erasing prior state or explanation.
4. Economic sensors and their coverage, entity resolution, decision
   contracts, reasoning and provenance are reusable cognitive
   infrastructure. Reusable outputs remain subordinate to evidence admission
   and deterministic AXIGNAL policy.
5. Compounding error is a systemic risk. Dependency and derivation history,
   evidence quality, staleness and uncertainty remain inspectable through
   reuse and reevaluation.
6. Cognitive amortization and replacement-cost asymmetry are product-value
   hypotheses. The defensible moat is persistent, governed, reusable and
   temporal economic understanding plus reusable reasoning infrastructure.
   Cheap tokens are not the moat.
7. Candidate measures are future measurement directions only; this decision
   sets no performance claim or target.
8. This ADR does not authorize runtime changes, schema, migration, provider
   use, or implementation.

## Required invariants

```text
COMPOUNDING_ECONOMIC_INTELLIGENCE=CORE
AXIGLAND_IS_REUSABLE_ECONOMIC_MEMORY
RESEARCH_SHOULD_NOT_RESTART_FROM_ZERO
VALID_KNOWLEDGE_IS_REUSABLE
REUSE_REQUIRES_CURRENTNESS
TEMPORAL_HISTORY_IS_ACCUMULATIVE_VALUE
ECONOMIC_SENSORS_ARE_REUSABLE_INFRASTRUCTURE
ENTITY_RESOLUTION_IS_REUSABLE
DECISION_CONTRACTS_ARE_REUSABLE
PROVENANCE_MUST_SURVIVE_REUSE
UPSTREAM_CHANGE_MUST_SUPPORT_DOWNSTREAM_REEVALUATION
COMPOUNDING_ERROR_IS_A_SYSTEMIC_RISK
CHEAP_TOKENS_ARE_NOT_THE_MOAT
PERSISTENT_GOVERNED_KNOWLEDGE_IS_THE_MOAT
```

## Alternatives considered

- Recompute all context for every query: rejected because it discards
  persistent observation and compounds marginal work.
- Reuse indefinitely without freshness checks: rejected because stale
  evidence and errors would accumulate invisibly.
- Define low inference cost as the moat: rejected because model prices and
  providers are replaceable and do not preserve independent economic
  understanding.
- Overwrite historical knowledge with refreshed state: rejected because it
  destroys temporal reconstruction and the explanation of prior decisions.

## Consequences and tradeoffs

Future product contracts must carry provenance and currentness through
reusable artifacts and support reevaluation when dependencies change. This
adds requirements to state and trace design, but avoids false certainty and
preserves accumulated value. Measurement remains future work and must not be
reported as existing capability until demonstrated.

## Risks and rollback

Reused incorrect knowledge can propagate across many downstream judgments.
Keep derivation and dependencies inspectable, distinguish epistemic state,
and permit invalidation/re-evaluation without history loss. A future doctrine
change must update the MASTER before amending this ADR.
