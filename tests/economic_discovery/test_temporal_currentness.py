from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery import (
    GovernedObservation,
    ObservationMode,
    ObservationRecord,
    ObservationReuseAuthority,
    ObservedField,
    ReobservationDisposition,
    TemporalCurrentnessPolicy,
    TypingDimensionContract,
    affected_temporal_dimensions,
    append_reobservation,
    evaluate_currentness,
    plan_subject_reobservations,
    reobservation_requirement,
    temporal_dependency_change,
)
from application.economic_discovery.brain_contracts import SemanticPrimitive
from domain.evidence import Currentness
from pipeline.observation_memory import SqliteObservationMemory

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
POLICY = TemporalCurrentnessPolicy(
    policy_id="temporal-currentness",
    version="1",
    stale_after=timedelta(days=30),
    historical_after=timedelta(days=365),
)


def _observation(
    observation_id: str,
    *,
    observed_at: datetime = NOW,
    currentness: Currentness = Currentness.CURRENT,
    source_ref: str = "https://example.com/acme",
    fields: tuple[ObservedField, ...] = (ObservedField("markets", "Spain"),),
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id="org:acme",
            source_ref=source_ref,
            source_type="OFFICIAL_WEB",
            observed_at=observed_at,
            content_fingerprint=f"sha256:{observation_id}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=f"snapshot:{observation_id}",
        fields=fields,
        reuse_authority=ObservationReuseAuthority(currentness=currentness),
    )


def _dimension(
    dimension_id: str,
    *dependencies: str,
) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.CHOICE,
        question=f"{dimension_id}?",
        state_requirements=(),
        dependencies=dependencies,
        mutually_exclusive=False,
        abstention_policy="ALLOW_UNKNOWN",
    )


def test_current_ages_to_stale_then_historical_without_becoming_false() -> None:
    observation = _observation("obs:1")

    current = evaluate_currentness(
        observation,
        as_of=NOW + timedelta(days=10),
        policy=POLICY,
    )
    stale = evaluate_currentness(
        observation,
        as_of=NOW + timedelta(days=31),
        policy=POLICY,
    )
    historical = evaluate_currentness(
        observation,
        as_of=NOW + timedelta(days=366),
        policy=POLICY,
    )

    assert current.current is Currentness.CURRENT
    assert stale.current is Currentness.STALE
    assert historical.current is Currentness.HISTORICAL


def test_unknown_remains_unknown_until_reobservation_supplies_new_evidence() -> None:
    observation = _observation("obs:unknown", currentness=Currentness.UNKNOWN)

    decision = evaluate_currentness(
        observation,
        as_of=NOW + timedelta(days=900),
        policy=POLICY,
    )

    assert decision.current is Currentness.UNKNOWN
    requirement = reobservation_requirement(
        observation,
        as_of=NOW + timedelta(days=900),
        policy=POLICY,
    )
    assert requirement.disposition is ReobservationDisposition.REQUIRED
    assert requirement.effective_currentness is Currentness.UNKNOWN


def test_stale_progresses_to_historical_and_historical_never_freshens_by_clock() -> None:
    stale = _observation("obs:stale", currentness=Currentness.STALE)
    historical = _observation("obs:historical", currentness=Currentness.HISTORICAL)

    assert (
        evaluate_currentness(
            stale,
            as_of=NOW + timedelta(days=400),
            policy=POLICY,
        ).current
        is Currentness.HISTORICAL
    )
    assert (
        evaluate_currentness(
            historical,
            as_of=NOW + timedelta(days=1),
            policy=POLICY,
        ).current
        is Currentness.HISTORICAL
    )


def test_reobservation_requirement_is_explicit_for_stale_and_historical() -> None:
    observation = _observation("obs:1")

    stale = reobservation_requirement(
        observation,
        as_of=NOW + timedelta(days=31),
        policy=POLICY,
    )
    historical = reobservation_requirement(
        observation,
        as_of=NOW + timedelta(days=366),
        policy=POLICY,
    )

    assert stale.disposition is ReobservationDisposition.REQUIRED
    assert stale.reason.value == "STALE"
    assert historical.disposition is ReobservationDisposition.REQUIRED
    assert historical.reason.value == "HISTORICAL"


def test_temporal_aging_re_evaluates_only_dimensions_depending_on_currentness() -> None:
    observation = _observation("obs:1")
    change = temporal_dependency_change(
        observation,
        as_of=NOW + timedelta(days=31),
        policy=POLICY,
    )
    assert change is not None

    contracts = (
        _dimension("MARKET_ROLE", "markets"),
        _dimension("CURRENT_MARKET_ROLE", "markets", "source.currentness"),
        _dimension("FRESHNESS_ONLY", "source.currentness"),
    )

    assert affected_temporal_dimensions(change, contracts) == (
        "CURRENT_MARKET_ROLE",
        "FRESHNESS_ONLY",
    )


def test_no_temporal_transition_creates_no_reevaluation_signal() -> None:
    observation = _observation("obs:1")

    assert (
        temporal_dependency_change(
            observation,
            as_of=NOW + timedelta(days=10),
            policy=POLICY,
        )
        is None
    )


def test_reobservation_appends_history_and_preserves_predecessor(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    predecessor = _observation("obs:old")
    assert memory.append(predecessor) is True

    fresh = _observation(
        "obs:new",
        observed_at=NOW + timedelta(days=31),
        fields=(ObservedField("markets", "Spain"),),
    )
    result = append_reobservation(
        memory,
        predecessor=predecessor,
        observation=fresh,
    )

    assert result.predecessor_observation_id == "obs:old"
    assert result.observation_id == "obs:new"
    assert result.mutation.inserted is True
    assert result.mutation.change is not None
    assert result.mutation.change.changed_fields == frozenset({"markets"})
    assert memory.for_subject("org:acme") == (predecessor, fresh)


def test_reobservation_cannot_overwrite_or_change_subject_or_source(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    predecessor = _observation("obs:old")
    memory.append(predecessor)

    with pytest.raises(ValueError, match="new observation id"):
        append_reobservation(
            memory,
            predecessor=predecessor,
            observation=_observation(
                "obs:old",
                observed_at=NOW + timedelta(days=1),
            ),
        )

    with pytest.raises(ValueError, match="source identity"):
        append_reobservation(
            memory,
            predecessor=predecessor,
            observation=_observation(
                "obs:new-source",
                observed_at=NOW + timedelta(days=1),
                source_ref="https://other.example/acme",
            ),
        )


def test_subject_plan_uses_only_latest_observation_per_source(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    old = _observation("obs:old", observed_at=NOW - timedelta(days=400))
    newer = _observation("obs:newer", observed_at=NOW - timedelta(days=10))
    other = _observation(
        "obs:other",
        observed_at=NOW - timedelta(days=40),
        source_ref="https://registry.example/acme",
    )
    for observation in (old, newer, other):
        memory.append(observation)

    plan = plan_subject_reobservations(
        memory,
        subject_id="org:acme",
        as_of=NOW,
        policy=POLICY,
    )

    assert tuple(item.observation_id for item in plan.requirements) == (
        "obs:newer",
        "obs:other",
    )
    assert plan.required_observation_ids == ("obs:other",)
