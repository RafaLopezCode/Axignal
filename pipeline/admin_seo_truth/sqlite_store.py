"""SQLite persistence for private SEO Production Truth observations."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from domain.admin_seo_truth import (
    CruxFormFactor,
    CruxMetric,
    CruxMetricName,
    CruxSnapshot,
    SeoIndexInspection,
    SeoSitemapSnapshot,
)


class SeoTruthStoreConflict(ValueError):
    pass


class SqliteSeoTruthStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS seo_url_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    inspection_url TEXT NOT NULL,
                    inspected_day TEXT NOT NULL,
                    inspected_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_seo_url_inspections_url_day
                    ON seo_url_inspections(inspection_url, inspected_day);

                CREATE TABLE IF NOT EXISTS seo_sitemap_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    sitemap_url TEXT NOT NULL,
                    observed_day TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_seo_sitemap_url_day
                    ON seo_sitemap_snapshots(sitemap_url, observed_day);

                CREATE TABLE IF NOT EXISTS seo_crux_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    origin TEXT NOT NULL,
                    form_factor TEXT NOT NULL,
                    collection_end TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_seo_crux_origin_end
                    ON seo_crux_snapshots(origin, collection_end, form_factor);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _inspection_payload(item: SeoIndexInspection) -> str:
        return json.dumps(
            {
                "property_ref": item.property_ref,
                "inspection_url": item.inspection_url,
                "verdict": item.verdict,
                "coverage_state": item.coverage_state,
                "robots_txt_state": item.robots_txt_state,
                "indexing_state": item.indexing_state,
                "page_fetch_state": item.page_fetch_state,
                "crawled_as": item.crawled_as,
                "last_crawl_time": (
                    item.last_crawl_time.isoformat() if item.last_crawl_time is not None else None
                ),
                "google_canonical": item.google_canonical,
                "user_canonical": item.user_canonical,
                "referring_urls": list(item.referring_urls),
                "inspected_at": item.inspected_at.isoformat(),
                "source_ref": item.source_ref,
                "instrument_version": item.instrument_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_inspection(self, item: SeoIndexInspection) -> bool:
        payload = self._inspection_payload(item)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM seo_url_inspections WHERE inspection_id = ?",
                (item.inspection_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise SeoTruthStoreConflict("SEO inspection id reused with different content")
            connection.execute(
                "INSERT INTO seo_url_inspections("
                "inspection_id, inspection_url, inspected_day, inspected_at, payload_json"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    item.inspection_id,
                    item.inspection_url,
                    item.inspected_at.date().isoformat(),
                    item.inspected_at.isoformat(),
                    payload,
                ),
            )
        return True

    def has_inspection_on(self, inspection_url: str, inspected_day: date) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM seo_url_inspections "
                "WHERE inspection_url = ? AND inspected_day = ? LIMIT 1",
                (inspection_url, inspected_day.isoformat()),
            ).fetchone()
        return row is not None

    def inspections(self) -> tuple[SeoIndexInspection, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM seo_url_inspections ORDER BY inspected_at, inspection_url"
            ).fetchall()
        result: list[SeoIndexInspection] = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                SeoIndexInspection(
                    property_ref=p["property_ref"],
                    inspection_url=p["inspection_url"],
                    verdict=p["verdict"],
                    coverage_state=p["coverage_state"],
                    robots_txt_state=p["robots_txt_state"],
                    indexing_state=p["indexing_state"],
                    page_fetch_state=p["page_fetch_state"],
                    crawled_as=p["crawled_as"],
                    last_crawl_time=(
                        datetime.fromisoformat(p["last_crawl_time"])
                        if p["last_crawl_time"] is not None
                        else None
                    ),
                    google_canonical=p["google_canonical"],
                    user_canonical=p["user_canonical"],
                    referring_urls=tuple(p["referring_urls"]),
                    inspected_at=datetime.fromisoformat(p["inspected_at"]),
                    source_ref=p["source_ref"],
                    instrument_version=p["instrument_version"],
                )
            )
        return tuple(result)

    @staticmethod
    def _sitemap_payload(item: SeoSitemapSnapshot) -> str:
        return json.dumps(
            {
                "property_ref": item.property_ref,
                "sitemap_url": item.sitemap_url,
                "is_pending": item.is_pending,
                "warnings": item.warnings,
                "errors": item.errors,
                "submitted_urls": item.submitted_urls,
                "indexed_urls": item.indexed_urls,
                "last_submitted": (
                    item.last_submitted.isoformat() if item.last_submitted is not None else None
                ),
                "last_downloaded": (
                    item.last_downloaded.isoformat() if item.last_downloaded is not None else None
                ),
                "observed_at": item.observed_at.isoformat(),
                "source_ref": item.source_ref,
                "instrument_version": item.instrument_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_sitemap(self, item: SeoSitemapSnapshot) -> bool:
        payload = self._sitemap_payload(item)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM seo_sitemap_snapshots WHERE snapshot_id = ?",
                (item.snapshot_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise SeoTruthStoreConflict("sitemap snapshot id reused with different content")
            connection.execute(
                "INSERT INTO seo_sitemap_snapshots("
                "snapshot_id, sitemap_url, observed_day, observed_at, payload_json"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    item.snapshot_id,
                    item.sitemap_url,
                    item.observed_at.date().isoformat(),
                    item.observed_at.isoformat(),
                    payload,
                ),
            )
        return True

    def sitemap_snapshots(self) -> tuple[SeoSitemapSnapshot, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM seo_sitemap_snapshots ORDER BY observed_at, sitemap_url"
            ).fetchall()
        result: list[SeoSitemapSnapshot] = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                SeoSitemapSnapshot(
                    property_ref=p["property_ref"],
                    sitemap_url=p["sitemap_url"],
                    is_pending=bool(p["is_pending"]),
                    warnings=int(p["warnings"]),
                    errors=int(p["errors"]),
                    submitted_urls=(
                        int(p["submitted_urls"]) if p["submitted_urls"] is not None else None
                    ),
                    indexed_urls=(
                        int(p["indexed_urls"]) if p["indexed_urls"] is not None else None
                    ),
                    last_submitted=(
                        datetime.fromisoformat(p["last_submitted"])
                        if p["last_submitted"] is not None
                        else None
                    ),
                    last_downloaded=(
                        datetime.fromisoformat(p["last_downloaded"])
                        if p["last_downloaded"] is not None
                        else None
                    ),
                    observed_at=datetime.fromisoformat(p["observed_at"]),
                    source_ref=p["source_ref"],
                    instrument_version=p["instrument_version"],
                )
            )
        return tuple(result)

    @staticmethod
    def _crux_payload(item: CruxSnapshot) -> str:
        return json.dumps(
            {
                "origin": item.origin,
                "form_factor": item.form_factor.value,
                "collection_start": item.collection_start.isoformat(),
                "collection_end": item.collection_end.isoformat(),
                "metrics": [
                    {"name": metric.name.value, "p75": metric.p75} for metric in item.metrics
                ],
                "observed_at": item.observed_at.isoformat(),
                "source_ref": item.source_ref,
                "instrument_version": item.instrument_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_crux(self, item: CruxSnapshot) -> bool:
        payload = self._crux_payload(item)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM seo_crux_snapshots WHERE snapshot_id = ?",
                (item.snapshot_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise SeoTruthStoreConflict("CrUX snapshot id reused with different content")
            connection.execute(
                "INSERT INTO seo_crux_snapshots("
                "snapshot_id, origin, form_factor, collection_end, observed_at, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.snapshot_id,
                    item.origin,
                    item.form_factor.value,
                    item.collection_end.isoformat(),
                    item.observed_at.isoformat(),
                    payload,
                ),
            )
        return True

    def crux_snapshots(self) -> tuple[CruxSnapshot, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM seo_crux_snapshots "
                "ORDER BY collection_end, form_factor, observed_at"
            ).fetchall()
        result: list[CruxSnapshot] = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                CruxSnapshot(
                    origin=p["origin"],
                    form_factor=CruxFormFactor(p["form_factor"]),
                    collection_start=date.fromisoformat(p["collection_start"]),
                    collection_end=date.fromisoformat(p["collection_end"]),
                    metrics=tuple(
                        CruxMetric(name=CruxMetricName(metric["name"]), p75=float(metric["p75"]))
                        for metric in p["metrics"]
                    ),
                    observed_at=datetime.fromisoformat(p["observed_at"]),
                    source_ref=p["source_ref"],
                    instrument_version=p["instrument_version"],
                )
            )
        return tuple(result)
