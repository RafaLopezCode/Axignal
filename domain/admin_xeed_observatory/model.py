"""AO-05 Xeed and AXIGLAND observatory semantic model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.admin_observability import DataCompleteness


@dataclass(frozen=True, slots=True)
class XeedRuntimeDiagnostic:
    xeed_id: str
    subject_ids: tuple[str, ...]
    lifecycle_state: str | None
    lifecycle_completeness: DataCompleteness
    lifecycle_reason: str | None
    currentness_state: str | None
    currentness_completeness: DataCompleteness
    currentness_reason: str | None
    observation_coverage_state: str | None
    observation_coverage_completeness: DataCompleteness
    observation_coverage_reason: str | None
    first_activity_at: datetime | None
    last_activity_at: datetime | None
    first_useful_xignal_at: datetime | None
    time_to_first_useful_xignal_ms: int | None
    learning_event_count: int
    failed_event_count: int
    partial_event_count: int
    observations_reused: int
    observations_added: int
    reuse_ratio: str | None
    xignals_emitted: int
    canonical_admissions: int
    known_costs_by_currency: tuple[tuple[str, int], ...]
    unknown_cost_event_count: int
    direct_cost_completeness: DataCompleteness
    shared_cost_completeness: DataCompleteness
    shared_cost_reason: str
    triggered_cost_completeness: DataCompleteness
    triggered_cost_reason: str
    revenue_attribution_completeness: DataCompleteness
    revenue_attribution_reason: str
    source_learning_event_ids: tuple[str, ...]
    source_admin_record_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AxiglandRuntimeDiagnostic:
    completeness: DataCompleteness
    canonical_admission_events: int
    observations_reused: int
    observations_added: int
    reuse_ratio: str | None
    growth_state: str | None
    growth_completeness: DataCompleteness
    contradiction_state: str | None
    contradiction_completeness: DataCompleteness
    identity_resolution_state: str | None
    identity_resolution_completeness: DataCompleteness
    currentness_state: str | None
    currentness_completeness: DataCompleteness
    provenance_state: str | None
    provenance_completeness: DataCompleteness
    source_learning_event_ids: tuple[str, ...]
    source_admin_record_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class XeedAxiglandObservatory:
    as_of: datetime
    generated_at: datetime
    completeness: DataCompleteness
    xeeds: tuple[XeedRuntimeDiagnostic, ...]
    axigland: AxiglandRuntimeDiagnostic
    coverage_notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        ids = tuple(item.xeed_id for item in self.xeeds)
        if len(ids) != len(set(ids)):
            raise ValueError("Xeed diagnostics require unique Xeed identities")
