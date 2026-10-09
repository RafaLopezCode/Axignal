"""Market-aware demand research planning for a First Observation (spec 063 §4 L4).

Reuses the existing routing (capability x market x question -> adopted sources, with
information gain, quality, learning and cost bands) and the spec 059 garden pruning.
It only plans; adapters execute elsewhere. No route is a grounded gap, not an answer.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from application.economic_discovery.observation_memory import GovernedObservation
from application.economic_reach.derive import derive_operating_model
from application.economic_reach.research import prune_research
from application.economic_reach.summary import GARDEN_TEMPORAL_POLICY, LEXICON_TERMS
from application.first_observation.policy import FirstObservationPolicy
from application.observation_intelligence import (
    EvidenceCoverageMap,
    ObservationStrategy,
    OperationalLearning,
    SourceRegistry,
    XeedObservationContext,
    build_strategy,
    derive_families,
)
from application.observation_intelligence.contracts import CapabilityHypothesis, MarketScope

WEBSITE_SOURCE = "official-public-website"


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    context: XeedObservationContext
    strategy: ObservationStrategy
    coverage: EvidenceCoverageMap
    gaps: tuple[tuple[str, str], ...]
    pruned: tuple[str, ...]


def plan_research(
    *,
    xeed_id: str,
    organization_id: str,
    capabilities: Sequence[CapabilityHypothesis],
    scopes: Sequence[MarketScope],
    observations: Sequence[GovernedObservation],
    as_of: datetime,
    policy: FirstObservationPolicy,
    registry: SourceRegistry | None = None,
    learning: OperationalLearning | None = None,
) -> ResearchPlan | None:
    """None when there is nothing to route (no coded capability or no scope)."""

    routable = tuple(c for c in capabilities if c.demand_codes)
    if not routable or not scopes:
        return None
    context = XeedObservationContext(
        xeed_id=xeed_id,
        as_of=as_of,
        capabilities=routable,
        families=derive_families(routable),
        markets=tuple(scopes),
    )
    coverage = EvidenceCoverageMap(max_age=timedelta(days=30))
    evidence = tuple(c.basis[0].observation_id for c in routable)
    for market in scopes:
        coverage.record(
            question_id="what-does-it-offer",
            market=market.geography,
            source_id=WEBSITE_SOURCE,
            evidence_ids=evidence,
            observed_at=max(c.basis[0].observed_at for c in routable),
        )
    registry = registry or SourceRegistry()
    strategy = build_strategy(
        context,
        coverage=coverage,
        budget=policy.research_budget,
        registry=registry,
        learning=learning or OperationalLearning(),
        stop_policy=policy.research_stop,
    )
    # The website was just read by the First Observation itself.
    strategy = replace(
        strategy, actions=tuple(a for a in strategy.actions if a.source_id != WEBSITE_SOURCE)
    )
    garden = derive_operating_model(
        organization_id=organization_id,
        capabilities=routable,
        capability_terms=LEXICON_TERMS,
        observations=tuple(observations),
        as_of=as_of,
        policy=GARDEN_TEMPORAL_POLICY,
    )
    strategy, pruned = prune_research(strategy, garden)
    gaps = tuple(sorted({(gap.market.code, gap.reason) for gap in strategy.gaps if gap.reason}))
    return ResearchPlan(context, strategy, coverage, gaps, pruned)
