"""Temporal Xeed bootstrap controller that hands off to AXIGNAL Prime quickly.

Bootstrap is deliberately short-lived: assess every governed semantic dimension,
handoff answerable work to Prime immediately, and preserve unresolved dimensions as
explicit gaps. Known sources may continue filling those gaps without blocking useful work.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery import (
    DimensionRoutingPolicy,
    PrimeControlPlan,
    TypingDimensionContract,
    build_initial_prime_control_plan,
)
from application.economic_discovery.brain_contracts import DimensionDisposition
from application.economic_discovery.planner import assess_dimension_work
from application.economic_discovery.research_value import (
    ResearchValueDecision,
    ResearchValueDisposition,
)
from application.source_representation import RichSubjectState
from application.xeed_access.organization_reader import AuthorizedXeedOrganization


class BootstrapDisposition(StrEnum):
    ACQUIRE_KNOWN_SOURCES = "ACQUIRE_KNOWN_SOURCES"
    HANDOFF_TO_PRIME = "HANDOFF_TO_PRIME"
    ADAPTIVE_RESEARCH = "ADAPTIVE_RESEARCH"
    RETAIN_UNKNOWN = "RETAIN_UNKNOWN"
    DEFER = "DEFER"
    BLOCKED_BY_BUDGET_OR_RIGHTS = "BLOCKED_BY_BUDGET_OR_RIGHTS"


@dataclass(frozen=True, slots=True)
class BootstrapPolicy:
    policy_id: str
    version: str
    max_known_sources: int = 3

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("bootstrap policy identity is required")
        if self.max_known_sources < 1:
            raise ValueError("bootstrap source budget must be positive")


@dataclass(frozen=True, slots=True)
class BootstrapSourceCandidate:
    candidate_id: str
    subject_id: str
    observation_slot: str
    source_ref: str
    source_type: str
    provides_fields: frozenset[str]
    priority: int = 100

    def __post_init__(self) -> None:
        required = (
            self.candidate_id,
            self.subject_id,
            self.observation_slot,
            self.source_ref,
            self.source_type,
        )
        if any(not value.strip() for value in required):
            raise ValueError("bootstrap source candidate identity is required")
        if not self.provides_fields or any(not field.strip() for field in self.provides_fields):
            raise ValueError("bootstrap source candidate must declare provided fields")
        if self.priority < 0:
            raise ValueError("bootstrap source priority cannot be negative")


@dataclass(frozen=True, slots=True)
class BootstrapDimensionGap:
    dimension_id: str
    missing_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.dimension_id.strip():
            raise ValueError("bootstrap dimension gap identity is required")
        if not self.missing_requirements:
            raise ValueError("bootstrap dimension gap requires missing state")
        if len(set(self.missing_requirements)) != len(self.missing_requirements):
            raise ValueError("bootstrap dimension gap requirements must be unique")
        if any(not requirement.strip() for requirement in self.missing_requirements):
            raise ValueError("bootstrap dimension gap requirements cannot be empty")


@dataclass(frozen=True, slots=True)
class BootstrapPlan:
    xeed_id: str
    subject_id: str
    policy_id: str
    policy_version: str
    state_fingerprint: str
    disposition: BootstrapDisposition
    reused_observation_count: int
    available_state_fields: frozenset[str]
    missing_requirements: tuple[str, ...]
    dimension_gaps: tuple[BootstrapDimensionGap, ...]
    source_candidates: tuple[BootstrapSourceCandidate, ...] = ()
    prime_plan: PrimeControlPlan | None = None
    plan_fingerprint: str = ""

    def __post_init__(self) -> None:
        required = (self.xeed_id, self.subject_id, self.policy_id, self.policy_version)
        if any(not value.strip() for value in required):
            raise ValueError("bootstrap plan identity is required")
        if self.reused_observation_count < 0:
            raise ValueError("reused observation count cannot be negative")
        gap_ids = [gap.dimension_id for gap in self.dimension_gaps]
        if len(gap_ids) != len(set(gap_ids)):
            raise ValueError("bootstrap dimension gaps must be unique")

        if self.disposition is BootstrapDisposition.HANDOFF_TO_PRIME:
            if self.prime_plan is None or not self.prime_plan.items:
                raise ValueError("Prime handoff requires at least one answerable dimension")
        elif self.prime_plan is not None and self.prime_plan.items:
            raise ValueError("only Prime handoff may carry executable Prime work")

        if self.disposition is BootstrapDisposition.ACQUIRE_KNOWN_SOURCES and (
            not self.source_candidates or not self.missing_requirements
        ):
            raise ValueError("source acquisition requires candidates and missing state")
        if self.disposition is BootstrapDisposition.ADAPTIVE_RESEARCH and (
            self.source_candidates or not self.missing_requirements
        ):
            raise ValueError("adaptive research requires unresolved missing state")
        if self.missing_requirements and not self.dimension_gaps:
            raise ValueError("missing bootstrap state requires explicit dimension gaps")
        if not self.missing_requirements and self.dimension_gaps:
            raise ValueError("dimension gaps require missing bootstrap state")
        if not self.plan_fingerprint.strip():
            raise ValueError("bootstrap plan fingerprint is required")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _select_known_sources(
    *,
    subject_id: str,
    missing: tuple[str, ...],
    candidates: tuple[BootstrapSourceCandidate, ...],
    limit: int,
) -> tuple[BootstrapSourceCandidate, ...]:
    missing_set = set(missing)
    eligible = [
        candidate
        for candidate in candidates
        if candidate.subject_id == subject_id
        and bool(candidate.provides_fields.intersection(missing_set))
    ]
    selected: list[BootstrapSourceCandidate] = []
    uncovered = set(missing_set)
    remaining = list(eligible)
    while uncovered and remaining and len(selected) < limit:
        remaining.sort(
            key=lambda item: (
                -len(item.provides_fields.intersection(uncovered)),
                item.priority,
                item.candidate_id,
            )
        )
        chosen = remaining.pop(0)
        if not chosen.provides_fields.intersection(uncovered):
            break
        selected.append(chosen)
        uncovered.difference_update(chosen.provides_fields)
    return tuple(selected)


def _resolve_research_disposition(
    *,
    subject_id: str,
    state_fingerprint: str,
    gaps: tuple[BootstrapDimensionGap, ...],
    decisions: tuple[ResearchValueDecision, ...],
) -> BootstrapDisposition:
    indexed = {decision.dimension_id: decision for decision in decisions}
    if len(indexed) != len(decisions):
        raise ValueError("bootstrap research-value decisions must be unique")

    resolved: list[ResearchValueDisposition] = []
    for gap in gaps:
        decision = indexed.get(gap.dimension_id)
        if decision is None:
            raise ValueError(
                f"missing Research Value decision for bootstrap gap {gap.dimension_id!r}"
            )
        if (
            decision.subject_id != subject_id
            or decision.state_fingerprint != state_fingerprint
            or decision.missing_requirements != gap.missing_requirements
        ):
            raise ValueError("bootstrap Research Value decision does not match current gap")
        resolved.append(decision.disposition)

    if ResearchValueDisposition.RESEARCH_NOW in resolved:
        return BootstrapDisposition.ADAPTIVE_RESEARCH
    if ResearchValueDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS in resolved:
        return BootstrapDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS
    if ResearchValueDisposition.DEFER in resolved:
        return BootstrapDisposition.DEFER
    return BootstrapDisposition.RETAIN_UNKNOWN


def _plan_fingerprint(
    *,
    xeed_id: str,
    subject_id: str,
    policy: BootstrapPolicy,
    state_fingerprint: str,
    disposition: BootstrapDisposition,
    missing: tuple[str, ...],
    gaps: tuple[BootstrapDimensionGap, ...],
    sources: tuple[BootstrapSourceCandidate, ...],
    prime_plan: PrimeControlPlan | None,
    research_decisions: tuple[ResearchValueDecision, ...],
) -> str:
    return _fingerprint(
        {
            "xeed_id": xeed_id,
            "subject_id": subject_id,
            "policy": (policy.policy_id, policy.version),
            "state_fingerprint": state_fingerprint,
            "disposition": disposition.value,
            "missing": missing,
            "gaps": [(gap.dimension_id, gap.missing_requirements) for gap in gaps],
            "sources": [item.candidate_id for item in sources],
            "research_decisions": [
                (
                    item.dimension_id,
                    item.disposition.value,
                    item.policy_id,
                    item.policy_version,
                    item.context_fingerprint,
                )
                for item in research_decisions
            ],
            "prime_items": []
            if prime_plan is None
            else [
                (
                    item.dimension_id,
                    item.disposition.value,
                    None if item.route is None else item.route.value,
                    item.policy_version,
                )
                for item in prime_plan.items
            ],
        }
    )


def build_bootstrap_plan(
    *,
    seed: AuthorizedXeedOrganization,
    rich_state: RichSubjectState,
    reused_observation_count: int,
    policy: BootstrapPolicy,
    known_sources: tuple[BootstrapSourceCandidate, ...],
    contracts: tuple[TypingDimensionContract, ...],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
    research_decisions: tuple[ResearchValueDecision, ...] = (),
) -> BootstrapPlan:
    """Return the shortest governed path from planted Xeed to Prime."""

    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("bootstrap requires an AuthorizedXeedOrganization")

    xeed_id = seed.authorized_xeed.xeed.id
    subject_id = seed.organization.id
    if rich_state.subject_id != subject_id:
        raise ValueError("bootstrap rich state must belong to the Xeed organization")
    if reused_observation_count < 0:
        raise ValueError("reused observation count cannot be negative")
    candidate_ids = [candidate.candidate_id for candidate in known_sources]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("bootstrap source candidate identities must be unique")
    if not contracts:
        raise ValueError("bootstrap requires at least one semantic dimension contract")

    available = rich_state.available_fields
    assessment = assess_dimension_work(
        contracts=contracts,
        available_state_fields=available,
    )
    gaps = tuple(
        BootstrapDimensionGap(
            dimension_id=item.dimension_id,
            missing_requirements=item.missing_requirements,
        )
        for item in assessment
        if item.disposition is DimensionDisposition.NOT_ANSWERABLE
    )
    missing = tuple(
        dict.fromkeys(requirement for gap in gaps for requirement in gap.missing_requirements)
    )
    sources = _select_known_sources(
        subject_id=subject_id,
        missing=missing,
        candidates=known_sources,
        limit=policy.max_known_sources,
    )

    initial_prime_plan = build_initial_prime_control_plan(
        subject_id=subject_id,
        state_fingerprint=rich_state.fingerprint,
        contracts=contracts,
        available_state_fields=available,
        routing_policies=routing_policies,
    )

    prime_plan: PrimeControlPlan | None
    if initial_prime_plan.items:
        prime_plan = initial_prime_plan
        disposition = BootstrapDisposition.HANDOFF_TO_PRIME
    elif sources:
        prime_plan = None
        disposition = BootstrapDisposition.ACQUIRE_KNOWN_SOURCES
    else:
        prime_plan = None
        disposition = _resolve_research_disposition(
            subject_id=subject_id,
            state_fingerprint=rich_state.fingerprint,
            gaps=gaps,
            decisions=research_decisions,
        )

    fingerprint = _plan_fingerprint(
        xeed_id=xeed_id,
        subject_id=subject_id,
        policy=policy,
        state_fingerprint=rich_state.fingerprint,
        disposition=disposition,
        missing=missing,
        gaps=gaps,
        sources=sources,
        prime_plan=prime_plan,
        research_decisions=research_decisions,
    )
    return BootstrapPlan(
        xeed_id=xeed_id,
        subject_id=subject_id,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        state_fingerprint=rich_state.fingerprint,
        disposition=disposition,
        reused_observation_count=reused_observation_count,
        available_state_fields=available,
        missing_requirements=missing,
        dimension_gaps=gaps,
        source_candidates=sources,
        prime_plan=prime_plan,
        plan_fingerprint=fingerprint,
    )
