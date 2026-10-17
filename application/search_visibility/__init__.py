"""Search visibility measured: where an organization ranks for the searches of its activity.

A measurement, declared as such (MASTER §54): the instrument (a search API that permits it,
with its own independent index), the conditions (the exact keywords, country, language and
result depth), the date and its uncertainty. It is that engine's ranking, not what every
person sees on Google, which personalizes results and forbids automated queries in its
robots.txt (AXIGNAL never scrapes it). Every keyword carries a link to run the same search
on Google, so anyone can see it for themselves.

Keywords are never asked of anyone: they come from the words the organization's own website
uses for its activity, in its language, plus its country (spec 091, CTO 2026-10-17).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

INSTRUMENT_VERSION = "search-rank.v1"
#: Results read per keyword: a ranking deeper than two pages says little to a buyer.
DEPTH = 20
MAX_KEYWORDS = 3

#: Country names as searched in each country's language (keywords read naturally).
_COUNTRY = {
    "ES": "España", "MX": "México", "AR": "Argentina", "CO": "Colombia", "CL": "Chile",
    "PE": "Perú", "FR": "France", "BE": "Belgique", "DE": "Deutschland", "AT": "Österreich",
    "CH": "Schweiz", "IT": "Italia", "PT": "Portugal", "BR": "Brasil", "GB": "UK",
    "IE": "Ireland", "US": "USA", "CA": "Canada", "AU": "Australia", "NL": "Nederland",
}  # fmt: skip
_LANGUAGE = {
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "CL": "es", "PE": "es", "FR": "fr",
    "BE": "fr", "DE": "de", "AT": "de", "CH": "de", "IT": "it", "PT": "pt", "BR": "pt",
    "NL": "nl",
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class SearchSubject:
    name: str
    domain: str
    #: The activity in the website's own words (lexicon terms its text uses), best first.
    terms: tuple[str, ...]
    country: str  # ISO 3166-1 alpha-2
    #: The language its website declares (its searches are in it), else its country's.
    language: str

    @property
    def key(self) -> str:
        parts = (self.domain, ",".join(self.terms), self.country.upper(), self.language)
        return "|".join((*parts, INSTRUMENT_VERSION))


def language_for(country: str, declared: str | None) -> str:
    """The website's declared language when known, else its country's main one."""
    return (declared or "").split("-")[0].lower() or _LANGUAGE.get(country.upper(), "en")


def keywords(subject: SearchSubject) -> tuple[str, ...]:
    """Up to three searches a buyer would type: the activity, then with the country."""
    # The country is added in its own language only ("abono orgánico España", never
    # "organic fertiliser España"): a mixed query is not one a buyer types.
    same = _LANGUAGE.get(subject.country.upper(), "en") == subject.language
    place = _COUNTRY.get(subject.country.upper()) if same else None
    out: list[str] = []
    for term in subject.terms[:2]:
        out.append(term)
        if place and len(out) < MAX_KEYWORDS:
            out.append(f"{term} {place}")
    return tuple(dict.fromkeys(out))[:MAX_KEYWORDS]


def google_url(keyword: str, subject: SearchSubject) -> str:
    """The same search on Google, for a person to see it; AXIGNAL never fetches it."""
    return "https://www.google.com/search?" + urlencode(
        {"q": keyword, "hl": subject.language, "gl": subject.country.lower()}
    )


def _host(url: str) -> str | None:
    host = (urlsplit(url).hostname or "").casefold().removeprefix("www.")
    return host or None


def _is_subject(host: str, domain: str) -> bool:
    bare = domain.casefold().removeprefix("www.")
    return host == bare or host.endswith("." + bare)


def terms_from_activity(excerpt: str, candidates: Sequence[str]) -> tuple[str, ...]:
    """The lexicon terms its own text uses, in the order they appear (its own words)."""
    folded = _fold(excerpt)
    found = [(folded.find(_fold(t)), t) for t in candidates if _fold(t) and _fold(t) in folded]
    return tuple(t for _i, t in sorted(found))


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def evaluate(
    subject: SearchSubject, results: Sequence[Sequence[Mapping[str, object]]]
) -> dict[str, object]:
    """Per keyword: its position (or None beyond the depth read) and who ranks instead."""
    rows: list[dict[str, object]] = []
    for keyword, found in zip(keywords(subject), results, strict=False):
        hosts = [h for item in found if (h := _host(str(item.get("url") or "")))]
        position = next((i for i, h in enumerate(hosts, 1) if _is_subject(h, subject.domain)), None)
        others = [h for h in dict.fromkeys(hosts) if not _is_subject(h, subject.domain)][:10]
        rows.append({"keyword": keyword, "position": position, "results": len(hosts),
                     "ranksInstead": others, "googleUrl": google_url(keyword, subject)})  # fmt: skip
    positions = [int(str(r["position"])) for r in rows if r.get("position")]
    rivals = Counter(
        h for r in rows for h in (r["ranksInstead"] if isinstance(r["ranksInstead"], list) else [])
    )
    return {
        "keywords": rows,
        "keywordsMeasured": len(rows),
        "ranked": len(positions),
        "top10": sum(1 for p in positions if p <= 10),
        "averagePosition": round(sum(positions) / len(positions), 1) if positions else None,
        "rankingInstead": [[host, n] for host, n in rivals.most_common(10)],
    }


def search_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    """SEARCH_VISIBILITY discoveries from one stored measurement."""
    result = measurement.get("result")
    if not isinstance(result, Mapping) or not result.get("keywordsMeasured"):
        return []
    rows = [r for r in result.get("keywords") or [] if isinstance(r, Mapping)]
    ranked, measured = int(result.get("ranked") or 0), int(result.get("keywordsMeasured") or 0)
    return [
        {
            "kind": "SEARCH_VISIBILITY",
            "code": "SEARCH_RANKS_MEASURED" if ranked else "SEARCH_NOT_RANKED",
            "statement": f"{ranked}/{measured}",
            "epistemicState": "OBSERVED",
            "sourceUrl": None,
            "excerpt": None,
            "observedAt": str(measurement.get("measuredAt") or observed_at),
            "detail": {
                "instrument": measurement.get("instrument"),
                "conditions": {
                    "keywords": [r.get("keyword") for r in rows],
                    "country": measurement.get("country"),
                    "language": measurement.get("language"),
                    "depth": DEPTH,
                },
                "measuredAt": measurement.get("measuredAt"),
                "sample": f"{measured} searches, top {DEPTH} results each",
                "uncertainty": "That engine's ranking on that date and place; results vary "
                "by engine, person, place and day. Not what every person sees on Google.",
                "averagePosition": result.get("averagePosition"),
                "top10": result.get("top10"),
                "rankingInstead": result.get("rankingInstead"),
                "rows": [dict(r) for r in rows],
                "notEndorsement": True,
            },
        }
    ]


def clean_terms(terms: Sequence[str]) -> tuple[str, ...]:
    """Search-ready terms: trimmed, no duplicates, no single short words."""
    out = [re.sub(r"\s+", " ", t).strip() for t in terms]
    return tuple(dict.fromkeys(t for t in out if len(t) >= 4))
