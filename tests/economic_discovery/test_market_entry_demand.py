from datetime import UTC, datetime

import pytest

from application.economic_discovery.demand import CampaignRelevanceProfile, DemandArchetype
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

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _basis(target: str) -> ExplainableBasis:
    return ExplainableBasis(
        basis_id=f"basis:{target}",
        subject_id="xeed:a",
        candidate_id="org:a",
        semantic_target=target,
        state_fingerprint="state:1",
        contract_fingerprint=f"contract:{target}",
        evaluated_at=NOW,
        data=(
            BasisDatum(
                datum_id=f"datum:{target}",
                observation_id="obs:1",
                source_ref="source:1",
                source_type="PUBLIC_WEB",
                observed_at=NOW,
                excerpt_or_summary="Observed data supporting this market interpretation.",
                contribution=BasisContribution.SUPPORTS,
            ),
        ),
        interpretation="Warrants considering this market.",
        uncertainty="Classification remains temporal and reevaluable.",
    )


def test_xeed_can_be_observed_b2c_and_potential_b2b_simultaneously() -> None:
    market_map = XeedMarketMap(
        xeed_id="xeed:a",
        state_fingerprint="state:1",
        classified_at=NOW,
        participations=(
            MarketParticipation(
                MarketRelationship.B2B, ParticipationState.POTENTIAL, 0.68, _basis("B2B")
            ),
            MarketParticipation(
                MarketRelationship.B2C, ParticipationState.OBSERVED, 0.93, _basis("B2C")
            ),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.UNKNOWN, None, None),
        ),
    )
    assert market_map.observation_targets == (MarketRelationship.B2B, MarketRelationship.B2C)


def test_potential_market_cannot_exist_without_explainable_basis() -> None:
    with pytest.raises(ValueError, match="explainable basis"):
        MarketParticipation(MarketRelationship.B2B, ParticipationState.POTENTIAL, 0.7, None)


def test_market_map_must_explicitly_preserve_unknown_channels() -> None:
    with pytest.raises(ValueError, match="B2B, B2C and B2G"):
        XeedMarketMap(
            "xeed:a",
            "state:1",
            NOW,
            (
                MarketParticipation(
                    MarketRelationship.B2C, ParticipationState.OBSERVED, 0.9, _basis("B2C")
                ),
            ),
        )


def test_b2c_demand_archetype_cannot_contain_person_identity() -> None:
    with pytest.raises(ValueError, match="never identify"):
        DemandArchetype(
            "demand:1",
            "xeed:a",
            "comfortable footwear",
            "commercial search",
            "long periods standing",
            "Madrid",
            "SEARCH",
            "state:1",
            NOW,
            _basis("DEMAND"),
            "Jose Luis",  # type: ignore[arg-type]
        )


def test_campaign_profile_is_relevance_not_purchase_probability() -> None:
    profile = CampaignRelevanceProfile(
        need_fit=0.9,
        intent_strength=0.8,
        demand_strength=0.7,
        growth=0.6,
        geographic_fit=0.9,
        channel_fit=0.8,
        message_fit=0.75,
        evidence_quality=0.85,
        currentness=0.9,
        uncertainty=0.2,
        policy_version="campaign-relevance.v1",
    )
    assert profile.need_fit == 0.9
    assert "purchase_probability" not in profile.__dataclass_fields__
