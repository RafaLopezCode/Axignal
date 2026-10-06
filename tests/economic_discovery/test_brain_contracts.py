from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.economic_discovery import (
    AttentionDisposition,
    DimensionDisposition,
    DimensionEvaluation,
    EconomicAssociationSnapshot,
    EpistemicProfile,
    ObservationMode,
    ObservationPlan,
    ObservationRecord,
    ObservationTask,
    SemanticPrimitive,
    StateChange,
    TypedJudgmentVector,
    TypingDimensionContract,
    XignalPresentation,
    affected_dimensions,
)

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _dimension(dimension_id: str, *dependencies: str) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=f"{dimension_id} relative to Xeed",
        primitive=SemanticPrimitive.NOUL,
        question=f"Does {dimension_id} apply?",
        state_requirements=("candidate_context",),
        dependencies=dependencies,
        mutually_exclusive=False,
        abstention_policy="NOT_ANSWERABLE",
    )


def _vector() -> TypedJudgmentVector:
    return TypedJudgmentVector(
        subject_id="xeed:a",
        candidate_id="org:b",
        state_fingerprint="state-2",
        evaluated_at=NOW,
        evaluations=(
            DimensionEvaluation(
                dimension_id="CUSTOMER_ROLE",
                contract_fingerprint="contract",
                disposition=DimensionDisposition.ANSWERABLE,
                evaluator="jev",
                evaluator_version="1.13.0",
                distribution=(("YES", 0.8), ("NO", 0.2)),
            ),
        ),
    )


def test_observation_retains_provenance_without_claiming_truth() -> None:
    record = ObservationRecord(
        observation_id="obs:1",
        subject_id="org:b",
        source_ref="source:official",
        source_type="WEB",
        observed_at=NOW,
        content_fingerprint="sha256",
        mode=ObservationMode.DETERMINISTIC_SENSOR,
    )
    assert record.mode is ObservationMode.DETERMINISTIC_SENSOR


def test_observation_plan_separates_sensor_and_active_research() -> None:
    plan = ObservationPlan(
        plan_id="plan:1",
        subject_id="xeed:a",
        version="1",
        tasks=(
            ObservationTask("task:1", "xeed:a", ObservationMode.DETERMINISTIC_SENSOR, "Fetch feed"),
            ObservationTask(
                "task:2", "xeed:a", ObservationMode.ACTIVE_RESEARCH, "Resolve ambiguity"
            ),
        ),
    )
    assert {task.mode for task in plan.tasks} == {
        ObservationMode.DETERMINISTIC_SENSOR,
        ObservationMode.ACTIVE_RESEARCH,
    }


def test_noul_dimension_cannot_fake_mutual_exclusivity() -> None:
    with pytest.raises(ValueError, match="mutual exclusivity"):
        TypingDimensionContract(
            "ROLE",
            "1",
            "role",
            SemanticPrimitive.NOUL,
            "Is this a role?",
            (),
            (),
            True,
            "ABSTAIN",
        )


def test_non_answerable_dimension_cannot_fabricate_jev_output() -> None:
    with pytest.raises(ValueError, match="fabricate"):
        DimensionEvaluation(
            dimension_id="CUSTOMER_ROLE",
            contract_fingerprint="contract",
            disposition=DimensionDisposition.NOT_ANSWERABLE,
            evaluator="jev",
            evaluator_version="1",
            distribution=(("YES", 0.5), ("NO", 0.5)),
            reason="missing current demand",
        )


def test_state_change_re_evaluates_only_dependent_dimensions() -> None:
    contracts = (
        _dimension("SUPPLIER_ROLE", "supply_evidence"),
        _dimension("CUSTOMER_ROLE", "demand_evidence", "tenders"),
        _dimension("NEED_CLASS", "tenders"),
    )
    change = StateChange(
        subject_id="org:b",
        changed_fields=frozenset({"tenders"}),
        previous_fingerprint="state-1",
        current_fingerprint="state-2",
    )
    assert affected_dimensions(change, contracts) == ("CUSTOMER_ROLE", "NEED_CLASS")


def test_association_snapshot_is_temporal_and_state_consistent() -> None:
    snapshot = EconomicAssociationSnapshot(
        association_id="assoc:1",
        xeed_id="xeed:a",
        candidate_id="org:b",
        state_fingerprint="state-2",
        judgment_vector=_vector(),
        valid_at=NOW,
        previous_snapshot_ref="assoc:0",
    )
    assert snapshot.previous_snapshot_ref == "assoc:0"


def test_typed_vector_allows_simultaneous_independent_roles() -> None:
    vector = TypedJudgmentVector(
        subject_id="xeed:a",
        candidate_id="org:b",
        state_fingerprint="state",
        evaluated_at=NOW,
        evaluations=(
            DimensionEvaluation(
                "SUPPLIER_ROLE",
                "c1",
                DimensionDisposition.ANSWERABLE,
                "jev",
                "1",
                (("YES", 0.9), ("NO", 0.1)),
            ),
            DimensionEvaluation(
                "CUSTOMER_ROLE",
                "c2",
                DimensionDisposition.ANSWERABLE,
                "jev",
                "1",
                (("YES", 0.8), ("NO", 0.2)),
            ),
        ),
    )
    assert {item.dimension_id for item in vector.evaluations} == {"SUPPLIER_ROLE", "CUSTOMER_ROLE"}


def test_xignal_score_is_epistemic_not_sale_probability() -> None:
    profile = EpistemicProfile(0.8, 0.9, 0.7, 0.6, 0.1, 0.75)
    xignal = XignalPresentation(
        xignal_id="xignal:1",
        subject_id="xeed:a",
        candidate_id="org:b",
        attention=AttentionDisposition.WARRANTED_ATTENTION,
        epistemic_profile=profile,
        explanation_ref="trace:1",
        policy_version="attention.v1",
    )
    assert xignal.sale_probability is None
    with pytest.raises(ValueError, match="sale probability"):
        XignalPresentation(
            "xignal:2",
            "xeed:a",
            "org:b",
            AttentionDisposition.WARRANTED_ATTENTION,
            profile,
            "trace:2",
            "attention.v1",
            0.8,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("distribution", "selected", "message"),
    [
        ((("YES", 0.8), ("NO", 0.8)), None, "sum to one"),
        ((("YES", 0.5), ("NO", 0.5)), "MAYBE", "present in its distribution"),
    ],
)
def test_answerable_dimension_rejects_output_outside_its_answer_space(
    distribution: tuple[tuple[str, float], ...], selected: str | None, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        DimensionEvaluation(
            dimension_id="CUSTOMER_ROLE",
            contract_fingerprint="contract",
            disposition=DimensionDisposition.ANSWERABLE,
            evaluator="jev",
            evaluator_version="1.13.0",
            distribution=distribution,
            selected_option=selected,
        )


def test_deterministic_selection_without_distribution_remains_valid() -> None:
    evaluation = DimensionEvaluation(
        dimension_id="CUSTOMER_ROLE",
        contract_fingerprint="contract",
        disposition=DimensionDisposition.ANSWERABLE,
        evaluator="python",
        evaluator_version="1",
        selected_option="UNKNOWN",
    )
    assert evaluation.distribution == ()
