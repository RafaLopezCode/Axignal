"""Economic Relevance Gate: does this world event belong to this Xeed's garden?

Relevance is not truth and not priority. A true global event can be outside a Xeed's
garden; it stays in global memory for every other Xeed. The gate composes typed,
deterministic judgments per delivery channel (MASTER §53.7 families):

GEOGRAPHIC_ECONOMIC_REACH · LOGISTICS_FEASIBILITY · REGULATORY_ELIGIBILITY ·
MARKET_ACCESS_FEASIBILITY · TEMPORAL_ACTIONABILITY

Each judgment has an outcome (COMPATIBLE / INCOMPATIBLE / UNRESOLVED / NOT_APPLICABLE)
and an epistemic state (OBSERVED / POTENTIAL / UNKNOWN). INCOMPATIBLE requires explicit
evidence; missing evidence is UNRESOLVED. No score, no model. A bounded evaluator may
later answer an UNRESOLVED family; it never overrides an evidenced judgment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_reach.model import (
    DISTANCE_INDEPENDENT,
    LOCATION_BOUND,
    CapabilityReach,
    ClaimBinding,
    DeliveryMode,
    EconomicOperatingModel,
    Polarity,
    ReachBasis,
    ReachClaim,
)
from application.observation_intelligence.contracts import EvidenceRef, TaxonomyCode
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState

OBSERVED = XignalEpistemicState.OBSERVED
POTENTIAL = XignalEpistemicState.POTENTIAL
UNKNOWN = XignalEpistemicState.UNKNOWN
GATE_VERSION = "economic-relevance:1"


class Family(StrEnum):
    GEOGRAPHIC_ECONOMIC_REACH = "GEOGRAPHIC_ECONOMIC_REACH"
    LOGISTICS_FEASIBILITY = "LOGISTICS_FEASIBILITY"
    REGULATORY_ELIGIBILITY = "REGULATORY_ELIGIBILITY"
    MARKET_ACCESS_FEASIBILITY = "MARKET_ACCESS_FEASIBILITY"
    TEMPORAL_ACTIONABILITY = "TEMPORAL_ACTIONABILITY"


class Outcome(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNRESOLVED = "UNRESOLVED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RelevanceScope(StrEnum):
    #: Inside a channel's evidenced reach: may become a POTENTIAL opportunity.
    OPERATING_REACH = "OPERATING_REACH"
    #: Where the Organization's own preparatory acts point: POTENTIAL, shown as growth.
    PLAUSIBLE_EXPANSION = "PLAUSIBLE_EXPANSION"
    #: No reach evidence either way: bounded exploration, explicit gap.
    UNRESOLVED_REACH = "UNRESOLVED_REACH"
    #: Reachable, but explicit evidence blocks acting (e.g. a withdrawn certification).
    NOT_ACTIONABLE = "NOT_ACTIONABLE"
    #: Location-bound channels with known reach elsewhere, or an explicit exclusion.
    OUTSIDE_XEED_REACH = "OUTSIDE_XEED_REACH"


#: Order used to pick the decision across channels; it is not a score.
_RANK = (
    RelevanceScope.OPERATING_REACH,
    RelevanceScope.PLAUSIBLE_EXPANSION,
    RelevanceScope.UNRESOLVED_REACH,
    RelevanceScope.NOT_ACTIONABLE,
    RelevanceScope.OUTSIDE_XEED_REACH,
)
SURFACED = frozenset(
    {
        RelevanceScope.OPERATING_REACH,
        RelevanceScope.PLAUSIBLE_EXPANSION,
        RelevanceScope.UNRESOLVED_REACH,
    }
)


@dataclass(frozen=True, slots=True)
class DemandEvent:
    """A candidate economic event already matched functionally to some capabilities."""

    event_id: str
    places: tuple[TaxonomyCode, ...]
    capability_ids: tuple[str, ...]
    deadline: str | None = None
    required_certifications: tuple[str, ...] = ()
    #: Set only when the event states how it must be delivered (e.g. on site).
    required_modes: frozenset[DeliveryMode] = frozenset()


@dataclass(frozen=True, slots=True)
class Judgment:
    family: Family
    outcome: Outcome
    state: XignalEpistemicState
    reason: str
    evidence: tuple[EvidenceRef, ...] = ()

    def to_wire(self) -> dict[str, object]:
        return {
            "family": self.family.value,
            "outcome": self.outcome.value,
            "state": self.state.value,
            "reason": self.reason,
            "evidence": [
                {"observationId": e.observation_id, "sourceRef": e.source_ref, "excerpt": e.excerpt}
                for e in self.evidence
            ],
        }


@dataclass(frozen=True, slots=True)
class ChannelDecision:
    capability_id: str
    mode: DeliveryMode | None
    scope: RelevanceScope
    judgments: tuple[Judgment, ...]

    def to_wire(self) -> dict[str, object]:
        return {
            "capabilityId": self.capability_id,
            "mode": None if self.mode is None else self.mode.value,
            "scope": self.scope.value,
            "judgments": [j.to_wire() for j in self.judgments],
        }


@dataclass(frozen=True, slots=True)
class RelevanceDecision:
    event_id: str
    scope: RelevanceScope
    #: Capabilities through which the event is relevant (empty when it is not).
    capability_ids: tuple[str, ...]
    channels: tuple[ChannelDecision, ...]
    model_fingerprint: str

    @property
    def surfaced(self) -> bool:
        return self.scope in SURFACED

    @property
    def unknowns(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    f"{j.family.value}:{c.capability_id}"
                    for c in self.channels
                    for j in c.judgments
                    if j.outcome is Outcome.UNRESOLVED
                }
            )
        )

    def explanation(self) -> dict[str, object]:
        """ExplanationTrace: structure AXENT may verbalize; no private reasoning."""
        return {
            "gate": GATE_VERSION,
            "scope": self.scope.value,
            "relevantThrough": list(self.capability_ids),
            "channels": [c.to_wire() for c in self.channels],
            "unknown": list(self.unknowns),
            "operatingModelFingerprint": self.model_fingerprint,
        }


def _contains(claim: ReachClaim, place: TaxonomyCode) -> bool:
    return place.within(claim.geography)


def specific_places(places: tuple[TaxonomyCode, ...]) -> tuple[TaxonomyCode, ...]:
    """Drop places that only contain another listed place (a country next to its region)."""
    return tuple(
        place for place in places if not any(o != place and o.within(place) for o in places)
    )


def _support_state(claims: list[ReachClaim]) -> tuple[XignalEpistemicState, str]:
    current = [c for c in claims if c.currentness is Currentness.CURRENT]
    if any(c.binding is ClaimBinding.CAPABILITY for c in current):
        return OBSERVED, "WITHIN_STATED_REACH"
    if current:
        return POTENTIAL, "WITHIN_ORGANIZATION_STATED_AREA"
    return POTENTIAL, "REACH_SUPPORT_NOT_CURRENT"


def _channel(
    reach: CapabilityReach | None,
    capability_id: str,
    mode: DeliveryMode | None,
    event: DemandEvent,
    as_of: datetime,
) -> ChannelDecision:
    claims = () if reach is None else reach.claims
    places = specific_places(event.places)
    for_mode = [c for c in claims if c.mode in (mode, None)]
    included = [c for c in for_mode if c.polarity is Polarity.INCLUDED]
    judgments: list[Judgment] = []

    def at_event(items: list[ReachClaim], basis: tuple[ReachBasis, ...]) -> list[ReachClaim]:
        return [c for c in items if c.basis in basis and any(_contains(c, p) for p in places)]

    operating_bases: tuple[ReachBasis, ...] = (ReachBasis.STATED_SERVICE_AREA,)
    if mode is DeliveryMode.PROVIDER_PREMISES:
        # Customers come to the premises: the premises' place is where it serves.
        operating_bases = (ReachBasis.STATED_SERVICE_AREA, ReachBasis.PREMISES)
    excluded = [
        c
        for c in for_mode
        if c.polarity is Polarity.EXCLUDED and any(_contains(c, p) for p in places)
    ]
    operating = at_event(included, operating_bases)
    expansion = at_event(included, (ReachBasis.EXPANSION_SIGNAL,))
    exclusive = [c for c in included if c.exclusive and c.basis is ReachBasis.STATED_SERVICE_AREA]
    known = [c for c in included if c.basis in operating_bases]
    # The event names a broader place that contains the reach (a national call next to a
    # Madrid installer): it may be performed inside the reach, so it is not outside.
    broader = [c for c in known if any(c.geography.within(p) for p in places)]

    if excluded:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.INCOMPATIBLE,
            OBSERVED,
            "EXPLICITLY_EXCLUDED_AREA",
            tuple(c.evidence for c in excluded),
        )
    elif operating:
        state, reason = _support_state(operating)
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.COMPATIBLE,
            state,
            reason,
            tuple(c.evidence for c in operating),
        )
    elif expansion:
        kinds = sorted({c.signal or "" for c in expansion})
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.COMPATIBLE,
            POTENTIAL,
            "EXPANSION_SIGNAL:" + "+".join(kinds),
            tuple(c.evidence for c in expansion),
        )
    elif broader:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.UNRESOLVED,
            UNKNOWN,
            "EVENT_PLACE_BROADER_THAN_REACH",
            tuple(c.evidence for c in broader),
        )
    elif exclusive:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.INCOMPATIBLE,
            OBSERVED,
            "OUTSIDE_EXCLUSIVE_STATED_AREA",
            tuple(c.evidence for c in exclusive),
        )
    elif mode in DISTANCE_INDEPENDENT:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.NOT_APPLICABLE,
            OBSERVED,
            "DISTANCE_INDEPENDENT_DELIVERY",
        )
    elif known:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH,
            Outcome.UNRESOLVED,
            UNKNOWN,
            "NO_REACH_EVIDENCE_AT_EVENT_PLACE",
            tuple(c.evidence for c in known),
        )
    else:
        geo = Judgment(
            Family.GEOGRAPHIC_ECONOMIC_REACH, Outcome.UNRESOLVED, UNKNOWN, "NO_REACH_EVIDENCE"
        )
    judgments.append(geo)

    # Market access: distance does not bind remote/digital channels, jurisdiction does.
    if mode in DISTANCE_INDEPENDENT and geo.outcome is Outcome.NOT_APPLICABLE:
        countries = {
            c.geography.code.split("/")[:2] == p.code.split("/")[:2] for c in known for p in places
        }
        if True in countries:
            judgments.append(
                Judgment(
                    Family.MARKET_ACCESS_FEASIBILITY,
                    Outcome.COMPATIBLE,
                    POTENTIAL,
                    "SAME_JURISDICTION_AS_STATED_REACH",
                    tuple(c.evidence for c in known),
                )
            )
        else:
            judgments.append(
                Judgment(
                    Family.MARKET_ACCESS_FEASIBILITY,
                    Outcome.UNRESOLVED,
                    UNKNOWN,
                    "JURISDICTION_ACCESS_UNKNOWN",
                )
            )
    elif mode is DeliveryMode.SHIPPED:
        judgments.append(
            Judgment(
                Family.MARKET_ACCESS_FEASIBILITY,
                Outcome.UNRESOLVED,
                UNKNOWN,
                "CUSTOMS_AND_TAX_UNOBSERVED",
            )
        )

    if mode in (DeliveryMode.CUSTOMER_SITE, DeliveryMode.SHIPPED):
        judgments.append(
            Judgment(
                Family.LOGISTICS_FEASIBILITY, Outcome.UNRESOLVED, UNKNOWN, "LOGISTICS_UNOBSERVED"
            )
        )
    elif mode is not None:
        judgments.append(
            Judgment(
                Family.LOGISTICS_FEASIBILITY,
                Outcome.NOT_APPLICABLE,
                OBSERVED,
                f"{mode.value}_DELIVERY",
            )
        )

    held = {} if reach is None else {k.value: k for k in reach.constraints}
    if not event.required_certifications:
        judgments.append(
            Judgment(
                Family.REGULATORY_ELIGIBILITY,
                Outcome.NOT_APPLICABLE,
                OBSERVED,
                "NO_STATED_REQUIREMENT",
            )
        )
    for required in event.required_certifications:
        claim = held.get(required.upper())
        if claim is None:
            judgments.append(
                Judgment(
                    Family.REGULATORY_ELIGIBILITY,
                    Outcome.UNRESOLVED,
                    UNKNOWN,
                    f"QUALIFICATION_UNOBSERVED:{required}",
                )
            )
        elif claim.withdrawn:
            judgments.append(
                Judgment(
                    Family.REGULATORY_ELIGIBILITY,
                    Outcome.INCOMPATIBLE,
                    OBSERVED,
                    f"QUALIFICATION_WITHDRAWN:{required}",
                    (claim.evidence,),
                )
            )
        else:
            judgments.append(
                Judgment(
                    Family.REGULATORY_ELIGIBILITY,
                    Outcome.COMPATIBLE,
                    OBSERVED if claim.binding is ClaimBinding.CAPABILITY else POTENTIAL,
                    f"QUALIFICATION_STATED:{required}",
                    (claim.evidence,),
                )
            )

    if event.deadline is None:
        judgments.append(
            Judgment(Family.TEMPORAL_ACTIONABILITY, Outcome.UNRESOLVED, UNKNOWN, "WINDOW_UNKNOWN")
        )
    elif event.deadline[:10] >= as_of.date().isoformat():
        judgments.append(
            Judgment(Family.TEMPORAL_ACTIONABILITY, Outcome.COMPATIBLE, OBSERVED, "WINDOW_OPEN")
        )
    else:
        judgments.append(
            Judgment(Family.TEMPORAL_ACTIONABILITY, Outcome.INCOMPATIBLE, OBSERVED, "WINDOW_CLOSED")
        )

    return ChannelDecision(
        capability_id, mode, _scope(judgments, geo, mode, known), tuple(judgments)
    )


def _scope(
    judgments: list[Judgment], geo: Judgment, mode: DeliveryMode | None, known: list[ReachClaim]
) -> RelevanceScope:
    if geo.outcome is Outcome.INCOMPATIBLE:
        return RelevanceScope.OUTSIDE_XEED_REACH
    blocked = any(
        j.outcome is Outcome.INCOMPATIBLE
        for j in judgments
        if j.family is not Family.GEOGRAPHIC_ECONOMIC_REACH
    )
    if geo.outcome is Outcome.COMPATIBLE:
        if blocked:
            return RelevanceScope.NOT_ACTIONABLE
        return (
            RelevanceScope.PLAUSIBLE_EXPANSION
            if geo.reason.startswith("EXPANSION_SIGNAL")
            else RelevanceScope.OPERATING_REACH
        )
    if geo.outcome is Outcome.NOT_APPLICABLE:
        access = next(j for j in judgments if j.family is Family.MARKET_ACCESS_FEASIBILITY)
        if blocked:
            return RelevanceScope.NOT_ACTIONABLE
        return (
            RelevanceScope.OPERATING_REACH
            if access.outcome is Outcome.COMPATIBLE
            else RelevanceScope.UNRESOLVED_REACH
        )
    # UNRESOLVED geography: a location-bound channel with evidenced reach elsewhere is
    # outside this Xeed's garden (not false: just not evidenced here).
    if known and mode in LOCATION_BOUND and geo.reason == "NO_REACH_EVIDENCE_AT_EVENT_PLACE":
        return RelevanceScope.OUTSIDE_XEED_REACH
    return RelevanceScope.NOT_ACTIONABLE if blocked else RelevanceScope.UNRESOLVED_REACH


def assess_demand(
    model: EconomicOperatingModel, event: DemandEvent, *, as_of: datetime
) -> RelevanceDecision:
    """Per channel (capability by delivery mode), then the best scope across channels."""

    if as_of.tzinfo is None:
        raise ValueError("relevance evaluation time must be timezone-aware")
    channels: list[ChannelDecision] = []
    for capability_id in sorted(set(event.capability_ids)):
        reach = model.reach_for(capability_id)
        modes: list[DeliveryMode | None] = list(sorted(reach.mode_values())) if reach else []
        if event.required_modes:
            fitting: list[DeliveryMode | None] = [m for m in modes if m in event.required_modes]
            modes = fitting or [None]
        for mode in modes or [None]:
            channels.append(_channel(reach, capability_id, mode, event, as_of))
    if not channels:
        raise ValueError("a demand event must name at least one matched capability")
    best = min(channels, key=lambda c: _RANK.index(c.scope)).scope
    through = tuple(sorted({c.capability_id for c in channels if c.scope is best}))
    return RelevanceDecision(
        event_id=event.event_id,
        scope=best,
        capability_ids=through if best in SURFACED else (),
        channels=tuple(channels),
        model_fingerprint=model.fingerprint,
    )
