"""Deterministic FR-26 unit-economics projection over Learning Memory."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.economic_discovery.learning_memory import (
    LearningEvent,
    LearningEventKind,
)


class EconomicsPhase(StrEnum):
    FIRST_VALUE = "FIRST_VALUE"
    GERMINATION = "GERMINATION"
    MAINTENANCE_REFRESH = "MAINTENANCE_REFRESH"


class CostScope(StrEnum):
    SHARED_CANONICAL = "SHARED_CANONICAL"
    XEED_PRIVATE = "XEED_PRIVATE"


class CostAllocationMethod(StrEnum):
    DIRECT = "DIRECT"
    SHARED_EQUAL_SPLIT = "SHARED_EQUAL_SPLIT"
    SHARED_POLICY = "SHARED_POLICY"


class ContributionMarginStatus(StrEnum):
    COMPLETE = "COMPLETE"
    MISSING_REVENUE = "MISSING_REVENUE"
    MISSING_NON_COMPUTE_COST = "MISSING_NON_COMPUTE_COST"
    MISSING_COMPUTE_COST = "MISSING_COMPUTE_COST"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"


@dataclass(frozen=True, slots=True)
class Ratio:
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator < 0 or self.denominator < 0:
            raise ValueError("ratio counts cannot be negative")
        if self.numerator > self.denominator:
            raise ValueError("ratio numerator cannot exceed denominator")

    @property
    def is_known(self) -> bool:
        return self.denominator > 0


@dataclass(frozen=True, slots=True)
class UnitEconomicsAttribution:
    """Explicit economic attribution for one underlying LearningEvent."""

    event_id: str
    phase: EconomicsPhase
    cost_scope: CostScope
    allocation_method: CostAllocationMethod
    allocated_cost_microunits: int | None = None
    currency: str | None = None
    fresh_observations_reused: int = 0
    useful_xignals: int = 0
    evidence_inspections: int = 0

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("unit-economics attribution requires event id")
        if (self.allocated_cost_microunits is None) != (self.currency is None):
            raise ValueError("allocated cost amount and currency must coexist")
        if self.allocated_cost_microunits is not None and self.allocated_cost_microunits < 0:
            raise ValueError("allocated cost cannot be negative")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("allocated cost currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)
        if (
            min(
                self.fresh_observations_reused,
                self.useful_xignals,
                self.evidence_inspections,
            )
            < 0
        ):
            raise ValueError("unit-economics observed counts cannot be negative")
        if self.cost_scope is CostScope.XEED_PRIVATE:
            if self.allocation_method is not CostAllocationMethod.DIRECT:
                raise ValueError("private cost must use DIRECT allocation")
        elif self.allocation_method is CostAllocationMethod.DIRECT:
            raise ValueError("shared cost requires an explicit shared allocation method")


@dataclass(frozen=True, slots=True)
class ContributionMarginInputs:
    revenue_microunits: int | None = None
    non_compute_variable_cost_microunits: int | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if self.revenue_microunits is not None and self.revenue_microunits < 0:
            raise ValueError("revenue cannot be negative")
        if (
            self.non_compute_variable_cost_microunits is not None
            and self.non_compute_variable_cost_microunits < 0
        ):
            raise ValueError("non-compute variable cost cannot be negative")
        has_value = (
            self.revenue_microunits is not None
            or self.non_compute_variable_cost_microunits is not None
        )
        if has_value and self.currency is None:
            raise ValueError("contribution-margin inputs require currency")
        if self.currency is not None:
            currency = self.currency.strip().upper()
            if len(currency) != 3 or not currency.isalpha():
                raise ValueError("contribution-margin currency must be a three-letter code")
            object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class ContributionMargin:
    status: ContributionMarginStatus
    amount_microunits: int | None = None
    currency: str | None = None


@dataclass(frozen=True, slots=True)
class PhaseEconomics:
    phase: EconomicsPhase
    event_count: int
    unknown_cost_event_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ScopeEconomics:
    scope: CostScope
    event_count: int
    unknown_cost_event_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class UnitEconomicsReport:
    xeed_id: str
    event_ids: tuple[str, ...]
    event_count: int
    known_cost_event_count: int
    unknown_cost_event_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]
    cost_coverage: Ratio
    phase_economics: tuple[PhaseEconomics, ...]
    scope_economics: tuple[ScopeEconomics, ...]
    observations_reused: int
    observations_added: int
    fresh_observations_reused: int
    reuse_ratio: Ratio
    fresh_reuse_ratio: Ratio
    first_learning_event_at: datetime | None
    first_useful_xignal_at: datetime | None
    time_to_first_useful_xignal_ms: int | None
    useful_xignals: int
    evidence_inspections: int
    corrections: int
    contribution_margin: ContributionMargin


@dataclass(frozen=True, slots=True)
class CohortEconomicsReport:
    cohort_id: str
    xeed_ids: tuple[str, ...]
    event_count: int
    known_cost_event_count: int
    unknown_cost_event_count: int
    known_costs_by_currency: tuple[tuple[str, int], ...]
    cost_coverage: Ratio
    reuse_ratio: Ratio
    fresh_reuse_ratio: Ratio
    useful_xignals: int
    evidence_inspections: int
    corrections: int


def _sum_costs(
    pairs: list[tuple[int | None, str | None]],
) -> tuple[tuple[tuple[str, int], ...], int]:
    totals: dict[str, int] = {}
    unknown = 0
    for amount, currency in pairs:
        if amount is None:
            unknown += 1
            continue
        assert currency is not None
        totals[currency] = totals.get(currency, 0) + amount
    return tuple(sorted(totals.items())), unknown


def _contribution_margin(
    costs: tuple[tuple[str, int], ...],
    unknown_cost_event_count: int,
    inputs: ContributionMarginInputs,
) -> ContributionMargin:
    if inputs.revenue_microunits is None:
        return ContributionMargin(ContributionMarginStatus.MISSING_REVENUE)
    if inputs.non_compute_variable_cost_microunits is None:
        return ContributionMargin(ContributionMarginStatus.MISSING_NON_COMPUTE_COST)
    if unknown_cost_event_count:
        return ContributionMargin(ContributionMarginStatus.MISSING_COMPUTE_COST)
    if len(costs) != 1 or costs[0][0] != inputs.currency:
        return ContributionMargin(ContributionMarginStatus.CURRENCY_MISMATCH)
    compute_cost = costs[0][1]
    amount = inputs.revenue_microunits - inputs.non_compute_variable_cost_microunits - compute_cost
    return ContributionMargin(
        ContributionMarginStatus.COMPLETE,
        amount_microunits=amount,
        currency=inputs.currency,
    )


def summarize_xeed_unit_economics(
    *,
    xeed_id: str,
    events: tuple[LearningEvent, ...],
    attributions: tuple[UnitEconomicsAttribution, ...],
    contribution_inputs: ContributionMarginInputs | None = None,
) -> UnitEconomicsReport:
    """Build one deterministic Xeed economics report without imputing missing cost/value."""

    if contribution_inputs is None:
        contribution_inputs = ContributionMarginInputs()
    if not xeed_id.strip():
        raise ValueError("unit-economics report requires Xeed id")
    event_by_id: dict[str, LearningEvent] = {}
    for event in events:
        if event.event_id in event_by_id:
            raise ValueError("duplicate learning event id in economics input")
        if event.xeed_id != xeed_id:
            raise ValueError("all economics events must be attributable to the requested Xeed")
        event_by_id[event.event_id] = event

    attribution_by_id: dict[str, UnitEconomicsAttribution] = {}
    for attribution in attributions:
        if attribution.event_id in attribution_by_id:
            raise ValueError("duplicate unit-economics attribution")
        if attribution.event_id not in event_by_id:
            raise ValueError("unit-economics attribution references unknown learning event")
        event = event_by_id[attribution.event_id]
        if attribution.fresh_observations_reused > event.yield_.observations_reused:
            raise ValueError("fresh reuse cannot exceed event observations_reused")
        if attribution.useful_xignals > event.yield_.xignals_emitted:
            raise ValueError("useful Xignals cannot exceed emitted Xignals")
        attribution_by_id[attribution.event_id] = attribution

    if set(attribution_by_id) != set(event_by_id):
        raise ValueError("every learning event requires explicit unit-economics attribution")

    ordered = tuple(sorted(events, key=lambda item: (item.occurred_at, item.event_id)))
    ordered_attributions = tuple(attribution_by_id[event.event_id] for event in ordered)
    cost_pairs = [(item.allocated_cost_microunits, item.currency) for item in ordered_attributions]
    known_costs, unknown_costs = _sum_costs(cost_pairs)

    phase_rows: list[PhaseEconomics] = []
    for phase in EconomicsPhase:
        rows = [item for item in ordered_attributions if item.phase is phase]
        costs, unknown = _sum_costs(
            [(item.allocated_cost_microunits, item.currency) for item in rows]
        )
        phase_rows.append(PhaseEconomics(phase, len(rows), unknown, costs))

    scope_rows: list[ScopeEconomics] = []
    for scope in CostScope:
        rows = [item for item in ordered_attributions if item.cost_scope is scope]
        costs, unknown = _sum_costs(
            [(item.allocated_cost_microunits, item.currency) for item in rows]
        )
        scope_rows.append(ScopeEconomics(scope, len(rows), unknown, costs))

    reused = sum(event.yield_.observations_reused for event in ordered)
    added = sum(event.yield_.observations_added for event in ordered)
    fresh_reused = sum(item.fresh_observations_reused for item in ordered_attributions)
    useful_xignals = sum(item.useful_xignals for item in ordered_attributions)
    inspections = sum(item.evidence_inspections for item in ordered_attributions)
    corrections = sum(event.kind is LearningEventKind.CORRECTION for event in ordered)

    first_event_at = ordered[0].occurred_at if ordered else None
    useful_times = [
        event.occurred_at
        for event in ordered
        if attribution_by_id[event.event_id].useful_xignals > 0
    ]
    first_useful_at = min(useful_times) if useful_times else None
    time_to_value = None
    if first_event_at is not None and first_useful_at is not None:
        time_to_value = int((first_useful_at - first_event_at).total_seconds() * 1000)

    return UnitEconomicsReport(
        xeed_id=xeed_id,
        event_ids=tuple(event.event_id for event in ordered),
        event_count=len(ordered),
        known_cost_event_count=len(ordered) - unknown_costs,
        unknown_cost_event_count=unknown_costs,
        known_costs_by_currency=known_costs,
        cost_coverage=Ratio(len(ordered) - unknown_costs, len(ordered)),
        phase_economics=tuple(phase_rows),
        scope_economics=tuple(scope_rows),
        observations_reused=reused,
        observations_added=added,
        fresh_observations_reused=fresh_reused,
        reuse_ratio=Ratio(reused, reused + added),
        fresh_reuse_ratio=Ratio(fresh_reused, reused),
        first_learning_event_at=first_event_at,
        first_useful_xignal_at=first_useful_at,
        time_to_first_useful_xignal_ms=time_to_value,
        useful_xignals=useful_xignals,
        evidence_inspections=inspections,
        corrections=corrections,
        contribution_margin=_contribution_margin(
            known_costs,
            unknown_costs,
            contribution_inputs,
        ),
    )


def summarize_cohort_unit_economics(
    *,
    cohort_id: str,
    reports: tuple[UnitEconomicsReport, ...],
) -> CohortEconomicsReport:
    """Aggregate Xeed reports without averaging ratios or mixing currencies."""

    if not cohort_id.strip():
        raise ValueError("cohort economics requires cohort id")
    xeed_ids = [report.xeed_id for report in reports]
    if len(xeed_ids) != len(set(xeed_ids)):
        raise ValueError("cohort economics requires unique Xeed reports")

    totals: dict[str, int] = {}
    for report in reports:
        for currency, amount in report.known_costs_by_currency:
            totals[currency] = totals.get(currency, 0) + amount

    event_count = sum(report.event_count for report in reports)
    known_count = sum(report.known_cost_event_count for report in reports)
    unknown_count = sum(report.unknown_cost_event_count for report in reports)
    reused = sum(report.observations_reused for report in reports)
    added = sum(report.observations_added for report in reports)
    fresh_reused = sum(report.fresh_observations_reused for report in reports)

    return CohortEconomicsReport(
        cohort_id=cohort_id,
        xeed_ids=tuple(sorted(xeed_ids)),
        event_count=event_count,
        known_cost_event_count=known_count,
        unknown_cost_event_count=unknown_count,
        known_costs_by_currency=tuple(sorted(totals.items())),
        cost_coverage=Ratio(known_count, event_count),
        reuse_ratio=Ratio(reused, reused + added),
        fresh_reuse_ratio=Ratio(fresh_reused, reused),
        useful_xignals=sum(report.useful_xignals for report in reports),
        evidence_inspections=sum(report.evidence_inspections for report in reports),
        corrections=sum(report.corrections for report in reports),
    )
