"""First Observation: cheapest-first, bounded, explainable (spec 063, ADR-0091).

L0 memory (world site reading, judgment memory) → L1 deterministic (robots, parse,
lexicon, schema.org, places) → L2 cheap fetch (homepage, then at most N pages only
while activity or location is UNKNOWN) → L3 one semantic batch when it can change the
outcome → L4 routed demand research when an adopted source covers a coded capability
in an attention scope. Luna is never used here. Nothing here writes canonical state.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import GovernedObservation
from application.first_observation.activity import (
    ActivityFinding,
    SemanticReading,
    declared_scopes,
    deterministic_activity,
    interpret_activity,
    plan_activity_batch,
    to_capabilities,
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
from application.first_observation.geography import area_jurisdiction
from application.first_observation.policy import FirstObservationPolicy, next_due
from application.first_observation.research import ResearchPlan, plan_research
from application.first_observation.site import (
    READER_VERSION,
    PageReading,
    RobotsReading,
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
from application.semantic_layer.cascade import SemanticCascade
from domain.xignal import XignalEpistemicState

_HTML = re.compile(r"^\s*(<!doctype html|<html|<head|<body|<meta|<title|<!--)", re.I)
_CHARSET = re.compile(rb"charset=[\"']?([A-Za-z0-9_\-]+)", re.I)
_DEFAULT_ROLES = frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES})
SYSTEM_ONE_EVALUATOR = "typesafe-system-one"


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


class SiteFetchPort(Protocol):
    def fetch(self, url: str, *, slot: str) -> FetchedResource: ...


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
        self, target: AttentionTarget, plan: ResearchPlan, *, now: datetime
    ) -> DemandOutcome: ...


class FocusSeedPort(Protocol):
    def seed(
        self, target: AttentionTarget, pages: Sequence[PageReading], *, now: datetime
    ) -> Mapping[str, str]:
        """Append readable pages under the Organization subject; page url → observation id."""


def origin_of(website: str) -> str:
    parts = urlsplit(website if "://" in website else "https://" + website)
    return f"{parts.scheme or 'https'}://{(parts.hostname or '').lower()}"


def _decode(resource: FetchedResource) -> str:
    body = resource.body or b""
    charset = None
    if resource.content_type and "charset=" in resource.content_type.lower():
        charset = resource.content_type.lower().split("charset=", 1)[1].split(";")[0].strip()
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
    ) -> None:
        self._fetcher = fetcher
        self._sites = sites
        self._research = research
        self._seeds = seeds
        self._cascade_factory = cascade_factory
        self._clock = clock
        self.policy = policy or FirstObservationPolicy()

    # ---- L0-L2: the website, world level ----------------------------------------
    def _fetch(self, url: str, slot: str, ledger: RunLedger) -> FetchedResource:
        resource = self._fetcher.fetch(url, slot=slot)
        ledger.http_requests += max(1, resource.requests)
        ledger.http_bytes += len(resource.body or b"")
        return resource

    def _page(self, resource: FetchedResource) -> PageReading | None:
        if resource.failure is not None or resource.status != 200 or resource.body is None:
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

    def read_site(self, website: str, now: datetime, ledger: RunLedger) -> SiteReading:
        policy = self.policy
        origin = origin_of(website)
        known = self._sites.site(origin)
        if (
            known is not None
            and known.failure is None
            and known.pages
            and now - known.observed_at <= policy.site_reuse_for
        ):
            ledger.site_reuse_hits += 1
            ledger.requests_avoided += 1 + len(known.pages)
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
            if fetched.failure is None and fetched.status == 200 and fetched.body is not None:
                robots = RobotsReading(_decode(fetched)[:65536], fetched.observed_at)
            elif fetched.status is not None and 400 <= fetched.status < 500:
                robots = RobotsReading(None, fetched.observed_at)  # none published (RFC 9309)
            else:
                return self._failed(origin, now, None, "ROBOTS_UNAVAILABLE", ledger)
        target = website if "://" in website else "https://" + website
        if not robots.allows(target):
            return self._failed(origin, now, robots, "ROBOTS_DISALLOWED", ledger)
        home = self._page(self._fetch(target, "website", ledger))
        if home is None:
            return self._failed(origin, now, robots, "HOMEPAGE_UNAVAILABLE", ledger)
        pages = [home]
        streak = 0
        if (
            known is not None
            and known.pages
            and known.pages[0].content_fingerprint == (home.content_fingerprint)
        ):
            pages += list(known.pages[1:])
            streak = known.unchanged_streak + 1
            ledger.requests_avoided += len(known.pages) - 1
            ledger.decide("UNCHANGED:HOMEPAGE:EXTRA_PAGES_REUSED")
        else:
            needs = policy.needs(
                activity_known=bool(deterministic_activity([home])),
                location_known=bool(declared_scopes([home]) or home.areas_served),
            )
            if not needs:
                ledger.decide("SKIPPED:EXTRA_PAGES:ACTIVITY_AND_LOCATION_EVIDENCED")
            links = rank_information_links(home, needs, limit=policy.max_extra_pages)
            if needs and not links:
                ledger.decide("SKIPPED:EXTRA_PAGES:NO_INFORMATION_LINK")
            for url, need in links:
                if ledger.http_requests >= policy.max_site_requests:
                    ledger.decide("STOPPED:SITE_REQUEST_BUDGET")
                    break
                if not robots.allows(url):
                    ledger.decide(f"SKIPPED:ROBOTS:{need}")
                    continue
                page = self._page(self._fetch(url, "site-page", ledger))
                if page is not None:
                    pages.append(page)
                    ledger.decide(f"FETCHED:{need}")
        reading = SiteReading(origin, now, robots, tuple(pages), None, streak)
        self._sites.save_site(reading)
        return reading

    def _failed(
        self,
        origin: str,
        now: datetime,
        robots: RobotsReading | None,
        failure: str,
        ledger: RunLedger,
    ) -> SiteReading:
        ledger.decide(f"STOPPED:{failure}")
        reading = SiteReading(origin, now, robots, (), failure)
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
    ) -> SemanticReading | None:
        plan = plan_activity_batch(origin, pages, known_scopes=scopes, deterministic=deterministic)
        if plan is None:
            ledger.decide("SKIPPED:SEMANTIC:DETERMINISTIC_SUFFICIENT")
            return None
        cascade = self._cascade_factory()
        if cascade is None:
            ledger.decide("SKIPPED:SEMANTIC:LAYER_DISABLED")
            return None
        outcome = cascade.run([plan.batch], now=now)[plan.batch.batch_id]
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
        ledger.decide("RAN:SEMANTIC:" + ",".join(q.question_id for q in plan.batch.questions))
        return interpret_activity(plan, outcome, pages, model=cascade.judge.model)

    # ---- the whole First Observation ---------------------------------------------------
    def observe(self, target: AttentionTarget) -> FirstProof:
        started = time.monotonic()
        now = self._clock()
        ledger = RunLedger()
        identity = self._identity_discoveries(target)
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
        reading = self.read_site(target.website, now, ledger)
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
        pages = reading.pages
        deterministic = deterministic_activity(pages)
        premises = declared_scopes(pages)
        areas = [
            (page, area, code)
            for page in pages
            for area in page.areas_served
            if (code := area_jurisdiction(area.name, area.nuts)) is not None
        ]
        semantic = self._semantic(
            reading.origin, pages, [*premises, *(c for _p, _a, c in areas)], deterministic,
            now, ledger,
        )  # fmt: skip
        findings = (*deterministic, *(() if semantic is None else semantic.findings))
        # Attention widens, never narrows on a judgment: a false rejection loses demand.
        roles = _DEFAULT_ROLES | (
            semantic.roles if semantic is not None and semantic.roles else frozenset()
        )
        scope_codes: dict[str, TaxonomyCode] = {c.code: c for c in premises}
        scope_codes.update({c.code: c for _p, _a, c in areas})
        if semantic is not None and not scope_codes:
            scope_codes.update({place.code: place for place, _u, _l in semantic.located})
        scopes = tuple(
            MarketScope(code, roles, XignalEpistemicState.POTENTIAL)
            for code in scope_codes.values()
        )
        subject = target.organization_id or f"attention:{target.target_ref}"
        if target.kind is TargetKind.FOCUS:
            observation_ids = dict(self._seeds.seed(target, pages, now=now))
        else:
            observation_ids = {
                page.url: f"site:{reading.origin}:{page.content_fingerprint[:24]}" for page in pages
            }
        capabilities = to_capabilities(findings, observation_ids, pages)
        discoveries: list[Discovery] = [*self._site_discoveries(reading, semantic)]
        discoveries += [self._activity(f) for f in findings]
        discoveries += self._web_representation(reading, findings)
        discoveries += identity
        demand = self._demand(
            target, subject, capabilities, scopes, pages, observation_ids, now, ledger,
            has_activity=bool(findings),
        )  # fmt: skip
        discoveries += demand
        if semantic is not None and semantic.operating is False:
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
            DiscoveryKind.IDENTITY_HINT,
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
        self, reading: SiteReading, semantic: SemanticReading | None
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
                {"pagesRead": len(reading.pages)},
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
        for page in reading.pages:
            for address in page.addresses:
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
            for area in page.areas_served:
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
            for identifier in page.identifiers:
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
            for name in page.legal_names:
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

    @staticmethod
    def _web_representation(
        reading: SiteReading, findings: Sequence[ActivityFinding]
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
                    "Its activity is evidenced in prose, but no service or product is "
                    "declared as structured data.",
                    "Search and generative surfaces that rely on structured data may not "
                    "connect this organization to what it offers. Not a measured ranking.",
                )
            )
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
        out = [
            unknown(
                f"NO_GOVERNED_DEMAND_SOURCE:{market}",
                f"No governed demand source is adopted for {market} yet. That is not an "
                "absence of demand.",
                {"jurisdiction": market, "reason": reason},
            )
            for market, reason in plan.gaps
            if reason in {"NO_ADOPTED_SOURCE", "NO_KNOWN_SOURCE"}
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
        outcome = self._research.research(target, plan, now=now)
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
    ) -> FirstProof:
        ledger.elapsed_ms = int((time.monotonic() - started) * 1000)
        return FirstProof(
            target=target,
            state=state,
            ready=ready,
            discoveries=discoveries,
            attention_scopes=tuple(
                (s.geography.code, tuple(sorted(r.value for r in s.roles))) for s in scopes
            ),
            capabilities=tuple(_capability_wire(c) for c in capabilities),
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
        )


def _capability_wire(capability: CapabilityHypothesis) -> dict[str, object]:
    basis = capability.basis[0]
    return {
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
