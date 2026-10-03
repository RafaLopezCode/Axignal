"""SQLite operations telemetry for AO-19."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_api_operations import (
    ApiOperationObservation,
    WebhookDisposition,
    WebhookEnvelope,
)


class ApiOperationsStoreConflict(ValueError):
    pass


class SqliteApiOperationsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS api_operation_observations (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id TEXT NOT NULL UNIQUE,
                    endpoint_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_api_operation_endpoint
                    ON api_operation_observations(endpoint_id, sequence);
                CREATE TABLE IF NOT EXISTS webhook_inbox (
                    integration_id TEXT NOT NULL,
                    provider_event_id TEXT NOT NULL,
                    payload_fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(integration_id, provider_event_id)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def append_observation(self, observation: ApiOperationObservation) -> bool:
        payload = json.dumps(
            {
                "observation_id": observation.observation_id,
                "endpoint_id": observation.endpoint_id,
                "occurred_at": observation.occurred_at.isoformat(),
                "latency_ms": observation.latency_ms,
                "status_code": observation.status_code,
                "error_category": observation.error_category,
                "quota_remaining": observation.quota_remaining,
                "rate_limited": observation.rate_limited,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM api_operation_observations WHERE observation_id = ?",
                (observation.observation_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise ApiOperationsStoreConflict("observation id reused with different content")
            connection.execute(
                "INSERT INTO api_operation_observations("
                "observation_id, endpoint_id, occurred_at, payload_json) VALUES (?, ?, ?, ?)",
                (
                    observation.observation_id,
                    observation.endpoint_id,
                    observation.occurred_at.isoformat(),
                    payload,
                ),
            )
        return True

    def observations(self) -> tuple[ApiOperationObservation, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM api_operation_observations ORDER BY sequence"
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            result.append(
                ApiOperationObservation(
                    observation_id=payload["observation_id"],
                    endpoint_id=payload["endpoint_id"],
                    occurred_at=datetime.fromisoformat(payload["occurred_at"]),
                    latency_ms=payload["latency_ms"],
                    status_code=payload["status_code"],
                    error_category=payload["error_category"],
                    quota_remaining=payload["quota_remaining"],
                    rate_limited=payload["rate_limited"],
                )
            )
        return tuple(result)

    @staticmethod
    def _webhook_payload(envelope: WebhookEnvelope) -> str:
        return json.dumps(
            {
                "inbox_id": envelope.inbox_id,
                "integration_id": envelope.integration_id,
                "provider_event_id": envelope.provider_event_id,
                "event_type": envelope.event_type,
                "received_at": envelope.received_at.isoformat(),
                "payload_fingerprint": envelope.payload_fingerprint,
                "payload_size": envelope.payload_size,
                "schema_version": envelope.schema_version,
                "disposition": envelope.disposition.value,
                "attempt_count": envelope.attempt_count,
                "max_attempts": envelope.max_attempts,
                "last_attempt_at": None
                if envelope.last_attempt_at is None
                else envelope.last_attempt_at.isoformat(),
                "next_retry_at": None
                if envelope.next_retry_at is None
                else envelope.next_retry_at.isoformat(),
                "failure_category": envelope.failure_category,
                "result_ref": envelope.result_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def put_webhook(self, envelope: WebhookEnvelope) -> bool:
        payload = self._webhook_payload(envelope)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_fingerprint, payload_json FROM webhook_inbox "
                "WHERE integration_id = ? AND provider_event_id = ?",
                (envelope.integration_id, envelope.provider_event_id),
            ).fetchone()
            if row is not None and str(row["payload_fingerprint"]) != envelope.payload_fingerprint:
                raise ApiOperationsStoreConflict("webhook identity reused with different payload")
            if row is not None and str(row["payload_json"]) == payload:
                return False
            connection.execute(
                "INSERT INTO webhook_inbox(integration_id, provider_event_id, payload_fingerprint, payload_json) "
                "VALUES (?, ?, ?, ?) ON CONFLICT(integration_id, provider_event_id) DO UPDATE SET "
                "payload_json=excluded.payload_json",
                (
                    envelope.integration_id,
                    envelope.provider_event_id,
                    envelope.payload_fingerprint,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _envelope(payload: dict[str, object]) -> WebhookEnvelope:
        return WebhookEnvelope(
            inbox_id=str(payload["inbox_id"]),
            integration_id=str(payload["integration_id"]),
            provider_event_id=str(payload["provider_event_id"]),
            event_type=str(payload["event_type"]),
            received_at=datetime.fromisoformat(str(payload["received_at"])),
            payload_fingerprint=str(payload["payload_fingerprint"]),
            payload_size=int(str(payload["payload_size"])),
            schema_version=str(payload["schema_version"]),
            disposition=WebhookDisposition(str(payload["disposition"])),
            attempt_count=int(str(payload["attempt_count"])),
            max_attempts=int(str(payload["max_attempts"])),
            last_attempt_at=(
                None
                if payload["last_attempt_at"] is None
                else datetime.fromisoformat(str(payload["last_attempt_at"]))
            ),
            next_retry_at=(
                None
                if payload["next_retry_at"] is None
                else datetime.fromisoformat(str(payload["next_retry_at"]))
            ),
            failure_category=(
                None if payload["failure_category"] is None else str(payload["failure_category"])
            ),
            result_ref=None if payload["result_ref"] is None else str(payload["result_ref"]),
        )

    def webhook(self, integration_id: str, provider_event_id: str) -> WebhookEnvelope | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM webhook_inbox WHERE integration_id = ? AND provider_event_id = ?",
                (integration_id, provider_event_id),
            ).fetchone()
        if row is None:
            return None
        return self._envelope(json.loads(str(row["payload_json"])))

    def webhooks(self) -> tuple[WebhookEnvelope, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM webhook_inbox ORDER BY integration_id, provider_event_id"
            ).fetchall()
        return tuple(self._envelope(json.loads(str(row["payload_json"]))) for row in rows)
