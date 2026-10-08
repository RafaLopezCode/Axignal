"""Build real governed observations and capabilities for archetype tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.economic_reach.derive import derive_operating_model
from application.economic_reach.model import EconomicOperatingModel
from application.economic_reach.relevance import DemandEvent
from application.observation_intelligence.contracts import (
    CapabilityHypothesis,
    EvidenceRef,
    TaxonomyCode,
)
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
POLICY = TemporalCurrentnessPolicy("reach-test", "1", timedelta(days=60), timedelta(days=365))


def page(
    organization: str,
    source: str,
    text: str,
    *,
    at: datetime = T0,
    n: int = 1,
    fields: tuple[ObservedField, ...] = (),
) -> GovernedObservation:
    observation_id = f"obs:{organization}:{source.rsplit('/', 1)[-1] or 'home'}:{n}"
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id=organization,
            source_ref=source,
            source_type="PUBLIC_WEBSITE",
            observed_at=at,
            content_fingerprint=f"fp:{observation_id}:{hash(text)}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=text,
        fields=fields,
        reuse_authority=ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.PERMITTED,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.GLOBAL_PUBLIC,
            provenance_ref=f"provenance:{observation_id}",
            currentness=Currentness.CURRENT,
            applicable_subject_ids=(organization,),
            applicable_purposes=("HISTORICAL_REFERENCE",),
            authority_id="test",
            authority_version="1",
        ),
    )


def capability(capability_id: str, label: str, source: GovernedObservation) -> CapabilityHypothesis:
    record = source.record
    return CapabilityHypothesis(
        capability_id=capability_id,
        label=label,
        state=XignalEpistemicState.POTENTIAL,
        basis=(EvidenceRef(record.observation_id, record.source_ref, label, record.observed_at),),
        demand_codes=(TaxonomyCode("CPV", "80000000"),),
    )


def model(
    organization: str,
    pages: tuple[GovernedObservation, ...],
    terms: dict[str, tuple[str, ...]],
    *,
    at: datetime = T0 + timedelta(hours=1),
) -> EconomicOperatingModel:
    return derive_operating_model(
        organization_id=organization,
        capabilities=tuple(capability(cid, cid, pages[0]) for cid in terms),
        capability_terms=terms,
        observations=pages,
        as_of=at,
        policy=POLICY,
    )


def demand(
    event_id: str, place: TaxonomyCode, *capability_ids: str, **kwargs: object
) -> DemandEvent:
    return DemandEvent(
        event_id=event_id,
        places=(place,),
        capability_ids=capability_ids,
        deadline=kwargs.pop("deadline", "2026-12-31"),  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
