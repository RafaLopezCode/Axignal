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
from application.economic_discovery.planner import plan_dimension_work


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
    route: PrimeRoute
    policy_version: str
    missing_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.dimension_id.strip() or not self.policy_version.strip():
            raise ValueError("prime work item identity is required")
        if self.disposition is DimensionDisposition.NOT_ANSWERABLE:
            if self.route is not PrimeRoute.ADAPTIVE_RESEARCH:
                raise ValueError("non-answerable work must route to adaptive research")
            if not self.missing_requirements:
                raise ValueError("adaptive research requires explicit missing information")
        elif self.missing_requirements:
            raise ValueError("answerable work cannot carry missing requirements")


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


def build_prime_control_plan(
    *,
    change: StateChange,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
) -> PrimeControlPlan:
    """Route impacted dimensions without delegating routing authority to a model."""

    policies = {policy.dimension_id: policy for policy in routing_policies}
    if len(policies) != len(routing_policies):
        raise ValueError("dimension routing policies must be unique")

    work = plan_dimension_work(
        change=change,
        contracts=contracts,
        available_state_fields=available_state_fields,
    )

    items: list[PrimeWorkItem] = []
    for dimension in work:
        policy = policies.get(dimension.dimension_id)
        if policy is None:
            raise ValueError(
                f"missing Prime routing policy for dimension {dimension.dimension_id!r}"
            )

        if dimension.disposition is DimensionDisposition.NOT_ANSWERABLE:
            route = PrimeRoute.ADAPTIVE_RESEARCH
        elif dimension.disposition is DimensionDisposition.ANSWERABLE:
            route = policy.answerable_route
        else:
            # NOT_APPLICABLE is currently produced only by explicit semantic
            # evaluation, not by the pre-provider answerability gate.
            raise ValueError("pre-provider Prime planning cannot route NOT_APPLICABLE dimensions")

        items.append(
            PrimeWorkItem(
                dimension_id=dimension.dimension_id,
                disposition=dimension.disposition,
                route=route,
                policy_version=policy.version,
                missing_requirements=dimension.missing_requirements,
            )
        )

    return PrimeControlPlan(
        subject_id=change.subject_id,
        state_fingerprint=change.current_fingerprint,
        items=tuple(items),
    )
