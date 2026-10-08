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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit

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
from application.first_observation.contracts import (
    AttentionTarget,
    IdentityLink,
    TargetKind,
)
from application.first_observation.metrics import runtime_metrics
from application.first_observation.policy import FirstObservationPolicy
from application.first_observation.research import ResearchPlan
from application.first_observation.service import (
    DemandOutcome,
    FirstObservationService,
    SiteFetchPort,
)
from application.first_observation.shared_findings import SharedFindingsPort
from application.first_observation.site import PageReading
from application.observation_intelligence import (
    OperationalLearning,
    SourceObservationPort,
    SourceRegistry,
)
from application.observation_intelligence.loop import OpportunityCandidate, run_observation_loop
from application.observation_runtime.replay import FindingsLedger
from application.organization_admission.locator import LocatorError, parse_locator, public_domain
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
from application.xeed_access.reader import TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore
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


class FocusSeed:
    """Append readable pages under the canonical Organization subject (ADR-0091 §3)."""

    def __init__(self, memory: ObservationMemory) -> None:
        self._memory = memory

    def seed(
        self, target: AttentionTarget, pages: Sequence[PageReading], *, now: datetime
    ) -> Mapping[str, str]:
        del now
        organization = target.organization_id
        if organization is None:
            raise ValueError("only a Focus target is seeded under an Organization")
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
                        rights_status=ObservationRightsStatus.PERMITTED,
                        access_status=ObservationAccessStatus.ACCESSIBLE,
                        scope=ObservationReuseScope.GLOBAL_PUBLIC,
                        provenance_ref=page.artifact_ref or f"first-observation:{page.url}",
                        currentness=Currentness.CURRENT,
                        applicable_subject_ids=(organization,),
                        applicable_purposes=(
                            ReusePurpose.CURRENT_STATE.value,
                            ReusePurpose.HISTORICAL_REFERENCE.value,
                        ),
                        authority_id="first-observation-public-website",
                        authority_version="1",
                        reuse_reason=(
                            "Public website page observed after robots.txt under a bounded "
                            f"GET policy; website link {target.identity_link.value}."
                        ),
                        robots_policy_ref="robots.txt observed before fetch",
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
        self, target: AttentionTarget, plan: ResearchPlan, *, now: datetime
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
        if target.kind is TargetKind.FOCUS:
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
        candidates = list(result.candidates)
        screen = self._economic.semantic_screen
        if target.kind is TargetKind.PENDING and screen is not None and candidates:
            run = screen.screen(candidates, now=now)
            candidates = [
                c
                for c in candidates
                if c.candidate_id not in run.screens or not run.screens[c.candidate_id].unrelated
            ]
        hits = sum(p.hits for p in shared.values() if isinstance(p, SharedFindingsPort))
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
    view = dict(proof)
    target = dict(view.pop("target"))
    view["target"] = {
        "kind": target["kind"],
        "website": target["website"],
        "name": target["name"],
        "identityLink": target["identityLink"],
    }
    view["state"] = state or view["state"]
    return view


def _headline(proof: Mapping[str, Any] | None) -> str | None:
    if proof is None:
        return None
    for kind in ("ACTIVITY", "PUBLIC_PRESENCE"):
        for discovery in proof.get("discoveries", ()):
            if discovery.get("kind") == kind:
                return str(discovery.get("statement"))
    return None


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
    ) -> None:
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
        verified = (
            domain is not None
            and str(self._websites.organization_by_domain(domain)) == organization
        )
        target = AttentionTarget(
            tenant_id=str(context.tenant_id),
            principal_id=str(context.principal_id),
            target_ref=str(focus_id),
            kind=TargetKind.FOCUS,
            website=website,
            name=name or entry.xeed.label,
            organization_id=organization,
            identity_link=IdentityLink.REGISTRY_VERIFIED if verified else IdentityLink.SUBSCRIBER_DIRECTED,
        )  # fmt: skip
        self.store.enqueue(target, key=f"focus:{key}", now=self._clock.now())
        self._kick()
        return "QUEUED"

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
        self.store.enqueue(target, key=f"pending:{pending.idempotency_key}", now=self._clock.now())
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
        if self.store.jobs_started_on(now.date().isoformat()) >= self._daily_jobs:
            return False
        job = self.store.claim(
            now=now, lease_seconds=policy.lease_seconds, max_attempts=policy.max_attempts
        )
        if job is None:
            return False
        if not self._still_authorized(job.target):
            self.store.fail(job, error="TARGET_NO_LONGER_AUTHORIZED", now=now, retry=False)
            return True
        try:
            proof = self.service.observe(job.target)
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

    def enqueue_due(self) -> int:
        now = self._clock.now()
        created = 0
        for target in self.store.due(now=now):
            created += self.store.enqueue(target, key=f"due:{now.date().isoformat()}", now=now)[1]
        return created

    def start(self) -> None:
        if self._worker != "thread" or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="first-observation", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        while True:
            self._wake.wait(timeout=60)
            self._wake.clear()
            try:
                self.enqueue_due()
                self.drain()
            except Exception:  # the next wake retries; jobs keep their leases and attempts
                continue

    def _kick(self) -> None:
        if self._worker == "thread":
            self.start()
            self._wake.set()

    # ---- subscriber reads -----------------------------------------------------------
    def summary(self, context: TrustedRequestContext, target_ref: str) -> dict[str, object] | None:
        tenant = str(context.tenant_id)
        state = self.store.status(tenant, target_ref)
        if state is None:
            return None
        proof = self.store.proof(tenant, target_ref)
        return {
            "state": state,
            "firstProofReady": bool(proof and proof.get("firstProofReady")),
            "headline": _headline(proof),
            "observedAt": None if proof is None else proof.get("observedAt"),
        }

    def view(self, context: TrustedRequestContext, target_ref: str) -> dict[str, object] | None:
        tenant = str(context.tenant_id)
        return public_view(
            self.store.proof(tenant, target_ref), self.store.status(tenant, target_ref)
        )


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
    from tools.runtime.semantic_layer import semantic_cascade_factory_from_env

    policy = FirstObservationPolicy()
    store = SqliteFirstObservationStore(root / "first-observation.sqlite3")
    fetcher = overrides.fetcher
    if fetcher is None:
        artifacts = ContentAddressedArtifactStore(root / "artifacts")
        fetcher = GovernedSiteFetcher(
            sensor=HttpSourceSensor(
                policy_gate=PublicSourcePolicyGate(),
                transport=PinnedHttpTransport(),
                artifacts=artifacts,
                clock=clock.now,
            ),
            artifacts=artifacts,
        )
    ports = overrides.source_ports
    if ports is None:
        ports = {"ted-search-v3": TedSearchAdapter(UrllibTedTransport(), clock=clock.now)}
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


def first_observation_reader(root: Path) -> DerivedReader | None:
    """A Focus's stored First Proof for the autonomous runtime, or None without a store."""
    database = root / "first-observation.sqlite3"
    if not database.is_file():
        return None
    store = SqliteFirstObservationStore(database)
    return lambda context, focus: store.proof(str(context.tenant_id), str(focus))
