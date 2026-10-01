"""FR-27 One Buyer / One Job Pilot Contract."""

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.pilot_validation import (
    FR27_AGENCY_CHANGE_PILOT,
    PilotAnswer,
    PilotEvidence,
    PilotEvidenceConflict,
    PilotEvidenceKind,
    PilotEvidenceSource,
    PricingEvidenceKind,
    summarize_pilot,
)
from application.economic_discovery.unit_economics import (
    CostAllocationMethod,
    CostScope,
    EconomicsPhase,
    UnitEconomicsAttribution,
    summarize_xeed_unit_economics,
)
from pipeline.pilot_validation.sqlite_store import SqlitePilotEvidenceMemory

T0 = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)


def _economics():
    event = LearningEvent(
        event_id="learn:1",
        kind=LearningEventKind.DETERMINISTIC_EVALUATION,
        outcome=LearningOutcome.COMPLETED,
        occurred_at=T0,
        subject_id="org:client",
        xeed_id=FR27_AGENCY_CHANGE_PILOT.primary_xeed_id,
        activity_ref="run:pilot",
        policy_id="pilot-policy",
        policy_version="1",
        code_sha="abc123",
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint="input:1",
        reason_code="XIGNAL_EMITTED",
        replay=LearningReplayReference.replayable(source="pilot-fixture"),
        cost=LearningCost(amount_microunits=100_000, currency="EUR"),
        yield_=LearningYield(xignals_emitted=1),
    )
    return summarize_xeed_unit_economics(
        xeed_id=FR27_AGENCY_CHANGE_PILOT.primary_xeed_id,
        events=(event,),
        attributions=(
            UnitEconomicsAttribution(
                event_id="learn:1",
                phase=EconomicsPhase.FIRST_VALUE,
                cost_scope=CostScope.XEED_PRIVATE,
                allocation_method=CostAllocationMethod.DIRECT,
                allocated_cost_microunits=100_000,
                currency="EUR",
                useful_xignals=1,
                evidence_inspections=1,
            ),
        ),
    )


def _evidence(
    evidence_id: str,
    kind: PilotEvidenceKind,
    *,
    answer: PilotAnswer = PilotAnswer.YES,
    source: PilotEvidenceSource = PilotEvidenceSource.DIRECT_USER_REPORT,
    minute: int = 1,
) -> PilotEvidence:
    return PilotEvidence(
        evidence_id=evidence_id,
        pilot_id=FR27_AGENCY_CHANGE_PILOT.pilot_id,
        occurred_at=T0 + timedelta(minutes=minute),
        kind=kind,
        source=source,
        evidence_ref=f"pilot-note:{evidence_id}",
        answer=answer,
        xeed_id=FR27_AGENCY_CHANGE_PILOT.primary_xeed_id,
        xignal_id="xignal:1",
        learning_event_id="learn:1",
    )


def test_canonical_pilot_is_one_buyer_and_one_job_hypothesis() -> None:
    pilot = FR27_AGENCY_CHANGE_PILOT

    assert "SEO/GEO/AEO agency" in pilot.buyer_archetype
    assert "material externally observable change" in pilot.job_to_be_done
    assert pilot.base_price_microunits == 9_950_000
    assert pilot.additional_xeed_price_microunits == 4_950_000


def test_usage_telemetry_cannot_establish_willingness_to_pay() -> None:
    with pytest.raises(ValueError, match="usage telemetry"):
        PilotEvidence(
            evidence_id="wtp:bad",
            pilot_id=FR27_AGENCY_CHANGE_PILOT.pilot_id,
            occurred_at=T0,
            kind=PilotEvidenceKind.WILLINGNESS_TO_PAY,
            source=PilotEvidenceSource.PRODUCT_TELEMETRY,
            evidence_ref="telemetry:session",
            pricing_kind=PricingEvidenceKind.ACCEPTED_OFFER,
            amount_microunits=9_950_000,
            currency="EUR",
        )


def test_trust_and_return_causality_require_explicit_user_report() -> None:
    with pytest.raises(ValueError, match="trust"):
        _evidence(
            "trust:bad",
            PilotEvidenceKind.EVIDENCE_TRUST_REPORT,
            source=PilotEvidenceSource.PRODUCT_TELEMETRY,
        )
    with pytest.raises(ValueError, match="return causality"):
        _evidence(
            "return:bad",
            PilotEvidenceKind.RETURN_BECAUSE_CHANGE,
            source=PilotEvidenceSource.PRODUCT_TELEMETRY,
        )


def test_negative_pilot_evidence_is_preserved_as_valid_outcome() -> None:
    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        economics=_economics(),
        evidence=(
            _evidence(
                "decision:no",
                PilotEvidenceKind.DECISION_ADVANCEMENT,
                answer=PilotAnswer.NO,
            ),
            _evidence(
                "trust:no",
                PilotEvidenceKind.EVIDENCE_TRUST_REPORT,
                answer=PilotAnswer.NO,
                minute=2,
            ),
        ),
    )

    assert report.negative_evidence_count == 2
    assert report.coverage.decision_advancement == 1
    assert report.coverage.evidence_trust_report == 1
    assert not report.coverage.protocol_complete


def test_protocol_complete_requires_all_six_observation_dimensions() -> None:
    wtp = PilotEvidence(
        evidence_id="wtp:1",
        pilot_id=FR27_AGENCY_CHANGE_PILOT.pilot_id,
        occurred_at=T0 + timedelta(minutes=5),
        kind=PilotEvidenceKind.WILLINGNESS_TO_PAY,
        source=PilotEvidenceSource.OFFER_RESPONSE,
        evidence_ref="offer:9.95",
        answer=PilotAnswer.YES,
        xeed_id=FR27_AGENCY_CHANGE_PILOT.primary_xeed_id,
        pricing_kind=PricingEvidenceKind.ACCEPTED_OFFER,
        amount_microunits=9_950_000,
        currency="EUR",
    )
    evidence = (
        _evidence("decision:1", PilotEvidenceKind.DECISION_ADVANCEMENT),
        _evidence(
            "inspection:1",
            PilotEvidenceKind.EVIDENCE_INSPECTION,
            source=PilotEvidenceSource.PRODUCT_TELEMETRY,
            minute=2,
        ),
        _evidence("trust:1", PilotEvidenceKind.EVIDENCE_TRUST_REPORT, minute=3),
        _evidence("return:1", PilotEvidenceKind.RETURN_BECAUSE_CHANGE, minute=4),
        wtp,
        _evidence(
            "xeed:1",
            PilotEvidenceKind.ADDITIONAL_XEED_VALUE,
            minute=6,
        ),
    )

    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        economics=_economics(),
        evidence=evidence,
    )

    assert report.coverage.protocol_complete
    assert report.pricing_evidence == (wtp,)
    assert report.additional_xeed_evidence[0].evidence_id == "xeed:1"


def test_pricing_hypothesis_is_not_observation_until_wtp_evidence_exists() -> None:
    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        economics=_economics(),
        evidence=(
            _evidence(
                "inspection:only",
                PilotEvidenceKind.EVIDENCE_INSPECTION,
                source=PilotEvidenceSource.PRODUCT_TELEMETRY,
            ),
        ),
    )

    assert report.hypothesis.base_price_microunits == 9_950_000
    assert report.pricing_evidence == ()


def test_pilot_must_use_matching_fr26_xeed_economics() -> None:
    economics = _economics()
    from dataclasses import replace

    with pytest.raises(ValueError, match="primary Xeed"):
        summarize_pilot(
            hypothesis=FR27_AGENCY_CHANGE_PILOT,
            economics=replace(economics, xeed_id="xeed:other"),
            evidence=(),
        )


def test_sqlite_pilot_evidence_is_append_only_and_replay_safe(tmp_path) -> None:
    memory = SqlitePilotEvidenceMemory(tmp_path / "pilot.sqlite3")
    evidence = _evidence("decision:durable", PilotEvidenceKind.DECISION_ADVANCEMENT)

    assert memory.append(evidence)
    assert not memory.append(evidence)
    assert memory.for_pilot(FR27_AGENCY_CHANGE_PILOT.pilot_id) == (evidence,)

    conflicting = PilotEvidence(
        **{
            field: getattr(evidence, field)
            for field in evidence.__dataclass_fields__
            if field != "answer"
        },
        answer=PilotAnswer.NO,
    )
    with pytest.raises(PilotEvidenceConflict):
        memory.append(conflicting)


def test_pilot_report_does_not_expose_truth_or_success_score() -> None:
    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        economics=_economics(),
        evidence=(),
    )

    assert not hasattr(report, "truth")
    assert not hasattr(report, "success_score")
    assert not hasattr(report, "validated")
