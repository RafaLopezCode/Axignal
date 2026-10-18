"""Governed web research: a search index proposes pages, AXIGNAL reads and verifies them (spec 098).

A web search API answers a query with candidate pages (title, URL, a relevance score and a
snippet the provider wrote). None of that is evidence: the provider's summary is never
shown or cited. Every candidate is read by AXIGNAL's own governed reader (robots.txt
honoured, bounded GETs, no authentication, no anti-bot bypass) and kept only when the page
itself supports it:

* Reputation: a third-party page (never its own domain, a same-brand domain or a social
  profile) whose text names the organization. Review platforms are told apart from other
  pages. A page that names it is a mention, not an endorsement (MASTER §54); whether it is
  about *this* organization is judged by Jev on the page title (spec 085, the safe
  direction: another entity is withheld) and stays POTENTIAL.
* Context: a page about its activity and the rules that frame it (sector, regulation),
  shared by every organization with the same activity and language.

Deterministic Python decides what is shown; the search provider is replaceable behind the
:class:`WebSearch` port, and the research is off unless its key is mounted.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol
from urllib.parse import urlsplit

from application.press.mentions import mentions, normalized_name, search_terms

#: The provider's own relevance score (0-3); below it a candidate is not read at all.
MIN_RERANK = 0.8
MAX_PAGES_PER_QUERY = 4
MAX_SHOWN = 12
EXCERPT_CHARS = 240

#: "Reviews" / "regulation" in the languages the observatory reads.
REVIEW_WORDS = {
    "es": "opiniones", "en": "reviews", "de": "Bewertungen", "fr": "avis",
    "it": "recensioni", "pt": "opiniões", "nl": "reviews",
}  # fmt: skip
REGULATION_WORDS = {
    "es": "normativa", "en": "regulation", "de": "Verordnung", "fr": "réglementation",
    "it": "normativa", "pt": "regulamentação", "nl": "regelgeving",
}  # fmt: skip

#: Hosts whose pages are a platform's own profiles, never a third-party mention.
SOCIAL_LABELS = frozenset({
    "facebook", "instagram", "twitter", "x", "linkedin", "youtube", "tiktok", "pinterest",
    "threads", "wikipedia", "wikidata",
})  # fmt: skip
#: Public review platforms (registrable label): their pages are reviews, told apart.
REVIEW_LABELS = frozenset({
    "trustpilot", "tripadvisor", "glassdoor", "indeed", "kununu", "ocu", "yelp", "sluurpy",
    "feefo", "trustedshops", "avis-verifies", "sitejabber", "opiniones-verificadas",
    "provenexpert", "thefork", "eltenedor", "productreview", "reclameaqui", "reviews",
    "ekomi", "judge", "verified-reviews", "comparably",
})  # fmt: skip
_SECOND_LEVEL = frozenset({"co", "com", "org", "net", "gov", "gob", "ac", "edu"})


@dataclass(frozen=True, slots=True)
class WebHit:
    """One candidate page as the search index returned it (not evidence)."""

    url: str
    title: str
    site_name: str | None
    rerank: float | None
    indexed_date: str | None  # the index's date, kept as reported

    def to_wire(self) -> dict[str, object]:
        return {
            "url": self.url, "title": self.title, "siteName": self.site_name,
            "rerank": self.rerank, "indexedDate": self.indexed_date,
        }  # fmt: skip

    @staticmethod
    def from_wire(raw: Mapping[str, object]) -> WebHit:
        rerank = raw.get("rerank")
        return WebHit(
            url=str(raw.get("url") or ""),
            title=str(raw.get("title") or ""),
            site_name=str(raw["siteName"]) if raw.get("siteName") else None,
            rerank=float(rerank) if isinstance(rerank, int | float) else None,
            indexed_date=str(raw["indexedDate"]) if raw.get("indexedDate") else None,
        )


class WebSearch(Protocol):
    instrument: str

    def search(self, query: str, *, count: int) -> Sequence[WebHit]: ...


@dataclass(frozen=True, slots=True)
class ResearchSubject:
    """Who is researched: its names, own website, language and the activity in its words."""

    names: tuple[str, ...]
    domain: str
    language: str
    activity_terms: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.domain}|{self.language}|{','.join(self.activity_terms)}"


@dataclass(frozen=True, slots=True)
class PlannedQuery:
    purpose: str  # REPUTATION | CONTEXT
    query: str


def plan(subject: ResearchSubject, *, today: date) -> tuple[PlannedQuery, ...]:
    """At most three queries: reviews, recent pages that name it, and its sector's rules."""
    terms = search_terms(subject.names)
    if not terms or not subject.domain:
        return ()
    name = max(subject.names, key=len) if len(terms) > 1 else subject.names[0]
    name = _plain(name)
    lang = subject.language if subject.language in REVIEW_WORDS else "en"
    since = date(today.year - 1, today.month, min(today.day, 28)).isoformat()
    out = [
        PlannedQuery("REPUTATION", f'"{name}" {REVIEW_WORDS[lang]} -site:{subject.domain}'),
        PlannedQuery("REPUTATION", f'"{name}" -site:{subject.domain} after:{since}'),
    ]
    if subject.activity_terms:
        term = subject.activity_terms[0]
        out.append(
            PlannedQuery("CONTEXT", f'"{term}" {REGULATION_WORDS[lang]} lang:{lang} after:{since}')
        )
    return tuple(PlannedQuery(q.purpose, q.query[:128]) for q in out)


def _plain(name: str) -> str:
    return re.sub(r"[\"“”]", "", name).strip()


def registrable_label(host: str) -> str:
    """The name part of a host: ``velascawomen`` for ``www.velascawomen.com``."""
    labels = host.lower().removeprefix("www.").split(".")
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL:
        return labels[-3]
    return labels[-2] if len(labels) >= 2 else labels[0]


def _brand_tokens(names: Sequence[str], domain: str) -> set[str]:
    tokens = {registrable_label(domain)} if domain else set()
    for name in names:
        squashed = normalized_name(name).replace(" ", "")
        if len(squashed) >= 4:
            tokens.add(squashed)
    return {t for t in tokens if len(t) >= 4}


def candidates(hits: Sequence[WebHit], subject: ResearchSubject, *, purpose: str) -> list[WebHit]:
    """Pages worth reading: relevant enough, third-party, and not a social profile."""
    own = subject.domain.lower().removeprefix("www.")
    brands = _brand_tokens(subject.names, own)
    out: list[WebHit] = []
    for hit in hits:
        host = (urlsplit(hit.url).hostname or "").lower().removeprefix("www.")
        if not host or urlsplit(hit.url).scheme not in {"http", "https"}:
            continue
        if hit.rerank is not None and hit.rerank < MIN_RERANK:
            continue
        label = registrable_label(host)
        if label in SOCIAL_LABELS:
            continue
        if purpose == "REPUTATION":
            if host == own or host.endswith("." + own):
                continue  # its own voice
            if any(b in label for b in brands) and label not in REVIEW_LABELS:
                continue  # a same-brand domain (velascawomen.com) is its own channel
        out.append(hit)
    out.sort(key=lambda h: -(h.rerank or 0.0))
    return list({h.url: h for h in out}.values())[:MAX_PAGES_PER_QUERY]


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def excerpt_around(text: str, needles: Sequence[str]) -> str | None:
    """The sentence-sized window of the page's own text where a (folded) needle first appears."""
    pieces: list[str] = []
    index: list[int] = []
    for i, char in enumerate(text[:200_000]):
        folded = _fold(char)
        pieces.append(folded)
        index.extend([i] * len(folded))
    haystack = "".join(pieces)
    for needle in needles:
        match = re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", haystack)
        if match:
            return _window(text, index[match.start()])
    return None


def _window(text: str, at: int) -> str:
    start = max(0, at - EXCERPT_CHARS // 2)
    end = min(len(text), start + EXCERPT_CHARS)
    snippet = " ".join(text[start:end].split())
    return ("…" if start else "") + snippet + ("…" if end < len(text) else "")


@dataclass(frozen=True, slots=True)
class PageCheck:
    """What AXIGNAL's own reading of a candidate page established (or why it could not)."""

    url: str
    state: str  # SUPPORTED | NOT_SUPPORTED | UNREADABLE | ROBOTS_DISALLOWED
    title: str = ""
    excerpt: str | None = None
    links_to_website: bool = False
    read_at: str | None = None

    def to_wire(self) -> dict[str, object]:
        return {
            "url": self.url, "state": self.state, "title": self.title, "excerpt": self.excerpt,
            "linksToWebsite": self.links_to_website, "readAt": self.read_at,
        }  # fmt: skip

    @staticmethod
    def from_wire(raw: Mapping[str, object]) -> PageCheck:
        return PageCheck(
            url=str(raw.get("url") or ""), state=str(raw.get("state") or "UNREADABLE"),
            title=str(raw.get("title") or ""),
            excerpt=str(raw["excerpt"]) if raw.get("excerpt") else None,
            links_to_website=bool(raw.get("linksToWebsite")),
            read_at=str(raw["readAt"]) if raw.get("readAt") else None,
        )  # fmt: skip


def check_page(
    url: str,
    *,
    title: str,
    text: str,
    links: Sequence[str],
    needles: Sequence[str],
    own_domain: str | None,
    read_at: str,
) -> PageCheck:
    """SUPPORTED only when the page's own title or text names a needle."""
    named = any(mentions(title, n) for n in needles) or any(
        mentions(text[:200_000], n) for n in needles
    )
    if not named:
        return PageCheck(url, "NOT_SUPPORTED", title=title[:300], read_at=read_at)
    own = (own_domain or "").lower().removeprefix("www.")
    linked = bool(own) and any(
        (h := (urlsplit(link).hostname or "").lower().removeprefix("www.")) == own
        or h.endswith("." + own)
        for link in links
    )
    excerpt = excerpt_around(text, needles) or excerpt_around(title, needles)
    return PageCheck(
        url, "SUPPORTED", title=title[:300], excerpt=excerpt, links_to_website=linked,
        read_at=read_at,
    )  # fmt: skip


def research_discoveries(
    result: Mapping[str, object],
    *,
    own_domain: str,
    attribution: Callable[[str], tuple[str, str] | None] | None = None,
) -> list[dict[str, object]]:
    """Verified pages as findings, always POTENTIAL, each with its page and excerpt."""
    raw = result.get("pages")
    pages = [p for p in raw if isinstance(p, Mapping)] if isinstance(raw, list) else []
    instrument = result.get("instrument")
    basis = {
        "instrument": instrument,
        "researchedAt": result.get("researchedAt"),
        "method": "A web search index proposed the page; AXIGNAL read it itself and kept it "
        "only because its own text supports the finding",
        "notEndorsement": True,
    }
    out: list[dict[str, object]] = []
    withheld = 0
    for page in pages:
        check = PageCheck.from_wire(page)
        if check.state != "SUPPORTED":
            continue
        purpose = str(page.get("purpose") or "")
        host = (urlsplit(check.url).hostname or "").lower().removeprefix("www.")
        outlet = str(page.get("siteName") or host)
        common = {
            "sourceUrl": check.url,
            "excerpt": check.excerpt,
            "observedAt": check.read_at,
            "epistemicState": "POTENTIAL",
        }
        if purpose == "REPUTATION":
            about = attribution(check.title) if attribution is not None and check.title else None
            if about is not None and about[0] == "ANOTHER_ENTITY":
                withheld += 1
                continue
            review = registrable_label(host) in REVIEW_LABELS
            out.append({
                "kind": "MENTION",
                "code": "REVIEW_PAGE" if review else "WEB_MENTION",
                "statement": check.title or host,
                **common,
                "detail": {
                    "outlet": outlet,
                    "linksToItsWebsite": check.links_to_website,
                    "attribution": "The page names the organization; that it is about this "
                    "organization is not verified."
                    if about is None
                    else "The page names the organization and was judged to be about it "
                    "(non-authoritative judgment).",
                    **({"attributionBy": about[1]} if about is not None else {}),
                    "indexedDate": page.get("indexedDate"),
                    **basis,
                },
            })  # fmt: skip
        elif purpose == "CONTEXT":
            out.append({
                "kind": "CONTEXT_SIGNAL",
                "code": "WEB_SECTOR_SOURCE",
                "statement": check.title or host,
                **common,
                "detail": {
                    "outlet": outlet,
                    "aboutSector": True,
                    "notAboutThisOrganization": True,
                    "indexedDate": page.get("indexedDate"),
                    **basis,
                    "limitation": "A page about its activity and the rules that frame it; "
                    "whether and how it applies to this organization is not assessed. "
                    "Not legal advice.",
                },
            })  # fmt: skip
    if withheld and out:
        for d in out:
            if d["kind"] == "MENTION":
                d["detail"]["withheldAsAnotherEntity"] = withheld  # type: ignore[index]
    return out[:MAX_SHOWN]
