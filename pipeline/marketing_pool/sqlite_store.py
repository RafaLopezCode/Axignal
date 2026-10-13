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
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, personas TEXT NOT NULL,
                    countries TEXT NOT NULL, target INTEGER NOT NULL, ends_at TEXT,
                    state TEXT NOT NULL, reason TEXT, created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                """
            )
            columns = {r["name"] for r in db.execute("PRAGMA table_info(prospects)")}
            if "campaign_id" not in columns:
                db.execute("ALTER TABLE prospects ADD COLUMN campaign_id TEXT")
            db.execute(
                "CREATE INDEX IF NOT EXISTS prospects_campaign ON prospects(campaign_id, state)"
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
    def add(
        self, candidates: list[Candidate], *, now: datetime, campaign_id: str | None = None
    ) -> int:
        """New domains only; a known or suppressed domain is never added again.

        A domain already in the pool keeps its first origin: a campaign never re-studies an
        organization the pool (or another campaign) already found.
        """
        added = 0
        with self._connect() as db:
            for c in candidates:
                domain = domain_of(c.website)
                if domain is None or self._suppressed(db, domain):
                    continue
                cursor = db.execute(
                    """INSERT OR IGNORE INTO prospects (domain, name, website, country,
                    persona, source, source_ref, state, discovered_at, updated_at, campaign_id)
                    VALUES (?,?,?,?,?,?,?,'DISCOVERED',?,?,?)""",
                    (domain, c.name[:200], c.website[:300], c.country, c.persona_hint,
                     c.source, c.source_ref[:300], now.isoformat(), now.isoformat(),
                     campaign_id),
                )  # fmt: skip
                added += cursor.rowcount
        return added

    # ---- campaigns --------------------------------------------------------------------
    def create_campaign(
        self,
        *,
        campaign_id: str,
        name: str,
        personas: list[str],
        countries: list[str],
        target: int,
        ends_at: datetime | None,
        actor: str,
        now: datetime,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO campaigns (id, name, personas, countries, target, ends_at,
                state, created_by, created_at, updated_at) VALUES (?,?,?,?,?,?,'ACTIVE',?,?,?)""",
                (campaign_id, name, json.dumps(personas), json.dumps(countries), target,
                 None if ends_at is None else ends_at.isoformat(), actor, now.isoformat(),
                 now.isoformat()),
            )  # fmt: skip
            db.execute(
                "INSERT INTO audit (domain, action, actor, at, note) VALUES (?,?,?,?,?)",
                (None, "CAMPAIGN_CREATED", actor, now.isoformat(), campaign_id),
            )

    def campaigns(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM campaigns ORDER BY created_at").fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["personas"] = json.loads(item["personas"])
            item["countries"] = json.loads(item["countries"])
            out.append(item)
        return out

    def end_campaign(
        self, campaign_id: str, state: str, *, reason: str, actor: str, now: datetime
    ) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                """UPDATE campaigns SET state=?, reason=?, updated_at=?
                WHERE id=? AND state='ACTIVE'""",
                (state, reason, now.isoformat(), campaign_id),
            )
            if cursor.rowcount:
                db.execute(
                    "INSERT INTO audit (domain, action, actor, at, note) VALUES (?,?,?,?,?)",
                    (None, f"CAMPAIGN_{state}", actor, now.isoformat(), campaign_id),
                )
        return bool(cursor.rowcount)

    def campaign_counts(self, campaign_id: str) -> dict[str, int]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT state, COUNT(*) n FROM prospects WHERE campaign_id=? GROUP BY state",
                (campaign_id,),
            ).fetchall()
            opted = db.execute(
                """SELECT COUNT(*) FROM prospects WHERE campaign_id=? AND state='SUPPRESSED'
                AND reason='RECIPIENT_OPT_OUT'""",
                (campaign_id,),
            ).fetchone()[0]
        out = {str(r["state"]): int(r["n"]) for r in rows}
        out["OPTED_OUT"] = int(opted)
        return out

    def waiting(self, campaign_id: str | None, *, limit: int = 500) -> list[dict[str, Any]]:
        """Discovered prospects of one campaign, or of the automatic pool (None)."""
        clause = "campaign_id IS NULL" if campaign_id is None else "campaign_id=?"
        params: tuple[object, ...] = () if campaign_id is None else (campaign_id,)
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM prospects WHERE state='DISCOVERED' AND {clause} "
                "ORDER BY discovered_at LIMIT ?",
                (*params, limit),
            ).fetchall()
        return [self._row(r) for r in rows]

    def yields(self) -> dict[tuple[str, str], tuple[int, int]]:
        """(persona, country) → (studied, qualified): what the pool has learned so far."""
        qualified = ("DRAFTED", "APPROVED", "SENT", "HELD", "SEND_FAILED")
        with self._connect() as db:
            rows = db.execute(
                """SELECT persona, country,
                SUM(state NOT IN ('DISCOVERED','STUDYING')) studied,
                SUM(state IN (?,?,?,?,?)) qualified
                FROM prospects GROUP BY persona, country""",
                qualified,
            ).fetchall()
        return {
            (str(r["persona"]), str(r["country"])): (
                int(r["studied"] or 0),
                int(r["qualified"] or 0),
            )
            for r in rows
        }

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
