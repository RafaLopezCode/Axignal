"""Append-only SQLite store for subscriber-scoped economic output snapshots."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application.subscriber_projection.subscriber_runtime import (
    StoredEconomicOutput,
    SubscriberEconomicStoreError,
)


class SqliteSubscriberEconomicOutputStore:
    """Persist real Human Output snapshots under one authorized Tenant/Focus."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriber_economic_outputs (
                    tenant_id TEXT NOT NULL,
                    xeed_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    output_id TEXT NOT NULL,
                    as_of TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    runtime_signal_json TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, xeed_id, output_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS subscriber_economic_outputs_latest
                ON subscriber_economic_outputs
                    (tenant_id, xeed_id, organization_id, as_of DESC, output_id DESC)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _payload(value: dict[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def append(self, output: StoredEconomicOutput) -> bool:
        """Store once, rejecting identity reuse with different output content."""

        output_json = self._payload(output.output_wire)
        signal_json = self._payload(output.runtime_signal)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT organization_id, as_of, output_json, runtime_signal_json
                FROM subscriber_economic_outputs
                WHERE tenant_id = ? AND xeed_id = ? AND output_id = ?
                """,
                (output.tenant_id, output.xeed_id, output.output_id),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing[0]) != output.organization_id
                    or str(existing[1]) != output.as_of.astimezone(UTC).isoformat()
                    or str(existing[2]) != output_json
                    or str(existing[3]) != signal_json
                ):
                    raise SubscriberEconomicStoreError(
                        "stored economic output id was reused with different content"
                    )
                return False

            connection.execute(
                """
                INSERT INTO subscriber_economic_outputs (
                    tenant_id, xeed_id, organization_id, output_id, as_of,
                    output_json, runtime_signal_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    output.tenant_id,
                    output.xeed_id,
                    output.organization_id,
                    output.output_id,
                    output.as_of.astimezone(UTC).isoformat(),
                    output_json,
                    signal_json,
                ),
            )
            return True

    def latest(
        self,
        *,
        tenant_id: str,
        xeed_id: str,
        organization_id: str,
        as_of: datetime,
    ) -> StoredEconomicOutput | None:
        if not as_of.tzinfo:
            raise ValueError("subscriber output read as_of must be timezone-aware")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, xeed_id, organization_id, output_id, as_of,
                       output_json, runtime_signal_json
                FROM subscriber_economic_outputs
                WHERE tenant_id = ? AND xeed_id = ? AND organization_id = ? AND as_of <= ?
                ORDER BY as_of DESC, output_id DESC
                LIMIT 1
                """,
                (
                    tenant_id,
                    xeed_id,
                    organization_id,
                    as_of.astimezone(UTC).isoformat(),
                ),
            ).fetchone()
        if row is None:
            return None
        output_wire = json.loads(str(row[5]))
        runtime_signal = json.loads(str(row[6]))
        if not isinstance(output_wire, dict) or not isinstance(runtime_signal, dict):
            raise SubscriberEconomicStoreError("stored output JSON must be an object")
        return StoredEconomicOutput(
            tenant_id=str(row[0]),
            xeed_id=str(row[1]),
            organization_id=str(row[2]),
            output_id=str(row[3]),
            as_of=datetime.fromisoformat(str(row[4])),
            output_wire=output_wire,
            runtime_signal=runtime_signal,
        )
