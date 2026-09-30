"""Provider-neutral control plane for AXIGNAL Prime cognitive work.

The Prime control plane decides *what kind of mechanism* may handle an impacted
semantic dimension. It does not select a concrete model provider, perform
research, admit evidence, or write canonical AXIGLAND state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    StateChange,
    TypingDimensionContract,
)
from application.economic_discovery.planner import (
    DimensionWork,
    assess_dimension_work,
    plan_dimension_work,
)
from application.economic_discovery.research_value import (
    ResearchValueDecision,
    ResearchValueDisposition,
)


class PrimeRoute(StrEnum):
    """Mechanism families allowed to resolve cognitive work."""

    DETERMINISTIC = "DETERMINISTIC"
    STRUCTURED_EVALUATOR = "STRUCTURED_EVALUATOR"
    ADAPTIVE_RESEARCH = "ADAPTIVE_RESEARCH"


@dataclass(frozen=True, slots=True)
class DimensionRoutingPolicy:
    """Versioned AXIGNAL-owned routing policy for one semantic dimension."""

    dimension_id: str
    version: str
    answerable_route: PrimeRoute

    def __post_init__(self) -> None:
        if not self.dimension_id.strip() or not self.version.strip():
            raise ValueError("dimension routing policy identity is required")
        if self.answerable_route is PrimeRoute.ADAPTIVE_RESEARCH:
            raise ValueError(
                "answerable dimensions must use deterministic or structured evaluation"
            )


@dataclass(frozen=True, slots=True)
class PrimeWorkItem:
    """One governed unit of work emitted by the Prime control plane."""

    dimension_id: str
    disposition: DimensionDisposition
    route: PrimeRoute | None
    policy_version: str
    missing_requirements: tuple[str, ...]
    research_disposition: ResearchValueDisposition | None = None
    research_policy_id: str | None = None
    research_policy_version: str | None = None
    research_context_fingerprint: str | None = None
    research_reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.dimension_id.strip() or not self.policy_version.strip():
            raise ValueError("prime work item identity is required")
        if self.disposition is DimensionDisposition.NOT_ANSWERABLE:
            if not self.missing_requirements:
                raise ValueError("non-answerable work requires explicit missing information")
            if self.research_disposition is None:
                raise ValueError("non-answerable work requires research-value disposition")
            if any(
                value is None or not value.strip()
                for value in (
                    self.research_policy_id,
                    self.research_policy_version,
                    self.research_context_fingerprint,
                )
            ):
                raise ValueError("non-answerable work requires research-value provenance")
            if not self.research_reason_codes:
                raise ValueError("research-value decision requires explicit reasons")
            if self.research_disposition is ResearchValueDisposition.RESEARCH_NOW:
                if self.route is not PrimeRoute.ADAPTIVE_RESEARCH:
                    raise ValueError("research-now work must route to adaptive research")
            elif self.route is not None:
                raise ValueError("non-research gap cannot carry an execution route")
        else:
            if self.missing_requirements:
                raise ValueError("answerable work cannot carry missing requirements")
            if self.route is None:
                raise ValueError("answerable work requires an execution route")
            if (
                self.research_disposition is not None
                or self.research_policy_id is not None
                or self.research_policy_version is not None
                or self.research_context_fingerprint is not None
                or self.research_reason_codes
            ):
                raise ValueError("answerable work cannot carry research-value decision")


@dataclass(frozen=True, slots=True)
class PrimeControlPlan:
    """Deterministic plan for the dimensions affected by one state change."""

    subject_id: str
    state_fingerprint: str
    items: tuple[PrimeWorkItem, ...]

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.state_fingerprint.strip():
            raise ValueError("prime control plan identity is required")
        ids = [item.dimension_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("prime control plan cannot duplicate dimensions")


def _route_work(
    *,
    subject_id: str,
    state_fingerprint: str,
    work: tuple[DimensionWork, ...],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
    research_decisions: tuple[ResearchValueDecision, ...] = (),
) -> PrimeControlPlan:
    policies = {policy.dimension_id: policy for policy in routing_policies}
    if len(policies) != len(routing_policies):
        raise ValueError("dimension routing policies must be unique")
    decisions = {decision.dimension_id: decision for decision in research_decisions}
    if len(decisions) != len(research_decisions):
        raise ValueError("research-value decisions must be unique")

    items: list[PrimeWorkItem] = []
    for dimension in work:
        policy = policies.get(dimension.dimension_id)
        if policy is None:
            raise ValueError(
                f"missing Prime routing policy for dimension {dimension.dimension_id!r}"
            )

        research_disposition: ResearchValueDisposition | None = None
        research_policy_id: str | None = None
        research_policy_version: str | None = None
        research_context_fingerprint: str | None = None
        research_reason_codes: tuple[str, ...] = ()
        if dimension.disposition is DimensionDisposition.NOT_ANSWERABLE:
            decision = decisions.get(dimension.dimension_id)
            if decision is None:
                raise ValueError(
                    f"missing Research Value decision for dimension {dimension.dimension_id!r}"
                )
            if (
                decision.subject_id != subject_id
                or decision.state_fingerprint != state_fingerprint
                or decision.missing_requirements != dimension.missing_requirements
            ):
                raise ValueError("Research Value decision does not match current gap state")
            research_disposition = decision.disposition
            research_policy_id = decision.policy_id
            research_policy_version = decision.policy_version
            research_context_fingerprint = decision.context_fingerprint
            research_reason_codes = tuple(reason.value for reason in decision.reason_codes)
            route = (
                PrimeRoute.ADAPTIVE_RESEARCH
                if decision.disposition is ResearchValueDisposition.RESEARCH_NOW
                else None
            )
        elif dimension.disposition is DimensionDisposition.ANSWERABLE:
            route = policy.answerable_route
        else:
            raise ValueError("pre-provider Prime planning cannot route NOT_APPLICABLE dimensions")

        items.append(
            PrimeWorkItem(
                dimension_id=dimension.dimension_id,
                disposition=dimension.disposition,
                route=route,
                policy_version=policy.version,
                missing_requirements=dimension.missing_requirements,
                research_disposition=research_disposition,
                research_policy_id=research_policy_id,
                research_policy_version=research_policy_version,
                research_context_fingerprint=research_context_fingerprint,
                research_reason_codes=research_reason_codes,
            )
        )

    return PrimeControlPlan(
        subject_id=subject_id,
        state_fingerprint=state_fingerprint,
        items=tuple(items),
    )


def build_prime_control_plan(
    *,
    change: StateChange,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
    research_decisions: tuple[ResearchValueDecision, ...] = (),
) -> PrimeControlPlan:
    """Route impacted dimensions without delegating routing authority to a model."""

    return _route_work(
        subject_id=change.subject_id,
        state_fingerprint=change.current_fingerprint,
        work=plan_dimension_work(
            change=change,
            contracts=contracts,
            available_state_fields=available_state_fields,
        ),
        routing_policies=routing_policies,
        research_decisions=research_decisions,
    )


def build_initial_prime_control_plan(
    *,
    subject_id: str,
    state_fingerprint: str,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
) -> PrimeControlPlan:
    """Route only answerable initial dimensions; retain gaps outside Prime for policy."""

    if not subject_id.strip() or not state_fingerprint.strip():
        raise ValueError("initial Prime plan identity is required")

    assessment = assess_dimension_work(
        contracts=contracts,
        available_state_fields=available_state_fields,
    )
    answerable = tuple(
        item for item in assessment if item.disposition is DimensionDisposition.ANSWERABLE
    )
    return _route_work(
        subject_id=subject_id,
        state_fingerprint=state_fingerprint,
        work=answerable,
        routing_policies=routing_policies,
    )
