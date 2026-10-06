"""Recorded source findings, replayed for downstream recomputation without refetching.

When autonomous acquisition finds new procurement evidence, the canonical
subscriber reobservation path recomputes the Xeed's opportunity projection.
It must see exactly what was retrieved, when it was retrieved, and nothing
more. This port answers a query only from a recorded, untruncated retrieval
whose query covers it (same capabilities, wider or equal geography and codes,
earlier or equal time floors) and filters those real records with the new
query's own criteria. Anything else is NOT_OBSERVED: coverage stays UNKNOWN.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.observation_intelligence.contracts import QuerySpec, SourceDescriptor
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.strategy import ObservationAction

NOT_OBSERVED = "NOT_OBSERVED_BY_AUTONOMOUS_RUNTIME"


@dataclass(frozen=True, slots=True)
class RecordedFindings:
    source_id: str
    query: QuerySpec
    findings: SourceFindings

    @property
    def complete(self) -> bool:
        """A failed or truncated page cannot answer anything beyond itself."""
        total = self.findings.total_available
        return self.findings.failure is None and (
            total is None or total <= len(self.findings.records)
        )


class FindingsLedger(Protocol):
    def record_findings(self, item: RecordedFindings) -> None: ...

    def recorded_findings(self, source_id: str) -> tuple[RecordedFindings, ...]: ...


def _floor_covers(recorded: datetime | None, wanted: datetime | None) -> bool:
    return recorded is None or (wanted is not None and recorded <= wanted)


def covers(recorded: QuerySpec, wanted: QuerySpec) -> bool:
    return (
        recorded.capabilities == wanted.capabilities
        and set(wanted.demand_codes) <= set(recorded.demand_codes)
        and all(any(g.within(r) for r in recorded.geographies) for g in wanted.geographies)
        and _floor_covers(recorded.published_since, wanted.published_since)
        and _floor_covers(recorded.open_on, wanted.open_on)
    )


def matches(record: ProcurementRecord, query: QuerySpec) -> bool:
    """The query's own criteria, as the source applies them (exact code, place, time)."""

    return (
        record.kind in query.capabilities
        and (not query.demand_codes or bool(set(record.demand_codes) & set(query.demand_codes)))
        and any(p.within(g) for p in record.places for g in query.geographies)
        and (
            query.published_since is None
            or record.published_at.date() >= query.published_since.date()
        )
        and (
            query.open_on is None
            or (
                record.deadline is not None
                and record.deadline[:10] >= query.open_on.date().isoformat()
            )
        )
    )


class RecordedFindingsPort:
    """A SourceObservationPort over real retrievals; it never reaches the network."""

    def __init__(self, ledger: FindingsLedger, *, clock: Callable[[], datetime]) -> None:
        self._ledger = ledger
        self._clock = clock

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        recorded = [
            item
            for item in self._ledger.recorded_findings(source.source_id)
            if item.complete and covers(item.query, action.query)
        ]
        if not recorded:
            return SourceFindings(
                source_id=source.source_id,
                retrieved_at=self._clock(),
                requests=0,
                amount_microunits=0,
                latency_ms=0,
                failure=NOT_OBSERVED,
            )
        latest = max(recorded, key=lambda item: item.findings.retrieved_at)
        records = tuple(r for r in latest.findings.records if matches(r, action.query))
        return SourceFindings(
            source_id=source.source_id,
            # The original retrieval time: replay never makes evidence look fresher.
            retrieved_at=latest.findings.retrieved_at,
            requests=0,
            amount_microunits=0,
            latency_ms=0,
            records=records,
            total_available=len(records),
        )
