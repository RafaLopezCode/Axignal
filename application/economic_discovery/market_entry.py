"""First Brain gate: classify how a Xeed participates in markets."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.explanation import ExplainableBasis


class MarketRelationship(StrEnum):
    B2B = "B2B"
    B2C = "B2C"
    B2G = "B2G"


class ParticipationState(StrEnum):
    OBSERVED = "OBSERVED"
    POTENTIAL = "POTENTIAL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class MarketParticipation:
    relationship: MarketRelationship
    state: ParticipationState
    relevance: float | None
    basis: ExplainableBasis | None

    def __post_init__(self) -> None:
        if self.relevance is not None and (
            not math.isfinite(self.relevance) or not 0.0 <= self.relevance <= 1.0
        ):
            raise ValueError("market relevance must be a finite normalized value")
        if self.state in {ParticipationState.OBSERVED, ParticipationState.POTENTIAL}:
            if self.basis is None:
                raise ValueError(
                    "observed/potential market participation requires explainable basis"
                )
            if self.relevance is None:
                raise ValueError("observed/potential market participation requires relevance")
        elif self.relevance is not None:
            raise ValueError("unknown/not-applicable participation cannot carry relevance")


@dataclass(frozen=True, slots=True)
class XeedMarketMap:
    xeed_id: str
    state_fingerprint: str
    classified_at: datetime
    participations: tuple[MarketParticipation, ...]

    def __post_init__(self) -> None:
        if not self.xeed_id.strip() or not self.state_fingerprint.strip():
            raise ValueError("Xeed market map identity is required")
        if self.classified_at.tzinfo is None:
            raise ValueError("market classification time must be timezone-aware")
        relationships = [item.relationship for item in self.participations]
        if len(relationships) != len(set(relationships)):
            raise ValueError("market relationship classification must be unique")
        if set(relationships) != set(MarketRelationship):
            raise ValueError("market map must explicitly classify B2B, B2C and B2G")
        for item in self.participations:
            if item.basis is not None and item.basis.subject_id != self.xeed_id:
                raise ValueError("market participation basis must belong to the Xeed")

    @property
    def observation_targets(self) -> tuple[MarketRelationship, ...]:
        """Observed and potential markets both deserve observation; UNKNOWN is preserved."""
        return tuple(
            item.relationship
            for item in self.participations
            if item.state in {ParticipationState.OBSERVED, ParticipationState.POTENTIAL}
        )
