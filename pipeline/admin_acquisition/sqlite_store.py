"""Append-only AO-15 acquisition event store."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_acquisition import (
    BriefRequestEvent,
    BriefRequestEventId,
    BriefRequestEventKind,
    BriefRequestId,
)


class AcquisitionStoreConflict(ValueError):
    pass


class SqliteAdminAcquisitionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS admin_acquisition_events ("
                "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
                "event_id TEXT NOT NULL UNIQUE,"
                "request_id TEXT NOT NULL,"
                "kind TEXT NOT NULL,"
                "occurred_at TEXT NOT NULL,"
                "actor TEXT NOT NULL,"
                "fingerprint TEXT NOT NULL,"
                "payload_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_admin_acquisition_request "
                "ON admin_acquisition_events(request_id, sequence)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(event: BriefRequestEvent) -> str:
        values = {
            "event_id": str(event.event_id),
            "request_id": str(event.request_id),
            "kind": event.kind.value,
            "occurred_at": event.occurred_at.isoformat(),
            "actor": event.actor,
            "payload": list(event.payload),
        }
        return json.dumps(values, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _fingerprint(payload: str) -> str:
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"

    def append_event(self, event: BriefRequestEvent) -> bool:
        payload = self._payload(event)
        fingerprint = self._fingerprint(payload)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT fingerprint, payload_json FROM admin_acquisition_events WHERE event_id = ?",
                (str(event.event_id),),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["fingerprint"]) == fingerprint
                    and str(existing["payload_json"]) == payload
                ):
                    return False
                raise AcquisitionStoreConflict(
                    "brief request event id reused with different content"
                )
            connection.execute(
                "INSERT INTO admin_acquisition_events("
                "event_id, request_id, kind, occurred_at, actor, fingerprint, payload_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    str(event.request_id),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.actor,
                    fingerprint,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _event(row: sqlite3.Row) -> BriefRequestEvent:
        payload = json.loads(str(row["payload_json"]))
        return BriefRequestEvent(
            event_id=BriefRequestEventId(payload["event_id"]),
            request_id=BriefRequestId(payload["request_id"]),
            kind=BriefRequestEventKind(payload["kind"]),
            occurred_at=datetime.fromisoformat(payload["occurred_at"]),
            actor=payload["actor"],
            payload=tuple((str(key), str(value)) for key, value in payload["payload"]),
        )

    def events_for_request(self, request_id: str) -> tuple[BriefRequestEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_acquisition_events WHERE request_id = ? ORDER BY sequence",
                (request_id,),
            ).fetchall()
        return tuple(self._event(row) for row in rows)

    def all_events(self) -> tuple[BriefRequestEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM admin_acquisition_events ORDER BY sequence"
            ).fetchall()
        return tuple(self._event(row) for row in rows)
