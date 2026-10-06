from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.batch_research import (
    claim_research_batch,
    complete_research_batch,
    release_research_batch,
)
from application.economic_discovery.continuous_observation import SharedObservationIntent
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 4, 30, tzinfo=UTC)


def _intent(dimension: str) -> SharedObservationIntent:
    return SharedObservationIntent(
        subject_id="org:acme",
        state_fingerprint="state:1",
        dimension_id=dimension,
        missing_requirements=(f"{dimension}.missing",),
        research_policy_id="research:value",
        research_policy_version="1",
        research_context_fingerprint=f"context:{dimension}",
    )


def _memory(tmp_path, *dimensions: str):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intents = tuple(_intent(dimension) for dimension in dimensions)
    for intent in intents:
        assert memory.enqueue(intent, "prime:test") is True
    return memory, intents


def test_claim_is_bounded_and_independent_work_continues(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo", "market")
    first_lease = memory.claim(intents[0].work_key, now=NOW, lease_for=timedelta(minutes=1))
    assert first_lease is not None

    claimed = claim_research_batch(
        memory,
        work_keys=tuple(intent.work_key for intent in intents),
        now=NOW,
        lease_for=timedelta(minutes=1),
        max_batch_size=1,
    )

    assert len(claimed) == 1
    assert claimed[0].work.intent.dimension_id == "geo"


def test_release_does_not_create_retry_and_allows_later_claim(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo")
    claimed = claim_research_batch(
        memory,
        work_keys=(intents[0].work_key,),
        now=NOW,
        lease_for=timedelta(minutes=1),
        max_batch_size=1,
    )

    assert release_research_batch(memory, claimed=claimed) == (intents[0].work_key,)
    later = claim_research_batch(
        memory,
        work_keys=(intents[0].work_key,),
        now=NOW + timedelta(seconds=1),
        lease_for=timedelta(minutes=1),
        max_batch_size=1,
    )
    assert len(later) == 1
    assert later[0].lease.lease_token != claimed[0].lease.lease_token


def test_completion_is_lease_fenced(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo")
    claimed = claim_research_batch(
        memory,
        work_keys=(intents[0].work_key,),
        now=NOW,
        lease_for=timedelta(minutes=1),
        max_batch_size=1,
    )
    assert complete_research_batch(
        memory,
        claimed=claimed,
        completed_at=NOW + timedelta(seconds=10),
    ) == (intents[0].work_key,)
    assert release_research_batch(memory, claimed=claimed) == ()


@pytest.mark.parametrize(
    ("work_keys", "lease_for", "max_batch_size", "message"),
    [
        (("x", "x"), timedelta(minutes=1), 1, "unique"),
        (("",), timedelta(minutes=1), 1, "blank"),
        (("x",), timedelta(0), 1, "duration"),
        (("x",), timedelta(minutes=1), 0, "size"),
    ],
)
def test_invalid_claim_bounds_fail_closed(
    tmp_path, work_keys, lease_for, max_batch_size, message
) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    with pytest.raises(ValueError, match=message):
        claim_research_batch(
            memory,
            work_keys=work_keys,
            now=NOW,
            lease_for=lease_for,
            max_batch_size=max_batch_size,
        )
