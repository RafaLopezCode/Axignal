"""Reach-aware research: spend observation only where the garden makes it useful.

An action looking for one capability in a market is dropped only when every delivery
channel of that capability is location-bound, its reach is evidenced, and the market
overlaps neither its operating reach nor its own expansion signals. Unknown reach,
remote/digital delivery and capability-agnostic questions are never pruned, so growth
stays discoverable; pruning is a cost decision, never a truth about the world.
"""

from __future__ import annotations

from dataclasses import replace

from application.economic_reach.model import (
    LOCATION_BOUND,
    EconomicOperatingModel,
    Polarity,
    ReachBasis,
)
from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.strategy import ObservationAction, ObservationStrategy


def _overlaps(a: TaxonomyCode, b: TaxonomyCode) -> bool:
    return a.within(b) or b.within(a)


def worth_observing(action: ObservationAction, model: EconomicOperatingModel) -> bool:
    if action.capability_id is None:
        return True
    reach = model.reach_for(action.capability_id)
    if reach is None or not reach.modes or not reach.mode_values() <= LOCATION_BOUND:
        return True
    garden = [
        claim
        for claim in reach.claims
        if claim.polarity is Polarity.INCLUDED
        and claim.basis
        in (ReachBasis.STATED_SERVICE_AREA, ReachBasis.PREMISES, ReachBasis.EXPANSION_SIGNAL)
    ]
    if not garden:
        return True
    return any(_overlaps(action.market, claim.geography) for claim in garden)


def prune_research(
    strategy: ObservationStrategy, model: EconomicOperatingModel
) -> tuple[ObservationStrategy, tuple[str, ...]]:
    """(strategy with only useful actions, ids of the actions not worth spending on)."""
    kept = tuple(action for action in strategy.actions if worth_observing(action, model))
    pruned = tuple(a.action_id for a in strategy.actions if a not in kept)
    return (replace(strategy, actions=kept) if pruned else strategy), pruned
