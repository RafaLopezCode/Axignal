"""Operational learning about sources, never about companies.

Realized yield may move a source's routing quality by at most one band, and
only after enough attempts. It is an input to routing policy, not evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from application.observation_intelligence.contracts import Band

MIN_ATTEMPTS_FOR_ADJUSTMENT = 3


@dataclass
class SourceOperationalStats:
    source_id: str
    attempts: int = 0
    failures: int = 0
    requests: int = 0
    records: int = 0
    new_records: int = 0
    duplicates: int = 0
    candidates: int = 0
    follow_ups: int = 0
    latency_ms: int = 0
    amount_microunits: int = 0

    @property
    def hit_rate(self) -> float | None:
        return None if self.attempts == 0 else (self.attempts - self.failures) / self.attempts

    @property
    def duplicate_rate(self) -> float | None:
        return None if self.records == 0 else self.duplicates / self.records


@dataclass
class OperationalLearning:
    stats: dict[str, SourceOperationalStats] = field(default_factory=dict)

    def for_source(self, source_id: str) -> SourceOperationalStats:
        return self.stats.setdefault(source_id, SourceOperationalStats(source_id))

    def adjusted_quality(self, source_id: str, declared: Band) -> tuple[Band, str | None]:
        """Declared quality, moved one band by realized yield once evidence suffices."""

        stats = self.stats.get(source_id)
        if (
            declared is Band.UNKNOWN
            or stats is None
            or stats.attempts < MIN_ATTEMPTS_FOR_ADJUSTMENT
        ):
            return declared, None
        if stats.failures * 2 > stats.attempts or (stats.duplicate_rate or 0.0) > 0.8:
            return Band(max(Band.LOW, declared - 1)), "LEARNED_LOW_YIELD"
        if stats.candidates >= stats.attempts:
            return Band(min(Band.HIGH, declared + 1)), "LEARNED_HIGH_YIELD"
        return declared, None
