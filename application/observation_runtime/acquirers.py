"""Acquisition ports over capabilities AXIGNAL already has.

* Public website: the governed HTTP sensor plus Observation Memory ingestion.
  Identical content re-observed is a temporal refresh with no state change.
* Procurement: the Economic Observation Intelligence strategy and loop, run as a
  single bounded step per lead (no in-loop expansion: the frontier owns that),
  through whichever adapter implements the routed source.

Both return fingerprints, POTENTIAL candidates and hints. Neither admits
evidence, decides fit or writes canonical state.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

from application.economic_discovery.brain_contracts import TypingDimensionContract
from application.economic_discovery.observation_memory import ObservationMemory
from application.observation_intelligence.catalog import QUESTIONS
from application.observation_intelligence.contracts import (
    MarketRole,
    MarketScope,
    ObservationBudget,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    XeedObservationContext,
)
from application.observation_intelligence.coverage import EvidenceCoverageMap
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.loop import (
    SourceObservationPort,
    code_within,
    regional_follow_ups,
    run_observation_loop,
)
from application.observation_intelligence.registry import SourceRegistry
from application.observation_intelligence.strategy import (
    ObservationAction,
    StopPolicy,
    build_strategy,
)
from application.observation_runtime.families import LeadKind, ObservationFamily
from application.observation_runtime.ports import (
    AcquiredEvidence,
    Acquisition,
    AcquisitionRequest,
    LeadHint,
    XeedAttention,
)
from application.source_acquisition.contracts import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
)
from application.source_acquisition.runtime import ingest_source_observation
from domain.xignal import XignalEpistemicState

_K = LeadKind


class WebSourceSensor(Protocol):
    def observe(
        self, request: SourceRequest, policy: SourceDispatchPolicy
    ) -> SourceObservation: ...


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class PublicWebsiteAcquirer:
    """The Xeed's own public web, fetched once per URL per tick for every family that needs it."""

    def __init__(
        self,
        *,
        sensor: WebSourceSensor,
        policy_for: Callable[[str], SourceDispatchPolicy | None],
        memory: ObservationMemory,
        contracts: tuple[TypingDimensionContract, ...] = (),
    ) -> None:
        self._sensor = sensor
        self._policy_for = policy_for
        self._memory = memory
        self._contracts = contracts

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return f"{request.source.source_id}:{request.lead.target}"

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        policy = self._policy_for(request.lead.target)
        return 1 if policy is None else 1 + policy.max_redirects

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        lead = request.lead
        policy = self._policy_for(lead.target)
        if policy is None or policy.disposition is not DispatchDisposition.ALLOW:
            return Acquisition(0, 0, None, blocked="NO_DISPATCH_POLICY_FOR_TARGET")
        slot = "website" if lead.kind in {_K.WEBSITE, _K.OFFER_DECLARATION} else "site-structure"
        source_request = SourceRequest(
            # Stable per Xeed and URL: the same content re-observed is the same observation.
            request_id="aor-" + _digest(lead.xeed_id, lead.target)[:24],
            subject_id=lead.xeed_id,
            observation_slot=slot,
            target_uri=lead.target,
            source_type=request.source.source_id,
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            policy_version=policy.policy_version,
        )
        try:
            observation = self._sensor.observe(source_request, policy)
        except (OSError, ValueError) as error:
            return Acquisition(1, 0, None, failure=f"SENSOR:{type(error).__name__}")
        requests = len(observation.redirect_chain)
        if observation.failure_state is not None:
            return Acquisition(requests, 0, None, failure=observation.failure_state)
        ingest_source_observation(
            memory=self._memory,
            request=source_request,
            observation=observation,
            contracts=self._contracts,
        )
        key = f"web:{lead.target}"
        evidence = AcquiredEvidence(
            key=key,
            fingerprint=observation.body_fingerprint or observation.observation_fingerprint,
            observed_at=observation.retrieved_at,
            provenance_ref=observation.raw_observation_ref,
        )
        hints: list[LeadHint] = []
        if lead.kind is _K.WEBSITE:
            parts = urlsplit(observation.final_uri)
            origin = f"{parts.scheme}://{parts.netloc}"
            for path in ("/robots.txt", "/sitemap.xml"):
                hints.append(
                    LeadHint(_K.SITE_STRUCTURE, origin + path, None, (key,), "SITE_REACHABLE")
                )
            hints.append(
                LeadHint(_K.SEARCH_VISIBILITY, parts.netloc, None, (key,), "SITE_REACHABLE")
            )
            hints.append(
                LeadHint(
                    _K.GENERATIVE_VISIBILITY,
                    request.attention.organization_name,
                    None,
                    (key,),
                    "SITE_REACHABLE",
                )
            )
        return Acquisition(requests, 0, None, evidence=(evidence,), hints=tuple(hints))


#: Lead kind -> the Economic Observation Intelligence question it executes.
PROCUREMENT_QUESTIONS: dict[LeadKind, str] = {
    _K.OPEN_DEMAND: "compatible-public-tenders",
    _K.REGIONAL_DEMAND: "compatible-public-tenders",
    _K.BUYER_OPEN_DEMAND: "compatible-public-tenders",
    _K.MARKET_DEMAND: "revealed-public-demand",
    _K.AWARD_COAPPEARANCE: "revealed-public-demand",
    _K.AWARD_ACTIVITY: "revealed-public-demand",
    _K.RECURRING_BUYER: "revealed-public-demand",
}
_BUYER_SCOPED = frozenset({_K.RECURRING_BUYER, _K.BUYER_OPEN_DEMAND})
_REVEALED = "REVEALED_CODES:"


@dataclass
class _Capturing:
    port: SourceObservationPort
    findings: list[SourceFindings] = field(default_factory=list)

    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings:
        result = self.port.observe(action, source)
        self.findings.append(result)
        return result


def _record_fingerprint(record: ProcurementRecord) -> str:
    return _digest(
        record.record_id,
        record.title,
        record.buyer_name or "",
        record.deadline or "",
        record.published_at.isoformat(),
        ",".join(f"{c.scheme}:{c.code}" for c in sorted(record.demand_codes)),
        ",".join(sorted(record.winners)),
    )


def _revealed(lead_reasons: tuple[str, ...]) -> tuple[TaxonomyCode, ...]:
    reason = next((r for r in lead_reasons if r.startswith(_REVEALED)), "")
    return tuple(
        TaxonomyCode(scheme, code)
        for item in reason.removeprefix(_REVEALED).split(",")
        if ":" in item
        for scheme, code in [item.split(":", 1)]
    )


class ProcurementAcquirer:
    """Any adopted source implementing the procurement capabilities, behind its own adapter."""

    def __init__(
        self,
        *,
        port: SourceObservationPort,
        contexts: Callable[[XeedAttention, datetime], XeedObservationContext | None],
        registry: SourceRegistry | None = None,
        max_requests_per_lead: int = 4,
    ) -> None:
        if max_requests_per_lead < 1:
            raise ValueError("a procurement lead needs at least one request")
        self._port = port
        self._contexts = contexts
        self._registry = registry or SourceRegistry()
        self._max = max_requests_per_lead
        self._questions = {q.question_id: q for q in QUESTIONS}

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        lead = request.lead
        geography = "" if lead.geography is None else lead.geography.code
        buyer = lead.target if lead.kind in _BUYER_SCOPED else ""
        revealed = ",".join(f"{c.scheme}:{c.code}" for c in _revealed(lead.reasons))
        question = PROCUREMENT_QUESTIONS.get(lead.kind, lead.kind.value)
        return f"{request.source.source_id}:{question}:{geography}:{buyer}:{revealed}"

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return self._max

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        lead, source = request.lead, request.source
        question_id = PROCUREMENT_QUESTIONS.get(lead.kind)
        if question_id is None or lead.geography is None:
            return Acquisition(0, 0, None, blocked=f"NOT_A_PROCUREMENT_QUESTION:{lead.kind.value}")
        context = self._contexts(request.attention, request.as_of)
        if context is None or not any(c.demand_codes for c in context.capabilities):
            # Without observed capabilities there is nothing to match demand against.
            return Acquisition(0, 0, None, blocked="NO_OBSERVED_CAPABILITY_CONTEXT")
        market = next(
            (m for m in context.markets if m.geography == lead.geography),
            MarketScope(
                lead.geography,
                frozenset({MarketRole.PUBLIC_BUYERS}),
                XignalEpistemicState.POTENTIAL,
            ),
        )
        # Every returned record is reported; the runtime, not the loop, decides what is new.
        scoped = replace(context, as_of=request.as_of, markets=(market,), evidence_seen=frozenset())
        budget = ObservationBudget(
            max_requests=request.max_requests,
            max_amount_microunits=0,
            max_depth=0,
            max_actions=request.max_requests,
        )
        strategy = build_strategy(
            scoped,
            coverage=EvidenceCoverageMap(max_age=timedelta(days=36_500)),
            budget=budget,
            registry=self._registry,
            questions=(self._questions[question_id],),
            stop_policy=StopPolicy(sufficient_candidates=10**6, max_no_gain_streak=10**6),
        )
        revealed = _revealed(lead.reasons)
        actions = tuple(
            replace(
                a,
                query=replace(
                    a.query, demand_codes=tuple(sorted({*a.query.demand_codes, *revealed}))
                ),
                reasons=(*a.reasons, next(r for r in lead.reasons if r.startswith(_REVEALED))),
            )
            if revealed
            else a
            for a in strategy.actions
            if a.source_id == source.source_id
        )
        if not actions:
            return Acquisition(0, 0, None, blocked="NO_CAPABILITY_CODES_IN_SOURCE_SCHEMES")
        capture = _Capturing(self._port)
        result = run_observation_loop(
            replace(strategy, actions=actions),
            scoped,
            adapters={source.source_id: capture},
            coverage=EvidenceCoverageMap(max_age=timedelta(days=36_500)),
            learning=OperationalLearning(),
            registry=self._registry,
        )
        latency = sum(f.latency_ms or 0 for f in capture.findings) or None
        failures = [f.failure for f in capture.findings if f.failure is not None]
        records = {r.record_id: r for f in capture.findings for r in f.records}
        if failures and not records:
            return Acquisition(
                result.requests, result.amount_microunits, latency, failure=failures[0]
            )
        if lead.kind in _BUYER_SCOPED:
            records = {k: r for k, r in records.items() if r.buyer_name == lead.target}
        retrieved = {r.record_id: f.retrieved_at for f in capture.findings for r in f.records}
        evidence = tuple(
            AcquiredEvidence(
                key=f"{source.source_id}:{record.record_id}",
                fingerprint=_record_fingerprint(record),
                observed_at=retrieved[record.record_id],
                provenance_ref=record.source_url,
            )
            for record in sorted(records.values(), key=lambda r: r.record_id)
        )
        candidates = tuple(c for c in result.candidates if c.record.record_id in records)
        hints = self._hints(lead.kind, actions, scoped, source, tuple(records.values()), candidates)
        return Acquisition(
            result.requests,
            result.amount_microunits,
            latency,
            evidence=evidence,
            candidates=candidates,
            hints=hints,
        )

    def _hints(
        self,
        kind: LeadKind,
        actions: tuple[ObservationAction, ...],
        context: XeedObservationContext,
        source: SourceDescriptor,
        records: tuple[ProcurementRecord, ...],
        candidates: tuple[object, ...],
    ) -> tuple[LeadHint, ...]:
        def key(record: ProcurementRecord) -> str:
            return f"{source.source_id}:{record.record_id}"

        awards = [r for r in records if r.kind is SourceCapability.PUBLIC_PROCUREMENT_AWARDS]
        hints: list[LeadHint] = []
        if kind is _K.RECURRING_BUYER and awards:
            buyer = awards[0].buyer_name or ""
            hints.append(
                LeadHint(
                    _K.BUYER_OPEN_DEMAND,
                    buyer,
                    actions[0].market,
                    tuple(sorted(key(a) for a in awards)),
                    f"BUYER_AWARDED_COMPATIBLE_WORK:{len(awards)}",
                    family=ObservationFamily.DEMAND,
                )
            )
            return tuple(hints)
        for action in actions:
            for follow_up in regional_follow_ups(awards, action, context, source):
                region = follow_up.market
                in_region = tuple(
                    sorted(key(a) for a in awards if any(p.within(region) for p in a.places))
                )
                detail = tuple(
                    r for r in follow_up.reasons if r.startswith(_REVEALED) and r != _REVEALED
                )
                hints.append(
                    LeadHint(
                        _K.REGIONAL_DEMAND,
                        region.code,
                        region,
                        in_region,
                        next(r for r in follow_up.reasons if r.startswith("REGION:")),
                        family=ObservationFamily.DEMAND,
                        detail=detail,
                    )
                )
        if kind is _K.OPEN_DEMAND and candidates:
            # Compatible open demand exists here: do funding programmes create more of it?
            hints.append(
                LeadHint(
                    _K.FUNDING_DEMAND,
                    actions[0].market.code,
                    actions[0].market,
                    tuple(
                        sorted(
                            key(r)
                            for r in records
                            if r.kind is not SourceCapability.PUBLIC_PROCUREMENT_AWARDS
                        )
                    ),
                    f"COMPATIBLE_OPEN_DEMAND:{len(candidates)}",
                )
            )
        codes = [c for capability in context.capabilities for c in capability.demand_codes]
        by_buyer: dict[str, list[ProcurementRecord]] = {}
        for award in awards:
            if award.buyer_name and any(
                code_within(c, w) for c in award.demand_codes for w in codes
            ):
                by_buyer.setdefault(award.buyer_name, []).append(award)
        for buyer, items in sorted(by_buyer.items()):
            if len(items) >= 2:
                hints.append(
                    LeadHint(
                        _K.RECURRING_BUYER,
                        buyer,
                        actions[0].market,
                        tuple(sorted(key(a) for a in items)),
                        f"BUYER_AWARDS_IN_MARKET:{len(items)}",
                        family=ObservationFamily.RELATIONSHIPS,
                    )
                )
        return tuple(hints)


def procurement_acquirers(
    ports: Mapping[str, SourceObservationPort],
    *,
    contexts: Callable[[XeedAttention, datetime], XeedObservationContext | None],
    registry: SourceRegistry | None = None,
    max_requests_per_lead: int = 4,
) -> dict[str, ProcurementAcquirer]:
    """One acquirer per adopted procurement source adapter (TED, PLACSP, SAM.gov...)."""

    return {
        source_id: ProcurementAcquirer(
            port=port,
            contexts=contexts,
            registry=registry,
            max_requests_per_lead=max_requests_per_lead,
        )
        for source_id, port in sorted(ports.items())
    }
