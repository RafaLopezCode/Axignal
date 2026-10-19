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

from application.first_observation.registry_ids import registry_identifiers
from application.press.mentions import mentions, normalized_name, search_terms
from application.web_research.money import reported_revenue

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

#: "Revenue" in the languages the observatory reads (spec 104).
REVENUE_WORDS = {
    "es": "facturación", "en": "revenue", "de": "Umsatz", "fr": "chiffre d'affaires",
    "it": "fatturato", "pt": "faturação", "nl": "omzet",
}  # fmt: skip

#: How a country's company directories name the identifier AXIGNAL can verify (check digits):
#: a page that names the organization and shows one such identifier is a potential identity.
IDENTITY_WORDS = {
    "ES": "CIF", "FR": "SIREN", "DE": "Handelsregister", "GB": '"company number"',
    "NO": "organisasjonsnummer",
}  # fmt: skip

#: Hosts whose pages are a platform's own profiles or app store listings, never a third-party
#: mention (play.google.com listed Holded's own app, 2026-10-18).
SOCIAL_LABELS = frozenset({
    "facebook", "instagram", "twitter", "x", "linkedin", "youtube", "tiktok", "pinterest",
    "threads", "wikipedia", "wikidata", "google", "apple",
})  # fmt: skip
#: Legal boilerplate names every brand it lists (a privacy policy named Vitaldent, 2026-10-18):
#: it says nothing about the organization.
_BOILERPLATE_PATH = re.compile(
    r"privacy|privacidad|privacite|privacidade|datenschutz|cookie|aviso-legal|legal-notice|"
    r"mentions-legales|impressum|terms|condiciones|conditions|/legal",
    re.IGNORECASE,
)
#: Public review platforms (registrable label): their pages are reviews, told apart.
REVIEW_LABELS = frozenset({
    "trustpilot", "tripadvisor", "glassdoor", "indeed", "kununu", "ocu", "yelp", "sluurpy",
    "feefo", "trustedshops", "avis-verifies", "sitejabber", "opiniones-verificadas",
    "provenexpert", "thefork", "eltenedor", "productreview", "reclameaqui", "reviews",
    "ekomi", "judge", "verified-reviews", "comparably",
})  # fmt: skip
#: Patent databases: an invention is not its sector's context (patsnap pages reached the
#: ventilation and solar clients' context, 2026-10-19).
PATENT_LABELS = frozenset({"patsnap", "freepatentsonline", "patentimages", "espacenet", "lens"})
_PATENT_HOSTS = frozenset({"patents.google.com", "worldwide.espacenet.com", "patentscope.wipo.int"})
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
    #: Where it is registered (ISO alpha-2), for its legal identity; None when unknown.
    country: str | None = None
    #: The activity terms are AXIGNAL's English label, not the website's own words.
    activity_from_label: bool = False

    @property
    def key(self) -> str:
        return (
            f"{self.domain}|{self.language}|{','.join(self.activity_terms)}|{self.country or ''}"
            f"|{int(self.activity_from_label)}"
        )


@dataclass(frozen=True, slots=True)
class PlannedQuery:
    purpose: str  # REPUTATION | CONTEXT
    query: str


def research_names(names: Sequence[str]) -> list[str]:
    """What a page must say to name the organization. Short single-word names (Goiko, Huel),
    too common for a press headline, are kept here: the query quotes the name and excludes
    its own website, and Jev judges the page title for another entity (spec 103)."""
    terms = search_terms(names)
    return terms or list(dict.fromkeys(n for n in map(normalized_name, names) if len(n) >= 3))


def plan(subject: ResearchSubject, *, today: date) -> tuple[PlannedQuery, ...]:
    """At most three queries: reviews, recent pages that name it, and its sector's rules."""
    terms = research_names(subject.names)
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
            # A label in English is searched as such, in any language (spec 103).
            PlannedQuery("CONTEXT", f'"{term}" regulation after:{since}')
            if subject.activity_from_label
            else PlannedQuery(
                "CONTEXT", f'"{term}" {REGULATION_WORDS[lang]} lang:{lang} after:{since}'
            )
        )
    two_years = date(today.year - 2, today.month, min(today.day, 28)).isoformat()
    out.append(
        PlannedQuery(
            "ECONOMICS",
            f'"{name}" {REVENUE_WORDS.get(lang, "revenue")} -site:{subject.domain} after:{two_years}',
        )
    )
    if subject.country in IDENTITY_WORDS:
        word = IDENTITY_WORDS[str(subject.country)]
        out.append(PlannedQuery("IDENTITY", f'"{name}" {word} -site:{subject.domain}'))
    return tuple(PlannedQuery(q.purpose, q.query[:128]) for q in out)


def _plain(name: str) -> str:
    return re.sub(r"[\"“”]", "", name).strip()


def registrable_label(host: str) -> str:
    """The name part of a host: ``velascawomen`` for ``www.velascawomen.com``."""
    labels = host.lower().removeprefix("www.").split(".")
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL:
        return labels[-3]
    return labels[-2] if len(labels) >= 2 else labels[0]


def page_key(url: str) -> str:
    """One page across its language subdomains (gl.example.com and example.com, same path)."""
    parts = urlsplit(url)
    return registrable_label(parts.hostname or "") + parts.path.rstrip("/").lower()


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
        if label in SOCIAL_LABELS or _BOILERPLATE_PATH.search(urlsplit(hit.url).path):
            continue
        if purpose == "CONTEXT" and (label in PATENT_LABELS or host in _PATENT_HOSTS):
            continue
        if purpose in {"REPUTATION", "IDENTITY", "ECONOMICS"}:
            if host == own or host.endswith("." + own):
                continue  # its own voice
            if any(b in label for b in brands) and label not in REVIEW_LABELS:
                continue  # a same-brand domain (velascawomen.com) is its own channel
        out.append(hit)
    out.sort(key=lambda h: -(h.rerank or 0.0))
    return list({page_key(h.url): h for h in reversed(out)}.values())[::-1][:MAX_PAGES_PER_QUERY]


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
    #: Company identifiers the page shows, check digits verified (identity research only).
    identifiers: tuple[tuple[str, str], ...] = ()
    #: Revenue the page reports for the organization (economics research only).
    revenue: Mapping[str, object] | None = None
    #: Why a page was not read (HTTP status or the reader's refusal), said as it is.
    reason: str | None = None
    #: The publication date the page declares (ISO), when it declares one.
    published: str | None = None

    def to_wire(self) -> dict[str, object]:
        return {
            "url": self.url, "state": self.state, "title": self.title, "excerpt": self.excerpt,
            "linksToWebsite": self.links_to_website, "readAt": self.read_at, "reason": self.reason,
            "published": self.published,
            "identifiers": [list(i) for i in self.identifiers],
            "revenue": dict(self.revenue) if self.revenue else None,
        }  # fmt: skip

    @staticmethod
    def from_wire(raw: Mapping[str, object]) -> PageCheck:
        return PageCheck(
            url=str(raw.get("url") or ""), state=str(raw.get("state") or "UNREADABLE"),
            title=str(raw.get("title") or ""),
            excerpt=str(raw["excerpt"]) if raw.get("excerpt") else None,
            links_to_website=bool(raw.get("linksToWebsite")),
            read_at=str(raw["readAt"]) if raw.get("readAt") else None,
            reason=str(raw["reason"]) if raw.get("reason") else None,
            published=str(raw["published"]) if raw.get("published") else None,
            revenue=_mapping(raw.get("revenue")),
            identifiers=tuple(
                (str(i[0]), str(i[1])) for i in raw.get("identifiers") or []  # type: ignore[attr-defined]
                if isinstance(i, list | tuple) and len(i) == 2
            ),
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
    published: str | None = None,
    require_identifier: bool = False,
    extract_revenue: bool = False,
) -> PageCheck:
    """SUPPORTED only when the page's own title or text names a needle."""
    if published is not None and published >= read_at[:10]:
        # A date on or after the day the page was read is the time it was served (review
        # platforms stamp every page with today), not when it was published: unknown.
        published = None
    named = any(mentions(title, n) for n in needles) or any(
        mentions(text[:200_000], n) for n in needles
    )
    if not named:
        return PageCheck(
            url, "NOT_SUPPORTED", title=title[:300], read_at=read_at, published=published
        )
    own = (own_domain or "").lower().removeprefix("www.")
    linked = bool(own) and any(
        (h := (urlsplit(link).hostname or "").lower().removeprefix("www.")) == own
        or h.endswith("." + own)
        for link in links
    )
    excerpt = excerpt_around(text, needles) or excerpt_around(title, needles)
    identifiers: tuple[tuple[str, str], ...] = ()
    if require_identifier:
        # One company's page: exactly one or two verified identifiers (a list of companies,
        # with many, says nothing about which one is this organization).
        found = registry_identifiers(f"{title}\n{text[:200_000]}", limit=4)
        if not 1 <= len(found) <= 2:
            return PageCheck(
                url, "NOT_SUPPORTED", title=title[:300], read_at=read_at, published=published
            )
        identifiers = tuple(found)
        value = (
            found[0][1].split(" ")[-1].lower() if found[0][0] == "DE_HR" else found[0][1].lower()
        )
        excerpt = excerpt_around(text, [value]) or excerpt
    revenue: dict[str, object] | None = None
    if extract_revenue:
        # The figure must be reported in the same sentence that names it (spec 104).
        found_revenue = reported_revenue(
            f"{title}. {text}", needles, current_year=int(read_at[:4] or 0)
        )
        if found_revenue is None:
            return PageCheck(
                url, "NOT_SUPPORTED", title=title[:300], read_at=read_at, published=published
            )
        revenue = {"value": found_revenue.value, "currency": found_revenue.currency,
                   "year": found_revenue.year}  # fmt: skip
        excerpt = found_revenue.excerpt
    return PageCheck(
        url, "SUPPORTED", title=title[:300], excerpt=excerpt, links_to_website=linked,
        read_at=read_at, published=published, identifiers=identifiers, revenue=revenue,
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
    reported: list[tuple[PageCheck, str, tuple[str, str] | None, Mapping[str, object]]] = []
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
                    "publishedAt": check.published,
                    "indexedDate": page.get("indexedDate"),
                    **basis,
                },
            })  # fmt: skip
        elif purpose == "IDENTITY" and check.identifiers:
            about = attribution(check.title) if attribution is not None and check.title else None
            if about is not None and about[0] == "ANOTHER_ENTITY":
                continue
            if any(d["code"] == "IDENTIFIER_IN_DIRECTORY" for d in out):
                continue  # one directory identity is enough to show
            scheme, value = check.identifiers[0]
            out.append({
                "kind": "IDENTITY_HINT",
                "code": "IDENTIFIER_IN_DIRECTORY",
                "statement": value,
                **common,
                "detail": {
                    "scheme": scheme,
                    "value": value,
                    "outlet": outlet,
                    "attributionBy": about[1] if about is not None else None,
                    **basis,
                    "limitation": "A third-party directory shows this identifier on a page that "
                    "names the organization; only an official register admits an identity.",
                },
            })  # fmt: skip
        elif purpose == "ECONOMICS" and check.revenue:
            about = attribution(check.title) if attribution is not None and check.title else None
            if about is not None and about[0] == "ANOTHER_ENTITY":
                continue
            reported.append((check, outlet, about, page))
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
                    "publishedAt": check.published,
                    "indexedDate": page.get("indexedDate"),
                    **basis,
                    "limitation": "A page about its activity and the rules that frame it; "
                    "whether and how it applies to this organization is not assessed. "
                    "Not legal advice.",
                },
            })  # fmt: skip
    if reported:
        # The most recent year reported; one figure, never a sum or an average of pages.
        check, outlet, about, page = max(
            reported, key=lambda r: int(str((r[0].revenue or {}).get("year") or 0))
        )
        revenue = check.revenue or {}
        out.append({
            "kind": "ECONOMIC_FACT",
            "code": "REPORTED:revenue",
            "statement": f"{revenue.get('value')} {revenue.get('currency')}",
            "sourceUrl": check.url,
            "excerpt": check.excerpt,
            "observedAt": check.read_at,
            "epistemicState": "POTENTIAL",
            "detail": {
                "fact": "revenue",
                "value": revenue.get("value"),
                "unit": revenue.get("currency"),
                "year": str(revenue.get("year")) if revenue.get("year") else None,
                "source": outlet,
                "sourceKind": "THIRD_PARTY_REPORT",
                "attributionBy": about[1] if about is not None else None,
                "reportsConsidered": len(reported),
                "publishedAt": check.published,
                **basis,
                "limitation": "Revenue a third-party page reports for the organization, read "
                "from its own text; not an official account, and possibly rounded or outdated.",
            },
        })  # fmt: skip
    if withheld and out:
        for d in out:
            if d["kind"] == "MENTION":
                d["detail"]["withheldAsAnotherEntity"] = withheld  # type: ignore[index]
    return out[:MAX_SHOWN]


def _mapping(value: object) -> dict[str, object] | None:
    return {str(k): v for k, v in value.items()} if isinstance(value, Mapping) else None
