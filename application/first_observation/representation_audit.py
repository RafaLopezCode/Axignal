"""Public web representation audit: search findability, AI-answer readiness, sharing.

What this instrument measures, and only that: the organization's own public website as
read by this First Observation (robots.txt, the pages read, the sitemap and llms.txt when
published). Every check states its status, the value observed, where it was observed and
why it matters. It is not a ranking, a traffic estimate or a measurement of what search
engines or generative systems answer: those need their own instruments and stay UNKNOWN
here. There is no universal score (MASTER §54): sections report counts of checks, and
attention items are ordered by a fixed impact class, never by a computed number.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from application.first_observation.site import PageReading, RobotsReading

AUDIT_VERSION = "representation-audit.v1"

#: Crawlers whose access decides whether a site can be read for search and AI answers.
SEARCH_CRAWLERS = ("Googlebot", "Bingbot")
AI_CRAWLERS = (
    "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
    "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot",
)  # fmt: skip


class Section(StrEnum):
    SEARCH = "SEARCH_FINDABILITY"
    AI = "AI_ANSWER_READINESS"
    SHARING = "SHARING_AND_MOBILE"
    EXPERIENCE = "REAL_USER_EXPERIENCE"


#: Google's "good" thresholds for Core Web Vitals at the 75th percentile of real users.
GOOD_P75 = {
    "largest_contentful_paint": 2500.0,  # ms
    "interaction_to_next_paint": 200.0,  # ms
    "cumulative_layout_shift": 0.1,
}


class Status(StrEnum):
    PASS = "PASS"
    ATTENTION = "ATTENTION"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Impact(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


IMPACT_ORDER = {Impact.HIGH: 0, Impact.MEDIUM: 1, Impact.LOW: 2}


@dataclass(frozen=True, slots=True)
class Check:
    check_id: str
    section: Section
    status: Status
    impact: Impact
    value: object
    evidence: str | None

    def to_wire(self) -> dict[str, object]:
        return {
            "id": self.check_id,
            "section": self.section.value,
            "status": self.status.value,
            "impact": self.impact.value,
            "value": self.value,
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class SiteExtras:
    """Bounded extra readings: the first declared sitemap and /llms.txt (None = not read)."""

    sitemap_url: str | None = None
    sitemap_urls: int | None = None
    sitemap_newest: str | None = None
    llms_txt: bool | None = None


@dataclass(frozen=True, slots=True)
class RepresentationAudit:
    checks: tuple[Check, ...]
    observed_at: datetime
    pages: int

    def attention(self) -> tuple[Check, ...]:
        """Attention items, highest fixed impact class first (no computed score)."""
        items = [c for c in self.checks if c.status is Status.ATTENTION]
        return tuple(sorted(items, key=lambda c: (IMPACT_ORDER[c.impact], c.check_id)))

    def summary(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for check in self.checks:
            counts = out.setdefault(check.section.value, {s.value: 0 for s in Status})
            counts[check.status.value] += 1
        return out

    def to_wire(self) -> dict[str, object]:
        return {
            "instrument": AUDIT_VERSION,
            "observedAt": self.observed_at.isoformat(),
            "pagesRead": self.pages,
            "sections": self.summary(),
            "checks": [c.to_wire() for c in self.checks],
        }


def _signal(page: PageReading, key: str) -> object:
    return page.signals.get(key) if page.signals else None


def _int(page: PageReading, key: str) -> int:
    value = _signal(page, key)
    return value if isinstance(value, int) else 0


def _strings(page: PageReading, key: str) -> list[str]:
    value = _signal(page, key)
    return [str(v) for v in value] if isinstance(value, list | tuple) else []


def crawler_access(robots: RobotsReading | None, url: str) -> dict[str, str]:
    """ALLOWED / BLOCKED per crawler from the published robots.txt (no file: ALLOWED)."""
    if robots is None:
        return {}
    if robots.text is None:
        return {agent: "ALLOWED" for agent in (*SEARCH_CRAWLERS, *AI_CRAWLERS)}
    parser = RobotFileParser()
    parser.parse(robots.text.splitlines())
    return {
        agent: "ALLOWED" if parser.can_fetch(agent, url) else "BLOCKED"
        for agent in (*SEARCH_CRAWLERS, *AI_CRAWLERS)
    }


def audit_representation(
    pages: Sequence[PageReading],
    robots: RobotsReading | None,
    extras: SiteExtras,
    *,
    activity_found: bool,
    field: Mapping[str, object] | None = None,
) -> RepresentationAudit:
    home = pages[0]
    measured = [p for p in pages if p.signals]  # pages read by this reader version
    checks: list[Check] = []

    def add(
        check_id: str,
        section: Section,
        ok: bool | None,
        impact: Impact,
        value: object,
        evidence: str | None = home.url,
    ) -> None:
        status = Status.UNKNOWN if ok is None else Status.PASS if ok else Status.ATTENTION
        checks.append(Check(check_id, section, status, impact, value, evidence))

    # ---- search findability ----------------------------------------------------------
    access = crawler_access(robots, home.url)
    blocked_search = [a for a in SEARCH_CRAWLERS if access.get(a) == "BLOCKED"]
    add("ROBOTS_TXT_PUBLISHED", Section.SEARCH,
        None if robots is None else robots.text is not None, Impact.LOW,
        robots is not None and robots.text is not None)  # fmt: skip
    add("SEARCH_CRAWLERS_ALLOWED", Section.SEARCH,
        None if not access else not blocked_search, Impact.HIGH, blocked_search or "ALL")  # fmt: skip
    noindex_pages = [p.url for p in pages if "noindex" in (p.meta_robots or "").lower()]
    add("NO_NOINDEX_ON_READ_PAGES", Section.SEARCH, not noindex_pages, Impact.HIGH,
        noindex_pages or "NONE", noindex_pages[0] if noindex_pages else home.url)  # fmt: skip
    sitemaps = () if robots is None else robots.sitemaps()
    add("SITEMAP_DECLARED", Section.SEARCH, None if robots is None else bool(sitemaps),
        Impact.MEDIUM, len(sitemaps))  # fmt: skip
    if extras.sitemap_url is not None:
        add("SITEMAP_READABLE", Section.SEARCH,
            None if extras.sitemap_urls is None else extras.sitemap_urls > 0, Impact.MEDIUM,
            {"urls": extras.sitemap_urls, "newestLastmod": extras.sitemap_newest},
            extras.sitemap_url)  # fmt: skip
    canonical = home.canonical
    canonical_ok = None
    if canonical is not None:
        canonical_ok = (urlsplit(canonical).hostname or "").removeprefix("www.") == (
            urlsplit(home.url).hostname or ""
        ).removeprefix("www.")
    add("HOMEPAGE_CANONICAL_SAME_SITE", Section.SEARCH,
        False if canonical is None else canonical_ok, Impact.MEDIUM, canonical or "ABSENT")  # fmt: skip
    titles = [p.title for p in pages if p.title]
    bad_titles = [p.url for p in pages if not 15 <= len(p.title) <= 65]
    add("TITLES_PRESENT_AND_SIZED", Section.SEARCH, not bad_titles, Impact.HIGH,
        {"pages": len(pages), "outOfRange": len(bad_titles), "homepage": home.title or None},
        bad_titles[0] if bad_titles else home.url)  # fmt: skip
    duplicates = len(titles) - len(set(titles))
    if len(pages) > 1:
        add("TITLES_DISTINCT", Section.SEARCH, duplicates == 0, Impact.MEDIUM, duplicates)
    bad_descriptions = [p.url for p in pages if not 50 <= len(p.description) <= 170]
    add("DESCRIPTIONS_PRESENT_AND_SIZED", Section.SEARCH, not bad_descriptions, Impact.MEDIUM,
        {"pages": len(pages), "outOfRange": len(bad_descriptions)},
        bad_descriptions[0] if bad_descriptions else home.url)  # fmt: skip
    if measured:
        bad_h1 = [p.url for p in measured if _signal(p, "h1Count") != 1]
        add("ONE_H1_PER_PAGE", Section.SEARCH, not bad_h1, Impact.MEDIUM,
            {str(p.url): _signal(p, "h1Count") for p in measured},
            bad_h1[0] if bad_h1 else home.url)  # fmt: skip
        add("HTTPS", Section.SEARCH, all(_signal(p, "https") for p in measured), Impact.HIGH,
            all(_signal(p, "https") for p in measured))  # fmt: skip
    add("LANGUAGE_DECLARED", Section.SEARCH, bool(home.language), Impact.LOW,
        home.language or "ABSENT")  # fmt: skip
    if home.alternate_languages:
        add("HREFLANG_X_DEFAULT", Section.SEARCH, bool(_signal(home, "xDefault")), Impact.LOW,
            sorted(home.alternate_languages)[:12])  # fmt: skip

    # ---- AI-answer readiness (GEO) ------------------------------------------------------
    blocked_ai = [a for a in AI_CRAWLERS if access.get(a) == "BLOCKED"]
    add("AI_CRAWLERS_ALLOWED", Section.AI, None if not access else not blocked_ai,
        Impact.HIGH, {"blocked": blocked_ai, "allowed": [a for a in AI_CRAWLERS if a not in blocked_ai]})  # fmt: skip
    types = {t for p in pages for t in p.schema_types}
    entity_fields = sorted({f for p in measured for f in _strings(p, "entityFields")})
    has_entity = bool(entity_fields) or bool(
        types & {"Organization", "LocalBusiness", "Corporation", "ProfessionalService"}
    )
    add("ORGANIZATION_DECLARED", Section.AI, has_entity, Impact.HIGH, sorted(types)[:16] or "NONE")
    if has_entity and measured:
        missing = [f for f in ("name", "url", "logo", "sameAs", "address", "contactPoint")
                   if f not in entity_fields and not (f == "contactPoint" and ("telephone" in entity_fields or "email" in entity_fields))]  # fmt: skip
        add("ORGANIZATION_COMPLETE", Section.AI, not missing, Impact.MEDIUM,
            {"declared": entity_fields, "missing": missing})  # fmt: skip
    same_as = sorted({link for p in measured for link in _strings(p, "sameAs")})
    if measured:
        add("ENTITY_PROFILES_LINKED", Section.AI, len(same_as) >= 2, Impact.MEDIUM,
            [urlsplit(link).hostname for link in same_as][:8])  # fmt: skip
    offer = bool(types & {"Service", "Product", "Offer", "SoftwareApplication"}) or any(
        p.services for p in pages
    )
    add("OFFER_DECLARED", Section.AI, offer, Impact.HIGH if activity_found else Impact.MEDIUM,
        sorted(types & {"Service", "Product", "Offer", "SoftwareApplication"}) or "NONE")  # fmt: skip
    add("FAQ_OR_QA_DECLARED", Section.AI, bool(types & {"FAQPage", "QAPage"}), Impact.LOW,
        bool(types & {"FAQPage", "QAPage"}))  # fmt: skip
    errors = sum(_int(p, "jsonldErrors") for p in measured)
    if any(_int(p, "jsonldDocuments") for p in measured):
        add("STRUCTURED_DATA_PARSES", Section.AI, errors == 0, Impact.MEDIUM, errors)
    add("LLMS_TXT_PUBLISHED", Section.AI, extras.llms_txt, Impact.LOW,
        extras.llms_txt, None if extras.llms_txt is None else f"{_origin(home.url)}/llms.txt")  # fmt: skip
    words = _int(home, "words") if home.signals else None
    add("HOMEPAGE_TEXT_DEPTH", Section.AI, None if words is None else words >= 250,
        Impact.MEDIUM, words)  # fmt: skip
    add("ACTIVITY_STATED_IN_TEXT", Section.AI, activity_found, Impact.HIGH, activity_found)

    # ---- sharing and mobile -----------------------------------------------------------
    if home.signals:
        add("MOBILE_VIEWPORT", Section.SHARING, bool(_signal(home, "viewport")), Impact.HIGH,
            bool(_signal(home, "viewport")))  # fmt: skip
        og = {k: bool(_signal(home, k)) for k in ("ogTitle", "ogDescription", "ogImage")}
        add("SOCIAL_PREVIEW_TAGS", Section.SHARING, all(og.values()), Impact.MEDIUM, og)
        images = sum(_int(p, "images") for p in measured)
        missing_alt = sum(_int(p, "imagesWithoutAlt") for p in measured)
        if images:
            add("IMAGES_DESCRIBED", Section.SHARING, missing_alt <= images // 10, Impact.LOW,
                {"images": images, "withoutAlt": missing_alt})  # fmt: skip
    # ---- real-user experience (CrUX field data, 28-day window) --------------------------
    state = None if field is None else field.get("state")
    p75 = field.get("p75") if field is not None else None
    for metric, check_id, impact in (
        ("largest_contentful_paint", "LOADING_SPEED_REAL_USERS", Impact.HIGH),
        ("interaction_to_next_paint", "RESPONSIVENESS_REAL_USERS", Impact.MEDIUM),
        ("cumulative_layout_shift", "VISUAL_STABILITY_REAL_USERS", Impact.MEDIUM),
    ):
        value = p75.get(metric) if isinstance(p75, Mapping) else None
        ok = (
            None
            if state != "MEASURED" or not isinstance(value, int | float)
            else value <= GOOD_P75[metric]
        )
        add(check_id, Section.EXPERIENCE, ok, impact,
            {"p75": value, "goodAtMost": GOOD_P75[metric], "state": state or "NOT_MEASURED",
             "period": None if field is None else field.get("period")})  # fmt: skip
    return RepresentationAudit(tuple(checks), home.observed_at, len(pages))


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def parse_sitemap(body: bytes) -> tuple[int, str | None]:
    """(URL entries, newest lastmod) of a sitemap or sitemap index; bounded, no network."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(body[:5_000_000])
    count, newest = 0, None
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "loc":
            count += 1
        elif tag == "lastmod" and element.text:
            value = element.text.strip()[:25]
            newest = value if newest is None or value > newest else newest
    return count, newest
