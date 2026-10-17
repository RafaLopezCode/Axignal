"""First Observation: cheapest-first, bounded, explainable (spec 063, ADR-0091).

L0 memory (world site reading, judgment memory) → L1 deterministic (robots, parse,
lexicon, schema.org, places) → L2 cheap fetch (homepage, then at most N pages only
while activity or location is UNKNOWN) → L3 one semantic batch when it can change the
outcome → L4 routed demand research when an adopted source covers a coded capability
in an attention scope. Luna is never used here. Nothing here writes canonical state.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlencode, urlsplit

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import GovernedObservation
from application.first_observation.activity import (
    ActivityFinding,
    ActivityMethod,
    SemanticReading,
    declared_scopes,
    deterministic_activity,
    interpret_activity,
    plan_activity_batch,
    prefer_specific_routing,
    to_capabilities,
)
from application.first_observation.activity_verification import (
    ACTIVITY_OFFERED,
    compose,
    interpret_verification,
    plan_verification,
)
from application.first_observation.contracts import (
    AttentionTarget,
    CostBasis,
    Discovery,
    DiscoveryKind,
    FirstProof,
    IdentityLink,
    ObservationState,
    RunLedger,
    SiteReading,
    TargetKind,
)
from application.first_observation.country_evidence import country_evidence
from application.first_observation.geography import area_jurisdiction, jurisdiction
from application.first_observation.policy import FirstObservationPolicy, next_due
from application.first_observation.registry_ids import REGISTER_SCHEMES
from application.first_observation.representation_audit import (
    AUDIT_VERSION,
    SiteExtras,
    audit_representation,
    parse_sitemap,
)
from application.first_observation.research import ResearchPlan, plan_research
from application.first_observation.rights import (
    NO_RIGHTS,
    ContentRights,
    ContentRightsPolicy,
    NoContentRights,
)
from application.first_observation.site import (
    READER_VERSION,
    PageReading,
    RobotsReading,
    language_entry_link,
    rank_information_links,
    read_page,
)
from application.first_observation.vocabularies import SCHEMA_TYPE_SECTIONS
from application.observation_intelligence.contracts import (
    CapabilityHypothesis,
    MarketRole,
    MarketScope,
    TaxonomyCode,
)
from application.own_site import OWN_SITE_VERSION, logo_walls, own_site_discoveries
from application.own_site.wall_roles import interpret_walls, wall_batch, walls
from application.semantic_layer.cascade import SemanticCascade
from domain.xignal import XignalEpistemicState

_HTML = re.compile(r"^\s*(<!doctype html|<html|<head|<body|<meta|<title|<!--)", re.I)
_CHARSET = re.compile(rb"charset=[\"']?([A-Za-z0-9_\-]+)", re.I)
_DEFAULT_ROLES = frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES})
SYSTEM_ONE_EVALUATOR = "typesafe-system-one"


#: The site's TLS certificate could not be verified; verification is never relaxed.
TLS_NOT_VERIFIED = "TLS_CERTIFICATE_NOT_VERIFIED"


#: Logo-wall roles judged by the evaluator (spec 083) and the model that judged them.
JudgedWalls = tuple[dict[tuple[str, str], str | None], str | None]


class FieldPerformance(Protocol):
    """Real-user performance of an origin (CrUX by default); replaceable."""

    def measure(self, origin: str) -> Mapping[str, object]: ...


class ReverseGeocoder(Protocol):
    """A point to its country, region and place (replaceable; OSM Nominatim by default)."""

    def place(self, latitude: float, longitude: float) -> Any: ...


@dataclass(frozen=True, slots=True)
class FetchedResource:
    """One governed GET (redirects included), as the sensor observed it."""

    requested_url: str
    final_url: str
    observed_at: datetime
    status: int | None
    content_type: str | None
    body: bytes | None
    content_fingerprint: str | None
    artifact_ref: str | None
    requests: int
    failure: str | None = None
    #: Where a refused cross-domain redirect pointed (not fetched).
    redirected_to: str | None = None


class SiteFetchPort(Protocol):
    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> FetchedResource:
        """One governed GET; the raw body is kept only when ``retain_body`` (rights)."""


class SiteReadingStore(Protocol):
    def site(self, origin: str) -> SiteReading | None: ...

    def save_site(self, reading: SiteReading) -> None: ...


@dataclass(frozen=True, slots=True)
class DemandOutcome:
    executed: bool
    candidates: tuple[Mapping[str, object], ...] = ()
    requests: int = 0
    cache_hits: int = 0
    stop_reason: str | None = None


class DemandResearchPort(Protocol):
    def research(
        self, target: AttentionTarget, plan: ResearchPlan, *, now: datetime, canonical: bool
    ) -> DemandOutcome:
        """``canonical``: publish through the Focus projection (registry-verified website
        with governed content rights); otherwise a tenant-private loop."""


class FocusSeedPort(Protocol):
    def seed(
        self,
        target: AttentionTarget,
        pages: Sequence[PageReading],
        *,
        now: datetime,
        rights: ContentRights,
    ) -> Mapping[str, str]:
        """Append readable pages under the Organization subject; page url → observation id."""


#: How old an archived homepage may be to stand in for an unreadable live one.
ARCHIVE_MAX_AGE = timedelta(days=180)

_SECOND_LEVEL = frozenset({"co", "com", "org", "net", "ac", "gov", "gob", "edu"})


def brand_label(host: str) -> str:
    """The registrable name of a host: ``impression`` for ``www.impression.co.uk``."""
    parts = host.lower().removeprefix("www.").split(".")
    if len(parts) > 2 and parts[-2] in _SECOND_LEVEL:
        parts = parts[:-1]
    return parts[-2] if len(parts) >= 2 else parts[0]


def same_brand(origin: str, target: str | None) -> bool:
    """A redirect to the same brand under another domain (``impression.co.uk`` to
    ``impressiondigital.com``, ``alan.com`` to ``alan.eu``): one name prefixes the other."""
    if not target:
        return False
    a = brand_label(urlsplit(origin).hostname or "")
    b = brand_label(urlsplit(target).hostname or "")
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 4 and long_.startswith(short)


def origin_of(website: str) -> str:
    parts = urlsplit(website if "://" in website else "https://" + website)
    return f"{parts.scheme or 'https'}://{(parts.hostname or '').lower()}"


def site_key(website: str) -> str:
    """World-level key of one website: origin plus the path the attention named.

    ``https://host/acme`` and ``https://host/bolt`` (hosted profiles) are different sites.
    """
    parts = urlsplit(website if "://" in website else "https://" + website)
    return origin_of(website) + (parts.path.rstrip("/") or "") + "/"


def _decode(resource: FetchedResource) -> str:
    body = resource.body or b""
    charset = None
    if resource.content_type and "charset=" in resource.content_type.lower():
        charset = resource.content_type.lower().split("charset=", 1)[1].split(";")[0].strip(" \"'")
    if charset is None and (match := _CHARSET.search(body[:2048])) is not None:
        charset = match.group(1).decode("ascii", "ignore")
    try:
        return body.decode(charset or "utf-8", errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _is_html(resource: FetchedResource, text: str) -> bool:
    content_type = (resource.content_type or "").lower()
    return "html" in content_type or (not content_type and bool(_HTML.match(text)))


class FirstObservationService:
    def __init__(
        self,
        *,
        fetcher: SiteFetchPort,
        sites: SiteReadingStore,
        research: DemandResearchPort,
        seeds: FocusSeedPort,
        cascade_factory: Callable[[], SemanticCascade | None],
        clock: Callable[[], datetime],
        policy: FirstObservationPolicy | None = None,
        rights: ContentRightsPolicy | None = None,
        geocoder: ReverseGeocoder | None = None,
        field_performance: FieldPerformance | None = None,
    ) -> None:
        self._geocoder = geocoder
        self._field_performance = field_performance
        self._rights: ContentRightsPolicy = rights or NoContentRights()
        self._fetcher = fetcher
        self._sites = sites
        self._research = research
        self._seeds = seeds
        self._cascade_factory = cascade_factory
        self._clock = clock
        self._extras_cache: dict[str, tuple[datetime, SiteExtras]] = {}
        self.policy = policy or FirstObservationPolicy()

    def content_rights(self, website: str, *, now: datetime) -> ContentRights:
        """The rights decided now; stored content is re-decided at every read and purge."""
        return self._rights.rights_for(website, now=now)

    # ---- L0-L2: the website, world level ----------------------------------------
    def _fetch(
        self, url: str, slot: str, ledger: RunLedger, *, retain_body: bool = False
    ) -> FetchedResource:
        resource = self._fetcher.fetch(url, slot=slot, retain_body=retain_body)
        ledger.http_requests += resource.requests  # requests actually sent
        ledger.http_bytes += len(resource.body or b"")
        return resource

    def _page(
        self, resource: FetchedResource, robots: RobotsReading, ledger: RunLedger
    ) -> PageReading | None:
        if resource.failure is not None or resource.status != 200 or resource.body is None:
            return None
        if not robots.allows(resource.final_url):  # a redirect may land on a disallowed path
            ledger.decide("DISCARDED:ROBOTS_AFTER_REDIRECT")
            return None
        text = _decode(resource)
        if not _is_html(resource, text):
            return None
        return read_page(
            url=resource.final_url,
            html=text,
            observed_at=resource.observed_at,
            content_fingerprint=resource.content_fingerprint or "unknown",
            artifact_ref=resource.artifact_ref,
        )

    def _archive_capture(
        self, host: str, since: str, now: datetime, ledger: RunLedger
    ) -> tuple[str, str] | None:
        """(timestamp, original URL) of the latest 200 capture: the CDX index first, its
        availability service when the index is temporarily offline."""
        index = self._fetch(
            "https://web.archive.org/cdx/search/cdx?"
            + urlencode({"url": f"{host}/", "output": "json", "filter": "statuscode:200",
                         "from": since, "limit": "-1", "fl": "timestamp,original"}),
            "archive-index", ledger,
        )  # fmt: skip
        if index.failure is None and index.status == 200 and index.body:
            try:
                rows = json.loads(index.body.decode("utf-8", "replace") or "[]")
            except ValueError:
                rows = []
            if isinstance(rows, list) and len(rows) >= 2 and isinstance(rows[-1], list):
                return str(rows[-1][0]), str(rows[-1][1])
            return None
        ledger.decide("ARCHIVE:INDEX_UNAVAILABLE")
        available = self._fetch(
            "https://archive.org/wayback/available?"
            + urlencode({"url": f"{host}/", "timestamp": now.strftime("%Y%m%d")}),
            "archive-index", ledger,
        )  # fmt: skip
        if available.failure is not None or available.status != 200 or not available.body:
            return None
        try:
            data = json.loads(available.body.decode("utf-8", "replace"))
        except ValueError:
            return None
        closest = ((data or {}).get("archived_snapshots") or {}).get("closest") or {}
        if not closest.get("available") or str(closest.get("status")) != "200":
            return None
        stamp = str(closest.get("timestamp") or "")
        original = f"https://{host}/"
        return (stamp, original) if stamp[:8] >= since else None

    def _archived_home(self, target: str, now: datetime, ledger: RunLedger) -> PageReading | None:
        """The latest Internet Archive capture (HTTP 200) of the homepage, at most
        ARCHIVE_MAX_AGE old, read as of its capture date; None when there is none."""
        host = (urlsplit(target).hostname or "").lower()
        if not host:
            return None
        since = (now - ARCHIVE_MAX_AGE).strftime("%Y%m%d")
        found = self._archive_capture(host, since, now, ledger)
        if found is None:
            ledger.decide("ARCHIVE:NO_RECENT_CAPTURE")
            return None
        stamp, original = found
        try:
            captured = datetime.strptime(stamp[:14], "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        except ValueError:
            return None
        if now - captured > ARCHIVE_MAX_AGE:
            ledger.decide("ARCHIVE:CAPTURE_TOO_OLD")
            return None
        snapshot = f"https://web.archive.org/web/{stamp}id_/{original}"
        fetched = self._fetch(snapshot, "archive", ledger)
        if fetched.failure is not None or fetched.status != 200 or fetched.body is None:
            ledger.decide("ARCHIVE:CAPTURE_UNAVAILABLE")
            return None
        text = _decode(fetched)
        if not _is_html(fetched, text):
            return None
        # Read as the organization's own page (its links resolve to its domain), dated by
        # the capture and cited through the archive.
        page = read_page(
            url=target, html=text, observed_at=captured,
            content_fingerprint=fetched.content_fingerprint or "unknown",
            artifact_ref=fetched.artifact_ref,
        )  # fmt: skip
        ledger.decide("READ:ARCHIVED_HOMEPAGE")
        return replace(
            page,
            url=snapshot,
            signals={**page.signals, "archivedAt": captured.isoformat(), "archivedFrom": target,
                     "archiveSource": "Internet Archive (Wayback Machine)"},
        )  # fmt: skip

    def read_site(
        self,
        website: str,
        now: datetime,
        ledger: RunLedger,
        rights: ContentRights | None = None,
        *,
        force_refresh: bool = False,
        redirected: bool = False,
    ) -> SiteReading:
        """The website's pages for this run; what is *kept* depends on governed rights.

        Shared content is reused only while its rights still permit it (re-decided now) and
        its retention has not expired; otherwise the stored content is purged first.
        """
        policy = self.policy
        rights = rights or NoContentRights().rights_for(website, now=now)
        origin = origin_of(website)
        key = site_key(website)
        known = self._sites.site(key)
        if known is not None and known.content_retained:
            expired = known.shared_until is not None and known.shared_until <= now
            if expired or not rights.reuse_permitted:
                ledger.decide(
                    "PURGED:SHARED_CONTENT:" + ("EXPIRED" if expired else "RIGHTS_NOT_PERMITTED")
                )
                known = known.without_content()
                self._sites.save_site(known)
        if (
            not force_refresh
            and known is not None
            and known.failure is None
            and known.content_retained
            and now - known.observed_at <= policy.site_reuse_for
            and (not policy.public_understanding or known.perception_coverage != "NOT_REQUESTED")
        ):
            ledger.site_reuse_hits += 1
            ledger.requests_avoided += 1 + len(known.pages)  # ESTIMATED counterfactual
            ledger.decide("REUSED:SITE_READING_CURRENT")
            return known
        robots = None
        if (
            known is not None
            and known.robots is not None
            and now - known.robots.observed_at <= policy.robots_reuse_for
        ):
            robots = known.robots
            ledger.requests_avoided += 1
            ledger.decide("REUSED:ROBOTS")
        else:
            fetched = self._fetch(origin + "/robots.txt", "robots", ledger)
            host = urlsplit(origin).hostname or ""
            if fetched.status is None and not host.startswith("www."):
                # The bare domain did not answer at all (TLS, DNS, timeout): many sites serve
                # only www. Same DNS domain, same organization; one more bounded request.
                alternate = f"{urlsplit(origin).scheme}://www.{host}"
                retried = self._fetch(alternate + "/robots.txt", "robots", ledger)
                if retried.status is not None:
                    ledger.decide("RETRIED:WWW_HOST")
                    origin, fetched = alternate, retried
                    parts = urlsplit(website if "://" in website else "https://" + website)
                    website = f"{alternate}{parts.path or '/'}"
            if fetched.failure is None and fetched.status == 200 and fetched.body is not None:
                robots = RobotsReading(_decode(fetched)[:512_000], fetched.observed_at)
            elif fetched.status is not None and 400 <= fetched.status < 500:
                robots = RobotsReading(None, fetched.observed_at)  # none published (RFC 9309)
            elif fetched.failure == "redirect_policy_rejected":
                if not redirected and same_brand(origin, fetched.redirected_to):
                    # The same brand under another domain: read that site once, and say so.
                    ledger.decide("FOLLOWED:SAME_BRAND_REDIRECT")
                    moved = urlsplit(str(fetched.redirected_to))
                    return self.read_site(
                        f"{moved.scheme}://{moved.netloc}/", now, ledger, rights,
                        force_refresh=force_refresh, redirected=True,
                    )  # fmt: skip
                # It sends visitors to another domain: possibly another organization, so it is
                # not followed; the subscriber is told to name that site instead.
                return self._failed(key, now, None, "REDIRECTS_TO_ANOTHER_SITE", ledger, known)
            elif fetched.failure == TLS_NOT_VERIFIED:
                return self._failed(key, now, None, TLS_NOT_VERIFIED, ledger, known)
            else:
                return self._failed(key, now, None, "ROBOTS_UNAVAILABLE", ledger, known)
        target = website if "://" in website else "https://" + website
        if not robots.allows(target):
            return self._failed(key, now, robots, "ROBOTS_DISALLOWED", ledger, None)
        # Parsed content has its own governed store; a second retained HTTP body
        # cannot be expired or revoked with that store. Do not persist raw blobs.
        retain = False
        fetched = self._fetch(target, "website", ledger, retain_body=retain)
        home = self._page(fetched, robots, ledger)
        if (
            home is None
            and fetched.failure == "redirect_policy_rejected"
            and not redirected
            and same_brand(origin, fetched.redirected_to)
        ):
            ledger.decide("FOLLOWED:SAME_BRAND_REDIRECT")
            moved = urlsplit(str(fetched.redirected_to))
            return self.read_site(
                f"{moved.scheme}://{moved.netloc}/", now, ledger, rights,
                force_refresh=force_refresh, redirected=True,
            )  # fmt: skip
        if home is None and fetched.failure != TLS_NOT_VERIFIED:
            # Its robots.txt allows reading the homepage, but the live page refused us
            # (anti-bot wall, error, timeout). A recent public archive copy is read instead,
            # dated by its capture and cited as such (ADR-0098). Never past robots.
            archived = self._archived_home(target, now, ledger)
            if archived is not None:
                reading = SiteReading(
                    key, now, robots, (archived,), None, 0, rights.shared_until(now),
                    "NOT_REQUESTED",
                )  # fmt: skip
                self._sites.save_site(
                    reading if reading.content_retained else reading.without_content()
                )
                return reading
        if home is None:
            failure = (
                TLS_NOT_VERIFIED if fetched.failure == TLS_NOT_VERIFIED else "HOMEPAGE_UNAVAILABLE"
            )
            return self._failed(key, now, robots, failure, ledger, known)
        pages = [home]
        streak = 0
        coverage = "BOUNDED_COMPLETE" if policy.public_understanding else "NOT_REQUESTED"
        if (
            known is not None
            and known.content_retained
            and known.pages
            and not policy.public_understanding
            and known.pages[0].content_fingerprint == (home.content_fingerprint)
        ):
            pages += list(known.pages[1:])
            streak = known.unchanged_streak + 1
            ledger.requests_avoided += len(known.pages) - 1
            ledger.decide("UNCHANGED:HOMEPAGE:EXTRA_PAGES_REUSED")
        else:
            needs = policy.needs(
                activity_known=bool(deterministic_activity([home])),
                # A served area ("Worldwide") is where it sells, not where it is: the
                # contact page that states where it is is still read (axignal.com, 2026-10-17).
                location_known=bool(declared_scopes([home])),
            )
            if policy.public_understanding:
                needs = tuple(dict.fromkeys(("ACTIVITY", "ABOUT", *needs)))
            if not needs:
                ledger.decide("SKIPPED:EXTRA_PAGES:ACTIVITY_AND_LOCATION_EVIDENCED")
            links = rank_information_links(home, needs, limit=policy.max_extra_pages)
            entry = language_entry_link(home) if needs and not links else None
            if entry is not None and robots.allows(entry):
                # A language or country selector: read the matching version as the home.
                landing = self._page(
                    self._fetch(entry, "site-page", ledger, retain_body=retain), robots, ledger
                )
                if landing is not None:
                    pages.append(landing)
                    ledger.decide("FETCHED:LANGUAGE_ENTRY")
                    links = rank_information_links(
                        landing, needs, limit=max(policy.max_extra_pages - 1, 0)
                    )
            if needs and not links:
                ledger.decide("SKIPPED:EXTRA_PAGES:NO_INFORMATION_LINK")
            if policy.public_understanding and len(
                rank_information_links(home, needs, limit=3)
            ) > len(links):
                coverage = "INCOMPLETE"
            for url, need in links:
                # Reserve the worst case (redirects included) before spending.
                if ledger.http_requests + policy.requests_per_fetch > policy.max_site_requests:
                    coverage = "INCOMPLETE"
                    ledger.decide("STOPPED:SITE_REQUEST_BUDGET")
                    break
                if not robots.allows(url):
                    coverage = "INCOMPLETE"
                    ledger.decide(f"SKIPPED:ROBOTS:{need}")
                    continue
                page = self._page(
                    self._fetch(url, "site-page", ledger, retain_body=retain), robots, ledger
                )
                if page is not None:
                    pages.append(page)
                    ledger.decide(f"FETCHED:{need}")
                else:
                    coverage = "INCOMPLETE"
                    ledger.decide(f"FAILED:ACQUISITION:{need}")
            # The legal notice is where the law makes a company state its register number
            # (mentions légales, Impressum, aviso legal): one more page, only when no page
            # read so far declares one, and only within the site's request budget.
            if not any(i.scheme in REGISTER_SCHEMES for p in pages for i in p.identifiers):
                legal = rank_information_links(home, ("LEGAL",), limit=1)
                read = {p.url for p in pages}
                for url, _need in legal:
                    if url in read or not robots.allows(url):
                        continue
                    if ledger.http_requests + policy.requests_per_fetch > policy.max_site_requests:
                        ledger.decide("STOPPED:SITE_REQUEST_BUDGET")
                        break
                    page = self._page(
                        self._fetch(url, "site-page", ledger, retain_body=retain), robots, ledger
                    )
                    if page is not None:
                        pages.append(page)
                        ledger.decide("FETCHED:LEGAL")
        # Who buys from it: its customers or case-studies page, one more page, only when
        # no page read so far shows a wall of clients (potential buyers, ADR-0099). Also when
        # its other pages were reused: a page already read is never fetched again.
        if not any(d.code == "CLIENT_DECLARED" for d in logo_walls(pages)):
            read = {p.url for p in pages}
            for url, _need in rank_information_links(home, ("CUSTOMERS",), limit=1):
                if url in read or not robots.allows(url):
                    continue
                if ledger.http_requests + policy.requests_per_fetch > policy.max_site_requests:
                    ledger.decide("STOPPED:SITE_REQUEST_BUDGET")
                    break
                page = self._page(
                    self._fetch(url, "site-page", ledger, retain_body=retain), robots, ledger
                )
                if page is not None:
                    pages.append(page)
                    ledger.decide("FETCHED:CUSTOMERS")
        reading = SiteReading(
            key, now, robots, tuple(pages), None, streak, rights.shared_until(now), coverage
        )
        # Without governed rights only fingerprints and robots are kept (ADR-0015).
        self._sites.save_site(reading if reading.content_retained else reading.without_content())
        if not reading.content_retained:
            ledger.decide("NOT_SHARED:CONTENT_RIGHTS_UNKNOWN")
        return reading

    def _failed(
        self,
        key: str,
        now: datetime,
        robots: RobotsReading | None,
        failure: str,
        ledger: RunLedger,
        known: SiteReading | None,
    ) -> SiteReading:
        ledger.decide(f"STOPPED:{failure}")
        reading = SiteReading(key, now, robots, (), failure)
        # A transient fault never erases a good shared reading; a robots refusal does.
        if failure == "ROBOTS_DISALLOWED" or known is None or known.failure is not None:
            self._sites.save_site(reading)
        return reading

    # ---- L3: one semantic batch, only when it can change the outcome -----------------
    def _semantic(
        self,
        origin: str,
        pages: Sequence[PageReading],
        scopes: Sequence[TaxonomyCode],
        deterministic: Sequence[ActivityFinding],
        now: datetime,
        ledger: RunLedger,
        provider_input: bool = False,
        premises_known: bool | None = None,
    ) -> tuple[tuple[ActivityFinding, ...], SemanticReading | None, JudgedWalls]:
        """Verify lexicon activities, then ask what is still unknown; one cascade, one budget.

        Returns the deterministic findings as composed by Python after verification and
        the semantic reading (None when no batch was worth asking or none could run).
        """

        cascade: SemanticCascade | None = None
        unavailable: str | None = None

        def open_cascade() -> SemanticCascade | None:
            nonlocal cascade, unavailable
            if cascade is not None or unavailable is not None:
                return cascade
            # ADR-0090 as amended 2026-10-16 (CTO: public data): the activity batches carry
            # public website text (``public_text``: contact data and sentences about people
            # removed, legal pages not sent), page kinds and anonymous page ids.
            ledger.decide(
                "SEMANTIC_INPUT:PUBLIC_TEXT" + ("" if provider_input else ":NO_SITE_CONTENT_RIGHTS")
            )
            try:
                cascade = self._cascade_factory()
            except Exception as error:  # a missing provider never costs the deterministic proof
                unavailable = f"FAILED:{type(error).__name__}"
                ledger.decide(f"SKIPPED:SEMANTIC:{unavailable}")
                return None
            if cascade is None:
                unavailable = "LAYER_DISABLED"
                ledger.decide("SKIPPED:SEMANTIC:LAYER_DISABLED")
            return cascade

        ran: list[str] = []  # one ledger line per batch run: "RAN:SEMANTIC:<question ids>"
        lexical = [f for f in deterministic if f.method is ActivityMethod.LEXICON]
        if lexical and not self.policy.activity_verification:
            ledger.decide("SKIPPED:ACTIVITY_VERIFICATION:DISABLED")
        verify = self.policy.activity_verification
        requests = plan_verification(origin, pages, deterministic) if verify else ()
        if requests:
            outcomes = None
            judge = open_cascade()
            if judge is not None:
                try:
                    outcomes = judge.run([r.batch for r in requests], now=now)
                    ran.append(ACTIVITY_OFFERED.question_id)
                except Exception as error:
                    unavailable = f"FAILED:{type(error).__name__}"
                    ledger.decide(f"SKIPPED:SEMANTIC:{unavailable}")
            verifications = interpret_verification(
                requests, outcomes, unavailable=unavailable or "NO_JUDGMENT"
            )
            for verification in verifications:
                ledger.decide(verification.decision)
                ledger.activity_verifications.append(verification.to_wire())
            deterministic = compose(deterministic, verifications)
        elif lexical:
            deterministic = compose(deterministic, ())
        reading = None
        plan = plan_activity_batch(origin, pages, known_scopes=scopes, deterministic=deterministic,
                                   premises_known=premises_known)  # fmt: skip
        if plan is None:
            ledger.decide("SKIPPED:SEMANTIC:DETERMINISTIC_SUFFICIENT")
        elif (judge := open_cascade()) is not None:
            try:
                outcome = judge.run([plan.batch], now=now)[plan.batch.batch_id]
            except Exception as error:
                ledger.decide(f"SKIPPED:SEMANTIC:FAILED:{type(error).__name__}")
            else:
                ran.append(",".join(q.question_id for q in plan.batch.questions))
                reading = interpret_activity(plan, outcome, pages, model=judge.judge.model)
        # Spec 083: what the organizations on each logo wall are to it (clients, partners,
        # or neither), judged from the heading and the names; the vocabulary otherwise.
        judged_walls: dict[tuple[str, str], str | None] = {}
        wall_model: str | None = None
        own_names = [n for page in pages for n in (*page.names, *page.legal_names)]
        candidates = walls(pages, own_names)
        batch = wall_batch(candidates)
        if batch is not None and (judge := open_cascade()) is not None:
            try:
                walled = judge.run([batch], now=now)[batch.batch_id]
            except Exception as error:
                ledger.decide(f"SKIPPED:SEMANTIC:WALLS:FAILED:{type(error).__name__}")
            else:
                ran.append("wall_role")
                judged_walls = interpret_walls(candidates, walled)
                wall_model = judge.judge.model
        if cascade is not None and ran:
            self._account(cascade, ledger, ran)
        return tuple(deterministic), reading, (judged_walls, wall_model)

    @staticmethod
    def _account(cascade: SemanticCascade, ledger: RunLedger, ran: Sequence[str]) -> None:
        wire = cascade.ledger.to_wire()
        lines = wire["lines"]
        assert isinstance(lines, list)
        usd = None
        unknown_tokens = False
        for line in lines:
            if line["evaluator"] == cascade.judge.name:
                ledger.jev_calls += int(line["calls"])
                ledger.jev_input_tokens += int(line["inputTokens"])
                unknown_tokens = unknown_tokens or bool(line["unknownTokenCalls"])
                usd = line["usd"] if not line["unknownCostCalls"] else None
            else:
                ledger.luna_calls += int(line["calls"])
        ledger.jev_memory_hits += int(str(wire["memoryHits"]))
        ledger.jev_tokens_basis = CostBasis.ESTIMATED if unknown_tokens else CostBasis.MEASURED
        ledger.jev_usd = usd
        ledger.jev_usd_basis = CostBasis.VENDOR_PUBLISHED if usd is not None else CostBasis.UNKNOWN
        for questions in ran:
            ledger.decide(f"RAN:SEMANTIC:{questions}")

    # ---- the whole First Observation ---------------------------------------------------
    def observe(self, target: AttentionTarget, *, force_refresh: bool = False) -> FirstProof:
        started = time.monotonic()
        now = self._clock()
        ledger = RunLedger()
        identity = self._identity_discoveries(target)
        if target.identity_link is IdentityLink.WEBSITE_OF_ANOTHER_ORGANIZATION:
            ledger.decide("STOPPED:WEBSITE_OF_ANOTHER_ORGANIZATION")
            unknown = Discovery(
                DiscoveryKind.SIGNIFICANT_UNKNOWN,
                "WEBSITE_OF_ANOTHER_ORGANIZATION",
                "A registry records this website for a different organization; it is not "
                "observed as this one.",
                XignalEpistemicState.UNKNOWN.value,
                target.website,
                None,
                None,
            )
            return self._proof(
                target, ObservationState.NO_PUBLIC_WEBSITE, (unknown,), ledger, started, now,
                site=None, activity_known=False,
            )  # fmt: skip
        if target.website is None:
            ledger.decide("STOPPED:NO_PUBLIC_WEBSITE")
            unknown = Discovery(
                DiscoveryKind.SIGNIFICANT_UNKNOWN,
                "NO_PUBLIC_WEBSITE",
                "No public website to observe was given or recorded by a registry.",
                XignalEpistemicState.UNKNOWN.value,
                None,
                None,
                None,
            )
            return self._proof(
                target, ObservationState.NO_PUBLIC_WEBSITE, (unknown, *identity), ledger,
                started, now, site=None, activity_known=False,
            )  # fmt: skip
        rights = self._rights.rights_for(target.website, now=now)
        reading = self.read_site(target.website, now, ledger, rights, force_refresh=force_refresh)
        if reading.failure is not None or not reading.pages:
            unknown = Discovery(
                DiscoveryKind.SIGNIFICANT_UNKNOWN,
                reading.failure or "NO_READABLE_PAGE",
                "The public website could not be observed under its robots rules and our "
                "bounded request policy. Nothing is concluded from that.",
                XignalEpistemicState.UNKNOWN.value,
                reading.origin,
                None,
                reading.observed_at,
            )
            return self._proof(
                target, ObservationState.SOURCE_UNAVAILABLE, (unknown, *identity), ledger,
                started, now, site=reading, activity_known=False, unavailable=True,
            )  # fmt: skip
        # Evidence acquired during this run must precede its evaluation as-of.
        # Using the job start would exclude freshly admitted pages as future evidence.
        now = self._clock()
        pages = reading.pages
        deterministic = deterministic_activity(pages)
        premises = declared_scopes(pages)
        areas = [
            (page, area, code)
            for page in pages
            for area in page.areas_served
            if (code := area_jurisdiction(area.name, area.nuts)) is not None
        ]
        deterministic, semantic, judged_walls = self._semantic(
            reading.origin, pages, [*premises, *(c for _p, _a, c in areas)], deterministic,
            now, ledger, rights.provider_input, premises_known=bool(premises),
        )  # fmt: skip
        if semantic is not None and semantic.withheld:
            for withheld in semantic.withheld:
                ledger.decide(f"WITHHELD:NATURE_CONFLICT:{withheld}")
            deterministic = tuple(
                f for f in deterministic if f.activity_id not in semantic.withheld
            )
        if semantic is not None and semantic.codes and not semantic.findings:
            deterministic = tuple(
                f if f.demand_codes else replace(f, demand_codes=semantic.codes)
                for f in deterministic
            )
        findings = prefer_specific_routing(
            (*deterministic, *(() if semantic is None else semantic.findings))
        )
        # Attention widens, never narrows on a judgment: a false rejection loses demand.
        roles = _DEFAULT_ROLES | (
            semantic.roles if semantic is not None and semantic.roles else frozenset()
        )
        mapped = self._mapped_premises(pages, ledger)
        scope_codes: dict[str, TaxonomyCode] = {c.code: c for c in premises}
        # Premises the site pins on a map it publishes: declared by the organization itself.
        scope_codes.update({code.code: code for code, _d in mapped if code.code not in scope_codes})
        scope_codes.update({c.code: c for _p, _a, c in areas})
        if semantic is not None and not scope_codes:
            scope_codes.update({place.code: place for place, _u, _l in semantic.located})
        # Nothing declared: two independent signals the site publishes (domain, language
        # region, phone prefix, tax identifier, postal code beside the country) start
        # where to look. POTENTIAL attention with its signals cited, never a market.
        country = None if scope_codes else country_evidence(pages)
        if country is not None:
            scope_codes[country.scope.code] = country.scope
            ledger.decide(f"LOCATION:COUNTRY_FROM_SITE_SIGNALS:{country.country}")
        scopes = tuple(
            MarketScope(code, roles, XignalEpistemicState.POTENTIAL)
            for code in scope_codes.values()
        )
        subject = target.organization_id or f"attention:{target.target_ref}"
        # Canonical path: the registry says it is the official website AND a governed rights
        # decision permits reusing and retaining its content (ADR-0015, ADR-0091 §3).
        verified = (
            target.kind is TargetKind.FOCUS
            and target.identity_link is IdentityLink.REGISTRY_VERIFIED
            and rights.raw_retention_days > 0
        )
        if (
            target.kind is TargetKind.FOCUS
            and target.identity_link is IdentityLink.REGISTRY_VERIFIED
            and not verified
        ):
            ledger.decide("PRIVATE_PATH:CONTENT_RIGHTS_UNKNOWN")
        if verified:
            observation_ids = dict(self._seeds.seed(target, pages, now=now, rights=rights))
        else:
            observation_ids = {
                page.url: f"site:{reading.origin}:{page.content_fingerprint[:24]}" for page in pages
            }
        # A judgment chooses where to look (routing), never what is true: on the canonical
        # projection path only deterministic hypotheses may route demand (ADR-0090/0091).
        routed = [
            f for f in findings if not verified or f.method is not ActivityMethod.SEMANTIC_JUDGMENT
        ]
        capabilities = to_capabilities(routed, observation_ids, pages)
        discoveries: list[Discovery] = [*self._site_discoveries(reading, semantic, judged_walls)]
        if country is not None:
            discoveries.append(
                Discovery(
                    DiscoveryKind.DECLARED_LOCATION,
                    "COUNTRY_FROM_SITE_SIGNALS",
                    country.scope.code,
                    XignalEpistemicState.POTENTIAL.value,
                    country.signals[0].page_url,
                    None,
                    reading.pages[0].observed_at,
                    {
                        "method": "SITE_SIGNALS",
                        "signals": [
                            {"kind": sig.kind, "value": sig.value, "page": sig.page_url}
                            for sig in country.signals
                        ],
                        "limitation": "Where to start looking for demand, not its market or reach.",
                    },
                )
            )
        discoveries += [discovery for _code, discovery in mapped]
        discoveries += [self._activity(f) for f in findings]
        discoveries += self._web_representation(
            reading, findings, ledger,
            # A parked or placeholder site has no offer to be unclear about.
            unclear_offer=None
            if semantic is None or semantic.operating is False
            else semantic.judged.get("offerNatureUnclear"),
        )  # fmt: skip
        discoveries += identity
        demand = self._demand(
            target, subject, capabilities, scopes, pages, observation_ids, now, ledger,
            has_activity=bool(findings), canonical=verified,
        )  # fmt: skip
        discoveries += demand
        if semantic is not None and semantic.operating is False and not _business_signals(pages):
            discoveries.append(
                Discovery(
                    DiscoveryKind.SIGNIFICANT_UNKNOWN,
                    "NOT_AN_OPERATING_BUSINESS_SITE",
                    "The page does not read as an operating organization's website.",
                    XignalEpistemicState.POTENTIAL.value,
                    pages[0].url,
                    pages[0].title or None,
                    pages[0].observed_at,
                )
            )
        useful = {
            DiscoveryKind.ACTIVITY,
            DiscoveryKind.DECLARED_LOCATION,
            DiscoveryKind.DECLARED_SERVICE_AREA,
            DiscoveryKind.DEMAND,
        }
        ready = any(d.kind in useful for d in discoveries)
        state = (
            ObservationState.FIRST_PROOF_READY
            if findings or ready
            else ObservationState.NOT_ENOUGH_CAPABILITY_EVIDENCE
        )
        return self._proof(
            target, state, tuple(discoveries), ledger, started, now, site=reading,
            activity_known=bool(findings), scopes=scopes, capabilities=capabilities,
            judged={} if semantic is None else semantic.judged, ready=ready,
            methods={f.activity_id: f for f in findings}, rights=rights,
            contact=_published_contact(pages),
        )  # fmt: skip

    # ---- discoveries --------------------------------------------------------------------
    def _identity_discoveries(self, target: AttentionTarget) -> tuple[Discovery, ...]:
        if target.identity_link is IdentityLink.IDENTITY_PENDING:
            return (
                Discovery(
                    DiscoveryKind.SIGNIFICANT_UNKNOWN,
                    "IDENTITY_NOT_VERIFIED",
                    "No registry has attested which legal entity this is yet. What follows "
                    "describes the public website, not a verified organization.",
                    XignalEpistemicState.UNKNOWN.value,
                    None,
                    None,
                    None,
                ),
            )
        if target.identity_link is IdentityLink.SUBSCRIBER_DIRECTED:
            return (
                Discovery(
                    DiscoveryKind.SIGNIFICANT_UNKNOWN,
                    "WEBSITE_LINK_NOT_REGISTRY_VERIFIED",
                    "You directed this website to the organization; no registry records it "
                    "as the organization's official website.",
                    XignalEpistemicState.UNKNOWN.value,
                    target.website,
                    None,
                    None,
                ),
            )
        return ()

    def _site_discoveries(
        self,
        reading: SiteReading,
        semantic: SemanticReading | None,
        judged_walls: JudgedWalls = ({}, None),
    ) -> list[Discovery]:
        home = reading.pages[0]
        out = [
            Discovery(
                DiscoveryKind.PUBLIC_PRESENCE,
                "PUBLIC_WEBSITE_OBSERVED",
                home.title or reading.origin,
                XignalEpistemicState.OBSERVED.value,
                home.url,
                home.description or home.title or None,
                home.observed_at,
                # Which own-site reader ran: its signals are comparable in time only then.
                {
                    "pagesRead": len(reading.pages),
                    "ownSiteVersion": OWN_SITE_VERSION,
                    **(
                        {
                            "archivedAt": home.signals["archivedAt"],
                            "limitation": "The live website refused automated reading; this is "
                            "a public archive copy dated by its capture.",
                        }
                        if home.signals.get("archivedAt")
                        else {}
                    ),
                },
            )
        ]
        languages = sorted({x for x in (home.language, *home.alternate_languages) if x})
        if languages:
            out.append(
                Discovery(
                    DiscoveryKind.LANGUAGES,
                    "LANGUAGES_PUBLISHED",
                    ", ".join(languages),
                    XignalEpistemicState.OBSERVED.value,
                    home.url,
                    None,
                    home.observed_at,
                    {"languages": languages},
                )
            )
        declared_ids: set[tuple[str, str]] = set()
        # The same footer address or legal name on every page is one declaration.
        declared: set[tuple[str, str]] = set()
        for page in reading.pages:
            for address in page.addresses[:5]:
                if ("ADDRESS", address.label.casefold()) in declared:
                    continue
                declared.add(("ADDRESS", address.label.casefold()))
                out.append(
                    Discovery(
                        DiscoveryKind.DECLARED_LOCATION,
                        "ADDRESS_DECLARED",
                        address.label,
                        "DECLARED",
                        page.url,
                        f"schema.org address: {address.label}",
                        page.observed_at,
                        {"basis": "PREMISES"},
                    )
                )
            for area in page.areas_served[:10]:
                out.append(
                    Discovery(
                        DiscoveryKind.DECLARED_SERVICE_AREA,
                        "SERVICE_AREA_DECLARED",
                        str(area.name or area.nuts),
                        "DECLARED",
                        page.url,
                        f"schema.org areaServed: {area.name or area.nuts}",
                        page.observed_at,
                        {"basis": "STATED_SERVICE_AREA"},
                    )
                )
            for identifier in page.identifiers[:5]:
                if (identifier.scheme, identifier.value) in declared_ids:
                    continue  # the same number in every page's footer is one declaration
                declared_ids.add((identifier.scheme, identifier.value))
                out.append(
                    Discovery(
                        DiscoveryKind.IDENTITY_HINT,
                        f"IDENTIFIER_DECLARED:{identifier.scheme}",
                        f"{identifier.scheme} {identifier.value}",
                        "DECLARED",
                        page.url,
                        None,
                        page.observed_at,
                        {"admitted": False, "reason": "A website declaring itself never admits identity."},
                    )
                )  # fmt: skip
            for name in page.legal_names[:3]:
                if ("LEGAL", name.casefold()) in declared:
                    continue
                declared.add(("LEGAL", name.casefold()))
                out.append(
                    Discovery(
                        DiscoveryKind.IDENTITY_HINT,
                        "LEGAL_NAME_DECLARED",
                        name,
                        "DECLARED",
                        page.url,
                        None,
                        page.observed_at,
                        {"admitted": False},
                    )
                )
        # Technology, clients and partners shown, credentials, hiring and review profiles.
        own_names = [n for page in reading.pages for n in (*page.names, *page.legal_names)]
        out += own_site_discoveries(reading.pages, own_names, *judged_walls)
        if semantic is not None:
            for place, url, line in semantic.located:
                out.append(
                    Discovery(
                        DiscoveryKind.DECLARED_LOCATION,
                        "LOCATION_STATED_IN_TEXT",
                        place.code,
                        XignalEpistemicState.POTENTIAL.value,
                        url,
                        line,
                        home.observed_at,
                        {"method": "SEMANTIC_JUDGMENT", "basis": "TEXT_MENTION"},
                    )
                )
        return out

    def _field(self, reading: SiteReading, ledger: RunLedger) -> Mapping[str, object] | None:
        """Real-user Core Web Vitals of the origin (CrUX); None when it cannot be asked."""
        if self._field_performance is None or not reading.pages:
            return None
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(reading.pages[0].url))
        try:
            return self._field_performance.measure(origin)
        except Exception:  # unavailable: the checks stay UNKNOWN, never a failure
            ledger.decide("FAILED:FIELD_PERFORMANCE")
            return None

    def _extras(self, reading: SiteReading, ledger: RunLedger) -> SiteExtras:
        """The first declared sitemap and /llms.txt, within the site request budget."""
        policy = self.policy
        robots = reading.robots
        if robots is None or not reading.pages:
            return SiteExtras()
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(reading.pages[0].url))
        now = self._clock()
        cached = self._extras_cache.get(origin)
        if cached is not None and now - cached[0] < policy.robots_reuse_for:
            ledger.decide("REUSED:AUDIT_EXTRAS")
            return cached[1]  # public, per origin: paid once, like robots.txt
        sitemap_url = next(iter(robots.sitemaps()), None)
        sitemap_urls: int | None = None
        newest: str | None = None
        llms: bool | None = None
        for kind, url in (("sitemap", sitemap_url), ("llms", origin + "/llms.txt")):
            if url is None or not robots.allows(url):
                continue
            if ledger.http_requests + policy.requests_per_fetch > policy.max_site_requests:
                ledger.decide(f"SKIPPED:AUDIT:{kind.upper()}:BUDGET")
                continue
            fetched = self._fetch(url, "site-audit", ledger)
            if kind == "llms":
                if fetched.failure is None and fetched.status == 200 and fetched.body:
                    text = _decode(fetched)
                    llms = not _is_html(fetched, text) and bool(text.strip())
                elif fetched.status is not None and 400 <= fetched.status < 500:
                    llms = False
                continue
            if fetched.failure is None and fetched.status == 200 and fetched.body:
                try:
                    sitemap_urls, newest = parse_sitemap(fetched.body)
                except Exception:  # an unreadable sitemap is a finding, never a crash
                    sitemap_urls = 0
            elif fetched.status is not None:
                sitemap_urls = 0
        extras = SiteExtras(sitemap_url, sitemap_urls, newest, llms)
        if len(self._extras_cache) >= 2048:
            self._extras_cache.clear()
        self._extras_cache[origin] = (now, extras)
        return extras

    def _web_representation(
        self,
        reading: SiteReading,
        findings: Sequence[ActivityFinding],
        ledger: RunLedger,
        unclear_offer: str | None = None,
    ) -> list[Discovery]:
        """Public web representation as measured by this instrument: checks, not a score.

        Observed with zero extra requests from robots.txt and the pages already read.
        A gap is a POTENTIAL derived pattern (evidence of activity + an absent machine-
        readable declaration), never a claim about rankings or about cause.
        """

        home = reading.pages[0]
        types = {t for page in reading.pages for t in page.schema_types}
        organization_declared = bool(
            types & {"Organization", "LocalBusiness", "Corporation"}
            or types & set(SCHEMA_TYPE_SECTIONS)
            or any(page.names or page.legal_names for page in reading.pages)
        )
        offer_declared = bool(
            types & {"Service", "Product", "Offer", "SoftwareApplication"}
            or any(page.services for page in reading.pages)
        )
        robots = reading.robots
        noindex = "noindex" in (home.meta_robots or "").lower()
        audit = audit_representation(
            reading.pages,
            robots,
            self._extras(reading, ledger),
            activity_found=bool(findings),
            field=self._field(reading, ledger),
        )
        checks: dict[str, object] = {
            "robotsTxtPublished": robots is not None and robots.text is not None,
            "sitemapsDeclared": 0 if robots is None else len(robots.sitemaps()),
            "canonical": home.canonical,
            "homepageNoindex": noindex,
            "titlePresent": bool(home.title),
            "descriptionPresent": bool(home.description),
            "schemaTypes": sorted(types)[:24],
            "organizationDeclared": organization_declared,
            "offerDeclared": offer_declared,
            "alternateLanguages": len(home.alternate_languages),
        }
        out = [
            Discovery(
                DiscoveryKind.WEB_REPRESENTATION,
                "PUBLIC_WEB_REPRESENTATION_MEASURED",
                "Public web representation checks",
                XignalEpistemicState.OBSERVED.value,
                home.url,
                None,
                home.observed_at,
                {
                    "instrument": READER_VERSION,
                    "conditions": "robots.txt plus pages read by this First Observation",
                    "checks": checks,
                    "audit": audit.to_wire(),
                    "limitation": "Own website only; not search results, rankings or "
                    "generative answers.",
                },
            )
        ]

        def gap(code: str, statement: str, why: str) -> Discovery:
            return Discovery(
                DiscoveryKind.REPRESENTATION_GAP, code, statement,
                XignalEpistemicState.POTENTIAL.value, home.url, None, home.observed_at,
                {"whyItMatters": why, "basis": ["ACTIVITY", "WEB_REPRESENTATION"],
                 "notCausal": True},
            )  # fmt: skip

        if noindex:
            out.append(
                gap(
                    "HOMEPAGE_NOINDEX",
                    "The homepage asks search engines not to index it.",
                    "Search surfaces may not represent this site at all while it stays so.",
                )
            )
        if findings and not offer_declared:
            out.append(
                gap(
                    "OFFER_NOT_MACHINE_READABLE",
                    "On the pages read, its activity is evidenced in prose but no service "
                    "or product is declared as structured data.",
                    "Search and generative surfaces that rely on structured data may not "
                    "connect this organization to what it offers. Not a measured ranking.",
                )
            )
        if unclear_offer is not None:
            # Spec 084 (Presence): what the site communicates vs what it is. Judged from its
            # own public text; POTENTIAL and derived, never a fact about the organization.
            out.append(
                Discovery(
                    DiscoveryKind.REPRESENTATION_GAP, "OFFER_NATURE_UNCLEAR",
                    "Its website does not make clear whether it mainly sells products, "
                    "performs services or carries out works.",
                    XignalEpistemicState.POTENTIAL.value, home.url,
                    home.description or home.title or None, home.observed_at,
                    {"whyItMatters": "Visitors, search engines and AI assistants may read it as "
                     "another kind of business and connect it with demand that is not its own.",
                     "basis": ["ACTIVITY", "WEB_REPRESENTATION"], "notCausal": True,
                     "method": "SEMANTIC_JUDGMENT", "judgment": unclear_offer},
                )
            )  # fmt: skip
        covered = {"NO_NOINDEX_ON_READ_PAGES", "OFFER_DECLARED"}  # stated by the gaps above
        for check in audit.attention():
            if check.check_id in covered:
                continue
            out.append(
                Discovery(
                    DiscoveryKind.REPRESENTATION_GAP,
                    f"AUDIT:{check.check_id}",
                    check.check_id,
                    XignalEpistemicState.POTENTIAL.value,
                    check.evidence,
                    None,
                    home.observed_at,
                    {
                        "section": check.section.value,
                        "impact": check.impact.value,
                        "value": check.value,
                        "instrument": AUDIT_VERSION,
                        "basis": ["WEB_REPRESENTATION"],
                        "notCausal": True,
                    },
                )
            )
        return out

    def _mapped_premises(
        self, pages: Sequence[PageReading], ledger: RunLedger, *, limit: int = 5
    ) -> list[tuple[TaxonomyCode, Discovery]]:
        """Places of the points the site publishes (its map links/embeds, schema.org geo)."""
        if self._geocoder is None:
            return []
        points: dict[tuple[float, float], tuple[str, str]] = {}
        for page in pages:
            raw = page.signals.get("coordinates") if page.signals else None
            for item in raw if isinstance(raw, list) else []:
                if isinstance(item, list | tuple) and len(item) == 3:
                    points.setdefault((float(item[0]), float(item[1])), (str(item[2]), page.url))
        out: list[tuple[TaxonomyCode, Discovery]] = []
        for (lat, lng), (method, url) in list(points.items())[:limit]:
            try:
                place = self._geocoder.place(lat, lng)
            except Exception:  # a geocoding failure leaves the place unknown, never guessed
                ledger.decide("FAILED:GEOCODE")
                continue
            if place is None or place.country_code is None:
                continue
            region = (place.region_code or "").split("-", 1)[-1] or None
            code = jurisdiction(place.country_code, region)
            if code is None:
                continue
            label = ", ".join(x for x in (place.locality, place.region, place.country_code) if x)
            ledger.decide(f"LOCATION:MAP_POINT:{place.country_code}")
            out.append(
                (
                    code,
                    Discovery(
                        DiscoveryKind.DECLARED_LOCATION, "PREMISES_PINNED_ON_MAP", label, "DECLARED",
                        url, None, pages[0].observed_at,
                        {
                            "method": method, "latitude": lat, "longitude": lng,
                            "jurisdiction": code.code, "regionCode": place.region_code,
                            "attribution": place.attribution,
                            "limitation": "A place the organization pins on its own website; "
                            "not its whole market or reach.",
                        },
                    ),
                )
            )  # fmt: skip
        return out

    @staticmethod
    def _activity(finding: ActivityFinding) -> Discovery:
        return Discovery(
            DiscoveryKind.ACTIVITY,
            finding.activity_id,
            finding.label,
            XignalEpistemicState.POTENTIAL.value,
            finding.page_url,
            finding.excerpt,
            finding.observed_at,
            {
                "method": finding.method.value,
                "confidence": finding.confidence,
                "model": finding.model,
                **({} if finding.verification is None else {"verification": finding.verification}),
                "routingCodes": [f"{c.scheme}:{c.code}" for c in finding.demand_codes],
            },
        )

    def _demand(
        self,
        target: AttentionTarget,
        subject: str,
        capabilities: Sequence[CapabilityHypothesis],
        scopes: tuple[MarketScope, ...],
        pages: Sequence[PageReading],
        observation_ids: Mapping[str, str],
        now: datetime,
        ledger: RunLedger,
        *,
        has_activity: bool,
        canonical: bool = False,
    ) -> list[Discovery]:
        def unknown(
            code: str, statement: str, detail: Mapping[str, object] | None = None
        ) -> Discovery:
            return Discovery(
                DiscoveryKind.SIGNIFICANT_UNKNOWN, code, statement,
                XignalEpistemicState.UNKNOWN.value, None, None, None, detail or {},
            )  # fmt: skip

        if not has_activity:
            ledger.decide("SKIPPED:DEMAND:ACTIVITY_UNKNOWN")
            return [unknown("ACTIVITY_NOT_ESTABLISHED", "What it offers is not established yet from its public website.")]  # fmt: skip
        if not scopes:
            ledger.decide("SKIPPED:DEMAND:NO_ATTENTION_SCOPE")
            return [unknown("LOCATION_NOT_DECLARED", "Its website does not declare where it is or serves; we do not guess a market.")]  # fmt: skip
        observations = tuple(
            GovernedObservation(
                record=ObservationRecord(
                    observation_id=observation_ids[page.url],
                    subject_id=subject,
                    source_ref=page.url,
                    source_type="PUBLIC_WEBSITE",
                    observed_at=page.observed_at,
                    content_fingerprint=page.content_fingerprint,
                    mode=ObservationMode.DETERMINISTIC_SENSOR,
                ),
                raw_content=page.readable(),
            )
            for page in pages
            if page.url in observation_ids and page.readable()
        )
        plan = plan_research(
            xeed_id=target.target_ref,
            organization_id=subject,
            capabilities=capabilities,
            scopes=scopes,
            observations=observations,
            as_of=now,
            policy=self.policy,
        )
        if plan is None:
            ledger.decide("SKIPPED:DEMAND:NO_ROUTING_CODE")
            return [unknown("DEMAND_NOT_ROUTABLE", "Its activity has no classification a governed demand source uses yet.")]  # fmt: skip
        reasons: dict[str, set[str]] = {}
        questions: dict[str, set[str]] = {}
        for gap in plan.strategy.gaps:
            if gap.reason in {"NO_ADOPTED_SOURCE", "NO_KNOWN_SOURCE"}:
                reasons.setdefault(gap.market.code, set()).add(gap.reason)
                questions.setdefault(gap.market.code, set()).add(gap.question_id)
        out = [  # one grounded gap per market, naming the questions it leaves open
            unknown(
                f"NO_GOVERNED_DEMAND_SOURCE:{market}",
                f"Some demand questions in {market} have no governed source yet "
                f"({', '.join(sorted(questions[market]))}). That is not an absence of demand.",
                {
                    "jurisdiction": market,
                    "reasons": sorted(found),
                    "questions": sorted(questions[market]),
                },
            )
            for market, found in sorted(reasons.items())
        ]
        if not plan.strategy.actions:
            ledger.decide("SKIPPED:DEMAND:NO_ROUTABLE_SOURCE")
            if not out:
                out.append(
                    unknown(
                        "NO_ROUTABLE_DEMAND_QUESTION",
                        "No governed demand question applies to this activity and place yet.",
                    )
                )
            return out
        outcome = self._research.research(target, plan, now=now, canonical=canonical)
        ledger.source_requests += outcome.requests
        ledger.source_cache_hits += outcome.cache_hits
        ledger.requests_avoided += outcome.cache_hits
        ledger.decide(
            f"RAN:DEMAND:{len(plan.strategy.actions)}_ACTIONS:{outcome.stop_reason or 'DONE'}"
        )
        for candidate in outcome.candidates[:5]:
            out.append(
                Discovery(
                    DiscoveryKind.DEMAND,
                    "POTENTIAL_DEMAND",
                    str(candidate.get("title") or "Public demand"),
                    XignalEpistemicState.POTENTIAL.value,
                    None if candidate.get("url") is None else str(candidate.get("url")),
                    None,
                    now,
                    dict(candidate),
                )
            )
        if outcome.executed and not outcome.candidates:
            out.append(
                unknown(
                    "NO_RELEVANT_DEMAND_FOUND",
                    "The governed sources searched returned no current matching demand. "
                    "No result is not no opportunity.",
                )
            )
        return out

    def _proof(
        self,
        target: AttentionTarget,
        state: ObservationState,
        discoveries: tuple[Discovery, ...],
        ledger: RunLedger,
        started: float,
        now: datetime,
        *,
        site: SiteReading | None,
        activity_known: bool,
        unavailable: bool = False,
        scopes: tuple[MarketScope, ...] = (),
        capabilities: Sequence[CapabilityHypothesis] = (),
        judged: Mapping[str, str] | None = None,
        ready: bool = False,
        methods: Mapping[str, ActivityFinding] | None = None,
        rights: ContentRights | None = None,
        contact: Mapping[str, object] | None = None,
    ) -> FirstProof:
        understanding = None
        if self.policy.public_understanding:
            from application.first_observation.understanding import measure

            grant = rights or NO_RIGHTS
            understanding = measure(
                site,
                now=now,
                rights=grant,
                rights_for=lambda url: self._rights.rights_for(url, now=now),
                cascade_factory=self._cascade_factory,
                ledger=ledger,
                token_budget=max(0, self.policy.semantic_tokens - ledger.jev_input_tokens),
            )
        ledger.elapsed_ms = int((time.monotonic() - started) * 1000)
        return FirstProof(
            target=target,
            state=state,
            ready=ready,
            discoveries=discoveries,
            attention_scopes=tuple(
                (s.geography.code, tuple(sorted(r.value for r in s.roles))) for s in scopes
            ),
            capabilities=tuple(
                _capability_wire(c, (methods or {}).get(c.capability_id)) for c in capabilities
            ),
            site_fingerprint=None if site is None else site.fingerprint,
            ledger=ledger.to_wire(),
            judged=dict(judged or {}),
            observed_at=now,
            next_due_at=next_due(
                now,
                unchanged_streak=0 if site is None else site.unchanged_streak,
                activity_known=activity_known,
                source_unavailable=unavailable,
            ),
            retain_until=(rights or NO_RIGHTS).private_until(now),
            rights=(rights or NO_RIGHTS).to_wire(),
            understanding=understanding,
            contact=dict(contact or {}),
        )


_ORGANIZATION_TYPES = frozenset(
    {"Organization", "Corporation", "LocalBusiness", "ProfessionalService", "Store",
     "OnlineBusiness", "NGO", "EducationalOrganization"}
)  # fmt: skip


#: Where organizations keep company profiles: linking one is a business signal.
_COMPANY_PROFILE_HOSTS = ("linkedin.com", "xing.com", "kununu.com", "glassdoor.com",
                          "glassdoor.es", "crunchbase.com", "trustpilot.com")  # fmt: skip


def _business_signals(pages: Sequence[PageReading]) -> bool:
    """What an operating organization's site shows: an address, a legal name or
    identifier, a contact address, a schema.org organization, a job board, a company
    profile it links, or the business tools it runs. With any of them, a judgment
    that the page is not an operating business is not believed (2026-10-13 golden
    pass: real companies with sparse homepages were called non-operating)."""
    for page in pages:
        if page.addresses or page.legal_names or page.identifiers:
            return True
        if set(page.schema_types) & _ORGANIZATION_TYPES:
            return True
        signals = page.signals or {}
        if signals.get("emails") or signals.get("jobBoards"):
            return True
        hosts = signals.get("resourceHosts")
        if isinstance(hosts, list) and len(hosts) >= 3:
            return True
        linked = signals.get("externalLinkHosts")
        if isinstance(linked, list) and any(
            str(h).endswith(_COMPANY_PROFILE_HOSTS) for h in linked
        ):
            return True
    return False


def _published_contact(pages: Sequence[PageReading]) -> dict[str, object]:
    """Addresses the site publishes for itself and the language its homepage declares."""
    emails: list[str] = []
    for page in pages:
        held = page.signals.get("emails")
        for email in held if isinstance(held, list) else []:
            if isinstance(email, str) and email not in emails:
                emails.append(email)
    language = pages[0].language if pages else None
    return {
        "emails": emails[:10],
        "language": None if language is None else language.split("-")[0].lower()[:8],
        "page": pages[0].url if pages else None,
    }


def _capability_wire(
    capability: CapabilityHypothesis, finding: ActivityFinding | None
) -> dict[str, object]:
    basis = capability.basis[0]
    return {
        "method": None if finding is None else finding.method.value,
        "model": None if finding is None else finding.model,
        # Operator trace (never the subscriber's view): decides whether a judged activity
        # may seed where the autonomous loop looks (spec 079, CTO 2026-10-16).
        "confidence": None if finding is None else finding.confidence,
        "capabilityId": capability.capability_id,
        "label": capability.label,
        "state": capability.state.value,
        "demandCodes": [[c.scheme, c.code] for c in capability.demand_codes],
        "basis": {
            "observationId": basis.observation_id,
            "sourceRef": basis.source_ref,
            "excerpt": basis.excerpt,
            "observedAt": basis.observed_at.isoformat(),
        },
    }
