"""PLACSP: Spain's public procurement platform read into the world demand index.

The fixture holds real entries of the platform's aggregation feed (contact blocks removed).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.observation_intelligence.catalog import SOURCES
from application.observation_intelligence.contracts import (
    AdoptionStatus,
    QuerySpec,
    SourceCapability,
    TaxonomyCode,
)
from application.observation_intelligence.findings import SourceFindings
from application.world_demand.index import DemandSlice, WorldDemandIngestor
from pipeline.observation_intelligence.placsp import (
    PLACSP_SOURCE_ID,
    PlacspFeedAdapter,
    UrllibPlacspTransport,
    parse_feed,
)

FIXTURE = Path(__file__).parent / "fixtures" / "placsp-feed-sample.atom"
NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)
OPEN = SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
SPAIN = TaxonomyCode("GEO", "EU/ES")


def test_real_feed_entries_become_open_tenders_with_their_own_facts() -> None:
    records, next_url, oldest = parse_feed(FIXTURE.read_bytes())
    assert len(records) == 3  # the two closed entries (evaluation, resolved) are not kept
    assert next_url is not None and next_url.startswith("https://contrataciondelestado.es/")
    assert oldest is not None
    for record in records:
        assert record.source_id == PLACSP_SOURCE_ID and record.kind is OPEN
        # The official link: the platform, or the regional platform an aggregated tender comes from.
        assert record.source_url.startswith("https://")
        assert record.demand_codes and all(
            c.scheme == "CPV" and len(c.code) == 8 for c in record.demand_codes
        )
        assert all(p.within(SPAIN) for p in record.places)
        # The deadline is the tender submission deadline, never the contract's end date.
        assert record.deadline is not None and record.deadline < "2030"
        assert record.published_at.tzinfo is not None and record.buyer_name


def _page(entries: list[tuple[str, str, str]], next_url: str | None) -> bytes:
    """A minimal CODICE feed page: (id, status, updated) per entry."""
    link = f'<link href="{next_url}" rel="next"/>' if next_url else ""
    body = "".join(
        f"""<entry><id>{eid}</id><link href="https://contrataciondelestado.es/x/{eid}"/>
        <title>Suministro {eid}</title><updated>{updated}</updated>
        <ContractFolderStatus><ContractFolderStatusCode>{status}</ContractFolderStatusCode>
        <LocatedContractingParty><Party><PartyName><Name>Ayuntamiento</Name></PartyName></Party>
        </LocatedContractingParty>
        <ProcurementProject><RequiredCommodityClassification><ItemClassificationCode>42520000
        </ItemClassificationCode></RequiredCommodityClassification>
        <RealizedLocation><CountrySubentityCode>ES300</CountrySubentityCode></RealizedLocation>
        </ProcurementProject>
        <TenderingProcess><TenderSubmissionDeadlinePeriod><EndDate>2026-11-02</EndDate>
        </TenderSubmissionDeadlinePeriod></TenderingProcess></ContractFolderStatus></entry>"""
        for eid, status, updated in entries
    )
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{link}{body}</feed>'.encode()


class Pages:
    def __init__(self, pages: dict[str, bytes]) -> None:
        self.pages = pages
        self.requests: list[str] = []

    def get(self, url: str) -> tuple[int, bytes]:
        self.requests.append(url)
        return 200, self.pages[url]


A1, A2 = (
    "https://contrataciondelsectorpublico.gob.es/a.atom",
    "https://contrataciondelestado.es/a_2.atom",
)
B1 = "https://contrataciondelsectorpublico.gob.es/b.atom"


def _query(since: datetime) -> QuerySpec:
    return QuerySpec(
        demand_codes=(), geographies=(SPAIN,), capabilities=frozenset({OPEN}), published_since=since
    )


def test_pages_both_feeds_back_to_the_window_and_then_stops() -> None:
    transport = Pages({
        A1: _page([("a1", "PUB", "2026-10-11T10:00:00+02:00"), ("a2", "ADJ", "2026-10-10T10:00:00+02:00")], A2),
        A2: _page([("a3", "PUB", "2026-10-09T10:00:00+02:00"), ("old", "PUB", "2026-09-01T10:00:00+02:00")], "https://contrataciondelestado.es/a_3.atom"),
        B1: _page([("b1", "PUB", "2026-10-11T08:00:00+02:00")], None),
    })  # fmt: skip
    adapter = PlacspFeedAdapter(transport, clock=lambda: NOW, feeds=(A1, B1))
    query = _query(NOW - timedelta(days=10))
    first, second, third = (adapter.search(query, page=p) for p in (1, 2, 3))
    assert [r.record_id for r in first.records] == ["a1"] and first.has_more is True
    # Page 2 reaches past the window: older pages of feed A are not read; feed B follows.
    assert [r.record_id for r in second.records] == ["a3"] and second.has_more is True
    assert [r.record_id for r in third.records] == ["b1"] and third.has_more is False
    assert transport.requests == [A1, A2, B1]


def test_a_query_outside_spain_or_for_awards_reads_nothing() -> None:
    transport = Pages({})
    adapter = PlacspFeedAdapter(transport, clock=lambda: NOW, feeds=(A1,))
    france = QuerySpec(
        demand_codes=(), geographies=(TaxonomyCode("GEO", "EU/FR"),), capabilities=frozenset({OPEN})
    )
    awards = QuerySpec(
        demand_codes=(),
        geographies=(SPAIN,),
        capabilities=frozenset({SourceCapability.PUBLIC_PROCUREMENT_AWARDS}),
    )
    for query in (france, awards):
        found = adapter.search(query, page=1)
        assert found.records == () and found.has_more is False and found.requests == 0
    assert transport.requests == []


def test_the_transport_only_reaches_the_platform_over_https() -> None:
    transport = UrllibPlacspTransport()
    for url in ("https://evil.example/feed.atom", "http://contrataciondelestado.es/x.atom"):
        with pytest.raises(ValueError):
            transport.get(url)


class _Store:
    def __init__(self) -> None:
        self.marked: dict[str, object] = {}
        self.records: list[object] = []

    def state(self, demand_slice: DemandSlice) -> None:
        return None

    def upsert(self, records: object) -> int:
        items = list(records)  # type: ignore[call-overload]
        self.records += items
        return len(items)

    def mark_ingested(self, demand_slice: DemandSlice, **facts: object) -> None:
        self.marked = facts


class _Feed:
    """Short filtered pages that still say there is more: the size alone would mislead."""

    def __init__(self) -> None:
        self.pages = 0

    def search(self, query: QuerySpec, *, page: int, limit: int | None = None) -> SourceFindings:
        self.pages += 1
        return SourceFindings(
            source_id=PLACSP_SOURCE_ID, retrieved_at=NOW, requests=1, amount_microunits=0,
            latency_ms=0, has_more=page < 3,
        )  # fmt: skip


def test_the_ingestor_follows_an_explicit_has_more_over_the_page_size() -> None:
    feed, store = _Feed(), _Store()
    ingestor = WorldDemandIngestor(feeds={PLACSP_SOURCE_ID: feed}, store=store, clock=lambda: NOW)  # type: ignore[arg-type]
    report = ingestor.ingest(DemandSlice(PLACSP_SOURCE_ID, "EU/ES", OPEN))
    assert feed.pages == 3 and report.complete and store.marked["complete"] is True


def test_a_records_refresh_rereads_the_window_and_never_touches_the_slice_state() -> None:
    feed, store = _Feed(), _Store()
    ingestor = WorldDemandIngestor(feeds={PLACSP_SOURCE_ID: feed}, store=store, clock=lambda: NOW)  # type: ignore[arg-type]
    report = ingestor.refresh_records(DemandSlice(PLACSP_SOURCE_ID, "EU/ES", OPEN), max_pages=2)
    # Bounded, and stopping early leaves completeness and freshness exactly as they were.
    assert feed.pages == 2 and not report.complete and store.marked == {}


def test_placsp_is_adopted_for_spanish_open_tenders_only() -> None:
    (source,) = [s for s in SOURCES if s.source_id == PLACSP_SOURCE_ID]
    assert source.adoption is AdoptionStatus.ADOPTED and not source.adoption_blockers
    assert source.capabilities == frozenset({OPEN})
    assert source.jurisdictions == (SPAIN,)


def test_the_traversal_is_bounded_even_when_the_window_asks_for_more() -> None:
    # Weekday pages hold hours of updates: sixty days would be gigabytes. The feed is read
    # back to MAX_AGE (30 days) at most, whatever window the index asks for.
    transport = Pages({
        A1: _page([("a1", "PUB", "2026-10-11T10:00:00+02:00")], A2),
        A2: _page([("a2", "PUB", "2026-09-01T10:00:00+02:00")], "https://contrataciondelestado.es/a_3.atom"),
    })  # fmt: skip
    adapter = PlacspFeedAdapter(transport, clock=lambda: NOW, feeds=(A1,))
    query = _query(NOW - timedelta(days=60))
    first, second = adapter.search(query, page=1), adapter.search(query, page=2)
    assert first.has_more is True and second.has_more is False
    assert transport.requests == [A1, A2]


class _StoreWithState(_Store):
    """A slice left mid-traversal at page 25 by a runtime that has since restarted."""

    def state(self, demand_slice: DemandSlice):  # type: ignore[no-untyped-def,override]
        from application.world_demand.index import SliceState

        return SliceState(
            demand_slice, NOW, NOW - timedelta(days=60), False, 250, 0, NOW,
            cursor_page=25, traversal_since=NOW - timedelta(days=30),
        )  # fmt: skip


def test_a_traversal_lost_in_a_restart_starts_again_instead_of_failing_forever() -> None:
    # Found in production: after a deploy the feed answered PAGE_NOT_REACHABLE at the
    # resumed page on every round and the slice never completed.
    transport = Pages({A1: _page([("a1", "PUB", "2026-10-11T10:00:00+02:00")], None)})
    adapter = PlacspFeedAdapter(transport, clock=lambda: NOW, feeds=(A1,))
    store = _StoreWithState()
    ingestor = WorldDemandIngestor(
        feeds={PLACSP_SOURCE_ID: adapter}, store=store, clock=lambda: NOW
    )  # type: ignore[dict-item,arg-type]
    report = ingestor.ingest(DemandSlice(PLACSP_SOURCE_ID, "EU/ES", OPEN))
    assert report.failure == "PAGE_NOT_REACHABLE" and transport.requests == []
    assert store.marked["cursor_page"] == 1 and store.marked["traversal_since"] is None
