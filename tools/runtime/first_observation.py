"""Root composition of the First Observation loop (spec 063, ADR-0091). Off by default.

``AXIGNAL_FIRST_OBSERVATION_ENABLED=true`` turns subscriber attention into a durable
First Observation job: the HTTP request only validates and enqueues. A single
in-process worker (``AXIGNAL_FIRST_OBSERVATION_WORKER=thread``, the default) drains the
queue and the due re-checks; ``manual`` leaves draining to the caller (tests, preflight).
Every job re-authorizes its subscriber context before any network work.

``python -m tools.runtime.first_observation metrics --data-dir DIR`` prints runtime
economics from stored proofs (no network, no model).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

from application.context.sector import context_discoveries
from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationMemory,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.source_registry import SourceRegistryEntry
from application.economics import (
    economic_discoveries,
    register_discoveries,
    same_organization_name,
)
from application.first_observation.contracts import (
    AttentionTarget,
    IdentityLink,
    TargetKind,
)
from application.first_observation.geography import EU_MEMBERS, country_name_en
from application.first_observation.metrics import runtime_metrics
from application.first_observation.policy import FirstObservationPolicy
from application.first_observation.research import ResearchPlan
from application.first_observation.rights import (
    ContentRights,
    ContentRightsPolicy,
    NoContentRights,
    RegisteredContentRights,
)
from application.first_observation.service import (
    DemandOutcome,
    FirstObservationService,
    SiteFetchPort,
)
from application.first_observation.shared_findings import SharedFindingsPort
from application.first_observation.site import PageReading
from application.first_observation.visibility import first_proof_live_deadline, withdraw_first_proof
from application.generative_visibility.probe import ProbeSubject, geo_discoveries
from application.observation_intelligence import (
    OperationalLearning,
    SourceObservationPort,
    SourceRegistry,
)
from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.loop import OpportunityCandidate, run_observation_loop
from application.observation_runtime.replay import FindingsLedger
from application.organization_admission.locator import LocatorError, parse_locator, public_domain
from application.organization_group import group_discoveries
from application.press.mentions import press_discoveries
from application.semantic_layer.cascade import SemanticCascade
from application.subscriber_identity.runtime import Clock
from application.subscriber_portfolio.models import (
    EntitlementSnapshot,
    FocusStatus,
    PendingAttentionEntry,
    PendingStatus,
    PortfolioError,
)
from application.subscriber_projection.subscriber_runtime import SubscriberEconomicRuntime
from application.world_demand.index import (
    DemandIndexPort,
    SliceFeedPort,
    WorldDemandIngestor,
    country_of,
)
from application.world_demand.live import LiveDemandReader, apply_live_demand
from application.world_demand.relations import AwardStore, apply_public_awards
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from pipeline.economics.registries import OfficialRegisters, registers_from_env
from pipeline.economics.wikidata import WikidataEconomics
from pipeline.entity_resolution.gleif_group import GleifGroupReader
from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore
from pipeline.geo.nominatim import NominatimReverseGeocoder
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.press.sqlite_store import PressIngestor, SqlitePressIndex
from pipeline.press.sqlite_store import SqlitePressIndex as _PressIndex
from tools.runtime.field_performance import field_performance_from_env
from tools.runtime.generative_probe import (
    GenerativeProbeRunner,
    assistant_from_values,
    generative_probe_from_values,
)
from tools.runtime.sector_context import SectorContextRunner
from tools.runtime.subscriber_portfolio import SubscriberPortfolioRuntime

ENABLED_KEY = "AXIGNAL_FIRST_OBSERVATION_ENABLED"
WORKER_KEY = "AXIGNAL_FIRST_OBSERVATION_WORKER"
DAILY_JOBS_KEY = "AXIGNAL_FIRST_OBSERVATION_DAILY_JOBS"


class EntitlementReader(Protocol):
    def snapshot(self, tenant_id: TenantId) -> EntitlementSnapshot: ...


class WebsiteIndex(Protocol):
    def websites_for(self, organization_id: OrganizationId) -> tuple[str, ...]: ...

    def organization_by_domain(self, domain: str) -> OrganizationId | None: ...


@dataclass(frozen=True, slots=True)
class FirstObservationOverrides:
    """Test/preflight seams: replace only the network-facing parts."""

    enabled: bool | None = None
    worker: str | None = None
    fetcher: SiteFetchPort | None = None
    source_ports: Mapping[str, SourceObservationPort] | None = None
    cascade_factory: Callable[[], SemanticCascade | None] | None = None
    public_understanding: bool | None = None
    feeds: Mapping[str, SliceFeedPort] | None = None
    rights: ContentRightsPolicy | None = None


class FocusSeed:
    """Append readable pages under the canonical Organization subject (ADR-0091 §3)."""

    def __init__(self, memory: ObservationMemory) -> None:
        self._memory = memory

    def seed(
        self,
        target: AttentionTarget,
        pages: Sequence[PageReading],
        *,
        now: datetime,
        rights: ContentRights,
    ) -> Mapping[str, str]:
        del now
        entry = rights.entry
        if entry is None or rights.raw_retention_days <= 0 or not rights.reuse_permitted:
            raise ValueError("seeding requires a governed rights decision with retention")
        organization = target.organization_id
        if organization is None or target.identity_link is not IdentityLink.REGISTRY_VERIFIED:
            # ADR-0091 §3: only a registry-recorded website speaks for the Organization.
            raise ValueError("only a registry-verified Focus website is seeded")
        ids: dict[str, str] = {}
        for page in pages:
            content = page.readable()
            if not content:
                continue
            identity = f"{organization}|{page.url}|{page.content_fingerprint}|{page.observed_at.isoformat()}"
            observation_id = "fo:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
            self._memory.append(
                GovernedObservation(
                    record=ObservationRecord(
                        observation_id=observation_id,
                        subject_id=organization,
                        source_ref=page.url,
                        source_type="PUBLIC_WEBSITE",
                        observed_at=page.observed_at,
                        content_fingerprint=page.content_fingerprint,
                        mode=ObservationMode.DETERMINISTIC_SENSOR,
                    ),
                    raw_content=content,
                    raw_artifact_ref=page.artifact_ref,
                    reuse_authority=ObservationReuseAuthority(
                        # Authority comes from the governed registry entry, never assumed.
                        rights_status=entry.rights_status,
                        access_status=entry.access_status,
                        scope=entry.reuse_scope,
                        provenance_ref=rights.basis_ref,
                        currentness=Currentness.CURRENT,
                        applicable_subject_ids=(organization,),
                        applicable_purposes=(
                            ReusePurpose.CURRENT_STATE.value,
                            ReusePurpose.HISTORICAL_REFERENCE.value,
                        ),
                        authority_id="first-observation-public-website",
                        authority_version="1",
                        reuse_reason=(
                            "Registry-recorded official website page, observed after "
                            "robots.txt under a bounded GET policy."
                        ),
                        retention_policy_ref=entry.retention_policy.ref,
                        content_retention_days=entry.retention_policy.raw_retention_days,
                        robots_policy_ref=entry.robots_policy_ref,
                    ),
                )
            )
            ids[page.url] = observation_id
        return ids


def _candidate_wire(candidate: OpportunityCandidate) -> dict[str, object]:
    record = candidate.record
    return {
        "title": record.title,
        "buyer": record.buyer_name,
        "url": record.source_url,
        "deadline": record.deadline,
        "publishedAt": record.published_at.isoformat(),
        "market": candidate.market.code,
        "capabilityIds": list(candidate.capability_ids),
        "codes": [f"{c.scheme}:{c.code}" for c in candidate.matched_codes],
        "source": record.source_id,
        "demandForm": candidate.demand_form,
        "epistemicState": "POTENTIAL",
    }


class RuntimeDemandResearch:
    """Execute a routed research plan: the Focus projection path or a private loop."""

    def __init__(
        self,
        *,
        economic: SubscriberEconomicRuntime,
        ports: Mapping[str, SourceObservationPort],
        ledger: FindingsLedger | None,
        clock: Callable[[], datetime],
    ) -> None:
        self._economic = economic
        self._ports = ports
        self._ledger = ledger
        self._clock = clock

    def research(
        self, target: AttentionTarget, plan: ResearchPlan, *, now: datetime, canonical: bool
    ) -> DemandOutcome:
        needed = {action.source_id for action in plan.strategy.actions}
        shared: dict[str, SourceObservationPort] = {}
        for source_id, port in self._ports.items():
            if source_id in needed:
                shared[source_id] = (
                    port
                    if self._ledger is None
                    else SharedFindingsPort(port, self._ledger, clock=self._clock)
                )
        indexes = [p for p in self._ports.values() if isinstance(p, DemandIndexPort)]
        index_before = sum(p.index_hits for p in indexes)
        if canonical:  # decided once, by the service (identity link AND content rights)
            result = self._economic.execute_observation_loop(
                TrustedRequestContext(PrincipalId(target.principal_id), TenantId(target.tenant_id)),
                XeedId(target.target_ref),
                observation_context=plan.context,
                strategy=plan.strategy,
                adapters=shared,
                coverage=plan.coverage,
                learning=OperationalLearning(),
                registry=SourceRegistry(),
            )
        else:
            result = run_observation_loop(
                plan.strategy,
                plan.context,
                adapters=shared,
                coverage=plan.coverage,
                learning=OperationalLearning(),
                registry=SourceRegistry(),
            )
        # No semantic screen here: it may escalate to Luna and would delete demand the
        # sources returned. Candidates stay POTENTIAL with their routing basis.
        candidates = list(result.candidates)
        hits = sum(p.hits for p in shared.values() if isinstance(p, SharedFindingsPort))
        hits += sum(p.index_hits for p in indexes) - index_before
        live = sum(p.live_requests for p in shared.values() if isinstance(p, SharedFindingsPort))
        return DemandOutcome(
            executed=True,
            candidates=tuple(_candidate_wire(c) for c in candidates),
            requests=live if self._ledger is not None else result.requests,
            cache_hits=hits,
            stop_reason=result.stop_reason.value,
        )


def _website_and_name(locator: str | None) -> tuple[str | None, str | None]:
    if not locator:
        return None, None
    try:
        parsed = parse_locator(locator)
    except LocatorError:
        return None, None
    if parsed.domain is None:
        return None, parsed.name
    # Fetch the address the subscriber typed (host and path) when it is the same site;
    # the normalized domain is an identity key, not necessarily the served host.
    for token in locator.split():
        try:
            same = public_domain(token) == parsed.domain
        except LocatorError:
            continue
        if same:
            parts = urlsplit(token if "://" in token else "https://" + token)
            scheme = "http" if parts.scheme == "http" else "https"
            return f"{scheme}://{(parts.hostname or '').lower()}{parts.path or '/'}", parsed.name
    return f"https://{parsed.domain}/", parsed.name


def public_view(proof: Mapping[str, Any] | None, state: str | None) -> dict[str, object] | None:
    """The subscriber's view: no tenant or principal identifiers, operational authority."""
    if proof is None and state is None:
        return None
    if proof is None:
        return {"state": state, "firstProofReady": False, "discoveries": []}
    # Operational internals (cost ledger, decisions, raw judgments) stay with operators:
    # they would also reveal whether another tenant recently observed the same site.
    view = {
        k: v
        for k, v in proof.items()
        if k
        not in {"ledger", "judged", "capabilities", "siteFingerprint", "rights", "publishedContact"}
    }
    # A provider's confidence stays in the authorized trace (the stored proof): shown to a
    # subscriber it reads as a probability of truth, which it is not (ADR-0047).
    view["discoveries"] = [
        {**d, "detail": {k: v for k, v in d.get("detail", {}).items() if k != "confidence"}}
        for d in view.get("discoveries", ())
    ]
    if isinstance(view.get("publicUnderstanding"), Mapping):
        view["publicUnderstanding"] = {
            k: v for k, v in view["publicUnderstanding"].items() if k != "trace"
        }
    target = dict(view.pop("target"))
    view["target"] = {
        "kind": target["kind"],
        "website": target["website"],
        "name": target["name"],
        "identityLink": target["identityLink"],
    }
    view["state"] = state or view["state"]
    return view


def _headline(proof: Mapping[str, Any] | None) -> tuple[str | None, str | None]:
    """(statement, stable code) of the most informative discovery, for the portfolio."""
    if proof is None:
        return None, None
    for kind in ("ACTIVITY", "PUBLIC_PRESENCE"):
        for discovery in proof.get("discoveries", ()):
            if discovery.get("kind") == kind:
                return str(discovery.get("statement")), str(discovery.get("code"))
    return None, None


#: AXIGNAL's own marketing pool studies prospects as staff: no subscriber, no Focus, no
#: Organization; its proofs are read only by the pool (Admin §5.7).
MARKETING_TENANT = "staff:marketing-pool"


class FirstObservationRuntime:
    def __init__(
        self,
        *,
        store: SqliteFirstObservationStore,
        service: FirstObservationService,
        portfolio: SubscriberPortfolioRuntime,
        entitlements: EntitlementReader,
        websites: WebsiteIndex,
        clock: Clock,
        worker: str = "thread",
        daily_jobs: int = 500,
        tenant_daily_jobs: int = 20,
        ingestor: WorldDemandIngestor | None = None,
        purge_canonical_raw: Callable[[datetime], int] | None = None,
        live_demand: LiveDemandReader | None = None,
        press: tuple[PressIngestor, SqlitePressIndex] | None = None,
        awards: AwardStore | None = None,
        groups: GleifGroupReader | None = None,
        geo: GenerativeProbeRunner | None = None,
        sector_context: SectorContextRunner | None = None,
        economics: WikidataEconomics | None = None,
        registers: OfficialRegisters | None = None,
    ) -> None:
        self._registers = registers
        self._sector_context = sector_context
        self._economics = economics
        self._geo = geo
        self._press = press
        self._groups = groups
        self._awards = awards
        self._purge_canonical_raw = purge_canonical_raw
        self._live_demand = live_demand
        self.ingestor = ingestor
        self.store = store
        self.service = service
        self._portfolio = portfolio
        self._entitlements = entitlements
        self._websites = websites
        self._clock = clock
        self._worker = worker
        self._daily_jobs = daily_jobs
        self._hint = threading.local()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._start_lock = threading.Lock()
        self._tenant_daily_jobs = tenant_daily_jobs
        self.marketing_pool: Any = None
        self.awards_backfill: Any = None
        self._backfill_thread: threading.Thread | None = None

    # ---- attention (synchronous, cheap) ---------------------------------------------
    def remember_locator(self, locator: str | None) -> None:
        """The locator of the add/replace being handled on this thread (website hint)."""
        self._hint.locator = locator

    def attend_focus(self, context: TrustedRequestContext, focus_id: XeedId, key: str) -> str:
        entry = self._portfolio.store.get_authorized(context, focus_id)
        if entry is None or entry.status is not FocusStatus.ACTIVE:
            return "NOT_READY"
        organization = str(entry.xeed.organization_id)
        website, name = _website_and_name(getattr(self._hint, "locator", None))
        if website is None:
            previous = self.store.proof(str(context.tenant_id), str(focus_id))
            if previous is not None and previous["target"]["organizationId"] == organization:
                website = previous["target"]["website"]
        if website is None:
            recorded = self._websites.websites_for(OrganizationId(organization))
            website = f"https://{recorded[0]}/" if recorded else None
        domain = (
            None if website is None else (urlsplit(website).hostname or "").removeprefix("www.")
        )
        owner = None if domain is None else self._websites.organization_by_domain(domain)
        verified = owner is not None and str(owner) == organization
        if owner is not None and not verified:
            link = IdentityLink.WEBSITE_OF_ANOTHER_ORGANIZATION
        else:
            link = IdentityLink.REGISTRY_VERIFIED if verified else IdentityLink.SUBSCRIBER_DIRECTED
        target = AttentionTarget(
            tenant_id=str(context.tenant_id),
            principal_id=str(context.principal_id),
            target_ref=str(focus_id),
            kind=TargetKind.FOCUS,
            website=website,
            name=name or entry.xeed.label,
            organization_id=organization,
            identity_link=link,
        )  # fmt: skip
        return self._enqueue(target, key=f"focus:{key}")

    def attend_pending(self, context: TrustedRequestContext, *, request_ref: str) -> str:
        pending = next(
            (p for p in self._portfolio.list_pending(context) if p.idempotency_key == request_ref),
            None,
        )
        return "NOT_READY" if pending is None else self._attend(context, pending)

    def attend_pending_id(self, context: TrustedRequestContext, pending_id: str) -> str:
        pending = self._portfolio.store.get_pending_authorized(context, pending_id)
        return "NOT_READY" if pending is None else self._attend(context, pending)

    def _attend(self, context: TrustedRequestContext, pending: PendingAttentionEntry) -> str:
        if pending.status is not PendingStatus.IDENTITY_PENDING:
            return "NOT_READY"
        if not self._capacity_allows(context, pending.pending_id):
            return "CAPACITY_REQUIRED"
        website, name = _website_and_name(pending.locator)
        target = AttentionTarget(
            tenant_id=str(context.tenant_id),
            principal_id=str(context.principal_id),
            target_ref=pending.pending_id,
            kind=TargetKind.PENDING,
            website=website,
            name=name or pending.display_label,
            organization_id=None,
            identity_link=IdentityLink.IDENTITY_PENDING,
        )
        return self._enqueue(target, key=f"pending:{pending.idempotency_key}")

    def _enqueue(self, target: AttentionTarget, *, key: str) -> str:
        """One open job per target; a finished target gets a fresh job; per-tenant cap."""
        states = self.store.jobs_for(target.tenant_id, target.target_ref)
        if any(state in {"QUEUED", "RUNNING"} for state in states):
            self._kick()
            return "QUEUED"
        now = self._clock.now()
        if self.store.jobs_created_today(target.tenant_id, now) >= self._tenant_daily_jobs:
            return "BUDGET_EXHAUSTED"
        self.store.enqueue(target, key=f"{key}:{len(states)}", now=now)
        self._kick()
        return "QUEUED"

    def _capacity_allows(self, context: TrustedRequestContext, pending_id: str) -> bool:
        """Pending attention observes only inside current capacity (MASTER §31.3)."""
        snapshot = self._entitlements.snapshot(context.tenant_id)
        if (
            snapshot is None
            or snapshot.capacity is None
            or snapshot.currentness is not Currentness.CURRENT
        ):
            return False
        observed = self.store.observed_targets(str(context.tenant_id))
        if pending_id in observed:
            return True
        active = sum(
            e.status in (FocusStatus.ACTIVE, FocusStatus.PAUSED)
            for e in self._portfolio.list(context)
        )
        open_pending = {
            p.pending_id
            for p in self._portfolio.list_pending(context)
            if p.status is PendingStatus.IDENTITY_PENDING
        }
        return active + len(observed & open_pending) < snapshot.capacity

    # ---- work (asynchronous, bounded) -------------------------------------------------
    def _still_authorized(self, target: AttentionTarget) -> bool:
        if target.tenant_id == MARKETING_TENANT:
            return True  # staff attention: no subscriber authority to lose
        context = TrustedRequestContext(
            PrincipalId(target.principal_id), TenantId(target.tenant_id)
        )
        try:
            if target.kind is TargetKind.FOCUS:
                return any(
                    str(e.focus_id) == target.target_ref
                    and e.status is FocusStatus.ACTIVE
                    and str(e.xeed.organization_id) == target.organization_id
                    for e in self._portfolio.list(context)
                )
            snapshot = self._entitlements.snapshot(context.tenant_id)
            if snapshot is None or snapshot.currentness is not Currentness.CURRENT:
                return False  # pending attention observes only under current capacity
            return any(
                p.pending_id == target.target_ref and p.status is PendingStatus.IDENTITY_PENDING
                for p in self._portfolio.list_pending(context)
            )
        except PortfolioError:
            return False

    def run_next(self) -> bool:
        """Run one queued job; False when nothing is runnable now."""
        policy = self.service.policy
        now = self._clock.now()
        # The daily ceiling bounds public reads; a job with no website reads nothing and
        # must not wait a day (nor take the day's slot) only to report NO_PUBLIC_WEBSITE.
        reads_left = self.store.jobs_started_on(now.date().isoformat()) < self._daily_jobs
        job = self.store.claim(
            now=now,
            lease_seconds=policy.lease_seconds,
            max_attempts=policy.max_attempts,
            offline_only=not reads_left,
        )
        if job is None:
            return False
        if not self._still_authorized(job.target):
            self.store.fail(job, error="TARGET_NO_LONGER_AUTHORIZED", now=now, retry=False)
            return True
        try:
            proof = self.service.observe(
                job.target,
                force_refresh=(
                    policy.public_understanding
                    and self.store.proof(job.target.tenant_id, job.target.target_ref) is not None
                ),
            )
        except Exception as error:  # a failed job is retried, never a crash of the runtime
            self.store.fail(
                job,
                error=type(error).__name__,
                now=self._clock.now(),
                retry=job.attempts < policy.max_attempts,
            )
            return True
        self.store.complete(job, proof, now=self._clock.now())
        return True

    def drain(self, limit: int = 100) -> int:
        done = 0
        with self._lock:
            while done < limit and self.run_next():
                done += 1
        return done

    def ingest_demanded(self, *, max_slices: int = 10) -> int:
        """Ingest world demand slices some Focus asked for (off the First Proof path)."""
        if self.ingestor is None:
            return 0
        with self._lock:
            return len(self.ingestor.run(max_slices=max_slices))

    def judge_sector_context(self) -> int:
        """Judge queued sector contexts (shared per activity and country per day)."""
        return 0 if self._sector_context is None else self._sector_context.run()

    def _with_sector_context(self, view: dict[str, object]) -> dict[str, object]:
        """Recent headlines about its activity in its country; queues a judgment when due."""
        if self._sector_context is None:
            return view
        held = view.get("discoveries")
        discoveries = held if isinstance(held, list) else []
        activities = [
            str(d.get("code"))
            for d in discoveries
            if isinstance(d, Mapping) and d.get("kind") == "ACTIVITY" and d.get("code")
        ][:2]
        scopes = view.get("attentionScopes")
        country = None
        if isinstance(scopes, list) and scopes and isinstance(scopes[0], Mapping):
            country = country_of(TaxonomyCode("GEO", str(scopes[0].get("jurisdiction") or "")))
        if not activities or not country:
            return view
        found: list[dict[str, object]] = []
        for capability_id in activities:
            self._sector_context.request(capability_id, country)
            result = self._sector_context.latest(capability_id, country)
            if result is not None:
                found += context_discoveries(
                    result, capability_id=capability_id, country=country,
                    observed_at=str(view.get("observedAt") or ""),
                )  # fmt: skip
        if found:
            view["discoveries"] = [*discoveries, *found]
        return view

    def measure_geo(self) -> int:
        """Run queued GEO measurements (a few per tick, under the daily cap)."""
        return 0 if self._geo is None else self._geo.run()

    def _with_geo(self, view: dict[str, object]) -> dict[str, object]:
        """Show a stored GEO measurement; queue one when none is fresh (never asks inline)."""
        if self._geo is None:
            return view
        held = view.get("discoveries")
        discoveries = held if isinstance(held, list) else []
        activity = next(
            (d for d in discoveries if isinstance(d, Mapping) and d.get("kind") == "ACTIVITY"), None
        )
        target = view.get("target")
        name = target.get("name") if isinstance(target, Mapping) else None
        website = target.get("website") if isinstance(target, Mapping) else None
        scopes = view.get("attentionScopes")
        country = None
        if isinstance(scopes, list) and scopes and isinstance(scopes[0], Mapping):
            parts = str(scopes[0].get("jurisdiction") or "").split("/")
            country = parts[1] if parts and parts[0] == "EU" and len(parts) > 1 else parts[0]
        place = country_name_en(country)
        if not activity or not name or not place:
            return view
        subject = ProbeSubject(
            name=str(name),
            domain=(urlsplit(str(website)).hostname or "").removeprefix("www.") or None
            if website
            else None,
            activity=str(activity.get("statement") or "").lower(),
            place=place,
            language="en",
        )
        measurement = self._geo.measurement(subject)
        self._geo.request(subject)  # no-op while fresh or queued
        if measurement is None:
            return view
        found = geo_discoveries(measurement, observed_at=str(view.get("observedAt") or ""))
        view["discoveries"] = [*discoveries, *found]
        return view

    def ingest_press(self) -> int:
        """Read due publisher feeds into the world press index (off the First Proof path)."""
        if self._press is None:
            return 0
        return self._press[0].run()

    def purge(self) -> dict[str, int]:
        """Retention enforcement for First Observation's own stores."""
        now = self._clock.now()
        from application.first_observation.understanding import rights_deadline

        # Revoked or shortened rights purge stored quotations too, not only elapsed dates.
        result = self.store.purge(
            now=now,
            deadline=lambda report: rights_deadline(
                report, lambda url: self.service.content_rights(url, now=now)
            ),
            proof_deadline=lambda proof: first_proof_live_deadline(
                proof, lambda url: self.service.content_rights(url, now=now)
            ),
        )
        if self._purge_canonical_raw is not None:
            result["canonicalRaw"] = self._purge_canonical_raw(now)
        return result

    # ---- marketing pool (staff-only studies) ------------------------------------------
    def study(self, target_ref: str, website: str, name: str) -> str:
        """Observe a prospect's public presence once, under the pool's staff tenant."""
        target = AttentionTarget(
            tenant_id=MARKETING_TENANT,
            principal_id=MARKETING_TENANT,
            target_ref=target_ref,
            kind=TargetKind.PENDING,
            website=website,
            name=name,
            organization_id=None,
            identity_link=IdentityLink.IDENTITY_PENDING,
        )
        return self._enqueue(target, key=f"pool:{target_ref}")

    def study_result(self, target_ref: str) -> tuple[dict[str, object] | None, Mapping[str, Any]]:
        """The study as a subscriber would read it, plus the contact the site publishes."""
        context = TrustedRequestContext(PrincipalId(MARKETING_TENANT), TenantId(MARKETING_TENANT))
        proof = self.store.proof(MARKETING_TENANT, target_ref) or {}
        contact = proof.get("publishedContact")
        return self.view(context, target_ref), contact if isinstance(contact, Mapping) else {}

    def run_marketing_pool(self) -> int:
        return 0 if self.marketing_pool is None else sum(self.marketing_pool.tick().values())

    def enqueue_due(self) -> int:
        now = self._clock.now()
        created = 0
        for target in self.store.due(now=now):
            if target.tenant_id == MARKETING_TENANT:
                continue  # a prospect is studied once, never kept under observation
            created += self._enqueue(target, key=f"due:{now.date().isoformat()}") == "QUEUED"
        return created

    def start(self) -> None:
        with self._start_lock:
            if self._worker != "thread" or self._thread is not None:
                return
            self._thread = threading.Thread(
                target=self._loop, name="first-observation", daemon=True
            )
            self._thread.start()
            if self.awards_backfill is not None and self._backfill_thread is None:
                # Heavy, slow and independent: its own thread, never in the observation loop.
                self._backfill_thread = threading.Thread(
                    target=self._backfill_loop, name="awards-backfill", daemon=True
                )
                self._backfill_thread.start()

    def _backfill_loop(self) -> None:
        while True:
            try:
                done = self.awards_backfill.run_one()
            except Exception:  # never stops the runtime; the month is retried later
                done = 0
            time.sleep(3600 if done is None else 600)

    def _loop(self) -> None:
        while True:
            self._wake.wait(timeout=60)
            self._wake.clear()
            # Each stage fails alone: one bad row never stalls the other stages.
            stages = (
                self.enqueue_due,
                self.drain,
                self.ingest_demanded,
                self.ingest_press,
                self.measure_geo,
                self.judge_sector_context,
                self.run_marketing_pool,
                self.purge,
            )
            for stage in stages:
                try:
                    stage()
                except Exception:  # the next wake retries; jobs keep leases and attempts
                    continue

    def _kick(self) -> None:
        if self._worker == "thread":
            self.start()
            self._wake.set()

    # ---- subscriber reads -----------------------------------------------------------
    def _proof(
        self, tenant: str, target_ref: str, organization_id: str | None
    ) -> dict[str, Any] | None:
        """The stored proof, unless it describes another Organization (a replaced Focus)."""
        proof = self.store.proof(tenant, target_ref)
        if (
            proof is not None
            and organization_id is not None
            and proof.get("target", {}).get("organizationId") != organization_id
        ):
            return None
        return proof

    def summary(
        self,
        context: TrustedRequestContext,
        target_ref: str,
        organization_id: str | None = None,
    ) -> dict[str, object] | None:
        tenant = str(context.tenant_id)
        state = self.store.status(tenant, target_ref)
        if state is None:
            return None
        proof = self._proof(tenant, target_ref, organization_id)
        if proof is not None:
            at = self._clock.now()
            live = first_proof_live_deadline(
                proof, lambda url: self.service.content_rights(url, now=at)
            )
            if live is not None and at >= live:
                proof = withdraw_first_proof(proof, at=at)
                state = "SOURCE_UNAVAILABLE"
        headline, headline_code = _headline(proof)
        return {
            "state": state,
            "firstProofReady": bool(proof and proof.get("firstProofReady")),
            "headline": headline,
            "headlineCode": headline_code,
            "observedAt": None if proof is None else proof.get("observedAt"),
        }

    def set_demand_markets(
        self, context: TrustedRequestContext, target_ref: str, markets: Sequence[str]
    ) -> dict[str, object]:
        """Where the subscriber wants demand looked for (attention only, never truth).

        Bounded to EU member states (where the adopted demand sources publish); five at
        most. The caller has already authorized the Focus for this tenant.
        """
        allowed = {f"EU/{code}" for code in EU_MEMBERS.values()}
        chosen = tuple(dict.fromkeys(str(m) for m in markets))
        if len(chosen) > 5 or any(m not in allowed for m in chosen):
            raise ValueError("demand markets must be up to five EU member states")
        self.store.set_demand_markets(
            str(context.tenant_id), target_ref, chosen, now=self._clock.now()
        )
        return {"state": "success", "directed": list(chosen)}

    def _with_registers(
        self, view: dict[str, object], organization_id: str | None
    ) -> dict[str, object]:
        """Official accounts and size from the business register of the organization's own
        identifier (its website's, or its LEI's in Wikidata); they supersede Wikidata's."""
        if self._registers is None:
            return view
        held = view.get("discoveries")
        discoveries = held if isinstance(held, list) else []
        target = view.get("target")
        names = [str(target.get("name") or "")] if isinstance(target, Mapping) else []
        website = target.get("website") if isinstance(target, Mapping) else None
        host = (urlsplit(str(website)).hostname or "").removeprefix("www.") if website else ""
        if host.count(".") >= 1:
            names.append(host.split(".")[-2])  # its own domain name ("vipps" for vipps.no)
        names += [
            str(d.get("statement") or "")
            for d in discoveries
            if isinstance(d, Mapping) and d.get("code") == "LEGAL_NAME_DECLARED"
        ]
        routes: list[tuple[str, str, str]] = []
        for d in discoveries:
            code = str(d.get("code") or "") if isinstance(d, Mapping) else ""
            scheme = code.removeprefix("IDENTIFIER_DECLARED:")
            if code.startswith("IDENTIFIER_DECLARED:") and scheme in self._registers.schemes:
                routes.append((scheme, str(d.get("statement", "")).split(" ", 1)[-1],
                               "REGISTER_ID_ON_WEBSITE"))  # fmt: skip
        verified: tuple[str, ...] = ()
        identifiers_for = getattr(self._websites, "identifiers_for", None)
        if organization_id and callable(identifiers_for):
            verified = tuple(identifiers_for(OrganizationId(organization_id), "LEI"))
        declared_lei = [
            str(d.get("statement", "")).split(" ", 1)[-1]
            for d in discoveries
            if isinstance(d, Mapping) and d.get("code") == "IDENTIFIER_DECLARED:LEI"
        ]
        lei = next(iter(verified), None) or next(iter(declared_lei), None)
        if lei and self._economics is not None:
            try:
                registers = self._economics.facts(lei).get("registers")
            except Exception:  # Wikidata unavailable: only the website's identifiers count
                registers = None
            for scheme, value in registers.items() if isinstance(registers, Mapping) else ():
                if scheme in self._registers.schemes:
                    routes.append((str(scheme), str(value),
                                   "VERIFIED_LEI" if lei in verified else "LEI_ON_WEBSITE"))  # fmt: skip
        observed_at = str(view.get("observedAt") or "")
        found: list[dict[str, object]] = []
        seen: set[tuple[str, str]] = set()
        for scheme, value, via in routes:
            if (scheme, value) in seen or len(seen) >= 3:
                continue
            seen.add((scheme, value))
            try:
                record = self._registers.record(scheme, value)
            except Exception:  # register unavailable: the facts stay unknown
                continue
            if record is None:
                continue
            attributed = via != "LEI_ON_WEBSITE" and same_organization_name(
                str(record.get("name") or ""), names
            )
            found += register_discoveries(record, attributed=attributed, via=via,
                                          observed_at=observed_at)  # fmt: skip
        if not found:
            return view
        official = {str(d["detail"]["fact"]) for d in found}  # type: ignore[index]
        kept = [
            d
            for d in discoveries
            if not (
                isinstance(d, Mapping)
                and str(d.get("code") or "").startswith("WIKIDATA:")
                and str((d.get("detail") or {}).get("fact")) in official
            )
        ]
        view["discoveries"] = [*kept, *found]
        return view

    def _with_group(
        self, view: dict[str, object], organization_id: str | None
    ) -> dict[str, object]:
        """Parents and subsidiaries from GLEIF when the organization has an LEI."""
        if self._groups is None and self._economics is None:
            return view
        verified: tuple[str, ...] = ()
        identifiers_for = getattr(self._websites, "identifiers_for", None)
        if organization_id and callable(identifiers_for):
            verified = tuple(identifiers_for(OrganizationId(organization_id), "LEI"))
        held = view.get("discoveries")
        discoveries = held if isinstance(held, list) else []
        declared = [
            str(d.get("statement", "")).split(" ", 1)[-1]
            for d in discoveries
            if isinstance(d, Mapping) and d.get("code") == "IDENTIFIER_DECLARED:LEI"
        ]
        lei = next(iter(verified), None) or next(iter(declared), None)
        if not lei:
            return view
        observed_at = str(view.get("observedAt") or "")
        found: list[dict[str, object]] = []
        try:
            if self._groups is not None:
                found += group_discoveries(
                    self._groups.group(lei), verified=lei in verified, observed_at=observed_at
                )
        except Exception:  # registry unavailable: the group stays unknown, nothing invented
            pass
        try:
            if self._economics is not None:
                # Economic magnitudes Wikidata states for the item carrying this LEI.
                found += economic_discoveries(
                    self._economics.facts(lei), verified=lei in verified, observed_at=observed_at
                )
        except Exception:  # unavailable: the magnitudes stay unknown
            pass
        if found:
            view["discoveries"] = [*discoveries, *found]
        return view

    def view(
        self,
        context: TrustedRequestContext,
        target_ref: str,
        organization_id: str | None = None,
    ) -> dict[str, object] | None:
        tenant = str(context.tenant_id)
        proof = self._proof(tenant, target_ref, organization_id)
        state = self.store.status(tenant, target_ref)
        if (
            proof is None
            and state is not None
            and state not in {"QUEUED", "OBSERVING_PUBLIC_PRESENCE", "OBSERVATION_FAILED"}
        ):
            state = None  # a proof of a replaced Organization is not this Focus's state
        if proof is not None:
            at = self._clock.now()
            live = first_proof_live_deadline(
                proof, lambda url: self.service.content_rights(url, now=at)
            )
            if live is not None and at >= live:
                proof = withdraw_first_proof(proof, at=at)
                state = "SOURCE_UNAVAILABLE"
        view = public_view(proof, state)
        if view is not None and proof is not None:
            # Tenders open and close daily: demand is matched again now, never frozen.
            directed = self.store.demand_markets(tenant, target_ref)
            view = apply_live_demand(
                view, proof, self._live_demand, now=self._clock.now(), directed=directed
            )
            view["demandMarkets"] = {"directed": list(directed)}
            if self._press is not None:
                # Reputation and activity: headlines that name it, from the press index.
                target = view.get("target")
                website = target.get("website") if isinstance(target, Mapping) else None
                host = urlsplit(str(website)).hostname if website else None
                mentions = press_discoveries(
                    view, self._press[1], now=self._clock.now(), own_domain=host
                )
                if mentions:
                    held = view.get("discoveries")
                    view["discoveries"] = [*(held if isinstance(held, list) else []), *mentions]
            view = self._with_group(view, organization_id)
            view = self._with_registers(view, organization_id)
            view = self._with_geo(view)
            view = self._with_sector_context(view)
            # Relationships and competition from published public contract awards.
            view = apply_public_awards(
                view, proof, self._awards, now=self._clock.now(), countries=lambda: directed
            )
        if view is not None and proof is not None and proof.get("publicUnderstanding"):
            from application.first_observation.understanding import compare, public_report

            now = self._clock.now()

            def rights_for(url: str) -> ContentRights:
                return self.service.content_rights(url, now=now)

            # Rights are re-decided at read: a revocation hides quotations immediately,
            # here and in AXENT (which reads this view), before any purge runs.
            current = public_report(proof["publicUnderstanding"], now=now, rights_for=rights_for)
            history = [
                public_report(r, now=now, rights_for=rights_for)
                for r in self.store.history(
                    tenant, target_ref, proof.get("target", {}).get("organizationId")
                )
                if r["reportId"] != current["reportId"]
            ]
            for previous in history:
                if previous.get("currentness") != "EXPIRED":
                    previous["currentness"] = "HISTORICAL"
            current["history"] = history
            current["comparison"] = compare(current, history[0]) if history else None
            view["publicUnderstanding"] = current
        return view


RIGHTS_FILE_KEY = "AXIGNAL_FIRST_OBSERVATION_CONTENT_RIGHTS_FILE"


class ReloadingContentRights:
    """Operator rights can be revoked without restarting the observation worker."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._signature: tuple[int, int] | None = None
        self._policy: ContentRightsPolicy = NoContentRights()

    def rights_for(self, website: str, *, now: datetime) -> ContentRights:
        with self._lock:
            try:
                stat = self._path.stat()
                signature = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                self._signature = None
                self._policy = NoContentRights()
                return self._policy.rights_for(website, now=now)
            if self._signature != signature:
                # A partially written or invalid file fails closed until repaired.
                policy: ContentRightsPolicy = NoContentRights()
                try:
                    raw = json.loads(self._path.read_text(encoding="utf-8"))
                    if not isinstance(raw, list):
                        raise ValueError("rights file must be a list")
                    entries, provider, public_offer = [], set(), set()
                    for item in raw:
                        entry = website_rights_entry(
                            host=str(item["host"]),
                            basis=str(item["rightsBasis"]),
                            raw_retention_days=int(item["rawRetentionDays"]),
                            metadata_retention_days=int(item["metadataRetentionDays"]),
                        )
                        entries.append(entry)
                        if item.get("providerInput") is True:
                            provider.add(entry.source_id)
                        if item.get("publicOfferInput") is True:
                            public_offer.add(entry.source_id)
                    policy = RegisteredContentRights(
                        tuple(entries),
                        provider_input=frozenset(provider),
                        public_offer_input=frozenset(public_offer),
                    )
                except (OSError, ValueError, KeyError, TypeError):
                    pass
                self._signature = signature
                self._policy = policy
            return self._policy.rights_for(website, now=now)


def load_content_rights(values: Mapping[str, str]) -> ContentRightsPolicy:
    """Live operator registry, fail-closed on deletion or invalid configuration."""
    path = values.get(RIGHTS_FILE_KEY, "").strip()
    return ReloadingContentRights(Path(path)) if path else NoContentRights()


def website_rights_entry(
    *, host: str, basis: str, raw_retention_days: int, metadata_retention_days: int
) -> SourceRegistryEntry:
    """A governed PUBLIC_WEBSITE registry entry for one host (rights PERMITTED by basis)."""
    from datetime import timedelta

    from application.economic_discovery.source_registry import (
        RobotsDecision,
        RobotsRequirement,
        SourceRatePolicy,
        SourceRetentionPolicy,
    )
    from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
    from application.source_acquisition import SourceTargetRule

    bare = host.strip().lower().removeprefix("www.")
    if not bare or not basis.strip():
        raise ValueError("website rights need a host and a rights basis")
    return SourceRegistryEntry(
        source_id=f"website:{bare}",
        version="1",
        source_type="PUBLIC_WEBSITE",
        instrument_ref="stdlib-pinned-http/0.2",
        decision_basis=basis,
        targets=(SourceTargetRule(bare, "/", ("https",)), SourceTargetRule("www." + bare, "/", ("https",))),
        allowed_purposes=(ReusePurpose.CURRENT_STATE, ReusePurpose.HISTORICAL_REFERENCE),
        rights_status=ObservationRightsStatus.PERMITTED,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        reuse_scope=ObservationReuseScope.GLOBAL_PUBLIC,
        reuse_reason=f"Operator-registered rights basis: {basis}",
        temporal_policy=TemporalCurrentnessPolicy(
            "first-observation-website", "1", timedelta(days=30), timedelta(days=90)
        ),
        retention_policy=SourceRetentionPolicy(
            f"website-retention:{bare}", "1", raw_retention_days, metadata_retention_days
        ),
        rate_policy=SourceRatePolicy("first-observation-site", "1", 16, 86_400),
        robots_requirement=RobotsRequirement.REQUIRED,
        robots_decision=RobotsDecision.PERMITTED,
        robots_policy_ref="robots.txt evaluated before every First Observation fetch",
    )  # fmt: skip


def _press(
    root: Path, clock: Clock, overrides: FirstObservationOverrides
) -> tuple[PressIngestor, SqlitePressIndex] | None:
    """The world press index; off in controlled tests that inject their own sources."""
    if overrides.source_ports is not None or overrides.feeds is not None:
        return None
    from application.press.contracts import FEEDS
    from pipeline.press.rss import UrllibFeedTransport

    store = SqlitePressIndex(root / "press-index.sqlite3")
    return PressIngestor(FEEDS, store, UrllibFeedTransport(FEEDS), clock=clock.now), store


def _sector_context(values: Mapping[str, str], root: Path) -> SectorContextRunner | None:
    """Sector context over the world press index, judged by the governed assistant."""
    assistant = assistant_from_values(values)
    if assistant is None:
        return None
    complete, model, _rates = assistant
    return SectorContextRunner(
        complete, model, _PressIndex(root / "press-index.sqlite3"), root / "sector-context.sqlite3"
    )


def _geocoder(root: Path, overrides: FirstObservationOverrides) -> NominatimReverseGeocoder | None:
    """Places of map points sites publish; off in controlled tests with injected sources."""
    if overrides.source_ports is not None or overrides.feeds is not None:
        return None
    return NominatimReverseGeocoder(root / "geo-reverse.sqlite3")


def build_first_observation(
    values: Mapping[str, str],
    root: Path,
    *,
    economic: SubscriberEconomicRuntime,
    portfolio: SubscriberPortfolioRuntime,
    entitlements: EntitlementReader,
    websites: WebsiteIndex,
    observation_memory: ObservationMemory,
    clock: Clock,
    overrides: FirstObservationOverrides | None = None,
) -> FirstObservationRuntime | None:
    overrides = overrides or FirstObservationOverrides()
    enabled = (
        overrides.enabled
        if overrides.enabled is not None
        else values.get(ENABLED_KEY, "false").strip().lower() == "true"
    )
    if not enabled:
        return None
    from pipeline.first_observation.http_fetcher import GovernedSiteFetcher
    from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport
    from pipeline.observation_runtime.sqlite_store import SqliteObservationRuntimeStore
    from pipeline.source_acquisition import ContentAddressedArtifactStore
    from pipeline.source_acquisition.http_sensor import HttpSourceSensor
    from pipeline.source_acquisition.http_transport import PinnedHttpTransport
    from pipeline.source_acquisition.policy import PublicSourcePolicyGate
    from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex
    from tools.runtime.semantic_layer import semantic_cascade_factory_from_env

    policy = FirstObservationPolicy(
        public_understanding=(
            overrides.public_understanding
            if overrides.public_understanding is not None
            else values.get("AXIGNAL_PUBLIC_UNDERSTANDING_ENABLED", "false").lower() == "true"
        )
    )
    store = SqliteFirstObservationStore(root / "first-observation.sqlite3")
    fetcher = overrides.fetcher
    if fetcher is None:
        # A dedicated store: bodies without retention rights are discarded after the run.
        artifacts = ContentAddressedArtifactStore(root / "first-observation-artifacts")
        fetcher = GovernedSiteFetcher(
            sensor=HttpSourceSensor(
                policy_gate=PublicSourcePolicyGate(),
                transport=PinnedHttpTransport(),
                artifacts=artifacts,
                clock=clock.now,
            ),
            artifacts=artifacts,
        )
    live_ted = TedSearchAdapter(UrllibTedTransport(), clock=clock.now)
    live = overrides.source_ports or {"ted-search-v3": live_ted}
    feeds: dict[str, SliceFeedPort] = (
        dict(overrides.feeds) if overrides.feeds is not None else {"ted-search-v3": live_ted}
    )
    index = SqliteWorldDemandIndex(root / "world-demand-index.sqlite3")
    placsp_index: SqliteWorldDemandIndex | None = None
    # Index first (world slices ingested once), the live adapter only for what no
    # fresh complete slice covers; the uncovered slice is demanded for ingestion.
    ports: dict[str, SourceObservationPort] = {
        source_id: DemandIndexPort(index, port, clock=clock.now) if source_id in feeds else port
        for source_id, port in live.items()
    }
    if overrides.source_ports is None and overrides.feeds is None:
        # Spain's own platform: read only for the index (its pages are large and cannot be
        # queried by code), so it answers from the index or not at all. Its slice is kept
        # demanded so it is ready before a subscriber needs it.
        from application.observation_intelligence.contracts import SourceCapability
        from application.world_demand.index import DemandSlice
        from pipeline.observation_intelligence.placsp import (
            PLACSP_SOURCE_ID,
            PlacspFeedAdapter,
            UrllibPlacspTransport,
        )

        feeds[PLACSP_SOURCE_ID] = PlacspFeedAdapter(
            UrllibPlacspTransport(), clock=clock.now, awards_sink=index.upsert_awards
        )
        placsp_index = index
        ports[PLACSP_SOURCE_ID] = DemandIndexPort(index, None, clock=clock.now)
        index.demand(
            DemandSlice(
                PLACSP_SOURCE_ID, "EU/ES", SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
            ),
            now=clock.now(),
        )
    ingestor = WorldDemandIngestor(
        feeds={k: v for k, v in feeds.items() if k in ports},
        store=index,
        clock=clock.now,
        # Ingestion shares the worker with first observations: short rounds keep a new
        # subscriber's wait bounded while a large backfill (PLACSP) spans many rounds.
        max_pages=8,
    )
    from application.subscriber_projection.evidence_delivery import ContentAccess
    from tools.runtime.evidence_content import LiveEvidenceContentRights

    rights_policy = overrides.rights or load_content_rights(values)
    factory = overrides.cascade_factory or semantic_cascade_factory_from_env(
        values, data_dir=root, token_budget=policy.semantic_tokens
    )
    service = FirstObservationService(
        fetcher=fetcher,
        sites=store,
        research=RuntimeDemandResearch(
            economic=economic,
            ports=ports,
            ledger=SqliteObservationRuntimeStore(root / "observation-runtime.sqlite3"),
            clock=clock.now,
        ),
        seeds=FocusSeed(observation_memory),
        cascade_factory=factory or (lambda: None),
        clock=clock.now,
        policy=policy,
        rights=rights_policy,
        geocoder=_geocoder(root, overrides),
        field_performance=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else field_performance_from_env(root),
    )
    try:
        daily_jobs = int(values.get(DAILY_JOBS_KEY, "500"))
    except ValueError:
        daily_jobs = 500
    runtime = FirstObservationRuntime(
        store=store,
        service=service,
        portfolio=portfolio,
        entitlements=entitlements,
        websites=websites,
        clock=clock,
        worker=overrides.worker or values.get(WORKER_KEY, "thread").strip() or "thread",
        daily_jobs=max(0, daily_jobs),
        ingestor=ingestor,
        live_demand=LiveDemandReader(index, sources=tuple(ports), clock=clock.now),
        press=_press(root, clock, overrides),
        groups=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else GleifGroupReader(root / "gleif-groups.sqlite3"),
        geo=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else generative_probe_from_values(values, root),
        sector_context=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else _sector_context(values, root),
        economics=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else WikidataEconomics(root / "wikidata-economics.sqlite3"),
        registers=None
        if overrides.source_ports is not None or overrides.feeds is not None
        else registers_from_env(root, values),
        awards=index,
        purge_canonical_raw=(
            lambda at: observation_memory.purge_first_observation_content(
                now=at,
                content_allowed=lambda metadata: (
                    LiveEvidenceContentRights(service._rights, lambda: at).decision(metadata)
                    is ContentAccess.PERMITTED
                ),
                retain_until=lambda url, observed: (
                    observed + timedelta(days=grant.raw_retention_days)
                    if (grant := service._rights.rights_for(url, now=at)).reuse_permitted
                    and grant.raw_retention_days > 0
                    else None
                ),
            )
        )
        if isinstance(observation_memory, SqliteObservationMemory)
        else None,
    )
    if placsp_index is not None:
        try:
            months = int(values.get("AXIGNAL_AWARDS_BACKFILL_MONTHS", "12"))
        except ValueError:
            months = 12
        if months > 0:
            from pipeline.observation_intelligence.placsp_archive import PlacspAwardsBackfill

            runtime.awards_backfill = PlacspAwardsBackfill(
                placsp_index.upsert_awards,
                root / "world-demand-index.sqlite3",
                root / "tmp" / "placsp-archives",
                months=min(months, 36),
            )
    if overrides.source_ports is None and overrides.feeds is None:
        from tools.runtime.marketing_pool import build_marketing_pool

        assistant = assistant_from_values(values)
        runtime.marketing_pool = build_marketing_pool(
            values,
            root,
            study=runtime.study,
            study_result=runtime.study_result,
            complete=None if assistant is None else assistant[0],
            model=None if assistant is None else assistant[1],
        )
    runtime.start()
    return runtime


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("metrics",))
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    database = args.data_dir / "first-observation.sqlite3"
    if not database.is_file():
        print(json.dumps({"jobs": 0, "state": "NO_FIRST_OBSERVATION_STORE"}))
        return
    print(json.dumps(runtime_metrics(SqliteFirstObservationStore(database).proofs()), indent=2))


if __name__ == "__main__":
    main()


DerivedReader = Callable[[TrustedRequestContext, XeedId], Mapping[str, Any] | None]


def first_observation_reader(
    root: Path,
    *,
    rights: ContentRightsPolicy | None = None,
    clock: Callable[[], datetime] | None = None,
) -> DerivedReader | None:
    """A Focus's stored First Proof for the autonomous runtime, or None without a store."""
    database = root / "first-observation.sqlite3"
    if not database.is_file():
        return None
    store = SqliteFirstObservationStore(database)
    from application.first_observation.understanding import public_report

    policy = rights or NoContentRights()
    now = clock or (lambda: datetime.now(UTC))

    def read(context: TrustedRequestContext, focus: XeedId) -> Mapping[str, Any] | None:
        proof = store.proof(str(context.tenant_id), str(focus))
        if proof is None:
            return None
        at = now()
        deadlines = [first_proof_live_deadline(proof, lambda u: policy.rights_for(u, now=at))]
        stored = proof.get("contentExpiresAt")
        if isinstance(stored, str):
            deadlines.append(datetime.fromisoformat(stored))
        if any(deadline is not None and at >= deadline for deadline in deadlines):
            proof = withdraw_first_proof(proof, at=at)
        report = proof.get("publicUnderstanding")
        if isinstance(report, dict):
            proof = dict(proof)
            proof["publicUnderstanding"] = public_report(
                report, now=at, rights_for=lambda url: policy.rights_for(url, now=at)
            )
        return proof

    return read
