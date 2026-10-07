"""Spec 052 boundaries: additive migration and no model path into identity."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore

ROOT = Path(__file__).resolve().parents[2]


def test_existing_pending_rows_survive_the_identity_reason_migration(tmp_path: Path) -> None:
    path = tmp_path / "subscriber-runtime.sqlite3"
    SqliteSubscriberPortfolioStore(path)
    with sqlite3.connect(path) as connection:
        # Simulate a database created before spec 052 closed (no identity_reason column).
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("ALTER TABLE subscriber_portfolio_pending RENAME TO legacy_pending")
        connection.execute(
            """CREATE TABLE subscriber_portfolio_pending AS
               SELECT pending_id, tenant_id, idempotency_key, request_fingerprint, locator,
                      display_label, status, resolved_focus_id, created_at, updated_at
               FROM legacy_pending WHERE 0"""
        )
        connection.execute("DROP TABLE legacy_pending")
        connection.execute(
            """INSERT INTO subscriber_portfolio_pending VALUES
               ('pending_old', 'tenant:a', 'key', 'fp', 'Old Locator SL', NULL,
                'IDENTITY_PENDING', NULL, '2026-10-01T00:00:00+00:00',
                '2026-10-01T00:00:00+00:00')"""
        )
    SqliteSubscriberPortfolioStore(path)  # reopen: additive migration only
    with sqlite3.connect(path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(subscriber_portfolio_pending)")
        }
        row = connection.execute(
            "SELECT locator, status, identity_reason FROM subscriber_portfolio_pending"
        ).fetchone()
    assert "identity_reason" in columns
    assert row == ("Old Locator SL", "IDENTITY_PENDING", None)


def test_identity_admission_has_no_model_or_provider_path() -> None:
    """Models may propose; they never reach the code that admits identity."""
    files = [
        *sorted((ROOT / "application" / "organization_admission").glob("*.py")),
        ROOT / "pipeline" / "entity_resolution" / "organization_store.py",
    ]
    forbidden = ("cognition", "application.axent", "openai", "anthropic", "tools")
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            modules = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for module in modules:
                assert not module.startswith(forbidden), (path.name, module)
