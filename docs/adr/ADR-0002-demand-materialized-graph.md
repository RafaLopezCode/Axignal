# ADR-0002: Demand-Materialized Graph

- **Status:** Accepted
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §3.2, §3.3, §8, §29, §46.3, §46.18

## Context

AXIGLAND has a global ontology but must not precompute the entire economy.
Materializing everything before demand would be economically wasteful and
technically unbounded.

## Decision

AXIGLAND materializes incrementally, driven by demand (`XIGNAL`). Absence of a
materialized node means "not yet observed", not "does not exist". Compute is
allocated by expected information gain over cost, weighting reuse potential.
Depth precedes breadth.

## Consequences

- The graph grows through use; future investigations reuse prior knowledge.
- `KnowledgeFrontier` tracks what remains unknown or stale.
- No attempt to crawl the whole economy up front.

## Enforcement

- `domain/knowledge_frontier/model.py` models explicit frontier state.
- `cognition/batch/packager.py` bounds work into deterministic batches.
- Doctrine phrase "One world model. One canonical graph. Demand-driven
  materialization." is preserved in the constitution.
