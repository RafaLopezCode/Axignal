"""Direct Google SEO Production Truth sync without third-party runtime dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from application.admin_measurements import MeasurementRegistryService
from application.admin_seo_truth import record_crux_measurements
from domain.admin_seo_truth import (
    CruxFormFactor,
    CruxMetric,
    CruxMetricName,
    CruxSnapshot,
    SeoIndexInspection,
    SeoSitemapSnapshot,
)
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_measurements import SqliteMeasurementRegistryStore
from pipeline.admin_seo_truth import SqliteSeoTruthStore
from tools.runtime.gsc_sync import GoogleOAuthRefreshCredentials, GoogleSearchConsoleClient

_CRUX_METRICS = tuple(metric.value for metric in CruxMetricName)


class ChromeUxReportClient:
    endpoint = "https://chromeuxreport.googleapis.com/v1/records:queryRecord"

    def __init__(self, api_key: str, *, timeout_seconds: int = 30) -> None:
        key = api_key.strip()
        if not key:
            raise ValueError("CrUX API key is required")
        self._api_key = key
        self._timeout = timeout_seconds

    @classmethod
    def from_file(cls, path: Path) -> ChromeUxReportClient:
        return cls(path.read_text(encoding="utf-8").strip())

    def query(
        self,
        *,
        origin: str,
        form_factor: CruxFormFactor,
    ) -> dict[str, Any] | None:
        body: dict[str, Any] = {"origin": origin, "metrics": list(_CRUX_METRICS)}
        if form_factor is not CruxFormFactor.ALL:
            body["formFactor"] = form_factor.value
        request = Request(
            f"{self.endpoint}?key={quote(self._api_key, safe='')}",
            data=json.dumps(body, separators=(",", ":")).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(f"CRUX_QUERY_FAILED: HTTP_{exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("CRUX_QUERY_FAILED: TRANSPORT_FAILURE") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("CRUX_QUERY_FAILED: INVALID_RESPONSE")
        record = payload.get("record")
        if not isinstance(record, dict):
            raise RuntimeError("CRUX_QUERY_FAILED: RECORD_MISSING")
        return record


def _fetch_sitemap_urls(sitemap_url: str, *, timeout_seconds: int = 30) -> tuple[str, ...]:
    request = Request(
        sitemap_url,
        headers={"User-Agent": "AXIGNAL-SEO-Truth/1.0"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"SEO_SITEMAP_FETCH_FAILED: HTTP_{exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("SEO_SITEMAP_FETCH_FAILED: TRANSPORT_FAILURE") from exc
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise RuntimeError("SEO_SITEMAP_FETCH_FAILED: INVALID_XML") from exc
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls = tuple(
        element.text.strip()
        for element in root.findall(f"{namespace}url/{namespace}loc")
        if element.text and element.text.strip()
    )
    if not urls:
        raise RuntimeError("SEO_SITEMAP_FETCH_FAILED: NO_URLS")
    if len(urls) != len(set(urls)):
        raise RuntimeError("SEO_SITEMAP_FETCH_FAILED: DUPLICATE_URLS")
    return urls


def _ensure_origin(urls: tuple[str, ...], origin: str) -> None:
    expected = urlparse(origin)
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != expected.netloc:
            raise RuntimeError("SEO_SITEMAP_INVALID: URL_OUTSIDE_CANONICAL_ORIGIN")


def _datetime_or_none(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _inspection_source_ref(url: str, day: date) -> str:
    digest = hashlib.sha256(url.encode()).hexdigest()[:20]
    return f"gsc-inspection:{digest}:{day:%Y%m%d}"


def _int_or_none(value: object) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise RuntimeError("GSC_SITEMAPS_FAILED: INVALID_COUNT")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as exc:
            raise RuntimeError("GSC_SITEMAPS_FAILED: INVALID_COUNT") from exc
    raise RuntimeError("GSC_SITEMAPS_FAILED: INVALID_COUNT")


def _sitemap_snapshot(
    *,
    property_ref: str,
    sitemap_url: str,
    raw: dict[str, Any],
    observed_at: datetime,
) -> SeoSitemapSnapshot:
    contents = raw.get("contents", [])
    if not isinstance(contents, list):
        contents = []
    submitted_values = [
        value
        for item in contents
        if isinstance(item, dict)
        for value in [_int_or_none(item.get("submitted"))]
        if value is not None
    ]
    indexed_values = [
        value
        for item in contents
        if isinstance(item, dict)
        for value in [_int_or_none(item.get("indexed"))]
        if value is not None
    ]
    return SeoSitemapSnapshot(
        property_ref=property_ref,
        sitemap_url=sitemap_url,
        is_pending=bool(raw.get("isPending", False)),
        warnings=_int_or_none(raw.get("warnings")) or 0,
        errors=_int_or_none(raw.get("errors")) or 0,
        submitted_urls=sum(submitted_values) if submitted_values else None,
        indexed_urls=sum(indexed_values) if indexed_values else None,
        last_submitted=_datetime_or_none(raw.get("lastSubmitted")),
        last_downloaded=_datetime_or_none(raw.get("lastDownloaded")),
        observed_at=observed_at,
        source_ref=f"gsc-sitemap:axignal-com:{observed_at:%Y%m%d}",
    )


def _inspection(
    *,
    property_ref: str,
    inspection_url: str,
    raw: dict[str, Any],
    inspected_at: datetime,
) -> SeoIndexInspection:
    index = raw.get("indexStatusResult")
    if not isinstance(index, dict):
        raise RuntimeError("GSC_URL_INSPECTION_FAILED: INDEX_STATUS_MISSING")
    refs = index.get("referringUrls", [])
    if not isinstance(refs, list):
        refs = []
    return SeoIndexInspection(
        property_ref=property_ref,
        inspection_url=inspection_url,
        verdict=str(index.get("verdict") or "VERDICT_UNSPECIFIED"),
        coverage_state=str(index.get("coverageState") or "UNKNOWN"),
        robots_txt_state=str(index.get("robotsTxtState") or "ROBOTS_TXT_STATE_UNSPECIFIED"),
        indexing_state=str(index.get("indexingState") or "INDEXING_STATE_UNSPECIFIED"),
        page_fetch_state=str(index.get("pageFetchState") or "PAGE_FETCH_STATE_UNSPECIFIED"),
        crawled_as=(str(index["crawledAs"]) if index.get("crawledAs") else None),
        last_crawl_time=_datetime_or_none(index.get("lastCrawlTime")),
        google_canonical=(str(index["googleCanonical"]) if index.get("googleCanonical") else None),
        user_canonical=(str(index["userCanonical"]) if index.get("userCanonical") else None),
        referring_urls=tuple(str(item) for item in refs if isinstance(item, str)),
        inspected_at=inspected_at,
        source_ref=_inspection_source_ref(inspection_url, inspected_at.date()),
    )


def _date_part(raw: object) -> date:
    if not isinstance(raw, dict):
        raise RuntimeError("CRUX_QUERY_FAILED: COLLECTION_PERIOD_MISSING")
    try:
        return date(int(raw["year"]), int(raw["month"]), int(raw["day"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("CRUX_QUERY_FAILED: INVALID_COLLECTION_DATE") from exc


def _crux_snapshot(
    *,
    origin: str,
    form_factor: CruxFormFactor,
    raw: dict[str, Any],
) -> CruxSnapshot:
    period = raw.get("collectionPeriod")
    if not isinstance(period, dict):
        raise RuntimeError("CRUX_QUERY_FAILED: COLLECTION_PERIOD_MISSING")
    collection_start = _date_part(period.get("firstDate"))
    collection_end = _date_part(period.get("lastDate"))
    raw_metrics = raw.get("metrics")
    if not isinstance(raw_metrics, dict):
        raise RuntimeError("CRUX_QUERY_FAILED: METRICS_MISSING")
    metrics: list[CruxMetric] = []
    for name in CruxMetricName:
        payload = raw_metrics.get(name.value)
        if not isinstance(payload, dict):
            continue
        percentiles = payload.get("percentiles")
        if not isinstance(percentiles, dict) or "p75" not in percentiles:
            continue
        try:
            p75 = float(percentiles["p75"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("CRUX_QUERY_FAILED: INVALID_P75") from exc
        metrics.append(CruxMetric(name=name, p75=p75))
    if not metrics:
        raise RuntimeError("CRUX_QUERY_FAILED: NO_REQUESTED_METRICS")
    observed_at = datetime.combine(collection_end, time.max, tzinfo=UTC)
    source_ref = f"crux:axignal-com:{form_factor.value.lower()}:{collection_end:%Y%m%d}"
    return CruxSnapshot(
        origin=origin,
        form_factor=form_factor,
        collection_start=collection_start,
        collection_end=collection_end,
        metrics=tuple(metrics),
        observed_at=observed_at,
        source_ref=source_ref,
    )


def _coverage_counts(items: tuple[SeoIndexInspection, ...], day: date) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if item.inspected_at.date() != day:
            continue
        counts[item.coverage_state] = counts.get(item.coverage_state, 0) + 1
    return dict(sorted(counts.items()))


def run_sync(*, now: datetime | None = None) -> dict[str, object]:
    enabled = os.getenv("AXIGNAL_SEO_TRUTH_ENABLED", "").strip().lower() in {"1", "true", "yes"}
    if not enabled:
        return {"state": "DISABLED"}

    data_dir_raw = os.getenv("AXIGNAL_DATA_DIR", "").strip()
    oauth_path_raw = os.getenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", "").strip()
    crux_path_raw = os.getenv("AXIGNAL_CRUX_API_KEY_FILE", "").strip()
    property_ref = os.getenv("AXIGNAL_GSC_PROPERTY", "sc-domain:axignal.com").strip()
    origin = os.getenv("AXIGNAL_PUBLIC_ORIGIN", "https://axignal.com").strip().rstrip("/")
    sitemap_url = os.getenv("AXIGNAL_SEO_SITEMAP_URL", f"{origin}/sitemap.xml").strip()
    limit_raw = os.getenv("AXIGNAL_SEO_INSPECTION_LIMIT", "750").strip()

    if not data_dir_raw or not oauth_path_raw or not property_ref or not origin or not sitemap_url:
        return {"state": "NOT_CONFIGURED"}
    data_dir = Path(data_dir_raw).expanduser().resolve()
    oauth_path = Path(oauth_path_raw).expanduser().resolve()
    if not oauth_path.is_file():
        return {"state": "NOT_CONFIGURED"}
    try:
        inspection_limit = int(limit_raw)
    except ValueError as exc:
        raise ValueError("AXIGNAL_SEO_INSPECTION_LIMIT must be an integer") from exc
    if not 1 <= inspection_limit <= 1500:
        raise ValueError("AXIGNAL_SEO_INSPECTION_LIMIT must be between 1 and 1500")

    wall_clock = now or datetime.now(UTC)
    inspected_at = datetime.combine(wall_clock.date(), time.min, tzinfo=UTC)
    urls = _fetch_sitemap_urls(sitemap_url)
    _ensure_origin(urls, origin)

    store = SqliteSeoTruthStore(data_dir / "admin-seo-truth.sqlite3")
    credentials = GoogleOAuthRefreshCredentials.from_file(oauth_path)
    gsc = GoogleSearchConsoleClient(credentials)

    sitemap_state: dict[str, object] = {"state": "NOT_SUBMITTED"}
    submitted_sitemaps = gsc.list_sitemaps(property_ref=property_ref)
    canonical_sitemap = next(
        (item for item in submitted_sitemaps if str(item.get("path", "")).strip() == sitemap_url),
        None,
    )
    if canonical_sitemap is not None:
        sitemap_snapshot = _sitemap_snapshot(
            property_ref=property_ref,
            sitemap_url=sitemap_url,
            raw=canonical_sitemap,
            observed_at=inspected_at,
        )
        store.append_sitemap(sitemap_snapshot)
        sitemap_state = {
            "state": "OBSERVED",
            "pending": sitemap_snapshot.is_pending,
            "warnings": sitemap_snapshot.warnings,
            "errors": sitemap_snapshot.errors,
            "submitted": sitemap_snapshot.submitted_urls,
            "indexed": sitemap_snapshot.indexed_urls,
        }

    inspected = 0
    skipped = 0
    for url in urls:
        if store.has_inspection_on(url, inspected_at.date()):
            skipped += 1
            continue
        if inspected >= inspection_limit:
            break
        raw = gsc.inspect_url(property_ref=property_ref, inspection_url=url)
        store.append_inspection(
            _inspection(
                property_ref=property_ref,
                inspection_url=url,
                raw=raw,
                inspected_at=inspected_at,
            )
        )
        inspected += 1

    crux_state = "NOT_CONFIGURED"
    crux_observations: list[str] = []
    crux_snapshots = 0
    crux_path = Path(crux_path_raw).expanduser().resolve() if crux_path_raw else None
    if crux_path is not None and crux_path.is_file():
        crux = ChromeUxReportClient.from_file(crux_path)
        registry = MeasurementRegistryService(
            SqliteMeasurementRegistryStore(data_dir / "admin-measurements.sqlite3"),
            SqliteAdminGovernanceAuditStore(data_dir / "admin-governance-audit.sqlite3"),
        )
        crux_state = "INSUFFICIENT_DATA"
        for form_factor in (
            CruxFormFactor.ALL,
            CruxFormFactor.PHONE,
            CruxFormFactor.DESKTOP,
        ):
            crux_raw = crux.query(origin=origin, form_factor=form_factor)
            if crux_raw is None:
                continue
            snapshot = _crux_snapshot(origin=origin, form_factor=form_factor, raw=crux_raw)
            store.append_crux(snapshot)
            crux_observations.extend(
                record_crux_measurements(registry=registry, snapshot=snapshot, now=inspected_at)
            )
            crux_snapshots += 1
        if crux_snapshots:
            crux_state = "MEASURED"

    day_inspections = tuple(
        item for item in store.inspections() if item.inspected_at.date() == inspected_at.date()
    )
    return {
        "state": "COMPLETED",
        "property": property_ref,
        "origin": origin,
        "sitemap": sitemap_url,
        "sitemapUrls": len(urls),
        "gscSitemap": sitemap_state,
        "inspectedToday": len(day_inspections),
        "newInspections": inspected,
        "replaySkipped": skipped,
        "remainingToday": max(0, len(urls) - len(day_inspections)),
        "coverage": _coverage_counts(day_inspections, inspected_at.date()),
        "cruxState": crux_state,
        "cruxSnapshots": crux_snapshots,
        "cruxMeasurementObservations": crux_observations,
    }


def main() -> None:
    try:
        result = run_sync()
    except Exception as exc:
        print(json.dumps({"state": "FAILED", "error": type(exc).__name__}, sort_keys=True))
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))
    if result["state"] == "NOT_CONFIGURED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
