"""FR-26 Unit Economics Instrumentation contract."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.unit_economics import (
    ContributionMarginInputs,
    ContributionMarginStatus,
    CostAllocationMethod,
    CostScope,
    EconomicsPhase,
    UnitEconomicsAttribution,
    summarize_cohort_unit_economics,
    summarize_xeed_unit_economics,
)

T0 = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)


def _event(
    event_id: str,
    *,
    at: datetime,
    amount: int | None,
    reused: int = 0,
    added: int = 0,
    xignals: int = 0,
    kind: LearningEventKind = LearningEventKind.DETERMINISTIC_EVALUATION,
) -> LearningEvent:
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=LearningOutcome.COMPLETED,
        occurred_at=at,
        subject_id="org:acme",
        xeed_id="xeed:1",
        activity_ref=f"run:{event_id}",
        policy_id="policy",
        policy_version="1",
        code_sha="abc123",
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=f"input:{event_id}",
        reason_code="OBSERVED_EXECUTION",
        corrects_event_id="e1" if kind is LearningEventKind.CORRECTION else None,
        replay=LearningReplayReference.replayable(source=event_id),
        cost=LearningCost(
            amount_microunits=amount,
            currency="EUR" if amount is not None else None,
        ),
        yield_=LearningYield(
            observations_reused=reused,
            observations_added=added,
            xignals_emitted=xignals,
        ),
    )


def _private(
    event_id: str,
    phase: EconomicsPhase,
    amount: int | None,
    *,
    fresh: int = 0,
    useful: int = 0,
    inspections: int = 0,
) -> UnitEconomicsAttribution:
    return UnitEconomicsAttribution(
        event_id=event_id,
        phase=phase,
        cost_scope=CostScope.XEED_PRIVATE,
        allocation_method=CostAllocationMethod.DIRECT,
        allocated_cost_microunits=amount,
        currency="EUR" if amount is not None else None,
        fresh_observations_reused=fresh,
        useful_xignals=useful,
        evidence_inspections=inspections,
    )


def test_missing_cost_is_unknown_not_zero() -> None:
    events = (_event("e1", at=T0, amount=None, added=1),)
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=events,
        attributions=(_private("e1", EconomicsPhase.FIRST_VALUE, None),),
    )

    assert report.known_cost_event_count == 0
    assert report.unknown_cost_event_count == 1
    assert report.known_costs_by_currency == ()
    assert report.cost_coverage.numerator == 0
    assert report.cost_coverage.denominator == 1
    assert report.contribution_margin.status is ContributionMarginStatus.MISSING_REVENUE


def test_zero_cost_remains_measured_zero() -> None:
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=(_event("e1", at=T0, amount=0),),
        attributions=(_private("e1", EconomicsPhase.GERMINATION, 0),),
    )

    assert report.unknown_cost_event_count == 0
    assert report.known_costs_by_currency == (("EUR", 0),)
    assert report.cost_coverage.numerator == 1


def test_reuse_fresh_reuse_first_value_and_interactions_are_observed() -> None:
    events = (
        _event("e1", at=T0, amount=100, added=2),
        _event(
            "e2",
            at=T0 + timedelta(seconds=3),
            amount=40,
            reused=3,
            xignals=2,
        ),
    )
    attributions = (
        _private("e1", EconomicsPhase.FIRST_VALUE, 100),
        _private(
            "e2",
            EconomicsPhase.FIRST_VALUE,
            40,
            fresh=2,
            useful=1,
            inspections=2,
        ),
    )
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=events,
        attributions=attributions,
    )

    assert report.reuse_ratio == report.reuse_ratio.__class__(3, 5)
    assert report.fresh_reuse_ratio == report.fresh_reuse_ratio.__class__(2, 3)
    assert report.time_to_first_useful_xignal_ms == 3000
    assert report.useful_xignals == 1
    assert report.evidence_inspections == 2


def test_emitted_xignal_is_not_silently_counted_as_useful() -> None:
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=(_event("e1", at=T0, amount=10, xignals=2),),
        attributions=(_private("e1", EconomicsPhase.FIRST_VALUE, 10),),
    )

    assert report.useful_xignals == 0
    assert report.first_useful_xignal_at is None
    assert report.time_to_first_useful_xignal_ms is None


def test_every_economics_row_traces_to_exact_learning_event() -> None:
    events = (_event("e1", at=T0, amount=10), _event("e2", at=T0, amount=20))
    with pytest.raises(ValueError, match="every learning event"):
        summarize_xeed_unit_economics(
            xeed_id="xeed:1",
            events=events,
            attributions=(_private("e1", EconomicsPhase.GERMINATION, 10),),
        )


def test_shared_cost_requires_explicit_allocation_method() -> None:
    with pytest.raises(ValueError, match="shared cost"):
        UnitEconomicsAttribution(
            event_id="e1",
            phase=EconomicsPhase.GERMINATION,
            cost_scope=CostScope.SHARED_CANONICAL,
            allocation_method=CostAllocationMethod.DIRECT,
            allocated_cost_microunits=5,
            currency="EUR",
        )


def test_corrections_and_contribution_margin_inputs_are_separate_from_usage() -> None:
    events = (
        _event("e1", at=T0, amount=100),
        _event(
            "e2",
            at=T0 + timedelta(seconds=1),
            amount=50,
            kind=LearningEventKind.CORRECTION,
        ),
    )
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=events,
        attributions=(
            _private("e1", EconomicsPhase.GERMINATION, 100),
            _private("e2", EconomicsPhase.MAINTENANCE_REFRESH, 50),
        ),
        contribution_inputs=ContributionMarginInputs(
            revenue_microunits=1000,
            non_compute_variable_cost_microunits=200,
            currency="EUR",
        ),
    )

    assert report.corrections == 1
    assert report.contribution_margin.status is ContributionMarginStatus.COMPLETE
    assert report.contribution_margin.amount_microunits == 650
    assert report.contribution_margin.currency == "EUR"


def test_unknown_compute_cost_blocks_contribution_margin() -> None:
    report = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=(_event("e1", at=T0, amount=None),),
        attributions=(_private("e1", EconomicsPhase.GERMINATION, None),),
        contribution_inputs=ContributionMarginInputs(
            revenue_microunits=1000,
            non_compute_variable_cost_microunits=200,
            currency="EUR",
        ),
    )

    assert report.contribution_margin.status is ContributionMarginStatus.MISSING_COMPUTE_COST
    assert report.contribution_margin.amount_microunits is None


def test_cohort_aggregates_counts_not_average_ratios() -> None:
    first = summarize_xeed_unit_economics(
        xeed_id="xeed:1",
        events=(_event("e1", at=T0, amount=10, reused=9, added=1),),
        attributions=(_private("e1", EconomicsPhase.GERMINATION, 10, fresh=8),),
    )
    second_event = replace(_event("e2", at=T0, amount=20, reused=1, added=9), xeed_id="xeed:2")

    second = summarize_xeed_unit_economics(
        xeed_id="xeed:2",
        events=(second_event,),
        attributions=(_private("e2", EconomicsPhase.GERMINATION, 20, fresh=1),),
    )

    cohort = summarize_cohort_unit_economics(
        cohort_id="pilot-2026-10",
        reports=(first, second),
    )

    assert cohort.reuse_ratio.numerator == 10
    assert cohort.reuse_ratio.denominator == 20
    assert cohort.fresh_reuse_ratio.numerator == 9
    assert cohort.fresh_reuse_ratio.denominator == 10
    assert cohort.known_costs_by_currency == (("EUR", 30),)
