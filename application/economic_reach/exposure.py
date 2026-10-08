"""Economic exposure: external drivers that reach a business without being its market.

An oil shock in another region is not an opportunity and not a place the business
serves. It can still affect it through a transmission channel its operating model
depends on. Exposure is assessed as a path driver → channel → delivery channel →
Organization; the driver's locus is irrelevant to reach. Paths derived from delivery
modes are governed derivations (POTENTIAL), never observed effects or forecasts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.economic_reach.model import (
    EconomicOperatingModel,
    ExposureChannel,
    Polarity,
    ReachBasis,
)
from application.observation_intelligence.contracts import EvidenceRef, TaxonomyCode
from domain.xignal import XignalEpistemicState


class DriverKind(StrEnum):
    ENERGY_PRICE = "ENERGY_PRICE"
    FUEL_PRICE = "FUEL_PRICE"
    FREIGHT_COST = "FREIGHT_COST"
    REGULATORY_CHANGE = "REGULATORY_CHANGE"
    PLATFORM_CHANGE = "PLATFORM_CHANGE"
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"


#: Governed transmission: which operating dependency a driver acts on.
DRIVER_CHANNELS: dict[DriverKind, tuple[ExposureChannel, ...]] = {
    DriverKind.ENERGY_PRICE: (ExposureChannel.PREMISES_ENERGY, ExposureChannel.FUEL_AND_TRAVEL),
    DriverKind.FUEL_PRICE: (ExposureChannel.FUEL_AND_TRAVEL, ExposureChannel.FREIGHT_AND_CUSTOMS),
    DriverKind.FREIGHT_COST: (ExposureChannel.FREIGHT_AND_CUSTOMS, ExposureChannel.SUPPLY_INPUTS),
    DriverKind.REGULATORY_CHANGE: (ExposureChannel.LOCAL_REGULATION,),
    DriverKind.PLATFORM_CHANGE: (ExposureChannel.DIGITAL_PLATFORM,),
    DriverKind.SUPPLY_DISRUPTION: (ExposureChannel.SUPPLY_INPUTS,),
}


class ExposureScope(StrEnum):
    EXPOSURE = "EXPOSURE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class DriverEvent:
    event_id: str
    driver: DriverKind
    evidence: EvidenceRef
    #: Where the driver happens; informative only, never a reach test.
    locus: TaxonomyCode | None = None
    #: For regulation: the jurisdiction where the rule applies.
    applies_in: TaxonomyCode | None = None


@dataclass(frozen=True, slots=True)
class ExposureDecision:
    event_id: str
    scope: ExposureScope
    state: XignalEpistemicState
    paths: tuple[dict[str, object], ...]
    reason: str

    def explanation(self) -> dict[str, object]:
        return {
            "scope": self.scope.value,
            "state": self.state.value,
            "reason": self.reason,
            "transmission": list(self.paths),
            "isOpportunity": False,
        }


def assess_exposure(model: EconomicOperatingModel, event: DriverEvent) -> ExposureDecision:
    channels = set(DRIVER_CHANNELS[event.driver])
    paths = [p for p in model.exposure if p.channel in channels]
    if event.driver is DriverKind.REGULATORY_CHANGE:
        # A rule binds where the business operates or has premises, not everywhere.
        where = [
            claim
            for reach in model.capabilities
            for claim in reach.claims
            if claim.polarity is Polarity.INCLUDED
            and claim.basis in (ReachBasis.STATED_SERVICE_AREA, ReachBasis.PREMISES)
        ]
        if event.applies_in is None or not where:
            return ExposureDecision(
                event.event_id,
                ExposureScope.UNRESOLVED,
                XignalEpistemicState.UNKNOWN,
                (),
                "JURISDICTION_OF_OPERATION_UNKNOWN",
            )
        if not any(
            claim.geography.within(event.applies_in) or event.applies_in.within(claim.geography)
            for claim in where
        ):
            return ExposureDecision(
                event.event_id,
                ExposureScope.NOT_APPLICABLE,
                XignalEpistemicState.OBSERVED,
                (),
                "RULE_APPLIES_ELSEWHERE",
            )
    if not paths:
        reason = "NO_DEPENDENCY_ON_DRIVER" if model.exposure else "OPERATING_MODEL_UNKNOWN"
        scope = ExposureScope.NOT_APPLICABLE if model.exposure else ExposureScope.UNRESOLVED
        state = XignalEpistemicState.OBSERVED if model.exposure else XignalEpistemicState.UNKNOWN
        return ExposureDecision(event.event_id, scope, state, (), reason)
    return ExposureDecision(
        event.event_id,
        ExposureScope.EXPOSURE,
        XignalEpistemicState.POTENTIAL,  # a plausible path, never an observed impact
        tuple(
            {
                "driver": event.driver.value,
                "locus": None if event.locus is None else event.locus.code,
                "channel": path.channel.value,
                "capabilityId": path.capability_id,
                "via": path.via,
                "evidence": [e.observation_id for e in path.evidence],
            }
            for path in sorted(paths, key=lambda p: (p.channel.value, p.capability_id or "", p.via))
        ),
        "TRANSMISSION_PATH_THROUGH_OPERATING_MODEL",
    )
