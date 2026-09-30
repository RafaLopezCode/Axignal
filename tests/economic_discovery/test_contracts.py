from __future__ import annotations

from dataclasses import replace

import pytest

from application.economic_discovery import (
    CandidateLineageEvent,
    ChoiceOption,
    ChoiceSpaceContract,
    ConfidenceCapability,
    ConfidenceSemantics,
    DiscoveryRunTrace,
    DiscoveryStage,
    DistributionAvailability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredJudgment,
    evaluate_structured,
)


def _space() -> ChoiceSpaceContract:
    return ChoiceSpaceContract(
        choice_space_id="customer-fit.v0",
        version="0.1",
        semantic_target="Distinguish the economic role of a candidate relative to a Xeed.",
        options=(
            ChoiceOption(
                "DIRECT_CUSTOMER", "Candidate plausibly buys the relevant capability directly."
            ),
            ChoiceOption(
                "PRESCRIBER", "Candidate can influence demand without being the direct buyer."
            ),
            ChoiceOption(
                "NO_MATCH", "Supplied alternatives do not establish a relevant economic role."
            ),
        ),
        mutually_exclusive=True,
        coverage_policy="EXPLICIT_NO_MATCH",
        scope="CURRENT_ECONOMIC_ROLE",
        composition_policy="PRESERVE_DISTRIBUTION_NO_IMPLICIT_THRESHOLD",
    )


def test_choice_space_fingerprint_is_semantic_and_stable() -> None:
    assert _space().fingerprint == _space().fingerprint
    assert replace(_space(), version="0.2").fingerprint != _space().fingerprint


def test_choice_space_rejects_duplicate_options() -> None:
    with pytest.raises(ValueError, match="unique"):
        ChoiceSpaceContract(
            "x",
            "1",
            "target",
            (ChoiceOption("A", "a"), ChoiceOption("A", "b")),
            True,
            "EXHAUSTIVE",
            "scope",
            "policy",
        )


def _profile(
    *,
    distribution: DistributionCapability,
    confidence: ConfidenceCapability,
) -> EvaluatorCapabilityProfile:
    return EvaluatorCapabilityProfile(
        profile_id="structured-evaluator",
        version="1",
        distribution=distribution,
        confidence=confidence,
        replay_reference_supported=True,
    )


def _request() -> StructuredEvaluationRequest:
    space = _space()
    return StructuredEvaluationRequest(
        decision_contract_id="CUSTOMER_FIT.v0",
        state_fingerprint="state",
        question_fingerprint="question",
        choice_space_fingerprint=space.fingerprint,
        option_ids=tuple(option.option_id for option in space.options),
    )


def test_structured_judgment_accepts_selected_choice_without_fake_distribution() -> None:
    judgment = StructuredJudgment(
        selected_option="DIRECT_CUSTOMER",
        evaluator="choice-only",
        evaluator_version="1",
        decision_contract_id="CUSTOMER_FIT.v0",
        state_fingerprint="state",
        question_fingerprint="question",
        choice_space_fingerprint=_space().fingerprint,
        capability_profile=_profile(
            distribution=DistributionCapability.NEVER,
            confidence=ConfidenceCapability.NEVER,
        ),
        distribution_availability=DistributionAvailability.UNAVAILABLE,
        confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
        replay_reference="artifact:choice-only:1",
    )

    assert judgment.selected_option == "DIRECT_CUSTOMER"
    assert judgment.distribution == ()
    assert judgment.confidence is None


def test_structured_judgment_preserves_real_distribution_and_provider_confidence() -> None:
    judgment = StructuredJudgment(
        selected_option="DIRECT_CUSTOMER",
        evaluator="distribution-capable",
        evaluator_version="1",
        decision_contract_id="CUSTOMER_FIT.v0",
        state_fingerprint="state",
        question_fingerprint="question",
        choice_space_fingerprint=_space().fingerprint,
        capability_profile=_profile(
            distribution=DistributionCapability.ALWAYS,
            confidence=ConfidenceCapability.OPTIONAL_PROVIDER_DEFINED,
        ),
        distribution_availability=DistributionAvailability.AVAILABLE,
        confidence_semantics=ConfidenceSemantics.PROVIDER_DEFINED,
        replay_reference="artifact:distribution:1",
        distribution=(
            ("DIRECT_CUSTOMER", 0.51),
            ("PRESCRIBER", 0.29),
            ("NO_MATCH", 0.20),
        ),
        confidence=0.4,
    )

    assert dict(judgment.distribution)["DIRECT_CUSTOMER"] == pytest.approx(0.51)
    assert judgment.confidence == pytest.approx(0.4)


@pytest.mark.parametrize(
    ("availability", "distribution"),
    [
        (DistributionAvailability.AVAILABLE, ()),
        (DistributionAvailability.UNAVAILABLE, (("A", 1.0),)),
        (DistributionAvailability.AVAILABLE, (("A", 0.7), ("B", 0.2))),
        (DistributionAvailability.AVAILABLE, (("A", 1.1), ("B", -0.1))),
        (DistributionAvailability.AVAILABLE, (("A", 0.5), ("A", 0.5))),
    ],
)
def test_structured_judgment_fails_closed_on_invalid_distribution_semantics(
    availability: DistributionAvailability,
    distribution: tuple[tuple[str, float], ...],
) -> None:
    with pytest.raises(ValueError):
        StructuredJudgment(
            selected_option="A",
            evaluator="e",
            evaluator_version="1",
            decision_contract_id="d",
            state_fingerprint="s",
            question_fingerprint="q",
            choice_space_fingerprint="c",
            capability_profile=_profile(
                distribution=DistributionCapability.OPTIONAL,
                confidence=ConfidenceCapability.NEVER,
            ),
            distribution_availability=availability,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference="artifact:e:1",
            distribution=distribution,
        )


def test_confidence_requires_provider_defined_semantics_and_capability() -> None:
    with pytest.raises(ValueError, match="provider-defined"):
        StructuredJudgment(
            selected_option="A",
            evaluator="e",
            evaluator_version="1",
            decision_contract_id="d",
            state_fingerprint="s",
            question_fingerprint="q",
            choice_space_fingerprint="c",
            capability_profile=_profile(
                distribution=DistributionCapability.NEVER,
                confidence=ConfidenceCapability.OPTIONAL_PROVIDER_DEFINED,
            ),
            distribution_availability=DistributionAvailability.UNAVAILABLE,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference="artifact:e:1",
            confidence=0.8,
        )


class _ChoiceOnlyEvaluator:
    capability_profile = _profile(
        distribution=DistributionCapability.NEVER,
        confidence=ConfidenceCapability.NEVER,
    )

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        return StructuredJudgment(
            selected_option=request.option_ids[0],
            evaluator="structured-output",
            evaluator_version="baseline-v1",
            decision_contract_id=request.decision_contract_id,
            state_fingerprint=request.state_fingerprint,
            question_fingerprint=request.question_fingerprint,
            choice_space_fingerprint=request.choice_space_fingerprint,
            capability_profile=self.capability_profile,
            distribution_availability=DistributionAvailability.UNAVAILABLE,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference="artifact:structured-output:1",
        )


def test_structured_evaluator_port_supports_choice_only_baseline_without_one_hot() -> None:
    judgment = evaluate_structured(_ChoiceOnlyEvaluator(), _request())

    assert judgment.selected_option == "DIRECT_CUSTOMER"
    assert judgment.distribution_availability is DistributionAvailability.UNAVAILABLE
    assert judgment.distribution == ()


class _DistributionEvaluator:
    capability_profile = _profile(
        distribution=DistributionCapability.OPTIONAL,
        confidence=ConfidenceCapability.OPTIONAL_PROVIDER_DEFINED,
    )

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        return StructuredJudgment(
            selected_option=request.option_ids[1],
            evaluator="distribution-output",
            evaluator_version="baseline-v2",
            decision_contract_id=request.decision_contract_id,
            state_fingerprint=request.state_fingerprint,
            question_fingerprint=request.question_fingerprint,
            choice_space_fingerprint=request.choice_space_fingerprint,
            capability_profile=self.capability_profile,
            distribution_availability=DistributionAvailability.AVAILABLE,
            confidence_semantics=ConfidenceSemantics.PROVIDER_DEFINED,
            replay_reference="artifact:distribution-output:1",
            distribution=(
                (request.option_ids[0], 0.2),
                (request.option_ids[1], 0.7),
                (request.option_ids[2], 0.1),
            ),
        )


def test_structured_evaluator_port_supports_distribution_without_forced_confidence() -> None:
    judgment = evaluate_structured(_DistributionEvaluator(), _request())

    assert judgment.selected_option == "PRESCRIBER"
    assert judgment.distribution_availability is DistributionAvailability.AVAILABLE
    assert judgment.confidence_semantics is ConfidenceSemantics.PROVIDER_DEFINED
    assert judgment.confidence is None


class _MismatchedEvaluator(_ChoiceOnlyEvaluator):
    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        judgment = super().evaluate(request)
        return replace(judgment, state_fingerprint="wrong-state")


def test_structured_evaluator_port_rejects_provenance_mismatch() -> None:
    with pytest.raises(ValueError, match="state fingerprint mismatch"):
        evaluate_structured(_MismatchedEvaluator(), _request())


def test_candidate_lineage_is_replayable_per_candidate() -> None:
    event = CandidateLineageEvent(
        candidate_id="org:1",
        stage=DiscoveryStage.RETRIEVE,
        outcome="SURVIVED",
        reason_code="TOP_K",
        contract_version="retrieval.v0",
        input_fingerprint="input",
        output_fingerprint="output",
    )
    trace = DiscoveryRunTrace("run-1", "abc123", "cfg", (event,))
    assert trace.lineage_for("org:1") == (event,)
    assert trace.lineage_for("org:2") == ()


def test_structured_choice_preserves_unknown_without_probability_claim() -> None:
    request = StructuredEvaluationRequest(
        decision_contract_id="EVIDENCE_SUPPORT.v1",
        state_fingerprint="state:unknown",
        question_fingerprint="question:unknown",
        choice_space_fingerprint="choice:unknown",
        option_ids=("SUPPORTED", "UNRESOLVED"),
    )

    class _UnknownEvaluator:
        capability_profile = _profile(
            distribution=DistributionCapability.NEVER,
            confidence=ConfidenceCapability.NEVER,
        )

        def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
            return StructuredJudgment(
                selected_option="UNRESOLVED",
                evaluator="choice-only",
                evaluator_version="1",
                decision_contract_id=request.decision_contract_id,
                state_fingerprint=request.state_fingerprint,
                question_fingerprint=request.question_fingerprint,
                choice_space_fingerprint=request.choice_space_fingerprint,
                capability_profile=self.capability_profile,
                distribution_availability=DistributionAvailability.UNAVAILABLE,
                confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
                replay_reference="artifact:unknown:1",
            )

    judgment = evaluate_structured(_UnknownEvaluator(), request)

    assert judgment.selected_option == "UNRESOLVED"
    assert judgment.distribution == ()
    assert judgment.confidence is None


def test_capability_profile_fingerprint_changes_with_semantics() -> None:
    choice_only = _profile(
        distribution=DistributionCapability.NEVER,
        confidence=ConfidenceCapability.NEVER,
    )
    distribution_capable = _profile(
        distribution=DistributionCapability.OPTIONAL,
        confidence=ConfidenceCapability.NEVER,
    )

    assert choice_only.fingerprint != distribution_capable.fingerprint


def test_structured_evaluator_requires_replay_reference_capability() -> None:
    class _NoReplayEvaluator(_ChoiceOnlyEvaluator):
        capability_profile = EvaluatorCapabilityProfile(
            profile_id="no-replay",
            version="1",
            distribution=DistributionCapability.NEVER,
            confidence=ConfidenceCapability.NEVER,
            replay_reference_supported=False,
        )

    with pytest.raises(ValueError, match="must provide a replay reference"):
        evaluate_structured(_NoReplayEvaluator(), _request())
