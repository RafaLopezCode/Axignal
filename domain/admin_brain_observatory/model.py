"""AO-06 AXENT / Brain / provider observatory semantic model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.admin_observability import DataCompleteness


@dataclass(frozen=True, slots=True)
class ProviderUsageSlice:
    provider: str
    provider_version: str
    operation_class: str
    policy_id: str
    policy_version: str
    comparison_key: str
    event_count: int
    completed_count: int
    partial_count: int
    no_change_count: int
    failed_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]
    unknown_cost_event_count: int
    cost_completeness: DataCompleteness
    known_latency_event_count: int
    total_latency_ms: int
    average_latency_ms: int | None
    latency_completeness: DataCompleteness
    known_input_unit_event_count: int
    known_output_unit_event_count: int
    total_input_units: int
    total_output_units: int
    semantic_judgments_produced: int
    research_objectives_resolved: int
    useful_output_event_count: int
    source_learning_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("provider", self.provider),
            ("provider_version", self.provider_version),
            ("operation_class", self.operation_class),
            ("policy_id", self.policy_id),
            ("policy_version", self.policy_version),
            ("comparison_key", self.comparison_key),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if self.event_count < 1:
            raise ValueError("provider slice requires at least one event")
        if self.known_latency_event_count > self.event_count:
            raise ValueError("known latency count cannot exceed event count")
        if self.known_input_unit_event_count > self.event_count:
            raise ValueError("known input-unit count cannot exceed event count")
        if self.known_output_unit_event_count > self.event_count:
            raise ValueError("known output-unit count cannot exceed event count")
        if len(self.source_learning_event_ids) != len(set(self.source_learning_event_ids)):
            raise ValueError("provider lineage ids must be unique")


@dataclass(frozen=True, slots=True)
class BrainControlState:
    research_objective_state: str | None
    research_objective_completeness: DataCompleteness
    research_objective_reason: str | None
    routing_state: str | None
    routing_completeness: DataCompleteness
    routing_reason: str | None
    stop_state: str | None
    stop_completeness: DataCompleteness
    stop_reason: str | None
    budget_state: str | None
    budget_completeness: DataCompleteness
    budget_reason: str | None
    no_progress_state: str | None
    no_progress_completeness: DataCompleteness
    no_progress_reason: str | None
    retry_state: str | None
    retry_completeness: DataCompleteness
    retry_reason: str | None
    abstention_state: str | None
    abstention_completeness: DataCompleteness
    abstention_reason: str | None
    knowledge_frontier_state: str | None
    knowledge_frontier_completeness: DataCompleteness
    knowledge_frontier_reason: str | None
    unresolved_gap_state: str | None
    unresolved_gap_completeness: DataCompleteness
    unresolved_gap_reason: str | None
    source_admin_record_ids: tuple[str, ...]
    source_learning_event_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BrainProviderObservatory:
    as_of: datetime
    generated_at: datetime
    completeness: DataCompleteness
    learning_event_count: int
    cognitive_event_count: int
    deterministic_event_count: int
    structured_evaluator_event_count: int
    adaptive_research_event_count: int
    governance_event_count: int
    completed_event_count: int
    partial_event_count: int
    no_change_event_count: int
    failed_event_count: int
    provider_attributed_event_count: int
    provider_unattributed_cognitive_event_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]
    unknown_cost_event_count: int
    cost_completeness: DataCompleteness
    known_latency_event_count: int
    total_latency_ms: int
    average_latency_ms: int | None
    latency_completeness: DataCompleteness
    semantic_judgments_produced: int
    research_objectives_resolved: int
    useful_output_event_count: int
    provider_slices: tuple[ProviderUsageSlice, ...]
    control: BrainControlState
    source_learning_event_ids: tuple[str, ...]
    coverage_notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        keys = tuple(
            (
                item.provider,
                item.provider_version,
                item.operation_class,
                item.policy_id,
                item.policy_version,
            )
            for item in self.provider_slices
        )
        if len(keys) != len(set(keys)):
            raise ValueError("provider usage slices require unique compatibility identities")
        if len(self.source_learning_event_ids) != len(set(self.source_learning_event_ids)):
            raise ValueError("brain observatory learning lineage ids must be unique")
