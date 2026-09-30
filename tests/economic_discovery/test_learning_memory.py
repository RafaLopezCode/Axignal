from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningMemoryConflict,
    LearningOutcome,
    LearningYield,
    summarize_learning,
)
from pipeline.learning_memory import SqliteLearningMemory

NOW = datetime(2026, 9, 30, 15, 0, tzinfo=UTC)


def _event(
    event_id: str,
    *,
    subject_id: str = "org:acme",
    xeed_id: str | None = "xeed:1",
    minute: int = 0,
    kind: LearningEventKind = LearningEventKind.BOOTSTRAP,
    outcome: LearningOutcome = LearningOutcome.COMPLETED,
    reason_code: str = "STATE_ADVANCED",
    corrects_event_id: str | None = None,
    cost: LearningCost | None = None,
    yield_: LearningYield | None = None,
) -> LearningEvent:
    if cost is None:
        cost = LearningCost()
    if yield_ is None:
        yield_ = LearningYield(state_fields_changed=1)
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=outcome,
        occurred_at=NOW + timedelta(minutes=minute),
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref="plan:abc",
        policy_id="bootstrap",
        policy_version="1",
        code_sha="abc123",
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint="input:1",
        output_fingerprint="output:1",
        reason_code=reason_code,
        before_state_fingerprint="state:before",
        after_state_fingerprint="state:after",
        corrects_event_id=corrects_event_id,
        cost=cost,
        yield_=yield_,
    )


def test_sqlite_learning_memory_survives_adapter_recreation(tmp_path: Path) -> None:
    database = tmp_path / "learning.sqlite3"
    event = _event("learn:1")

    assert SqliteLearningMemory(database).append(event) is True
    assert SqliteLearningMemory(database).get("learn:1") == event


def test_exact_replay_is_idempotent_and_conflicting_id_fails(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    event = _event("learn:1")
    conflicting = _event("learn:1", reason_code="DIFFERENT")

    assert memory.append(event) is True
    assert memory.append(event) is False
    with pytest.raises(LearningMemoryConflict, match="different governed content"):
        memory.append(conflicting)


def test_unknown_cost_is_not_measured_zero() -> None:
    unknown = LearningCost()
    zero = LearningCost(amount_microunits=0, currency="usd", latency_ms=0)

    assert unknown != zero
    assert unknown.amount_microunits is None
    assert zero.amount_microunits == 0
    assert zero.currency == "USD"


def test_cost_amount_without_currency_is_rejected() -> None:
    with pytest.raises(ValueError, match="amount and currency"):
        LearningCost(amount_microunits=12)


def test_failed_event_cannot_claim_successful_yield() -> None:
    with pytest.raises(ValueError, match="cannot fabricate"):
        _event("learn:failed", outcome=LearningOutcome.FAILED)


def test_correction_is_append_only_and_preserves_original(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    original = _event("learn:original")
    correction = _event(
        "learn:correction",
        minute=5,
        kind=LearningEventKind.CORRECTION,
        reason_code="LATER_EVIDENCE_REVISED_OPERATIONAL_INTERPRETATION",
        corrects_event_id=original.event_id,
        yield_=LearningYield(),
    )

    memory.append(original)
    memory.append(correction)

    history = memory.for_subject("org:acme")
    assert history == (original, correction)
    assert memory.get(original.event_id) == original
    assert memory.get(correction.event_id) == correction


def test_correction_cannot_reference_unknown_event(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    correction = _event(
        "learn:correction",
        kind=LearningEventKind.CORRECTION,
        corrects_event_id="learn:missing",
        yield_=LearningYield(),
    )

    with pytest.raises(LearningMemoryConflict, match="unknown learning event"):
        memory.append(correction)


def test_correction_cannot_cross_subjects(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    original = _event("learn:original", subject_id="org:a")
    correction = _event(
        "learn:correction",
        subject_id="org:b",
        kind=LearningEventKind.CORRECTION,
        corrects_event_id=original.event_id,
        yield_=LearningYield(),
    )
    memory.append(original)

    with pytest.raises(LearningMemoryConflict, match="cannot cross"):
        memory.append(correction)


def test_subject_and_xeed_histories_are_chronological(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    later = _event("learn:later", minute=10)
    earlier = _event("learn:earlier", minute=1)

    memory.append(later)
    memory.append(earlier)

    assert memory.for_subject("org:acme") == (earlier, later)
    assert memory.for_xeed("xeed:1") == (earlier, later)


def test_storage_normalizes_time_to_utc(tmp_path: Path) -> None:
    memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    cet = timezone(timedelta(hours=2))
    event = LearningEvent(
        event_id="learn:tz",
        kind=LearningEventKind.OBSERVATION_INGESTION,
        outcome=LearningOutcome.NO_CHANGE,
        occurred_at=datetime(2026, 9, 30, 17, 0, tzinfo=cet),
        subject_id="org:acme",
        activity_ref="obs:1",
        policy_id="observation",
        policy_version="1",
        code_sha="abc123",
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint="input:tz",
        reason_code="IDEMPOTENT_REOBSERVATION",
    )
    memory.append(event)

    restored = memory.get(event.event_id)
    assert restored is not None
    assert restored.occurred_at == datetime(2026, 9, 30, 15, 0, tzinfo=UTC)
    assert restored.fingerprint == event.fingerprint


def test_concurrent_exact_replay_inserts_once(tmp_path: Path) -> None:
    database = tmp_path / "learning.sqlite3"
    event = _event("learn:concurrent")

    def append_once() -> bool:
        return SqliteLearningMemory(database).append(event)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: append_once(), range(2)))

    assert sorted(results) == [False, True]
    assert SqliteLearningMemory(database).for_subject("org:acme") == (event,)


def test_learning_summary_preserves_unknown_cost_and_avoids_opaque_score() -> None:
    events = (
        _event(
            "learn:known",
            cost=LearningCost(
                amount_microunits=125,
                currency="USD",
                latency_ms=40,
                input_units=100,
                output_units=5,
            ),
            yield_=LearningYield(
                observations_reused=2,
                observations_added=1,
                state_fields_changed=2,
                dimensions_became_answerable=1,
            ),
        ),
        _event(
            "learn:unknown",
            minute=1,
            outcome=LearningOutcome.NO_CHANGE,
            cost=LearningCost(latency_ms=10),
            yield_=LearningYield(),
        ),
    )

    summary = summarize_learning(events)

    assert summary.event_count == 2
    assert summary.known_costs_by_currency == (("USD", 125),)
    assert summary.unknown_cost_event_count == 1
    assert summary.known_latency_event_count == 2
    assert summary.total_latency_ms == 50
    assert summary.yield_.observations_reused == 2
    assert summary.yield_.observations_added == 1
    assert summary.yield_.state_fields_changed == 2
    assert not hasattr(summary, "score")
