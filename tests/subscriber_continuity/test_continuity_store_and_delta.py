"""Store invariants, semantic delta, open questions, migration and the T12 owe fence."""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.observation_runtime.families import ObservationFamily
from application.observation_runtime.ports import PendingRecompute, RecomputeTrigger
from application.subscriber_continuity.delta import DeltaKind, state_delta
from application.subscriber_continuity.derive import derive_continuity_state
from application.subscriber_continuity.model import QuestionKind
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from pipeline.subscriber_projection.continuity_store import SqliteSubscriberContinuityStore
from pipeline.subscriber_projection.sqlite_store import SqliteSubscriberEconomicOutputStore

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _projection(
    *,
    epistemic: str = "POTENTIAL",
    currentness: str = "CURRENT",
    evaluated: datetime = T0,
    reverse: bool = False,
    unknown_value: bool = True,
    opportunities: int = 2,
) -> dict[str, object]:
    items = [
        {
            "id": f"cand:{n}",
            "familyId": "demand",
            "opportunityFamily": "PUBLIC_PROCUREMENT",
            "title": f"Solar plant {n}",
            "buyer": "Ayuntamiento",
            "market": "ES",
            "form": "TENDER",
            "deadline": "2026-11-01",
            "epistemic": epistemic,
            "currentness": currentness,
            "currentnessEvaluatedAt": evaluated.isoformat(),
            "capability": {"label": "solar", "sourceId": "page:1"},
            "demand": {"code": "09331200", "sourceId": f"opportunity-evidence:{n}"},
            "unknown": ["Price and capacity were not assessed."],
            "matchBasis": ["cpv", "keyword"] if not reverse else ["keyword", "cpv"],
        }
        for n in range(opportunities)
    ]
    sources = [
        {
            "id": f"opportunity-evidence:{n}",
            "observedAt": T0.isoformat(),
            "sourceRef": f"https://ted.example.com/{n}",
            "provenanceRef": f"ted:{n}",
            "title": f"Solar plant {n}",
            "instrument": "ted-search@3",
            "currentnessEvaluatedAt": evaluated.isoformat(),
        }
        for n in range(opportunities)
    ]
    return {
        "cognition": {
            "opportunities": items[::-1] if reverse else items,
            "sources": sources[::-1] if reverse else sources,
            "asOf": evaluated.isoformat(),
        },
        "economicOutput": {
            "epistemic_state": epistemic,
            "temporal_state": currentness,
            "dimensions": [
                {
                    "dimension_id": "b2g",
                    "value": None if unknown_value else "POTENTIAL",
                    "disposition": "ANSWERABLE",
                    "reason": "No public buyer evidence",
                    "evidence_refs": [],
                },
            ],
            "evidence": [],
        },
        "digitalRepresentation": {"state": "NOT_MEASURED", "reason": {"code": "NO_MEASURE"}},
    }


def _state(memory: SqliteObservationMemory, cut: datetime = T0, **kwargs: object):  # type: ignore[no-untyped-def]
    return derive_continuity_state(
        _projection(**kwargs),
        organization_id="org:one",
        snapshot_refs=("projection:1",),
        execution_trace={"marketMap": {"stateFingerprint": "mm:1"}, "replayRefs": ["r:2", "r:1"]},
        memory=memory,
        temporal_cut=cut,
    )


def test_timestamps_ordering_and_serialization_never_change_meaning(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    a = _state(memory)
    b = _state(memory, cut=T0 + timedelta(hours=5), evaluated=T0 + timedelta(hours=5), reverse=True)
    assert a.semantic_fingerprint == b.semantic_fingerprint
    assert not state_delta(a, b).changed
    assert a.trace["marketMapFingerprint"] == "mm:1" and a.trace["replayRefs"] == ["r:1", "r:2"]


def test_unknown_to_potential_resolves_the_open_question(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    before = _state(memory, epistemic="UNKNOWN", unknown_value=True)
    after = _state(memory, cut=T0 + timedelta(days=1), epistemic="POTENTIAL", unknown_value=False)
    kinds = {(e.subject, e.key): e.kind for e in state_delta(before, after).entries}
    assert kinds[("QUESTION", "q:dimension:b2g")] is DeltaKind.RESOLVED
    assert kinds[("ITEM", "economic:b2g")] is DeltaKind.CHANGED  # UNKNOWN value → POTENTIAL
    assert kinds[("ITEM", "opportunity:cand:0")] is DeltaKind.RESOLVED  # UNKNOWN → POTENTIAL
    question = next(q for q in before.questions if q.key == "q:dimension:b2g")
    assert question.kind is QuestionKind.DIMENSION_UNKNOWN and question.about == "economic:b2g"
    assert {q.kind for q in before.questions} >= {
        QuestionKind.MISSING_CONTEXT,
        QuestionKind.REPRESENTATION_UNMEASURED,
    }


def test_withdrawn_item_and_new_family_question(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    with_two = _state(memory, opportunities=2)
    none = _state(memory, cut=T0 + timedelta(days=1), opportunities=0)
    kinds = {(e.subject, e.key): e.kind for e in state_delta(with_two, none).entries}
    assert kinds[("ITEM", "opportunity:cand:1")] is DeltaKind.WITHDRAWN  # not deleted, not FALSE
    assert kinds[("QUESTION", "q:family:demand")] is DeltaKind.NEW


def test_store_is_append_only_idempotent_and_lineaged(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    store = SqliteSubscriberContinuityStore(tmp_path / "out.sqlite3")
    s1, created = store.append("tenant:1", "focus_1", _state(memory))
    assert created and s1.sequence == 1
    again, created = store.append(
        "tenant:1", "focus_1", _state(memory, cut=T0 + timedelta(hours=1))
    )
    assert not created and again.checkpoint_id == s1.checkpoint_id
    s2, created = store.append(
        "tenant:1", "focus_1", _state(memory, cut=T0 + timedelta(days=1), opportunities=1)
    )
    assert created and s2.origin.previous_checkpoint_id == s1.checkpoint_id and s2.sequence == 2
    assert store.get("tenant:1", "focus_1", s1.checkpoint_id).state == s1.state  # type: ignore[union-attr]
    assert store.latest("tenant:1", "focus_1", as_of=T0).checkpoint_id == s1.checkpoint_id  # type: ignore[union-attr]
    assert store.latest("tenant:2", "focus_1") is None  # keyed by Tenant and Focus
    with pytest.raises(ValueError):
        store.append(
            "tenant:1", "focus_1", _state(memory, cut=T0 - timedelta(days=1), opportunities=0)
        )
    assert store.dependents("org:one") == (("tenant:1", "focus_1"),)


def test_concurrent_recording_of_one_state_creates_one_checkpoint(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    store = SqliteSubscriberContinuityStore(tmp_path / "out.sqlite3")
    state = _state(memory)
    created: list[bool] = []

    def record() -> None:
        created.append(
            SqliteSubscriberContinuityStore(tmp_path / "out.sqlite3").append(
                "tenant:1", "focus_1", state
            )[1]
        )

    threads = [threading.Thread(target=record) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(created) == 1 and len(store.history("tenant:1", "focus_1")) == 1


def test_migration_from_an_existing_output_database_keeps_snapshots(tmp_path: Path) -> None:
    database = tmp_path / "subscriber-economic-output.sqlite3"
    SqliteSubscriberEconomicOutputStore(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO subscriber_economic_outputs VALUES ('tenant:1','focus_1','org:one','out:1',?, '{}','{}')",
            (T0.isoformat(),),
        )
    before = (
        sqlite3.connect(database).execute("SELECT * FROM subscriber_economic_outputs").fetchall()
    )
    SqliteSubscriberContinuityStore(database)  # new binary on the old database
    SqliteSubscriberContinuityStore(database)  # restart: idempotent
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT * FROM subscriber_economic_outputs").fetchall() == before
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {
        "subscriber_continuity_checkpoints",
        "subscriber_continuity_dependents",
        "subscriber_continuity_invalidations",
        "subscriber_continuity_recompute",
    } <= tables


def test_owed_recompute_is_fenced_by_the_t12_tick_lease(tmp_path: Path) -> None:
    store = SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3")
    claim = store.claim_tick("2026-10-01", now=T0, lease_seconds=600)
    assert claim is not None
    # A live tick holds the lease: continuity must not write (the tick would clear it).
    assert not store.owe_recompute(
        xeed_id="focus_1", family="demand", evidence_keys=("obs:a",), now=T0 + timedelta(minutes=1)
    )
    assert store.pending_recompute() == ()
    store.complete_tick(claim, completed_at=T0 + timedelta(minutes=2), report={})
    assert store.owe_recompute(
        xeed_id="focus_1", family="demand", evidence_keys=("obs:a",), now=T0 + timedelta(minutes=3)
    )
    assert store.owe_recompute(
        xeed_id="focus_1", family="demand", evidence_keys=("obs:b",), now=T0 + timedelta(minutes=4)
    )
    restarted = SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3")
    assert restarted.pending_recompute() == (
        PendingRecompute(
            "focus_1",
            ObservationFamily.DEMAND,
            RecomputeTrigger.MATERIAL_CHANGE,
            ("obs:a", "obs:b"),
        ),
    )
    # A crashed tick whose lease expired does not block owed work.
    crashed = restarted.claim_tick("2026-10-02", now=T0 + timedelta(days=1), lease_seconds=60)
    assert crashed is not None
    assert restarted.owe_recompute(
        xeed_id="focus_2",
        family="demand",
        evidence_keys=("obs:c",),
        now=T0 + timedelta(days=1, minutes=5),
    )


def test_invalidations_and_owed_work_are_idempotent(tmp_path: Path) -> None:
    from application.subscriber_continuity.dependencies import DependencyEvaluation
    from application.subscriber_continuity.model import DependencyStatus

    memory = SqliteObservationMemory(tmp_path / "m.sqlite3")
    store = SqliteSubscriberContinuityStore(tmp_path / "out.sqlite3")
    checkpoint, _ = store.append("tenant:1", "focus_1", _state(memory))
    stale = (DependencyEvaluation("demand:x", DependencyStatus.STALE, "DEMAND_RECORD_STALE"),)
    assert store.record_invalidations(checkpoint, stale, evaluated_at=T0) == 1
    assert store.record_invalidations(checkpoint, stale, evaluated_at=T0 + timedelta(days=1)) == 0
    assert store.invalidations("tenant:1", "focus_1", checkpoint.checkpoint_id)[0][
        "firstEvaluatedAt"
    ].startswith("2026-10-01")
    assert store.owe(checkpoint, "demand", ("obs:a",), owed_at=T0)
    assert not store.owe(checkpoint, "demand", ("obs:a",), owed_at=T0 + timedelta(hours=1))
    assert store.undelivered("tenant:1", "focus_1") == (
        (checkpoint.checkpoint_id, "demand", ("obs:a",)),
    )
    store.mark_delivered("tenant:1", "focus_1", checkpoint.checkpoint_id, "demand", at=T0)
    assert store.undelivered("tenant:1", "focus_1") == ()
