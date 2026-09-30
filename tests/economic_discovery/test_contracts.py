from __future__ import annotations

from dataclasses import replace

import pytest

from application.economic_discovery import (
    CandidateLineageEvent,
    ChoiceOption,
    ChoiceSpaceContract,
    DiscoveryRunTrace,
    DiscoveryStage,
    StructuredJudgment,
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


def test_structured_judgment_requires_complete_distribution() -> None:
    space = _space()
    judgment = StructuredJudgment(
        selected_option="DIRECT_CUSTOMER",
        distribution=(("DIRECT_CUSTOMER", 0.51), ("PRESCRIBER", 0.29), ("NO_MATCH", 0.20)),
        evaluator="test-double",
        evaluator_version="1",
        decision_contract_id="CUSTOMER_FIT.v0",
        state_fingerprint="state",
        question_fingerprint="question",
        choice_space_fingerprint=space.fingerprint,
        confidence=0.4,
    )
    assert dict(judgment.distribution)["DIRECT_CUSTOMER"] == pytest.approx(0.51)


@pytest.mark.parametrize(
    "distribution",
    [
        (("A", 0.7), ("B", 0.2)),
        (("A", 1.1), ("B", -0.1)),
        (("A", 0.5), ("A", 0.5)),
    ],
)
def test_structured_judgment_fails_closed_on_invalid_distribution(
    distribution: tuple[tuple[str, float], ...],
) -> None:
    with pytest.raises(ValueError):
        StructuredJudgment(
            selected_option="A",
            distribution=distribution,
            evaluator="e",
            evaluator_version="1",
            decision_contract_id="d",
            state_fingerprint="s",
            question_fingerprint="q",
            choice_space_fingerprint="c",
        )


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
