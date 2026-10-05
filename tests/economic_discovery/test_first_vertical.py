"""Synthetic structural proof, not evidence of real-world evaluator quality.

Run the visible example with:
uv run pytest tests/economic_discovery/test_first_vertical.py -k end_to_end -s
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery.brain_contracts import (
    AttentionDisposition,
    DimensionDisposition,
    DimensionEvaluation,
)
from application.economic_discovery.contracts import (
    ConfidenceCapability,
    ConfidenceSemantics,
    DistributionAvailability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredJudgment,
)
from application.economic_discovery.economic_state import (
    EconomicObservation,
    EvidenceBackedEconomicState,
    fingerprint,
)
from application.economic_discovery.explanation import BasisContribution, BasisDatum
from application.economic_discovery.first_vertical import (
    DIMENSIONS,
    EconomicEvaluationRequest,
    EconomicInterpretation,
    EconomicReasoningResult,
    run_economic_vertical,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.source_representation import RichStateDatum, compile_rich_subject_state
from application.subscriber_projection.economic_output import compile_economic_human_output
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId
from domain.relationships.model import ObservedRelationship
from domain.xignal import XignalEpistemicState
from tests.support.grounding import with_synthetic_representation

CORPUS = json.loads((Path(__file__).parent / "fixtures/refrigeration-v1.json").read_text())
AS_OF = datetime.fromisoformat(CORPUS["as_of"])
TEMPORAL = TemporalCurrentnessPolicy(
    "synthetic-economic-currentness", "1", timedelta(days=30), timedelta(days=90)
)


def _state(
    subject_id: str, observations: tuple[EconomicObservation, ...]
) -> EvidenceBackedEconomicState:
    return EvidenceBackedEconomicState(
        compile_rich_subject_state(
            subject_id=subject_id, contributions=tuple(item.datum for item in observations)
        ),
        observations,
    )


def _capability_evidence() -> Evidence:
    """Ground the synthetic capability through current-main admission contracts."""
    document = CORPUS["documents"][0]
    claim = document["text"].split(". ", 1)[0] + "."
    value = document["fields"]["capability"]
    return with_synthetic_representation(
        Evidence(
            id=f"evidence:{document['id']}:capability",
            source=document["source_ref"],
            source_type=document["source_type"],
            reference=f"fixture:refrigeration-v1:{document['id']}",
            extracted_claim=claim,
            observed_at=datetime.fromisoformat(CORPUS["observed_at"]),
            authority=SourceAuthority.OFFICIAL_WEB,
            observation_subject_id=document["subject_id"],
            grounded_claim=GroundedClaim(
                subject_id=document["subject_id"],
                predicate="capability",
                object_or_value=value,
                subject_mention=document["subject_mention"],
                predicate_mention=document["capability_predicate_mention"],
                object_mention=value,
                supporting_excerpt=claim,
            ),
        )
    )


def _document(index: int) -> tuple[EconomicObservation, ...]:
    document = CORPUS["documents"][index]
    observed_at = datetime.fromisoformat(CORPUS["observed_at"])
    observations: list[EconomicObservation] = []
    for name, value in document["fields"].items():
        assert value in document["text"]  # exact material in the rights-cleared source fixture
        basis = BasisDatum(
            datum_id=f"datum:{document['id']}:{name}",
            observation_id=f"obs:{document['id']}",
            source_ref=document["source_ref"],
            source_type=document["source_type"],
            observed_at=observed_at,
            excerpt_or_summary=value,
            contribution=BasisContribution.CONTRADICTS
            if index == 2
            else BasisContribution.SUPPORTS,
            evidence_ref=f"evidence:{document['id']}:{name}",
            representation_fingerprint=fingerprint(document["text"]),
        )
        datum = RichStateDatum(
            name,
            value,
            basis.observation_id,
            f"repr:{document['id']}",
            basis.source_ref,
            observed_at,
        )
        support = None
        if name == "capability":
            # The only canonical creation happens during preparation of already-backed
            # input, through the existing admission factory, never during reasoning.
            evidence = _capability_evidence()
            decision = EvidenceAdmission.admit_claim(
                AdmissionRequest(
                    evidence=evidence,
                    subject_id=document["subject_id"],
                    predicate=name,
                    object_or_value=value,
                    claim_proposition=evidence.extracted_claim,
                )
            )
            assert decision.admitted
            support = FAXT.create(
                faxt_id=FaxtId("faxt:arbor:capability:v1"),
                subject_id=document["subject_id"],
                predicate=name,
                object_or_value=value,
                evidence=evidence,
                decision=decision,
                currentness=Currentness.CURRENT,
            )
        observations.append(
            EconomicObservation(
                datum=datum,
                basis=basis,
                epistemic_state=EpistemicState.OBSERVED if support else EpistemicState.DECLARED,
                currentness=Currentness.CURRENT,
                rights_basis_ref=CORPUS["rights_basis_ref"],
                canonical_support=support,
                contradicts_fields=tuple(document.get("contradicts_fields", ())),
            )
        )
    return tuple(observations)


@pytest.fixture
def inputs() -> tuple[EvidenceBackedEconomicState, EvidenceBackedEconomicState]:
    return _state(CORPUS["documents"][0]["subject_id"], _document(0)), _state(
        CORPUS["documents"][1]["subject_id"], _document(1)
    )


class FakeEvaluator:
    """Choice-only fixture evaluator; no SDK, network, statistical or truth claim."""

    capability_profile = EvaluatorCapabilityProfile(
        "fixture-choice-only",
        "1",
        DistributionCapability.NEVER,
        ConfidenceCapability.NEVER,
        replay_reference_supported=True,
    )

    def __init__(
        self,
        *,
        choices: dict[str, str] | None = None,
        fail: frozenset[str] = frozenset(),
        mismatch: bool = False,
    ) -> None:
        self.choices = choices or {}
        self.fail = fail
        self.mismatch = mismatch
        self.requests: list[EconomicEvaluationRequest] = []

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        assert isinstance(request, EconomicEvaluationRequest)
        self.requests.append(request)
        for field in request.dimension.state_requirements:
            assert (
                request.candidate.state.get(field).value
                == request.candidate.observation(field).datum.value
            )
        assert request.dimension.question and all(
            option.meaning for option in request.choice_space.options
        )
        if request.dimension.dimension_id in self.fail:
            raise TimeoutError("provider outage with untrusted diagnostic payload")
        return StructuredJudgment(
            selected_option=self.choices.get(request.dimension.dimension_id, "YES"),
            evaluator="synthetic-choice-evaluator",
            evaluator_version="fixture-v1",
            decision_contract_id=request.decision_contract_id,
            state_fingerprint="wrong-state" if self.mismatch else request.state_fingerprint,
            question_fingerprint=request.question_fingerprint,
            choice_space_fingerprint=request.choice_space_fingerprint,
            capability_profile=self.capability_profile,
            distribution_availability=DistributionAvailability.UNAVAILABLE,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference=f"fixture-evaluation:{request.dimension.dimension_id}:{request.state_fingerprint}",
        )


def _run(
    inputs: tuple[EvidenceBackedEconomicState, EvidenceBackedEconomicState],
    evaluator: FakeEvaluator | None = None,
    *,
    as_of: datetime = AS_OF,
) -> EconomicReasoningResult:
    return run_economic_vertical(
        subject=inputs[0],
        activity=inputs[1],
        evaluator=evaluator or FakeEvaluator(),
        as_of=as_of,
        temporal_policy=TEMPORAL,
    )


def _change(
    source: EvidenceBackedEconomicState, field: str, value: str | None
) -> EvidenceBackedEconomicState:
    observations = tuple(
        replace(
            item,
            datum=replace(item.datum, value=value),
            basis=replace(item.basis, excerpt_or_summary=value),
        )
        if item.datum.name == field and value is not None
        else item
        for item in source.observations
        if item.datum.name != field or value is not None
    )
    return _state(source.state.subject_id, observations)


def _axis(result: EconomicReasoningResult, dimension: str) -> DimensionEvaluation:
    return next(item for item in result.vector.evaluations if item.dimension_id == dimension)


def test_end_to_end_explainable_potential_from_independent_source_state(
    inputs, monkeypatch
) -> None:
    subject, activity = inputs
    capability = subject.get("capability")
    assert capability.epistemic_state is EpistemicState.OBSERVED
    assert capability.canonical_support.evidence_refs == ("evidence:arbor-capabilities:capability",)
    assert activity.get("event").epistemic_state is EpistemicState.DECLARED
    assert "Arbor" not in CORPUS["documents"][1]["text"]
    assert "Harbor" not in CORPUS["documents"][0]["text"]
    before = (subject.fingerprint, activity.fingerprint, capability.canonical_support)

    def forbidden_write(*args, **kwargs):
        raise AssertionError("reasoning must never call a canonical writer")

    monkeypatch.setattr(EvidenceAdmission, "admit_claim", forbidden_write)
    monkeypatch.setattr(FAXT, "create", forbidden_write)
    monkeypatch.setattr(ObservedRelationship, "create", forbidden_write)
    fake = FakeEvaluator()
    result = _run(inputs, fake)
    output = compile_economic_human_output(result, as_of=AS_OF)
    wire = output.to_wire()
    assert result.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL
    assert result.interpretation.attention is AttentionDisposition.WARRANTED_ATTENTION
    assert [item.dimension.dimension_id for item in fake.requests] == [
        "supplier_role",
        "customer_role",
        "functional_alignment",
    ]
    assert len(result.vector.evaluations) == len(DIMENSIONS) == 6
    assert _axis(result, "supplier_role").selected_option == "YES"
    assert _axis(result, "customer_role").selected_option == "YES"
    assert {datum.source_ref for datum in result.basis.data} == {
        CORPUS["documents"][0]["source_ref"],
        CORPUS["documents"][1]["source_ref"],
    }
    alignment_basis = next(
        item for item in result.dimension_bases if item.semantic_target == "functional_alignment"
    )
    assert {datum.evidence_ref for datum in alignment_basis.data} == {
        "evidence:arbor-capabilities:capability",
        "evidence:harbor-project:required_capability",
        "evidence:harbor-project:event",
    }
    assert before == (subject.fingerprint, activity.fingerprint, capability.canonical_support)
    assert wire["epistemic_state"] == "POTENTIAL" and wire["temporal_state"] == "CURRENT"
    assert "could address" in output.one_sentence_meaning
    assert "commercial access" in output.unknowns[-1]
    assert "sale_probability" not in wire and "confidence" not in wire
    assert all(axis["basis_ref"] for axis in wire["dimensions"])
    json.dumps(wire)  # consumable by a future UI without a model or custom encoder
    print(
        json.dumps(
            {
                key: wire[key]
                for key in (
                    "headline",
                    "one_sentence_meaning",
                    "epistemic_state",
                    "attention",
                    "unknowns",
                    "dimensions",
                )
            },
            indent=2,
        )
    )


@pytest.mark.parametrize(
    "scope,field,dimension",
    [
        (0, "reach_region", "delivery_reach"),
        (1, "required_capability", "functional_alignment"),
        (1, "event", "functional_alignment"),
        (1, "action_until", "timing"),
        (0, "certification", "eligibility"),
        (1, "required_certification", "eligibility"),
    ],
)
def test_missing_material_context_remains_unknown_and_investigate(
    inputs, scope, field, dimension
) -> None:
    modified = list(inputs)
    modified[scope] = _change(modified[scope], field, None)
    fake = FakeEvaluator()
    result = _run(tuple(modified), fake)
    axis = _axis(result, dimension)
    assert axis.disposition is DimensionDisposition.NOT_ANSWERABLE
    assert axis.selected_option is None and axis.evaluator is None
    assert f"MISSING:{'subject' if scope == 0 else 'activity'}.{field}" in axis.reason
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE
    assert dimension not in {request.dimension.dimension_id for request in fake.requests}
    wire = compile_economic_human_output(result, as_of=AS_OF).to_wire()
    assert (
        next(axis for axis in wire["dimensions"] if axis["dimension_id"] == dimension)["value"]
        is None
    )
    assert "could address" not in wire["one_sentence_meaning"]


def test_role_missingness_does_not_force_customer_or_supplier_false(inputs) -> None:
    result = _run((_change(inputs[0], "purchase_activity", None), inputs[1]))
    assert _axis(result, "customer_role").selected_option is None
    assert _axis(result, "supplier_role").selected_option == "YES"
    assert result.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL


def test_contradiction_blocks_positive_interpretation_before_evaluator(inputs) -> None:
    subject = _state(inputs[0].state.subject_id, (*inputs[0].observations, *_document(2)))
    fake = FakeEvaluator()
    result = _run((subject, inputs[1]), fake)
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE
    assert "functional_alignment" not in {
        request.dimension.dimension_id for request in fake.requests
    }
    contradiction = next(
        item for item in result.basis.data if item.contribution is BasisContribution.CONTRADICTS
    )
    assert contradiction.source_ref == CORPUS["documents"][2]["source_ref"]
    assert contradiction.evidence_ref == "evidence:arbor-dispute:capability_dispute"
    output = compile_economic_human_output(result, as_of=AS_OF)
    assert output.contradictions == (CORPUS["documents"][2]["fields"]["capability_dispute"],)
    assert "Potential" not in output.headline
    assert result.vector.state_fingerprint != _run(inputs).vector.state_fingerprint


@pytest.mark.parametrize(
    "choices,fail,mismatch",
    [
        ({"functional_alignment": "UNKNOWN"}, frozenset(), False),
        ({}, frozenset({"functional_alignment"}), False),
        ({}, frozenset({"supplier_role", "customer_role", "functional_alignment"}), False),
        ({}, frozenset(), True),
        ({"functional_alignment": "OUTSIDE_CHOICE_SPACE"}, frozenset(), False),
    ],
)
def test_evaluator_abstention_outage_and_invalid_result_degrade_safely(
    inputs, choices, fail, mismatch
) -> None:
    result = _run(inputs, FakeEvaluator(choices=choices, fail=fail, mismatch=mismatch))
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE
    alignment = _axis(result, "functional_alignment")
    assert alignment.selected_option in (None, "UNKNOWN")
    if fail or mismatch or "OUTSIDE_CHOICE_SPACE" in choices.values():
        assert alignment.replay_reference is None and alignment.distribution == ()
        assert "EVALUATOR_FAILURE" in alignment.reason
        assert "untrusted diagnostic" not in result.basis.uncertainty
    assert _axis(result, "timing").selected_option == "YES"


def test_negative_semantic_classification_is_retained_without_claiming_false_opportunity(
    inputs,
) -> None:
    result = _run(inputs, FakeEvaluator(choices={"functional_alignment": "NO"}))
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.RETAIN
    assert result.raw_judgments[-1].selected_option == "NO"
    assert _axis(result, "functional_alignment").selected_option == "NO"


def test_unknown_reach_is_not_a_home_jurisdiction_rejection(inputs) -> None:
    result = _run((inputs[0], _change(inputs[1], "region", "region:unverified")))
    assert _axis(result, "delivery_reach").selected_option == "UNKNOWN"
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE


def test_explicit_no_requirement_is_not_applicable_not_missing_or_false(inputs) -> None:
    result = _run(
        (
            _change(inputs[0], "certification", None),
            _change(inputs[1], "required_certification", "NONE"),
        )
    )
    eligibility = _axis(result, "eligibility")
    assert eligibility.disposition is DimensionDisposition.NOT_APPLICABLE
    assert eligibility.selected_option is None and eligibility.evaluator is None
    assert result.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL


def test_closed_window_is_known_temporal_block_and_retains_candidate(inputs) -> None:
    activity = _change(inputs[1], "action_until", AS_OF.isoformat())
    result = _run((inputs[0], activity))
    assert _axis(result, "timing").selected_option == "NO"
    assert result.interpretation.attention is AttentionDisposition.RETAIN
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN


def test_temporal_aging_invalidates_without_mutating_history(inputs) -> None:
    initial = _run(inputs)
    later = _run(inputs, as_of=AS_OF + timedelta(days=31))
    assert later.vector.state_fingerprint != initial.vector.state_fingerprint
    assert later.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert later.raw_judgments == ()
    assert inputs[0].get("capability").currentness is Currentness.CURRENT
    assert (
        compile_economic_human_output(later, as_of=later.candidate.as_of).temporal_state
        is Currentness.STALE
    )
    with pytest.raises(ValueError, match="reevaluation"):
        compile_economic_human_output(initial, as_of=later.candidate.as_of)
    assert _run(inputs) == initial


def test_explicit_validity_end_is_preserved_and_blocks_positive_reuse(inputs) -> None:
    reach = inputs[0].get("reach_region")
    expired = replace(reach, valid_until=AS_OF)
    subject = _state(
        inputs[0].state.subject_id,
        tuple(
            expired if item.datum.name == "reach_region" else item
            for item in inputs[0].observations
        ),
    )
    result = _run((subject, inputs[1]))
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert _axis(result, "delivery_reach").selected_option is None
    assert result.vector.state_fingerprint != _run(inputs).vector.state_fingerprint
    proof = next(
        item
        for item in compile_economic_human_output(result, as_of=AS_OF).to_wire()["evidence"]
        if item["datum_ref"] == reach.basis.datum_id
    )
    assert proof["valid_until"] == AS_OF.isoformat()
    assert proof["currentness"] == "HISTORICAL"
    assert reach.valid_until is None and reach.currentness is Currentness.CURRENT


def test_choice_only_provider_does_not_fabricate_probabilities(inputs) -> None:
    result = _run(inputs)
    assert all(item.distribution == () and item.confidence is None for item in result.raw_judgments)
    assert all(
        item.distribution == () and item.confidence is None and item.score is None
        for item in result.vector.evaluations
    )
    assert all(item.replay_reference for item in result.raw_judgments)


class DistributionEvaluator(FakeEvaluator):
    capability_profile = EvaluatorCapabilityProfile(
        "fixture-distribution",
        "1",
        DistributionCapability.OPTIONAL,
        ConfidenceCapability.OPTIONAL_PROVIDER_DEFINED,
        replay_reference_supported=True,
    )

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        judgment = super().evaluate(request)
        return replace(
            judgment,
            evaluator="alternative-synthetic-evaluator",
            evaluator_version="fixture-v2",
            distribution_availability=DistributionAvailability.AVAILABLE,
            distribution=(("YES", 0.51), ("NO", 0.48), ("UNKNOWN", 0.01)),
            confidence_semantics=ConfidenceSemantics.PROVIDER_DEFINED,
            confidence=0.0,
            replay_reference=f"alternative:{judgment.replay_reference}",
        )


def test_provider_swap_retains_full_raw_metadata_without_governing_attention(inputs) -> None:
    choice_only = _run(inputs)
    alternative = _run(inputs, DistributionEvaluator())
    assert alternative.interpretation == choice_only.interpretation
    assert alternative.vector.state_fingerprint == choice_only.vector.state_fingerprint
    for raw in alternative.raw_judgments:
        axis = _axis(alternative, raw.decision_contract_id.split(":")[0])
        assert (
            axis.distribution
            == raw.distribution
            == (("YES", 0.51), ("NO", 0.48), ("UNKNOWN", 0.01))
        )
        assert axis.confidence == raw.confidence == 0.0
        assert axis.replay_reference == raw.replay_reference
    output = compile_economic_human_output(alternative, as_of=AS_OF)
    assert output.output_id != compile_economic_human_output(choice_only, as_of=AS_OF).output_id
    assert "confidence" not in output.to_wire()


def test_malformed_distribution_cannot_produce_positive_output(inputs) -> None:
    class MalformedEvaluator(DistributionEvaluator):
        def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
            return replace(super().evaluate(request), distribution=(("YES", 0.8), ("NO", 0.8)))

    result = _run(inputs, MalformedEvaluator())
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.raw_judgments == ()
    assert "EVALUATOR_FAILURE:ValueError" in _axis(result, "functional_alignment").reason


def test_economic_interpretation_cannot_be_observed_truth() -> None:
    with pytest.raises(ValueError, match="never assert OBSERVED"):
        EconomicInterpretation(
            XignalEpistemicState.OBSERVED, AttentionDisposition.WARRANTED_ATTENTION, ("MODEL_YES",)
        )


def test_cannot_promote_declared_claim_to_observed_or_change_canonical_binding(inputs) -> None:
    declared = inputs[0].get("purchase_activity")
    with pytest.raises(ValueError, match="admitted FAXT"):
        replace(declared, epistemic_state=EpistemicState.OBSERVED)
    capability = inputs[0].get("capability")
    with pytest.raises(ValueError, match="canonical support"):
        replace(
            capability,
            datum=replace(capability.datum, value="false capability"),
            basis=replace(capability.basis, excerpt_or_summary="false capability"),
        )
    with pytest.raises(ValueError, match="every considered observation"):
        replace(inputs[0], observations=inputs[0].observations[:-1])
    with pytest.raises(ValueError, match="exact evidence"):
        replace(declared, basis=replace(declared.basis, source_ref="https://wrong.example"))


@pytest.mark.parametrize(
    "changes",
    [
        {"subject_id": "org:unrelated"},
        {"predicate": "manufactures"},
        {"object_or_value": "nuclear weapons"},
    ],
)
def test_vertical_capability_cannot_admit_a_different_tuple_from_same_claim(changes) -> None:
    evidence = _capability_evidence()
    original = AdmissionRequest(
        evidence=evidence,
        subject_id=CORPUS["documents"][0]["subject_id"],
        predicate="capability",
        object_or_value=CORPUS["documents"][0]["fields"]["capability"],
        claim_proposition=evidence.extracted_claim,
    )
    request = replace(original, **changes)
    valid_decision = EvidenceAdmission.admit_claim(original)
    assert valid_decision.is_canonical
    assert not EvidenceAdmission.admit_claim(request).admitted
    # Neither a rejected decision nor the valid original decision authorizes
    # a different tuple. Keep the exact same evidence bytes and claim throughout.
    for decision in (EvidenceAdmission.admit_claim(request), valid_decision):
        with pytest.raises(EvidenceAdmissionRequired):
            FAXT.create(
                faxt_id=FaxtId("faxt:invalid-capability"),
                subject_id=request.subject_id,
                predicate=request.predicate,
                object_or_value=request.object_or_value,
                evidence=evidence,
                decision=decision,
            )


@pytest.mark.parametrize("missing", ["observation_subject_id", "grounded_claim"])
def test_vertical_capability_requires_current_main_grounding(missing) -> None:
    evidence = replace(_capability_evidence(), **{missing: None})
    request = AdmissionRequest(
        evidence=evidence,
        subject_id=CORPUS["documents"][0]["subject_id"],
        predicate="capability",
        object_or_value=CORPUS["documents"][0]["fields"]["capability"],
        claim_proposition=evidence.extracted_claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    assert not decision.admitted
    with pytest.raises(EvidenceAdmissionRequired):
        FAXT.create(
            faxt_id=FaxtId("faxt:ungrounded-capability"),
            subject_id=request.subject_id,
            predicate=request.predicate,
            object_or_value=request.object_or_value,
            evidence=evidence,
            decision=decision,
        )


def test_vertical_canonical_support_cannot_cross_subjects(inputs) -> None:
    with pytest.raises(ValueError, match="cannot cross economic subjects"):
        _state("org:unrelated", inputs[0].observations)


def test_future_evidence_is_rejected_before_evaluation(inputs) -> None:
    fake = FakeEvaluator()
    with pytest.raises(ValueError, match="before observation"):
        _run(inputs, fake, as_of=AS_OF - timedelta(days=10))
    assert fake.requests == []


@pytest.mark.parametrize(
    "metadata",
    [{"selected_option": "NO"}, {"replay_reference": "fake"}, {"evaluator_version": "fake"}],
)
def test_unanswerable_vector_cannot_fabricate_choice_or_replay(metadata) -> None:
    with pytest.raises(ValueError, match="cannot fabricate"):
        DimensionEvaluation(
            "test", "contract", DimensionDisposition.NOT_ANSWERABLE, reason="MISSING", **metadata
        )
