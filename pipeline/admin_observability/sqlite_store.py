"""SQLite persistence for append-only Admin observability and snapshots."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from application.admin_observability import AdminProjectionConflict
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminProjectionId,
    AdminProjectionSnapshot,
    AdminProjectionSnapshotId,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
    ProjectionDatum,
)


class SqliteAdminObservabilityStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_observability_records (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_observability_record_id
                ON admin_observability_records(record_id);

                CREATE TABLE IF NOT EXISTS admin_projection_snapshots (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id TEXT NOT NULL UNIQUE,
                    projection_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_projection_latest
                ON admin_projection_snapshots(projection_id, scope, sequence);
                """
            )

    @staticmethod
    def _record_payload(record: AdminEventEnvelope) -> dict[str, object]:
        return {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "record_class": record.record_class.value,
            "schema_version": record.schema_version,
            "producer": record.producer,
            "owning_domain": record.owning_domain,
            "recorded_at": record.recorded_at.isoformat(),
            "outcome_state": record.outcome_state,
            "completeness": record.completeness.value,
            "privacy_class": record.privacy_class.value,
            "occurred_at": None if record.occurred_at is None else record.occurred_at.isoformat(),
            "observed_at": None if record.observed_at is None else record.observed_at.isoformat(),
            "effective_at": None
            if record.effective_at is None
            else record.effective_at.isoformat(),
            "subject_refs": list(record.subject_refs),
            "correlation_refs": list(record.correlation_refs),
            "causation_ref": record.causation_ref,
            "policy_refs": list(record.policy_refs),
            "provenance_refs": list(record.provenance_refs),
            "unknown_reason": record.unknown_reason,
            "supersedes_record_id": record.supersedes_record_id,
        }

    @staticmethod
    def _record_from_payload(data: dict[str, Any]) -> AdminEventEnvelope:
        def _dt(name: str) -> datetime | None:
            value = data.get(name)
            return None if value is None else datetime.fromisoformat(str(value))

        return AdminEventEnvelope(
            record_id=AdminRecordId(str(data["record_id"])),
            record_type=str(data["record_type"]),
            record_class=AdminRecordClass(str(data["record_class"])),
            schema_version=int(data["schema_version"]),
            producer=str(data["producer"]),
            owning_domain=str(data["owning_domain"]),
            recorded_at=datetime.fromisoformat(str(data["recorded_at"])),
            outcome_state=str(data["outcome_state"]),
            completeness=DataCompleteness(str(data["completeness"])),
            privacy_class=AdminPrivacyClass(str(data["privacy_class"])),
            occurred_at=_dt("occurred_at"),
            observed_at=_dt("observed_at"),
            effective_at=_dt("effective_at"),
            subject_refs=tuple(str(x) for x in data.get("subject_refs", [])),
            correlation_refs=tuple(str(x) for x in data.get("correlation_refs", [])),
            causation_ref=None if data.get("causation_ref") is None else str(data["causation_ref"]),
            policy_refs=tuple(str(x) for x in data.get("policy_refs", [])),
            provenance_refs=tuple(str(x) for x in data.get("provenance_refs", [])),
            unknown_reason=None
            if data.get("unknown_reason") is None
            else str(data["unknown_reason"]),
            supersedes_record_id=(
                None
                if data.get("supersedes_record_id") is None
                else AdminRecordId(str(data["supersedes_record_id"]))
            ),
        )

    @staticmethod
    def _snapshot_payload(snapshot: AdminProjectionSnapshot) -> dict[str, object]:
        return {
            "snapshot_id": snapshot.snapshot_id,
            "projection_id": snapshot.projection_id,
            "schema_version": snapshot.schema_version,
            "scope": snapshot.scope,
            "as_of": snapshot.as_of.isoformat(),
            "generated_at": snapshot.generated_at.isoformat(),
            "completeness": snapshot.completeness.value,
            "source_record_ids": list(snapshot.source_record_ids),
            "data": [{"key": item.key, "value": item.value} for item in snapshot.data],
            "fingerprint": snapshot.fingerprint,
        }

    @staticmethod
    def _snapshot_from_payload(data: dict[str, Any]) -> AdminProjectionSnapshot:
        items = data.get("data", [])
        return AdminProjectionSnapshot(
            snapshot_id=AdminProjectionSnapshotId(str(data["snapshot_id"])),
            projection_id=AdminProjectionId(str(data["projection_id"])),
            schema_version=int(data["schema_version"]),
            scope=str(data["scope"]),
            as_of=datetime.fromisoformat(str(data["as_of"])),
            generated_at=datetime.fromisoformat(str(data["generated_at"])),
            completeness=DataCompleteness(str(data["completeness"])),
            source_record_ids=tuple(
                AdminRecordId(str(x)) for x in data.get("source_record_ids", [])
            ),
            data=tuple(
                ProjectionDatum(key=str(item["key"]), value=str(item["value"])) for item in items
            ),
            fingerprint=str(data["fingerprint"]),
        )

    def append_record(self, record: AdminEventEnvelope) -> bool:
        payload = json.dumps(self._record_payload(record), sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT fingerprint, payload_json FROM admin_observability_records WHERE record_id = ?",
                (record.record_id,),
            ).fetchone()
            if row is not None:
                if (
                    str(row["fingerprint"]) == record.fingerprint
                    and str(row["payload_json"]) == payload
                ):
                    return False
                raise AdminProjectionConflict("record id already exists with different content")
            connection.execute(
                "INSERT INTO admin_observability_records (record_id, fingerprint, payload_json) VALUES (?, ?, ?)",
                (record.record_id, record.fingerprint, payload),
            )
        return True

    def get_record(self, record_id: AdminRecordId) -> AdminEventEnvelope | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM admin_observability_records WHERE record_id = ?",
                (record_id,),
            ).fetchone()
        return (
            None if row is None else self._record_from_payload(json.loads(str(row["payload_json"])))
        )

    def records_through(self, as_of: datetime) -> tuple[AdminEventEnvelope, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_observability_records ORDER BY sequence"
            ).fetchall()
        records = tuple(
            self._record_from_payload(json.loads(str(row["payload_json"]))) for row in rows
        )
        return tuple(record for record in records if record.recorded_at <= as_of)

    def append_snapshot(self, snapshot: AdminProjectionSnapshot) -> bool:
        payload = json.dumps(
            self._snapshot_payload(snapshot), sort_keys=True, separators=(",", ":")
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT fingerprint FROM admin_projection_snapshots WHERE snapshot_id = ?",
                (snapshot.snapshot_id,),
            ).fetchone()
            if row is not None:
                if str(row["fingerprint"]) == snapshot.fingerprint:
                    return False
                raise AdminProjectionConflict("snapshot id already exists with different content")
            connection.execute(
                """
                INSERT INTO admin_projection_snapshots
                (snapshot_id, projection_id, scope, fingerprint, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.snapshot_id,
                    snapshot.projection_id,
                    snapshot.scope,
                    snapshot.fingerprint,
                    payload,
                ),
            )
        return True

    def latest_snapshot(
        self, projection_id: AdminProjectionId, scope: str
    ) -> AdminProjectionSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM admin_projection_snapshots
                WHERE projection_id = ? AND scope = ?
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (projection_id, scope),
            ).fetchone()
        return (
            None
            if row is None
            else self._snapshot_from_payload(json.loads(str(row["payload_json"])))
        )

    def recent_snapshots(
        self,
        projection_id: AdminProjectionId,
        scope: str,
        *,
        limit: int = 2,
        through: datetime | None = None,
    ) -> tuple[AdminProjectionSnapshot, ...]:
        """Return newest eligible snapshots first for governed temporal comparison."""
        if limit < 1:
            raise ValueError("limit must be >= 1")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM admin_projection_snapshots
                WHERE projection_id = ? AND scope = ?
                ORDER BY sequence DESC
                """,
                (projection_id, scope),
            ).fetchall()
        snapshots = (
            self._snapshot_from_payload(json.loads(str(row["payload_json"]))) for row in rows
        )
        eligible = tuple(
            snapshot for snapshot in snapshots if through is None or snapshot.as_of <= through
        )
        return eligible[:limit]
