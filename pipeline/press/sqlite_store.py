"""World press index: syndicated headlines (no article text) and per-feed read state."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

from application.press.contracts import PressFeed, PressItem


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


class FeedTransport(Protocol):
    def get(self, url: str) -> tuple[int, bytes]: ...


class SqlitePressIndex:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS press_items (
                    url TEXT PRIMARY KEY,
                    feed_id TEXT NOT NULL,
                    outlet TEXT NOT NULL,
                    title TEXT NOT NULL,
                    title_folded TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    language TEXT NOT NULL,
                    country TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_press_published ON press_items(published_at);
                CREATE TABLE IF NOT EXISTS press_feeds (
                    feed_id TEXT PRIMARY KEY,
                    read_at TEXT,
                    status TEXT,
                    items INTEGER NOT NULL DEFAULT 0
                );
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

    def upsert(self, items: Sequence[PressItem]) -> int:
        rows = [
            (i.url, i.feed_id, i.outlet, i.title, _fold(i.title), i.published_at.isoformat(), i.language, i.country)
            for i in items
        ]  # fmt: skip
        if rows:
            with self._connect() as db:
                db.executemany(
                    """INSERT INTO press_items VALUES (?,?,?,?,?,?,?,?)
                    ON CONFLICT(url) DO UPDATE SET title=excluded.title,
                    title_folded=excluded.title_folded""",
                    rows,
                )
        return len(rows)

    def mark_read(self, feed_id: str, *, at: datetime, status: str, items: int) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO press_feeds (feed_id, read_at, status, items) VALUES (?,?,?,?)
                ON CONFLICT(feed_id) DO UPDATE SET read_at=excluded.read_at,
                status=excluded.status, items=press_feeds.items + excluded.items""",
                (feed_id, at.isoformat(), status, items),
            )

    def read_at(self, feed_id: str) -> datetime | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT read_at FROM press_feeds WHERE feed_id=?", (feed_id,)
            ).fetchone()
        return (
            None
            if row is None or row["read_at"] is None
            else datetime.fromisoformat(row["read_at"])
        )

    def items_matching(
        self, terms: Sequence[str], *, since: datetime, limit: int = 500
    ) -> tuple[PressItem, ...]:
        """Headlines since a date containing any of the folded terms (prefilter)."""
        if not terms:
            return ()
        clause = " OR ".join("title_folded LIKE ?" for _ in terms)
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM press_items WHERE published_at>=? AND ({clause}) "
                "ORDER BY published_at DESC LIMIT ?",
                (since.isoformat(), *(f"%{t}%" for t in terms), limit),
            ).fetchall()
        return tuple(
            PressItem(
                r["feed_id"], r["outlet"], r["title"], r["url"],
                datetime.fromisoformat(r["published_at"]), r["language"], r["country"],
            )
            for r in rows
        )  # fmt: skip

    def coverage(self) -> tuple[datetime | None, int, int]:
        """(earliest headline held, headlines held, feeds read successfully)."""
        with self._connect() as db:
            row = db.execute(
                "SELECT MIN(published_at) AS since, COUNT(*) AS n FROM press_items"
            ).fetchone()
            feeds = db.execute("SELECT COUNT(*) FROM press_feeds WHERE status='OK'").fetchone()[0]
        since = None if row["since"] is None else datetime.fromisoformat(row["since"])
        return since, int(row["n"]), int(feeds)


class PressIngestor:
    """Reads each registered feed at most once per ``every``; a refusal is recorded, not retried."""

    def __init__(
        self,
        feeds: Sequence[PressFeed],
        store: SqlitePressIndex,
        transport: FeedTransport,
        *,
        clock: Callable[[], datetime],
        every: timedelta = timedelta(hours=6),
    ) -> None:
        self._feeds = tuple(feeds)
        self._store = store
        self._transport = transport
        self._clock = clock
        self._every = every

    def run(self, *, max_feeds: int = 6) -> int:
        from pipeline.press.rss import parse_feed

        read = 0
        now = self._clock()
        for feed in self._feeds:
            if read >= max_feeds:
                break
            last = self._store.read_at(feed.feed_id)
            if last is not None and now - last < self._every:
                continue
            read += 1
            try:
                status, body = self._transport.get(feed.url)
                if status != 200:
                    self._store.mark_read(feed.feed_id, at=now, status=f"HTTP_{status}", items=0)
                    continue
                items = parse_feed(feed, body)
            except Exception as error:  # a refusal or a broken feed is recorded, never bypassed
                self._store.mark_read(feed.feed_id, at=now, status=type(error).__name__, items=0)
                continue
            self._store.mark_read(
                feed.feed_id, at=now, status="OK", items=self._store.upsert(items)
            )
        return read
