"""SQLite persistence for AO-21 provider-neutral accounting reconciliation."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_accounting import (
    AccountingCategory,
    AccountingEntry,
    AccountMapping,
    PeriodClose,
    PeriodCloseState,
    ProcessorSettlement,
    ReconciliationIssue,
    ReconciliationIssueKind,
    ReconciliationIssueState,
)


class AccountingStoreConflict(ValueError):
    pass


class SqliteAccountingReconciliationStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounting_mappings (
                    mapping_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(mapping_id, version)
                );
                CREATE TABLE IF NOT EXISTS accounting_entries (
                    entry_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS processor_settlements (
                    settlement_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reconciliation_issues (
                    issue_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS accounting_periods (
                    period_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _put_immutable(
        connection: sqlite3.Connection,
        *,
        table: str,
        key_column: str,
        key_value: str,
        payload: str,
    ) -> bool:
        row = connection.execute(
            f"SELECT payload_json FROM {table} WHERE {key_column} = ?",
            (key_value,),
        ).fetchone()
        if row is not None:
            if str(row["payload_json"]) == payload:
                return False
            raise AccountingStoreConflict(f"{table} identity reused with different content")
        connection.execute(
            f"INSERT INTO {table}({key_column}, payload_json) VALUES (?, ?)",
            (key_value, payload),
        )
        return True

    def append_mapping(self, mapping: AccountMapping) -> bool:
        payload = json.dumps(
            {
                "mapping_id": mapping.mapping_id,
                "integration_id": mapping.integration_id,
                "category": mapping.category.value,
                "account_code": mapping.account_code,
                "effective_at": mapping.effective_at.isoformat(),
                "version": mapping.version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM accounting_mappings WHERE mapping_id = ? AND version = ?",
                (mapping.mapping_id, mapping.version),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise AccountingStoreConflict("mapping version reused with different content")
            previous = connection.execute(
                "SELECT MAX(version) AS max_version FROM accounting_mappings WHERE mapping_id = ?",
                (mapping.mapping_id,),
            ).fetchone()
            max_version = None if previous is None else previous["max_version"]
            if max_version is None and mapping.version != 1:
                raise AccountingStoreConflict("first mapping version must be 1")
            if max_version is not None and mapping.version != int(max_version) + 1:
                raise AccountingStoreConflict("mapping version is out of sequence")
            connection.execute(
                "INSERT INTO accounting_mappings(mapping_id, version, payload_json) VALUES (?, ?, ?)",
                (mapping.mapping_id, mapping.version, payload),
            )
        return True

    def mappings(self) -> tuple[AccountMapping, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM accounting_mappings "
                "WHERE (mapping_id, version) IN ("
                "SELECT mapping_id, MAX(version) FROM accounting_mappings GROUP BY mapping_id"
                ") ORDER BY mapping_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                AccountMapping(
                    mapping_id=p["mapping_id"],
                    integration_id=p["integration_id"],
                    category=AccountingCategory(p["category"]),
                    account_code=p["account_code"],
                    effective_at=datetime.fromisoformat(p["effective_at"]),
                    version=int(p["version"]),
                )
            )
        return tuple(result)

    def append_entry(self, entry: AccountingEntry) -> bool:
        payload = json.dumps(
            {
                "entry_id": entry.entry_id,
                "integration_id": entry.integration_id,
                "account_code": entry.account_code,
                "category": entry.category.value,
                "occurred_at": entry.occurred_at.isoformat(),
                "recorded_at": entry.recorded_at.isoformat(),
                "currency": entry.currency,
                "signed_amount_minor": entry.signed_amount_minor,
                "source_ref": entry.source_ref,
                "financial_record_id": entry.financial_record_id,
                "settlement_id": entry.settlement_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            return self._put_immutable(
                connection,
                table="accounting_entries",
                key_column="entry_id",
                key_value=entry.entry_id,
                payload=payload,
            )

    def entries(self) -> tuple[AccountingEntry, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM accounting_entries ORDER BY entry_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                AccountingEntry(
                    entry_id=p["entry_id"],
                    integration_id=p["integration_id"],
                    account_code=p["account_code"],
                    category=AccountingCategory(p["category"]),
                    occurred_at=datetime.fromisoformat(p["occurred_at"]),
                    recorded_at=datetime.fromisoformat(p["recorded_at"]),
                    currency=p["currency"],
                    signed_amount_minor=int(p["signed_amount_minor"]),
                    source_ref=p["source_ref"],
                    financial_record_id=p["financial_record_id"],
                    settlement_id=p["settlement_id"],
                )
            )
        return tuple(result)

    def append_settlement(self, settlement: ProcessorSettlement) -> bool:
        payload = json.dumps(
            {
                "settlement_id": settlement.settlement_id,
                "integration_id": settlement.integration_id,
                "processor": settlement.processor,
                "occurred_at": settlement.occurred_at.isoformat(),
                "recorded_at": settlement.recorded_at.isoformat(),
                "currency": settlement.currency,
                "gross_minor": settlement.gross_minor,
                "fee_minor": settlement.fee_minor,
                "net_minor": settlement.net_minor,
                "source_ref": settlement.source_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            return self._put_immutable(
                connection,
                table="processor_settlements",
                key_column="settlement_id",
                key_value=settlement.settlement_id,
                payload=payload,
            )

    def settlements(self) -> tuple[ProcessorSettlement, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM processor_settlements ORDER BY settlement_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                ProcessorSettlement(
                    settlement_id=p["settlement_id"],
                    integration_id=p["integration_id"],
                    processor=p["processor"],
                    occurred_at=datetime.fromisoformat(p["occurred_at"]),
                    recorded_at=datetime.fromisoformat(p["recorded_at"]),
                    currency=p["currency"],
                    gross_minor=int(p["gross_minor"]),
                    fee_minor=int(p["fee_minor"]),
                    net_minor=int(p["net_minor"]),
                    source_ref=p["source_ref"],
                )
            )
        return tuple(result)

    @staticmethod
    def _issue_payload(issue: ReconciliationIssue) -> str:
        return json.dumps(
            {
                "issue_id": issue.issue_id,
                "kind": issue.kind.value,
                "state": issue.state.value,
                "opened_at": issue.opened_at.isoformat(),
                "currency": issue.currency,
                "expected_minor": issue.expected_minor,
                "observed_minor": issue.observed_minor,
                "financial_record_id": issue.financial_record_id,
                "accounting_entry_id": issue.accounting_entry_id,
                "settlement_id": issue.settlement_id,
                "resolved_at": None if issue.resolved_at is None else issue.resolved_at.isoformat(),
                "resolution_ref": issue.resolution_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def put_issue(self, issue: ReconciliationIssue) -> bool:
        payload = self._issue_payload(issue)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM reconciliation_issues WHERE issue_id = ?",
                (issue.issue_id,),
            ).fetchone()
            if row is not None and str(row["payload_json"]) == payload:
                return False
            connection.execute(
                "INSERT INTO reconciliation_issues(issue_id, payload_json) VALUES (?, ?) "
                "ON CONFLICT(issue_id) DO UPDATE SET payload_json=excluded.payload_json",
                (issue.issue_id, payload),
            )
        return True

    def issues(self) -> tuple[ReconciliationIssue, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM reconciliation_issues ORDER BY issue_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                ReconciliationIssue(
                    issue_id=p["issue_id"],
                    kind=ReconciliationIssueKind(p["kind"]),
                    state=ReconciliationIssueState(p["state"]),
                    opened_at=datetime.fromisoformat(p["opened_at"]),
                    currency=p["currency"],
                    expected_minor=p["expected_minor"],
                    observed_minor=p["observed_minor"],
                    financial_record_id=p["financial_record_id"],
                    accounting_entry_id=p["accounting_entry_id"],
                    settlement_id=p["settlement_id"],
                    resolved_at=(
                        None
                        if p["resolved_at"] is None
                        else datetime.fromisoformat(p["resolved_at"])
                    ),
                    resolution_ref=p["resolution_ref"],
                )
            )
        return tuple(result)

    def put_period(self, period: PeriodClose) -> bool:
        payload = json.dumps(
            {
                "period_id": period.period_id,
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
                "state": period.state.value,
                "evaluated_at": period.evaluated_at.isoformat(),
                "closed_at": None if period.closed_at is None else period.closed_at.isoformat(),
                "source_ref": period.source_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM accounting_periods WHERE period_id = ?",
                (period.period_id,),
            ).fetchone()
            if row is not None and str(row["payload_json"]) == payload:
                return False
            connection.execute(
                "INSERT INTO accounting_periods(period_id, payload_json) VALUES (?, ?) "
                "ON CONFLICT(period_id) DO UPDATE SET payload_json=excluded.payload_json",
                (period.period_id, payload),
            )
        return True

    def periods(self) -> tuple[PeriodClose, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM accounting_periods ORDER BY period_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                PeriodClose(
                    period_id=p["period_id"],
                    period_start=datetime.fromisoformat(p["period_start"]),
                    period_end=datetime.fromisoformat(p["period_end"]),
                    state=PeriodCloseState(p["state"]),
                    evaluated_at=datetime.fromisoformat(p["evaluated_at"]),
                    closed_at=(
                        None if p["closed_at"] is None else datetime.fromisoformat(p["closed_at"])
                    ),
                    source_ref=p["source_ref"],
                )
            )
        return tuple(result)
