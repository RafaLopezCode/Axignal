"""AO-24 governed KPI and measurement registry domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,239}$")


class MeasurementUnit(StrEnum):
    COUNT = "COUNT"
    RATIO = "RATIO"
    CURRENCY = "CURRENCY"
    DURATION_MS = "DURATION_MS"
    SCALAR = "SCALAR"
    STATUS = "STATUS"


class MeasurementState(StrEnum):
    MEASURED = "MEASURED"
    NOT_MEASURED = "NOT_MEASURED"
    INSUFFICIENT = "INSUFFICIENT"


class MeasurementFreshness(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    NOT_MEASURED = "NOT_MEASURED"


class MeasurementComparisonState(StrEnum):
    COMPARABLE = "COMPARABLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class MeasurementInstrumentAuthority:
    integration_id: str
    source_family: str
    instrument_id: str

    def __post_init__(self) -> None:
        _identifier(self.integration_id, "integration_id")
        _text(self.source_family, "source_family")
        _identifier(self.instrument_id, "instrument_id")


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded opaque identifier")


def _text(value: str, name: str, *, maximum: int = 2000) -> None:
    if not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be non-empty and bounded")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class MeasurementDefinition:
    measure_id: str
    version: int
    label: str
    question_served: str
    decision_served: str
    formula_or_coding_rule: str
    unit: MeasurementUnit
    source_family: str
    instrument_id: str
    instrument_version: str
    subject_scope: str
    default_window: str
    freshness_seconds: int
    minimum_sample_size: int
    uncertainty_policy: str
    compatibility_key: str
    interpretation_limits: tuple[str, ...]
    evaluation_cases: tuple[str, ...]
    effective_at: datetime

    def __post_init__(self) -> None:
        _identifier(self.measure_id, "measure_id")
        if self.version < 1:
            raise ValueError("measurement definition version must be >= 1")
        for value, name in (
            (self.instrument_id, "instrument_id"),
            (self.instrument_version, "instrument_version"),
            (self.compatibility_key, "compatibility_key"),
        ):
            _identifier(value, name)
        for value, name in (
            (self.label, "label"),
            (self.question_served, "question_served"),
            (self.decision_served, "decision_served"),
            (self.formula_or_coding_rule, "formula_or_coding_rule"),
            (self.source_family, "source_family"),
            (self.subject_scope, "subject_scope"),
            (self.default_window, "default_window"),
            (self.uncertainty_policy, "uncertainty_policy"),
        ):
            _text(value, name)
        if self.freshness_seconds < 1:
            raise ValueError("freshness_seconds must be positive")
        if self.minimum_sample_size < 1:
            raise ValueError("minimum_sample_size must be positive")
        if not self.interpretation_limits:
            raise ValueError("measurement definition requires interpretation limits")
        if not self.evaluation_cases:
            raise ValueError("measurement definition requires evaluation cases")
        for value in (*self.interpretation_limits, *self.evaluation_cases):
            _text(value, "measurement definition list item", maximum=1000)
        _aware(self.effective_at, "effective_at")


@dataclass(frozen=True, slots=True)
class MeasurementObservation:
    observation_id: str
    measure_id: str
    definition_version: int
    subject_ref: str
    instrument_id: str
    instrument_version: str
    compatibility_key: str
    state: MeasurementState
    observed_at: datetime
    window_start: datetime
    window_end: datetime
    sample_size: int | None
    informative_sample_size: int | None
    value: str | None
    currency: str | None
    uncertainty: str
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.observation_id, "observation_id"),
            (self.measure_id, "measure_id"),
            (self.subject_ref, "subject_ref"),
            (self.instrument_id, "instrument_id"),
            (self.instrument_version, "instrument_version"),
            (self.compatibility_key, "compatibility_key"),
        ):
            _identifier(value, name)
        if self.definition_version < 1:
            raise ValueError("definition_version must be >= 1")
        _aware(self.observed_at, "observed_at")
        _aware(self.window_start, "window_start")
        _aware(self.window_end, "window_end")
        if self.window_end < self.window_start:
            raise ValueError("measurement window end cannot precede start")
        if self.sample_size is not None and self.sample_size < 0:
            raise ValueError("sample_size cannot be negative")
        if self.informative_sample_size is not None and self.informative_sample_size < 0:
            raise ValueError("informative_sample_size cannot be negative")
        if (
            self.sample_size is not None
            and self.informative_sample_size is not None
            and self.informative_sample_size > self.sample_size
        ):
            raise ValueError("informative sample cannot exceed sample size")
        if self.state is MeasurementState.MEASURED and self.value is None:
            raise ValueError("MEASURED observation requires a value")
        if self.state is not MeasurementState.MEASURED and self.value is not None:
            raise ValueError("NOT_MEASURED/INSUFFICIENT observation cannot carry a value")
        if self.currency is not None and (len(self.currency) != 3 or not self.currency.isalpha()):
            raise ValueError("currency must be ISO-like three letters")
        _text(self.uncertainty, "uncertainty")
        if not self.source_refs:
            raise ValueError("measurement observation requires source references")
        for source_ref in self.source_refs:
            _identifier(source_ref, "source_ref")


@dataclass(frozen=True, slots=True)
class MeasurementReadout:
    observation: MeasurementObservation
    freshness: MeasurementFreshness
    usable: bool
    reason: str


@dataclass(frozen=True, slots=True)
class MeasurementComparison:
    earlier_observation_id: str
    later_observation_id: str
    state: MeasurementComparisonState
    reason: str


@dataclass(frozen=True, slots=True)
class MeasurementRegistryProjection:
    generated_at: datetime
    privacy_class: str
    definitions: tuple[MeasurementDefinition, ...]
    readouts: tuple[MeasurementReadout, ...]
    coverage_notes: tuple[str, ...]
