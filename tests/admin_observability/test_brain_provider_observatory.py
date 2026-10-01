from datetime import UTC, datetime, timedelta

from application.admin_brain_observatory import project_brain_provider_observatory
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
)
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)

NOW = datetime(2026, 10, 1, 22, 0, tzinfo=UTC)


def _event(
    event_id: str,
    *,
    mechanism: LearningMechanism = LearningMechanism.DETERMINISTIC,
    kind: LearningEventKind = LearningEventKind.DETERMINISTIC_EVALUATION,
    outcome: LearningOutcome = LearningOutcome.COMPLETED,
    provider: str | None = None,
    provider_version: str | None = None,
    policy_id: str = "policy",
    policy_version: str = "1",
    cost: int | None = None,
    latency_ms: int | None = None,
    input_units: int | None = None,
    output_units: int | None = None,
    judgments: int = 0,
    objectives: int = 0,
    reason_code: str = "TEST_REASON",
    occurred_at: datetime = NOW,
) -> LearningEvent:
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=outcome,
        occurred_at=occurred_at,
        subject_id="org:brain",
        activity_ref=f"activity:{event_id}",
        policy_id=policy_id,
        policy_version=policy_version,
        code_sha="a" * 40,
        mechanism=mechanism,
        input_fingerprint=f"input:{event_id}",
        reason_code=reason_code,
        xeed_id="xeed:brain",
        provider=provider,
        provider_version=provider_version,
        cost=LearningCost(
            amount_microunits=cost,
            currency=None if cost is None else "EUR",
            latency_ms=latency_ms,
            input_units=input_units,
            output_units=output_units,
        ),
        yield_=LearningYield(
            semantic_judgments_produced=judgments,
            research_objectives_resolved=objectives,
        ),
    )


def _record(
    record_id: str,
    record_type: str,
    state: str,
    *,
    completeness: DataCompleteness = DataCompleteness.KNOWN,
    unknown_reason: str | None = None,
    recorded_at: datetime = NOW,
) -> AdminEventEnvelope:
    return AdminEventEnvelope(
        record_id=AdminRecordId(record_id),
        record_type=record_type,
        record_class=AdminRecordClass.OPERATIONAL_EVENT,
        schema_version=1,
        producer="brain-owner",
        owning_domain="research",
        recorded_at=recorded_at,
        outcome_state=state,
        completeness=completeness,
        privacy_class=AdminPrivacyClass.INTERNAL,
        provenance_refs=(f"source:{record_id}",),
        unknown_reason=unknown_reason,
    )


def test_provider_slices_compare_only_compatible_operation_and_policy() -> None:
    events = (
        _event(
            "p1",
            mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
            kind=LearningEventKind.STRUCTURED_EVALUATION,
            provider="provider-a",
            provider_version="model-1",
            cost=100,
            latency_ms=80,
            judgments=1,
        ),
        _event(
            "p2",
            mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
            kind=LearningEventKind.STRUCTURED_EVALUATION,
            provider="provider-b",
            provider_version="model-2",
            cost=200,
            latency_ms=120,
            judgments=1,
        ),
        _event(
            "different-policy",
            mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
            kind=LearningEventKind.STRUCTURED_EVALUATION,
            provider="provider-a",
            provider_version="model-1",
            policy_version="2",
            judgments=1,
        ),
    )
    result = project_brain_provider_observatory(
        learning_events=events,
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    assert len(result.provider_slices) == 3
    matching = [item for item in result.provider_slices if item.policy_version == "1"]
    assert {item.provider for item in matching} == {"provider-a", "provider-b"}
    assert len({item.comparison_key for item in matching}) == 1
    assert (
        next(item for item in result.provider_slices if item.policy_version == "2").comparison_key
        != matching[0].comparison_key
    )


def test_unknown_cost_latency_and_provider_are_not_zero_or_free() -> None:
    event = _event(
        "unknown",
        mechanism=LearningMechanism.ADAPTIVE_RESEARCH,
        kind=LearningEventKind.ADAPTIVE_RESEARCH,
    )
    result = project_brain_provider_observatory(
        learning_events=(event,),
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.cognitive_event_count == 1
    assert result.provider_unattributed_cognitive_event_count == 1
    assert result.provider_slices == ()
    assert result.unknown_cost_event_count == 1
    assert result.cost_completeness is DataCompleteness.UNKNOWN
    assert result.average_latency_ms is None
    assert result.latency_completeness is DataCompleteness.UNKNOWN


def test_failure_and_abstention_remain_separate_first_class_states() -> None:
    failed = _event(
        "failed",
        mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
        kind=LearningEventKind.STRUCTURED_EVALUATION,
        outcome=LearningOutcome.FAILED,
        provider="jev-like",
        provider_version="v1",
    )
    abstention = _record("abstain-1", "brain.abstention", "INSUFFICIENT_EVIDENCE")
    result = project_brain_provider_observatory(
        learning_events=(failed,),
        admin_records=(abstention,),
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.failed_event_count == 1
    assert result.control.abstention_state == "INSUFFICIENT_EVIDENCE"
    assert result.control.abstention_completeness is DataCompleteness.KNOWN
    assert result.control.stop_state is None
    assert result.control.stop_completeness is DataCompleteness.UNKNOWN


def test_budget_stop_frontier_and_no_progress_require_owner_records() -> None:
    records = (
        _record("budget", "brain.budget", "EXHAUSTED"),
        _record("stop", "brain.stop", "BUDGET_EXHAUSTED"),
        _record("np", "brain.no_progress", "3_CONSECUTIVE"),
        _record("frontier", "brain.knowledge_frontier", "OPEN"),
        _record("gap", "brain.unresolved_gap", "gap:market-evidence"),
    )
    result = project_brain_provider_observatory(
        learning_events=(),
        admin_records=records,
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.control.budget_state == "EXHAUSTED"
    assert result.control.stop_state == "BUDGET_EXHAUSTED"
    assert result.control.no_progress_state == "3_CONSECUTIVE"
    assert result.control.knowledge_frontier_state == "OPEN"
    assert result.control.unresolved_gap_state == "gap:market-evidence"
    assert set(result.control.source_admin_record_ids) == {
        "budget",
        "stop",
        "np",
        "frontier",
        "gap",
    }


def test_commercial_records_cannot_relabel_cognitive_correctness_and_future_is_excluded() -> None:
    current = _event(
        "current",
        mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
        kind=LearningEventKind.STRUCTURED_EVALUATION,
        provider="provider-a",
        provider_version="model",
        judgments=1,
    )
    future = _event(
        "future",
        mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
        kind=LearningEventKind.STRUCTURED_EVALUATION,
        provider="provider-a",
        provider_version="model",
        judgments=99,
        occurred_at=NOW + timedelta(hours=1),
    )
    commercial = _record("sale", "customer.subscription", "PAID")
    result = project_brain_provider_observatory(
        learning_events=(current, future),
        admin_records=(commercial,),
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.learning_event_count == 1
    assert result.semantic_judgments_produced == 1
    assert result.control.source_admin_record_ids == ()
    assert all("sale" not in item.source_learning_event_ids for item in result.provider_slices)


def test_learning_stop_evidence_fills_control_state_without_shadow_event() -> None:
    stop = _event(
        "stop",
        mechanism=LearningMechanism.ADAPTIVE_RESEARCH,
        kind=LearningEventKind.ADAPTIVE_RESEARCH,
        outcome=LearningOutcome.PARTIAL,
        reason_code="NO_PROGRESS",
    )
    result = project_brain_provider_observatory(
        learning_events=(stop,),
        admin_records=(),
        as_of=NOW,
        generated_at=NOW,
    )

    assert result.control.routing_state == "ADAPTIVE_RESEARCH"
    assert result.control.stop_state == "NO_PROGRESS"
    assert result.control.no_progress_state == "STOPPED_NO_PROGRESS"
    assert result.control.source_learning_event_ids == ("stop",)
