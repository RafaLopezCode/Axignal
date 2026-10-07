"""EB-07 shared work → one fenced execution → global evidence → dependent continuity.

The shared-work authority is the existing EB-07 store (work key, requester ledger,
token leases). Its result lands in global Observation Memory; only a completion that
still owns its lease fans out to dependent Foci, through the continuity index.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery.batch_research import (
    claim_research_batch,
    complete_research_batch,
)
from application.economic_discovery.continuous_observation import (
    SharedObservationIntent,
    opaque_requester_ref,
)
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _intent(**overrides: str) -> SharedObservationIntent:
    values = {
        "subject_id": "org:shared",
        "state_fingerprint": "state:1",
        "dimension_id": "demand",
        "missing_requirements": ("public-buyer-evidence",),
        "research_policy_id": "public-research",
        "research_policy_version": "1",
        "research_context_fingerprint": "ted-search@3:EU/ES",
    }
    values.update(overrides)
    return SharedObservationIntent(**values)  # type: ignore[arg-type]


def test_two_consumers_share_one_fenced_execution(tmp_path: Path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    ref_a = opaque_requester_ref("focus", "tenant:a", "focus_a")
    ref_b = opaque_requester_ref("focus", "tenant:b", "focus_b")
    assert memory.enqueue(_intent(), ref_a) is True
    assert memory.enqueue(_intent(), ref_b) is False  # same governed work: one row
    work = memory.get(_intent().work_key)
    assert work is not None and work.requester_refs == tuple(sorted((ref_a, ref_b)))
    # No private identifier reaches the shared ledger.
    assert all("tenant:" not in ref and "focus_" not in ref for ref in work.requester_refs)

    worker_a = claim_research_batch(
        memory,
        work_keys=(_intent().work_key,),
        now=T0,
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    worker_b = claim_research_batch(
        memory,
        work_keys=(_intent().work_key,),
        now=T0,
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    assert len(worker_a) == 1 and worker_b == ()  # simultaneous claim: one authority

    changed: list[tuple[str, datetime]] = []
    done = complete_research_batch(
        memory,
        claimed=worker_a,
        completed_at=T0 + timedelta(minutes=1),
        on_subject_changed=lambda subject, at: changed.append((subject, at)),
    )
    assert done == (_intent().work_key,) and changed == [("org:shared", T0 + timedelta(minutes=1))]
    # Duplicate replay of the same completion: no second execution, no second fan-out.
    assert (
        complete_research_batch(
            memory,
            claimed=worker_a,
            completed_at=T0 + timedelta(minutes=2),
            on_subject_changed=lambda *_: changed.append(("again", T0)),
        )
        == ()
    )
    assert len(changed) == 1


def test_a_stale_owner_cannot_commit_after_the_lease_moves(tmp_path: Path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    memory.enqueue(_intent(), opaque_requester_ref("focus", "tenant:a", "focus_a"))
    stale = claim_research_batch(
        memory,
        work_keys=(_intent().work_key,),
        now=T0,
        lease_for=timedelta(minutes=1),
        max_batch_size=1,
    )
    # Worker A dies; its lease expires; worker B obtains a new lease (new fencing token).
    fresh = claim_research_batch(
        memory,
        work_keys=(_intent().work_key,),
        now=T0 + timedelta(minutes=2),
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    assert fresh and fresh[0].lease.lease_token != stale[0].lease.lease_token
    fanned: list[str] = []
    late = complete_research_batch(
        memory,
        claimed=stale,
        completed_at=T0 + timedelta(minutes=3),
        on_subject_changed=lambda subject, _at: fanned.append(subject),
    )
    assert late == () and fanned == []  # the late result is not authority and invalidates nothing
    assert complete_research_batch(
        memory,
        claimed=fresh,
        completed_at=T0 + timedelta(minutes=3),
        on_subject_changed=lambda subject, _at: fanned.append(subject),
    ) == (_intent().work_key,)
    assert fanned == ["org:shared"]
    # Restart: a new process sees the work complete and cannot claim it again.
    restarted = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    assert (
        restarted.claim(
            _intent().work_key, now=T0 + timedelta(hours=1), lease_for=timedelta(minutes=1)
        )
        is None
    )


def test_incompatible_instrument_or_policy_version_is_never_reused(tmp_path: Path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    memory.enqueue(_intent(), opaque_requester_ref("focus", "tenant:a", "focus_a"))
    for variant in (
        _intent(research_policy_version="2"),
        _intent(research_context_fingerprint="ted-search@4:EU/ES"),
        _intent(subject_id="org:other"),  # different Organization: no cross-subject reuse
        _intent(state_fingerprint="state:2"),  # changed state: new work, old history kept
    ):
        assert variant.work_key != _intent().work_key
        assert memory.enqueue(variant, opaque_requester_ref("focus", "tenant:b", "focus_b")) is True
    assert len(memory.pending_work_keys()) == 5


@pytest.mark.parametrize(
    "ref", ["focus_0123abcd", "tenant:acme", "principal:alice", "pending_42", "mcpgrant_x"]
)
def test_private_subscriber_identifiers_never_enter_the_shared_ledger(
    tmp_path: Path, ref: str
) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "research-work.sqlite3")
    with pytest.raises(ValueError):
        memory.enqueue(_intent(), ref)
    assert memory.pending_work_keys() == ()


def test_opaque_requester_refs_are_stable_and_reveal_nothing() -> None:
    first = opaque_requester_ref("focus", "tenant:a", "focus_a")
    assert first == opaque_requester_ref("focus", "tenant:a", "focus_a")
    assert first != opaque_requester_ref("focus", "tenant:b", "focus_a")
    assert "tenant" not in first.split(":", 1)[1] and "focus_a" not in first
