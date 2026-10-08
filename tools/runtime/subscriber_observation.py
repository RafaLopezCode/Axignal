"""Server-owned Opportunity Intelligence plan construction for subscriber reobservation.

The configuration directs attention only. Capabilities are derived from reusable
public Observation Memory and remain POTENTIAL. Missing configuration, evidence,
or routable sources yields no plan rather than fabricated context.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from application.economic_reach.derive import derive_operating_model
from application.economic_reach.research import prune_research
from application.economic_reach.summary import GARDEN_TEMPORAL_POLICY, LEXICON_TERMS
from application.observation_intelligence import (
    EvidenceCoverageMap,
    MarketRole,
    MarketScope,
    ObservationBudget,
    ObservationStrategy,
    OperationalLearning,
    SourceObservationPort,
    SourceRegistry,
    StopPolicy,
    XeedObservationContext,
    build_strategy,
    derive_families,
    detect_capabilities,
    geo,
)
from application.subscriber_identity.runtime import Clock, TrustedSubscriberContext
from application.subscriber_projection.subscriber_runtime import (
    SubscriberEconomicRuntime,
    SubscriberObservationLoopExecutionPlan,
)
from domain.identity import XeedId
from domain.xignal import XignalEpistemicState
from pipeline.observation_intelligence import (
    TedSearchAdapter,
    UrllibTedTransport,
)


class SubscriberObservationPlanConfigurationError(ValueError):
    """Fail-closed configuration error without leaking file contents."""


@dataclass(frozen=True, slots=True)
class ObservationMarketAttention:
    jurisdiction: str
    roles: frozenset[MarketRole]


@dataclass(frozen=True, slots=True)
class OrganizationObservationAttention:
    organization_id: str
    markets: tuple[ObservationMarketAttention, ...]


def load_observation_attention(path: Path) -> tuple[OrganizationObservationAttention, ...]:
    """Load exact server-owned attention scopes from bounded JSON."""

    if not path.is_file() or path.stat().st_size > 65536:
        raise SubscriberObservationPlanConfigurationError(
            "observation plan file unavailable or too large"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SubscriberObservationPlanConfigurationError(
            "invalid observation plan file"
        ) from error
    if not isinstance(raw, list):
        raise SubscriberObservationPlanConfigurationError("observation plan must be a list")

    entries: list[OrganizationObservationAttention] = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"organizationId", "markets"}:
            raise SubscriberObservationPlanConfigurationError("invalid observation plan entry")
        organization_id = item["organizationId"]
        markets_raw = item["markets"]
        if not isinstance(organization_id, str) or not organization_id.strip():
            raise SubscriberObservationPlanConfigurationError("organization id is required")
        if not isinstance(markets_raw, list) or not markets_raw:
            raise SubscriberObservationPlanConfigurationError(
                "at least one market attention is required"
            )
        markets: list[ObservationMarketAttention] = []
        for market in markets_raw:
            if not isinstance(market, dict) or set(market) != {"jurisdiction", "roles"}:
                raise SubscriberObservationPlanConfigurationError("invalid market attention")
            jurisdiction = market["jurisdiction"]
            roles_raw = market["roles"]
            if not isinstance(jurisdiction, str) or not jurisdiction.strip():
                raise SubscriberObservationPlanConfigurationError("market jurisdiction is required")
            if not isinstance(roles_raw, list) or not roles_raw:
                raise SubscriberObservationPlanConfigurationError("market roles are required")
            try:
                roles = frozenset(MarketRole(str(role)) for role in roles_raw)
                geo(jurisdiction)
            except (TypeError, ValueError) as error:
                raise SubscriberObservationPlanConfigurationError(
                    "invalid market jurisdiction or role"
                ) from error
            markets.append(ObservationMarketAttention(jurisdiction, roles))
        entries.append(OrganizationObservationAttention(organization_id, tuple(markets)))

    identifiers = [item.organization_id for item in entries]
    if len(set(identifiers)) != len(identifiers):
        raise SubscriberObservationPlanConfigurationError("duplicate organization observation plan")
    return tuple(entries)


@dataclass(slots=True)
class ConfiguredSubscriberObservationPlanReader:
    """Build one bounded runtime plan from authorized evidence plus configured attention."""

    economic: SubscriberEconomicRuntime
    clock: Clock
    attention: tuple[OrganizationObservationAttention, ...]
    #: Source adapters for the strategy; None keeps the live adopted adapters. The
    #: autonomous runtime passes a replay of its own real retrievals instead.
    adapters_for: Callable[[ObservationStrategy], Mapping[str, SourceObservationPort]] | None = None
    #: None keeps the acquisition stop policy (it saves requests). A replay costs no
    #: request, so stopping early would only truncate the projection.
    stop_policy: StopPolicy | None = None

    def observation_plan_for(
        self, context: TrustedSubscriberContext, focus_id: XeedId
    ) -> SubscriberObservationLoopExecutionPlan | None:
        as_of = self.clock.now()
        authorized, history = self.economic.observation_seed(context, focus_id, as_of=as_of)
        organization_id = str(authorized.organization.id)
        configured = next(
            (item for item in self.attention if item.organization_id == organization_id), None
        )
        if configured is None:
            return None

        usable = tuple(
            observation
            for observation, currentness in history
            if currentness.value == "CURRENT" and observation.raw_content
        )
        if not usable:
            return None
        source = max(
            usable,
            key=lambda item: (item.record.observed_at, item.record.observation_id),
        )
        assert source.raw_content is not None
        capabilities = detect_capabilities(
            text=source.raw_content,
            observation_id=source.record.observation_id,
            source_ref=source.record.source_ref,
            observed_at=source.record.observed_at,
        )
        if not capabilities:
            return None

        markets = tuple(
            MarketScope(
                geo(item.jurisdiction),
                item.roles,
                XignalEpistemicState.POTENTIAL,
            )
            for item in configured.markets
        )
        observation_context = XeedObservationContext(
            xeed_id=str(focus_id),
            as_of=as_of,
            capabilities=capabilities,
            families=derive_families(capabilities),
            markets=markets,
        )
        coverage = EvidenceCoverageMap(max_age=timedelta(days=30))
        for market in markets:
            coverage.record(
                question_id="what-does-it-offer",
                market=market.geography,
                source_id="official-public-website",
                evidence_ids=(source.record.observation_id,),
                observed_at=source.record.observed_at,
            )

        registry = SourceRegistry()
        learning = OperationalLearning()
        strategy = build_strategy(
            observation_context,
            coverage=coverage,
            budget=ObservationBudget(
                max_requests=8,
                max_amount_microunits=0,
                max_depth=2,
                max_actions=8,
            ),
            registry=registry,
            learning=learning,
            stop_policy=self.stop_policy
            or StopPolicy(sufficient_candidates=3, max_no_gain_streak=2),
        )
        # Spec 058: no research spend outside the garden of location-bound channels.
        garden = derive_operating_model(
            organization_id=organization_id,
            capabilities=capabilities,
            capability_terms=LEXICON_TERMS,
            observations=tuple(observation for observation, _currentness in history),
            as_of=as_of,
            policy=GARDEN_TEMPORAL_POLICY,
        )
        strategy, _pruned = prune_research(strategy, garden)
        if not strategy.actions:
            return None
        adapters: dict[str, SourceObservationPort] = {}
        if self.adapters_for is not None:
            adapters = dict(self.adapters_for(strategy))
        elif any(action.source_id == "ted-search-v3" for action in strategy.actions):
            adapters["ted-search-v3"] = TedSearchAdapter(
                UrllibTedTransport(),
                clock=self.clock.now,
            )
        if any(action.source_id not in adapters for action in strategy.actions):
            return None
        return SubscriberObservationLoopExecutionPlan(
            observation_context=observation_context,
            strategy=strategy,
            adapters=adapters,
            coverage=coverage,
            learning=learning,
            registry=registry,
        )
