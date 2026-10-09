"""Authorized, persisted subscriber read path for governed Brain outputs.

This application service never performs acquisition or synthesizes economics.
It reauthorizes the selected Observation Focus on every read, resolves its one
canonical Organization, loads immutable output snapshots, and revalidates the
snapshot evidence against reusable Observation Memory at the requested time.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.brain_contracts import (
    ObservationMode,
    ObservationRecord,
)
from application.economic_discovery.contracts import StructuredEvaluatorPort
from application.economic_discovery.execution_budget import (
    ExecutionReservationRejected,
    GovernedExecutionController,
)
from application.economic_discovery.execution_learning import execution_stop_learning_event
from application.economic_discovery.first_vertical_e2e import (
    FirstEconomicVerticalE2EResult,
    FirstVerticalDispatchCosts,
    FirstVerticalSourcePlan,
    SourceMaterializationNotMeasured,
    SubjectIdentityBindingPort,
    run_first_economic_vertical_e2e,
)
from application.economic_discovery.learning_memory import (
    LearningEventKind,
    LearningMechanism,
    LearningMemory,
)
from application.economic_discovery.market_entry import (
    MarketRelationship,
    ParticipationState,
    XeedMarketMap,
)
from application.economic_discovery.market_planning import (
    MarketObservationDirective,
    ObservationObjectType,
    plan_market_observation,
)
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessMetadata,
    ObservationAccessStatus,
    ObservationMemory,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
)
from application.economic_discovery.observation_reuse import (
    ObservationReuseContext,
    ObservationReusePolicy,
    ReusePurpose,
    ReuseTargetScope,
    select_reusable_observations,
)
from application.economic_discovery.prime_execution import (
    SemanticExtractionPort,
    SourceAcquisitionPort,
    SourceRepresentationPort,
)
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_effective_currentness,
)
from application.economic_reach.exposure import DriverEvent
from application.observation_intelligence.contracts import MarketRole, XeedObservationContext
from application.observation_intelligence.coverage import EvidenceCoverageMap
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.loop import (
    LoopResult,
    SourceObservationPort,
    run_observation_loop,
)
from application.observation_intelligence.registry import SourceRegistry
from application.observation_intelligence.semantic_screen import DemandScreenPort
from application.observation_intelligence.strategy import ObservationStrategy
from application.observation_intelligence.subscriber_projection import (
    SubscriberOpportunityProjection,
    SubscriberOpportunityProjectionError,
    project_observation_opportunities,
)
from application.semantic_extraction import EconomicClaimCandidate
from application.subscriber_projection.cognitive_projection import observation_cognition
from application.subscriber_projection.dri_measurement import (
    DRI_INSTRUMENT_REF,
    DRI_INSTRUMENT_VERSION,
    measure_public_page_representation,
)
from application.subscriber_projection.economic_runtime import economic_output_runtime_signal
from application.subscriber_projection.evidence_delivery import (
    CurrentContentRights,
    RecordedContentRights,
    content_reusable_history,
    deliver_evidence_content,
)
from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganization,
    AuthorizedXeedOrganizationReader,
)
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    TrustedRequestContext,
)
from domain.evidence.epistemics import Currentness
from domain.identity import XeedId
from domain.organizations.model import Organization
from domain.xeed.model import Xeed


class SubscriberRuntimeStatus(StrEnum):
    SUCCESS = "success"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class SubscriberEconomicStoreError(ValueError):
    """A persisted output is malformed, mismatched, or conflicts with history."""


_CURRENTNESS_PRECEDENCE = {
    Currentness.CURRENT: 0,
    Currentness.STALE: 1,
    Currentness.HISTORICAL: 2,
    Currentness.UNKNOWN: 3,
}


@dataclass(frozen=True, slots=True)
class StoredEconomicOutput:
    tenant_id: str
    xeed_id: str
    organization_id: str
    output_id: str
    as_of: datetime
    output_wire: dict[str, object]
    runtime_signal: dict[str, object]

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.tenant_id,
                self.xeed_id,
                self.organization_id,
                self.output_id,
            )
        ):
            raise SubscriberEconomicStoreError("stored economic output identity is required")
        if self.as_of.tzinfo is None:
            raise SubscriberEconomicStoreError("stored economic output time must be timezone-aware")
        if self.output_wire.get("output_id") != self.output_id:
            raise SubscriberEconomicStoreError("stored output payload identity mismatch")
        if self.output_wire.get("subject_ref") != self.organization_id:
            raise SubscriberEconomicStoreError("stored output subject mismatch")
        if self.runtime_signal.get("nodeKind") != "XIGNAL":
            raise SubscriberEconomicStoreError("stored subscriber signal is invalid")


class SubscriberEconomicOutputStore(Protocol):
    def append(self, output: StoredEconomicOutput) -> bool:
        """Append immutable output; return False only for an exact replay."""

    def latest(
        self,
        *,
        tenant_id: str,
        xeed_id: str,
        organization_id: str,
        as_of: datetime,
    ) -> StoredEconomicOutput | None:
        """Read the latest output in this exact private context, effective by as_of."""


class SubscriberOpportunityProjectionStore(Protocol):
    def append(self, projection: SubscriberOpportunityProjection) -> bool:
        """Append an immutable cognition projection; False means exact replay."""

    def latest(
        self,
        *,
        tenant_id: str,
        xeed_id: str,
        organization_id: str,
        as_of: datetime,
    ) -> SubscriberOpportunityProjection | None:
        """Read only the latest projection in this exact authorized context."""


class ContinuityRecorder(Protocol):
    def record(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, *, as_of: datetime
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class SubscriberRuntimeRead:
    status: SubscriberRuntimeStatus
    projection: dict[str, object]
    reason: str | None = None

    def to_wire(self) -> dict[str, object]:
        result: dict[str, object] = {"state": self.status.value, "projection": self.projection}
        if self.reason is not None:
            result["reason"] = self.reason
        return result


@dataclass(frozen=True, slots=True)
class SubscriberObservationLoopExecutionPlan:
    """Server-owned plan for one bounded Opportunity Intelligence observation loop."""

    observation_context: XeedObservationContext
    strategy: ObservationStrategy
    adapters: Mapping[str, SourceObservationPort]
    coverage: EvidenceCoverageMap
    learning: OperationalLearning
    registry: SourceRegistry

    def __post_init__(self) -> None:
        if self.strategy.xeed_id != self.observation_context.xeed_id:
            raise ValueError("observation loop plan Xeed identity mismatch")
        if self.strategy.as_of != self.observation_context.as_of:
            raise ValueError("observation loop plan temporal cut mismatch")


@dataclass(frozen=True, slots=True)
class SubscriberEconomicExecutionPlan:
    """Server-owned, already-authorized inputs for one bounded EB-04 run."""

    market_map: XeedMarketMap
    subject_plan: FirstVerticalSourcePlan
    market_catalogue: tuple[MarketActivityPlanDescriptor, ...]
    selected_relationship: MarketRelationship | None
    source_acquirer: SourceAcquisitionPort
    representation_port: SourceRepresentationPort
    semantic_extractor: SemanticExtractionPort
    binding_port: SubjectIdentityBindingPort
    evaluator: StructuredEvaluatorPort
    execution_controller: GovernedExecutionController
    dispatch_costs: FirstVerticalDispatchCosts
    learning_memory: LearningMemory
    as_of: datetime

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None:
            raise ValueError("subscriber execution time must be timezone-aware")
        if self.market_map.classified_at > self.as_of:
            raise ValueError("market map cannot be from after the execution time")


@dataclass(frozen=True, slots=True)
class MarketActivityPlanDescriptor:
    """Server-owned bounded activity source plan for one posture and object kind."""

    descriptor_id: str
    version: str
    relationship: MarketRelationship
    participation_state: ParticipationState
    object_type: ObservationObjectType
    plan: FirstVerticalSourcePlan

    def __post_init__(self) -> None:
        if not self.descriptor_id.strip() or not self.version.strip():
            raise ValueError("market activity plan descriptor identity is required")
        if self.participation_state not in {
            ParticipationState.OBSERVED,
            ParticipationState.POTENTIAL,
        }:
            raise ValueError("source plan descriptors cannot target UNKNOWN market posture")
        if (
            self.relationship is MarketRelationship.B2C
            and self.object_type is not ObservationObjectType.DEMAND_ARCHETYPE
        ):
            raise ValueError("B2C routing may target aggregate Demand Archetypes only")


@dataclass(frozen=True, slots=True)
class MarketPlanRouting:
    directive: MarketObservationDirective | None
    descriptor: MarketActivityPlanDescriptor | None
    rejected: tuple[str, ...]


def route_market_activity_plan(
    *,
    market_map: XeedMarketMap,
    catalogue: tuple[MarketActivityPlanDescriptor, ...],
    selected_relationship: MarketRelationship | None,
) -> MarketPlanRouting:
    """Select exactly one configured market plan or retain an explicit abstention."""
    directives = plan_market_observation(market_map)
    candidates = tuple(
        item
        for item in directives
        if selected_relationship is None or item.relationship is selected_relationship
    )
    if not candidates:
        return MarketPlanRouting(None, None, ("NO_OBSERVED_OR_POTENTIAL_MARKET_TARGET",))
    if len(candidates) != 1:
        return MarketPlanRouting(
            None,
            None,
            ("MULTIPLE_MARKETS_REQUIRE_EXPLICIT_RELATIONSHIP_SELECTION",),
        )
    directive = candidates[0]
    matching = tuple(
        item
        for item in catalogue
        if item.relationship is directive.relationship
        and item.participation_state is directive.participation_state
        and item.object_type in directive.object_types
    )
    if not matching:
        return MarketPlanRouting(
            directive,
            None,
            (
                f"NO_CONFIGURED_PLAN:{directive.relationship.value}:{directive.participation_state.value}",
            ),
        )
    if len(matching) != 1:
        return MarketPlanRouting(
            directive,
            None,
            (f"AMBIGUOUS_CONFIGURED_PLANS:{directive.relationship.value}",),
        )
    descriptor = matching[0]
    rejected = tuple(
        f"NOT_SELECTED:{item.relationship.value}:{item.object_type.value}"
        for item in catalogue
        if item.descriptor_id != descriptor.descriptor_id
    )
    return MarketPlanRouting(directive, descriptor, rejected)


@dataclass(frozen=True, slots=True)
class SubscriberExecutionOutcome:
    state: str
    read: SubscriberRuntimeRead | None = None
    reason: str | None = None
    market_targets: tuple[str, ...] = ()
    dri_measurement_attempt: dict[str, object] | None = None

    def to_wire(self) -> dict[str, object]:
        result: dict[str, object] = {"state": self.state}
        if self.read is not None:
            result["read"] = self.read.to_wire()
        if self.reason is not None:
            result["reason"] = self.reason
        if self.market_targets:
            result["marketTargets"] = list(self.market_targets)
        if self.dri_measurement_attempt is not None:
            result["digitalRepresentationAttempt"] = self.dri_measurement_attempt
        return result


def _dri_not_measured(
    reason_code: str,
    explanation: str,
    *,
    detail_code: str | None = None,
    sample_attempt: dict[str, object] | None = None,
) -> dict[str, object]:
    reason: dict[str, object] = {"code": reason_code, "explanation": explanation}
    if detail_code is not None:
        reason["detailCode"] = detail_code
    result: dict[str, object] = {
        "kind": "DRI_PUBLIC_PAGE_REPRESENTATION",
        "instrument": {"ref": DRI_INSTRUMENT_REF, "version": DRI_INSTRUMENT_VERSION},
        "state": "NOT_MEASURED",
        "reason": reason,
        "scopeLimit": (
            "No page-level measurement was completed. This run does not establish search, "
            "generative, social, whole-Organization or SEO/GEO visibility."
        ),
    }
    if sample_attempt is not None:
        result["sampleAttempt"] = sample_attempt
    return result


def _iso(value: datetime) -> str:
    return value.isoformat()


def _base_projection(
    *,
    organization: Organization,
    xeed: Xeed,
    code_sha: str,
) -> dict[str, object]:
    return {
        "realityLevel": "SUBSCRIBER_RUNTIME_READ_MODEL",
        "runtimeCodeSha": code_sha,
        "lifecycleStatus": "LIVE",
        "context": {"id": xeed.id, "label": organization.canonical_name},
        "organization": {"id": organization.id, "name": organization.canonical_name},
        "nodes": [],
        "temporalHistory": {"disposition": "EMPTY", "items": []},
        "digitalRepresentation": {
            "state": "NOT_MEASURED",
            "reason": "No condition-bound public page measurement is available for this read.",
        },
        "memberships": [],
        "today": {"disposition": "EMPTY", "items": []},
        "reloadContinuity": "PERSISTED_RUNTIME_READ_MODEL",
    }


def _authorized_public_history(
    *,
    memory: ObservationMemory,
    organization_id: str,
    xeed_id: str,
    tenant_id: str,
    as_of: datetime,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
) -> tuple[tuple[GovernedObservation, Currentness], ...]:
    context = ObservationReuseContext(
        subject_id=organization_id,
        xeed_id=xeed_id,
        tenant_id=tenant_id,
        target_scope=ReuseTargetScope.GLOBAL_WORLD,
        purpose=ReusePurpose.HISTORICAL_REFERENCE,
        as_of=as_of,
    )
    selection = select_reusable_observations(
        memory, context=context, policy=reuse_policy, temporal_policy=temporal_policy
    )
    currentness_by_id = {
        decision.observation_id: decision.effective_currentness
        for decision in selection.decisions
        if decision.disposition.value == "ALLOW"
    }
    return tuple(
        (item, currentness_by_id[item.record.observation_id])
        for item in selection.observations
        if item.record.observation_id in currentness_by_id
    )


def _temporal_history(
    observations: tuple[tuple[GovernedObservation, Currentness], ...],
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    prior_fields: tuple[tuple[str, str], ...] | None = None
    for observation, currentness in observations:
        record = observation.record
        fields = tuple(sorted((item.name, item.value) for item in observation.fields))
        items.append(
            {
                "observationId": record.observation_id,
                "sourceRef": record.source_ref,
                "sourceType": record.source_type,
                "observedAt": _iso(record.observed_at),
                "currentness": currentness.value,
                "normalizedStateChanged": None if prior_fields is None else fields != prior_fields,
            }
        )
        prior_fields = fields
    return {
        "disposition": (
            "EMPTY"
            if not items
            else "SINGLE_OBSERVATION"
            if len(items) == 1
            else "MULTIPLE_OBSERVATIONS"
        ),
        "items": items,
    }


def _currentness_at(
    source: dict[str, object], *, as_of: datetime, policy: TemporalCurrentnessPolicy
) -> Currentness:
    source_id = source.get("id")
    observed_at = source.get("observedAt")
    if not isinstance(source_id, str) or not isinstance(observed_at, str):
        return Currentness.UNKNOWN
    try:
        previous = Currentness(str(source.get("currentness")))
        observed_time = datetime.fromisoformat(observed_at)
        return evaluate_effective_currentness(
            observation_id=source_id,
            observed_at=observed_time,
            previous=previous,
            as_of=as_of,
            policy=policy,
        ).current
    except (TypeError, ValueError):
        return Currentness.UNKNOWN


def _merge_opportunity_cognition(
    *,
    base: dict[str, object],
    stored: SubscriberOpportunityProjection | None,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> dict[str, object]:
    """Merge persisted opportunity facts with this read's authorized evidence."""
    cognition = deepcopy(base)
    cognition["asOf"] = _iso(as_of)
    if stored is None:
        return cognition

    stored_cognition = stored.cognition
    base_sources = cognition.get("sources")
    stored_sources = stored_cognition.get("sources")
    base_signals = cognition.get("signals")
    stored_signals = stored_cognition.get("signals")
    base_opportunities = cognition.get("opportunities")
    stored_opportunities = stored_cognition.get("opportunities")
    if not all(
        isinstance(items, list)
        for items in (
            base_sources,
            stored_sources,
            base_signals,
            stored_signals,
            base_opportunities,
            stored_opportunities,
        )
    ):
        raise SubscriberEconomicStoreError("persisted cognition collections are malformed")
    assert isinstance(base_sources, list)
    assert isinstance(stored_sources, list)
    assert isinstance(base_signals, list)
    assert isinstance(stored_signals, list)
    assert isinstance(base_opportunities, list)
    assert isinstance(stored_opportunities, list)

    sources_by_id: dict[str, dict[str, object]] = {}
    for value in (*base_sources, *stored_sources):
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            continue
        sources_by_id[str(value["id"])] = deepcopy(value)
    effective_sources: dict[str, Currentness] = {}
    for source_id, source in sources_by_id.items():
        currentness = _currentness_at(source, as_of=as_of, policy=policy)
        source["currentness"] = currentness.value
        source["currentnessEvaluatedAt"] = _iso(as_of)
        effective_sources[source_id] = currentness

    opportunities: list[dict[str, object]] = []
    for value in stored_opportunities:
        if not isinstance(value, dict):
            continue
        opportunity = deepcopy(value)
        capability = opportunity.get("capability")
        demand = opportunity.get("demand")
        source_ids = (
            capability.get("sourceId") if isinstance(capability, dict) else None,
            demand.get("sourceId") if isinstance(demand, dict) else None,
        )
        statuses = [
            effective_sources.get(source_id, Currentness.UNKNOWN)
            for source_id in source_ids
            if isinstance(source_id, str)
        ]
        currentness = (
            max(statuses, key=_CURRENTNESS_PRECEDENCE.__getitem__)
            if len(statuses) == 2
            else Currentness.UNKNOWN
        )
        opportunity["currentness"] = currentness.value
        opportunity["currentnessEvaluatedAt"] = _iso(as_of)
        if currentness is not Currentness.CURRENT:
            opportunity["epistemic"] = "UNKNOWN"
            unknowns = opportunity.get("unknown")
            opportunity["unknown"] = list(
                dict.fromkeys(
                    [
                        *(unknowns if isinstance(unknowns, list) else []),
                        "Supporting evidence is stale or its currentness cannot be verified.",
                    ]
                )
            )
        opportunities.append(opportunity)

    signal_by_id: dict[str, dict[str, str]] = {}
    for value in (*base_signals, *stored_signals):
        if (
            isinstance(value, dict)
            and isinstance(value.get("id"), str)
            and isinstance(value.get("familyId"), str)
        ):
            signal_by_id[str(value["id"])] = {
                "id": str(value["id"]),
                "familyId": str(value["familyId"]),
            }
    cognition["sources"] = [sources_by_id[key] for key in sorted(sources_by_id)]
    cognition["signals"] = [signal_by_id[key] for key in sorted(signal_by_id)]
    cognition["opportunities"] = sorted(
        opportunities,
        key=lambda item: (str(item.get("observedAt", "")), str(item.get("id", ""))),
    )
    # Spec 059: the garden the snapshot was judged against, what it kept out, and the
    # exposure it found travel with the snapshot (its reach evidence is a declared
    # continuity dependency, so a stale garden is re-evaluated, not shown as current).
    for key in ("economicGarden", "relevanceFiltered", "exposure", "semanticLayer"):
        if key in stored_cognition:
            cognition[key] = deepcopy(stored_cognition[key])
    return cognition


def _output_evidence_currentness(
    *,
    output: StoredEconomicOutput,
    memory: ObservationMemory,
    xeed_id: str,
    tenant_id: str,
    as_of: datetime,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
) -> Currentness:
    evidence = output.output_wire.get("evidence")
    if not isinstance(evidence, (tuple, list)) or not evidence:
        return Currentness.UNKNOWN

    subjects = tuple(
        dict.fromkeys(
            value
            for value in (
                output.output_wire.get("subject_ref"),
                output.output_wire.get("activity_subject_ref"),
            )
            if isinstance(value, str) and value.strip()
        )
    )
    records: dict[str, tuple[GovernedObservation, Currentness]] = {}
    for subject_id in subjects:
        context = ObservationReuseContext(
            subject_id=subject_id,
            xeed_id=xeed_id,
            tenant_id=tenant_id,
            target_scope=ReuseTargetScope.GLOBAL_WORLD,
            purpose=ReusePurpose.HISTORICAL_REFERENCE,
            as_of=as_of,
        )
        selection = select_reusable_observations(
            memory, context=context, policy=reuse_policy, temporal_policy=temporal_policy
        )
        decision_by_id = {
            item.observation_id: item
            for item in selection.decisions
            if item.disposition.value == "ALLOW"
        }
        for item in selection.observations:
            decision = decision_by_id.get(item.record.observation_id)
            if decision is not None:
                records[item.record.observation_id] = (item, decision.effective_currentness)

    statuses: list[Currentness] = []
    for datum in evidence:
        if not isinstance(datum, dict):
            return Currentness.UNKNOWN
        observation_id = datum.get("observation_ref")
        record = records.get(str(observation_id)) if observation_id is not None else None
        if record is None:
            statuses.append(Currentness.UNKNOWN)
            continue
        observation, currentness = record
        if observation.record.source_ref != datum.get("source_ref") or _iso(
            observation.record.observed_at
        ) != datum.get("observed_at"):
            statuses.append(Currentness.UNKNOWN)
        else:
            statuses.append(currentness)

    for candidate in (Currentness.UNKNOWN, Currentness.HISTORICAL, Currentness.STALE):
        if candidate in statuses:
            return candidate
    return Currentness.CURRENT


def _refresh_signal(
    output: StoredEconomicOutput,
    currentness: Currentness,
) -> tuple[dict[str, object], dict[str, object], bool]:
    signal = deepcopy(output.runtime_signal)
    wire = deepcopy(output.output_wire)
    is_current = currentness is Currentness.CURRENT
    signal["currentness"] = currentness.value
    if is_current:
        return signal, wire, True

    message = "Supporting observations could not be confirmed current for this read."
    signal["epistemicState"] = "UNKNOWN"
    signal["title"] = "Economic result needs reevaluation"
    signal["whyAttention"] = message
    signal["interpretation"] = message
    signal["uncertainty"] = message
    unknowns = signal.get("unknowns")
    signal["unknowns"] = list(
        dict.fromkeys([*(unknowns if isinstance(unknowns, list) else []), message])
    )
    narrative = signal.get("evidenceNarrative")
    if isinstance(narrative, dict):
        for step in narrative.get("steps", []):
            if isinstance(step, dict):
                step["currentness"] = currentness.value

    wire["temporal_state"] = currentness.value
    wire["epistemic_state"] = "UNKNOWN"
    wire["attention"] = "INVESTIGATE"
    wire["headline"] = "Economic result needs reevaluation"
    wire["one_sentence_meaning"] = message
    wire["why_it_may_matter"] = message
    existing_unknowns = wire.get("unknowns")
    wire["unknowns"] = tuple(
        dict.fromkeys(
            [*(existing_unknowns if isinstance(existing_unknowns, (list, tuple)) else ()), message]
        )
    )
    return signal, wire, False


@dataclass(slots=True)
class SubscriberEconomicRuntime:
    """Membership-first runtime read/write service for subscriber outputs."""

    authorized_xeeds: AuthorizedXeedReader
    organization_reader: AuthorizedXeedOrganizationReader
    observation_memory: ObservationMemory
    output_store: SubscriberEconomicOutputStore
    opportunity_store: SubscriberOpportunityProjectionStore
    reuse_policy: ObservationReusePolicy
    temporal_policy: TemporalCurrentnessPolicy
    code_sha: str
    content_rights: CurrentContentRights = field(default_factory=RecordedContentRights)
    #: Private continuity recorder (TASK-050 T023); checkpoints follow each new snapshot.
    continuity: ContinuityRecorder | None = None
    #: Optional semantic demand screen (Spec 062); absent, projection is deterministic only.
    semantic_screen: DemandScreenPort | None = None

    def __post_init__(self) -> None:
        if not self.code_sha.strip():
            raise ValueError("subscriber runtime code identity is required")

    def authorize(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
    ) -> AuthorizedXeedOrganization:
        """Membership, Focus and canonical Organization recheck (no data is read)."""
        return self._read_context(authorized_context, xeed_id)

    def _checkpoint(
        self, authorized_context: TrustedRequestContext, xeed_id: XeedId, as_of: datetime
    ) -> None:
        if self.continuity is not None:
            self.continuity.record(authorized_context, xeed_id, as_of=as_of)

    def _read_context(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
    ) -> AuthorizedXeedOrganization:
        authorized_xeed = self.authorized_xeeds.read(authorized_context, xeed_id)
        return self.organization_reader.read(authorized_xeed)

    def observation_seed(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        *,
        as_of: datetime,
    ) -> tuple[AuthorizedXeedOrganization, tuple[tuple[GovernedObservation, Currentness], ...]]:
        """Authorize one Focus and expose only reusable public history for plan construction."""

        authorized = self._read_context(authorized_context, xeed_id)
        xeed = authorized.authorized_xeed.xeed
        history = _authorized_public_history(
            memory=self.observation_memory,
            organization_id=authorized.organization.id,
            xeed_id=xeed.id,
            tenant_id=xeed.tenant_id,
            as_of=as_of,
            reuse_policy=self.reuse_policy,
            temporal_policy=self.temporal_policy,
        )
        return authorized, self._content_reusable_history(history)

    def _content_reusable_history(
        self, history: tuple[tuple[GovernedObservation, Currentness], ...]
    ) -> tuple[tuple[GovernedObservation, Currentness], ...]:
        return content_reusable_history(history, self.content_rights)

    def deliver_content(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        projection: dict[str, object],
    ) -> dict[str, object]:
        authorized = self._read_context(authorized_context, xeed_id)
        organization_id = authorized.organization.id
        economic = projection.get("economicOutput")
        subjects = [organization_id]
        if isinstance(economic, dict) and isinstance(economic.get("activity_subject_ref"), str):
            subjects.append(economic["activity_subject_ref"])

        def metadata_for(identifier: str) -> ObservationAccessMetadata | None:
            # Lookup metadata only after membership; rejected raw content is never loaded.
            lookup = getattr(self.observation_memory, "access_metadata", None)
            if callable(lookup):
                for subject in subjects:
                    metadata = lookup(subject, identifier)
                    if isinstance(metadata, ObservationAccessMetadata):
                        return metadata
                return None
            for subject in subjects:
                for observation in self.observation_memory.for_subject(subject):
                    if observation.record.observation_id == identifier:
                        return ObservationAccessMetadata(
                            observation.record, observation.reuse_authority
                        )
            return None

        def metadata_for_source(source: str) -> tuple[ObservationAccessMetadata, ...]:
            lookup = getattr(self.observation_memory, "access_metadata_for_source", None)
            if callable(lookup):
                return tuple(
                    metadata for subject in subjects for metadata in lookup(subject, source)
                )
            return tuple(
                ObservationAccessMetadata(item.record, item.reuse_authority)
                for subject in subjects
                for item in self.observation_memory.for_subject(subject)
                if item.record.source_ref == source
            )

        return deliver_evidence_content(
            projection,
            metadata_for=metadata_for,
            metadata_for_source=metadata_for_source,
            rights=self.content_rights,
        )

    def publish(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        result: FirstEconomicVerticalE2EResult,
        *,
        execution_trace: dict[str, object] | None = None,
    ) -> bool:
        """Persist a real completed EB-04 output after reauthorizing its subject."""

        if not isinstance(result, FirstEconomicVerticalE2EResult):
            raise TypeError("subscriber runtime publication requires a real EB-04 result")
        organization_context = self._read_context(authorized_context, xeed_id)
        output = result.human_output
        if output.result.candidate.subject.state.subject_id != organization_context.organization.id:
            raise SubscriberEconomicStoreError(
                "economic output subject differs from authorized Organization"
            )
        output_wire = output.to_wire()
        output_as_of = result.reasoning.vector.evaluated_at
        if output_wire.get("as_of") != _iso(output_as_of):
            raise SubscriberEconomicStoreError(
                "economic output timestamp does not match EB-04 result"
            )
        signal = economic_output_runtime_signal(output)
        if execution_trace is not None:
            signal["executionTrace"] = deepcopy(execution_trace)
        appended = self.output_store.append(
            StoredEconomicOutput(
                tenant_id=organization_context.authorized_xeed.xeed.tenant_id,
                xeed_id=organization_context.authorized_xeed.xeed.id,
                organization_id=organization_context.organization.id,
                output_id=output.output_id,
                as_of=output_as_of,
                output_wire=output_wire,
                runtime_signal=signal,
            )
        )
        if appended:
            self._checkpoint(authorized_context, xeed_id, output_as_of)
        return appended

    def publish_observation_loop(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        *,
        observation_context: XeedObservationContext,
        strategy: ObservationStrategy,
        result: LoopResult,
        coverage: EvidenceCoverageMap,
        registry: SourceRegistry | None = None,
        drivers: tuple[DriverEvent, ...] = (),
    ) -> bool:
        """Persist a real opportunity-loop result after exact-scope authorization."""
        authorized = self._read_context(authorized_context, xeed_id)
        output_as_of = max(
            (
                observation_context.as_of,
                *(candidate.observed_at for candidate in result.candidates),
            )
        )
        xeed = authorized.authorized_xeed.xeed
        observations = _authorized_public_history(
            memory=self.observation_memory,
            organization_id=authorized.organization.id,
            xeed_id=xeed.id,
            tenant_id=xeed.tenant_id,
            as_of=output_as_of,
            reuse_policy=self.reuse_policy,
            temporal_policy=self.temporal_policy,
        )
        projection = project_observation_opportunities(
            authorized_context=authorized,
            context=observation_context,
            strategy=strategy,
            result=result,
            coverage=coverage,
            observations=self._content_reusable_history(observations),
            registry=registry,
            drivers=drivers,
            semantic_screen=self.semantic_screen,
        )
        if projection is None:
            return False
        appended = self.opportunity_store.append(projection)
        if appended:
            self._checkpoint(authorized_context, xeed_id, projection.as_of)
        return appended

    def execute_observation_loop(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        *,
        observation_context: XeedObservationContext,
        strategy: ObservationStrategy,
        adapters: Mapping[str, SourceObservationPort],
        coverage: EvidenceCoverageMap,
        learning: OperationalLearning,
        registry: SourceRegistry | None = None,
        drivers: tuple[DriverEvent, ...] = (),
    ) -> LoopResult:
        """Authorize and validate the observation seed before dispatching adapters."""
        authorized = self._read_context(authorized_context, xeed_id)
        xeed = authorized.authorized_xeed.xeed
        organization = authorized.organization
        if (
            observation_context.xeed_id != xeed.id
            or strategy.xeed_id != xeed.id
            or strategy.as_of != observation_context.as_of
            or organization.id != xeed.organization_id
        ):
            raise SubscriberOpportunityProjectionError(
                "observation seed must match the authorized Observation Focus and Organization"
            )

        seed_history = _authorized_public_history(
            memory=self.observation_memory,
            organization_id=organization.id,
            xeed_id=xeed.id,
            tenant_id=xeed.tenant_id,
            as_of=observation_context.as_of,
            reuse_policy=self.reuse_policy,
            temporal_policy=self.temporal_policy,
        )
        seed_history = self._content_reusable_history(seed_history)
        admitted_evidence = {
            (item.record.observation_id, item.record.source_ref, item.record.observed_at): item
            for item, _currentness in seed_history
            if item.record.subject_id == organization.id
        }
        if any(
            not capability.basis
            or any(
                (
                    observation := admitted_evidence.get(
                        (basis.observation_id, basis.source_ref, basis.observed_at)
                    )
                )
                is None
                or observation.raw_content is None
                or basis.excerpt not in observation.raw_content
                for basis in capability.basis
            )
            for capability in observation_context.capabilities
        ):
            raise SubscriberOpportunityProjectionError(
                "observation capabilities require evidence admitted for this Organization"
            )

        resolved_registry = registry or SourceRegistry()
        capability_ids = {item.capability_id for item in observation_context.capabilities}
        market_scopes = observation_context.markets
        for action in strategy.actions:
            if (
                action.capability_id is not None and action.capability_id not in capability_ids
            ) or not any(
                action.market.within(market.geography) and MarketRole.PUBLIC_BUYERS in market.roles
                for market in market_scopes
            ):
                raise SubscriberOpportunityProjectionError(
                    "observation strategy action falls outside the authorized seed"
                )
            try:
                source = resolved_registry.get(action.source_id)
            except KeyError as error:
                raise SubscriberOpportunityProjectionError(
                    "observation strategy references an unregistered source"
                ) from error
            if (
                not source.routable
                or not source.covers(action.market)
                or not action.query.capabilities <= source.capabilities
            ):
                raise SubscriberOpportunityProjectionError(
                    "observation strategy source is not adopted for the target jurisdiction"
                )

        result = run_observation_loop(
            strategy,
            observation_context,
            adapters=adapters,
            coverage=coverage,
            learning=learning,
            registry=resolved_registry,
        )
        self.publish_observation_loop(
            authorized_context,
            xeed_id,
            observation_context=observation_context,
            strategy=strategy,
            result=result,
            coverage=coverage,
            registry=resolved_registry,
            drivers=drivers,
        )
        return result

    def execute(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        plan: SubscriberEconomicExecutionPlan | None,
    ) -> SubscriberExecutionOutcome:
        """Run server-authorized EB-04 inputs, checkpoint, and read back the result."""
        organization_context = self._read_context(authorized_context, xeed_id)
        xeed = organization_context.authorized_xeed.xeed
        organization = organization_context.organization
        if plan is None:
            return SubscriberExecutionOutcome(
                "NOT_READY",
                reason="No server-authorized economic execution plan is configured for this Organization.",
                dri_measurement_attempt=_dri_not_measured(
                    "EXECUTION_PLAN_UNAVAILABLE",
                    "No page observation was dispatched because required server-owned execution inputs are unavailable.",
                ),
            )
        if plan.market_map.xeed_id != xeed.id:
            raise ValueError("market map does not belong to the authorized Observation Focus")
        if plan.subject_plan.authorization.request.subject_id != organization.id:
            raise ValueError("subject source plan does not target the canonical Organization")
        if plan.subject_plan.authorization.purpose is not ReusePurpose.HISTORICAL_REFERENCE:
            raise ValueError("subscriber EB-04 requires source authorization for historical reuse")
        directives = plan_market_observation(plan.market_map)
        routing = route_market_activity_plan(
            market_map=plan.market_map,
            catalogue=plan.market_catalogue,
            selected_relationship=plan.selected_relationship,
        )
        if routing.descriptor is None:
            return SubscriberExecutionOutcome(
                "INSUFFICIENT_EVIDENCE" if routing.directive is None else "NOT_READY",
                reason=";".join(routing.rejected),
                market_targets=tuple(item.relationship.value for item in directives),
                dri_measurement_attempt=_dri_not_measured(
                    "MARKET_ROUTE_UNAVAILABLE",
                    "No page observation was dispatched because there is no uniquely authorized market plan.",
                ),
            )
        activity_plan = routing.descriptor.plan
        if activity_plan.authorization.purpose is not ReusePurpose.HISTORICAL_REFERENCE:
            raise ValueError(
                "subscriber EB-04 activity source requires historical reuse authorization"
            )

        for source_plan in (plan.subject_plan, activity_plan):
            authority = source_plan.authorization.reuse_authority
            if (
                authority.rights_status is not ObservationRightsStatus.PERMITTED
                or authority.scope is not ObservationReuseScope.GLOBAL_PUBLIC
                or authority.provenance_ref is None
                or authority.access_status is not ObservationAccessStatus.ACCESSIBLE
                or ReusePurpose.HISTORICAL_REFERENCE.value not in authority.applicable_purposes
            ):
                raise ValueError(
                    "subscriber EB-04 requires permitted public evidence and reuse authority"
                )

        try:
            result = run_first_economic_vertical_e2e(
                subject_plan=plan.subject_plan,
                activity_plan=activity_plan,
                source_acquirer=plan.source_acquirer,
                representation_port=plan.representation_port,
                semantic_extractor=plan.semantic_extractor,
                binding_port=plan.binding_port,
                evaluator=plan.evaluator,
                execution_controller=plan.execution_controller,
                as_of=plan.as_of,
                dispatch_costs=plan.dispatch_costs,
            )
        except ExecutionReservationRejected as exc:
            reason = exc.decision.stop_reason.value if exc.decision.stop_reason else "UNKNOWN"
            event = execution_stop_learning_event(
                event_id=(
                    f"learning:subscriber-preflight:{xeed.id}:"
                    f"{plan.market_map.state_fingerprint}:{plan.as_of.isoformat()}:"
                    f"{plan.execution_controller.policy.fingerprint[:16]}:{reason}"
                ),
                occurred_at=plan.as_of,
                subject_id=organization.id,
                xeed_id=xeed.id,
                activity_ref=plan.market_map.state_fingerprint,
                code_sha=self.code_sha,
                kind=LearningEventKind.ADAPTIVE_RESEARCH,
                mechanism=LearningMechanism.GOVERNANCE,
                policy=plan.execution_controller.policy,
                state=plan.execution_controller.state,
                decision=exc.decision,
            )
            plan.learning_memory.append(event)
            if (
                exc.decision.stop_reason is not None
                and exc.decision.stop_reason.value == "COST_UNKNOWN"
            ):
                return SubscriberExecutionOutcome(
                    "BLOCKED_COST_UNKNOWN",
                    reason="Execution cost is not fully bounded; no source, extractor, or evaluator dispatch was started.",
                    dri_measurement_attempt=_dri_not_measured(
                        "COST_PREFLIGHT_BLOCKED",
                        "The complete monetary fan-out was not bounded; no public page measurement ran.",
                    ),
                )
            return SubscriberExecutionOutcome(
                "BLOCKED_BUDGET",
                reason=f"Execution budget preflight rejected the full fan-out: {exc.decision.stop_reason}.",
                dri_measurement_attempt=_dri_not_measured(
                    "BUDGET_PREFLIGHT_BLOCKED",
                    "The complete monetary fan-out exceeded the authorized budget; no public page measurement ran.",
                ),
            )
        except SourceMaterializationNotMeasured as exc:
            reason = (
                "The requested page was inaccessible under the authorized acquisition attempt."
                if exc.reason_code == "SOURCE_ACQUISITION_FAILED"
                else "The acquired page could not produce an informative authorized representation."
            )
            return SubscriberExecutionOutcome(
                "PARTIAL",
                reason=reason,
                market_targets=tuple(item.relationship.value for item in directives),
                dri_measurement_attempt=_dri_not_measured(
                    exc.reason_code,
                    reason,
                    detail_code=exc.detail_code,
                    sample_attempt={
                        "planned": 1,
                        "acquired": 0 if exc.reason_code == "SOURCE_ACQUISITION_FAILED" else 1,
                        "informative": 0,
                        "resultState": (
                            "INACCESSIBLE"
                            if exc.reason_code == "SOURCE_ACQUISITION_FAILED"
                            else "NON_INFORMATIVE"
                        ),
                    },
                ),
            )
        self._persist_run_observations(result)
        execution_trace: dict[str, object] = {
            "pipelineVersion": result.pipeline_version,
            "epistemicPolicyVersion": result.epistemic_policy_version,
            "budget": {
                "policyId": plan.execution_controller.policy.policy_id,
                "policyVersion": plan.execution_controller.policy.version,
                "amountMicrounits": result.execution_state.amount_microunits,
                "currency": result.execution_state.currency,
                "costComplete": result.execution_state.cost_complete,
                "requests": result.execution_state.requests,
                "sources": result.execution_state.sources,
            },
            "dispatchCostBasis": {
                "source": {
                    "amountMicrounits": plan.dispatch_costs.source.amount_microunits,
                    "currency": plan.dispatch_costs.source.currency,
                    "basisRef": plan.dispatch_costs.source.basis_ref,
                    "basisVersion": plan.dispatch_costs.source.basis_version,
                },
                "semanticExtraction": {
                    "amountMicrounits": plan.dispatch_costs.semantic_extraction.amount_microunits,
                    "currency": plan.dispatch_costs.semantic_extraction.currency,
                    "basisRef": plan.dispatch_costs.semantic_extraction.basis_ref,
                    "basisVersion": plan.dispatch_costs.semantic_extraction.basis_version,
                },
                "evaluator": {
                    "amountMicrounits": plan.dispatch_costs.evaluator.amount_microunits,
                    "currency": plan.dispatch_costs.evaluator.currency,
                    "basisRef": plan.dispatch_costs.evaluator.basis_ref,
                    "basisVersion": plan.dispatch_costs.evaluator.basis_version,
                },
            },
            "attempts": [
                {
                    "kind": attempt.attempt_kind,
                    "reservationId": attempt.reservation_id,
                    "succeeded": attempt.succeeded,
                    "requests": attempt.requests,
                    "sources": attempt.sources,
                    "costMicrounits": attempt.amount_microunits,
                    "currency": attempt.currency,
                }
                for attempt in result.attempts
            ],
            "replayRefs": list(result.replay_refs),
            "marketMap": {
                "stateFingerprint": plan.market_map.state_fingerprint,
                "classifiedAt": _iso(plan.market_map.classified_at),
                "directives": [
                    {
                        "relationship": item.relationship.value,
                        "participationState": item.participation_state.value,
                        "researchIntent": item.research_intent.value,
                        "objectTypes": [value.value for value in item.object_types],
                        "semanticQuestions": list(item.semantic_questions),
                    }
                    for item in directives
                ],
            },
            "marketPlanRouting": {
                "selectedDescriptorId": routing.descriptor.descriptor_id,
                "selectedDescriptorVersion": routing.descriptor.version,
                "selectedRelationship": routing.descriptor.relationship.value,
                "selectedParticipationState": routing.descriptor.participation_state.value,
                "selectedObjectType": routing.descriptor.object_type.value,
                "rejectedRationales": list(routing.rejected),
            },
            "driMeasurement": measure_public_page_representation(
                source=result.subject_source,
                organization=organization,
            ).to_wire(),
        }
        self.publish(authorized_context, xeed_id, result, execution_trace=execution_trace)
        read = self.read(authorized_context, xeed_id, plan.as_of)
        return SubscriberExecutionOutcome(
            "COMPLETED" if read.status is SubscriberRuntimeStatus.SUCCESS else "PARTIAL",
            read=read,
            reason=read.reason,
            market_targets=tuple(item.relationship.value for item in directives),
        )

    def _persist_run_observations(self, result: FirstEconomicVerticalE2EResult) -> None:
        """Materialize exact extracted public excerpts into the existing shared memory."""
        for source in (result.subject_source, result.activity_source):
            candidates_by_id: dict[str, list[EconomicClaimCandidate]] = {}
            for candidate in source.candidates.candidates:
                candidates_by_id.setdefault(candidate.observation_id, []).append(candidate)
            fields_by_id: dict[str, list[ObservedField]] = {}
            for observation in source.state.observations:
                fields_by_id.setdefault(str(observation.datum.observation_id), []).append(
                    ObservedField(observation.datum.name, observation.datum.value)
                )
            for observation_id, candidates in candidates_by_id.items():
                first = candidates[0]
                record = ObservationRecord(
                    observation_id=observation_id,
                    subject_id=source.authorization.request.subject_id,
                    source_ref=first.source_ref,
                    source_type=first.source_type,
                    observed_at=first.observed_at,
                    content_fingerprint=first.supporting_representation.document_fingerprint,
                    mode=ObservationMode.ACTIVE_RESEARCH,
                )
                raw_content = "\n".join(dict.fromkeys(item.excerpt for item in candidates))
                if not raw_content:
                    continue
                self.observation_memory.append(
                    GovernedObservation(
                        record=record,
                        raw_content=raw_content,
                        fields=tuple(fields_by_id.get(observation_id, ())),
                        reuse_authority=source.authorization.reuse_authority,
                    )
                )

    def read(
        self,
        authorized_context: TrustedRequestContext,
        xeed_id: XeedId,
        as_of: datetime,
    ) -> SubscriberRuntimeRead:
        """Reauthorize, load real history/output, and refresh evidence currentness."""

        if as_of.tzinfo is None:
            raise ValueError("subscriber runtime as_of must be timezone-aware")
        organization_context = self._read_context(authorized_context, xeed_id)
        authorized_xeed = organization_context.authorized_xeed.xeed
        organization = organization_context.organization

        public_history = _authorized_public_history(
            memory=self.observation_memory,
            organization_id=organization.id,
            xeed_id=authorized_xeed.id,
            tenant_id=authorized_xeed.tenant_id,
            as_of=as_of,
            reuse_policy=self.reuse_policy,
            temporal_policy=self.temporal_policy,
        )
        projection = _base_projection(
            organization=organization,
            xeed=authorized_xeed,
            code_sha=self.code_sha,
        )
        projection["temporalHistory"] = _temporal_history(public_history)

        stored_opportunities = self.opportunity_store.latest(
            tenant_id=authorized_xeed.tenant_id,
            xeed_id=authorized_xeed.id,
            organization_id=organization.id,
            as_of=as_of,
        )
        projection["cognition"] = _merge_opportunity_cognition(
            base=observation_cognition(public_history, as_of=as_of),
            stored=stored_opportunities,
            as_of=as_of,
            policy=self.temporal_policy,
        )

        stored = self.output_store.latest(
            tenant_id=authorized_xeed.tenant_id,
            xeed_id=authorized_xeed.id,
            organization_id=organization.id,
            as_of=as_of,
        )
        if stored is None:
            cognition = projection.get("cognition")
            opportunities = cognition.get("opportunities") if isinstance(cognition, dict) else None
            if isinstance(opportunities, list) and opportunities:
                return SubscriberRuntimeRead(
                    SubscriberRuntimeStatus.SUCCESS,
                    self.deliver_content(authorized_context, xeed_id, projection),
                )
            return SubscriberRuntimeRead(
                SubscriberRuntimeStatus.INSUFFICIENT_EVIDENCE,
                self.deliver_content(authorized_context, xeed_id, projection),
                "No persisted evidence-backed economic output is available for this Organization and time.",
            )

        currentness = _output_evidence_currentness(
            output=stored,
            memory=self.observation_memory,
            xeed_id=authorized_xeed.id,
            tenant_id=authorized_xeed.tenant_id,
            as_of=as_of,
            reuse_policy=self.reuse_policy,
            temporal_policy=self.temporal_policy,
        )
        signal, wire, is_current = _refresh_signal(stored, currentness)
        nodes = projection["nodes"]
        assert isinstance(nodes, list)
        nodes.append(signal)
        projection["memberships"] = [
            {
                "from": authorized_xeed.id,
                "to": signal["id"],
                "meaning": "Observation Focus observes Signal",
            }
        ]
        projection["economicOutput"] = wire
        execution_trace = signal.get("executionTrace")
        if isinstance(execution_trace, dict):
            measurement = execution_trace.get("driMeasurement")
            if isinstance(measurement, dict):
                measurement = dict(measurement)
                representation = measurement.get("representation")
                representation_ref = (
                    representation.get("ref") if isinstance(representation, dict) else None
                )
                observed_at = measurement.get("observedAt")
                try:
                    if not isinstance(representation_ref, str) or not isinstance(observed_at, str):
                        raise ValueError("DRI snapshot is missing temporal identity")
                    previous = Currentness(str(measurement.get("currentness")))
                    page_currentness = evaluate_effective_currentness(
                        observation_id=representation_ref,
                        observed_at=datetime.fromisoformat(observed_at),
                        previous=previous,
                        as_of=as_of,
                        policy=self.temporal_policy,
                    )
                except (TypeError, ValueError):
                    measurement["currentness"] = Currentness.UNKNOWN.value
                    measurement["currentnessEvaluation"] = {
                        "state": Currentness.UNKNOWN.value,
                        "reason": "Measurement temporal basis is unavailable or invalid.",
                    }
                else:
                    measurement["currentness"] = page_currentness.current.value
                    measurement["currentnessEvaluation"] = {
                        "previous": page_currentness.previous.value,
                        "asOf": _iso(page_currentness.as_of),
                        "policyRef": (
                            f"{page_currentness.policy_id}@{page_currentness.policy_version}"
                        ),
                    }
                instrument = measurement.get("instrument")
                recorded_ref = instrument.get("ref") if isinstance(instrument, dict) else None
                recorded_version = (
                    instrument.get("version") if isinstance(instrument, dict) else None
                )
                if recorded_ref != DRI_INSTRUMENT_REF or recorded_version != DRI_INSTRUMENT_VERSION:
                    compatibility = {
                        "state": "INSTRUMENT_VERSION_MISMATCH",
                        "expected": {
                            "ref": DRI_INSTRUMENT_REF,
                            "version": DRI_INSTRUMENT_VERSION,
                        },
                        "recorded": {"ref": recorded_ref, "version": recorded_version},
                    }
                    execution_trace["driMeasurementCompatibility"] = compatibility
                    projection["digitalRepresentation"] = {
                        "kind": "DRI_PUBLIC_PAGE_REPRESENTATION",
                        "state": "NOT_MEASURED",
                        "currentness": Currentness.UNKNOWN.value,
                        "reason": {
                            "code": "INSTRUMENT_VERSION_MISMATCH",
                            "explanation": "A newer page instrument is configured; the recorded measure is retained as historical evidence and is not compared or shown as current.",
                        },
                        "expectedInstrument": compatibility["expected"],
                        "recordedMeasurement": measurement,
                    }
                else:
                    projection["digitalRepresentation"] = measurement

        if is_current and signal.get("epistemicState") in {"POTENTIAL", "UNKNOWN"}:
            projection["today"] = {
                "disposition": "READY",
                "items": [
                    {
                        "xignalId": signal["id"],
                        "whatChanged": signal["title"],
                        "whyItMatters": signal["whyAttention"],
                        "observedAt": signal["observedAt"],
                        "showHowRef": signal["id"],
                    }
                ],
            }
        reason = (
            None
            if is_current
            else "Stored economic output is retained, but its supporting evidence is not current enough for a positive interpretation."
        )
        return SubscriberRuntimeRead(
            SubscriberRuntimeStatus.SUCCESS,
            self.deliver_content(authorized_context, xeed_id, projection),
            reason,
        )
