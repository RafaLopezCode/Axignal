"""Evidence coverage per economic question and market.

Searching a source and finding nothing is coverage *within that source's
scope*, never evidence of absence: UNKNOWN != FALSE. Coverage ages into STALE.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum

from application.observation_intelligence.contracts import TaxonomyCode


class CoverageState(StrEnum):
    OBSERVED_CURRENT = "OBSERVED_CURRENT"
    SEARCHED_NO_EVIDENCE = "SEARCHED_NO_EVIDENCE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class CoverageEntry:
    question_id: str
    market: TaxonomyCode
    evidence_ids: tuple[str, ...]
    searched_sources: tuple[str, ...]
    last_observed_at: datetime


@dataclass
class EvidenceCoverageMap:
    max_age: timedelta
    _entries: dict[tuple[str, TaxonomyCode], CoverageEntry] = field(default_factory=dict)

    def record(
        self,
        *,
        question_id: str,
        market: TaxonomyCode,
        source_id: str,
        evidence_ids: tuple[str, ...],
        observed_at: datetime,
    ) -> None:
        key = (question_id, market)
        current = self._entries.get(key)
        if current is None:
            self._entries[key] = CoverageEntry(
                question_id, market, evidence_ids, (source_id,), observed_at
            )
            return
        self._entries[key] = replace(
            current,
            evidence_ids=tuple(dict.fromkeys((*current.evidence_ids, *evidence_ids))),
            searched_sources=tuple(dict.fromkeys((*current.searched_sources, source_id))),
            last_observed_at=max(current.last_observed_at, observed_at),
        )

    def entry(self, question_id: str, market: TaxonomyCode) -> CoverageEntry | None:
        return self._entries.get((question_id, market))

    def state(self, question_id: str, market: TaxonomyCode, *, as_of: datetime) -> CoverageState:
        entry = self._entries.get((question_id, market))
        if entry is None:
            return CoverageState.UNKNOWN
        if as_of - entry.last_observed_at > self.max_age:
            return CoverageState.STALE
        if entry.evidence_ids:
            return CoverageState.OBSERVED_CURRENT
        return CoverageState.SEARCHED_NO_EVIDENCE

    def searched(self, question_id: str, market: TaxonomyCode, source_id: str) -> bool:
        entry = self._entries.get((question_id, market))
        return entry is not None and source_id in entry.searched_sources

    def entries(self) -> tuple[CoverageEntry, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries, key=str))
