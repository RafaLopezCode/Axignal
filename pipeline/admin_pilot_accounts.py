"""Append-only, operator-private pilot preparation with atomic revision checks."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from application.admin_pilot_accounts import PilotAccounts, PilotAccountsConflict


class SqlitePilotAccountsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS pilot_test_account_preparation ("
                "revision INTEGER PRIMARY KEY, account_a TEXT NOT NULL, "
                "account_b TEXT NOT NULL, saved_by TEXT NOT NULL, saved_at TEXT NOT NULL)"
            )

    def read(self) -> PilotAccounts:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT account_a, account_b, revision, saved_by, saved_at "
                "FROM pilot_test_account_preparation ORDER BY revision DESC LIMIT 1"
            ).fetchone()
        return (
            PilotAccounts(row[0], row[1], row[2], row[3], datetime.fromisoformat(row[4]))
            if row
            else PilotAccounts()
        )

    def append(self, accounts: PilotAccounts, *, expected_revision: int) -> PilotAccounts:
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            revision = db.execute(
                "SELECT COALESCE(MAX(revision), 0) FROM pilot_test_account_preparation"
            ).fetchone()[0]
            if revision != expected_revision:
                raise PilotAccountsConflict("preparation revision conflict")
            assert accounts.saved_at is not None
            db.execute(
                "INSERT INTO pilot_test_account_preparation VALUES (?, ?, ?, ?, ?)",
                (
                    accounts.revision,
                    accounts.a,
                    accounts.b,
                    accounts.saved_by,
                    accounts.saved_at.isoformat(),
                ),
            )
        return accounts
