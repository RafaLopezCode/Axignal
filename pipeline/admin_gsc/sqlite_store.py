"""Private append-only Google Search Console observations."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from domain.admin_gsc import GscSearchRow, GscSyncRun


class GscStoreConflict(ValueError):
    pass


class SqliteAdminGscStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS gsc_search_rows ("
                "fingerprint TEXT PRIMARY KEY,"
                "property_ref TEXT NOT NULL,"
                "window_start TEXT NOT NULL,"
                "window_end TEXT NOT NULL,"
                "observed_at TEXT NOT NULL,"
                "payload_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_gsc_rows_property_window "
                "ON gsc_search_rows(property_ref, window_end, observed_at)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS gsc_sync_runs ("
                "sync_id TEXT PRIMARY KEY,"
                "property_ref TEXT NOT NULL,"
                "window_start TEXT NOT NULL,"
                "window_end TEXT NOT NULL,"
                "observed_at TEXT NOT NULL,"
                "row_count INTEGER NOT NULL,"
                "source_ref TEXT NOT NULL,"
                "state TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(row: GscSearchRow) -> str:
        return json.dumps(
            {
                "property_ref": row.property_ref,
                "window_start": row.window_start.isoformat(),
                "window_end": row.window_end.isoformat(),
                "dimensions": list(row.dimensions),
                "clicks": row.clicks,
                "impressions": row.impressions,
                "ctr": row.ctr,
                "position": row.position,
                "observed_at": row.observed_at.isoformat(),
                "source_ref": row.source_ref,
                "instrument_version": row.instrument_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_rows(self, rows: tuple[GscSearchRow, ...]) -> int:
        inserted = 0
        with self._connect() as connection:
            for row in rows:
                payload = self._payload(row)
                existing = connection.execute(
                    "SELECT payload_json FROM gsc_search_rows WHERE fingerprint = ?",
                    (row.fingerprint,),
                ).fetchone()
                if existing is not None:
                    # Fingerprint excludes ingestion time; replay of the same measured row is a no-op.
                    continue
                connection.execute(
                    "INSERT INTO gsc_search_rows("
                    "fingerprint, property_ref, window_start, window_end, observed_at, payload_json"
                    ") VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        row.fingerprint,
                        row.property_ref,
                        row.window_start.isoformat(),
                        row.window_end.isoformat(),
                        row.observed_at.isoformat(),
                        payload,
                    ),
                )
                inserted += 1
        return inserted

    @staticmethod
    def _row(record: sqlite3.Row) -> GscSearchRow:
        payload = json.loads(str(record["payload_json"]))
        return GscSearchRow(
            property_ref=payload["property_ref"],
            window_start=date.fromisoformat(payload["window_start"]),
            window_end=date.fromisoformat(payload["window_end"]),
            dimensions=tuple((str(k), str(v)) for k, v in payload["dimensions"]),
            clicks=float(payload["clicks"]),
            impressions=float(payload["impressions"]),
            ctr=float(payload["ctr"]),
            position=float(payload["position"]),
            observed_at=datetime.fromisoformat(payload["observed_at"]),
            source_ref=payload["source_ref"],
            instrument_version=payload["instrument_version"],
        )

    def rows(self, property_ref: str | None = None) -> tuple[GscSearchRow, ...]:
        with self._connect() as connection:
            if property_ref is None:
                records = connection.execute(
                    "SELECT * FROM gsc_search_rows ORDER BY window_end, observed_at, fingerprint"
                ).fetchall()
            else:
                records = connection.execute(
                    "SELECT * FROM gsc_search_rows WHERE property_ref = ? "
                    "ORDER BY window_end, observed_at, fingerprint",
                    (property_ref,),
                ).fetchall()
        return tuple(self._row(record) for record in records)

    def append_sync(self, run: GscSyncRun) -> bool:
        values = (
            run.property_ref,
            run.window_start.isoformat(),
            run.window_end.isoformat(),
            run.observed_at.isoformat(),
            run.row_count,
            run.source_ref,
            run.state,
        )
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT property_ref, window_start, window_end, observed_at, row_count, "
                "source_ref, state FROM gsc_sync_runs WHERE sync_id = ?",
                (run.sync_id,),
            ).fetchone()
            if existing is not None:
                semantic_existing = (
                    str(existing["property_ref"]),
                    str(existing["window_start"]),
                    str(existing["window_end"]),
                    int(existing["row_count"]),
                    str(existing["source_ref"]),
                    str(existing["state"]),
                )
                semantic_values = (
                    run.property_ref,
                    run.window_start.isoformat(),
                    run.window_end.isoformat(),
                    run.row_count,
                    run.source_ref,
                    run.state,
                )
                if semantic_existing == semantic_values:
                    return False
                raise GscStoreConflict("GSC sync id reused with different content")
            connection.execute(
                "INSERT INTO gsc_sync_runs("
                "sync_id, property_ref, window_start, window_end, observed_at, row_count, "
                "source_ref, state) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (run.sync_id, *values),
            )
        return True

    def sync_runs(self) -> tuple[GscSyncRun, ...]:
        with self._connect() as connection:
            records = connection.execute(
                "SELECT * FROM gsc_sync_runs ORDER BY observed_at, sync_id"
            ).fetchall()
        return tuple(
            GscSyncRun(
                sync_id=str(record["sync_id"]),
                property_ref=str(record["property_ref"]),
                window_start=date.fromisoformat(str(record["window_start"])),
                window_end=date.fromisoformat(str(record["window_end"])),
                observed_at=datetime.fromisoformat(str(record["observed_at"])),
                row_count=int(record["row_count"]),
                source_ref=str(record["source_ref"]),
                state=str(record["state"]),
            )
            for record in records
        )
