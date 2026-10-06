"""Adaptive, budgeted observation loop: observe → learn what to observe → stop.

Each step executes the highest-priority action through the adapter registered
for that concrete source, records what was new, derives POTENTIAL opportunity
candidates and may add follow-up actions through versioned deterministic rules.
It stops on its own for an explicit, recorded reason. Nothing here admits
evidence or writes canonical state.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from application.observation_intelligence.catalog import QUESTIONS, REGIONAL_DEPTH
from application.observation_intelligence.contracts import (
    Band,
    OpportunityFamily,
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    XeedObservationContext,
    geo,
)
from application.observation_intelligence.coverage import EvidenceCoverageMap
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.registry import SourceRegistry
from application.observation_intelligence.strategy import (
    ActionPriority,
    ObservationAction,
    ObservationStrategy,
    action_order,
    reobservation_interval,
)
from domain.xignal import XignalEpistemicState

OBSERVED = XignalEpistemicState.OBSERVED

FOLLOW_UP_RULES_VERSION = "eoil-follow-up-2026-10-06.2"
UNASSESSED_CONTEXT = (
    "technical requirements",
    "eligibility and solvency",
    "available capacity",
    "price competitiveness",
    "incumbent supplier",
)


class SourceObservationPort(Protocol):
    def observe(self, action: ObservationAction, source: SourceDescriptor) -> SourceFindings: ...


class StopReason(StrEnum):
    SUFFICIENT_EVIDENCE = "SUFFICIENT_EVIDENCE"
    NO_MARGINAL_GAIN = "NO_MARGINAL_GAIN"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    SOURCES_EXHAUSTED = "SOURCES_EXHAUSTED"
    IRREDUCIBLE_WITH_ADOPTED_SOURCES = "IRREDUCIBLE_WITH_ADOPTED_SOURCES"


#: Code length that identifies a sibling group per classification scheme.
_GROUP_LENGTH = {"CPV": 5, "NAICS": 5, "PSC": 3}


def code_within(narrow: TaxonomyCode, broad: TaxonomyCode) -> bool:
    """``narrow`` is ``broad`` or one of its descendants (CPV nests by trailing zeros)."""

    if narrow.scheme != broad.scheme:
        return False
    if broad.scheme == "CPV":
        return narrow.code.startswith(broad.code.rstrip("0") or broad.code)
    return narrow.within(broad)


def same_group(left: TaxonomyCode, right: TaxonomyCode) -> bool:
    """Siblings in one classification group (CPV 45261210 and 45261215)."""

    length = _GROUP_LENGTH.get(left.scheme)
    return (
        length is not None
        and left.scheme == right.scheme
        and left.code[:length] == right.code[:length]
    )


def region_of(place: TaxonomyCode) -> TaxonomyCode | None:
    """The regional level of a jurisdiction path, per its tree's declared depth."""

    if place.scheme != "GEO":
        return None
    segments = place.code.split("/")
    depth = REGIONAL_DEPTH.get(segments[0])
    if depth is None or len(segments) < depth:
        return None
    return geo("/".join(segments[:depth]))


@dataclass(frozen=True, slots=True)
class OpportunityCandidate:
    """Plausible fit between published demand and observed capability. Never OBSERVED."""

    candidate_id: str
    xeed_id: str
    record: ProcurementRecord
    market: TaxonomyCode
    capability_ids: tuple[str, ...]
    matched_codes: tuple[TaxonomyCode, ...]
    why_looked: tuple[str, ...]
    missing_context: tuple[str, ...]
    observed_at: datetime
    match_basis: tuple[str, ...]
    opportunity_family: OpportunityFamily
    demand_form: str
    epistemic_state: XignalEpistemicState = XignalEpistemicState.POTENTIAL

    def __post_init__(self) -> None:
        if self.epistemic_state is XignalEpistemicState.OBSERVED:
            raise ValueError("an opportunity candidate can never be OBSERVED")
        if not self.capability_ids or not self.matched_codes or not self.missing_context:
            raise ValueError("an opportunity candidate needs its capability basis and limits")


@dataclass(frozen=True, slots=True)
class LoopStep:
    action: ObservationAction
    requests: int
    new_records: int
    duplicates: int
    candidates_added: int
    follow_ups: tuple[str, ...]
    failure: str | None


@dataclass(frozen=True, slots=True)
class LoopResult:
    xeed_id: str
    stop_reason: StopReason
    stop_detail: str
    steps: tuple[LoopStep, ...]
    candidates: tuple[OpportunityCandidate, ...]
    revealed_buyers: tuple[tuple[str, str], ...]
    requests: int
    amount_microunits: int
    unexecuted_actions: tuple[ObservationAction, ...]
    reobservation: tuple[tuple[str, str, str], ...]


@dataclass
class _State:
    seen: set[str] = field(default_factory=set)
    candidates: dict[str, OpportunityCandidate] = field(default_factory=dict)
    buyers: dict[str, str] = field(default_factory=dict)
    queries: set[tuple[str, tuple[object, ...]]] = field(default_factory=set)
    searched: set[tuple[str, str, str | None]] = field(default_factory=set)
    requests: int = 0
    amount: int = 0
    no_gain_streak: int = 0


def _revealed_codes(action: ObservationAction) -> tuple[TaxonomyCode, ...]:
    reason = next((r for r in action.reasons if r.startswith("REVEALED_CODES:")), "")
    return tuple(
        TaxonomyCode(scheme, code)
        for item in reason.removeprefix("REVEALED_CODES:").split(",")
        if ":" in item
        for scheme, code in [item.split(":", 1)]
    )


def _procurement_candidate(
    record: ProcurementRecord,
    action: ObservationAction,
    context: XeedObservationContext,
    chain: tuple[str, ...],
    observed_at: datetime,
) -> OpportunityCandidate | None:
    if record.kind is not SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES:
        return None
    # A closed call is evidence of demand, not an open opportunity; unknown is not open.
    if record.deadline is None or record.deadline[:10] < context.as_of.date().isoformat():
        return None
    if not any(place.within(action.market) for place in record.places):
        return None
    revealed = _revealed_codes(action)
    matched: dict[str, set[TaxonomyCode]] = defaultdict(set)
    basis: set[str] = set()
    for capability in context.capabilities:
        for offered in record.demand_codes:
            # Demand must sit inside what the capability covers; a broad parent code
            # (all "installation work") is too vague to count as compatible demand.
            if any(code_within(offered, wanted) for wanted in capability.demand_codes):
                matched[capability.capability_id].add(offered)
                basis.add("DIRECT_CAPABILITY_CODE")
            elif capability.capability_id == action.capability_id and any(
                code_within(offered, code) for code in revealed
            ):
                matched[capability.capability_id].add(offered)
                basis.add("ADJACENT_CODE_REVEALED_BY_AWARDS")
    if not matched:
        return None
    digest = hashlib.sha256(f"{context.xeed_id}|{record.source_id}|{record.record_id}".encode())
    return OpportunityCandidate(
        candidate_id="opportunity-candidate:" + digest.hexdigest()[:24],
        xeed_id=context.xeed_id,
        record=record,
        market=action.market,
        capability_ids=tuple(sorted(matched)),
        matched_codes=tuple(sorted({code for codes in matched.values() for code in codes})),
        why_looked=chain,
        missing_context=UNASSESSED_CONTEXT,
        observed_at=observed_at,
        match_basis=tuple(sorted(basis)),
        opportunity_family=OpportunityFamily.PUBLIC_PROCUREMENT,
        demand_form="OPEN_CALL_FOR_TENDER",
    )


DemandInterpreter = Callable[
    [Any, ObservationAction, XeedObservationContext, tuple[str, ...], datetime],
    "OpportunityCandidate | None",
]

#: Evidence type -> deterministic interpreter of plausible demand. Each opportunity
#: family adds its own normalized evidence and interpreter; procurement is one entry.
DEMAND_INTERPRETERS: dict[type, DemandInterpreter] = {
    ProcurementRecord: _procurement_candidate,
}


def _regional_follow_ups(
    awards: list[ProcurementRecord],
    action: ObservationAction,
    context: XeedObservationContext,
    source: SourceDescriptor,
) -> list[ObservationAction]:
    """Relevant awards concentrated in one region → look for open demand from similar buyers.

    Sibling codes the awarded buyers used next to the capability's own codes are
    proposed as adjacent demand to search for; they never widen to a parent code.
    """

    targets = [
        c
        for c in context.capabilities
        if action.capability_id is None or c.capability_id == action.capability_id
    ]
    capability_codes = [
        code
        for capability in targets
        for code in capability.demand_codes
        if code.scheme in source.classification_systems
    ]
    regions: Counter[TaxonomyCode] = Counter()
    buyers: dict[TaxonomyCode, set[str]] = defaultdict(set)
    revealed: dict[TaxonomyCode, set[TaxonomyCode]] = defaultdict(set)
    for award in awards:
        if not any(code_within(c, w) for c in award.demand_codes for w in capability_codes):
            continue
        for region in {
            r for place in award.places if (r := region_of(place)) and r.within(action.market)
        }:
            if region == action.market:
                continue
            regions[region] += 1
            if award.buyer_name:
                buyers[region].add(award.buyer_name)
            revealed[region] |= {
                code
                for code in award.demand_codes
                if not any(code_within(code, w) for w in capability_codes)
                and any(same_group(code, w) for w in capability_codes)
            }
    follow_ups: list[ObservationAction] = []
    for region, count in sorted(regions.items(), key=lambda item: (-item[1], item[0])):
        if count < 2 or not source.covers(region):
            continue
        codes = tuple(sorted({*capability_codes, *revealed[region]}))
        suffix = f":{action.capability_id}" if action.capability_id else ""
        follow_ups.append(
            ObservationAction(
                action_id=(
                    f"compatible-public-tenders@{region.code}:{source.source_id}{suffix}:from-awards"
                ),
                question_id="compatible-public-tenders",
                market=region,
                source_id=source.source_id,
                query=QuerySpec(
                    demand_codes=codes,
                    geographies=(region,),
                    capabilities=frozenset({SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES}),
                    published_since=action.query.published_since,
                    open_on=context.as_of,
                ),
                priority=ActionPriority(
                    Band.HIGH, Band.HIGH, action.priority.source_quality, action.priority.cost
                ),
                reasons=(
                    f"RULE:{FOLLOW_UP_RULES_VERSION}:AWARD_CONCENTRATION",
                    f"REGION:{region.code}:{count}_AWARDS",
                    "BUYERS:" + "|".join(sorted(buyers[region])),
                    "REVEALED_CODES:"
                    + ",".join(f"{c.scheme}:{c.code}" for c in sorted(revealed[region])),
                ),
                depth=action.depth + 1,
                reobserve_after=action.reobserve_after,
                parent_action_id=action.action_id,
                capability_id=action.capability_id,
                market_observed=action.market_observed,
            )
        )
    return follow_ups


def run_observation_loop(
    strategy: ObservationStrategy,
    context: XeedObservationContext,
    *,
    adapters: Mapping[str, SourceObservationPort],
    coverage: EvidenceCoverageMap,
    learning: OperationalLearning,
    registry: SourceRegistry | None = None,
) -> LoopResult:
    registry = registry or SourceRegistry()
    questions = {question.question_id: question for question in QUESTIONS}
    budget, policy = strategy.budget, strategy.stop_policy
    queue = list(strategy.actions)
    state = _State(seen=set(context.evidence_seen))
    steps: list[LoopStep] = []
    stop: tuple[StopReason, str] | None = None
    executed = 0
    # Sufficiency needs every capability's highest-value question searched in every
    # market where the Xeed is OBSERVED; an incidental match is not characterization.
    observed_markets = {m.geography.code for m in context.markets if m.state is OBSERVED}
    top_value = max((a.priority.economic_value for a in strategy.actions), default=Band.UNKNOWN)
    required = {
        (a.question_id, a.market.code, a.capability_id)
        for a in strategy.actions
        if a.priority.economic_value == top_value and a.market.code in observed_markets
    }

    while queue:
        action = queue.pop(0)
        query_key = (action.source_id, action.query.key)
        if query_key in state.queries or action.depth > budget.max_depth:
            continue
        source = registry.get(action.source_id)
        adapter = adapters.get(source.source_id)
        if not source.routable or adapter is None:
            steps.append(LoopStep(action, 0, 0, 0, 0, (), "NO_ROUTABLE_ADAPTER"))
            continue
        if executed >= budget.max_actions or state.requests + 1 > budget.max_requests:
            queue.insert(0, action)
            stop = (StopReason.BUDGET_EXHAUSTED, f"requests={state.requests} actions={executed}")
            break
        state.queries.add(query_key)
        findings = adapter.observe(action, source)
        executed += 1
        state.requests += findings.requests
        state.amount += findings.amount_microunits or 0
        stats = learning.for_source(source.source_id)
        stats.attempts += 1
        stats.requests += findings.requests
        stats.latency_ms += findings.latency_ms or 0
        stats.amount_microunits += findings.amount_microunits or 0
        if findings.failure is not None:
            stats.failures += 1
            steps.append(LoopStep(action, findings.requests, 0, 0, 0, (), findings.failure))
            continue

        new = [r for r in findings.records if r.record_id not in state.seen]
        state.seen.update(r.record_id for r in new)
        stats.records += len(findings.records)
        stats.new_records += len(new)
        stats.duplicates += len(findings.records) - len(new)
        coverage.record(
            question_id=action.question_id,
            market=action.market,
            source_id=source.source_id,
            evidence_ids=tuple(r.record_id for r in new),
            observed_at=findings.retrieved_at,
        )
        chain = (
            *action.reasons,
            f"STRATEGY:{strategy.policy_version}",
            f"ACTION:{action.action_id}",
        )
        added = 0
        for record in new:
            interpret = DEMAND_INTERPRETERS.get(type(record))
            candidate = (
                None
                if interpret is None
                else interpret(record, action, context, chain, findings.retrieved_at)
            )
            if candidate is not None and candidate.candidate_id not in state.candidates:
                state.candidates[candidate.candidate_id] = candidate
                added += 1
            if record.kind is SourceCapability.PUBLIC_PROCUREMENT_AWARDS and record.buyer_name:
                state.buyers[record.buyer_name] = record.record_id
        stats.candidates += added
        follow_ups = [
            f
            for f in _regional_follow_ups(
                [r for r in new if r.kind is SourceCapability.PUBLIC_PROCUREMENT_AWARDS],
                action,
                context,
                source,
            )
            if (f.source_id, f.query.key) not in state.queries
        ]
        stats.follow_ups += len(follow_ups)
        queue.extend(follow_ups)
        queue.sort(key=action_order)
        steps.append(
            LoopStep(
                action,
                findings.requests,
                len(new),
                len(findings.records) - len(new),
                added,
                tuple(f.action_id for f in follow_ups),
                None,
            )
        )

        # A first search of a question x market x capability is informative even when
        # empty (coverage leaves UNKNOWN); only redundant searches count as no gain.
        combo = (action.question_id, action.market.code, action.capability_id)
        informative = bool(new) or combo not in state.searched
        state.searched.add(combo)
        state.no_gain_streak = 0 if informative else state.no_gain_streak + 1
        if state.no_gain_streak >= policy.max_no_gain_streak:
            stop = (
                StopReason.NO_MARGINAL_GAIN,
                f"{state.no_gain_streak} steps without new evidence",
            )
            break
        pending_follow_up = any(a.parent_action_id is not None for a in queue)
        covered = {c for candidate in state.candidates.values() for c in candidate.capability_ids}
        every_capability = all(
            c.capability_id in covered for c in context.capabilities if c.demand_codes
        )
        if (
            len(state.candidates) >= policy.sufficient_candidates
            and every_capability
            and required <= state.searched
            and not pending_follow_up
        ):
            stop = (
                StopReason.SUFFICIENT_EVIDENCE,
                f"{len(state.candidates)} candidates characterized; no pending adaptive step",
            )
            break

    if stop is None:
        if strategy.gaps:
            stop = (
                StopReason.IRREDUCIBLE_WITH_ADOPTED_SOURCES,
                f"{len(strategy.gaps)} question x market gaps have no adopted source",
            )
        else:
            stop = (StopReason.SOURCES_EXHAUSTED, "no remaining action with expected gain")

    active = bool(state.candidates)
    reobservation = tuple(
        sorted(
            {
                (
                    step.action.question_id,
                    step.action.market.code,
                    str(
                        reobservation_interval(
                            registry.get(step.action.source_id),
                            questions[step.action.question_id],
                            active_opportunity=active,
                        )
                    ),
                )
                for step in steps
                if step.failure is None
            }
        )
    )
    return LoopResult(
        xeed_id=context.xeed_id,
        stop_reason=stop[0],
        stop_detail=stop[1],
        steps=tuple(steps),
        candidates=tuple(
            sorted(
                state.candidates.values(),
                key=lambda c: (c.record.published_at, c.record.record_id),
            )
        ),
        revealed_buyers=tuple(sorted(state.buyers.items())),
        requests=state.requests,
        amount_microunits=state.amount,
        unexecuted_actions=tuple(queue),
        reobservation=reobservation,
    )
