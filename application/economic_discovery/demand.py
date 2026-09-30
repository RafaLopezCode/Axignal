"""Aggregate demand intelligence without individual consumer profiling."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.explanation import ExplainableBasis


@dataclass(frozen=True, slots=True)
class DemandArchetype:
    archetype_id: str
    xeed_id: str
    need: str
    intent: str
    context: str
    geography: str | None
    channel: str | None
    state_fingerprint: str
    observed_at: datetime
    basis: ExplainableBasis
    individual_identity: None = None

    def __post_init__(self) -> None:
        required = (
            self.archetype_id,
            self.xeed_id,
            self.need,
            self.intent,
            self.context,
            self.state_fingerprint,
        )
        if any(not value.strip() for value in required):
            raise ValueError("demand archetype requires aggregate semantic identity")
        if self.observed_at.tzinfo is None:
            raise ValueError("demand archetype time must be timezone-aware")
        if self.individual_identity is not None:
            raise ValueError("B2C demand archetypes must never identify an individual")
        if self.basis.subject_id != self.xeed_id:
            raise ValueError("demand archetype basis must belong to the Xeed")


@dataclass(frozen=True, slots=True)
class CampaignRelevanceProfile:
    need_fit: float
    intent_strength: float
    demand_strength: float
    growth: float
    geographic_fit: float
    channel_fit: float
    message_fit: float
    evidence_quality: float
    currentness: float
    uncertainty: float
    policy_version: str

    def __post_init__(self) -> None:
        values = (
            self.need_fit,
            self.intent_strength,
            self.demand_strength,
            self.growth,
            self.geographic_fit,
            self.channel_fit,
            self.message_fit,
            self.evidence_quality,
            self.currentness,
            self.uncertainty,
        )
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("campaign relevance dimensions must be finite normalized values")
        if not self.policy_version.strip():
            raise ValueError("campaign relevance policy version is required")
