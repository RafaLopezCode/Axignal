"""Build an inspectable, budgeted ObservationStrategy before acquiring anything.

capability + economic question + jurisdiction + buyer roles
    → abstract SourceCapability → concrete sources (registry resolution)
    → query in each source's own classification scheme.

Priority is a dominance ordering over explicit ordinal dimensions, each with a
reason (MASTER §53.3: no opaque universal score). Unknown rights or cost make a
source ineligible rather than cheap.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.observation_intelligence.catalog import QUESTIONS
from application.observation_intelligence.contracts import (
    Band,
    CapabilityHypothesis,
    EconomicQuestion,
    MarketScope,
    ObservationBudget,
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    XeedObservationContext,
)
from application.observation_intelligence.coverage import CoverageState, EvidenceCoverageMap
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.registry import (
    SourceDiscoveryRequest,
    SourceRegistry,
    SourceResolution,
)
from domain.xignal import XignalEpistemicState

POLICY_VERSION = "eoil-routing-2026-10-06.2"

# How far back each capability's evidence is still economically actionable.
RECENCY_WINDOWS: dict[SourceCapability, timedelta] = {
    SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES: timedelta(days=60),
    SourceCapability.PUBLIC_PROCUREMENT_AWARDS: timedelta(days=365),
}


@dataclass(frozen=True, slots=True)
class ActionPriority:
    economic_value: Band
    information_gain: Band
    source_quality: Band
    cost: Band

    @property
    def order_key(self) -> tuple[int, int, int, int]:
        # Dominance order: value first, then what we would learn, then trust, then cost.
        return (-self.economic_value, -self.information_gain, -self.source_quality, self.cost)


@dataclass(frozen=True, slots=True)
class ObservationAction:
    action_id: str
    question_id: str
    market: TaxonomyCode
    source_id: str
    query: QuerySpec
    priority: ActionPriority
    reasons: tuple[str, ...]
    depth: int
    reobserve_after: timedelta
    parent_action_id: str | None = None
    # The Xeed capability this action looks for, when the question is classification-driven.
    capability_id: str | None = None
    market_observed: bool = False


def action_order(action: ObservationAction) -> tuple[object, ...]:
    """Dominance order, then markets where the Xeed is OBSERVED, then a stable id."""

    return (action.priority.order_key, not action.market_observed, action.action_id)


@dataclass(frozen=True, slots=True)
class CoverageGap:
    """A question and market no routable source can reduce now; feeds source discovery."""

    question_id: str
    market: TaxonomyCode
    reason: str
    candidate_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Why each concrete source was or was not chosen for one question and market."""

    question_id: str
    market: TaxonomyCode
    resolution: SourceResolution
    selected: tuple[tuple[str, str], ...]
    skipped: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class StopPolicy:
    sufficient_candidates: int = 3
    max_no_gain_streak: int = 2


@dataclass(frozen=True, slots=True)
class ObservationStrategy:
    xeed_id: str
    as_of: datetime
    catalog_version: str
    policy_version: str
    questions: tuple[tuple[str, str], ...]
    actions: tuple[ObservationAction, ...]
    decisions: tuple[RoutingDecision, ...]
    gaps: tuple[CoverageGap, ...]
    discovery_requests: tuple[SourceDiscoveryRequest, ...]
    budget: ObservationBudget
    stop_policy: StopPolicy

    @property
    def fingerprint(self) -> str:
        payload = {
            "xeed_id": self.xeed_id,
            "as_of": self.as_of.isoformat(),
            "catalog": self.catalog_version,
            "policy": self.policy_version,
            "actions": [
                (a.question_id, a.market.code, a.source_id, repr(a.query.key)) for a in self.actions
            ],
            "gaps": [(g.question_id, g.market.code, g.reason) for g in self.gaps],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()


def _cost_band(source: SourceDescriptor) -> Band:
    if source.cost_per_request_microunits is None:
        return Band.UNKNOWN
    if source.cost_per_request_microunits == 0:
        return source.computational_cost
    return Band.HIGH if source.cost_per_request_microunits > 50_000 else Band.MEDIUM


def _information_gain(state: CoverageState, already_searched: bool) -> tuple[Band, str]:
    if state is CoverageState.UNKNOWN:
        return Band.HIGH, "GAIN_UNKNOWN_QUESTION"
    if state is CoverageState.STALE:
        return Band.MEDIUM, "GAIN_REFRESH_AGED_EVIDENCE"
    if not already_searched:
        return Band.MEDIUM, "GAIN_NEW_SOURCE_FOR_COVERED_QUESTION"
    return Band.LOW, "GAIN_ALREADY_SEARCHED_CURRENT"


def reobservation_interval(
    source: SourceDescriptor, question: EconomicQuestion, *, active_opportunity: bool
) -> timedelta:
    """Source volatility and economic relevance; an active opportunity tightens it."""

    base = source.expected_change_interval
    if active_opportunity:
        return base
    factor = {Band.HIGH: 1, Band.MEDIUM: 3}.get(question.economic_value, 7)
    return base * factor


def _query(
    question: EconomicQuestion,
    source: SourceDescriptor,
    market: MarketScope,
    context: XeedObservationContext,
    capability: CapabilityHypothesis | None,
) -> QuerySpec | None:
    capabilities = question.requires & source.capabilities
    codes: tuple[TaxonomyCode, ...] = ()
    if capability is not None:
        # The capability, expressed in this source's own classification system.
        codes = tuple(
            sorted(c for c in capability.demand_codes if c.scheme in source.classification_systems)
        )
        if not codes:
            return None
    windows = [RECENCY_WINDOWS[c] for c in capabilities if c in RECENCY_WINDOWS]
    return QuerySpec(
        demand_codes=codes,
        geographies=(market.geography,),
        capabilities=frozenset(capabilities),
        published_since=context.as_of - max(windows) if windows else None,
        open_on=(
            context.as_of
            if SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES in capabilities
            else None
        ),
    )


def build_strategy(
    context: XeedObservationContext,
    *,
    coverage: EvidenceCoverageMap,
    budget: ObservationBudget,
    registry: SourceRegistry | None = None,
    learning: OperationalLearning | None = None,
    stop_policy: StopPolicy | None = None,
    questions: tuple[EconomicQuestion, ...] = QUESTIONS,
) -> ObservationStrategy:
    registry = registry or SourceRegistry()
    learning = learning or OperationalLearning()
    stop_policy = stop_policy or StopPolicy()
    selected_questions: list[tuple[str, str]] = []
    actions: list[ObservationAction] = []
    decisions: list[RoutingDecision] = []
    gaps: list[CoverageGap] = []
    discovery: list[tuple[SourceCapability, TaxonomyCode, str, tuple[str, ...], str]] = []
    for question in questions:
        markets = [m for m in context.markets if m.roles & question.market_roles]
        if not markets:
            continue
        if question.uses_capability_codes and not any(c.demand_codes for c in context.capabilities):
            continue
        roles = sorted({r.value for m in markets for r in m.roles & question.market_roles})
        selected_questions.append((question.question_id, "MARKET_ROLES:" + ",".join(roles)))
        for market in markets:
            for capability in sorted(question.requires):
                resolution = registry.resolve(capability, market.geography)
                chosen: list[tuple[str, str]] = []
                skipped: list[tuple[str, str]] = []
                state = coverage.state(question.question_id, market.geography, as_of=context.as_of)
                targets: list[CapabilityHypothesis | None] = (
                    [c for c in context.capabilities if c.demand_codes]
                    if question.uses_capability_codes
                    else [None]
                )
                for source in resolution.routable:
                    for target in targets:
                        query = _query(question, source, market, context, target)
                        if query is None:
                            skipped.append(
                                (source.source_id, "NO_CAPABILITY_CODES_IN_SOURCE_SCHEMES")
                            )
                            continue
                        gain, gain_reason = _information_gain(
                            state,
                            coverage.searched(
                                question.question_id, market.geography, source.source_id
                            ),
                        )
                        if gain is Band.LOW:
                            skipped.append((source.source_id, gain_reason))
                            continue
                        quality, learned = learning.adjusted_quality(
                            source.source_id,
                            min(source.reliability, source.precision, source.provenance_quality),
                        )
                        reasons = [
                            f"QUESTION:{question.question_id}",
                            f"CAPABILITY:{capability.value}",
                            f"MARKET:{market.geography.code}:{market.state.value}",
                            gain_reason,
                        ]
                        if target is not None:
                            reasons.append(f"XEED_CAPABILITY:{target.capability_id}")
                        if query.demand_codes:
                            schemes = sorted({c.scheme for c in query.demand_codes})
                            reasons.append(
                                f"CLASSIFICATION:{'+'.join(schemes)}:"
                                + ",".join(c.code for c in query.demand_codes)
                            )
                        if learned:
                            reasons.append(learned)
                        chosen.append((source.source_id, gain_reason))
                        suffix = f":{target.capability_id}" if target is not None else ""
                        actions.append(
                            ObservationAction(
                                action_id=(
                                    f"{question.question_id}@{market.geography.code}:"
                                    f"{source.source_id}{suffix}"
                                ),
                                question_id=question.question_id,
                                market=market.geography,
                                source_id=source.source_id,
                                query=query,
                                priority=ActionPriority(
                                    question.economic_value, gain, quality, _cost_band(source)
                                ),
                                reasons=tuple(reasons),
                                depth=0,
                                reobserve_after=reobservation_interval(
                                    source, question, active_opportunity=False
                                ),
                                capability_id=None if target is None else target.capability_id,
                                market_observed=market.state is XignalEpistemicState.OBSERVED,
                            )
                        )
                decisions.append(
                    RoutingDecision(
                        question.question_id,
                        market.geography,
                        resolution,
                        tuple(chosen),
                        tuple(skipped),
                    )
                )
                covered = bool(chosen) or any(r.startswith("GAIN_") for _, r in skipped)
                known = tuple(source_id for source_id, _ in resolution.pending)
                if not covered:
                    reason = (
                        "NO_ADOPTED_SOURCE"
                        if resolution.pending
                        else "NO_SOURCE_FOR_CLASSIFICATION"
                        if resolution.routable
                        else "NO_KNOWN_SOURCE"
                    )
                    gaps.append(CoverageGap(question.question_id, market.geography, reason, known))
                    discovery.append(
                        (capability, market.geography, question.question_id, known, reason)
                    )
                elif (
                    question.uses_capability_codes
                    and not known
                    and all(s.coverage < Band.HIGH for s in resolution.routable)
                ):
                    # Only partial-coverage sources (e.g. above-threshold notices): look for
                    # national/regional implementations instead of treating coverage as complete.
                    discovery.append(
                        (
                            capability,
                            market.geography,
                            question.question_id,
                            known,
                            "PARTIAL_COVERAGE_ONLY",
                        )
                    )
    actions.sort(key=action_order)
    return ObservationStrategy(
        xeed_id=context.xeed_id,
        as_of=context.as_of,
        catalog_version=registry.version,
        policy_version=POLICY_VERSION,
        questions=tuple(selected_questions),
        actions=tuple(actions),
        decisions=tuple(decisions),
        gaps=tuple(gaps),
        discovery_requests=_discovery_requests(discovery, context),
        budget=budget,
        stop_policy=stop_policy,
    )


def _discovery_requests(
    items: list[tuple[SourceCapability, TaxonomyCode, str, tuple[str, ...], str]],
    context: XeedObservationContext,
) -> tuple[SourceDiscoveryRequest, ...]:
    """One governed research ask per capability x jurisdiction, in the Xeed's own schemes."""

    schemes = tuple(sorted({c.scheme for cap in context.capabilities for c in cap.demand_codes}))
    grouped: dict[tuple[SourceCapability, TaxonomyCode], tuple[list[str], set[str], str]] = {}
    for capability, market, question_id, known, reason in items:
        ids, candidates, _ = grouped.setdefault((capability, market), ([], set(), reason))
        ids.append(question_id)
        candidates.update(known)
    return tuple(
        SourceDiscoveryRequest(
            capability, market, schemes, tuple(ids), tuple(sorted(candidates)), reason
        )
        for (capability, market), (ids, candidates, reason) in sorted(
            grouped.items(), key=lambda item: (item[0][0], item[0][1].code)
        )
    )
