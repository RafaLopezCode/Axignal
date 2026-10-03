from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from application.economic_discovery import (
    GovernedObservation,
    ObservationMemoryConflict,
    ObservationMode,
    ObservationRecord,
    ObservedField,
    compile_observation_state,
    ingest_observation,
)
from pipeline.observation_memory import SqliteObservationMemory

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def _observation(
    observation_id: str,
    *,
    subject_id: str = "org:acme",
    minute: int = 0,
    fingerprint: str | None = None,
    fields: tuple[ObservedField, ...] = (),
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id=subject_id,
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=NOW + timedelta(minutes=minute),
            content_fingerprint=fingerprint or f"sha256:{observation_id}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=f"snapshot:{observation_id}",
        fields=fields,
    )


def test_sqlite_memory_survives_adapter_recreation(tmp_path: Path) -> None:
    database = tmp_path / "observation-memory.sqlite3"
    first = SqliteObservationMemory(database)
    observation = _observation(
        "obs:1",
        fields=(
            ObservedField("candidate_context", "industrial pumps"),
            ObservedField("markets", "food processing"),
        ),
    )

    assert first.append(observation) is True

    reopened = SqliteObservationMemory(database)
    assert reopened.for_subject("org:acme") == (observation,)


def test_exact_replay_is_idempotent_and_conflicting_reuse_fails(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    original = _observation(
        "obs:1",
        fields=(ObservedField("candidate_context", "industrial pumps"),),
    )
    conflicting = _observation(
        "obs:1",
        fingerprint="sha256:different",
        fields=(ObservedField("candidate_context", "industrial pumps"),),
    )

    assert memory.append(original) is True
    assert memory.append(original) is False
    with pytest.raises(ObservationMemoryConflict, match="different governed content"):
        memory.append(conflicting)

    assert memory.for_subject("org:acme") == (original,)


def test_history_is_append_only_and_latest_field_wins_deterministically(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    old = _observation(
        "obs:old",
        fields=(
            ObservedField("markets", "Spain"),
            ObservedField("candidate_context", "pump manufacturer"),
        ),
    )
    new = _observation(
        "obs:new",
        minute=5,
        fields=(ObservedField("markets", "Spain | France"),),
    )
    assert memory.append(old) is True
    assert memory.append(new) is True

    history = memory.for_subject("org:acme")
    assert history == (old, new)

    state = compile_observation_state("org:acme", history)
    assert state.get("markets") is not None
    assert state.get("markets").value == "Spain | France"  # type: ignore[union-attr]
    assert state.get("markets").observation_id == "obs:new"  # type: ignore[union-attr]
    assert state.get("candidate_context") is not None
    assert state.get("candidate_context").observation_id == "obs:old"  # type: ignore[union-attr]


def test_reobservation_changes_state_provenance_even_when_value_is_same(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    first = _observation(
        "obs:1",
        fields=(ObservedField("markets", "Spain"),),
    )
    second = _observation(
        "obs:2",
        minute=30,
        fields=(ObservedField("markets", "Spain"),),
    )

    first_mutation = ingest_observation(memory, first)
    second_mutation = ingest_observation(memory, second)

    assert first_mutation.change is not None
    assert first_mutation.change.changed_fields == frozenset({"markets"})
    assert second_mutation.change is not None
    assert second_mutation.change.changed_fields == frozenset({"markets"})
    assert second_mutation.change.previous_fingerprint != second_mutation.change.current_fingerprint


def test_exact_replay_does_not_create_a_false_state_change(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    observation = _observation(
        "obs:1",
        fields=(ObservedField("markets", "Spain"),),
    )

    assert ingest_observation(memory, observation).change is not None
    replay = ingest_observation(memory, observation)

    assert replay.inserted is False
    assert replay.change is None
    assert replay.previous_state == replay.current_state


def test_shared_subject_memory_is_not_partitioned_by_xeed(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    observation = _observation(
        "obs:public",
        fields=(ObservedField("capabilities", "CNC machining"),),
    )
    memory.append(observation)

    # Xeed-specific meaning is computed elsewhere; public observation memory is
    # keyed by canonical subject and therefore reusable by any authorized Xeed.
    first_reader_state = compile_observation_state("org:acme", memory.for_subject("org:acme"))
    second_reader_state = compile_observation_state("org:acme", memory.for_subject("org:acme"))

    assert first_reader_state == second_reader_state
    assert len(memory.for_subject("org:acme")) == 1


def test_observation_memory_does_not_require_or_create_canonical_evidence(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    observation = _observation(
        "obs:unadmitted",
        fields=(ObservedField("candidate_context", "unverified public claim"),),
    )

    mutation = ingest_observation(memory, observation)

    assert mutation.inserted is True
    assert mutation.current_state.get("candidate_context") is not None
    # Persistence succeeds without an AdmissionDecision by design:
    # INFORMATION SURVIVAL != TRUTH ADMISSION.


def test_observation_requires_reconstructible_raw_material() -> None:
    record = _observation("obs:raw-required").record

    with pytest.raises(ValueError, match="raw content or an immutable artifact reference"):
        GovernedObservation(record=record)


def test_immutable_artifact_reference_can_back_raw_observation(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    template = _observation("obs:artifact")
    observation = GovernedObservation(
        record=template.record,
        raw_artifact_ref="sha256-artifact:abc123",
        fields=(ObservedField("markets", "Spain"),),
    )

    assert memory.append(observation) is True
    assert memory.for_subject("org:acme") == (observation,)


def test_storage_normalizes_time_to_utc_and_preserves_chronological_history(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    cet = timezone(timedelta(hours=2))
    first = GovernedObservation(
        record=ObservationRecord(
            observation_id="obs:first",
            subject_id="org:acme",
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=datetime(2026, 9, 30, 14, 0, tzinfo=cet),
            content_fingerprint="sha256:first",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="first snapshot",
    )
    second = GovernedObservation(
        record=ObservationRecord(
            observation_id="obs:second",
            subject_id="org:acme",
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=datetime(2026, 9, 30, 12, 30, tzinfo=UTC),
            content_fingerprint="sha256:second",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="second snapshot",
    )

    memory.append(second)
    memory.append(first)

    history = memory.for_subject("org:acme")
    assert [item.record.observation_id for item in history] == ["obs:first", "obs:second"]
    assert all(item.record.observed_at.tzinfo == UTC for item in history)


def test_concurrent_exact_replay_inserts_once(tmp_path: Path) -> None:
    database = tmp_path / "memory.sqlite3"
    observation = _observation(
        "obs:concurrent",
        fields=(ObservedField("markets", "Spain"),),
    )

    def append_once() -> bool:
        return SqliteObservationMemory(database).append(observation)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: append_once(), range(2)))

    assert sorted(results) == [False, True]
    assert SqliteObservationMemory(database).for_subject("org:acme") == (observation,)


def test_state_fingerprint_is_timezone_representation_independent() -> None:
    cet = timezone(timedelta(hours=2))
    utc_observation = GovernedObservation(
        record=ObservationRecord(
            observation_id="obs:same-instant",
            subject_id="org:acme",
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=datetime(2026, 9, 30, 12, 0, tzinfo=UTC),
            content_fingerprint="sha256:same",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="snapshot",
        fields=(ObservedField("markets", "Spain"),),
    )
    cet_observation = GovernedObservation(
        record=ObservationRecord(
            observation_id="obs:same-instant",
            subject_id="org:acme",
            source_ref="https://example.com/acme",
            source_type="OFFICIAL_WEB",
            observed_at=datetime(2026, 9, 30, 14, 0, tzinfo=cet),
            content_fingerprint="sha256:same",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content="snapshot",
        fields=(ObservedField("markets", "Spain"),),
    )

    utc_state = compile_observation_state("org:acme", (utc_observation,))
    cet_state = compile_observation_state("org:acme", (cet_observation,))

    assert utc_state.fingerprint == cet_state.fingerprint


def test_access_metadata_does_not_load_raw_observation_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory = SqliteObservationMemory(tmp_path / "metadata-only.sqlite3")
    observation = _observation("obs:metadata")
    assert memory.append(observation) is True

    def fail_full_load(*_args, **_kwargs):
        raise AssertionError("metadata authorization must not load raw observation material")

    monkeypatch.setattr(memory, "_load_by_id", fail_full_load)

    metadata = memory.access_metadata("org:acme", "obs:metadata")

    assert metadata is not None
    assert metadata.record.observation_id == "obs:metadata"
    assert metadata.record.subject_id == "org:acme"
    assert not hasattr(metadata, "raw_content")
    assert not hasattr(metadata, "raw_artifact_ref")
