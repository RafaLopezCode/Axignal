"""Web research runner: searches proposed by an index, pages read by AXIGNAL (spec 098).

Requests are queued when an observation is read; a background stage researches a few per
tick. Searches are paid API requests: each query is shared by every organization that asks
it (30 days), and a global daily cap bounds the spend, which is recorded with every search.
Each candidate page is read with the governed reader (robots.txt first, bounded GETs, no
authentication, no bypass) and only its own text supports a finding. Off unless the key
file is mounted.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from application.first_observation.service import FetchedResource
from application.first_observation.site import RobotsReading, read_page
from application.press.mentions import search_terms
from application.web_research import (
    PageCheck,
    PlannedQuery,
    ResearchSubject,
    WebHit,
    WebSearch,
    candidates,
    check_page,
    page_key,
    plan,
)
from pipeline.web_search.article import read_article

TTL = timedelta(days=30)
MAX_SEARCHES_PER_DAY = 120  # paid requests per UTC day, all tenants together (≈ $0.09)
COUNT = 10


class PageFetcher(Protocol):
    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource: ...


class WebResearchRunner:
    def __init__(
        self,
        search: WebSearch,
        fetcher: PageFetcher,
        database_path: str | Path,
        *,
        usd_per_request: float,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_searches_per_day: int = MAX_SEARCHES_PER_DAY,
    ) -> None:
        self._search = search
        self._fetcher = fetcher
        self._usd = usd_per_request
        self._clock = clock
        self._max_per_day = max_searches_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS research (
                    subject_key TEXT PRIMARY KEY, subject TEXT NOT NULL, state TEXT NOT NULL,
                    result TEXT, requested_at TEXT NOT NULL, researched_at TEXT);
                CREATE TABLE IF NOT EXISTS searches (
                    query TEXT PRIMARY KEY, hits TEXT NOT NULL, searched_at TEXT NOT NULL,
                    billed INTEGER NOT NULL, usd REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS pages (
                    check_key TEXT PRIMARY KEY, page TEXT NOT NULL, checked_at TEXT NOT NULL);
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

    def result(self, subject: ResearchSubject) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT result FROM research WHERE subject_key=? AND state='DONE'",
                (subject.key,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["result"]))

    def request(self, subject: ResearchSubject) -> None:
        """Queue research unless a fresh one exists or one is already queued."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, researched_at FROM research WHERE subject_key=?", (subject.key,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (
                    row["researched_at"]
                    and now - datetime.fromisoformat(row["researched_at"]) < TTL
                )
            ):
                return
            db.execute(
                """INSERT INTO research (subject_key, subject, state, requested_at)
                VALUES (?,?,'QUEUED',?) ON CONFLICT(subject_key) DO UPDATE SET
                state='QUEUED', requested_at=excluded.requested_at""",
                (subject.key, json.dumps(_wire(subject)), now.isoformat()),
            )

    def spent_today(self) -> tuple[int, float]:
        day = self._clock().date().isoformat()
        with self._connect() as db:
            row = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(usd),0) FROM searches WHERE substr(searched_at,1,10)=?",
                (day,),
            ).fetchone()
        return int(row[0]), float(row[1])

    def _hits(self, query: str) -> tuple[list[WebHit], bool] | None:
        """Shared hits for a query (fresh), else one search under the cap, and whether it was
        billed; None when the cap is reached."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT hits, searched_at FROM searches WHERE query=?", (query,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row["searched_at"]) < TTL:
            return [WebHit.from_wire(h) for h in json.loads(row["hits"])], False
        if self.spent_today()[0] >= self._max_per_day:
            return None
        hits = list(self._search.search(query, count=COUNT))  # raises when unavailable
        billed = 1 if hits else 0  # empty answers are not billed
        with self._connect() as db:
            db.execute(
                """INSERT INTO searches (query, hits, searched_at, billed, usd) VALUES (?,?,?,?,?)
                ON CONFLICT(query) DO UPDATE SET hits=excluded.hits,
                searched_at=excluded.searched_at, billed=excluded.billed, usd=excluded.usd""",
                (query, json.dumps([h.to_wire() for h in hits]), now.isoformat(), billed,
                 round(billed * self._usd, 6)),
            )  # fmt: skip
        return hits, bool(billed)

    def _check(self, hit: WebHit, needles: Sequence[str], own_domain: str) -> PageCheck:
        key = f"{hit.url}|{'/'.join(needles)}|{own_domain}"
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT page, checked_at FROM pages WHERE check_key=?", (key,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row["checked_at"]) < TTL:
            return PageCheck.from_wire(json.loads(row["page"]))
        check = self._read(hit.url, needles, own_domain)
        with self._connect() as db:
            db.execute(
                """INSERT INTO pages (check_key, page, checked_at) VALUES (?,?,?)
                ON CONFLICT(check_key) DO UPDATE SET page=excluded.page,
                checked_at=excluded.checked_at""",
                (key, json.dumps(check.to_wire()), now.isoformat()),
            )
        return check

    def _read(self, url: str, needles: Sequence[str], own_domain: str) -> PageCheck:
        parts = urlsplit(url)
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
        robots = self._fetcher.fetch(robots_url, slot="web-research")
        if robots.status == 200 and robots.body is not None:
            reading = RobotsReading(_text(robots)[:512_000], robots.observed_at)
        elif robots.status in {404, 410}:
            reading = RobotsReading(None, robots.observed_at)  # none published (RFC 9309)
        else:
            # robots.txt unknown: not read
            return PageCheck(url, "UNREADABLE", reason=f"ROBOTS:{robots.failure or robots.status}")
        if not reading.allows(url):
            return PageCheck(url, "ROBOTS_DISALLOWED")
        fetched = self._fetcher.fetch(url, slot="web-research")
        if (
            fetched.status != 200
            or fetched.body is None
            or "html" not in (fetched.content_type or "html").lower()
        ):
            reason = fetched.failure or f"HTTP_{fetched.status}"
            return PageCheck(url, "UNREADABLE", reason=reason)
        html = _text(fetched)
        page = read_page(
            url=fetched.final_url, html=html, observed_at=fetched.observed_at,
            content_fingerprint=fetched.content_fingerprint or "", artifact_ref=None,
        )  # fmt: skip
        # The mention must be in the title or the main text: navigation, footers and brand
        # lists say nothing about the organization (spec 099). Whole page when unavailable.
        article = read_article(html, fetched.final_url)
        return check_page(
            fetched.final_url, title=page.title or (article.title if article else ""),
            text=article.text if article else page.text,
            links=[href for href, _ in page.links], needles=needles, own_domain=own_domain,
            read_at=fetched.observed_at.isoformat(),
            published=article.published if article else None,
        )  # fmt: skip

    def run(self, *, max_runs: int = 2) -> int:
        with self._connect() as db:
            queued = db.execute(
                "SELECT subject_key, subject FROM research WHERE state='QUEUED' ORDER BY requested_at LIMIT ?",
                (max_runs,),
            ).fetchall()
        ran = 0
        for row in queued:
            wire = json.loads(row["subject"])
            subject = ResearchSubject(
                names=tuple(wire["names"]), domain=str(wire["domain"]),
                language=str(wire["language"]), activity_terms=tuple(wire["activityTerms"]),
            )  # fmt: skip
            try:
                result = self._research(subject)
            except Exception:  # unavailable: stays queued for a later tick, nothing invented
                continue
            if result is None:
                continue  # the daily cap was reached: stays queued
            with self._connect() as db:
                db.execute(
                    "UPDATE research SET state='DONE', result=?, researched_at=? WHERE subject_key=?",
                    (json.dumps(result), result["researchedAt"], row["subject_key"]),
                )
            ran += 1
        return ran

    def _research(self, subject: ResearchSubject) -> dict[str, object] | None:
        planned: Sequence[PlannedQuery] = plan(subject, today=self._clock().date())
        names = search_terms(subject.names)
        pages: list[dict[str, object]] = []
        searched = 0
        seen: set[str] = set()
        for query in planned:
            found = self._hits(query.query)
            if found is None:
                return None
            hits, paid = found
            searched += int(paid)
            needles = names if query.purpose == "REPUTATION" else list(subject.activity_terms)
            for hit in candidates(hits, subject, purpose=query.purpose):
                if page_key(hit.url) in seen:
                    continue
                seen.add(page_key(hit.url))
                check = self._check(hit, needles, subject.domain)
                pages.append({
                    **check.to_wire(), "purpose": query.purpose,
                    "siteName": hit.site_name, "indexedDate": hit.indexed_date,
                    "rerank": hit.rerank,
                })  # fmt: skip
        return {
            "instrument": {"search": self._search.instrument, "reader": "governed-site-reader"},
            "queries": [{"purpose": q.purpose, "query": q.query} for q in planned],
            "pages": pages,
            "researchedAt": self._clock().isoformat(),
            "cost": {"paidSearches": searched, "usd": round(searched * self._usd, 6)},
        }


def _text(fetched: FetchedResource) -> str:
    body = fetched.body or b""
    charset = "utf-8"
    content_type = fetched.content_type or ""
    if "charset=" in content_type.lower():
        charset = content_type.lower().split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
    try:
        return body.decode(charset, "replace")
    except LookupError:
        return body.decode("utf-8", "replace")


def _wire(subject: ResearchSubject) -> dict[str, object]:
    return {
        "names": list(subject.names), "domain": subject.domain, "language": subject.language,
        "activityTerms": list(subject.activity_terms),
    }  # fmt: skip


KEY_FILE = "AXIGNAL_DEEPSEEK_API_KEY_FILE"
ENABLED = "AXIGNAL_WEB_RESEARCH_ENABLED"


def web_research_from_values(
    values: Mapping[str, str], root: Path, fetcher: PageFetcher
) -> WebResearchRunner | None:
    """On only when explicitly enabled and the API key file is mounted and readable."""
    if values.get(ENABLED, "false").strip().lower() != "true":
        return None
    filename = values.get(KEY_FILE, "").strip()
    if not filename:
        return None
    key_file = Path(filename)
    if not key_file.is_absolute() or not key_file.is_file() or not os.access(key_file, os.R_OK):
        return None
    from pipeline.web_search.deepseek import USD_PER_REQUEST, DeepSeekSearch

    return WebResearchRunner(
        DeepSeekSearch(key_file), fetcher, root / "web-research.sqlite3",
        usd_per_request=USD_PER_REQUEST,
    )  # fmt: skip
