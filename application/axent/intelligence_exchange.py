"""Evidence-loyal AXENT intelligence exchange contracts.

AXENT may converse, challenge, advise and elicit product-validation evidence.
It has no authority to mutate AXIGLAND, create canonical truth from user claims,
or reinterpret a subscriber assertion as economic evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.pilot_validation import (
    PilotAnswer,
    PilotEvidence,
    PilotEvidenceKind,
    PilotEvidenceSource,
    PilotObservabilityAssessment,
    PresenceRelevance,
    PricingEvidenceKind,
    project_presence_relevance,
)


class AxentExchangeKind(StrEnum):
    EVIDENCE_CONTRAST = "EVIDENCE_CONTRAST"
    NEXT_INVESTIGATION = "NEXT_INVESTIGATION"
    PRODUCT_VALIDATION = "PRODUCT_VALIDATION"


class AxentLever(StrEnum):
    SEO = "SEO"
    GEO = "GEO"
    CONTENT = "CONTENT"
    PUBLIC_RELATIONS = "PUBLIC_RELATIONS"
    PAID_MEDIA = "PAID_MEDIA"
    COMMUNICATION = "COMMUNICATION"
    INDEXATION = "INDEXATION"
    DISTRIBUTION = "DISTRIBUTION"
    MEASUREMENT_COVERAGE = "MEASUREMENT_COVERAGE"


class AxentPilotQuestionKind(StrEnum):
    DECISION_ADVANCEMENT = "DECISION_ADVANCEMENT"
    EVIDENCE_TRUST = "EVIDENCE_TRUST"
    RETURN_BECAUSE_CHANGE = "RETURN_BECAUSE_CHANGE"
    WILLINGNESS_TO_PAY = "WILLINGNESS_TO_PAY"
    ADDITIONAL_XEED_VALUE = "ADDITIONAL_XEED_VALUE"


@dataclass(frozen=True, slots=True)
class AxentUserStatement:
    """Private conversational input, explicitly non-authoritative for economic truth."""

    statement_id: str
    xeed_id: str
    occurred_at: datetime
    text: str

    def __post_init__(self) -> None:
        if not self.statement_id.strip() or not self.xeed_id.strip() or not self.text.strip():
            raise ValueError("AXENT user statement identity, Xeed and text are required")
        if self.occurred_at.tzinfo is None:
            raise ValueError("AXENT user statement time must be timezone-aware")

    @property
    def is_economic_evidence(self) -> bool:
        return False

    @property
    def grants_canonical_write(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class AxentIntelligenceReply:
    """Subscriber-facing intelligence grounded in existing governed observations."""

    reply_id: str
    xeed_id: str
    exchange_kind: AxentExchangeKind
    message: str
    observation_refs: tuple[str, ...]
    xignal_refs: tuple[str, ...] = ()
    suggested_levers: tuple[AxentLever, ...] = ()
    uncertainty: str = ""

    def __post_init__(self) -> None:
        if not self.reply_id.strip() or not self.xeed_id.strip() or not self.message.strip():
            raise ValueError("AXENT reply identity, Xeed and message are required")
        if self.exchange_kind is AxentExchangeKind.EVIDENCE_CONTRAST and not (
            self.observation_refs or self.xignal_refs
        ):
            raise ValueError("evidence contrast requires governed observation or Xignal refs")
        if len(set(self.observation_refs)) != len(self.observation_refs):
            raise ValueError("AXENT observation refs must be unique")
        if len(set(self.xignal_refs)) != len(self.xignal_refs):
            raise ValueError("AXENT Xignal refs must be unique")
        if self.suggested_levers and self.exchange_kind is AxentExchangeKind.PRODUCT_VALIDATION:
            raise ValueError("product-validation prompts cannot masquerade as business advice")

    @property
    def is_canonical_truth(self) -> bool:
        return False

    @property
    def can_write_axigland(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class AxentPilotQuestion:
    """A proactive question that must earn the interruption with a defined return."""

    question_id: str
    pilot_id: str
    xeed_id: str
    kind: AxentPilotQuestionKind
    prompt: str
    trigger_ref: str
    intelligence_return: str
    xignal_id: str | None = None
    pricing_kind: PricingEvidenceKind | None = None
    amount_microunits: int | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        for value in (
            self.question_id,
            self.pilot_id,
            self.xeed_id,
            self.prompt,
            self.trigger_ref,
            self.intelligence_return,
        ):
            if not value.strip():
                raise ValueError(
                    "AXENT proactive question requires trigger and intelligence return"
                )
        if self.xignal_id is not None and not self.xignal_id.strip():
            raise ValueError("AXENT pilot question Xignal ref cannot be empty")
        monetary = self.kind is AxentPilotQuestionKind.WILLINGNESS_TO_PAY
        if monetary != (self.pricing_kind is not None):
            raise ValueError("willingness-to-pay question requires pricing evidence kind")
        if monetary != (self.amount_microunits is not None):
            raise ValueError("willingness-to-pay question requires offered amount")
        if monetary != (self.currency is not None):
            raise ValueError("willingness-to-pay question requires currency")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("AXENT offered amount cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("AXENT pilot question currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)


def build_visibility_intelligence_reply(
    *,
    reply_id: str,
    assessment: PilotObservabilityAssessment,
) -> AxentIntelligenceReply:
    """Return evidence-loyal visibility intelligence without claiming a causal diagnosis."""

    relevance = project_presence_relevance(assessment)
    observed_refs = tuple(
        item.evidence_ref for item in assessment.surfaces if item.evidence_ref is not None
    )
    if relevance is PresenceRelevance.VISIBILITY_GAP_CANDIDATE:
        return AxentIntelligenceReply(
            reply_id=reply_id,
            xeed_id=assessment.xeed_id,
            exchange_kind=AxentExchangeKind.EVIDENCE_CONTRAST,
            message=(
                "The measured public surfaces show a visibility gap for the current "
                "growth objective. This does not prove that SEO, GEO or communication "
                "work is poor; it shows that the desired external presence is not yet "
                "observable on the measured surfaces. Review the suggested levers or "
                "investigate where the visibility chain is breaking."
            ),
            observation_refs=observed_refs,
            suggested_levers=(
                AxentLever.SEO,
                AxentLever.GEO,
                AxentLever.CONTENT,
                AxentLever.PUBLIC_RELATIONS,
                AxentLever.COMMUNICATION,
                AxentLever.INDEXATION,
                AxentLever.DISTRIBUTION,
            ),
            uncertainty=(
                "The observation is condition-bound to measured surfaces, queries, "
                "geographies and times; internal agency work and unmeasured surfaces remain unknown."
            ),
        )
    if relevance is PresenceRelevance.UNEXPECTED_EXPOSURE_CANDIDATE:
        return AxentIntelligenceReply(
            reply_id=reply_id,
            xeed_id=assessment.xeed_id,
            exchange_kind=AxentExchangeKind.EVIDENCE_CONTRAST,
            message=(
                "Public presence is observable on the measured surfaces despite the current "
                "low-profile objective. Review where that exposure originates before deciding "
                "whether any action is appropriate."
            ),
            observation_refs=observed_refs,
            suggested_levers=(AxentLever.MEASUREMENT_COVERAGE,),
            uncertainty="Observed exposure is not proof of harm or unwanted disclosure.",
        )
    return AxentIntelligenceReply(
        reply_id=reply_id,
        xeed_id=assessment.xeed_id,
        exchange_kind=AxentExchangeKind.NEXT_INVESTIGATION,
        message=(
            "The current observations do not justify a stronger visibility diagnosis. "
            "Keep the measured state separate from assumptions and expand observation only where useful."
        ),
        observation_refs=observed_refs,
        suggested_levers=(AxentLever.MEASUREMENT_COVERAGE,),
        uncertainty="Insufficient or non-material observation must remain explicit.",
    )


_QUESTION_TO_EVIDENCE = {
    AxentPilotQuestionKind.DECISION_ADVANCEMENT: PilotEvidenceKind.DECISION_ADVANCEMENT,
    AxentPilotQuestionKind.EVIDENCE_TRUST: PilotEvidenceKind.EVIDENCE_TRUST_REPORT,
    AxentPilotQuestionKind.RETURN_BECAUSE_CHANGE: PilotEvidenceKind.RETURN_BECAUSE_CHANGE,
    AxentPilotQuestionKind.WILLINGNESS_TO_PAY: PilotEvidenceKind.WILLINGNESS_TO_PAY,
    AxentPilotQuestionKind.ADDITIONAL_XEED_VALUE: PilotEvidenceKind.ADDITIONAL_XEED_VALUE,
}


def capture_axent_pilot_answer(
    *,
    question: AxentPilotQuestion,
    answer: PilotAnswer,
    occurred_at: datetime,
    response_ref: str,
) -> PilotEvidence:
    """Convert an explicit human answer into FR-27 product evidence, never economic truth."""

    if occurred_at.tzinfo is None:
        raise ValueError("AXENT pilot answer time must be timezone-aware")
    if not response_ref.strip():
        raise ValueError("AXENT pilot answer requires response provenance")
    return PilotEvidence(
        evidence_id=f"axent:{question.question_id}:answer",
        pilot_id=question.pilot_id,
        occurred_at=occurred_at,
        kind=_QUESTION_TO_EVIDENCE[question.kind],
        source=(
            PilotEvidenceSource.OFFER_RESPONSE
            if question.kind is AxentPilotQuestionKind.WILLINGNESS_TO_PAY
            else PilotEvidenceSource.DIRECT_USER_REPORT
        ),
        evidence_ref=response_ref,
        answer=answer,
        xeed_id=question.xeed_id,
        xignal_id=question.xignal_id,
        pricing_kind=question.pricing_kind,
        amount_microunits=question.amount_microunits,
        currency=question.currency,
    )
