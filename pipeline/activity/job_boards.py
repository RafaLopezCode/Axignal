"""Public job boards of applicant-tracking vendors, read on the source thread.

Each vendor publishes an open, unauthenticated board API meant for embedding a company's
openings on its own careers page. Only the fields an economic reading needs are kept
(title, location, country, department); descriptions and any personal data never are.
Each board is refreshed every three days; reads use only what is stored.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.activity import JOB_BOARDS_VERSION, function_of

USER_AGENT = "AXIGNAL/1.0 (https://axignal.com; economic observation) job-boards"
REFRESH = timedelta(days=3)
MAX_JOBS = 500
MAX_BYTES = 8_000_000

Fetch = Callable[[str], bytes]


def _http(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        return bytes(response.read(MAX_BYTES))


def _q(token: str) -> str:
    return urllib.parse.quote(token, safe="")


ENDPOINTS: dict[str, tuple[str, str]] = {
    # vendor: (api url, public board url)
    "GREENHOUSE": ("https://boards-api.greenhouse.io/v1/boards/{t}/jobs",
                   "https://job-boards.greenhouse.io/{t}"),
    "LEVER": ("https://api.lever.co/v0/postings/{t}?mode=json&limit=500",
              "https://jobs.lever.co/{t}"),
    "ASHBY": ("https://api.ashbyhq.com/posting-api/job-board/{t}", "https://jobs.ashbyhq.com/{t}"),
    "WORKABLE": ("https://apply.workable.com/api/v1/widget/accounts/{t}",
                 "https://apply.workable.com/{t}"),
    "RECRUITEE": ("https://{t}.recruitee.com/api/offers/", "https://{t}.recruitee.com/"),
    "SMARTRECRUITERS": ("https://api.smartrecruiters.com/v1/companies/{t}/postings?limit=100",
                        "https://careers.smartrecruiters.com/{t}"),
    "PERSONIO": ("https://{t}.jobs.personio.de/xml", "https://{t}.jobs.personio.de/"),
}  # fmt: skip


def _job(title: object, location: object = None, country: object = None,
         department: object = None) -> dict[str, str | None]:  # fmt: skip
    def text(value: object) -> str | None:
        return str(value).strip()[:120] if isinstance(value, str) and value.strip() else None

    named = text(department)
    return {
        "title": text(title),
        "location": text(location),
        "country": text(country),
        # Only a function is stored: boards sometimes put a recruiter's name here.
        "department": None if named is None else function_of(named),
    }


def parse(vendor: str, raw: bytes) -> list[dict[str, str | None]]:
    """Normalized openings: title, location, country (ISO when given), department."""
    if vendor == "PERSONIO":
        root = ET.fromstring(raw)
        return [
            _job(p.findtext("name"), p.findtext("office"), None, p.findtext("department"))
            for p in root.iter("position")
        ]
    data: Any = json.loads(raw)
    if vendor == "GREENHOUSE":
        return [_job(j.get("title"), (j.get("location") or {}).get("name"))
                for j in data.get("jobs") or []]  # fmt: skip
    if vendor == "LEVER":
        return [_job(j.get("text"), (j.get("categories") or {}).get("location"), j.get("country"),
                     (j.get("categories") or {}).get("department")
                     or (j.get("categories") or {}).get("team"))
                for j in data if isinstance(j, dict)]  # fmt: skip
    if vendor == "ASHBY":
        return [_job(j.get("title"), j.get("location"),
                     ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry"),
                     j.get("department"))
                for j in data.get("jobs") or [] if j.get("isListed", True)]  # fmt: skip
    if vendor == "WORKABLE":
        return [_job(j.get("title"), j.get("city") or j.get("location"), j.get("country"),
                     j.get("department"))
                for j in data.get("jobs") or []]  # fmt: skip
    if vendor == "RECRUITEE":
        return [_job(j.get("title"), j.get("location") or j.get("city"),
                     j.get("country_code"), j.get("department"))
                for j in data.get("offers") or []]  # fmt: skip
    if vendor == "SMARTRECRUITERS":
        return [_job(j.get("name"), (j.get("location") or {}).get("city"),
                     (j.get("location") or {}).get("country"),
                     (j.get("department") or {}).get("label"))
                for j in data.get("content") or []]  # fmt: skip
    return []


class JobBoards:
    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Fetch = _http,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._fetch = fetch
        self._clock = clock
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS job_boards (
                    board TEXT PRIMARY KEY, requested_at TEXT NOT NULL, read_at TEXT,
                    payload TEXT, error TEXT)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def request(self, board: str) -> None:
        vendor = board.split(":", 1)[0]
        if vendor not in ENDPOINTS:
            return
        with self._connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO job_boards (board, requested_at) VALUES (?,?)",
                (board, self._clock().isoformat()),
            )

    def latest(self, board: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM job_boards WHERE board=?", (board,)).fetchone()
        return None if row is None or row[0] is None else dict(json.loads(row[0]))

    def run(self, *, max_runs: int = 10) -> int:
        now = self._clock()
        with self._connect() as db:
            due = db.execute(
                """SELECT board FROM job_boards WHERE read_at IS NULL OR read_at <= ?
                ORDER BY read_at IS NOT NULL, read_at LIMIT ?""",
                ((now - REFRESH).isoformat(), max_runs),
            ).fetchall()
        for (board,) in due:
            vendor, token = board.split(":", 1)
            api, public = ENDPOINTS[vendor]
            try:
                jobs = parse(vendor, self._fetch(api.format(t=_q(token))))[:MAX_JOBS]
                payload: dict[str, Any] | None = {
                    "vendor": vendor,
                    "url": public.format(t=_q(token)),
                    "readAt": now.isoformat(),
                    "instrument": JOB_BOARDS_VERSION,
                    "jobs": [j for j in jobs if j["title"]],
                }
                error = None
            except Exception as failure:  # retried after REFRESH; the previous read stays
                payload, error = None, type(failure).__name__
            with self._connect() as db:
                if payload is None:
                    db.execute("UPDATE job_boards SET read_at=?, error=? WHERE board=?",
                               (now.isoformat(), error, board))  # fmt: skip
                else:
                    db.execute(
                        "UPDATE job_boards SET read_at=?, payload=?, error=NULL WHERE board=?",
                        (now.isoformat(), json.dumps(payload, ensure_ascii=False), board),
                    )
        return len(due)
