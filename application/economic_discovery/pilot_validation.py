"""FR-27 one-buyer / one-job pilot validation contract.

This module records product-validation evidence. It never mutates canonical truth and
never treats commercial outcomes or Xeed-private attention preferences as epistemic
validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.unit_economics import UnitEconomicsReport


class PilotEvidenceKind(StrEnum):
    DECISION_ADVANCEMENT = "DECISION_ADVANCEMENT"
    EVIDENCE_INSPECTION = "EVIDENCE_INSPECTION"
    EVIDENCE_TRUST_REPORT = "EVIDENCE_TRUST_REPORT"
    RETURN_BECAUSE_CHANGE = "RETURN_BECAUSE_CHANGE"
    WILLINGNESS_TO_PAY = "WILLINGNESS_TO_PAY"
    ADDITIONAL_XEED_VALUE = "ADDITIONAL_XEED_VALUE"


class PilotEvidenceSource(StrEnum):
    PRODUCT_TELEMETRY = "PRODUCT_TELEMETRY"
    DIRECT_USER_REPORT = "DIRECT_USER_REPORT"
    INTERVIEW_RECORD = "INTERVIEW_RECORD"
    OFFER_RESPONSE = "OFFER_RESPONSE"
    PAYMENT_RECORD = "PAYMENT_RECORD"


class PilotAnswer(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class PricingEvidenceKind(StrEnum):
    STATED_MAXIMUM = "STATED_MAXIMUM"
    ACCEPTED_OFFER = "ACCEPTED_OFFER"
    DECLINED_OFFER = "DECLINED_OFFER"
    PAID = "PAID"


class XeedAttentionPosture(StrEnum):
    """Private subscriber intent; never canonical organization state."""

    GROW_VISIBILITY = "GROW_VISIBILITY"
    MONITOR_VISIBILITY = "MONITOR_VISIBILITY"
    LOW_PROFILE = "LOW_PROFILE"
    UNKNOWN = "UNKNOWN"


class PilotObservabilityDisposition(StrEnum):
    PUBLICLY_OBSERVABLE = "PUBLICLY_OBSERVABLE"
    PARTIALLY_OBSERVABLE = "PARTIALLY_OBSERVABLE"
    PRIVATE_OR_NON_OBSERVABLE = "PRIVATE_OR_NON_OBSERVABLE"
    UNKNOWN = "UNKNOWN"


class PublicSurfaceObservation(StrEnum):
    PRESENCE_OBSERVED = "PRESENCE_OBSERVED"
    NO_PRESENCE_OBSERVED = "NO_PRESENCE_OBSERVED"
    NOT_OBSERVED = "NOT_OBSERVED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    OUTSIDE_PUBLIC_SCOPE = "OUTSIDE_PUBLIC_SCOPE"


class DiscoveryEvaluability(StrEnum):
    EVALUABLE = "EVALUABLE"
    PARTIALLY_EVALUABLE = "PARTIALLY_EVALUABLE"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    UNKNOWN = "UNKNOWN"


class PresenceRelevance(StrEnum):
    VISIBILITY_GAP_CANDIDATE = "VISIBILITY_GAP_CANDIDATE"
    PUBLIC_PRESENCE_OBSERVED = "PUBLIC_PRESENCE_OBSERVED"
    LOW_EXPOSURE_OBSERVED = "LOW_EXPOSURE_OBSERVED"
    UNEXPECTED_EXPOSURE_CANDIDATE = "UNEXPECTED_EXPOSURE_CANDIDATE"
    MONITORING_BASELINE = "MONITORING_BASELINE"
    INSUFFICIENT_OBSERVATION = "INSUFFICIENT_OBSERVATION"


@dataclass(frozen=True, slots=True)
class PilotHypothesis:
    pilot_id: str
    buyer_archetype: str
    job_to_be_done: str
    primary_xeed_id: str
    currency: str
    base_price_microunits: int
    additional_xeed_price_microunits: int

    def __post_init__(self) -> None:
        for value in (
            self.pilot_id,
            self.buyer_archetype,
            self.job_to_be_done,
            self.primary_xeed_id,
        ):
            if not value.strip():
                raise ValueError("pilot hypothesis identity and job are required")
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("pilot currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        if self.base_price_microunits < 0 or self.additional_xeed_price_microunits < 0:
            raise ValueError("pilot pricing hypothesis cannot be negative")


FR27_AGENCY_CHANGE_PILOT = PilotHypothesis(
    pilot_id="fr27-agency-external-change-v1",
    buyer_archetype="SEO/GEO/AEO agency responsible for an active client portfolio",
    job_to_be_done=(
        "Detect a material externally observable change around one client, understand "
        "why it warrants attention, inspect the evidence, and decide whether further "
        "agency action or investigation is justified."
    ),
    primary_xeed_id="pilot:xeed:client-1",
    currency="EUR",
    base_price_microunits=9_950_000,
    additional_xeed_price_microunits=4_950_000,
)


@dataclass(frozen=True, slots=True)
class SurfaceObservation:
    surface_id: str
    result: PublicSurfaceObservation
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.surface_id.strip():
            raise ValueError("surface observation requires surface id")
        if self.evidence_ref is not None and not self.evidence_ref.strip():
            raise ValueError("surface observation evidence ref cannot be empty")
        if (
            self.result
            in {
                PublicSurfaceObservation.PRESENCE_OBSERVED,
                PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            }
            and self.evidence_ref is None
        ):
            raise ValueError("an observed surface result requires evidence provenance")
        if (
            self.result is PublicSurfaceObservation.OUTSIDE_PUBLIC_SCOPE
            and self.evidence_ref is not None
        ):
            raise ValueError("outside-public-scope surfaces do not carry public evidence")


@dataclass(frozen=True, slots=True)
class PilotObservabilityAssessment:
    assessment_id: str
    pilot_id: str
    xeed_id: str
    assessed_at: datetime
    disposition: PilotObservabilityDisposition
    attention_posture: XeedAttentionPosture
    surfaces: tuple[SurfaceObservation, ...]
    private_context_declared: bool = False
    assessment_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.assessment_id.strip() or not self.pilot_id.strip() or not self.xeed_id.strip():
            raise ValueError(
                "observability assessment requires assessment, pilot and Xeed identity"
            )
        if self.assessed_at.tzinfo is None:
            raise ValueError("observability assessment time must be timezone-aware")
        if self.assessment_ref is not None and not self.assessment_ref.strip():
            raise ValueError("observability assessment ref cannot be empty")
        surface_ids = [item.surface_id for item in self.surfaces]
        if len(surface_ids) != len(set(surface_ids)):
            raise ValueError("observability assessment requires unique surface ids")
        if self.disposition is PilotObservabilityDisposition.PUBLICLY_OBSERVABLE and not any(
            item.result
            in {
                PublicSurfaceObservation.PRESENCE_OBSERVED,
                PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            }
            for item in self.surfaces
        ):
            raise ValueError(
                "publicly observable pilot requires at least one observed public surface"
            )
        if self.disposition is PilotObservabilityDisposition.PRIVATE_OR_NON_OBSERVABLE and any(
            item.result
            in {
                PublicSurfaceObservation.PRESENCE_OBSERVED,
                PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            }
            for item in self.surfaces
        ):
            raise ValueError(
                "private/non-observable disposition cannot contain observed public surfaces"
            )

    @property
    def observed_surface_count(self) -> int:
        return sum(
            item.result
            in {
                PublicSurfaceObservation.PRESENCE_OBSERVED,
                PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            }
            for item in self.surfaces
        )

    @property
    def observed_presence_count(self) -> int:
        return sum(
            item.result is PublicSurfaceObservation.PRESENCE_OBSERVED for item in self.surfaces
        )

    @property
    def observed_no_presence_count(self) -> int:
        return sum(
            item.result is PublicSurfaceObservation.NO_PRESENCE_OBSERVED for item in self.surfaces
        )

    @property
    def discovery_evaluability(self) -> DiscoveryEvaluability:
        if self.disposition is PilotObservabilityDisposition.PUBLICLY_OBSERVABLE:
            return DiscoveryEvaluability.EVALUABLE
        if self.disposition is PilotObservabilityDisposition.PARTIALLY_OBSERVABLE:
            return (
                DiscoveryEvaluability.PARTIALLY_EVALUABLE
                if self.observed_surface_count
                else DiscoveryEvaluability.UNKNOWN
            )
        if self.disposition is PilotObservabilityDisposition.PRIVATE_OR_NON_OBSERVABLE:
            return DiscoveryEvaluability.NOT_EVALUABLE
        return DiscoveryEvaluability.UNKNOWN


def project_presence_relevance(
    assessment: PilotObservabilityAssessment,
) -> PresenceRelevance:
    """Project Xeed-private relevance without changing the observed public state."""

    if assessment.discovery_evaluability in {
        DiscoveryEvaluability.NOT_EVALUABLE,
        DiscoveryEvaluability.UNKNOWN,
    }:
        return PresenceRelevance.INSUFFICIENT_OBSERVATION

    has_presence = assessment.observed_presence_count > 0
    has_absence = assessment.observed_no_presence_count > 0

    if assessment.attention_posture is XeedAttentionPosture.GROW_VISIBILITY:
        if has_absence:
            return PresenceRelevance.VISIBILITY_GAP_CANDIDATE
        if has_presence:
            return PresenceRelevance.PUBLIC_PRESENCE_OBSERVED
    elif assessment.attention_posture is XeedAttentionPosture.LOW_PROFILE:
        if has_presence:
            return PresenceRelevance.UNEXPECTED_EXPOSURE_CANDIDATE
        if has_absence:
            return PresenceRelevance.LOW_EXPOSURE_OBSERVED
    elif assessment.attention_posture is XeedAttentionPosture.MONITOR_VISIBILITY:
        if assessment.observed_surface_count:
            return PresenceRelevance.MONITORING_BASELINE

    return PresenceRelevance.INSUFFICIENT_OBSERVATION


@dataclass(frozen=True, slots=True)
class PilotEvidence:
    evidence_id: str
    pilot_id: str
    occurred_at: datetime
    kind: PilotEvidenceKind
    source: PilotEvidenceSource
    evidence_ref: str
    answer: PilotAnswer = PilotAnswer.UNKNOWN
    xeed_id: str | None = None
    xignal_id: str | None = None
    learning_event_id: str | None = None
    pricing_kind: PricingEvidenceKind | None = None
    amount_microunits: int | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        for value in (self.evidence_id, self.pilot_id, self.evidence_ref):
            if not value.strip():
                raise ValueError("pilot evidence identity and provenance are required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("pilot evidence time must be timezone-aware")
        for reference in (self.xeed_id, self.xignal_id, self.learning_event_id):
            if reference is not None and not reference.strip():
                raise ValueError("pilot evidence references cannot be empty")

        has_amount = self.amount_microunits is not None
        if has_amount != (self.currency is not None):
            raise ValueError("pilot monetary amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("pilot monetary amount cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("pilot evidence currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)

        if self.kind is PilotEvidenceKind.WILLINGNESS_TO_PAY:
            if self.source not in {
                PilotEvidenceSource.DIRECT_USER_REPORT,
                PilotEvidenceSource.INTERVIEW_RECORD,
                PilotEvidenceSource.OFFER_RESPONSE,
                PilotEvidenceSource.PAYMENT_RECORD,
            }:
                raise ValueError("usage telemetry cannot establish willingness to pay")
            if self.pricing_kind is None or self.amount_microunits is None:
                raise ValueError("willingness-to-pay evidence requires kind and amount")
        elif self.pricing_kind is not None or self.amount_microunits is not None:
            raise ValueError("only willingness-to-pay evidence may carry monetary fields")

        explicit_report_sources = {
            PilotEvidenceSource.DIRECT_USER_REPORT,
            PilotEvidenceSource.INTERVIEW_RECORD,
        }
        if (
            self.kind is PilotEvidenceKind.EVIDENCE_TRUST_REPORT
            and self.source not in explicit_report_sources
        ):
            raise ValueError("evidence trust requires explicit user report")
        if (
            self.kind is PilotEvidenceKind.RETURN_BECAUSE_CHANGE
            and self.source not in explicit_report_sources
        ):
            raise ValueError("return causality requires explicit user report")


class PilotEvidenceConflict(ValueError):
    """Raised when a stable pilot evidence id is reused with different content."""


class PilotEvidenceMemory(Protocol):
    def append(self, evidence: PilotEvidence) -> bool:
        """Persist once; False means exact idempotent replay."""

    def for_pilot(self, pilot_id: str) -> tuple[PilotEvidence, ...]:
        """Return chronological evidence for one pilot."""


@dataclass(frozen=True, slots=True)
class PilotEvidenceCoverage:
    decision_advancement: int
    evidence_inspection: int
    evidence_trust_report: int
    return_because_change: int
    willingness_to_pay: int
    additional_xeed_value: int

    @property
    def protocol_complete(self) -> bool:
        return all(
            value > 0
            for value in (
                self.decision_advancement,
                self.evidence_inspection,
                self.evidence_trust_report,
                self.return_because_change,
                self.willingness_to_pay,
                self.additional_xeed_value,
            )
        )


@dataclass(frozen=True, slots=True)
class PilotReport:
    hypothesis: PilotHypothesis
    observability: PilotObservabilityAssessment
    economics: UnitEconomicsReport
    evidence_ids: tuple[str, ...]
    coverage: PilotEvidenceCoverage
    negative_evidence_count: int
    unknown_evidence_count: int
    pricing_evidence: tuple[PilotEvidence, ...]
    additional_xeed_evidence: tuple[PilotEvidence, ...]


def summarize_pilot(
    *,
    hypothesis: PilotHypothesis,
    observability: PilotObservabilityAssessment,
    economics: UnitEconomicsReport,
    evidence: tuple[PilotEvidence, ...],
) -> PilotReport:
    """Summarize observed pilot evidence without manufacturing a product verdict."""

    if economics.xeed_id != hypothesis.primary_xeed_id:
        raise ValueError("pilot economics must belong to the pilot primary Xeed")
    if observability.pilot_id != hypothesis.pilot_id:
        raise ValueError("observability assessment belongs to a different pilot")
    if observability.xeed_id != hypothesis.primary_xeed_id:
        raise ValueError("observability assessment belongs to a different primary Xeed")

    seen: set[str] = set()
    ordered = tuple(sorted(evidence, key=lambda item: (item.occurred_at, item.evidence_id)))
    for item in ordered:
        if item.evidence_id in seen:
            raise ValueError("duplicate pilot evidence id")
        seen.add(item.evidence_id)
        if item.pilot_id != hypothesis.pilot_id:
            raise ValueError("pilot evidence belongs to a different pilot")
        if item.xeed_id is not None and item.xeed_id != hypothesis.primary_xeed_id:
            raise ValueError("pilot evidence references a different primary Xeed")
        if item.currency is not None and item.currency != hypothesis.currency:
            raise ValueError("pilot monetary evidence currency mismatch")

    counts = {kind: 0 for kind in PilotEvidenceKind}
    for item in ordered:
        counts[item.kind] += 1

    pricing = tuple(item for item in ordered if item.kind is PilotEvidenceKind.WILLINGNESS_TO_PAY)
    additional_xeed = tuple(
        item for item in ordered if item.kind is PilotEvidenceKind.ADDITIONAL_XEED_VALUE
    )

    return PilotReport(
        hypothesis=hypothesis,
        observability=observability,
        economics=economics,
        evidence_ids=tuple(item.evidence_id for item in ordered),
        coverage=PilotEvidenceCoverage(
            decision_advancement=counts[PilotEvidenceKind.DECISION_ADVANCEMENT],
            evidence_inspection=counts[PilotEvidenceKind.EVIDENCE_INSPECTION],
            evidence_trust_report=counts[PilotEvidenceKind.EVIDENCE_TRUST_REPORT],
            return_because_change=counts[PilotEvidenceKind.RETURN_BECAUSE_CHANGE],
            willingness_to_pay=counts[PilotEvidenceKind.WILLINGNESS_TO_PAY],
            additional_xeed_value=counts[PilotEvidenceKind.ADDITIONAL_XEED_VALUE],
        ),
        negative_evidence_count=sum(item.answer is PilotAnswer.NO for item in ordered),
        unknown_evidence_count=sum(item.answer is PilotAnswer.UNKNOWN for item in ordered),
        pricing_evidence=pricing,
        additional_xeed_evidence=additional_xeed,
    )
