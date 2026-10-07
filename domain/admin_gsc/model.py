"""AO-13 private Google Search Console measurement contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class GscDimension(StrEnum):
    QUERY = "query"
    PAGE = "page"
    COUNTRY = "country"
    DEVICE = "device"
    SEARCH_APPEARANCE = "searchAppearance"


@dataclass(frozen=True, slots=True)
class GscSearchRow:
    property_ref: str
    window_start: date
    window_end: date
    dimensions: tuple[tuple[str, str], ...]
    clicks: float
    impressions: float
    ctr: float
    position: float
    observed_at: datetime
    source_ref: str
    instrument_version: str = "gsc-search-analytics-v1"

    def __post_init__(self) -> None:
        if not self.property_ref.strip():
            raise ValueError("GSC property_ref is required")
        if self.window_end < self.window_start:
            raise ValueError("GSC window end cannot precede start")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("GSC observed_at must be timezone-aware")
        if self.clicks < 0 or self.impressions < 0:
            raise ValueError("GSC clicks/impressions cannot be negative")
        if not 0 <= self.ctr <= 1:
            raise ValueError("GSC ctr must be between zero and one")
        if self.position < 0:
            raise ValueError("GSC position cannot be negative")
        if not self.source_ref.strip():
            raise ValueError("GSC source_ref is required")
        seen: set[str] = set()
        allowed = {item.value for item in GscDimension}
        for name, value in self.dimensions:
            if name not in allowed:
                raise ValueError("unsupported GSC dimension")
            if name in seen:
                raise ValueError("GSC dimensions must be unique")
            if not value:
                raise ValueError("GSC dimension values cannot be empty")
            seen.add(name)

    @property
    def fingerprint(self) -> str:
        payload = {
            "property_ref": self.property_ref,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "dimensions": list(self.dimensions),
            "clicks": self.clicks,
            "impressions": self.impressions,
            "ctr": self.ctr,
            "position": self.position,
            "source_ref": self.source_ref,
            "instrument_version": self.instrument_version,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class GscSyncRun:
    sync_id: str
    property_ref: str
    window_start: date
    window_end: date
    observed_at: datetime
    row_count: int
    source_ref: str
    state: str

    def __post_init__(self) -> None:
        if not self.sync_id.strip() or not self.property_ref.strip() or not self.source_ref.strip():
            raise ValueError("GSC sync identity fields are required")
        if self.window_end < self.window_start:
            raise ValueError("GSC sync window end cannot precede start")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("GSC sync observed_at must be timezone-aware")
        if self.row_count < 0:
            raise ValueError("GSC sync row_count cannot be negative")
        if self.state not in {"COMPLETED", "FAILED"}:
            raise ValueError("unsupported GSC sync state")


@dataclass(frozen=True, slots=True)
class GscPrivateAnalyticsProjection:
    privacy_class: str
    generated_at: datetime
    property_ref: str | None
    latest_window_start: date | None
    latest_window_end: date | None
    latest_sync_at: datetime | None
    latest_row_count: int
    breakdown_counts: tuple[tuple[str, int], ...]
    coverage_notes: tuple[str, ...]
