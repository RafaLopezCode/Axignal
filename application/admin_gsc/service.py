"""AO-13 private GSC ingestion and projection."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime
from typing import Protocol

from domain.admin_gsc import GscPrivateAnalyticsProjection, GscSearchRow, GscSyncRun


class GscStore(Protocol):
    def append_rows(self, rows: tuple[GscSearchRow, ...]) -> int: ...
    def append_sync(self, run: GscSyncRun) -> bool: ...
    def rows(self, property_ref: str | None = None) -> tuple[GscSearchRow, ...]: ...
    def sync_runs(self) -> tuple[GscSyncRun, ...]: ...


class GscIngestionService:
    def __init__(self, store: GscStore) -> None:
        self._store = store

    def ingest(
        self,
        *,
        sync_id: str,
        property_ref: str,
        rows: tuple[GscSearchRow, ...],
        window_start: date,
        window_end: date,
        observed_at: datetime,
        source_ref: str,
    ) -> int:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("GSC ingestion observed_at must be timezone-aware")
        if any(row.property_ref != property_ref for row in rows):
            raise ValueError("GSC ingestion cannot mix properties")
        if any(row.window_start != window_start or row.window_end != window_end for row in rows):
            raise ValueError("GSC ingestion cannot mix measurement windows")
        inserted = self._store.append_rows(rows)
        self._store.append_sync(
            GscSyncRun(
                sync_id=sync_id,
                property_ref=property_ref,
                window_start=window_start,
                window_end=window_end,
                observed_at=observed_at,
                row_count=len(rows),
                source_ref=source_ref,
                state="COMPLETED",
            )
        )
        return inserted


def project_private_gsc(
    *,
    store: GscStore,
    generated_at: datetime,
) -> GscPrivateAnalyticsProjection:
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("GSC projection time must be timezone-aware")
    runs = tuple(run for run in store.sync_runs() if run.state == "COMPLETED")
    if not runs:
        return GscPrivateAnalyticsProjection(
            privacy_class="PRIVATE_AXIGNAL_GSC",
            generated_at=generated_at,
            property_ref=None,
            latest_window_start=None,
            latest_window_end=None,
            latest_sync_at=None,
            latest_row_count=0,
            breakdown_counts=(),
            coverage_notes=(
                "No Search Console sync has been recorded.",
                "GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION.",
            ),
        )
    latest = max(runs, key=lambda item: (item.window_end, item.observed_at, item.sync_id))
    rows = tuple(
        row
        for row in store.rows(latest.property_ref)
        if row.window_start == latest.window_start and row.window_end == latest.window_end
    )
    counts: Counter[str] = Counter()
    for row in rows:
        key = "+".join(name for name, _ in row.dimensions) or "summary"
        counts[key] += 1
    return GscPrivateAnalyticsProjection(
        privacy_class="PRIVATE_AXIGNAL_GSC",
        generated_at=generated_at,
        property_ref=latest.property_ref,
        latest_window_start=latest.window_start,
        latest_window_end=latest.window_end,
        latest_sync_at=latest.observed_at.astimezone(UTC),
        latest_row_count=len(rows),
        breakdown_counts=tuple(sorted(counts.items())),
        coverage_notes=(
            "Search Console data is private AXIGNAL operating evidence, not AXIGLAND truth.",
            "Rows preserve property, period, dimensions, instrument version and source reference.",
            "Missing Search Console rows are not interpreted as zero global demand.",
            "GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION.",
        ),
    )
