"""Activity from the organization's public job board: what it is hiring for, and where.

Many organizations publish their openings through an applicant-tracking vendor whose
public job board is meant to be embedded and read (Greenhouse, Lever, Ashby, Workable,
Recruitee, SmartRecruiters, Personio, Teamtailor). The board is found on its own website
(a link or an embed), so it is the organization's own declaration: DECLARED. Openings
are activity (what it is building now); the countries it hires in are market evidence.
Global by construction: the same vendors serve organizations in every country.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import parse_qs, urlsplit

from application.first_observation.geography import country_code, us_state

JOB_BOARDS_VERSION = "job-boards-v1"
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,60}$")
_NOT_TOKENS = frozenset({"embed", "v1", "jobs", "api", "careers", "postings", "job_board", "js"})


def _token(value: str | None) -> str | None:
    return value if value and _TOKEN.match(value) and value.lower() not in _NOT_TOKENS else None


def board_of(url: str) -> tuple[str, str] | None:
    """(vendor, board token) for a public job board link or embed, else None."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    segments = [s for s in parts.path.split("/") if s]
    first = segments[0] if segments else None
    if host.endswith("greenhouse.io"):
        embedded = parse_qs(parts.query).get("for", [None])[0]
        if host.startswith("boards-api."):
            return (
                ("GREENHOUSE", t)
                if (t := _token(segments[2] if len(segments) > 2 else None))
                else None
            )
        token = _token(embedded) or _token(first)
        return ("GREENHOUSE", token) if token else None
    if host in {"jobs.lever.co", "jobs.eu.lever.co"}:
        return ("LEVER", t) if (t := _token(first)) else None
    if host == "jobs.ashbyhq.com":
        return ("ASHBY", t) if (t := _token(first)) else None
    if host == "apply.workable.com":
        return ("WORKABLE", t) if (t := _token(first)) else None
    if host in {"careers.smartrecruiters.com", "jobs.smartrecruiters.com"}:
        return ("SMARTRECRUITERS", t) if (t := _token(first)) else None
    for suffix, vendor in ((".recruitee.com", "RECRUITEE"), (".jobs.personio.de", "PERSONIO"),
                           (".jobs.personio.com", "PERSONIO"), (".teamtailor.com", "TEAMTAILOR")):  # fmt: skip
        if host.endswith(suffix):
            token = _token(host[: -len(suffix)].split(".")[-1])
            return (vendor, token) if token else None
    return None


def country_of_location(location: str | None) -> str | None:
    """ISO country of a posting location ("Madrid, Spain", "San Francisco, CA", "DE")."""
    if not location:
        return None
    parts = [p.strip() for p in re.split(r"[,;|/()\-\u2013]", location) if p.strip()]
    # "San Francisco, CA": a two-letter US state after a city is the US, not Canada.
    if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isupper() and us_state(parts[-1]):
        return "US"
    for part in reversed(parts):
        code = country_code(part)
        if code and len(code) == 2:
            return code
        if us_state(part):
            return "US"
    return None


#: Function words, multilingual. A department label is kept only when it names a
#: function with one of them: boards sometimes carry a recruiter's name in that field,
#: and a person's name must never be stored. Anything else counts as OTHER.
FUNCTION_WORDS = frozenset(
    """
    engineering engineer software data analytics product design ux ui research science
    sales marketing growth brand communications commercial business partnerships
    customer support success service care operations ops logistics supply finance
    accounting legal compliance risk security people hr talent recruiting admin
    strategy consulting creative content media editorial production manufacturing
    quality maintenance construction projects procurement purchasing it infrastructure
    platform mobile ai ml insurance claims medical clinical health education teaching
    ingenieria ingeniería ventas comercial marketing producto diseño datos finanzas
    operaciones atencion atención clientes legal personas recursos humanos tecnologia
    tecnología vertrieb technik entwicklung produkt kunden finanzen personal recht
    beratung kreation ventes ingénierie produit données finances juridique clients
    opérations vendite tecnologia prodotto dati finanza
    """.split()  # noqa: SIM905
)


def function_of(department: str | None) -> str:
    """The department label when it names a function; otherwise OTHER (never stored)."""
    if not department:
        return "OTHER"
    words = set(re.findall(r"[^\W\d_]+", department.casefold()))
    return department[:60] if words & FUNCTION_WORDS else "OTHER"


def _country(job: Mapping[str, Any]) -> str | None:
    raw = job.get("country")
    if isinstance(raw, str) and raw.strip():
        code = country_code(raw)
        if code and len(code) == 2:
            return code
    return country_of_location(str(job.get("location") or ""))


def job_board_discoveries(
    result: Mapping[str, Any] | None, *, source_page: str | None
) -> list[dict[str, object]]:
    """Open positions (activity) and hiring countries (markets) from a stored board read."""
    if not result or not isinstance(result.get("jobs"), list):
        return []
    jobs = [j for j in result["jobs"] if isinstance(j, Mapping) and j.get("title")]
    vendor, url, read_at = result.get("vendor"), result.get("url"), result.get("readAt")
    limitation = (
        "Openings it publishes through its job board, as read on that day; a posting is "
        "an intention to hire, not a hire."
    )
    functions: dict[str, int] = {}
    countries: dict[str, int] = {}
    for job in jobs:
        function = function_of(str(job.get("department") or "").strip() or None)
        functions[function] = functions.get(function, 0) + 1
        country = _country(job)
        if country:
            countries[country] = countries.get(country, 0) + 1
    out: list[dict[str, object]] = [
        {
            "kind": "OPERATING_SIGNAL",
            "code": "OPEN_POSITIONS",
            "statement": str(len(jobs)),
            "epistemicState": "DECLARED",
            "sourceUrl": url or source_page,
            "excerpt": "; ".join(str(j["title"]) for j in jobs[:5])[:240] or None,
            "observedAt": read_at,
            "detail": {
                "count": len(jobs),
                "vendor": vendor,
                "functions": dict(sorted(functions.items(), key=lambda kv: -kv[1])[:12]),
                "countries": dict(sorted(countries.items(), key=lambda kv: -kv[1])),
                "titles": [str(j["title"])[:120] for j in jobs[:15]],
                "instrument": JOB_BOARDS_VERSION,
                "limitation": limitation,
            },
        }
    ]
    if countries:
        out.append(
            {
                "kind": "DECLARED_LOCATION",
                "code": "HIRING_IN_COUNTRIES",
                "statement": ", ".join(sorted(countries)),
                "epistemicState": "DECLARED",
                "sourceUrl": url or source_page,
                "excerpt": None,
                "observedAt": read_at,
                "detail": {
                    "countries": countries,
                    "basis": "OPEN_POSITIONS",
                    "instrument": JOB_BOARDS_VERSION,
                    "limitation": "Countries of the positions it is hiring for: an operating "
                    "presence or an intention to have one there.",
                },
            }
        )
    return out


def boards_on(pages: Sequence[Any]) -> list[tuple[str, str]]:
    """Distinct job boards found on the pages read (links and embeds)."""
    found: list[tuple[str, str]] = []
    for page in pages:
        signals = getattr(page, "signals", {}) or {}
        for raw in signals.get("jobBoards") or []:
            if isinstance(raw, str) and ":" in raw:
                vendor, token = raw.split(":", 1)
                if (vendor, token) not in found:
                    found.append((vendor, token))
    return found[:3]
