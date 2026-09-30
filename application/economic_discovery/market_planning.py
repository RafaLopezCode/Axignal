"""Translate Xeed market posture into governed observation strategy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery.market_entry import (
    MarketRelationship,
    ParticipationState,
    XeedMarketMap,
)


class ObservationObjectType(StrEnum):
    ORGANIZATION = "ORGANIZATION"
    DEMAND_ARCHETYPE = "DEMAND_ARCHETYPE"
    PUBLIC_BODY = "PUBLIC_BODY"
    PROCUREMENT_EVENT = "PROCUREMENT_EVENT"


class MarketResearchIntent(StrEnum):
    CONFIRM_CURRENT_PARTICIPATION = "CONFIRM_CURRENT_PARTICIPATION"
    TEST_POTENTIAL_PARTICIPATION = "TEST_POTENTIAL_PARTICIPATION"


@dataclass(frozen=True, slots=True)
class MarketObservationDirective:
    relationship: MarketRelationship
    participation_state: ParticipationState
    research_intent: MarketResearchIntent
    object_types: tuple[ObservationObjectType, ...]
    semantic_questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.participation_state not in {
            ParticipationState.OBSERVED,
            ParticipationState.POTENTIAL,
        }:
            raise ValueError("only observed/potential markets may produce observation directives")
        expected = (
            MarketResearchIntent.CONFIRM_CURRENT_PARTICIPATION
            if self.participation_state is ParticipationState.OBSERVED
            else MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
        )
        if self.research_intent is not expected:
            raise ValueError("research intent must preserve observed versus potential semantics")
        if not self.object_types or not self.semantic_questions:
            raise ValueError("market observation directive requires targets and questions")


def _objects_for(relationship: MarketRelationship) -> tuple[ObservationObjectType, ...]:
    if relationship is MarketRelationship.B2B:
        return (ObservationObjectType.ORGANIZATION, ObservationObjectType.DEMAND_ARCHETYPE)
    if relationship is MarketRelationship.B2C:
        return (ObservationObjectType.DEMAND_ARCHETYPE,)
    return (
        ObservationObjectType.PUBLIC_BODY,
        ObservationObjectType.PROCUREMENT_EVENT,
        ObservationObjectType.DEMAND_ARCHETYPE,
    )


def _questions_for(relationship: MarketRelationship) -> tuple[str, ...]:
    if relationship is MarketRelationship.B2B:
        return (
            "Which organizations exhibit needs addressable by Xeed capabilities?",
            "Which organization roles and demand archetypes deserve attention?",
        )
    if relationship is MarketRelationship.B2C:
        return (
            "Which aggregate needs, intents, contexts, geographies and channels are observable?",
            "Which demand archetypes warrant campaign attention without identifying individuals?",
        )
    return (
        "Which public bodies or procurement contexts exhibit addressable needs?",
        "Which governed procurement or public-demand archetypes deserve investigation?",
    )


def plan_market_observation(market_map: XeedMarketMap) -> tuple[MarketObservationDirective, ...]:
    directives: list[MarketObservationDirective] = []
    for participation in market_map.participations:
        if participation.state not in {
            ParticipationState.OBSERVED,
            ParticipationState.POTENTIAL,
        }:
            continue
        intent = (
            MarketResearchIntent.CONFIRM_CURRENT_PARTICIPATION
            if participation.state is ParticipationState.OBSERVED
            else MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
        )
        directives.append(
            MarketObservationDirective(
                relationship=participation.relationship,
                participation_state=participation.state,
                research_intent=intent,
                object_types=_objects_for(participation.relationship),
                semantic_questions=_questions_for(participation.relationship),
            )
        )
    return tuple(directives)
