"""SQLite append-only store for AO-07 privileged action audit."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
)


class AdminGovernanceAuditConflict(ValueError):
    """Raised when an audit id is reused with different immutable content."""


class SqliteAdminGovernanceAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_governance_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT NOT NULL UNIQUE,
                    occurred_at TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_governance_audit_time
                    ON admin_governance_audit(occurred_at, audit_id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(record: AdminGovernanceAuditRecord) -> str:
        return json.dumps(
            {
                "audit_id": record.audit_id,
                "command_id": record.command_id,
                "occurred_at": record.occurred_at.isoformat(),
                "actor_principal_id": record.actor_principal_id,
                "actor_session_id": record.actor_session_id,
                "target": record.target.value,
                "action": record.action,
                "reason": record.reason,
                "required_scope": record.required_scope,
                "outcome": record.outcome.value,
                "result_code": record.result_code,
                "before_ref": record.before_ref,
                "after_ref": record.after_ref,
                "approval_ref": record.approval_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _load(payload: str) -> AdminGovernanceAuditRecord:
        from datetime import datetime

        data = json.loads(payload)
        return AdminGovernanceAuditRecord(
            audit_id=str(data["audit_id"]),
            command_id=str(data["command_id"]),
            occurred_at=datetime.fromisoformat(str(data["occurred_at"])),
            actor_principal_id=str(data["actor_principal_id"]),
            actor_session_id=str(data["actor_session_id"]),
            target=AdminGovernanceCommandTarget(str(data["target"])),
            action=str(data["action"]),
            reason=str(data["reason"]),
            required_scope=str(data["required_scope"]),
            outcome=AdminGovernanceCommandOutcome(str(data["outcome"])),
            result_code=str(data["result_code"]),
            before_ref=None if data.get("before_ref") is None else str(data["before_ref"]),
            after_ref=None if data.get("after_ref") is None else str(data["after_ref"]),
            approval_ref=(None if data.get("approval_ref") is None else str(data["approval_ref"])),
        )

    def append(self, record: AdminGovernanceAuditRecord) -> bool:
        payload = self._payload(record)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT fingerprint, payload_json FROM admin_governance_audit WHERE audit_id = ?",
                (record.audit_id,),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["fingerprint"]) == record.fingerprint
                    and str(existing["payload_json"]) == payload
                ):
                    return False
                raise AdminGovernanceAuditConflict(
                    "governance audit id already exists with different content"
                )
            connection.execute(
                "INSERT INTO admin_governance_audit(audit_id, occurred_at, fingerprint, payload_json) "
                "VALUES (?, ?, ?, ?)",
                (record.audit_id, record.occurred_at.isoformat(), record.fingerprint, payload),
            )
        return True

    def all(self) -> tuple[AdminGovernanceAuditRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_governance_audit ORDER BY sequence"
            ).fetchall()
        return tuple(self._load(str(row["payload_json"])) for row in rows)
