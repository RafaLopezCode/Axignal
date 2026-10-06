from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
    run_research_runtime_tick,
)
from pipeline.continuous_observation import SqliteResearchRuntimeStore

NOW = datetime(2026, 10, 6, 8, 0, tzinfo=UTC)


def _policy(mode=ResearchRuntimeMode.ENABLED, *, global_limit=2, subject_limit=1):
    return ResearchRuntimePolicy(
        policy_id="pb09",
        version="1",
        mode=mode,
        wake_interval=timedelta(minutes=5),
        max_global_inflight=global_limit,
        max_subject_inflight=subject_limit,
        inflight_lease_for=timedelta(minutes=15),
        canary_subject_ids=frozenset({"org:canary"}) if mode is ResearchRuntimeMode.CANARY else frozenset(),
    )


class _Runner:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def run(self, *, now, execution_id):
        self.calls.append((now, execution_id))
        if self.fail:
            raise RuntimeError("cycle failure")
        return None


def test_disabled_runtime_never_executes(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    runner = _Runner()
    tick = run_research_runtime_tick(
        store=store, runner=runner, policy=_policy(ResearchRuntimeMode.DISABLED),
        subject_id="org:a", now=NOW, execution_id="tick:1",
    )
    assert not tick.ran
    assert runner.calls == []


def test_kill_switch_is_durable_and_prevents_dispatch(tmp_path) -> None:
    path = tmp_path / "runtime.sqlite3"
    store = SqliteResearchRuntimeStore(path)
    store.set_kill_switch(True)
    reopened = SqliteResearchRuntimeStore(path)
    runner = _Runner()
    tick = run_research_runtime_tick(
        store=reopened, runner=runner, policy=_policy(),
        subject_id="org:a", now=NOW, execution_id="tick:1",
    )
    assert tick.reason == "disabled"
    assert runner.calls == []


def test_canary_allowlist_is_enforced_before_acquire(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    runner = _Runner()
    denied = run_research_runtime_tick(
        store=store, runner=runner, policy=_policy(ResearchRuntimeMode.CANARY),
        subject_id="org:not-canary", now=NOW, execution_id="tick:1",
    )
    assert denied.reason == "outside-canary"
    assert store.snapshot().cycles_started == 0


def test_wake_interval_survives_restart(tmp_path) -> None:
    path = tmp_path / "runtime.sqlite3"
    store = SqliteResearchRuntimeStore(path)
    runner = _Runner()
    first = run_research_runtime_tick(
        store=store, runner=runner, policy=_policy(),
        subject_id="org:a", now=NOW, execution_id="tick:1",
    )
    assert first.ran
    reopened = SqliteResearchRuntimeStore(path)
    second = run_research_runtime_tick(
        store=reopened, runner=runner, policy=_policy(),
        subject_id="org:a", now=NOW + timedelta(minutes=4), execution_id="tick:2",
    )
    assert second.reason == "not-due"
    assert len(runner.calls) == 1


def test_atomic_global_and_subject_concurrency_limits(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    policy = _policy(global_limit=2, subject_limit=1)
    assert store.try_acquire(subject_id="org:a", now=NOW, policy=policy)
    assert not store.try_acquire(subject_id="org:a", now=NOW, policy=policy)
    assert store.try_acquire(subject_id="org:b", now=NOW, policy=policy)
    assert not store.try_acquire(subject_id="org:c", now=NOW, policy=policy)
    assert store.snapshot().global_inflight == 2


def test_failure_releases_capacity_and_records_health(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    with pytest.raises(RuntimeError, match="cycle failure"):
        run_research_runtime_tick(
            store=store, runner=_Runner(fail=True), policy=_policy(),
            subject_id="org:a", now=NOW, execution_id="tick:fail",
        )
    snapshot = store.snapshot()
    assert snapshot.global_inflight == 0
    assert snapshot.status.value == "ERROR"
    assert snapshot.last_error_type == "RuntimeError"
    assert snapshot.cycles_started == snapshot.cycles_completed == 1


def test_success_records_operational_snapshot_without_epistemic_payload(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    tick = run_research_runtime_tick(
        store=store, runner=_Runner(), policy=_policy(),
        subject_id="org:a", now=NOW, execution_id="tick:ok",
    )
    assert tick.ran
    assert tick.snapshot.global_inflight == 0
    assert tick.snapshot.cycles_started == tick.snapshot.cycles_completed == 1
    assert tick.snapshot.last_error_type is None


def test_expired_inflight_is_reaped_after_process_crash(tmp_path) -> None:
    path = tmp_path / "runtime.sqlite3"
    store = SqliteResearchRuntimeStore(path)
    policy = _policy(global_limit=1, subject_limit=1)
    assert store.try_acquire(subject_id="org:crashed", now=NOW, policy=policy)
    reopened = SqliteResearchRuntimeStore(path)
    assert reopened.try_acquire(
        subject_id="org:next",
        now=NOW + timedelta(minutes=16),
        policy=policy,
    )
    snapshot = reopened.snapshot()
    assert snapshot.global_inflight == 1
