"""Semantic model for AO-04 Command Center projections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.admin_observability import AdminProjectionId, AdminRecordId, DataCompleteness


class AdminMetricUnit(StrEnum):
    CURRENCY = "CURRENCY"
    COUNT = "COUNT"
    RATIO = "RATIO"
    STATUS = "STATUS"


@dataclass(frozen=True, slots=True)
class AdminMetricDefinition:
    metric_id: str
    label: str
    group: str
    purpose: str
    unit: AdminMetricUnit
    source_projection_id: AdminProjectionId
    source_value_key: str
    methodology_version: str
    source_record_types: tuple[str, ...]
    default_window: str

    def __post_init__(self) -> None:
        for name, value in (
            ("metric_id", self.metric_id),
            ("label", self.label),
            ("group", self.group),
            ("purpose", self.purpose),
            ("source_value_key", self.source_value_key),
            ("methodology_version", self.methodology_version),
            ("default_window", self.default_window),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.source_record_types:
            raise ValueError("source_record_types are required")


@dataclass(frozen=True, slots=True)
class AdminMetricReadout:
    definition: AdminMetricDefinition
    completeness: DataCompleteness
    value: str | None
    currency: str | None
    period_start: datetime | None
    period_end: datetime | None
    observed_methodology_version: str | None
    source_record_ids: tuple[AdminRecordId, ...]
    unknown_reason: str | None
    comparison_state: str
    previous_value: str | None = None

    def __post_init__(self) -> None:
        carries_value = self.completeness in {DataCompleteness.KNOWN, DataCompleteness.PARTIAL}
        if carries_value and self.value is None:
            raise ValueError("KNOWN/PARTIAL metric requires a value")
        if not carries_value and self.value is not None:
            raise ValueError("UNKNOWN/UNAVAILABLE metric cannot carry a value")
        if self.completeness is not DataCompleteness.KNOWN and not self.unknown_reason:
            raise ValueError("non-KNOWN metric requires unknown_reason")
        if self.definition.unit is AdminMetricUnit.CURRENCY and carries_value and not self.currency:
            raise ValueError("known/partial currency metric requires currency")
        if self.definition.unit is not AdminMetricUnit.CURRENCY and self.currency is not None:
            raise ValueError("non-currency metric cannot carry currency")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end cannot precede period_start")


@dataclass(frozen=True, slots=True)
class AdminCommandCenterProjection:
    as_of: datetime
    generated_at: datetime
    completeness: DataCompleteness
    metrics: tuple[AdminMetricReadout, ...]

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        ids = tuple(item.definition.metric_id for item in self.metrics)
        if len(ids) != len(set(ids)):
            raise ValueError("metric ids must be unique")
