"""Slices, local matching, the index-first source port and the slice ingestor.

Why this exists (measured in spec 063 validation): per-Focus pull spends requests per
(Focus x capability x market x question) and sees only one truncated page; a slice
pays per (country x notice kind x day), sees every notice of the window, and answers
every Focus locally. The index answers only when its slice is fresh and complete for
the asked window; otherwise the caller's live port answers and the slice is demanded.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from application.observation_intelligence.contracts import (
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
)
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.loop import SourceObservationPort
from application.observation_intelligence.strategy import RECENCY_WINDOWS, ObservationAction

INDEX_VERSION = "world-demand-index.v1"
NOT_INDEXED = "NOT_INDEXED"


@dataclass(frozen=True, slots=True)
class DemandSlice:
    source_id: str
    jurisdiction: str  # country-level path, e.g. EU/ES
    kind: SourceCapability

    @property
    def key(self) -> str:
        return f"{self.source_id}|{self.jurisdiction}|{self.kind.value}"


@dataclass(frozen=True, slots=True)
class SliceState:
    slice: DemandSlice
    ingested_at: datetime | None
    window_start: datetime | None
    complete: bool
    requests: int
    records: int
    demanded_at: datetime | None


class DemandIndexStore(Protocol):
    def state(self, demand_slice: DemandSlice) -> SliceState | None: ...

    def demand(self, demand_slice: DemandSlice, *, now: datetime) -> None: ...

    def demanded(self) -> tuple[SliceState, ...]: ...

    def upsert(self, records: Sequence[ProcurementRecord]) -> int: ...

    def mark_ingested(
        self,
        demand_slice: DemandSlice,
        *,
        at: datetime,
        window_start: datetime,
        complete: bool,
        requests: int,
        records: int,
    ) -> None: ...

    def records(self, demand_slice: DemandSlice) -> tuple[ProcurementRecord, ...]: ...


def country_of(code: TaxonomyCode) -> str | None:
    """EU/ES/ES5/ES52 → EU/ES; other trees keep their first two segments (US/US-AR → US)."""
    segments = code.code.split("/") if code.scheme == "GEO" else []
    if not segments:
        return None
    if segments[0] == "EU":
        return "/".join(segments[:2]) if len(segments) >= 2 else None
    return segments[0]


def slices_for(source_id: str, query: QuerySpec) -> tuple[DemandSlice, ...] | None:
    """The slices covering a query; None when a geography is coarser than a country."""
    out: dict[str, DemandSlice] = {}
    for geography in query.geographies:
        country = country_of(geography)
        if country is None:
            return None
        for kind in query.capabilities:
            item = DemandSlice(source_id, country, kind)
            out[item.key] = item
    return tuple(out.values()) or None


def _cpv_prefix(code: str) -> str:
    stripped = code.rstrip("0")
    return code[: max(2, len(stripped))]


def code_within(record: TaxonomyCode, asked: TaxonomyCode) -> bool:
    """Classification hierarchy: CPV by significant prefix, other schemes by prefix."""
    if record.scheme != asked.scheme:
        return False
    if asked.scheme == "CPV":
        return record.code.startswith(_cpv_prefix(asked.code))
    return record.code.startswith(asked.code)


def matches_hierarchically(record: ProcurementRecord, query: QuerySpec) -> bool:
    return (
        record.kind in query.capabilities
        and (
            not query.demand_codes
            or any(code_within(c, a) for c in record.demand_codes for a in query.demand_codes)
        )
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


class DemandIndexPort:
    """Index first; the live port answers (and the slice is demanded) when it cannot."""

    def __init__(
        self,
        store: DemandIndexStore,
        live: SourceObservationPort | None,
        *,
        clock: Callable[[], datetime],
        fresh_for: timedelta = timedelta(hours=26),
    ) -> None:
        self._store = store
        self._live = live
        self._clock = clock
        self._fresh_for = fresh_for
        self.index_hits = 0
        self.live_calls = 0

    def covered(self, source_id: str, query: QuerySpec) -> tuple[DemandSlice, ...] | None:
        slices = slices_for(source_id, query)
        if slices is None:
            return None
        now = self._clock()
        for item in slices:
            state = self._store.state(item)
            if (
                state is None
                or state.ingested_at is None
                or not state.complete
                or now - state.ingested_at > self._fresh_for
                or state.window_start is None
                or query.published_since is None
                or state.window_start.date() > query.published_since.date()
            ):
                return None
        return slices

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        now = self._clock()
        slices = self.covered(source.source_id, action.query)
        if slices is not None:
            self.index_hits += 1
            found: dict[str, ProcurementRecord] = {}
            ingested = min(
                state.ingested_at
                for item in slices
                if (state := self._store.state(item)) is not None and state.ingested_at
            )
            for item in slices:
                for record in self._store.records(item):
                    if matches_hierarchically(record, action.query):
                        found[record.record_id] = record
            return SourceFindings(
                source_id=source.source_id,
                retrieved_at=ingested,  # the ingestion time, never fresher than observed
                requests=0,
                amount_microunits=0,
                latency_ms=0,
                records=tuple(sorted(found.values(), key=lambda r: r.record_id)),
                total_available=len(found),
                failure=None,
            )
        for item in slices_for(source.source_id, action.query) or ():
            self._store.demand(item, now=now)
        if self._live is None:
            return SourceFindings(
                source_id=source.source_id,
                retrieved_at=now,
                requests=0,
                amount_microunits=0,
                latency_ms=0,
                failure=NOT_INDEXED,
            )
        self.live_calls += 1
        return self._live.observe(action, source)


class SliceFeedPort(Protocol):
    def search(
        self, query: QuerySpec, *, page: int, limit: int | None = None
    ) -> SourceFindings: ...


@dataclass(frozen=True, slots=True)
class IngestionReport:
    slice_key: str
    pages: int
    records: int
    complete: bool
    failure: str | None


class WorldDemandIngestor:
    """Page through demanded slices; incomplete slices never answer (fail closed)."""

    def __init__(
        self,
        *,
        feeds: dict[str, SliceFeedPort],
        store: DemandIndexStore,
        clock: Callable[[], datetime],
        max_pages: int = 20,
        page_size: int = 100,
        refresh_after: timedelta = timedelta(hours=20),
    ) -> None:
        self._feeds = feeds
        self._store = store
        self._clock = clock
        self._max_pages = max_pages
        self._page_size = page_size
        self._refresh_after = refresh_after

    def due(self) -> tuple[SliceState, ...]:
        now = self._clock()
        return tuple(
            s
            for s in self._store.demanded()
            if s.slice.source_id in self._feeds
            and (s.ingested_at is None or now - s.ingested_at >= self._refresh_after)
        )

    def ingest(self, demand_slice: DemandSlice) -> IngestionReport:
        now = self._clock()
        feed = self._feeds[demand_slice.source_id]
        window = RECENCY_WINDOWS.get(demand_slice.kind, timedelta(days=60))
        previous = self._store.state(demand_slice)
        window_start = now - window
        # Delta after a complete ingestion: one day of overlap, never a gap.
        since = (
            max(window_start, previous.ingested_at - timedelta(days=1))
            if previous is not None and previous.complete and previous.ingested_at is not None
            else window_start
        )
        query = QuerySpec(
            demand_codes=(),
            geographies=(TaxonomyCode("GEO", demand_slice.jurisdiction),),
            capabilities=frozenset({demand_slice.kind}),
            published_since=since,
        )
        pages = records = 0
        complete = False
        failure = None
        for page in range(1, self._max_pages + 1):
            findings = feed.search(query, page=page, limit=self._page_size)
            pages += 1
            if findings.failure is not None:
                failure = findings.failure
                break
            records += self._store.upsert(findings.records)
            if len(findings.records) < self._page_size:
                complete = True
                break
        kept_start = (
            previous.window_start
            if complete
            and previous is not None
            and previous.complete
            and previous.window_start is not None
            else window_start
        )
        self._store.mark_ingested(
            demand_slice,
            at=now,
            window_start=max(kept_start, window_start),
            complete=complete,
            requests=pages + (0 if previous is None else previous.requests),
            records=records,
        )
        return IngestionReport(demand_slice.key, pages, records, complete, failure)

    def run(self, *, max_slices: int = 10) -> tuple[IngestionReport, ...]:
        return tuple(self.ingest(s.slice) for s in self.due()[:max_slices])


def per_focus_requests(
    *, foci: int, capabilities: int, markets: int, questions: int, cadence_days: float
) -> float:
    """ESTIMATED requests/day of the per-Focus pull model (one page per action)."""
    return foci * capabilities * markets * questions / cadence_days


def world_slice_requests(*, slices: int, daily_notices_per_slice: float, page_size: int) -> float:
    """ESTIMATED steady-state requests/day of slice ingestion (delta pages per slice)."""
    pages = max(1.0, -(-daily_notices_per_slice // page_size))
    return slices * pages


def touched(slices: Iterable[DemandSlice]) -> frozenset[str]:
    return frozenset(s.key for s in slices)
