from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.axent import (
    AxentExchangeKind,
    AxentLever,
    AxentPilotQuestion,
    AxentPilotQuestionKind,
    AxentUserStatement,
    build_visibility_intelligence_reply,
    capture_axent_pilot_answer,
)
from application.economic_discovery.pilot_validation import (
    PilotAnswer,
    PilotEvidenceKind,
    PilotEvidenceSource,
    PilotObservabilityAssessment,
    PilotObservabilityDisposition,
    PricingEvidenceKind,
    PublicSurfaceObservation,
    SurfaceObservation,
    XeedAttentionPosture,
)

NOW = datetime(2026, 10, 1, 10, 30, tzinfo=UTC)


def _assessment(*, posture: XeedAttentionPosture) -> PilotObservabilityAssessment:
    return PilotObservabilityAssessment(
        assessment_id="assessment:1",
        pilot_id="pilot:1",
        xeed_id="xeed:1",
        assessed_at=NOW,
        disposition=PilotObservabilityDisposition.PUBLICLY_OBSERVABLE,
        attention_posture=posture,
        surfaces=(
            SurfaceObservation(
                surface_id="search:es:industrial-plastics",
                result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
                evidence_ref="observation:search:1",
            ),
        ),
        assessment_ref="assessment-ref:1",
    )


def test_user_statement_is_never_economic_evidence_or_canonical_authority() -> None:
    statement = AxentUserStatement(
        statement_id="statement:1",
        xeed_id="xeed:1",
        occurred_at=NOW,
        text="Our SEO is excellent and our agency says everything is working.",
    )

    assert statement.is_economic_evidence is False
    assert statement.grants_canonical_write is False


def test_visibility_gap_returns_evidence_loyal_advice_not_causal_claim() -> None:
    reply = build_visibility_intelligence_reply(
        reply_id="reply:1",
        assessment=_assessment(posture=XeedAttentionPosture.GROW_VISIBILITY),
    )

    assert reply.exchange_kind is AxentExchangeKind.EVIDENCE_CONTRAST
    assert reply.observation_refs == ("observation:search:1",)
    assert AxentLever.SEO in reply.suggested_levers
    assert AxentLever.GEO in reply.suggested_levers
    assert "does not prove" in reply.message
    assert reply.is_canonical_truth is False
    assert reply.can_write_axigland is False


def test_same_measured_absence_does_not_prescribe_growth_levers_for_low_profile() -> None:
    reply = build_visibility_intelligence_reply(
        reply_id="reply:2",
        assessment=_assessment(posture=XeedAttentionPosture.LOW_PROFILE),
    )

    assert AxentLever.SEO not in reply.suggested_levers
    assert AxentLever.GEO not in reply.suggested_levers
    assert reply.can_write_axigland is False


def test_proactive_question_requires_trigger_and_promised_intelligence_return() -> None:
    with pytest.raises(ValueError, match="trigger and intelligence return"):
        AxentPilotQuestion(
            question_id="question:1",
            pilot_id="pilot:1",
            xeed_id="xeed:1",
            kind=AxentPilotQuestionKind.DECISION_ADVANCEMENT,
            prompt="Did this help you decide what to do next?",
            trigger_ref="",
            intelligence_return="I can investigate the unresolved part.",
        )


def test_axent_answer_becomes_product_evidence_never_business_truth() -> None:
    question = AxentPilotQuestion(
        question_id="question:decision:1",
        pilot_id="pilot:1",
        xeed_id="xeed:1",
        xignal_id="xignal:1",
        kind=AxentPilotQuestionKind.DECISION_ADVANCEMENT,
        prompt="Did this Xignal advance a decision?",
        trigger_ref="xignal:1",
        intelligence_return="I can investigate the remaining uncertainty if it did not.",
    )

    evidence = capture_axent_pilot_answer(
        question=question,
        answer=PilotAnswer.NO,
        occurred_at=NOW,
        response_ref="axent-thread:message:42",
    )

    assert evidence.kind is PilotEvidenceKind.DECISION_ADVANCEMENT
    assert evidence.source is PilotEvidenceSource.DIRECT_USER_REPORT
    assert evidence.answer is PilotAnswer.NO
    assert evidence.xignal_id == "xignal:1"


def test_willingness_to_pay_requires_real_offer_context_and_is_offer_response() -> None:
    question = AxentPilotQuestion(
        question_id="question:wtp:1",
        pilot_id="pilot:1",
        xeed_id="xeed:1",
        kind=AxentPilotQuestionKind.WILLINGNESS_TO_PAY,
        prompt="Would you keep this Xeed active for EUR 9.95 per month?",
        trigger_ref="offer:xeed:1",
        intelligence_return="Your answer helps validate whether ongoing observation is worth the price.",
        pricing_kind=PricingEvidenceKind.ACCEPTED_OFFER,
        amount_microunits=9_950_000,
        currency="EUR",
    )

    evidence = capture_axent_pilot_answer(
        question=question,
        answer=PilotAnswer.YES,
        occurred_at=NOW,
        response_ref="axent-thread:message:43",
    )

    assert evidence.kind is PilotEvidenceKind.WILLINGNESS_TO_PAY
    assert evidence.source is PilotEvidenceSource.OFFER_RESPONSE
    assert evidence.amount_microunits == 9_950_000
    assert evidence.currency == "EUR"


def test_axent_exchange_has_no_canonical_write_dependency() -> None:
    source = (
        Path(__file__).parents[2] / "application" / "axent" / "intelligence_exchange.py"
    ).read_text(encoding="utf-8")

    assert "from domain.evidence.admission" not in source
    assert "from domain.faxt" not in source
    assert "import EvidenceAdmission" not in source
