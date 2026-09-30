"""Governed append-only Learning Memory for AXIGNAL Prime.

Learning Memory records what AXIGNAL tried, what changed, what it cost and how
later evidence corrected prior operational conclusions. It is not canonical
economic truth and it cannot mutate production policy by itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("learning-memory identity and provenance are required")


class LearningEventKind(StrEnum):
    BOOTSTRAP = "BOOTSTRAP"
    SOURCE_ACQUISITION = "SOURCE_ACQUISITION"
    OBSERVATION_INGESTION = "OBSERVATION_INGESTION"
    STRUCTURED_EVALUATION = "STRUCTURED_EVALUATION"
    ADAPTIVE_RESEARCH = "ADAPTIVE_RESEARCH"
    CORRECTION = "CORRECTION"


class LearningOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    NO_CHANGE = "NO_CHANGE"
    FAILED = "FAILED"


class LearningMechanism(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    STRUCTURED_EVALUATOR = "STRUCTURED_EVALUATOR"
    ADAPTIVE_RESEARCH = "ADAPTIVE_RESEARCH"
    GOVERNANCE = "GOVERNANCE"


@dataclass(frozen=True, slots=True)
class LearningCost:
    """Measured operational cost. None means unknown; zero is measured zero."""

    amount_microunits: int | None = None
    currency: str | None = None
    latency_ms: int | None = None
    input_units: int | None = None
    output_units: int | None = None

    def __post_init__(self) -> None:
        if (self.amount_microunits is None) != (self.currency is None):
            raise ValueError("learning cost amount and currency must coexist")
        if self.amount_microunits is not None and self.amount_microunits < 0:
            raise ValueError("learning cost cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("learning cost currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        for value in (self.latency_ms, self.input_units, self.output_units):
            if value is not None and value < 0:
                raise ValueError("learning usage and latency cannot be negative")


@dataclass(frozen=True, slots=True)
class LearningYield:
    """Observable output cardinality. Counts do not imply quality."""

    observations_added: int = 0
    state_fields_changed: int = 0
    dimensions_became_answerable: int = 0
    semantic_judgments_produced: int = 0
    research_objectives_resolved: int = 0
    xignals_emitted: int = 0
    canonical_admissions: int = 0

    def __post_init__(self) -> None:
        values = (
            self.observations_added,
            self.state_fields_changed,
            self.dimensions_became_answerable,
            self.semantic_judgments_produced,
            self.research_objectives_resolved,
            self.xignals_emitted,
            self.canonical_admissions,
        )
        if any(value < 0 for value in values):
            raise ValueError("learning yield counts cannot be negative")

    @property
    def total_observed_output(self) -> int:
        return sum(
            (
                self.observations_added,
                self.state_fields_changed,
                self.dimensions_became_answerable,
                self.semantic_judgments_produced,
                self.research_objectives_resolved,
                self.xignals_emitted,
                self.canonical_admissions,
            )
        )


@dataclass(frozen=True, slots=True)
class LearningEvent:
    event_id: str
    kind: LearningEventKind
    outcome: LearningOutcome
    occurred_at: datetime
    subject_id: str
    activity_ref: str
    policy_id: str
    policy_version: str
    code_sha: str
    mechanism: LearningMechanism
    input_fingerprint: str
    reason_code: str
    xeed_id: str | None = None
    provider: str | None = None
    provider_version: str | None = None
    before_state_fingerprint: str | None = None
    after_state_fingerprint: str | None = None
    output_fingerprint: str | None = None
    corrects_event_id: str | None = None
    cost: LearningCost = LearningCost()
    yield_: LearningYield = LearningYield()

    def __post_init__(self) -> None:
        _required(
            self.event_id,
            self.subject_id,
            self.activity_ref,
            self.policy_id,
            self.policy_version,
            self.code_sha,
            self.input_fingerprint,
            self.reason_code,
        )
        if self.occurred_at.tzinfo is None:
            raise ValueError("learning event time must be timezone-aware")
        if self.xeed_id is not None and not self.xeed_id.strip():
            raise ValueError("learning event Xeed id cannot be empty")
        if (self.provider is None) != (self.provider_version is None):
            raise ValueError("provider and provider version must coexist")
        if self.provider is not None:
            _required(self.provider, self.provider_version or "")
        if (self.before_state_fingerprint is None) != (self.after_state_fingerprint is None):
            raise ValueError("before/after state fingerprints must coexist")
        if self.before_state_fingerprint is not None:
            _required(
                self.before_state_fingerprint,
                self.after_state_fingerprint or "",
            )
        if self.output_fingerprint is not None:
            _required(self.output_fingerprint)
        if self.kind is LearningEventKind.CORRECTION:
            if self.corrects_event_id is None:
                raise ValueError("correction event must reference the corrected event")
            _required(self.corrects_event_id)
        elif self.corrects_event_id is not None:
            raise ValueError("only correction events may reference a corrected event")
        if self.outcome is LearningOutcome.FAILED and self.yield_.total_observed_output:
            raise ValueError("failed learning event cannot fabricate successful yield")

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["outcome"] = self.outcome.value
        payload["mechanism"] = self.mechanism.value
        payload["occurred_at"] = self.occurred_at.astimezone(UTC).isoformat()
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class LearningMemoryConflict(ValueError):
    """Raised when a stable learning-event id is reused with different content."""


class LearningMemory(Protocol):
    """Persistence port for append-only operational learning evidence."""

    def append(self, event: LearningEvent) -> bool:
        """Persist once. False means an exact idempotent replay."""

    def get(self, event_id: str) -> LearningEvent | None:
        """Return one learning event by stable identity."""

    def for_subject(self, subject_id: str) -> tuple[LearningEvent, ...]:
        """Return the chronological learning history for one canonical subject."""

    def for_xeed(self, xeed_id: str) -> tuple[LearningEvent, ...]:
        """Return the chronological learning history attributable to one Xeed."""


@dataclass(frozen=True, slots=True)
class LearningSummary:
    event_count: int
    outcome_counts: tuple[tuple[LearningOutcome, int], ...]
    known_costs_by_currency: tuple[tuple[str, int], ...]
    unknown_cost_event_count: int
    known_latency_event_count: int
    total_latency_ms: int
    corrections: int
    yield_: LearningYield


def summarize_learning(events: tuple[LearningEvent, ...]) -> LearningSummary:
    """Aggregate observable learning evidence without inventing a quality score."""

    outcome_counts = {outcome: 0 for outcome in LearningOutcome}
    costs: dict[str, int] = {}
    unknown_costs = 0
    known_latency = 0
    total_latency = 0
    corrections = 0
    yield_totals = {
        "observations_added": 0,
        "state_fields_changed": 0,
        "dimensions_became_answerable": 0,
        "semantic_judgments_produced": 0,
        "research_objectives_resolved": 0,
        "xignals_emitted": 0,
        "canonical_admissions": 0,
    }

    for event in events:
        outcome_counts[event.outcome] += 1
        if event.cost.amount_microunits is None:
            unknown_costs += 1
        else:
            assert event.cost.currency is not None
            costs[event.cost.currency] = (
                costs.get(event.cost.currency, 0) + event.cost.amount_microunits
            )
        if event.cost.latency_ms is not None:
            known_latency += 1
            total_latency += event.cost.latency_ms
        if event.kind is LearningEventKind.CORRECTION:
            corrections += 1
        for name in yield_totals:
            yield_totals[name] += getattr(event.yield_, name)

    return LearningSummary(
        event_count=len(events),
        outcome_counts=tuple((outcome, outcome_counts[outcome]) for outcome in LearningOutcome),
        known_costs_by_currency=tuple(sorted(costs.items())),
        unknown_cost_event_count=unknown_costs,
        known_latency_event_count=known_latency,
        total_latency_ms=total_latency,
        corrections=corrections,
        yield_=LearningYield(**yield_totals),
    )
