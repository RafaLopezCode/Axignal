"""TASK-050 T022/T023: checkpoints, declared dependencies, temporal invalidation, history."""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from application.economic_discovery.observation_memory import (
    ObservationFieldState,
    ObservedField,
)
from application.economic_discovery.observation_memory import (
    ObservationRightsStatus as Rights,
)
from application.subscriber_continuity.delta import DeltaKind, invalidation_delta, state_delta
from application.subscriber_continuity.dependencies import evaluate_dependencies
from application.subscriber_continuity.derive import _observation_dependency
from application.subscriber_continuity.model import DependencyStatus, InvalidationAction
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from tests.economic_discovery.test_first_vertical_e2e import _run_fixture
from tests.subscriber_continuity.harness import (
    POLICY,
    REUSE,
    Auth,
    observation,
    public,
    runtime,
    seed_eb04_evidence,
)


@pytest.fixture
def brain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):  # type: ignore[no-untyped-def]
    result, *_ = _run_fixture(monkeypatch, tmp_path / "eb04")
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    organization_id, activity_id = seed_eb04_evidence(result, memory)
    auth = Auth()
    context, xeed = auth.focus(1, Organization(OrganizationId(organization_id), "Arbor Cooling"))
    economic, store = runtime(tmp_path, auth, memory)
    t0 = result.reasoning.vector.evaluated_at
    return result, economic, store, context, xeed, memory, t0, organization_id, activity_id


def test_snapshot_publication_records_one_traced_checkpoint(brain) -> None:  # type: ignore[no-untyped-def]
    result, economic, store, context, xeed, _memory, t0, organization_id, _ = brain
    assert economic.publish(context, xeed.id, result) is True
    (s1,) = store.history(xeed.tenant_id, xeed.id)
    assert s1.origin.previous_checkpoint_id is None and s1.sequence == 1
    assert s1.origin.organization_id == organization_id
    assert s1.origin.temporal_cut == t0 and s1.origin.snapshot_refs
    assert {item.kind for item in s1.state.items} == {"ECONOMIC_DIMENSION"}
    assert all(item.dependency_keys for item in s1.state.items)
    assert s1.state.dependencies and all(d.key.startswith("obs:") for d in s1.state.dependencies)
    # T022: the trace binds the EB-04 replay refs (and MarketMap when executed by plan).
    assert s1.state.trace == {} or "replayRefs" in s1.state.trace
    # Replay of the same snapshot: no new snapshot, no new checkpoint.
    assert economic.publish(context, xeed.id, result) is False
    assert len(store.history(xeed.tenant_id, xeed.id)) == 1


def test_no_semantic_change_creates_no_checkpoint_or_delta(brain) -> None:  # type: ignore[no-untyped-def]
    result, economic, store, context, xeed, *_rest, t0, _org, _act = brain
    economic.publish(context, xeed.id, result)
    service = economic.continuity
    # A later cut with the same meaning (still CURRENT): clocks alone change nothing.
    s1_again, created = service.record(context, xeed.id, as_of=t0 + timedelta(days=1))
    assert created is False
    assert len(store.history(xeed.tenant_id, xeed.id)) == 1
    read = service.read(context, xeed.id, as_of=t0 + timedelta(days=1))
    assert read["currentSupport"]["isCurrent"] is True
    assert read["currentSupport"]["delta"]["counts"] == {"UNCHANGED": len(s1_again.state.items)}


def test_t0_t1_t2_stale_is_explained_without_rewriting_history(brain) -> None:  # type: ignore[no-untyped-def]
    result, economic, store, context, xeed, _memory, t0, *_ = brain
    economic.publish(context, xeed.id, result)
    service = economic.continuity
    (s1,) = store.history(xeed.tenant_id, xeed.id)
    raw = _raw(store, s1.checkpoint_id)
    # t1: still current; nothing owed, nothing invalidated.
    t1 = service.reconcile(xeed.tenant_id, xeed.id, now=t0 + timedelta(days=1))
    assert set(t1.statuses.values()) == {"CURRENT"} and t1.new_invalidations == 0
    # t2: support aged past the policy. Stale is not false: REVALIDATE, not recompute.
    t2 = t0 + timedelta(days=8)
    report = service.reconcile(xeed.tenant_id, xeed.id, now=t2)
    assert set(report.statuses.values()) == {"STALE"} and report.owed == ()
    assert service.reconcile(xeed.tenant_id, xeed.id, now=t2).new_invalidations == 0  # idempotent
    read = service.read(context, xeed.id, as_of=t2)
    assert read["currentSupport"]["isCurrent"] is False
    assert set(read["currentSupport"]["delta"]["counts"]) == {"STALE"}
    assert {item["action"] for item in read["invalidations"]} == {"REVALIDATE"}
    # A new checkpoint at t2 records the new state; S1 stays exactly as written.
    s2, created = service.record(context, xeed.id, as_of=t2)
    assert created and s2.origin.previous_checkpoint_id == s1.checkpoint_id
    assert all(item.epistemic == "UNKNOWN" for item in s2.state.items)  # not shown as current
    delta = state_delta(s1.state, s2.state)
    assert {entry.kind for entry in delta.entries if entry.subject == "ITEM"} == {DeltaKind.UNKNOWN}
    assert _raw(store, s1.checkpoint_id) == raw
    # Historical read: the cut t0 still sees S1 as it was.
    historical = service.read(context, xeed.id, as_of=t0)
    assert historical["checkpoint"]["checkpointId"] == s1.checkpoint_id
    assert historical["currentSupport"]["isCurrent"] is True


def test_withdrawn_replaced_rights_and_unrelated_evidence(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    t0 = _t0()
    subject, other = "org:one", "org:two"
    capability = observation(
        subject,
        "cap:1",
        source_ref="https://one.example.com/",
        observed_at=t0,
        content="solar installation",
        fields=(ObservedField("capability", "solar installation"),),
    )
    page = observation(
        subject, "page:1", source_ref="https://one.example.com/about", observed_at=t0, content="a"
    )
    for item in (capability, page):
        memory.append(item)
    deps = (_observation_dependency(capability), _observation_dependency(page))

    def statuses(at=t0 + timedelta(hours=2)):  # type: ignore[no-untyped-def]
        return {
            key: item.status
            for key, item in evaluate_dependencies(
                deps,
                memory=memory,
                tenant_id="tenant:1",
                xeed_id="focus_1",
                as_of=at,
                reuse_policy=REUSE,
                temporal_policy=POLICY,
            ).items()
        }

    assert set(statuses().values()) == {DependencyStatus.CURRENT}
    # Unrelated evidence (another subject, another source) changes nothing.
    memory.append(
        observation(
            other, "other:1", source_ref="https://two.example.com/", observed_at=t0, content="x"
        )
    )
    memory.append(
        observation(
            subject,
            "news:1",
            source_ref="https://one.example.com/news",
            observed_at=t0 + timedelta(hours=1),
            content="n",
        )
    )
    assert set(statuses().values()) == {DependencyStatus.CURRENT}
    # Same meaning observed again: REFRESHED, not a change.
    memory.append(
        observation(
            subject,
            "cap:2",
            source_ref="https://one.example.com/",
            observed_at=t0 + timedelta(hours=1),
            content="solar installation v2",
            fields=(ObservedField("capability", "solar installation"),),
        )
    )
    assert statuses()["obs:cap:1"] is DependencyStatus.REFRESHED
    # Meaning withdrawn by a later observation (EB-06 typed state): RECOMPUTE.
    memory.append(
        observation(
            subject,
            "cap:3",
            source_ref="https://one.example.com/",
            observed_at=t0 + timedelta(hours=1, minutes=30),
            content="withdrawn",
            fields=(
                ObservedField("capability", "solar installation", ObservationFieldState.WITHDRAWN),
            ),
        )
    )
    evaluated = evaluate_dependencies(
        deps,
        memory=memory,
        tenant_id="tenant:1",
        xeed_id="focus_1",
        as_of=t0 + timedelta(hours=2),
        reuse_policy=REUSE,
        temporal_policy=POLICY,
    )
    assert evaluated["obs:cap:1"].status is DependencyStatus.WITHDRAWN
    assert evaluated["obs:cap:1"].action is InvalidationAction.RECOMPUTE
    # Page content replaced at the same source: RECOMPUTE; history before t0+1h unaffected.
    memory.append(
        observation(
            subject,
            "page:2",
            source_ref="https://one.example.com/about",
            observed_at=t0 + timedelta(hours=1),
            content="b",
        )
    )
    assert statuses()["obs:page:1"] is DependencyStatus.REPLACED
    assert set(statuses(t0 + timedelta(minutes=30)).values()) == {DependencyStatus.CURRENT}


def test_rights_lost_or_unknown_make_support_unknown_not_false(tmp_path: Path) -> None:
    memory = SqliteObservationMemory(tmp_path / "memory.sqlite3")
    t0 = _t0()
    blocked = observation(
        "org:one",
        "blocked:1",
        source_ref="https://one.example.com/",
        observed_at=t0,
        content="c",
        authority=public("org:one", "blocked:1", rights_status=Rights.UNKNOWN),
    )
    memory.append(blocked)
    (result,) = evaluate_dependencies(
        (_observation_dependency(blocked),),
        memory=memory,
        tenant_id="tenant:1",
        xeed_id="focus_1",
        as_of=t0 + timedelta(hours=1),
        reuse_policy=REUSE,
        temporal_policy=POLICY,
    ).values()
    assert result.status is DependencyStatus.RIGHTS_BLOCKED
    assert result.action is InvalidationAction.UNKNOWN  # never FALSE, never silently current
    missing = evaluate_dependencies(
        (_observation_dependency(blocked),),
        memory=SqliteObservationMemory(tmp_path / "empty.sqlite3"),
        tenant_id="tenant:1",
        xeed_id="focus_1",
        as_of=t0,
        reuse_policy=REUSE,
        temporal_policy=POLICY,
    )
    assert next(iter(missing.values())).status is DependencyStatus.MISSING


def test_invalidation_is_selective_per_item(brain) -> None:  # type: ignore[no-untyped-def]
    result, economic, store, context, xeed, memory, t0, *_ = brain
    economic.publish(context, xeed.id, result)
    (s1,) = store.history(xeed.tenant_id, xeed.id)
    target = s1.state.items[0]
    dependency = next(d for d in s1.state.dependencies if d.key == target.dependency_keys[0])
    others = [item for item in s1.state.items if dependency.key not in item.dependency_keys]
    memory.append(
        observation(
            str(dependency.subject_id),
            "replacement:1",
            source_ref=dependency.source_ref,
            observed_at=t0 + timedelta(hours=1),
            content="changed content",
        )
    )
    evaluations = evaluate_dependencies(
        s1.state.dependencies,
        memory=memory,
        tenant_id=xeed.tenant_id,
        xeed_id=xeed.id,
        as_of=t0 + timedelta(hours=2),
        reuse_policy=REUSE,
        temporal_policy=POLICY,
    )
    delta = invalidation_delta(s1.state, evaluations)
    kinds = {entry.key: entry.kind for entry in delta.entries}
    assert kinds[target.key] is DeltaKind.INVALIDATED
    assert all(kinds[item.key] is DeltaKind.UNCHANGED for item in others)


def _t0():  # type: ignore[no-untyped-def]
    from datetime import UTC, datetime

    return datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def _raw(store, checkpoint_id: str) -> tuple[object, ...]:  # type: ignore[no-untyped-def]
    with sqlite3.connect(store._path) as connection:
        return tuple(
            connection.execute(
                "SELECT * FROM subscriber_continuity_checkpoints WHERE checkpoint_id=?",
                (checkpoint_id,),
            ).fetchone()
        )


def test_historical_read_ignores_evidence_observed_after_the_cut(brain) -> None:  # type: ignore[no-untyped-def]
    """Regression: newer evidence used to make every historical subscriber read raise."""
    result, economic, _store, context, xeed, memory, t0, organization_id, _ = brain
    economic.publish(context, xeed.id, result)
    later = t0 + timedelta(days=2)
    memory.append(
        observation(
            organization_id,
            "later:1",
            source_ref="https://later.example.com/",
            observed_at=later,
            content="later",
        )
    )
    historical = economic.read(context, xeed.id, t0)
    assert historical.status.value == "success"
    assert all(
        item["observedAt"] <= t0.isoformat()
        for item in historical.projection["temporalHistory"]["items"]
    )
    assert economic.continuity.read(context, xeed.id, as_of=t0)["currentSupport"]["isCurrent"]


class _Tick:
    """A T12 owed-work queue whose live tick refuses writes until it finishes."""

    def __init__(self) -> None:
        self.live = True
        self.owed: list[tuple[str, str, tuple[str, ...]]] = []

    def owe_recompute(self, *, xeed_id, family, evidence_keys, now):  # type: ignore[no-untyped-def]
        if self.live:
            return False
        self.owed.append((xeed_id, family, evidence_keys))
        return True


def test_owed_recompute_is_never_lost_while_a_tick_holds_the_lease(brain) -> None:  # type: ignore[no-untyped-def]
    result, economic, store, context, xeed, memory, t0, *_ = brain
    economic.publish(context, xeed.id, result)
    (s1,) = store.history(xeed.tenant_id, xeed.id)
    dependency = s1.state.dependencies[0]
    memory.append(
        observation(
            str(dependency.subject_id),
            "replacement:9",
            source_ref=dependency.source_ref,
            observed_at=t0 + timedelta(hours=1),
            content="changed again",
        )
    )
    # EB-04 dimensions have no T12 family: owe them under a family to exercise delivery.
    from dataclasses import replace

    from application.subscriber_continuity.model import ContinuityState

    state = s1.state
    store.append(
        xeed.tenant_id,
        xeed.id,
        ContinuityState(
            state.organization_id,
            state.snapshot_refs,
            t0 + timedelta(minutes=1),
            tuple(replace(item, family="demand") for item in state.items),
            state.questions,
            state.dependencies,
            state.trace,
        ),
    )
    tick = _Tick()
    held = economic.continuity.reconcile(
        xeed.tenant_id, xeed.id, now=t0 + timedelta(hours=2), owe=tick
    )
    assert held.owed == ("demand",) and held.delivered == () and tick.owed == []
    tick.live = False
    delivered = economic.continuity.reconcile(
        xeed.tenant_id, xeed.id, now=t0 + timedelta(hours=3), owe=tick
    )
    assert delivered.delivered == ("demand",) and len(tick.owed) == 1
    again = economic.continuity.reconcile(
        xeed.tenant_id, xeed.id, now=t0 + timedelta(hours=4), owe=tick
    )
    assert again.delivered == () and len(tick.owed) == 1  # delivered once, no storm
