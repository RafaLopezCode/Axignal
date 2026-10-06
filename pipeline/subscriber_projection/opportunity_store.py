"""Append-only SQLite persistence for authorized opportunity projections."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application.observation_intelligence.subscriber_projection import (
    SubscriberOpportunityProjection,
    SubscriberOpportunityProjectionError,
)


class SqliteSubscriberOpportunityProjectionStore:
    """Persist cognition opportunity snapshots under an exact Tenant/Focus pair."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriber_opportunity_projections (
                    tenant_id TEXT NOT NULL,
                    xeed_id TEXT NOT NULL,
                    organization_id TEXT NOT NULL,
                    projection_id TEXT NOT NULL,
                    as_of TEXT NOT NULL,
                    cognition_json TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, xeed_id, projection_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS subscriber_opportunity_projections_latest
                ON subscriber_opportunity_projections
                    (tenant_id, xeed_id, organization_id, as_of DESC, projection_id DESC)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _payload(value: dict[str, object]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def append(self, projection: SubscriberOpportunityProjection) -> bool:
        payload = self._payload(projection.cognition)
        as_of = projection.as_of.astimezone(UTC).isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT organization_id, as_of, cognition_json
                FROM subscriber_opportunity_projections
                WHERE tenant_id = ? AND xeed_id = ? AND projection_id = ?
                """,
                (projection.tenant_id, projection.xeed_id, projection.projection_id),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing[0]) != projection.organization_id
                    or str(existing[1]) != as_of
                    or str(existing[2]) != payload
                ):
                    raise SubscriberOpportunityProjectionError(
                        "projection identity was reused with different content"
                    )
                return False
            connection.execute(
                """
                INSERT INTO subscriber_opportunity_projections (
                    tenant_id, xeed_id, organization_id, projection_id, as_of, cognition_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    projection.tenant_id,
                    projection.xeed_id,
                    projection.organization_id,
                    projection.projection_id,
                    as_of,
                    payload,
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
    ) -> SubscriberOpportunityProjection | None:
        if as_of.tzinfo is None:
            raise ValueError("opportunity projection read time must be timezone-aware")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT tenant_id, xeed_id, organization_id, projection_id, as_of, cognition_json
                FROM subscriber_opportunity_projections
                WHERE tenant_id = ? AND xeed_id = ? AND organization_id = ? AND as_of <= ?
                ORDER BY as_of DESC, projection_id DESC
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
        cognition = json.loads(str(row[5]))
        if not isinstance(cognition, dict):
            raise SubscriberOpportunityProjectionError("persisted cognition must be an object")
        return SubscriberOpportunityProjection(
            tenant_id=str(row[0]),
            xeed_id=str(row[1]),
            organization_id=str(row[2]),
            projection_id=str(row[3]),
            as_of=datetime.fromisoformat(str(row[4])),
            cognition=cognition,
        )
