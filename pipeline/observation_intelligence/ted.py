"""TED Search API v3 adapter for the Economic Observation Intelligence Layer.

Built against the published contract (``POST /v3/notices/search``, anonymous,
expert-query syntax) and the observed response shape: multilingual text maps,
repeated code lists and eForms notice-type codes. It returns provider-neutral
records; it never interprets fit, admits evidence or writes canonical state.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any, Protocol

from application.observation_intelligence import (
    ObservationAction,
    ProcurementRecord,
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    SourceFindings,
    TaxonomyCode,
)
from application.observation_intelligence.catalog import eu_nuts
from application.observation_intelligence.contracts import geo

TED_SOURCE_ID = "ted-search-v3"
TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"
_MAX_RESPONSE_BYTES = 5_000_000
_FIELDS = (
    "publication-number",
    "notice-title",
    "notice-type",
    "buyer-name",
    "classification-cpv",
    "place-of-performance",
    "publication-date",
    "deadline-receipt-tender-date-lot",
    "winner-name",
)
_NOTICE_TYPES = {
    SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES: ("cn-standard", "cn-social"),
    SourceCapability.PUBLIC_PROCUREMENT_AWARDS: ("can-standard", "can-social"),
}
# NUTS level-0 codes as TED expects country places (ISO 3166-1 alpha-3).
_NUTS0_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "SE": "SWE", "SI": "SVN", "SK": "SVK",
}  # fmt: skip
_ISO3_TO_NUTS0 = {iso3: nuts0 for nuts0, iso3 in _NUTS0_TO_ISO3.items()}
_LANGUAGES = ("spa", "fra", "eng", "deu", "ita", "por")


class TedTransport(Protocol):
    def post(self, body: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]: ...


class UrllibTedTransport:
    """Fixed-endpoint HTTPS transport with a timeout and a response size cap."""

    def __init__(self, *, timeout_s: float = 20.0) -> None:
        self._timeout_s = timeout_s

    def post(self, body: Mapping[str, Any]) -> tuple[int, Mapping[str, Any]]:
        request = urllib.request.Request(
            TED_SEARCH_URL,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
                status = response.status
        except urllib.error.HTTPError as error:
            return error.code, {}
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise ValueError("TED response exceeds the size cap")
        return status, json.loads(raw)


def expert_query(query: QuerySpec) -> str:
    """Translate a provider-neutral query into TED expert-query syntax."""

    parts: list[str] = []
    cpv = [code.code for code in query.demand_codes if code.scheme == "CPV"]
    if cpv:
        parts.append(f"classification-cpv IN ({' '.join(cpv)})")
    places = [place for code in query.geographies if (place := _ted_place(code))]
    if places:
        parts.append(f"place-of-performance IN ({' '.join(places)})")
    types = [t for kind in sorted(query.capabilities) for t in _NOTICE_TYPES.get(kind, ())]
    if types:
        parts.append(f"notice-type IN ({' '.join(types)})")
    if query.published_since is not None:
        parts.append(f"publication-date>={query.published_since.strftime('%Y%m%d')}")
    if query.open_on is not None:
        parts.append(f"deadline-receipt-tender-date-lot>={query.open_on.strftime('%Y%m%d')}")
    if not parts:
        raise ValueError("TED query requires at least one criterion")
    return " AND ".join(parts) + " SORT BY publication-date DESC"


def _text(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        return next((t for item in value if (t := _text(item))), None)
    if isinstance(value, Mapping):
        for language in (*_LANGUAGES, *sorted(value)):
            if language in value and (text := _text(value[language])):
                return text
    return None


def _all_texts(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, list):
        return tuple(dict.fromkeys(t for item in value for t in _all_texts(item)))
    if isinstance(value, Mapping):
        language = next((key for key in (*_LANGUAGES, *sorted(value)) if key in value), None)
        return _all_texts(value[language]) if language else ()
    return ()


def _ted_place(code: TaxonomyCode) -> str | None:
    """Jurisdiction path → TED place: EU/ES → ESP (country), EU/ES/ES5/ES52 → ES52 (NUTS)."""

    segments = code.code.split("/") if code.scheme == "GEO" else []
    if len(segments) < 2 or segments[0] != "EU":
        return None
    return _NUTS0_TO_ISO3.get(segments[1]) if len(segments) == 2 else segments[-1]


def _codes(value: object) -> tuple[str, ...]:
    values = value if isinstance(value, list) else [value] if isinstance(value, str) else []
    return tuple(sorted({item for item in values if isinstance(item, str) and item.strip()}))


def _places(value: object) -> tuple[TaxonomyCode, ...]:
    """TED places (ISO3 countries or NUTS codes) → jurisdiction paths."""

    return tuple(
        sorted(
            {
                geo(f"EU/{_ISO3_TO_NUTS0[item]}") if item in _ISO3_TO_NUTS0 else eu_nuts(item)
                for item in _codes(value)
            }
        )
    )


def _date(value: object) -> datetime | None:
    """TED dates look like ``2026-08-03+02:00``; keep the published offset."""

    text = _text(value)
    if text is None:
        return None
    offset = text[10:]
    try:
        return datetime.fromisoformat(
            f"{text[:10]}T00:00:00{'+00:00' if offset in ('', 'Z') else offset}"
        )
    except ValueError:
        return None


def parse_notices(payload: Mapping[str, Any]) -> tuple[ProcurementRecord, ...]:
    records: list[ProcurementRecord] = []
    for notice in payload.get("notices") or ():
        if not isinstance(notice, Mapping):
            continue
        number = _text(notice.get("publication-number"))
        notice_type = _text(notice.get("notice-type")) or ""
        kind = (
            SourceCapability.PUBLIC_PROCUREMENT_AWARDS
            if notice_type.startswith("can")
            else SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
            if notice_type.startswith("cn")
            else None
        )
        title = _text(notice.get("notice-title"))
        published = _date(notice.get("publication-date"))
        if number is None or kind is None or title is None or published is None:
            continue
        records.append(
            ProcurementRecord(
                record_id=f"ted:{number}",
                source_id=TED_SOURCE_ID,
                kind=kind,
                title=title,
                buyer_name=_text(notice.get("buyer-name")),
                places=_places(notice.get("place-of-performance")),
                demand_codes=tuple(
                    TaxonomyCode("CPV", c) for c in _codes(notice.get("classification-cpv"))
                ),
                published_at=published,
                source_url=f"https://ted.europa.eu/en/notice/-/detail/{number}",
                deadline=max(
                    _all_texts(notice.get("deadline-receipt-tender-date-lot")), default=None
                ),
                winners=_all_texts(notice.get("winner-name")),
            )
        )
    return tuple(records)


class TedSearchAdapter:
    """One bounded search request per action; failures are recorded, never guessed."""

    def __init__(
        self,
        transport: TedTransport,
        *,
        clock: Callable[[], datetime],
        limit: int = 20,
    ) -> None:
        if not 1 <= limit <= 100:
            raise ValueError("TED page limit must be between 1 and 100")
        self._transport = transport
        self._clock = clock
        self._limit = limit

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        if source.source_id != TED_SOURCE_ID or action.source_id != TED_SOURCE_ID:
            raise ValueError("TED adapter only serves the TED source capability")
        return self.search(action.query, page=1)

    def search(self, query: QuerySpec, *, page: int, limit: int | None = None) -> SourceFindings:
        """One page of one expert query (world-slice ingestion pages through it)."""
        size = self._limit if limit is None else limit
        if page < 1 or not 1 <= size <= 100:
            raise ValueError("TED page must be >= 1 and limit between 1 and 100")
        body = {
            "query": expert_query(query),
            "fields": list(_FIELDS),
            "page": page,
            "limit": size,
        }
        started = time.monotonic()
        try:
            status, payload = self._transport.post(body)
        except (OSError, ValueError) as error:
            return self._failure(f"TRANSPORT:{type(error).__name__}", started)
        if status != 200:
            return self._failure(f"HTTP_{status}", started)
        if payload.get("timedOut") is True:
            return self._failure("SOURCE_TIMED_OUT", started)
        total = payload.get("totalNoticeCount")
        return SourceFindings(
            source_id=TED_SOURCE_ID,
            retrieved_at=self._clock(),
            requests=1,
            amount_microunits=0,
            latency_ms=int((time.monotonic() - started) * 1000),
            records=parse_notices(payload),
            total_available=total if isinstance(total, int) else None,
        )

    def _failure(self, reason: str, started: float) -> SourceFindings:
        return SourceFindings(
            source_id=TED_SOURCE_ID,
            retrieved_at=self._clock(),
            requests=1,
            amount_microunits=0,
            latency_ms=int((time.monotonic() - started) * 1000),
            failure=reason,
        )
