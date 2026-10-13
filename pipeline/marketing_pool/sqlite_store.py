"""The marketing pool ledger: every organization once, ever; suppressions are permanent.

A prospect is keyed by its registrable website domain, so a candidate found again by any
source, persona or country is never studied or written to twice. Every decision is kept
in an append-only audit with its actor.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

#: DISCOVERED → STUDYING → (DRAFTED | HELD | NOT_QUALIFIED | STUDY_FAILED)
#: DRAFTED → APPROVED → SENT ; any open state → DISCARDED ; any → SUPPRESSED
STATES = (
    "DISCOVERED", "STUDYING", "DRAFTED", "HELD", "NOT_QUALIFIED", "STUDY_FAILED",
    "APPROVED", "SENT", "SEND_FAILED", "DISCARDED", "SUPPRESSED",
)  # fmt: skip


#: Platforms are not an organization's own website.
PLATFORMS = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "google.com",
    "business.site",
    "wixsite.com",
    "linktr.ee",
    "yelp.com",
    "pages.dev",
    "github.io",
    "blogspot.com",
    "wordpress.com",
    "medium.com",
)


def domain_of(website: str) -> str | None:
    host = (urlsplit(website if "//" in website else f"https://{website}").hostname or "").lower()
    host = host.removeprefix("www.")
    if any(host == p or host.endswith("." + p) for p in PLATFORMS):
        return None
    return host if "." in host and len(host) <= 253 else None


@dataclass(frozen=True, slots=True)
class Candidate:
    name: str
    website: str
    country: str
    persona_hint: str
    source: str
    source_ref: str


class SqliteMarketingPool:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS prospects (
                    domain TEXT PRIMARY KEY, name TEXT NOT NULL, website TEXT NOT NULL,
                    country TEXT NOT NULL, persona TEXT, source TEXT NOT NULL,
                    source_ref TEXT, state TEXT NOT NULL, reason TEXT, detail TEXT,
                    discovered_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS prospects_state ON prospects(state, discovered_at);
                CREATE TABLE IF NOT EXISTS suppressions (
                    value TEXT PRIMARY KEY, reason TEXT NOT NULL, at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS discovery_runs (
                    key TEXT PRIMARY KEY, at TEXT NOT NULL, found INTEGER NOT NULL,
                    added INTEGER NOT NULL, error TEXT);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, action TEXT NOT NULL,
                    actor TEXT NOT NULL, at TEXT NOT NULL, note TEXT);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    # ---- discovery ------------------------------------------------------------------
    def add(self, candidates: list[Candidate], *, now: datetime) -> int:
        """New domains only; a known or suppressed domain is never added again."""
        added = 0
        with self._connect() as db:
            for c in candidates:
                domain = domain_of(c.website)
                if domain is None or self._suppressed(db, domain):
                    continue
                cursor = db.execute(
                    """INSERT OR IGNORE INTO prospects (domain, name, website, country,
                    persona, source, source_ref, state, discovered_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,'DISCOVERED',?,?)""",
                    (domain, c.name[:200], c.website[:300], c.country, c.persona_hint,
                     c.source, c.source_ref[:300], now.isoformat(), now.isoformat()),
                )  # fmt: skip
                added += cursor.rowcount
        return added

    def discovery_done(self, key: str) -> tuple[str, str | None] | None:
        """When this search last ran, and the error if it failed."""
        with self._connect() as db:
            row = db.execute("SELECT at, error FROM discovery_runs WHERE key=?", (key,)).fetchone()
        return None if row is None else (str(row["at"]), row["error"])

    def record_discovery(
        self, key: str, *, now: datetime, found: int, added: int, error: str | None
    ) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO discovery_runs VALUES (?,?,?,?,?)",
                (key, now.isoformat(), found, added, error),
            )

    # ---- lifecycle ------------------------------------------------------------------
    def in_state(self, state: str, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM prospects WHERE state=? ORDER BY discovered_at LIMIT ?",
                (state, limit),
            ).fetchall()
        return [self._row(r) for r in rows]

    def get(self, domain: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM prospects WHERE domain=?", (domain,)).fetchone()
        return None if row is None else self._row(row)

    def move(
        self,
        domain: str,
        state: str,
        *,
        now: datetime,
        actor: str,
        reason: str | None = None,
        detail: Mapping[str, object] | None = None,
        persona: str | None = None,
        expected: tuple[str, ...] | None = None,
    ) -> bool:
        assert state in STATES
        with self._connect() as db:
            current = db.execute(
                "SELECT state, detail FROM prospects WHERE domain=?", (domain,)
            ).fetchone()
            if current is None or (expected is not None and current["state"] not in expected):
                return False
            merged = {**json.loads(current["detail"] or "{}"), **dict(detail or {})}
            db.execute(
                """UPDATE prospects SET state=?, reason=?, detail=?, updated_at=?,
                persona=COALESCE(?, persona) WHERE domain=?""",
                (state, reason, json.dumps(merged), now.isoformat(), persona, domain),
            )
            db.execute(
                "INSERT INTO audit (domain, action, actor, at, note) VALUES (?,?,?,?,?)",
                (domain, state, actor, now.isoformat(), reason),
            )
        return True

    def sent_today(self, day: str) -> int:
        with self._connect() as db:
            return int(
                db.execute(
                    "SELECT COUNT(*) FROM audit WHERE action='SENT' AND substr(at,1,10)=?",
                    (day,),
                ).fetchone()[0]
            )

    def studies_started_today(self, day: str) -> int:
        with self._connect() as db:
            return int(
                db.execute(
                    "SELECT COUNT(*) FROM audit WHERE action='STUDYING' AND substr(at,1,10)=?",
                    (day,),
                ).fetchone()[0]
            )

    # ---- suppression ----------------------------------------------------------------
    def suppress(self, value: str, *, reason: str, now: datetime, actor: str) -> None:
        """Never contact this domain or address again (an opt-out is permanent)."""
        value = value.strip().lower()
        with self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO suppressions VALUES (?,?,?)",
                (value, reason, now.isoformat()),
            )
            domain = value.rsplit("@", 1)[-1].removeprefix("www.")
            db.execute(
                "UPDATE prospects SET state='SUPPRESSED', reason=?, updated_at=? WHERE domain=?",
                (reason, now.isoformat(), domain),
            )
            db.execute(
                "INSERT INTO audit (domain, action, actor, at, note) VALUES (?,?,?,?,?)",
                (domain, "SUPPRESSED", actor, now.isoformat(), reason),
            )

    def is_suppressed(self, value: str) -> bool:
        with self._connect() as db:
            return self._suppressed(db, value)

    @staticmethod
    def _suppressed(db: sqlite3.Connection, value: str) -> bool:
        value = value.strip().lower()
        domain = value.rsplit("@", 1)[-1].removeprefix("www.")
        return (
            db.execute(
                "SELECT 1 FROM suppressions WHERE value IN (?, ?)", (value, domain)
            ).fetchone()
            is not None
        )

    # ---- admin projection -----------------------------------------------------------
    def counts(self) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute("SELECT state, COUNT(*) n FROM prospects GROUP BY state").fetchall()
            suppressed = db.execute("SELECT COUNT(*) FROM suppressions").fetchone()[0]
        out = {str(r["state"]): int(r["n"]) for r in rows}
        out["SUPPRESSION_LIST"] = int(suppressed)
        return out

    def recent(self, states: tuple[str, ...], *, limit: int = 100) -> list[dict[str, Any]]:
        marks = ",".join("?" * len(states))
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM prospects WHERE state IN ({marks}) "
                "ORDER BY updated_at DESC LIMIT ?",
                (*states, limit),
            ).fetchall()
        return [self._row(r) for r in rows]

    def discovery_log(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM discovery_runs ORDER BY at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        out = dict(row)
        out["detail"] = json.loads(out.get("detail") or "{}")
        return out
