"""A killed acquisition must not erase its daily spend boundary (synthetic web)."""

from __future__ import annotations

import subprocess
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from application.observation_runtime import (
    DailyObservationBudget,
    ObservationFamily,
    run_daily_tick,
)
from application.observation_runtime.families import FAMILY_POLICIES
from tests.observation_runtime.harness import ATTENTION, DAY_1, world


@pytest.mark.parametrize("resumed_limit", [1, 6])
def test_killed_acquisition_preserves_budget_before_any_receipt(
    tmp_path: Path, resumed_limit: int
) -> None:
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import os, sys
from pathlib import Path
from application.observation_runtime import DailyObservationBudget, ObservationFamily, run_daily_tick
from application.observation_runtime.families import FAMILY_POLICIES
from tests.observation_runtime.harness import ATTENTION, DAY_1, world
w = world(Path(sys.argv[1]))
inner = w.acquirers()['official-public-website']
class KillAfterNetwork:
    def acquisition_key(self, request): return inner.acquisition_key(request)
    def worst_case_requests(self, request): return inner.worst_case_requests(request)
    def acquire(self, request):
        inner.acquire(request)
        Path(sys.argv[1], 'network-calls').write_text('1')
        os._exit(17)
run_daily_tick(store=w.store(), now=DAY_1, attention=ATTENTION,
    acquirers={'official-public-website': KillAfterNetwork()}, recompute=w.downstream,
    policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
    budget=DailyObservationBudget(max_http_requests=1))
""",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert child.returncode == 17, child.stderr
    assert (tmp_path / "network-calls").read_text() == "1"
    restarted = world(tmp_path)
    usage = restarted.store().budget_usage(DAY_1.date().isoformat())
    assert usage.requests == 1, "network work cannot vanish before its receipt is committed"
    assert usage.actions == 1
    assert not restarted.store().receipts(DAY_1.date().isoformat())
    report = run_daily_tick(
        store=restarted.store(),
        now=DAY_1 + timedelta(hours=1, seconds=1),
        attention=ATTENTION,
        acquirers=restarted.acquirers(),
        recompute=restarted.downstream,
        policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
        budget=DailyObservationBudget(max_http_requests=resumed_limit),
    )
    assert report.resumed and report.status.value == "COMPLETED"
    assert not restarted.web.requests, "a missing receipt cannot authorize a repeated call"
    assert report.executed and all(e.outcome.value == "BLOCKED" for e in report.executed)
    assert {reason for _, reason in report.blocked} == {"ACQUISITION_OUTCOME_UNKNOWN"}
    assert report.requests == 0 and not restarted.store().evidence()
    assert restarted.store().budget_usage(DAY_1.date().isoformat()) == usage
    status = restarted.store().inspect(restarted.store()._path, now=DAY_1)
    assert status["budget"]["unsettledAcquisitions"] == 1
    assert status["budget"]["reservedRequests"] == 1
    assert "official-public-website:" not in str(status), "operator status has no source keys"
    # A later scheduled observation can succeed without altering the unknown prior outcome.
    lead = restarted.store().leads()[0]
    later = run_daily_tick(
        store=restarted.store(),
        now=lead.next_due_at,
        attention=ATTENTION,
        acquirers=restarted.acquirers(),
        recompute=restarted.downstream,
        policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
        budget=DailyObservationBudget(max_http_requests=1),
    )
    assert later.requests == 1 and restarted.web.requests
    assert restarted.store().budget_usage(DAY_1.date().isoformat()) == usage
