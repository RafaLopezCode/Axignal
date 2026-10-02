"""SQLite append-only event store for AO-09 customer accounts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from application.admin_customer_accounts import replay_account
from domain.admin_customer_accounts import (
    AccountEvent,
    AccountEventId,
    AccountEventKind,
    AccountId,
    AccountSnapshot,
)


class SqliteAdminCustomerAccountStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_customer_account_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    account_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_customer_account_events_account
                ON admin_customer_account_events(account_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _payload(event: AccountEvent) -> str:
        return json.dumps(dict(event.payload), sort_keys=True, separators=(",", ":"))

    def append(self, event: AccountEvent) -> bool:
        payload_json = self._payload(event)
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT account_id, kind, occurred_at, actor, reason, payload_json
                FROM admin_customer_account_events
                WHERE event_id = ?
                """,
                (str(event.event_id),),
            ).fetchone()
            if existing is not None:
                expected = (
                    str(event.account_id),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.actor,
                    event.reason,
                    payload_json,
                )
                actual = tuple(
                    str(existing[key])
                    for key in (
                        "account_id",
                        "kind",
                        "occurred_at",
                        "actor",
                        "reason",
                        "payload_json",
                    )
                )
                if actual == expected:
                    return False
                raise ValueError("account event id reused with different immutable content")
            connection.execute(
                """
                INSERT INTO admin_customer_account_events(
                    event_id, account_id, kind, occurred_at, actor, reason, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id),
                    str(event.account_id),
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.actor,
                    event.reason,
                    payload_json,
                ),
            )
        return True

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AccountEvent:
        from datetime import datetime

        data = json.loads(str(row["payload_json"]))
        return AccountEvent(
            event_id=AccountEventId(str(row["event_id"])),
            account_id=AccountId(str(row["account_id"])),
            kind=AccountEventKind(str(row["kind"])),
            occurred_at=datetime.fromisoformat(str(row["occurred_at"])),
            actor=str(row["actor"]),
            reason=str(row["reason"]),
            payload=tuple(sorted((str(key), str(value)) for key, value in data.items())),
        )

    def for_account(self, account_id: AccountId) -> tuple[AccountEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, account_id, kind, occurred_at, actor, reason, payload_json
                FROM admin_customer_account_events
                WHERE account_id = ?
                ORDER BY sequence
                """,
                (str(account_id),),
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def all_events(self) -> tuple[AccountEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, account_id, kind, occurred_at, actor, reason, payload_json
                FROM admin_customer_account_events
                ORDER BY sequence
                """
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def snapshot_for_tenant(self, tenant_id: str) -> AccountSnapshot | None:
        account_ids: list[str] = []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT account_id
                FROM admin_customer_account_events
                WHERE kind = ?
                  AND json_extract(payload_json, '$.tenant_id') = ?
                ORDER BY account_id
                """,
                (AccountEventKind.ACCOUNT_SIGNED_UP.value, tenant_id),
            ).fetchall()
            account_ids.extend(str(row["account_id"]) for row in rows)
        if not account_ids:
            return None
        if len(account_ids) > 1:
            raise ValueError("tenant linked to multiple AXIGNAL accounts")
        return replay_account(self.for_account(AccountId(account_ids[0])))
