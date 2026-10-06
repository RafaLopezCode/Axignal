from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.economic_discovery.async_research_runtime import (
    AsyncResearchRuntimeCycle,
    run_async_research_runtime_tick,
)
from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
)
from pipeline.continuous_observation.runtime_store import SqliteResearchRuntimeStore

NOW = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)


def _policy(mode=ResearchRuntimeMode.CANARY, *, global_limit=1) -> ResearchRuntimePolicy:
    return ResearchRuntimePolicy(
        policy_id="pb11-runtime",
        version="1",
        mode=mode,
        wake_interval=timedelta(minutes=5),
        max_global_inflight=global_limit,
        max_subject_inflight=1,
        inflight_lease_for=timedelta(hours=27),
        canary_subject_ids=frozenset({"org:canary"})
        if mode is ResearchRuntimeMode.CANARY
        else frozenset(),
    )


class _Runner:
    def __init__(self, actions):
        self.actions = list(actions)
        self.active = False
        self.calls = []

    def has_active(self, subject_id):
        del subject_id
        return self.active

    def run(self, *, subject_id, now, execution_id, allow_submit):
        self.calls.append((subject_id, now, execution_id, allow_submit))
        action = self.actions.pop(0)
        self.active = action in {"submitted", "pending"}
        return AsyncResearchRuntimeCycle(action=action)


def test_submitted_batch_keeps_runtime_capacity_until_terminal_collection(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    runner = _Runner(["submitted", "pending", "completed"])

    first = run_async_research_runtime_tick(
        store=store,
        runner=runner,
        policy=_policy(),
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:1",
    )
    assert first.reason == "submitted"
    assert first.snapshot.global_inflight == 1

    pending = run_async_research_runtime_tick(
        store=store,
        runner=runner,
        policy=_policy(),
        subject_id="org:canary",
        now=NOW + timedelta(minutes=1),
        execution_id="pb11:poll",
    )
    assert pending.reason == "pending"
    assert pending.snapshot.global_inflight == 1

    done = run_async_research_runtime_tick(
        store=store,
        runner=runner,
        policy=_policy(),
        subject_id="org:canary",
        now=NOW + timedelta(minutes=2),
        execution_id="pb11:collect",
    )
    assert done.reason == "completed"
    assert done.snapshot.global_inflight == 0
    assert done.snapshot.cycles_started == done.snapshot.cycles_completed == 1


def test_kill_switch_blocks_submit_but_allows_existing_batch_collection(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    runner = _Runner(["submitted", "completed"])
    run_async_research_runtime_tick(
        store=store,
        runner=runner,
        policy=_policy(),
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:1",
    )
    store.set_kill_switch(True)

    collected = run_async_research_runtime_tick(
        store=store,
        runner=runner,
        policy=_policy(),
        subject_id="org:canary",
        now=NOW + timedelta(minutes=1),
        execution_id="pb11:collect",
    )
    assert collected.reason == "completed"
    assert collected.snapshot.global_inflight == 0

    blocked = run_async_research_runtime_tick(
        store=store,
        runner=_Runner(["submitted"]),
        policy=_policy(),
        subject_id="org:canary",
        now=NOW + timedelta(minutes=10),
        execution_id="pb11:new",
    )
    assert blocked.reason == "disabled"


def test_canary_allowlist_and_global_capacity_are_enforced_before_submit(tmp_path) -> None:
    store = SqliteResearchRuntimeStore(tmp_path / "runtime.sqlite3")
    denied_runner = _Runner(["submitted"])
    denied = run_async_research_runtime_tick(
        store=store,
        runner=denied_runner,
        policy=_policy(),
        subject_id="org:not-canary",
        now=NOW,
        execution_id="pb11:denied",
    )
    assert denied.reason == "outside-canary"
    assert denied_runner.calls == []

    first = _Runner(["submitted"])
    run_async_research_runtime_tick(
        store=store,
        runner=first,
        policy=_policy(global_limit=1),
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:first",
    )
    second = _Runner(["submitted"])
    blocked = run_async_research_runtime_tick(
        store=store,
        runner=second,
        policy=ResearchRuntimePolicy(
            policy_id="pb11-runtime",
            version="1",
            mode=ResearchRuntimeMode.CANARY,
            wake_interval=timedelta(minutes=5),
            max_global_inflight=1,
            max_subject_inflight=1,
            inflight_lease_for=timedelta(hours=27),
            canary_subject_ids=frozenset({"org:canary", "org:second"}),
        ),
        subject_id="org:second",
        now=NOW + timedelta(seconds=1),
        execution_id="pb11:second",
    )
    assert blocked.reason == "concurrency-limit"
    assert second.calls == []
