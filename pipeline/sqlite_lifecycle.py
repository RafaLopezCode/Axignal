"""Deterministic sqlite connection lifecycle for pipeline and tool stores.

``with connection:`` on a ``sqlite3.Connection`` only commits or rolls back the
active transaction; it never closes the connection. A store that opens a
connection, executes ``BEGIN IMMEDIATE`` and then raises keeps its write
transaction (and the database lock) alive until garbage collection, which can
block concurrent processes. Every store therefore enters its connections
through this module so commit/rollback and close always happen together.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


@contextmanager
def closing_connection(
    database: str | Path,
    *,
    uri: bool = False,
    timeout: float = 5.0,
    row_factory: Any | None = None,
    foreign_keys: bool = False,
    busy_timeout_ms: int | None = None,
) -> Iterator[sqlite3.Connection]:
    """Open one sqlite connection that commits, rolls back and closes deterministically."""
    connection = sqlite3.connect(database, uri=uri, timeout=timeout)
    try:
        if row_factory is not None:
            connection.row_factory = row_factory
        if foreign_keys:
            connection.execute("PRAGMA foreign_keys = ON")
        if busy_timeout_ms is not None:
            connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
        with connection:
            yield connection
    finally:
        connection.close()
