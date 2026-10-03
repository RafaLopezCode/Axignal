"""Replay-safe SQLite persistence for AO-20 financial records."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_financial_documents import (
    FinancialRecord,
    FinancialRecordKind,
    FinancialRecordState,
    FinancialSource,
    TaxBasisState,
)


class FinancialDocumentStoreConflict(ValueError):
    pass


class SqliteFinancialDocumentStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_financial_records (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    account_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    billing_event_id TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_financial_account
                    ON admin_financial_records(account_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_financial_billing_event
                    ON admin_financial_records(billing_event_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(record: FinancialRecord) -> str:
        return json.dumps(
            {
                "record_id": record.record_id,
                "account_id": record.account_id,
                "kind": record.kind.value,
                "state": record.state.value,
                "occurred_at": record.occurred_at.isoformat(),
                "recorded_at": record.recorded_at.isoformat(),
                "currency": record.currency,
                "gross_minor": record.gross_minor,
                "source": {
                    "system": record.source.system,
                    "object_ref": record.source.object_ref,
                    "event_ref": record.source.event_ref,
                    "adapter_ref": record.source.adapter_ref,
                },
                "billing_event_id": record.billing_event_id,
                "document_number": record.document_number,
                "period_start": None
                if record.period_start is None
                else record.period_start.isoformat(),
                "period_end": None if record.period_end is None else record.period_end.isoformat(),
                "tax_basis_state": record.tax_basis_state.value,
                "net_minor": record.net_minor,
                "tax_minor": record.tax_minor,
                "corrects_record_id": record.corrects_record_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _record(payload: dict[str, object]) -> FinancialRecord:
        source = payload["source"]
        if not isinstance(source, dict):
            raise FinancialDocumentStoreConflict("stored financial source is invalid")
        return FinancialRecord(
            record_id=str(payload["record_id"]),
            account_id=str(payload["account_id"]),
            kind=FinancialRecordKind(str(payload["kind"])),
            state=FinancialRecordState(str(payload["state"])),
            occurred_at=datetime.fromisoformat(str(payload["occurred_at"])),
            recorded_at=datetime.fromisoformat(str(payload["recorded_at"])),
            currency=str(payload["currency"]),
            gross_minor=int(str(payload["gross_minor"])),
            source=FinancialSource(
                system=str(source["system"]),
                object_ref=str(source["object_ref"]),
                event_ref=None if source["event_ref"] is None else str(source["event_ref"]),
                adapter_ref=None if source["adapter_ref"] is None else str(source["adapter_ref"]),
            ),
            billing_event_id=(
                None if payload["billing_event_id"] is None else str(payload["billing_event_id"])
            ),
            document_number=(
                None if payload["document_number"] is None else str(payload["document_number"])
            ),
            period_start=(
                None
                if payload["period_start"] is None
                else datetime.fromisoformat(str(payload["period_start"]))
            ),
            period_end=(
                None
                if payload["period_end"] is None
                else datetime.fromisoformat(str(payload["period_end"]))
            ),
            tax_basis_state=TaxBasisState(str(payload["tax_basis_state"])),
            net_minor=None if payload["net_minor"] is None else int(str(payload["net_minor"])),
            tax_minor=None if payload["tax_minor"] is None else int(str(payload["tax_minor"])),
            corrects_record_id=(
                None
                if payload["corrects_record_id"] is None
                else str(payload["corrects_record_id"])
            ),
        )

    def append(self, record: FinancialRecord) -> bool:
        payload = self._payload(record)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM admin_financial_records WHERE record_id = ?",
                (record.record_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise FinancialDocumentStoreConflict(
                    "financial record id reused with different content"
                )
            connection.execute(
                "INSERT INTO admin_financial_records("
                "record_id, account_id, kind, occurred_at, billing_event_id, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.record_id,
                    record.account_id,
                    record.kind.value,
                    record.occurred_at.isoformat(),
                    record.billing_event_id,
                    payload,
                ),
            )
        return True

    def get(self, record_id: str) -> FinancialRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM admin_financial_records WHERE record_id = ?",
                (record_id,),
            ).fetchone()
        return None if row is None else self._record(json.loads(str(row["payload_json"])))

    def all(self) -> tuple[FinancialRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_financial_records ORDER BY sequence"
            ).fetchall()
        return tuple(self._record(json.loads(str(row["payload_json"]))) for row in rows)

    def for_account(self, account_id: str) -> tuple[FinancialRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_financial_records "
                "WHERE account_id = ? ORDER BY sequence",
                (account_id,),
            ).fetchall()
        return tuple(self._record(json.loads(str(row["payload_json"]))) for row in rows)

    def for_billing_event(self, billing_event_id: str) -> tuple[FinancialRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_financial_records "
                "WHERE billing_event_id = ? ORDER BY sequence",
                (billing_event_id,),
            ).fetchall()
        return tuple(self._record(json.loads(str(row["payload_json"]))) for row in rows)
