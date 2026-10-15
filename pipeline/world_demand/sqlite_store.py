"""World demand index storage: public procurement records and slice states.

Records are public source observations with their original URL and publication time;
nothing tenant-specific is stored here (which Focus asked is never recorded).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode
from application.observation_intelligence.findings import ProcurementRecord
from application.world_demand.awards import AwardRecord, normalized_name
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
            "main_codes": [[c.scheme, c.code] for c in record.main_codes],
            "contract_nature": record.contract_nature,
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
        # Records stored before main codes were read carry none: unknown, not additional.
        main_codes=tuple(TaxonomyCode(str(s), str(c)) for s, c in raw.get("main_codes") or ()),
        contract_nature=None if raw.get("contract_nature") is None else str(raw["contract_nature"]),
    )


def _time(value: object) -> datetime | None:
    return None if value is None else datetime.fromisoformat(str(value))


def _encode_award(award: AwardRecord) -> str:
    return json.dumps(
        {
            "source_id": award.source_id, "record_id": award.record_id, "lot": award.lot,
            "title": award.title, "buyer_name": award.buyer_name,
            "winner_name": award.winner_name, "winner_id": award.winner_id,
            "amount": award.amount, "currency": award.currency,
            "awarded_on": None if award.awarded_on is None else award.awarded_on.isoformat(),
            "offers_received": award.offers_received,
            "demand_codes": [[c.scheme, c.code] for c in award.demand_codes],
            "places": [[p.scheme, p.code] for p in award.places],
            "source_url": award.source_url,
        },
        ensure_ascii=False,
        sort_keys=True,
    )  # fmt: skip


def _decode_award(raw: dict[str, Any]) -> AwardRecord:
    return AwardRecord(
        source_id=str(raw["source_id"]), record_id=str(raw["record_id"]), lot=str(raw["lot"]),
        title=str(raw["title"]), buyer_name=raw["buyer_name"], winner_name=str(raw["winner_name"]),
        winner_id=raw["winner_id"], amount=raw["amount"], currency=raw["currency"],
        awarded_on=None if raw["awarded_on"] is None else date.fromisoformat(raw["awarded_on"]),
        offers_received=raw["offers_received"],
        demand_codes=tuple(TaxonomyCode(str(s), str(c)) for s, c in raw["demand_codes"]),
        places=tuple(TaxonomyCode(str(s), str(c)) for s, c in raw["places"]),
        source_url=str(raw["source_url"]),
    )  # fmt: skip


class SqliteWorldDemandIndex:
    def upsert_awards(self, awards: Sequence[AwardRecord]) -> int:
        """Published award results; idempotent (one row per folder, lot and winner)."""
        rows = [
            (
                award.key,
                award.source_id,
                award.winner_id,
                normalized_name(award.winner_name),
                next((c for p in award.places if (c := country_of(p))), None),
                None if award.awarded_on is None else award.awarded_on.isoformat(),
                _encode_award(award),
            )
            for award in awards
        ]
        if not rows:
            return 0
        with self._connect() as db:
            db.executemany(
                """INSERT INTO wd_awards
                (award_key, source_id, winner_id, winner_name_norm, country, awarded_on, payload)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(award_key) DO UPDATE SET
                payload=excluded.payload, awarded_on=excluded.awarded_on""",
                rows,
            )
        return len(rows)

    def awards_won_by(
        self, *, tax_ids: Sequence[str] = (), names: Sequence[str] = (), limit: int = 500
    ) -> tuple[AwardRecord, ...]:
        """Awards whose winner has one of these tax ids, or exactly one of these names."""
        ids = [t for t in tax_ids if t]
        norms = [n for n in (normalized_name(x) for x in names) if len(n) >= 4]
        if not ids and not norms:
            return ()
        clauses, params = [], []
        if ids:
            clauses.append(f"winner_id IN ({','.join('?' * len(ids))})")
            params += ids
        if norms:
            clauses.append(f"winner_name_norm IN ({','.join('?' * len(norms))})")
            params += norms
        with self._connect() as db:
            rows = db.execute(
                f"SELECT payload FROM wd_awards WHERE {' OR '.join(clauses)} "
                "ORDER BY awarded_on DESC LIMIT ?",
                (*params, limit),
            ).fetchall()
        return tuple(_decode_award(json.loads(row["payload"])) for row in rows)

    def awards_in(
        self, country: str, *, since: date, limit: int = 20000
    ) -> tuple[AwardRecord, ...]:
        """Awards in a country since a date, for comparing who wins what (POTENTIAL reading)."""
        with self._connect() as db:
            rows = db.execute(
                "SELECT payload FROM wd_awards WHERE country=? AND awarded_on>=? "
                "ORDER BY awarded_on DESC LIMIT ?",
                (country, since.isoformat(), limit),
            ).fetchall()
        return tuple(_decode_award(json.loads(row["payload"])) for row in rows)

    def awards_coverage(self, country: str) -> tuple[date | None, int]:
        """Since when awards are held for a country, and how many.

        After an archive backfill, coverage starts with the first month read in full (older
        award dates in it are updates of old tenders, not a complete history).
        """
        with self._connect() as db:
            row = db.execute(
                "SELECT MIN(awarded_on) AS since, COUNT(*) AS held FROM wd_awards WHERE country=?",
                (country,),
            ).fetchone()
            backfilled = None
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='wd_awards_backfill'"
            ).fetchone():
                backfilled = db.execute(
                    "SELECT MIN(month) FROM wd_awards_backfill WHERE state='DONE'"
                ).fetchone()[0]
        since = None if row is None or row["since"] is None else date.fromisoformat(row["since"])
        if backfilled:
            since = date(int(backfilled[:4]), int(backfilled[4:6]), 1)
        return since, 0 if row is None else int(row["held"])

    def awards_of_lots(
        self, lots: Sequence[tuple[str, str, str]], *, limit: int = 2000
    ) -> tuple[AwardRecord, ...]:
        """Every award of these contract lots (all their winners)."""
        if not lots:
            return ()
        out: list[AwardRecord] = []
        with self._connect() as db:
            for source, record, lot in list(dict.fromkeys(lots))[:400]:
                prefix = f"{source}|{record}|{lot}|"
                rows = db.execute(
                    "SELECT payload FROM wd_awards WHERE award_key >= ? AND award_key < ?",
                    (prefix, prefix + "\uffff"),
                ).fetchall()
                out += [_decode_award(json.loads(r["payload"])) for r in rows]
                if len(out) >= limit:
                    break
        return tuple(out)

    def joint_venture_awards(
        self, names: Sequence[str], *, limit: int = 300
    ) -> tuple[AwardRecord, ...]:
        """Awards to joint ventures (UTE) whose name contains one of these names."""
        norms = [n for n in (normalized_name(x) for x in names) if len(n) >= 4]
        if not norms:
            return ()
        clause = " OR ".join("winner_name_norm LIKE ?" for _ in norms)
        with self._connect() as db:
            rows = db.execute(
                f"SELECT payload FROM wd_awards WHERE (winner_name_norm LIKE 'ute %' "
                f"OR winner_name_norm LIKE '% ute %' OR winner_name_norm LIKE 'union temporal%') "
                f"AND ({clause}) ORDER BY awarded_on DESC LIMIT ?",
                (*[f"%{n}%" for n in norms], limit),
            ).fetchall()
        return tuple(_decode_award(json.loads(r["payload"])) for r in rows)

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
                    records INTEGER NOT NULL DEFAULT 0,
                    cursor_page INTEGER NOT NULL DEFAULT 1,
                    traversal_since TEXT
                );
                CREATE TABLE IF NOT EXISTS wd_awards (
                    award_key TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    winner_id TEXT,
                    winner_name_norm TEXT NOT NULL,
                    country TEXT,
                    awarded_on TEXT,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_wd_awards_winner ON wd_awards(winner_id);
                CREATE INDEX IF NOT EXISTS idx_wd_awards_name ON wd_awards(winner_name_norm);
                CREATE INDEX IF NOT EXISTS idx_wd_awards_country ON wd_awards(country, awarded_on);
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
            cursor_page=int(row["cursor_page"]),
            traversal_since=_time(row["traversal_since"]),
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
                    ON CONFLICT(source_id, record_id) DO UPDATE SET payload=excluded.payload,
                    kind=excluded.kind, published_at=excluded.published_at""",
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
        cursor_page: int = 1,
        traversal_since: datetime | None = None,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO wd_slices (slice_key, source_id, jurisdiction, kind, ingested_at,
                window_start, complete, requests, records, cursor_page, traversal_since)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(slice_key) DO UPDATE SET ingested_at=excluded.ingested_at,
                window_start=excluded.window_start, complete=excluded.complete,
                requests=excluded.requests, records=excluded.records,
                cursor_page=excluded.cursor_page, traversal_since=excluded.traversal_since""",
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
                    cursor_page,
                    None if traversal_since is None else traversal_since.isoformat(),
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
