"""The First Observation value policy (versioned, deterministic, operational).

Each optional step must reduce an open unknown (identity, activity, location, demand)
at a bounded marginal cost, preferring world-level reusable work. This orders and
bounds spending; it is not a relevance score and never a truth (MASTER §53).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from application.first_observation.contracts import POLICY_VERSION
from application.observation_intelligence.contracts import ObservationBudget
from application.observation_intelligence.strategy import StopPolicy

__all__ = ["POLICY_VERSION", "FirstObservationPolicy", "next_due"]


_RESEARCH_BUDGET = ObservationBudget(
    max_requests=4, max_amount_microunits=0, max_depth=1, max_actions=4
)
_RESEARCH_STOP = StopPolicy(sufficient_candidates=3, max_no_gain_streak=2)


@dataclass(frozen=True, slots=True)
class FirstObservationPolicy:
    #: A site reading younger than this is reused instead of fetched (world level).
    site_reuse_for: timedelta = timedelta(days=7)
    #: robots.txt decisions are reused this long per origin.
    robots_reuse_for: timedelta = timedelta(days=7)
    #: Extra pages read after the homepage, only while activity or location is UNKNOWN.
    max_extra_pages: int = 2
    #: Hard ceiling of HTTP requests for the whole site stage (redirects included);
    #: every optional fetch reserves its worst case (1 + max redirects) before running.
    max_site_requests: int = 16
    requests_per_fetch: int = 4
    #: Demand research at first observation: small; T12 continues if it is justified.
    research_budget: ObservationBudget = _RESEARCH_BUDGET
    research_stop: StopPolicy = _RESEARCH_STOP
    #: Semantic tokens one First Observation may spend (System One input, estimated).
    semantic_tokens: int = 12_000
    max_attempts: int = 3
    lease_seconds: int = 300

    def needs(self, *, activity_known: bool, location_known: bool) -> tuple[str, ...]:
        """Which kinds of extra page could reduce an open unknown, most valuable first."""
        needs: list[str] = []
        if not activity_known:
            needs += ["ACTIVITY", "ABOUT"]
        if not location_known:
            needs.append("LOCATION")
        return tuple(needs)


def next_due(
    now: datetime,
    *,
    unchanged_streak: int,
    activity_known: bool,
    source_unavailable: bool,
) -> datetime:
    """Re-check uncertainty sooner, back off on a stable site, never daily by default."""

    if source_unavailable:
        return now + timedelta(days=2)
    if not activity_known:
        return now + timedelta(days=7)
    return now + timedelta(days=min(30, 7 * 2 ** max(0, unchanged_streak)))
