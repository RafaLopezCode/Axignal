"""Private SEO Production Truth contracts for AXIGNAL's own public origin."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from urllib.parse import urlparse


class CruxFormFactor(StrEnum):
    ALL = "ALL"
    PHONE = "PHONE"
    DESKTOP = "DESKTOP"
    TABLET = "TABLET"


class CruxMetricName(StrEnum):
    LCP = "largest_contentful_paint"
    INP = "interaction_to_next_paint"
    CLS = "cumulative_layout_shift"
    FCP = "first_contentful_paint"
    TTFB = "experimental_time_to_first_byte"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _absolute_web_url(value: str, name: str, *, https_only: bool = False) -> None:
    parsed = urlparse(value)
    allowed = {"https"} if https_only else {"http", "https"}
    if parsed.scheme not in allowed or not parsed.netloc:
        qualifier = "HTTPS" if https_only else "HTTP(S)"
        raise ValueError(f"{name} must be an absolute {qualifier} URL")


@dataclass(frozen=True, slots=True)
class SeoIndexInspection:
    property_ref: str
    inspection_url: str
    verdict: str
    coverage_state: str
    robots_txt_state: str
    indexing_state: str
    page_fetch_state: str
    crawled_as: str | None
    last_crawl_time: datetime | None
    google_canonical: str | None
    user_canonical: str | None
    referring_urls: tuple[str, ...]
    inspected_at: datetime
    source_ref: str
    instrument_version: str = "gsc-url-inspection-v1"

    def __post_init__(self) -> None:
        if not self.property_ref.strip():
            raise ValueError("SEO inspection property_ref is required")
        _absolute_web_url(self.inspection_url, "inspection_url", https_only=True)
        _aware(self.inspected_at, "inspected_at")
        if self.last_crawl_time is not None:
            _aware(self.last_crawl_time, "last_crawl_time")
        for value, name in (
            (self.verdict, "verdict"),
            (self.coverage_state, "coverage_state"),
            (self.robots_txt_state, "robots_txt_state"),
            (self.indexing_state, "indexing_state"),
            (self.page_fetch_state, "page_fetch_state"),
            (self.source_ref, "source_ref"),
            (self.instrument_version, "instrument_version"),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        for optional in (self.google_canonical, self.user_canonical, *self.referring_urls):
            if optional is not None:
                _absolute_web_url(optional, "inspection URL field")

    @property
    def inspection_id(self) -> str:
        raw = json.dumps(
            {
                "url": self.inspection_url,
                "day": self.inspected_at.date().isoformat(),
                "instrument": self.instrument_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return "seo-inspection:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class SeoSitemapSnapshot:
    property_ref: str
    sitemap_url: str
    is_pending: bool
    warnings: int
    errors: int
    submitted_urls: int | None
    indexed_urls: int | None
    last_submitted: datetime | None
    last_downloaded: datetime | None
    observed_at: datetime
    source_ref: str
    instrument_version: str = "gsc-sitemaps-v1"

    def __post_init__(self) -> None:
        if not self.property_ref.strip():
            raise ValueError("sitemap property_ref is required")
        _absolute_web_url(self.sitemap_url, "sitemap_url", https_only=True)
        _aware(self.observed_at, "sitemap observed_at")
        if self.last_submitted is not None:
            _aware(self.last_submitted, "last_submitted")
        if self.last_downloaded is not None:
            _aware(self.last_downloaded, "last_downloaded")
        if self.warnings < 0 or self.errors < 0:
            raise ValueError("sitemap warning/error counts cannot be negative")
        for value in (self.submitted_urls, self.indexed_urls):
            if value is not None and value < 0:
                raise ValueError("sitemap URL counts cannot be negative")
        if not self.source_ref.strip() or not self.instrument_version.strip():
            raise ValueError("sitemap source identity is required")

    @property
    def snapshot_id(self) -> str:
        semantic = json.dumps(
            {
                "url": self.sitemap_url,
                "day": self.observed_at.date().isoformat(),
                "pending": self.is_pending,
                "warnings": self.warnings,
                "errors": self.errors,
                "submitted": self.submitted_urls,
                "indexed": self.indexed_urls,
                "last_submitted": (
                    self.last_submitted.isoformat() if self.last_submitted is not None else None
                ),
                "last_downloaded": (
                    self.last_downloaded.isoformat() if self.last_downloaded is not None else None
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return "gsc-sitemap:" + hashlib.sha256(semantic).hexdigest()


@dataclass(frozen=True, slots=True)
class CruxMetric:
    name: CruxMetricName
    p75: float

    def __post_init__(self) -> None:
        if self.p75 < 0:
            raise ValueError("CrUX p75 cannot be negative")


@dataclass(frozen=True, slots=True)
class CruxSnapshot:
    origin: str
    form_factor: CruxFormFactor
    collection_start: date
    collection_end: date
    metrics: tuple[CruxMetric, ...]
    observed_at: datetime
    source_ref: str
    instrument_version: str = "crux-query-record-v1"

    def __post_init__(self) -> None:
        _absolute_web_url(self.origin, "CrUX origin", https_only=True)
        if self.collection_end < self.collection_start:
            raise ValueError("CrUX collection end cannot precede start")
        _aware(self.observed_at, "CrUX observed_at")
        if not self.metrics:
            raise ValueError("CrUX snapshot requires at least one metric")
        if len({metric.name for metric in self.metrics}) != len(self.metrics):
            raise ValueError("CrUX snapshot metrics must be unique")
        if not self.source_ref.strip() or not self.instrument_version.strip():
            raise ValueError("CrUX source identity is required")

    @property
    def snapshot_id(self) -> str:
        return (
            f"crux:{self.origin.removeprefix('https://').replace('.', '-')}:"
            f"{self.form_factor.value.lower()}:{self.collection_end:%Y%m%d}"
        )
