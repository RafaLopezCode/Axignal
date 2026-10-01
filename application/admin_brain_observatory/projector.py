"""AO-06 deterministic AXENT / Brain / provider observatory projection."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from application.economic_discovery.execution_budget import ExecutionStopReason
from application.economic_discovery.learning_memory import (
    LearningEvent,
    LearningMechanism,
    LearningOutcome,
)
from domain.admin_brain_observatory import (
    BrainControlState,
    BrainProviderObservatory,
    ProviderUsageSlice,
)
from domain.admin_observability import AdminEventEnvelope, DataCompleteness

_CONTROL_TYPES: tuple[tuple[str, str, str], ...] = (
    ("research_objective", "brain.research_objective", "RESEARCH_OBJECTIVE_STATE_UNAVAILABLE"),
    ("routing", "brain.routing", "BRAIN_ROUTING_STATE_UNAVAILABLE"),
    ("stop", "brain.stop", "RESEARCH_STOP_STATE_UNAVAILABLE"),
    ("budget", "brain.budget", "RESEARCH_BUDGET_STATE_UNAVAILABLE"),
    ("no_progress", "brain.no_progress", "NO_PROGRESS_STATE_UNAVAILABLE"),
    ("retry", "brain.retry", "RETRY_STATE_UNAVAILABLE"),
    ("abstention", "brain.abstention", "ABSTENTION_STATE_UNAVAILABLE"),
    ("knowledge_frontier", "brain.knowledge_frontier", "KNOWLEDGE_FRONTIER_STATE_UNAVAILABLE"),
    ("unresolved_gap", "brain.unresolved_gap", "UNRESOLVED_GAP_STATE_UNAVAILABLE"),
)


def _latest(records: tuple[AdminEventEnvelope, ...], record_type: str) -> AdminEventEnvelope | None:
    matches = [record for record in records if record.record_type == record_type]
    return max(matches, key=lambda item: (item.recorded_at, str(item.record_id)), default=None)


def _state(
    records: tuple[AdminEventEnvelope, ...],
    record_type: str,
    *,
    default_reason: str,
) -> tuple[str | None, DataCompleteness, str | None, tuple[str, ...]]:
    record = _latest(records, record_type)
    if record is None:
        return None, DataCompleteness.UNKNOWN, default_reason, ()
    return (
        record.outcome_state,
        record.completeness,
        record.unknown_reason,
        (str(record.record_id),),
    )


def _coverage(known: int, total: int) -> DataCompleteness:
    if total == 0 or known == 0:
        return DataCompleteness.UNKNOWN
    if known == total:
        return DataCompleteness.KNOWN
    return DataCompleteness.PARTIAL


def _known_costs(events: tuple[LearningEvent, ...]) -> tuple[tuple[str, int], ...]:
    totals: dict[str, int] = {}
    for event in events:
        if event.cost.amount_microunits is None:
            continue
        assert event.cost.currency is not None
        totals[event.cost.currency] = (
            totals.get(event.cost.currency, 0) + event.cost.amount_microunits
        )
    return tuple(sorted(totals.items()))


def _provider_slice(events: tuple[LearningEvent, ...]) -> ProviderUsageSlice:
    first = events[0]
    assert first.provider is not None
    assert first.provider_version is not None
    costs = _known_costs(events)
    latency_values = tuple(
        event.cost.latency_ms for event in events if event.cost.latency_ms is not None
    )
    input_values = tuple(
        event.cost.input_units for event in events if event.cost.input_units is not None
    )
    output_values = tuple(
        event.cost.output_units for event in events if event.cost.output_units is not None
    )
    return ProviderUsageSlice(
        provider=first.provider,
        provider_version=first.provider_version,
        operation_class=first.kind.value,
        policy_id=first.policy_id,
        policy_version=first.policy_version,
        comparison_key=f"{first.kind.value}|{first.policy_id}|{first.policy_version}",
        event_count=len(events),
        completed_count=sum(event.outcome is LearningOutcome.COMPLETED for event in events),
        partial_count=sum(event.outcome is LearningOutcome.PARTIAL for event in events),
        no_change_count=sum(event.outcome is LearningOutcome.NO_CHANGE for event in events),
        failed_count=sum(event.outcome is LearningOutcome.FAILED for event in events),
        known_costs_by_currency=costs,
        unknown_cost_event_count=sum(event.cost.amount_microunits is None for event in events),
        cost_completeness=_coverage(
            sum(event.cost.amount_microunits is not None for event in events),
            len(events),
        ),
        known_latency_event_count=len(latency_values),
        total_latency_ms=sum(latency_values),
        average_latency_ms=(
            None if not latency_values else sum(latency_values) // len(latency_values)
        ),
        latency_completeness=_coverage(len(latency_values), len(events)),
        known_input_unit_event_count=len(input_values),
        known_output_unit_event_count=len(output_values),
        total_input_units=sum(input_values),
        total_output_units=sum(output_values),
        semantic_judgments_produced=sum(
            event.yield_.semantic_judgments_produced for event in events
        ),
        research_objectives_resolved=sum(
            event.yield_.research_objectives_resolved for event in events
        ),
        useful_output_event_count=sum(event.yield_.total_observed_output > 0 for event in events),
        source_learning_event_ids=tuple(event.event_id for event in events),
    )


def _control_state(
    records: tuple[AdminEventEnvelope, ...],
    events: tuple[LearningEvent, ...],
) -> BrainControlState:
    states: dict[
        str,
        tuple[str | None, DataCompleteness, str | None, tuple[str, ...]],
    ] = {
        key: _state(records, record_type, default_reason=default_reason)
        for key, record_type, default_reason in _CONTROL_TYPES
    }
    learning_ids: set[str] = set()

    cognitive_events = tuple(
        event
        for event in events
        if event.mechanism
        in {LearningMechanism.STRUCTURED_EVALUATOR, LearningMechanism.ADAPTIVE_RESEARCH}
    )
    latest_cognitive = (
        max(cognitive_events, key=lambda event: (event.occurred_at, event.event_id))
        if cognitive_events
        else None
    )
    if states["routing"][0] is None and latest_cognitive is not None:
        states["routing"] = (
            latest_cognitive.mechanism.value,
            DataCompleteness.KNOWN,
            "LEARNING_EVENT_EXECUTED_ROUTE",
            (),
        )
        learning_ids.add(latest_cognitive.event_id)

    stop_values = {reason.value for reason in ExecutionStopReason}
    stop_events = tuple(event for event in events if event.reason_code in stop_values)
    latest_stop = (
        max(stop_events, key=lambda event: (event.occurred_at, event.event_id))
        if stop_events
        else None
    )
    if latest_stop is not None:
        learning_ids.add(latest_stop.event_id)
        if states["stop"][0] is None:
            states["stop"] = (
                latest_stop.reason_code,
                DataCompleteness.KNOWN,
                "LEARNING_EVENT_EXECUTION_STOP",
                (),
            )
        if states["budget"][0] is None and latest_stop.reason_code in {
            ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED.value,
            ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED.value,
            ExecutionStopReason.SOURCE_BUDGET_EXHAUSTED.value,
        }:
            states["budget"] = (
                "EXHAUSTED",
                DataCompleteness.KNOWN,
                latest_stop.reason_code,
                (),
            )
        if (
            states["budget"][0] is None
            and latest_stop.reason_code == ExecutionStopReason.COST_UNKNOWN.value
        ):
            states["budget"] = (
                "BLOCKED_UNKNOWN_COST",
                DataCompleteness.KNOWN,
                latest_stop.reason_code,
                (),
            )
        if (
            states["no_progress"][0] is None
            and latest_stop.reason_code == ExecutionStopReason.NO_PROGRESS.value
        ):
            states["no_progress"] = (
                "STOPPED_NO_PROGRESS",
                DataCompleteness.KNOWN,
                latest_stop.reason_code,
                (),
            )
        if (
            states["retry"][0] is None
            and latest_stop.reason_code == ExecutionStopReason.RETRY_LIMIT_REACHED.value
        ):
            states["retry"] = (
                "LIMIT_REACHED",
                DataCompleteness.KNOWN,
                latest_stop.reason_code,
                (),
            )

    source_ids = tuple(sorted({source_id for _, _, _, ids in states.values() for source_id in ids}))
    research_objective = states["research_objective"]
    routing = states["routing"]
    stop = states["stop"]
    budget = states["budget"]
    no_progress = states["no_progress"]
    retry = states["retry"]
    abstention = states["abstention"]
    knowledge_frontier = states["knowledge_frontier"]
    unresolved_gap = states["unresolved_gap"]
    return BrainControlState(
        research_objective_state=research_objective[0],
        research_objective_completeness=research_objective[1],
        research_objective_reason=research_objective[2],
        routing_state=routing[0],
        routing_completeness=routing[1],
        routing_reason=routing[2],
        stop_state=stop[0],
        stop_completeness=stop[1],
        stop_reason=stop[2],
        budget_state=budget[0],
        budget_completeness=budget[1],
        budget_reason=budget[2],
        no_progress_state=no_progress[0],
        no_progress_completeness=no_progress[1],
        no_progress_reason=no_progress[2],
        retry_state=retry[0],
        retry_completeness=retry[1],
        retry_reason=retry[2],
        abstention_state=abstention[0],
        abstention_completeness=abstention[1],
        abstention_reason=abstention[2],
        knowledge_frontier_state=knowledge_frontier[0],
        knowledge_frontier_completeness=knowledge_frontier[1],
        knowledge_frontier_reason=knowledge_frontier[2],
        unresolved_gap_state=unresolved_gap[0],
        unresolved_gap_completeness=unresolved_gap[1],
        unresolved_gap_reason=unresolved_gap[2],
        source_admin_record_ids=source_ids,
        source_learning_event_ids=tuple(sorted(learning_ids)),
    )


def project_brain_provider_observatory(
    *,
    learning_events: tuple[LearningEvent, ...],
    admin_records: tuple[AdminEventEnvelope, ...],
    as_of: datetime,
    generated_at: datetime,
) -> BrainProviderObservatory:
    """Project operational cognition without promoting provider output to truth."""

    eligible_events = tuple(
        sorted(
            (event for event in learning_events if event.occurred_at <= as_of),
            key=lambda event: (event.occurred_at, event.event_id),
        )
    )
    eligible_records = tuple(record for record in admin_records if record.recorded_at <= as_of)
    cognitive = tuple(
        event
        for event in eligible_events
        if event.provider is not None
        or event.mechanism
        in {LearningMechanism.STRUCTURED_EVALUATOR, LearningMechanism.ADAPTIVE_RESEARCH}
    )

    by_slice: dict[tuple[str, str, str, str, str], list[LearningEvent]] = defaultdict(list)
    for event in eligible_events:
        if event.provider is None:
            continue
        assert event.provider_version is not None
        key = (
            event.provider,
            event.provider_version,
            event.kind.value,
            event.policy_id,
            event.policy_version,
        )
        by_slice[key].append(event)
    provider_slices = tuple(_provider_slice(tuple(by_slice[key])) for key in sorted(by_slice))

    latency_values = tuple(
        event.cost.latency_ms for event in eligible_events if event.cost.latency_ms is not None
    )
    known_cost_count = sum(event.cost.amount_microunits is not None for event in eligible_events)
    control = _control_state(eligible_records, eligible_events)
    control_completeness = (
        DataCompleteness.KNOWN
        if all(
            getattr(control, f"{key}_completeness") is DataCompleteness.KNOWN
            for key, _, _ in _CONTROL_TYPES
        )
        else DataCompleteness.PARTIAL
    )
    overall = (
        DataCompleteness.KNOWN
        if eligible_events and control_completeness is DataCompleteness.KNOWN
        else DataCompleteness.PARTIAL
    )

    return BrainProviderObservatory(
        as_of=as_of,
        generated_at=generated_at,
        completeness=overall,
        learning_event_count=len(eligible_events),
        cognitive_event_count=len(cognitive),
        deterministic_event_count=sum(
            event.mechanism is LearningMechanism.DETERMINISTIC for event in eligible_events
        ),
        structured_evaluator_event_count=sum(
            event.mechanism is LearningMechanism.STRUCTURED_EVALUATOR for event in eligible_events
        ),
        adaptive_research_event_count=sum(
            event.mechanism is LearningMechanism.ADAPTIVE_RESEARCH for event in eligible_events
        ),
        governance_event_count=sum(
            event.mechanism is LearningMechanism.GOVERNANCE for event in eligible_events
        ),
        completed_event_count=sum(
            event.outcome is LearningOutcome.COMPLETED for event in eligible_events
        ),
        partial_event_count=sum(
            event.outcome is LearningOutcome.PARTIAL for event in eligible_events
        ),
        no_change_event_count=sum(
            event.outcome is LearningOutcome.NO_CHANGE for event in eligible_events
        ),
        failed_event_count=sum(
            event.outcome is LearningOutcome.FAILED for event in eligible_events
        ),
        provider_attributed_event_count=sum(
            event.provider is not None for event in eligible_events
        ),
        provider_unattributed_cognitive_event_count=sum(
            event.provider is None for event in cognitive
        ),
        known_costs_by_currency=_known_costs(eligible_events),
        unknown_cost_event_count=len(eligible_events) - known_cost_count,
        cost_completeness=_coverage(known_cost_count, len(eligible_events)),
        known_latency_event_count=len(latency_values),
        total_latency_ms=sum(latency_values),
        average_latency_ms=(
            None if not latency_values else sum(latency_values) // len(latency_values)
        ),
        latency_completeness=_coverage(len(latency_values), len(eligible_events)),
        semantic_judgments_produced=sum(
            event.yield_.semantic_judgments_produced for event in eligible_events
        ),
        research_objectives_resolved=sum(
            event.yield_.research_objectives_resolved for event in eligible_events
        ),
        useful_output_event_count=sum(
            event.yield_.total_observed_output > 0 for event in eligible_events
        ),
        provider_slices=provider_slices,
        control=control,
        source_learning_event_ids=tuple(event.event_id for event in eligible_events),
        coverage_notes=(
            "Provider/model identity is mutable execution policy, never AXIGNAL truth authority.",
            "Provider comparisons are compatible only when comparison_key matches operation class and policy version.",
            "Useful output is observed yield cardinality, not correctness, quality, commercial value or epistemic validity.",
            "Missing cost, latency, retry, abstention, budget or frontier evidence remains UNKNOWN rather than zero.",
            "Commercial outcomes are intentionally excluded from cognitive correctness and provider comparison.",
        ),
    )
