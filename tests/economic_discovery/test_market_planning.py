from datetime import UTC, datetime

from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.market_entry import (
    MarketParticipation,
    MarketRelationship,
    ParticipationState,
    XeedMarketMap,
)
from application.economic_discovery.market_planning import (
    MarketResearchIntent,
    ObservationObjectType,
    plan_market_observation,
)

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _basis(target: str) -> ExplainableBasis:
    return ExplainableBasis(
        f"basis:{target}",
        "xeed:a",
        "org:a",
        target,
        "state:1",
        f"contract:{target}",
        NOW,
        (
            BasisDatum(
                f"datum:{target}",
                "obs:1",
                "source:1",
                "PUBLIC_WEB",
                NOW,
                "Observed market data.",
                BasisContribution.SUPPORTS,
            ),
        ),
        "Market interpretation.",
        "Temporal and reevaluable.",
    )


def _map() -> XeedMarketMap:
    return XeedMarketMap(
        "xeed:a",
        "state:1",
        NOW,
        (
            MarketParticipation(
                MarketRelationship.B2B,
                ParticipationState.POTENTIAL,
                0.68,
                _basis("B2B"),
            ),
            MarketParticipation(
                MarketRelationship.B2C,
                ParticipationState.OBSERVED,
                0.93,
                _basis("B2C"),
            ),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.UNKNOWN, None, None),
        ),
    )


def test_market_posture_drives_different_observation_objects() -> None:
    directives = plan_market_observation(_map())
    assert len(directives) == 2

    b2b, b2c = directives
    assert b2b.object_types == (
        ObservationObjectType.ORGANIZATION,
        ObservationObjectType.DEMAND_ARCHETYPE,
    )
    assert b2c.object_types == (ObservationObjectType.DEMAND_ARCHETYPE,)


def test_potential_market_is_researched_not_misrepresented_as_current() -> None:
    b2b, b2c = plan_market_observation(_map())
    assert b2b.research_intent is MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
    assert b2c.research_intent is MarketResearchIntent.CONFIRM_CURRENT_PARTICIPATION


def test_unknown_market_does_not_silently_become_observation_target() -> None:
    directives = plan_market_observation(_map())
    assert all(item.relationship is not MarketRelationship.B2G for item in directives)


def test_b2c_observation_strategy_has_no_person_object_type() -> None:
    b2c = plan_market_observation(_map())[1]
    assert {item.value for item in b2c.object_types} == {"DEMAND_ARCHETYPE"}
    assert all("individual" not in item.value.lower() for item in b2c.object_types)
