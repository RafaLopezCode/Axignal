"""SQLite append-only persistence for secret-free AO-18 registry metadata."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
    IntegrationHealth,
    IntegrationHealthState,
    definition_fingerprint,
)


class IntegrationRegistryConflict(ValueError):
    """An immutable integration event or version conflicts with prior state."""


class SqliteAdminIntegrationStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_integration_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL UNIQUE,
                    integration_id TEXT NOT NULL,
                    event_kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_integration_events_id
                    ON admin_integration_events(integration_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _definition_payload(definition: IntegrationDefinition) -> str:
        credential = definition.credential
        return json.dumps(
            {
                "integration_id": definition.integration_id,
                "provider": definition.provider,
                "purpose": definition.purpose,
                "owner": definition.owner,
                "environment": definition.environment.value,
                "enabled": definition.enabled,
                "credential": {
                    "reference": credential.reference,
                    "state": credential.state.value,
                    "last_rotated_at": (
                        None
                        if credential.last_rotated_at is None
                        else credential.last_rotated_at.isoformat()
                    ),
                    "expires_at": None
                    if credential.expires_at is None
                    else credential.expires_at.isoformat(),
                    "revoked_at": None
                    if credential.revoked_at is None
                    else credential.revoked_at.isoformat(),
                },
                "scopes": list(definition.scopes),
                "direction": definition.direction.value,
                "authority_boundary": definition.authority_boundary,
                "webhook_capable": definition.webhook_capable,
                "webhook_endpoint": definition.webhook_endpoint,
                "rate_limit_posture": definition.rate_limit_posture,
                "health_freshness_seconds": definition.health_freshness_seconds,
                "version": definition.version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _load_definition(payload: str) -> IntegrationDefinition:
        data = json.loads(payload)
        credential = data["credential"]
        return IntegrationDefinition(
            integration_id=str(data["integration_id"]),
            provider=str(data["provider"]),
            purpose=str(data["purpose"]),
            owner=str(data["owner"]),
            environment=IntegrationEnvironment(str(data["environment"])),
            enabled=bool(data["enabled"]),
            credential=CredentialLifecycle(
                reference=None if credential["reference"] is None else str(credential["reference"]),
                state=CredentialState(str(credential["state"])),
                last_rotated_at=(
                    None
                    if credential["last_rotated_at"] is None
                    else datetime.fromisoformat(str(credential["last_rotated_at"]))
                ),
                expires_at=(
                    None
                    if credential["expires_at"] is None
                    else datetime.fromisoformat(str(credential["expires_at"]))
                ),
                revoked_at=(
                    None
                    if credential["revoked_at"] is None
                    else datetime.fromisoformat(str(credential["revoked_at"]))
                ),
            ),
            scopes=tuple(str(value) for value in data["scopes"]),
            direction=IntegrationDirection(str(data["direction"])),
            authority_boundary=str(data["authority_boundary"]),
            webhook_capable=bool(data["webhook_capable"]),
            webhook_endpoint=(
                None if data["webhook_endpoint"] is None else str(data["webhook_endpoint"])
            ),
            rate_limit_posture=(
                None if data["rate_limit_posture"] is None else str(data["rate_limit_posture"])
            ),
            health_freshness_seconds=int(data["health_freshness_seconds"]),
            version=int(data["version"]),
        )

    @staticmethod
    def _health_payload(observation: IntegrationHealth) -> str:
        return json.dumps(
            {
                "integration_id": observation.integration_id,
                "state": observation.state.value,
                "observed_at": observation.observed_at.isoformat(),
                "last_success_at": (
                    None
                    if observation.last_success_at is None
                    else observation.last_success_at.isoformat()
                ),
                "last_failure_at": (
                    None
                    if observation.last_failure_at is None
                    else observation.last_failure_at.isoformat()
                ),
                "failure_category": observation.failure_category,
                "source_ref": observation.source_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _load_health(payload: str) -> IntegrationHealth:
        data = json.loads(payload)
        return IntegrationHealth(
            integration_id=str(data["integration_id"]),
            state=IntegrationHealthState(str(data["state"])),
            observed_at=datetime.fromisoformat(str(data["observed_at"])),
            last_success_at=(
                None
                if data["last_success_at"] is None
                else datetime.fromisoformat(str(data["last_success_at"]))
            ),
            last_failure_at=(
                None
                if data["last_failure_at"] is None
                else datetime.fromisoformat(str(data["last_failure_at"]))
            ),
            failure_category=(
                None if data["failure_category"] is None else str(data["failure_category"])
            ),
            source_ref=None if data["source_ref"] is None else str(data["source_ref"]),
        )

    @staticmethod
    def _append(
        connection: sqlite3.Connection,
        *,
        operation_id: str,
        integration_id: str,
        event_kind: str,
        occurred_at: datetime,
        payload: str,
        fingerprint: str,
    ) -> bool:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT integration_id, event_kind, occurred_at, fingerprint, payload_json "
            "FROM admin_integration_events WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        if existing is not None:
            if (
                str(existing["integration_id"]) == integration_id
                and str(existing["event_kind"]) == event_kind
                and str(existing["occurred_at"]) == occurred_at.isoformat()
                and str(existing["fingerprint"]) == fingerprint
                and str(existing["payload_json"]) == payload
            ):
                return False
            raise IntegrationRegistryConflict(
                "integration operation id already has different content"
            )
        connection.execute(
            "INSERT INTO admin_integration_events"
            "(operation_id, integration_id, event_kind, occurred_at, fingerprint, payload_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                operation_id,
                integration_id,
                event_kind,
                occurred_at.isoformat(),
                fingerprint,
                payload,
            ),
        )
        return True

    def append_definition(
        self,
        *,
        operation_id: str,
        occurred_at: datetime,
        definition: IntegrationDefinition,
    ) -> bool:
        payload = self._definition_payload(definition)
        fingerprint = definition_fingerprint(definition)
        with self._connect() as connection:
            duplicate = connection.execute(
                "SELECT integration_id, event_kind, occurred_at, fingerprint, payload_json "
                "FROM admin_integration_events WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if duplicate is not None:
                return self._append(
                    connection,
                    operation_id=operation_id,
                    integration_id=definition.integration_id,
                    event_kind="DEFINITION",
                    occurred_at=occurred_at,
                    payload=payload,
                    fingerprint=fingerprint,
                )
            row = connection.execute(
                "SELECT payload_json FROM admin_integration_events WHERE integration_id = ? "
                "AND event_kind = 'DEFINITION' ORDER BY sequence DESC LIMIT 1",
                (definition.integration_id,),
            ).fetchone()
            expected_version = (
                1 if row is None else self._load_definition(str(row["payload_json"])).version + 1
            )
            if definition.version != expected_version:
                raise IntegrationRegistryConflict(
                    "integration definition version is out of sequence"
                )
            return self._append(
                connection,
                operation_id=operation_id,
                integration_id=definition.integration_id,
                event_kind="DEFINITION",
                occurred_at=occurred_at,
                payload=payload,
                fingerprint=fingerprint,
            )

    def append_health(
        self,
        *,
        operation_id: str,
        occurred_at: datetime,
        observation: IntegrationHealth,
    ) -> bool:
        payload = self._health_payload(observation)
        fingerprint = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
        with self._connect() as connection:
            registered = connection.execute(
                "SELECT 1 FROM admin_integration_events WHERE integration_id = ? "
                "AND event_kind = 'DEFINITION' LIMIT 1",
                (observation.integration_id,),
            ).fetchone()
            if registered is None:
                raise IntegrationRegistryConflict(
                    "cannot append health for an unregistered integration"
                )
            return self._append(
                connection,
                operation_id=operation_id,
                integration_id=observation.integration_id,
                event_kind="HEALTH",
                occurred_at=occurred_at,
                payload=payload,
                fingerprint=fingerprint,
            )

    def all_definitions(self) -> tuple[IntegrationDefinition, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM admin_integration_events WHERE event_kind = 'DEFINITION' "
                "ORDER BY sequence"
            ).fetchall()
        current: dict[str, IntegrationDefinition] = {}
        for row in rows:
            definition = self._load_definition(str(row["payload_json"]))
            current[definition.integration_id] = definition
        return tuple(current[key] for key in sorted(current))

    def latest_health(self, integration_id: str, *, as_of: datetime) -> IntegrationHealth | None:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("health projection as_of must be timezone-aware")
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT sequence, occurred_at, payload_json FROM admin_integration_events "
                "WHERE integration_id = ? AND event_kind = 'HEALTH' ORDER BY sequence",
                (integration_id,),
            ).fetchall()
        eligible: list[tuple[int, IntegrationHealth]] = []
        for row in rows:
            recorded_at = datetime.fromisoformat(str(row["occurred_at"]))
            observation = self._load_health(str(row["payload_json"]))
            if recorded_at <= as_of and observation.observed_at <= as_of:
                eligible.append((int(row["sequence"]), observation))
        if not eligible:
            return None
        _, latest = max(eligible, key=lambda item: (item[1].observed_at, item[0]))
        return latest
