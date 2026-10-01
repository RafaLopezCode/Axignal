"""FR-27 One Buyer / One Job Pilot Contract."""

from dataclasses import replace
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
    DiscoveryEvaluability,
    PilotAnswer,
    PilotEvidence,
    PilotEvidenceConflict,
    PilotEvidenceKind,
    PilotEvidenceSource,
    PilotObservabilityAssessment,
    PilotObservabilityDisposition,
    PresenceRelevance,
    PricingEvidenceKind,
    PublicSurfaceObservation,
    SurfaceObservation,
    XeedAttentionPosture,
    project_presence_relevance,
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


def _observability(
    *,
    posture: XeedAttentionPosture = XeedAttentionPosture.GROW_VISIBILITY,
    disposition: PilotObservabilityDisposition = (
        PilotObservabilityDisposition.PUBLICLY_OBSERVABLE
    ),
    surfaces: tuple[SurfaceObservation, ...] | None = None,
) -> PilotObservabilityAssessment:
    if surfaces is None:
        surfaces = (
            SurfaceObservation(
                surface_id="search:google:es",
                result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
                evidence_ref="measurement:search:1",
            ),
            SurfaceObservation(
                surface_id="public-web:news",
                result=PublicSurfaceObservation.PRESENCE_OBSERVED,
                evidence_ref="measurement:news:1",
            ),
        )
    return PilotObservabilityAssessment(
        assessment_id="observability:1",
        pilot_id=FR27_AGENCY_CHANGE_PILOT.pilot_id,
        xeed_id=FR27_AGENCY_CHANGE_PILOT.primary_xeed_id,
        assessed_at=T0,
        disposition=disposition,
        attention_posture=posture,
        surfaces=surfaces,
        assessment_ref="pilot-observability-note:1",
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


def test_no_presence_is_an_observed_result_only_with_provenance() -> None:
    surface = SurfaceObservation(
        surface_id="search:google:es",
        result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
        evidence_ref="measurement:search:1",
    )

    assert surface.result is PublicSurfaceObservation.NO_PRESENCE_OBSERVED

    with pytest.raises(ValueError, match="provenance"):
        SurfaceObservation(
            surface_id="search:google:es",
            result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
        )


def test_public_observability_requires_a_real_observed_surface() -> None:
    with pytest.raises(ValueError, match="at least one observed public surface"):
        _observability(
            surfaces=(
                SurfaceObservation(
                    surface_id="search:google:es",
                    result=PublicSurfaceObservation.NOT_OBSERVED,
                ),
            ),
        )


def test_private_or_non_observable_job_is_not_scored_as_discovery_failure() -> None:
    assessment = _observability(
        disposition=PilotObservabilityDisposition.PRIVATE_OR_NON_OBSERVABLE,
        surfaces=(
            SurfaceObservation(
                surface_id="crm:pipeline",
                result=PublicSurfaceObservation.OUTSIDE_PUBLIC_SCOPE,
            ),
        ),
    )

    assert assessment.discovery_evaluability is DiscoveryEvaluability.NOT_EVALUABLE
    assert assessment.observed_surface_count == 0


def test_low_public_presence_can_be_valid_for_growth_or_low_profile_posture() -> None:
    surfaces = (
        SurfaceObservation(
            surface_id="search:google:es",
            result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            evidence_ref="measurement:search:1",
        ),
        SurfaceObservation(
            surface_id="public-web:news",
            result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            evidence_ref="measurement:news:1",
        ),
    )
    growth = _observability(
        posture=XeedAttentionPosture.GROW_VISIBILITY,
        surfaces=surfaces,
    )
    low_profile = replace(
        growth,
        assessment_id="observability:2",
        attention_posture=XeedAttentionPosture.LOW_PROFILE,
    )

    assert growth.observed_no_presence_count == 2
    assert low_profile.observed_no_presence_count == 2
    assert growth.attention_posture is XeedAttentionPosture.GROW_VISIBILITY
    assert low_profile.attention_posture is XeedAttentionPosture.LOW_PROFILE


def test_same_low_presence_projects_different_private_relevance() -> None:
    surfaces = (
        SurfaceObservation(
            surface_id="search:google:es",
            result=PublicSurfaceObservation.NO_PRESENCE_OBSERVED,
            evidence_ref="measurement:search:1",
        ),
    )
    growth = _observability(
        posture=XeedAttentionPosture.GROW_VISIBILITY,
        surfaces=surfaces,
    )
    low_profile = replace(
        growth,
        assessment_id="observability:2",
        attention_posture=XeedAttentionPosture.LOW_PROFILE,
    )

    assert project_presence_relevance(growth) is PresenceRelevance.VISIBILITY_GAP_CANDIDATE
    assert project_presence_relevance(low_profile) is PresenceRelevance.LOW_EXPOSURE_OBSERVED


def test_public_mention_is_exposure_candidate_for_low_profile_posture() -> None:
    low_profile = _observability(posture=XeedAttentionPosture.LOW_PROFILE)

    assert (
        project_presence_relevance(low_profile) is PresenceRelevance.UNEXPECTED_EXPOSURE_CANDIDATE
    )


def test_attention_posture_does_not_become_canonical_truth() -> None:
    assessment = _observability(posture=XeedAttentionPosture.LOW_PROFILE)

    assert not hasattr(assessment, "canonical_truth")
    assert not hasattr(assessment, "organization_profile")
    assert not hasattr(assessment, "faxt")


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
        observability=_observability(),
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
        observability=_observability(),
        economics=_economics(),
        evidence=evidence,
    )

    assert report.coverage.protocol_complete
    assert report.pricing_evidence == (wtp,)
    assert report.additional_xeed_evidence[0].evidence_id == "xeed:1"
    assert report.observability.discovery_evaluability is DiscoveryEvaluability.EVALUABLE


def test_pricing_hypothesis_is_not_observation_until_wtp_evidence_exists() -> None:
    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        observability=_observability(),
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


def test_pilot_must_use_matching_fr26_xeed_economics_and_observability() -> None:
    economics = _economics()

    with pytest.raises(ValueError, match="primary Xeed"):
        summarize_pilot(
            hypothesis=FR27_AGENCY_CHANGE_PILOT,
            observability=_observability(),
            economics=replace(economics, xeed_id="xeed:other"),
            evidence=(),
        )

    with pytest.raises(ValueError, match="observability assessment"):
        summarize_pilot(
            hypothesis=FR27_AGENCY_CHANGE_PILOT,
            observability=replace(_observability(), xeed_id="xeed:other"),
            economics=economics,
            evidence=(),
        )


def test_sqlite_pilot_evidence_and_observability_are_append_only(tmp_path) -> None:
    memory = SqlitePilotEvidenceMemory(tmp_path / "pilot.sqlite3")
    evidence = _evidence("decision:durable", PilotEvidenceKind.DECISION_ADVANCEMENT)
    observability = _observability()

    assert memory.append(evidence)
    assert not memory.append(evidence)
    assert memory.for_pilot(FR27_AGENCY_CHANGE_PILOT.pilot_id) == (evidence,)

    assert memory.append_observability(observability)
    assert not memory.append_observability(observability)
    assert memory.observability_for_pilot(FR27_AGENCY_CHANGE_PILOT.pilot_id) == (observability,)

    conflicting = replace(evidence, answer=PilotAnswer.NO)
    with pytest.raises(PilotEvidenceConflict):
        memory.append(conflicting)

    conflicting_observability = replace(
        observability,
        attention_posture=XeedAttentionPosture.LOW_PROFILE,
    )
    with pytest.raises(PilotEvidenceConflict):
        memory.append_observability(conflicting_observability)


def test_pilot_report_does_not_expose_truth_or_success_score() -> None:
    report = summarize_pilot(
        hypothesis=FR27_AGENCY_CHANGE_PILOT,
        observability=_observability(),
        economics=_economics(),
        evidence=(),
    )

    assert not hasattr(report, "truth")
    assert not hasattr(report, "success_score")
    assert not hasattr(report, "validated")
