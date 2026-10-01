"""SQLite authority store for AO-08 AXIGNAL first-party commercial operations."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from domain.admin_commercial import (
    CommercialAuditId,
    CommercialAuditRecord,
    CommercialCompany,
    CommercialCompanyId,
    CommercialContact,
    CommercialContactId,
    CommercialDeal,
    CommercialDealId,
    CommercialNote,
    CommercialNoteId,
    CommercialOpportunity,
    CommercialOpportunityId,
    CommercialOrigin,
    CommercialProspect,
    CommercialProspectId,
    CommercialTask,
    CommercialTaskId,
    ConsentBasis,
    DealStage,
    OpportunityStage,
    ProspectStage,
    TaskState,
)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


class SqliteAdminCommercialStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_commercial_records (
                    record_type TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(record_type, record_id)
                );
                CREATE TABLE IF NOT EXISTS admin_commercial_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT NOT NULL UNIQUE,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(record: Any) -> str:
        return json.dumps(
            asdict(record), default=_json_default, sort_keys=True, separators=(",", ":")
        )

    def _put(self, record_type: str, record_id: str, record: object, updated_at: datetime) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO admin_commercial_records(record_type, record_id, payload_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(record_type, record_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (record_type, record_id, self._payload(record), updated_at.isoformat()),
            )

    def put_prospect(self, record: CommercialProspect) -> None:
        self._put("prospect", str(record.prospect_id), record, record.updated_at)

    def put_company(self, record: CommercialCompany) -> None:
        self._put("company", str(record.company_id), record, record.created_at)

    def put_contact(self, record: CommercialContact) -> None:
        self._put("contact", str(record.contact_id), record, record.created_at)

    def put_opportunity(self, record: CommercialOpportunity) -> None:
        self._put("opportunity", str(record.opportunity_id), record, record.updated_at)

    def put_deal(self, record: CommercialDeal) -> None:
        self._put("deal", str(record.deal_id), record, record.updated_at)

    def put_note(self, record: CommercialNote) -> None:
        self._put("note", str(record.note_id), record, record.created_at)

    def put_task(self, record: CommercialTask) -> None:
        self._put("task", str(record.task_id), record, record.created_at)

    def append_audit(self, record: CommercialAuditRecord) -> bool:
        payload = self._payload(record)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT payload_json FROM admin_commercial_audit WHERE audit_id = ?",
                (str(record.audit_id),),
            ).fetchone()
            if existing is not None:
                if str(existing["payload_json"]) == payload:
                    return False
                raise ValueError("commercial audit id reused with different immutable content")
            connection.execute(
                "INSERT INTO admin_commercial_audit(audit_id, occurred_at, payload_json) VALUES (?, ?, ?)",
                (str(record.audit_id), record.occurred_at.isoformat(), payload),
            )
        return True

    def _rows(self, record_type: str) -> tuple[dict[str, Any], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_commercial_records WHERE record_type = ? ORDER BY updated_at, record_id",
                (record_type,),
            ).fetchall()
        return tuple(json.loads(str(row["payload_json"])) for row in rows)

    def prospects(self) -> tuple[CommercialProspect, ...]:
        return tuple(
            CommercialProspect(
                prospect_id=CommercialProspectId(row["prospect_id"]),
                display_name=row["display_name"],
                acquisition_source=row["acquisition_source"],
                consent_basis=ConsentBasis(row["consent_basis"]),
                origin=CommercialOrigin(row["origin"]),
                stage=ProspectStage(row["stage"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
                updated_at=datetime.fromisoformat(row["updated_at"]),
                company_id=(
                    None if row["company_id"] is None else CommercialCompanyId(row["company_id"])
                ),
                disposition_reason=row["disposition_reason"],
            )
            for row in self._rows("prospect")
        )

    def companies(self) -> tuple[CommercialCompany, ...]:
        return tuple(
            CommercialCompany(
                company_id=CommercialCompanyId(row["company_id"]),
                display_name=row["display_name"],
                acquisition_source=row["acquisition_source"],
                consent_basis=ConsentBasis(row["consent_basis"]),
                origin=CommercialOrigin(row["origin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
                observed_organization_id=row["observed_organization_id"],
                observed_mapping_reason=row["observed_mapping_reason"],
                account_id=row["account_id"],
            )
            for row in self._rows("company")
        )

    def contacts(self) -> tuple[CommercialContact, ...]:
        return tuple(
            CommercialContact(
                contact_id=CommercialContactId(row["contact_id"]),
                company_id=None
                if row["company_id"] is None
                else CommercialCompanyId(row["company_id"]),
                display_name=row["display_name"],
                email=row["email"],
                phone=row["phone"],
                acquisition_source=row["acquisition_source"],
                consent_basis=ConsentBasis(row["consent_basis"]),
                origin=CommercialOrigin(row["origin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
            )
            for row in self._rows("contact")
        )

    def opportunities(self) -> tuple[CommercialOpportunity, ...]:
        return tuple(
            CommercialOpportunity(
                opportunity_id=CommercialOpportunityId(row["opportunity_id"]),
                company_id=CommercialCompanyId(row["company_id"]),
                title=row["title"],
                stage=OpportunityStage(row["stage"]),
                origin=CommercialOrigin(row["origin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
                updated_at=datetime.fromisoformat(row["updated_at"]),
                loss_reason=row["loss_reason"],
            )
            for row in self._rows("opportunity")
        )

    def deals(self) -> tuple[CommercialDeal, ...]:
        return tuple(
            CommercialDeal(
                deal_id=CommercialDealId(row["deal_id"]),
                opportunity_id=CommercialOpportunityId(row["opportunity_id"]),
                stage=DealStage(row["stage"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
                updated_at=datetime.fromisoformat(row["updated_at"]),
                account_id=row["account_id"],
                close_reason=row["close_reason"],
            )
            for row in self._rows("deal")
        )

    def notes(self) -> tuple[CommercialNote, ...]:
        return tuple(
            CommercialNote(
                note_id=CommercialNoteId(row["note_id"]),
                company_id=CommercialCompanyId(row["company_id"]),
                body=row["body"],
                origin=CommercialOrigin(row["origin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
            )
            for row in self._rows("note")
        )

    def tasks(self) -> tuple[CommercialTask, ...]:
        return tuple(
            CommercialTask(
                task_id=CommercialTaskId(row["task_id"]),
                company_id=CommercialCompanyId(row["company_id"]),
                title=row["title"],
                due_at=None if row["due_at"] is None else datetime.fromisoformat(row["due_at"]),
                state=TaskState(row["state"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                created_by=row["created_by"],
            )
            for row in self._rows("task")
        )

    def audits(self) -> tuple[CommercialAuditRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_commercial_audit ORDER BY sequence"
            ).fetchall()
        result = []
        for raw in rows:
            row = json.loads(str(raw["payload_json"]))
            result.append(
                CommercialAuditRecord(
                    audit_id=CommercialAuditId(row["audit_id"]),
                    occurred_at=datetime.fromisoformat(row["occurred_at"]),
                    actor=row["actor"],
                    action=row["action"],
                    record_type=row["record_type"],
                    record_id=row["record_id"],
                    origin=CommercialOrigin(row["origin"]),
                    reason=row["reason"],
                    before_ref=row["before_ref"],
                    after_ref=row["after_ref"],
                )
            )
        return tuple(result)
