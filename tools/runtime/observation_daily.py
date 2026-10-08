"""Daily autonomous observation: production entrypoint and real Brain wiring.

Off by default. It runs only when ``AXIGNAL_OBSERVATION_RUNTIME_ENABLED=true``
and the operator has provided both server-owned inputs:

* ``AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE`` — the existing market attention
  per Organization (the same file the subscriber reobservation uses);
* ``AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE`` — which subscriber focus is
  observed on whose behalf (tenant, principal, focus). Every tick re-checks the
  principal's membership and the focus's tenant; a revoked grant fails closed.

Downstream recomputation goes through the canonical subscriber reobservation
entry (`ConfiguredSubscriberObservationPlanReader` →
`SubscriberEconomicRuntime.execute_observation_loop`), fed by a replay of the
runtime's own real retrievals: no second Brain, no refetch, no new authority.
Only adopted sources with documented rights are wired; the public website needs
an operator source-rights grant (FR-30) that this entrypoint does not invent,
so website leads stay blocked.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from application.axent.grounded.answer import ResearchRequest
from application.axent.grounded.corpus import AuthorizedCorpus, corpus_from_reading
from application.axent.research import ResearchConsumer, ResearchLedger
from application.economic_discovery.continuous_observation import SharedObservationWorkMemory
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.observation_intelligence import (
    MarketScope,
    StopPolicy,
    XeedObservationContext,
    geo,
)
from application.observation_intelligence.loop import SourceObservationPort
from application.observation_runtime import (
    DailyObservationBudget,
    ObservationFamily,
    RecomputationRequest,
    RecomputeTrigger,
    TickReport,
    XeedAttention,
    procurement_acquirers,
    run_daily_tick,
)
from application.observation_runtime.ports import (
    Acquisition,
    AcquisitionPort,
    AcquisitionRequest,
    LeaseLost,
    ObservationRuntimeStore,
)
from application.observation_runtime.replay import FindingsLedger, RecordedFindingsPort
from application.subscriber_continuity.service import ContinuityService
from application.subscriber_identity.runtime import Clock
from application.subscriber_projection.subscriber_runtime import SubscriberEconomicRuntime
from application.xeed_access.organization_reader import OrganizationReadError
from application.xeed_access.reader import TrustedRequestContext, XeedReadError
from domain.identity import PrincipalId, TenantId, XeedId
from domain.xignal import XignalEpistemicState
from tools.runtime.first_observation import DerivedReader, first_observation_reader
from tools.runtime.subscriber_observation import (
    ConfiguredSubscriberObservationPlanReader,
    SubscriberObservationPlanConfigurationError,
    load_observation_attention,
)

#: Families whose governed downstream is the subscriber opportunity projection.
OPPORTUNITY_PROJECTION_FAMILIES = frozenset({ObservationFamily.DEMAND, ObservationFamily.MARKETS})


class RuntimeStore(ObservationRuntimeStore, FindingsLedger, Protocol):
    """Operational state plus the ledger of real retrievals (one SQLite file)."""

    def owe_recompute(
        self, *, xeed_id: str, family: str, evidence_keys: tuple[str, ...], now: datetime
    ) -> bool:
        """Brain-continuity debt, fenced against a live tick (TASK-050 T022)."""


class ObservationRuntimeConfigurationError(ValueError):
    """Fail-closed configuration error without leaking file contents."""


@dataclass(frozen=True, slots=True)
class ObservationEnrollment:
    context: TrustedRequestContext
    focus_id: XeedId


def load_enrollment(path: Path) -> tuple[ObservationEnrollment, ...]:
    if not path.is_file() or path.stat().st_size > 65536:
        raise ObservationRuntimeConfigurationError("enrollment file unavailable or too large")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ObservationRuntimeConfigurationError("invalid enrollment file") from error
    if not isinstance(raw, list):
        raise ObservationRuntimeConfigurationError("enrollment must be a list")
    entries = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"tenantId", "principalId", "focusId"}:
            raise ObservationRuntimeConfigurationError("invalid enrollment entry")
        if not all(isinstance(v, str) and v.strip() for v in item.values()):
            raise ObservationRuntimeConfigurationError("enrollment values are required")
        entries.append(
            ObservationEnrollment(
                TrustedRequestContext(PrincipalId(item["principalId"]), TenantId(item["tenantId"])),
                XeedId(item["focusId"]),
            )
        )
    if len({e.focus_id for e in entries}) != len(entries):
        raise ObservationRuntimeConfigurationError("duplicate enrolled focus")
    return tuple(entries)


def attention_for(
    economic: SubscriberEconomicRuntime,
    plans: ConfiguredSubscriberObservationPlanReader,
    enrollment: ObservationEnrollment,
    *,
    as_of: datetime,
) -> XeedAttention | None:
    """Authorized attention: configured markets, the canonical name, the observed site."""

    try:
        authorized, history = economic.observation_seed(
            enrollment.context, enrollment.focus_id, as_of=as_of
        )
    except (XeedReadError, OrganizationReadError):
        return None
    organization_id = str(authorized.organization.id)
    configured = next((a for a in plans.attention if a.organization_id == organization_id), None)
    if configured is None:
        return None
    current = [
        o
        for o, c in history
        if c.value == "CURRENT" and o.raw_content and o.record.source_type == "PUBLIC_WEBSITE"
    ]
    website = (
        max(
            current, key=lambda o: (o.record.observed_at, o.record.observation_id)
        ).record.source_ref
        if current
        else None
    )
    return XeedAttention(
        xeed_id=str(enrollment.focus_id),
        organization_name=authorized.organization.canonical_name,
        website=website,
        markets=tuple(
            MarketScope(geo(m.jurisdiction), m.roles, XignalEpistemicState.POTENTIAL)
            for m in configured.markets
        ),
    )


def replay_plans(
    economic: SubscriberEconomicRuntime,
    clock: Clock,
    attention_file: Path,
    ledger: FindingsLedger,
    derived_for: DerivedReader | None = None,
) -> ConfiguredSubscriberObservationPlanReader:
    """The canonical plan reader, answering its strategy from the runtime's real retrievals."""

    port = RecordedFindingsPort(ledger, clock=clock.now)
    return ConfiguredSubscriberObservationPlanReader(
        economic=economic,
        clock=clock,
        attention=load_observation_attention(attention_file),
        adapters_for=lambda strategy: {a.source_id: port for a in strategy.actions},
        derived_for=derived_for,
        # Replay is free: every recorded answer is projected, none cut by a budget stop.
        stop_policy=StopPolicy(sufficient_candidates=10**6, max_no_gain_streak=10**6),
    )


def capability_contexts(
    plans: ConfiguredSubscriberObservationPlanReader,
    contexts: Mapping[str, TrustedRequestContext],
) -> Callable[[XeedAttention, datetime], XeedObservationContext | None]:
    """Capabilities only from evidence admitted for the authorized Organization."""

    def provide(attention: XeedAttention, as_of: datetime) -> XeedObservationContext | None:
        context = contexts.get(attention.xeed_id)
        if context is None:
            return None
        try:
            plan = plans.observation_plan_for(context, XeedId(attention.xeed_id))
        except (XeedReadError, OrganizationReadError):
            return None
        return None if plan is None else replace(plan.observation_context, as_of=as_of)

    return provide


@dataclass
class SubscriberBrainRecomputation:
    """RecomputationPort over the canonical subscriber reobservation entry.

    Selective: only families whose governed consumer is the opportunity
    projection republish it, at most once per Xeed and tick, and only for a
    material change. Currentness alone is re-evaluated by every subscriber read.
    """

    economic: SubscriberEconomicRuntime
    plans: ConfiguredSubscriberObservationPlanReader
    contexts: Mapping[str, TrustedRequestContext]
    scope_authorized: Callable[[TrustedRequestContext, XeedId, datetime], bool] | None = None
    outcomes: list[tuple[str, str, str, str]] = field(default_factory=list)
    _published: set[tuple[str, str]] = field(default_factory=set)

    def _note(self, request: RecomputationRequest, outcome: str) -> None:
        self.outcomes.append(
            (request.xeed_id, request.family.value, request.trigger.value, outcome)
        )

    def recompute(self, request: RecomputationRequest) -> None:
        if request.family not in OPPORTUNITY_PROJECTION_FAMILIES:
            # Website evidence is already in Observation Memory; no other governed consumer here.
            return self._note(request, "OBSERVATION_MEMORY_ONLY")
        if request.trigger is RecomputeTrigger.CURRENTNESS_TRANSITION:
            return self._note(request, "CURRENTNESS_REEVALUATED_AT_READ")
        key = (request.xeed_id, request.as_of.isoformat())
        if key in self._published:
            return self._note(request, "ALREADY_RECOMPUTED_THIS_TICK")
        context = self.contexts.get(request.xeed_id)
        if context is None:
            return self._note(request, "NOT_ENROLLED")
        focus = XeedId(request.xeed_id)
        if self.scope_authorized is not None and not self.scope_authorized(
            context, focus, request.as_of
        ):
            return self._note(request, "NOT_AUTHORIZED")
        try:
            plan = self.plans.observation_plan_for(context, focus)
            if plan is None:
                return self._note(request, "NO_AUTHORIZED_PLAN")
            result = self.economic.execute_observation_loop(
                context,
                focus,
                observation_context=plan.observation_context,
                strategy=plan.strategy,
                adapters=plan.adapters,
                coverage=plan.coverage,
                learning=plan.learning,
                registry=plan.registry,
            )
        except (XeedReadError, OrganizationReadError):
            return self._note(request, "NOT_AUTHORIZED")
        self._published.add(key)
        self._note(request, f"PROJECTION_RECOMPUTED:{len(result.candidates)}")


# Must match the subscriber read policies composed in tools/runtime/service.py.
SUBSCRIBER_REUSE_POLICY = ObservationReusePolicy("subscriber-output-reuse", "051-v1")
SUBSCRIBER_TEMPORAL_POLICY = TemporalCurrentnessPolicy(
    policy_id="subscriber-public-observation-currentness",
    version="051-v1",
    stale_after=timedelta(days=30),
    historical_after=timedelta(days=90),
)


@dataclass
class AuthorizedAcquisition:
    """Recheck current subscriber authority before the existing source boundary."""

    inner: AcquisitionPort
    contexts: Mapping[str, TrustedRequestContext]
    clock: Clock
    allowed: Callable[[TrustedRequestContext, XeedId, datetime], bool]

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return self.inner.acquisition_key(request)

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return self.inner.worst_case_requests(request)

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        context = self.contexts.get(request.lead.xeed_id)
        if context is None or not self.allowed(
            context, XeedId(request.lead.xeed_id), self.clock.now()
        ):
            return Acquisition(0, 0, 0, blocked="AUTHORIZATION_REVOKED")
        return self.inner.acquire(request)


def run_once(
    *,
    economic: SubscriberEconomicRuntime,
    store: RuntimeStore,
    clock: Clock,
    attention_file: Path,
    enrollment: tuple[ObservationEnrollment, ...],
    source_ports: Mapping[str, SourceObservationPort],
    budget: DailyObservationBudget | None = None,
    research_ledger: ResearchLedger | None = None,
    research_access: Callable[[TrustedRequestContext, XeedId, datetime], bool] | None = None,
    research_shared: SharedObservationWorkMemory | None = None,
    derived_for: DerivedReader | None = None,
) -> tuple[TickReport, SubscriberBrainRecomputation]:
    """One daily tick wired to the real subscriber Brain."""

    plans = replay_plans(economic, clock, attention_file, store, derived_for)
    now = clock.now()
    if research_access is not None:
        enrollment = tuple(e for e in enrollment if research_access(e.context, e.focus_id, now))
    contexts = {str(e.focus_id): e.context for e in enrollment}
    attention = tuple(
        item
        for e in enrollment
        if (item := attention_for(economic, plans, e, as_of=now)) is not None
    )
    acquirers: dict[str, AcquisitionPort] = dict(
        procurement_acquirers(
            source_ports,
            contexts=capability_contexts(plans, contexts),
            ledger=store,
        )
    )
    if research_access is not None:
        acquirers = {
            key: AuthorizedAcquisition(port, contexts, clock, research_access)
            for key, port in acquirers.items()
        }
    # Declared-dependency invalidation (TASK-050 T022): owe material recomputation for
    # enrolled Foci whose Brain checkpoint lost its support. The tick below drains it
    # through the same RecomputationPort; this adds no scheduler and no second queue.
    continuity = economic.continuity
    if isinstance(continuity, ContinuityService):
        for enrolled in enrollment:
            try:
                xeed = economic.authorize(enrolled.context, enrolled.focus_id).authorized_xeed.xeed
            except (XeedReadError, OrganizationReadError):
                continue
            continuity.reconcile(xeed.tenant_id, xeed.id, now=now, owe=store)
    brain = SubscriberBrainRecomputation(
        economic=economic, plans=plans, contexts=contexts, scope_authorized=research_access
    )

    def research_corpus(item: ResearchRequest, as_of: datetime) -> AuthorizedCorpus | None:
        context = contexts.get(item.xeed_id)
        if (
            context is None
            or str(context.tenant_id) != item.tenant_id
            or research_access is None
            or not research_access(context, XeedId(item.xeed_id), as_of)
        ):
            return None
        try:
            authorized = economic.authorize(context, XeedId(item.xeed_id))
            if str(authorized.organization.id) != item.organization_id:
                return None
            reading = economic.read(context, XeedId(item.xeed_id), as_of)
        except (XeedReadError, OrganizationReadError):
            return None
        return corpus_from_reading(
            tenant_id=item.tenant_id, projection=reading.projection, as_of=as_of
        )

    from tools.runtime.observation_research import compatible_shared_key

    consumer = (
        None
        if research_ledger is None
        else ResearchConsumer(
            research_ledger,
            research_corpus,
            evidence_for=lambda ids: tuple(
                sorted(f"{e.key}@{e.fingerprint}" for e in store.evidence() if e.lead_id in ids)
            ),
            shared=research_shared,
            shared_key_for=lambda item: (
                None if research_shared is None else compatible_shared_key(research_shared, item)
            ),
        )
    )
    report = run_daily_tick(
        store=store,
        now=now,
        attention=attention,
        acquirers=acquirers,
        recompute=brain,
        budget=budget,
        research=consumer,
    )
    return report, brain


def build_economic_runtime(root: Path, *, code_sha: str) -> SubscriberEconomicRuntime:
    """The same membership-checked subscriber runtime the HTTP service composes."""

    from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
    from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
    from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
    from pipeline.source_acquisition import (
        ContentAddressedArtifactIntegrityAdapter,
        ContentAddressedArtifactStore,
    )
    from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
    from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore
    from tools.runtime.subscriber_economic import build_subscriber_economic_runtime

    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    return build_subscriber_economic_runtime(
        database_path=root / "subscriber-economic-output.sqlite3",
        identity_store=SqliteSubscriberIdentityStore(root / "subscriber-runtime.sqlite3"),
        portfolio_store=SqliteSubscriberPortfolioStore(root / "subscriber-runtime.sqlite3"),
        organizations=SqliteCanonicalOrganizationStore(
            root / "canonical-organizations.sqlite3",
            integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            governance=SqliteIdentityGovernanceStore(root / "identity-governance.sqlite3"),
        ),
        observation_memory=SqliteObservationMemory(root / "observation-memory.sqlite3"),
        reuse_policy=SUBSCRIBER_REUSE_POLICY,
        temporal_policy=SUBSCRIBER_TEMPORAL_POLICY,
        code_sha=code_sha,
    )


def run_scheduled_tick(
    *,
    root: Path,
    clock: Clock,
    code_sha: str,
    attention_file: Path,
    enrollment: tuple[ObservationEnrollment, ...],
    source_ports: Mapping[str, SourceObservationPort],
    economic: SubscriberEconomicRuntime | None = None,
    research_access: Callable[[TrustedRequestContext, XeedId, datetime], bool] | None = None,
) -> dict[str, object]:
    """One existing runtime entry with durable, redacted operator evidence. No retries."""

    from pipeline.axent import SqliteResearchRequestLedger
    from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
    from pipeline.observation_runtime import SqliteObservationRuntimeStore
    from tools.runtime.observation_enrollment import SubscriberObservationAuthority

    store = SqliteObservationRuntimeStore(root / "observation-runtime.sqlite3")
    started_at = clock.now()
    invocation_id = store.begin_invocation(started_at=started_at, code_sha=code_sha)
    began = time.monotonic()
    summary: dict[str, object]
    try:
        report, brain = run_once(
            economic=economic or build_economic_runtime(root, code_sha=code_sha),
            store=store,
            clock=clock,
            attention_file=attention_file,
            enrollment=enrollment,
            source_ports=source_ports,
            derived_for=first_observation_reader(root),
            research_ledger=SqliteResearchRequestLedger(
                root / "axent-research.sqlite3", runtime_path=root / "observation-runtime.sqlite3"
            ),
            research_access=research_access
            or SubscriberObservationAuthority(
                root,
                clock,
                Path(os.environ["AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE"])
                if os.getenv("AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE")
                else None,
            ).allows,
            research_shared=SqliteSharedObservationWorkMemory(root / "research-work.sqlite3"),
        )
        summary = {
            "state": report.status.value,
            "day": report.day,
            "stop": report.stop_reason.value,
            "detail": report.stop_detail,
            "resumed": report.resumed,
            "items": len(report.executed),
            "failed_items": sum(e.outcome.value == "FAILED" for e in report.executed),
            "blocked_items": len(report.blocked),
            "deferred_items": len(report.deferred),
            "requests": report.requests,
            "candidates_new": report.candidates_new,
            "evidence_new": sum(e.new_evidence for e in report.executed),
            "recomputations": len(brain.outcomes),
            "brain_recomputed": sum(
                outcome[3].startswith("PROJECTION_RECOMPUTED") for outcome in brain.outcomes
            ),
            "next_due_at": report.next_due_at,
            "lease_status": "HELD_BY_OTHER" if report.status.value == "LEASE_HELD" else "COMPLETED",
        }
    except LeaseLost:
        summary = {"state": "LEASE_LOST", "lease_status": "LOST"}
    except Exception as error:
        # No exception message, traceback, raw evidence, tenant/focus id or credentials.
        summary = {
            "state": "ERROR",
            "error_class": type(error).__name__,
            "lease_status": "INSPECT_STORE",
        }
    summary["duration_seconds"] = round(time.monotonic() - began, 6)
    summary["code_sha"] = code_sha
    store.finish_invocation(invocation_id, finished_at=clock.now(), summary=summary)
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true", help="Read redacted operational status only"
    )
    args = parser.parse_args(argv)
    if args.status:
        from pipeline.observation_runtime import SqliteObservationRuntimeStore

        data = os.getenv("AXIGNAL_DATA_DIR", "").strip()
        if not data:
            print(json.dumps({"state": "NOT_CONFIGURED"}))
            sys.exit(2)
        print(
            json.dumps(
                SqliteObservationRuntimeStore.inspect(
                    Path(data) / "observation-runtime.sqlite3", now=datetime.now(UTC)
                )
            )
        )
        return
    if os.getenv("AXIGNAL_OBSERVATION_RUNTIME_ENABLED", "").strip().lower() != "true":
        print(json.dumps({"state": "DISABLED"}))
        return
    from application.subscriber_identity.runtime import SystemClock
    from pipeline.observation_intelligence import TedSearchAdapter, UrllibTedTransport

    data = os.getenv("AXIGNAL_DATA_DIR", "").strip()
    attention_file = os.getenv("AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE", "").strip()
    enrollment_file = os.getenv("AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE", "").strip()
    if not data or not attention_file or not enrollment_file:
        print(json.dumps({"state": "NOT_CONFIGURED"}))
        sys.exit(2)
    try:
        enrollment = load_enrollment(Path(enrollment_file).expanduser().resolve())
        load_observation_attention(Path(attention_file).expanduser().resolve())
    except (ObservationRuntimeConfigurationError, SubscriberObservationPlanConfigurationError):
        print(json.dumps({"state": "INVALID_CONFIGURATION"}))
        sys.exit(2)
    root = Path(data).resolve()
    clock = SystemClock()
    manifest = os.getenv("AXIGNAL_OBSERVATION_MATERIALIZATION_FILE", "").strip()
    if manifest:
        from tools.runtime.observation_enrollment import validate_manifest

        if not validate_manifest(Path(manifest), Path(enrollment_file), Path(attention_file)):
            print(json.dumps({"state": "INVALID_CONFIGURATION"}))
            sys.exit(2)
        from application.observation_runtime.materialization import derive_observation
        from tools.runtime.observation_enrollment import (
            SubscriberObservationAuthority,
            snapshot_bytes,
        )

        try:
            authority = SubscriberObservationAuthority(
                root,
                clock,
                Path(os.environ["AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE"])
                if os.getenv("AXIGNAL_SUBSCRIBER_CONFIGURATION_FILE")
                else None,
            )
            desired = snapshot_bytes(derive_observation(authority, now=clock.now()))
            stale = (
                Path(enrollment_file).read_bytes() != desired["enrollment.json"]
                or Path(attention_file).read_bytes() != desired["attention.json"]
            )
        except Exception as error:
            print(
                json.dumps(
                    {
                        "state": "AUTHORITY_UNAVAILABLE",
                        "requests": 0,
                        "error_class": type(error).__name__,
                    }
                )
            )
            sys.exit(2)
        if stale:
            print(json.dumps({"state": "STALE_MATERIALIZATION", "requests": 0}))
            return
    summary = run_scheduled_tick(
        root=root,
        code_sha=os.getenv("AXIGNAL_CODE_SHA", "UNKNOWN").strip() or "UNKNOWN",
        clock=clock,
        attention_file=Path(attention_file).expanduser().resolve(),
        enrollment=enrollment,
        source_ports={
            "ted-search-v3": TedSearchAdapter(UrllibTedTransport(), clock=lambda: datetime.now(UTC))
        },
    )
    print(json.dumps(summary))
    if summary["state"] in {"ERROR", "LEASE_LOST"}:
        sys.exit(1)


if __name__ == "__main__":
    main()
