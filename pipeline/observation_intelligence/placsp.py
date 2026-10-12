"""PLACSP — Spain's public procurement platform, through its open ATOM syndication.

The Plataforma de Contratación del Sector Público publishes every tender of the contracting
profiles it hosts (and, in a second feed, of the regional platforms aggregated into it) as
CODICE entries in paged ATOM feeds, newest first. Reuse follows the general conditions for
State documents (Ley 37/2007, RD 1495/2011 art. 8): cite the source, do not distort, keep
the update date. Each record keeps its official link and dates.

The feed cannot be queried by classification: it is read page by page for the world demand
index (never on a subscriber's request) and filtered locally. Only open tenders (status PUB)
are kept: an award history would mean gigabytes of syndication for little first value.
"""

from __future__ import annotations

import time
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

from application.observation_intelligence.contracts import (
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
)
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.strategy import ObservationAction

PLACSP_SOURCE_ID = "es-placsp"
FEEDS = (
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
    "licitacionesPerfilesContratanteCompleto3.atom",
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_1044/"
    "PlataformasAgregadasSinMenores.atom",
)
HOSTS = frozenset({"contrataciondelsectorpublico.gob.es", "contrataciondelestado.es"})
MAX_FEED_BYTES = 40_000_000
#: How far back the feed is read. Weekday pages hold a few hours of updates, so sixty
#: days would be gigabytes; an open tender almost always had an update within thirty.
MAX_AGE = timedelta(days=30)
OPEN = "PUB"


class PlacspTransport(Protocol):
    def get(self, url: str) -> tuple[int, bytes]: ...


class UrllibPlacspTransport:
    """HTTPS GET to the platform's own hosts only, bounded in time and size."""

    def __init__(self, *, timeout_s: float = 60.0) -> None:
        self._timeout_s = timeout_s

    def get(self, url: str) -> tuple[int, bytes]:
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in HOSTS:
            raise ValueError("PLACSP transport only reaches the platform's own hosts")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AXIGNAL-SourceObserver/0.2", "Accept": "application/atom+xml"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
            body = response.read(MAX_FEED_BYTES + 1)
            if len(body) > MAX_FEED_BYTES:
                raise ValueError("PLACSP feed page too large")
            return int(response.status), body


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element: ET.Element | None, *names: str) -> ET.Element | None:
    """Follow direct children by local name (CODICE namespaces vary by version)."""
    current = element
    for name in names:
        if current is None:
            return None
        current = next((c for c in current if _local(c.tag) == name), None)
    return current


def _children(element: ET.Element | None, name: str) -> Iterator[ET.Element]:
    return (c for c in (element if element is not None else ()) if _local(c.tag) == name)


def _text(element: ET.Element | None) -> str | None:
    value = None if element is None else (element.text or "").strip()
    return value or None


def _date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _place(nuts: str | None) -> TaxonomyCode:
    """A Spanish NUTS code (ES511) as a jurisdiction path; without one, the country."""
    if nuts and nuts.isalnum() and nuts.upper().startswith("ES") and 2 <= len(nuts) <= 5:
        code = nuts.upper()
        return TaxonomyCode(
            "GEO", "/".join(["EU", "ES", *(code[:i] for i in range(3, len(code) + 1))])
        )
    return TaxonomyCode("GEO", "EU/ES")


def parse_entry(entry: ET.Element) -> ProcurementRecord | None:
    """One open tender from one CODICE entry, or None when it is not open or incomplete."""
    folder = _child(entry, "ContractFolderStatus")
    status = _text(_child(folder, "ContractFolderStatusCode"))
    title = _text(_child(entry, "title"))
    record_id = _text(_child(entry, "id"))
    link = _child(entry, "link")
    url = None if link is None else link.get("href")
    if status != OPEN or not title or not record_id or not url:
        return None
    if urlsplit(url).scheme not in {"https", "http"}:
        return None  # only a web link is shown to a subscriber
    project = _child(folder, "ProcurementProject")
    codes = {
        code
        for classification in _children(project, "RequiredCommodityClassification")
        if (code := _text(_child(classification, "ItemClassificationCode"))) and code.isdigit()
    }
    for lot in _children(folder, "ProcurementProjectLot"):
        lot_project = _child(lot, "ProcurementProject")
        for classification in _children(lot_project, "RequiredCommodityClassification"):
            code = _text(_child(classification, "ItemClassificationCode"))
            if code and code.isdigit():
                codes.add(code)
    nuts = _text(_child(project, "RealizedLocation", "CountrySubentityCode"))
    deadline_period = _child(folder, "TenderingProcess", "TenderSubmissionDeadlinePeriod")
    deadline = _text(_child(deadline_period, "EndDate"))
    issued = [
        d
        for notice in _children(folder, "ValidNoticeInfo")
        for status_info in _children(notice, "AdditionalPublicationStatus")
        for reference in _children(status_info, "AdditionalPublicationDocumentReference")
        if (d := _date(_text(_child(reference, "IssueDate")))) is not None
    ]
    published = min(issued) if issued else _date(_text(_child(entry, "updated")))
    if published is None:
        return None
    buyer = _text(_child(folder, "LocatedContractingParty", "Party", "PartyName", "Name"))
    return ProcurementRecord(
        record_id=record_id,
        source_id=PLACSP_SOURCE_ID,
        kind=SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
        title=title[:500],
        buyer_name=buyer,
        places=(_place(nuts),),
        demand_codes=tuple(TaxonomyCode("CPV", code[:8].ljust(8, "0")) for code in sorted(codes)),
        published_at=published,
        source_url=url,
        deadline=deadline,
    )


def parse_feed(body: bytes) -> tuple[tuple[ProcurementRecord, ...], str | None, datetime | None]:
    """Open tenders of one feed page, the next (older) page and the page's oldest update."""
    root = ET.fromstring(body)
    if _local(root.tag) != "feed":
        raise ValueError("not an ATOM feed")
    next_url = next(
        (link.get("href") for link in _children(root, "link") if link.get("rel") == "next"), None
    )
    records: list[ProcurementRecord] = []
    oldest: datetime | None = None
    for entry in _children(root, "entry"):
        updated = _date(_text(_child(entry, "updated")))
        if updated is not None and (oldest is None or updated < oldest):
            oldest = updated
        record = parse_entry(entry)
        if record is not None:
            records.append(record)
    return tuple(records), next_url, oldest


class PlacspFeedAdapter:
    """Pages through both PLACSP feeds for the world demand index; nothing per subscriber."""

    def __init__(
        self,
        transport: PlacspTransport,
        *,
        clock: Callable[[], datetime],
        feeds: tuple[str, ...] = FEEDS,
        max_age: timedelta = MAX_AGE,
    ) -> None:
        self._transport = transport
        self._max_age = max_age
        self._clock = clock
        self._feeds = feeds
        #: The traversal so far, page by page: (feed index, page URL). Next links are dated
        #: files, so a traversal can resume within one runtime; after a restart it restarts.
        self._chain: list[tuple[int, str]] = [(0, feeds[0])]
        self._done: set[int] = set()

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        """Never read live for a request: the index answers, or the slice is demanded."""
        if source.source_id != PLACSP_SOURCE_ID or action.source_id != PLACSP_SOURCE_ID:
            raise ValueError("PLACSP adapter only serves the PLACSP source")
        return SourceFindings(
            source_id=PLACSP_SOURCE_ID,
            retrieved_at=self._clock(),
            requests=0,
            amount_microunits=0,
            latency_ms=0,
            failure="INDEX_ONLY",
        )

    def search(self, query: QuerySpec, *, page: int, limit: int | None = None) -> SourceFindings:
        del limit  # a feed page is what the platform publishes; filtering is local
        if page < 1:
            raise ValueError("PLACSP page must be >= 1")
        if page == 1:
            self._chain = [(0, self._feeds[0])]
            self._done = set()
        spain = TaxonomyCode("GEO", "EU/ES")
        if SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES not in query.capabilities or not any(
            spain.within(g) or g.within(spain) for g in query.geographies
        ):
            return self._findings((), has_more=False, requests=0, started=time.monotonic())
        if page > len(self._chain):
            return self._failure("PAGE_NOT_REACHABLE", time.monotonic())
        feed, url = self._chain[page - 1]
        started = time.monotonic()
        try:
            status, body = self._transport.get(url)
        except (OSError, ValueError) as error:
            return self._failure(f"TRANSPORT:{type(error).__name__}", started)
        if status != 200:
            return self._failure(f"HTTP_{status}", started)
        try:
            records, next_url, oldest = parse_feed(body)
        except (ET.ParseError, ValueError):
            return self._failure("FEED_NOT_PARSEABLE", started)
        # Publication filters records; the traversal stops by update time, bounded by MAX_AGE
        # (a tender published long ago but updated recently is still kept while open).
        since = query.published_since
        horizon = self._clock() - self._max_age
        if since is not None:
            horizon = max(horizon, since)
        kept = tuple(
            r
            for r in records
            if (since is None or r.published_at >= since)
            and any(p.within(g) for p in r.places for g in query.geographies)
        )
        # This feed is finished when it has no older page or its page already reaches
        # back past the horizon; then the next feed starts, until every feed is read.
        finished = next_url is None or (oldest is not None and oldest < horizon)
        if not finished and next_url is not None:
            if urlsplit(next_url).hostname not in HOSTS or urlsplit(next_url).scheme != "https":
                return self._failure("NEXT_LINK_OUTSIDE_PLATFORM", started)
            self._chain.append((feed, next_url))
        elif feed + 1 < len(self._feeds):
            self._chain.append((feed + 1, self._feeds[feed + 1]))
        has_more = len(self._chain) > page
        return self._findings(kept, has_more=has_more, requests=1, started=started)

    def _findings(
        self,
        records: tuple[ProcurementRecord, ...],
        *,
        has_more: bool,
        requests: int,
        started: float,
    ) -> SourceFindings:
        return SourceFindings(
            source_id=PLACSP_SOURCE_ID,
            retrieved_at=self._clock(),
            requests=requests,
            amount_microunits=0,
            latency_ms=int((time.monotonic() - started) * 1000),
            records=records,
            has_more=has_more,
        )

    def _failure(self, reason: str, started: float) -> SourceFindings:
        return SourceFindings(
            source_id=PLACSP_SOURCE_ID,
            retrieved_at=self._clock(),
            requests=1,
            amount_microunits=0,
            latency_ms=int((time.monotonic() - started) * 1000),
            failure=reason,
        )
