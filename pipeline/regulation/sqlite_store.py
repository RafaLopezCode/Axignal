"""The regulation index and its daily ingestion, bounded per source and resumable."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from application.regulation import MAX_EU_CANDIDATES, RegulationItem, applies_in
from pipeline.regulation import sources

WINDOW = timedelta(days=60)
#: Entries about people or single cases, never sector rules (folded titles).
_NOISE = re.compile(
    r"recurso interpuesto|fe publica|nombramiento|se nombra|cese de|se dispone el cese|"
    r"convoca(?:toria)? .*(?:plaza|proceso selectivo)|oposicion|concurso de traslados|"
    r"jubilacion|designa|appointment of|replacing a member|sustituye a un miembro|"
    r"safety zone|security zone|drawbridge|special local regulation"
)
EVERY = timedelta(hours=12)
#: A source that failed is tried again after this, not on every tick.
RETRY_AFTER = timedelta(hours=1)
BOE_DAYS_PER_RUN = 7


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


class SqliteRegulationIndex:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS reg_items (
                    item_key TEXT PRIMARY KEY, source TEXT NOT NULL, scope TEXT NOT NULL,
                    language TEXT NOT NULL, published TEXT NOT NULL, title_fold TEXT NOT NULL,
                    payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS reg_items_scope ON reg_items(scope, published);
                CREATE TABLE IF NOT EXISTS reg_cursor (
                    source TEXT PRIMARY KEY, cursor TEXT, at TEXT NOT NULL, error TEXT);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def upsert(self, items: Sequence[RegulationItem]) -> int:
        rows = [
            (f"{i.source}|{i.item_id}", i.source, i.scope, i.language, i.published.isoformat(),
             _fold(i.title), json.dumps(i.to_wire()))
            for i in items
        ]  # fmt: skip
        with self._connect() as db:
            db.executemany("INSERT OR REPLACE INTO reg_items VALUES (?,?,?,?,?,?,?)", rows)
        return len(rows)

    def candidates(
        self,
        country: str,
        phrases: Sequence[str],
        *,
        keywords: Sequence[str] = (),
        since: date,
        language: str,
        limit: int = 40,
    ) -> list[dict[str, object]]:
        """Entries applying in ``country`` that speak of the activity, best first.

        Scored: an activity phrase counts 3, a single activity word 1; at least 2 are needed
        (one shared word is not enough). Personnel, appointments and individual appeals are
        never candidates. An EU act is read in the organization's language, else English.
        """
        scopes = {"EU"} if country.startswith("EU/") else set()
        parts = country.split("/")
        scopes |= {"/".join(parts[: i + 1]) for i in range(len(parts))}
        marks = ",".join("?" * len(scopes))
        with self._connect() as db:
            rows = db.execute(
                f"SELECT title_fold, payload FROM reg_items WHERE scope IN ({marks}) "
                "AND published >= ? ORDER BY published DESC LIMIT 20000",
                (*sorted(scopes), since.isoformat()),
            ).fetchall()
        whole = [re.compile(rf"(?<![a-z]){re.escape(k)}") for k in phrases]
        single = [re.compile(rf"(?<![a-z]){re.escape(k)}") for k in keywords]
        chosen: dict[str, dict[str, object]] = {}
        for folded, payload in rows:
            if _NOISE.search(folded):
                continue
            score = 3 * sum(1 for w in whole if w.search(folded)) + sum(
                1 for w in single if w.search(folded)
            )
            if score < 2:
                continue
            item = json.loads(payload)
            if not applies_in(str(item["scope"]), country):
                continue
            if item["source"] == "EUR_LEX" and item["language"] not in {language, "en"}:
                continue
            key = (
                str(item["id"]).split(":", 1)[0] if item["source"] == "EUR_LEX" else str(item["id"])
            )
            held = chosen.get(key)
            item["score"] = score
            if held is None or (item["language"] == language and held["language"] != language):
                chosen[key] = item
        ordered = sorted(
            chosen.values(), key=lambda i: (int(str(i["score"])), str(i["published"])),
            reverse=True,
        )  # fmt: skip
        # EU acts are many and long-titled: they never crowd out the national journal.
        eu = [i for i in ordered if i["source"] == "EUR_LEX"][:MAX_EU_CANDIDATES]
        national = [i for i in ordered if i["source"] != "EUR_LEX"]
        kept = [*national[: max(0, limit - len(eu))], *eu]
        return sorted(kept, key=lambda i: str(i["published"]), reverse=True)[:limit]

    def last_error(self, source: str) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT error FROM reg_cursor WHERE source=?", (source,)).fetchone()
        return None if row is None else row[0]

    def cursor(self, source: str) -> tuple[str | None, datetime | None]:
        with self._connect() as db:
            row = db.execute(
                "SELECT cursor, at FROM reg_cursor WHERE source=?", (source,)
            ).fetchone()
        return (None, None) if row is None else (row[0], datetime.fromisoformat(row[1]))

    def set_cursor(
        self, source: str, cursor: str | None, *, at: datetime, error: str | None
    ) -> None:
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO reg_cursor VALUES (?,?,?,?)",
                       (source, cursor, at.isoformat(), error))  # fmt: skip


class RegulationIngestor:
    """Each source on its own clock: the BOE day by day, the others twice a day."""

    def __init__(
        self,
        index: SqliteRegulationIndex,
        *,
        fetch: sources.Fetch = sources._urlopen,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._index = index
        self._fetch = fetch
        self._clock = clock

    def run(self) -> int:
        added = 0
        for source, step in (
            ("BOE", self._boe),
            ("FEDERAL_REGISTER", self._federal_register),
            ("EUR_LEX", self._eur_lex),
            ("LEGISLATION_GOV_UK", self._uk),
        ):
            try:
                added += step()
            except Exception as error:  # one journal failing never stops the others
                # Recorded with its time: retried after RETRY_AFTER, not on every tick.
                cursor, _at = self._index.cursor(source)
                self._index.set_cursor(source, cursor, at=self._clock(),
                                       error=type(error).__name__)  # fmt: skip
        return added

    def _due(self, source: str) -> tuple[str | None, bool]:
        cursor, at = self._index.cursor(source)
        wait = RETRY_AFTER if self._index.last_error(source) else EVERY
        return cursor, at is None or self._clock() - at >= wait

    def _boe(self) -> int:
        today = self._clock().date()
        cursor, at = self._index.cursor("BOE")
        caught_up = cursor is not None and cursor >= (today - timedelta(days=1)).isoformat()
        if caught_up and at is not None and self._clock() - at < timedelta(hours=1):
            return 0  # up to date: today's summary is looked for at most hourly
        start = (
            max(today - WINDOW, date.fromisoformat(cursor) + timedelta(days=1))
            if cursor
            else today - WINDOW
        )
        added, day = 0, start
        for _ in range(BOE_DAYS_PER_RUN):
            if day > today:
                break
            try:
                added += self._index.upsert(sources.read_boe(day, self._fetch))
            except Exception as error:  # no summary that day (weekend) or unavailable
                if day >= today:
                    self._index.set_cursor("BOE", (day - timedelta(days=1)).isoformat(),
                                           at=self._clock(), error=type(error).__name__)  # fmt: skip
                    return added
            self._index.set_cursor("BOE", day.isoformat(), at=self._clock(), error=None)
            day += timedelta(days=1)
        return added

    def _federal_register(self) -> int:
        cursor, due = self._due("FEDERAL_REGISTER")
        if not due:
            return 0
        since = self._clock().date() - (timedelta(days=3) if cursor else WINDOW)
        added = self._index.upsert(sources.read_federal_register(since, self._fetch))
        self._index.set_cursor("FEDERAL_REGISTER", since.isoformat(), at=self._clock(), error=None)
        return added

    def _eur_lex(self) -> int:
        cursor, due = self._due("EUR_LEX")
        if not due:
            return 0
        since = self._clock().date() - (timedelta(days=10) if cursor else WINDOW)
        added = self._index.upsert(sources.read_eur_lex(since, self._fetch))
        self._index.set_cursor("EUR_LEX", since.isoformat(), at=self._clock(), error=None)
        return added

    def _uk(self) -> int:
        _cursor, due = self._due("LEGISLATION_GOV_UK")
        if not due:
            return 0
        added = self._index.upsert(sources.read_legislation_gov_uk(self._fetch))
        self._index.set_cursor("LEGISLATION_GOV_UK", self._clock().date().isoformat(),
                               at=self._clock(), error=None)  # fmt: skip
        return added
