"""T12 discriminants: actual entry, overlap, expiry, redacted audit and cost gates."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event

import pytest

from application.observation_intelligence import SourceRegistry
from application.observation_intelligence.catalog import SOURCES
from application.observation_runtime import LeaseLost, TickStatus, run_daily_tick
from application.observation_runtime.ports import Acquisition, AcquisitionPort, AcquisitionRequest
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tests.observation_runtime.harness import ATTENTION, DAY_1, world
from tests.observation_runtime.test_runtime_units import _run
from tools.runtime import observation_daily


class FixedClock:
    def __init__(self, now: datetime = DAY_1) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def _entry(
    root: Path, *, enabled: bool = True, status: bool = False
) -> subprocess.CompletedProcess[str]:
    config = root / "config"
    config.mkdir(exist_ok=True)
    for name in ("attention.json", "enrollment.json"):
        (config / name).write_text("[]", encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.runtime.observation_daily",
            *(["--status"] if status else []),
        ],
        env={
            **os.environ,
            "AXIGNAL_OBSERVATION_RUNTIME_ENABLED": str(enabled).lower(),
            "AXIGNAL_DATA_DIR": str(root / "data"),
            "AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE": str(config / "attention.json"),
            "AXIGNAL_OBSERVATION_RUNTIME_ENROLLMENT_FILE": str(config / "enrollment.json"),
            "AXIGNAL_CODE_SHA": "t12-test",
        },
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def test_disabled_and_status_never_create_runtime_state(tmp_path: Path) -> None:
    disabled = _entry(tmp_path, enabled=False)
    assert disabled.returncode == 0 and json.loads(disabled.stdout) == {"state": "DISABLED"}
    assert not (tmp_path / "data").exists()
    status = _entry(tmp_path, status=True)
    assert status.returncode == 0 and json.loads(status.stdout)["state"] == "NOT_RUN"
    assert not (tmp_path / "data").exists()


def test_real_process_no_work_restart_and_replay_are_durable(tmp_path: Path) -> None:
    first = _entry(tmp_path)
    assert first.returncode == 0, first.stderr
    summary = json.loads(first.stdout)
    assert summary["state"] == "COMPLETED" and summary["stop"] == "NOTHING_DUE"
    assert summary["requests"] == summary["items"] == 0
    restarted = _entry(tmp_path)
    assert restarted.returncode == 0
    assert json.loads(restarted.stdout)["state"] == "ALREADY_COMPLETED"
    status = json.loads(_entry(tmp_path, status=True).stdout)
    assert status["lease_status"] == "COMPLETED"
    assert status["last_invocation"]["summary"]["state"] == "ALREADY_COMPLETED"
    assert "token" not in json.dumps(status)


class ControlledAcquirer:
    def __init__(self, inner: AcquisitionPort, entered: Event, release: Event) -> None:
        self.inner, self.entered, self.release = inner, entered, release
        self.calls = 0

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return self.inner.acquisition_key(request)

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return self.inner.worst_case_requests(request)

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        self.calls += 1
        self.entered.set()
        assert self.release.wait(10), "test worker was not released"
        return self.inner.acquire(request)


def test_simultaneous_invocations_have_one_governed_worker(tmp_path: Path) -> None:
    w = world(tmp_path)
    entered, release = Event(), Event()
    adapters = {k: ControlledAcquirer(v, entered, release) for k, v in w.acquirers().items()}
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_run, w, acquirers=adapters)
        try:
            assert entered.wait(10)
            second = pool.submit(_run, w, acquirers=adapters).result(timeout=10)
            assert second.status is TickStatus.LEASE_HELD and not second.executed
        finally:
            release.set()
        completed = first.result(timeout=10)
    assert completed.status is TickStatus.COMPLETED
    assert completed.requests == sum(w.web.requests.values()) + len(w.ted.bodies)


def test_expired_authority_stops_before_child_work_even_without_a_takeover(tmp_path: Path) -> None:
    w = world(tmp_path)
    elapsed = iter([0.0, 0.0, 61.0])
    with pytest.raises(LeaseLost):
        _run(w, lease_seconds=60, monotonic=lambda: next(elapsed, 61.0))
    assert not w.web.requests and not w.ted.bodies and not w.downstream.requests
    assert w.store().tick_report(DAY_1.date().isoformat()) is None
    w.clock.now = DAY_1 + timedelta(seconds=61)
    assert _run(w).resumed


def test_utc_day_change_does_not_create_two_store_owners(tmp_path: Path) -> None:
    store = world(tmp_path).store()
    midnight = datetime(2026, 10, 6, 23, 59, 50, tzinfo=UTC)
    first = store.claim_tick("2026-10-06", now=midnight, lease_seconds=60)
    assert first is not None
    assert (
        store.claim_tick("2026-10-07", now=midnight + timedelta(seconds=20), lease_seconds=60)
        is None
    )
    store.assert_claim(first, now=midnight + timedelta(seconds=20))
    second = store.claim_tick("2026-10-07", now=midnight + timedelta(seconds=61), lease_seconds=60)
    assert second is not None
    with pytest.raises(LeaseLost):
        store.assert_claim(first, now=midnight + timedelta(seconds=61))


def test_unknown_source_cost_produces_zero_child_calls(tmp_path: Path) -> None:
    w = world(tmp_path)
    registry = SourceRegistry(tuple(replace(s, cost_per_request_microunits=None) for s in SOURCES))
    report = run_daily_tick(
        store=w.store(),
        now=DAY_1,
        attention=ATTENTION,
        acquirers=w.acquirers(),
        recompute=w.downstream,
        registry=registry,
    )
    assert report.requests == 0 and not w.web.requests and not w.ted.bodies
    assert any("COST_UNKNOWN" in reason for _, reason in report.blocked)


def test_scheduler_error_is_durable_and_never_logs_exception_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(**kwargs: object) -> None:
        raise RuntimeError("private token: NEVER_LOG_THIS")

    monkeypatch.setattr(observation_daily, "run_once", fail)
    attention = tmp_path / "attention.json"
    attention.write_text("[]", encoding="utf-8")
    result = observation_daily.run_scheduled_tick(
        root=tmp_path,
        clock=FixedClock(),
        code_sha="test",
        attention_file=attention,
        enrollment=(),
        source_ports={},
    )
    assert result["state"] == "ERROR" and result["error_class"] == "RuntimeError"
    status = SqliteObservationRuntimeStore.inspect(
        tmp_path / "observation-runtime.sqlite3", now=DAY_1
    )
    assert status["last_invocation"] is not None
    assert "NEVER_LOG_THIS" not in json.dumps(status)


def test_process_death_leaves_inspectable_lease_and_recovers_after_expiry(tmp_path: Path) -> None:
    db = tmp_path / "observation-runtime.sqlite3"
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "from datetime import datetime; import os,sys; "
            "from pipeline.observation_runtime import SqliteObservationRuntimeStore as S; "
            "s=S(sys.argv[1]); n=datetime.fromisoformat(sys.argv[2]); "
            "s.begin_invocation(started_at=n,code_sha='killed'); "
            "s.claim_tick(n.date().isoformat(),now=n,lease_seconds=60); os._exit(9)",
            str(db),
            DAY_1.isoformat(),
        ],
        check=False,
        timeout=10,
    )
    assert child.returncode == 9
    status = SqliteObservationRuntimeStore.inspect(db, now=DAY_1)
    assert status["state"] == "INTERRUPTED_OR_RUNNING" and status["lease_status"] == "ACTIVE"
    attention = tmp_path / "attention.json"
    attention.write_text("[]", encoding="utf-8")
    clock = FixedClock(DAY_1 + timedelta(seconds=61))
    recovered = observation_daily.run_scheduled_tick(
        root=tmp_path,
        clock=clock,
        code_sha="restart",
        attention_file=attention,
        enrollment=(),
        source_ports={},
    )
    assert recovered["state"] == "COMPLETED" and recovered["resumed"]
    assert recovered["requests"] == 0
