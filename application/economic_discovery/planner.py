"""Deterministic routing for AXIGNAL cognitive-loop work."""

from __future__ import annotations

from dataclasses import dataclass

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    ObservationMode,
    StateChange,
    TypingDimensionContract,
    affected_dimensions,
)


@dataclass(frozen=True, slots=True)
class ObservationIngress:
    observation_id: str
    mode: ObservationMode
    bound_subject_id: str | None
    requires_universe_discovery: bool

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation identity is required")
        if self.bound_subject_id is not None and not self.bound_subject_id.strip():
            raise ValueError("bound subject cannot be empty")


@dataclass(frozen=True, slots=True)
class DimensionWork:
    dimension_id: str
    disposition: DimensionDisposition
    missing_requirements: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CognitiveWorkPlan:
    retrieval_required: bool
    state_mutation_required: bool
    evaluation: tuple[DimensionWork, ...]
    research_dimensions: tuple[str, ...]


def route_retrieval(ingress: ObservationIngress) -> bool:
    """Use semantic retrieval only to discover candidates in a wider universe."""
    if ingress.bound_subject_id is not None:
        return False
    return ingress.requires_universe_discovery


def assess_dimension_work(
    *,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
) -> tuple[DimensionWork, ...]:
    """Assess answerability for every supplied dimension without inventing state change."""

    work: list[DimensionWork] = []
    for contract in contracts:
        missing = tuple(
            requirement
            for requirement in contract.state_requirements
            if requirement not in available_state_fields
        )
        disposition = (
            DimensionDisposition.NOT_ANSWERABLE if missing else DimensionDisposition.ANSWERABLE
        )
        work.append(DimensionWork(contract.dimension_id, disposition, missing))
    return tuple(work)


def plan_dimension_work(
    *,
    change: StateChange,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
) -> tuple[DimensionWork, ...]:
    impacted = set(affected_dimensions(change, contracts))
    return tuple(
        item
        for item in assess_dimension_work(
            contracts=contracts,
            available_state_fields=available_state_fields,
        )
        if item.dimension_id in impacted
    )


def build_work_plan(
    *,
    ingress: ObservationIngress,
    change: StateChange,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
) -> CognitiveWorkPlan:
    evaluation = plan_dimension_work(
        change=change,
        contracts=contracts,
        available_state_fields=available_state_fields,
    )
    research = tuple(
        item.dimension_id
        for item in evaluation
        if item.disposition is DimensionDisposition.NOT_ANSWERABLE
    )
    return CognitiveWorkPlan(
        retrieval_required=route_retrieval(ingress),
        state_mutation_required=ingress.bound_subject_id is not None,
        evaluation=evaluation,
        research_dimensions=research,
    )
