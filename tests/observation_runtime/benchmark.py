"""Before/after benchmark on the controlled 40-day world.

before: a naive daily observer. Every routable lead every day, no shared
        acquisition, and full downstream recomputation of every family that
        holds evidence (no delta, no currentness distinction).
after:  the autonomous runtime as shipped (family cadence, backoff, shared
        acquisitions, net-currentness and material-change recomputation).

Run: uv run python -m tests.observation_runtime.benchmark <work-dir> [out.json]
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

from application.observation_runtime import (
    FAMILY_POLICIES,
    Acquisition,
    AcquisitionRequest,
    LeadOutcome,
    TickReport,
    run_daily_tick,
)
from application.observation_runtime.ports import AcquisitionPort
from tests.observation_runtime.harness import ATTENTION, NEW_CALL, World, world

DAYS = 40
PUBLISH_DAY = 17


class _Unshared:
    def __init__(self, inner: AcquisitionPort) -> None:
        self._inner = inner

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return request.lead.lead_id

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return self._inner.worst_case_requests(request)

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        return self._inner.acquire(request)


_DAILY = {
    family: replace(
        policy,
        base_interval=timedelta(days=1),
        max_interval=timedelta(days=1),
        blocked_recheck=timedelta(days=1),
    )
    for family, policy in FAMILY_POLICIES.items()
}


def simulate(root: Path, *, naive: bool) -> dict[str, Any]:
    w: World = world(root)
    reports: list[TickReport] = []
    found_on: int | None = None
    full_recompute_families = 0
    started = time.perf_counter()
    for day in range(1, DAYS + 1):
        if day == PUBLISH_DAY:
            w.ted.publish(NEW_CALL)
        now = w.clock.at_day(day)
        acquirers = w.acquirers()
        report = run_daily_tick(
            store=w.store(),
            now=now,
            attention=ATTENTION,
            acquirers={k: _Unshared(v) for k, v in acquirers.items()} if naive else acquirers,
            recompute=w.downstream,
            policies=_DAILY if naive else FAMILY_POLICIES,
        )
        reports.append(report)
        if found_on is None and report.candidates_new and day >= PUBLISH_DAY:
            found_on = day
        if naive:
            full_recompute_families += len({e.family for e in w.store().evidence()})
    wall = time.perf_counter() - started
    executed = [e for r in reports for e in r.executed]
    if naive:
        # No delta: every family with evidence is fully recomputed every day.
        extractions = full_recompute_families
        evaluations = full_recompute_families * w.downstream.dimensions_per_family
        recomputations = full_recompute_families
    else:
        extractions = w.downstream.semantic_extractions
        evaluations = w.downstream.structured_evaluations
        recomputations = len(w.downstream.requests)
    return {
        "days": DAYS,
        "http_requests": len(w.ted.bodies) + sum(w.web.requests.values()),
        "ted_requests": len(w.ted.bodies),
        "web_requests": sum(w.web.requests.values()),
        "paid_cost_microunits": sum(r.paid_cost_microunits for r in reports),
        "lead_executions": sum(e.outcome is not LeadOutcome.BLOCKED for e in executed),
        "shared_acquisitions_reused": sum(r.shared_acquisitions for r in reports),
        "duplicate_evidence_seen": sum(r.duplicate_evidence for r in reports),
        "downstream_recomputations": recomputations,
        "semantic_extraction_calls": extractions,
        "structured_evaluator_calls": evaluations,
        "scheduler_model_calls": sum(r.scheduler_model_calls for r in reports),
        "candidates_total": reports[-1].candidates_total,
        "new_demand_found_on_day": found_on,
        "frontier_size_final": reports[-1].frontier_size,
        "frontier_max_depth": max(r.frontier_max_depth for r in reports),
        "idle_days": sum(r.stop_reason.value == "NOTHING_DUE" for r in reports),
        "stop_reasons": sorted({r.stop_reason.value for r in reports}),
        "wall_seconds": round(wall, 3),
    }


def benchmark(work: Path) -> dict[str, Any]:
    before = simulate(work / "naive", naive=True)
    after = simulate(work / "runtime", naive=False)
    return {"before_naive_daily": before, "after_autonomous_runtime": after}


if __name__ == "__main__":
    result = benchmark(Path(sys.argv[1]))
    text = json.dumps(result, indent=2, sort_keys=True)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text + "\n", encoding="utf-8")
    print(text)
