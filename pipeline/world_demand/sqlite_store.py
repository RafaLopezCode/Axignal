"""World demand index storage: public procurement records and slice states.

Records are public source observations with their original URL and publication time;
nothing tenant-specific is stored here (which Focus asked is never recorded).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode
from application.observation_intelligence.findings import ProcurementRecord
from application.world_demand.index import DemandSlice, SliceState, country_of


def _encode(record: ProcurementRecord) -> str:
    return json.dumps(
        {
            "record_id": record.record_id,
            "source_id": record.source_id,
            "kind": record.kind.value,
            "title": record.title,
            "buyer_name": record.buyer_name,
            "places": [[p.scheme, p.code] for p in record.places],
            "demand_codes": [[c.scheme, c.code] for c in record.demand_codes],
            "published_at": record.published_at.isoformat(),
            "source_url": record.source_url,
            "deadline": record.deadline,
            "winners": list(record.winners),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _decode(raw: dict[str, Any]) -> ProcurementRecord:
    return ProcurementRecord(
        record_id=str(raw["record_id"]),
        source_id=str(raw["source_id"]),
        kind=SourceCapability(str(raw["kind"])),
        title=str(raw["title"]),
        buyer_name=None if raw["buyer_name"] is None else str(raw["buyer_name"]),
        places=tuple(TaxonomyCode(str(s), str(c)) for s, c in raw["places"]),
        demand_codes=tuple(TaxonomyCode(str(s), str(c)) for s, c in raw["demand_codes"]),
        published_at=datetime.fromisoformat(str(raw["published_at"])),
        source_url=str(raw["source_url"]),
        deadline=None if raw["deadline"] is None else str(raw["deadline"]),
        winners=tuple(str(w) for w in raw["winners"]),
    )


def _time(value: object) -> datetime | None:
    return None if value is None else datetime.fromisoformat(str(value))


class SqliteWorldDemandIndex:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS wd_records (
                    source_id TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    PRIMARY KEY (source_id, record_id)
                );
                CREATE TABLE IF NOT EXISTS wd_record_countries (
                    source_id TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    country TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    PRIMARY KEY (source_id, record_id, country)
                );
                CREATE INDEX IF NOT EXISTS idx_wd_country
                    ON wd_record_countries(source_id, country, kind);
                CREATE TABLE IF NOT EXISTS wd_slices (
                    slice_key TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    jurisdiction TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    demanded_at TEXT,
                    ingested_at TEXT,
                    window_start TEXT,
                    complete INTEGER NOT NULL DEFAULT 0,
                    requests INTEGER NOT NULL DEFAULT 0,
                    records INTEGER NOT NULL DEFAULT 0
                );
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _state(row: sqlite3.Row) -> SliceState:
        return SliceState(
            slice=DemandSlice(
                str(row["source_id"]), str(row["jurisdiction"]), SourceCapability(str(row["kind"]))
            ),
            ingested_at=_time(row["ingested_at"]),
            window_start=_time(row["window_start"]),
            complete=bool(row["complete"]),
            requests=int(row["requests"]),
            records=int(row["records"]),
            demanded_at=_time(row["demanded_at"]),
        )

    def state(self, demand_slice: DemandSlice) -> SliceState | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM wd_slices WHERE slice_key=?", (demand_slice.key,)
            ).fetchone()
        return None if row is None else self._state(row)

    def demand(self, demand_slice: DemandSlice, *, now: datetime) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO wd_slices (slice_key, source_id, jurisdiction, kind, demanded_at)
                VALUES (?,?,?,?,?) ON CONFLICT(slice_key) DO UPDATE SET
                demanded_at=excluded.demanded_at""",
                (
                    demand_slice.key,
                    demand_slice.source_id,
                    demand_slice.jurisdiction,
                    demand_slice.kind.value,
                    now.isoformat(),
                ),
            )

    def demanded(self) -> tuple[SliceState, ...]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM wd_slices WHERE demanded_at IS NOT NULL ORDER BY demanded_at"
            ).fetchall()
        return tuple(self._state(row) for row in rows)

    def upsert(self, records: Sequence[ProcurementRecord]) -> int:
        with self._connect() as db:
            for record in records:
                db.execute(
                    """INSERT INTO wd_records VALUES (?,?,?,?,?)
                    ON CONFLICT(source_id, record_id) DO UPDATE SET payload=excluded.payload""",
                    (
                        record.source_id,
                        record.record_id,
                        record.kind.value,
                        _encode(record),
                        record.published_at.isoformat(),
                    ),
                )
                for country in {c for p in record.places if (c := country_of(p))}:
                    db.execute(
                        "INSERT OR IGNORE INTO wd_record_countries VALUES (?,?,?,?)",
                        (record.source_id, record.record_id, country, record.kind.value),
                    )
        return len(records)

    def mark_ingested(
        self,
        demand_slice: DemandSlice,
        *,
        at: datetime,
        window_start: datetime,
        complete: bool,
        requests: int,
        records: int,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO wd_slices (slice_key, source_id, jurisdiction, kind, ingested_at,
                window_start, complete, requests, records) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(slice_key) DO UPDATE SET ingested_at=excluded.ingested_at,
                window_start=excluded.window_start, complete=excluded.complete,
                requests=excluded.requests, records=excluded.records""",
                (
                    demand_slice.key,
                    demand_slice.source_id,
                    demand_slice.jurisdiction,
                    demand_slice.kind.value,
                    at.isoformat(),
                    window_start.isoformat(),
                    int(complete),
                    requests,
                    records,
                ),
            )

    def records(self, demand_slice: DemandSlice) -> tuple[ProcurementRecord, ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT r.payload FROM wd_records r JOIN wd_record_countries c
                ON r.source_id=c.source_id AND r.record_id=c.record_id
                WHERE c.source_id=? AND c.country=? AND c.kind=?""",
                (demand_slice.source_id, demand_slice.jurisdiction, demand_slice.kind.value),
            ).fetchall()
        return tuple(_decode(json.loads(row["payload"])) for row in rows)
