"""The fit of open demand is judged once per UTC day by the runtime (spec 087)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from tests.first_observation.harness import World, build, runtime


def test_the_runtime_judges_demand_fit_once_per_day(tmp_path: Path) -> None:
    facade = build(tmp_path, World())
    rt = runtime(facade)
    calls: list[datetime] = []

    def fit(now: datetime) -> dict[str, Any]:
        calls.append(now)
        return {"state": "DONE", "pairs": 7}

    rt._demand_fit = fit
    now = datetime(2026, 10, 17, 9, tzinfo=UTC)

    class Clock:
        def __init__(self, at: datetime) -> None:
            self.at = at

        def now(self) -> datetime:
            return self.at

    clock = Clock(now)
    rt._clock = clock  # type: ignore[assignment]
    assert rt.judge_demand_fit() == 7
    assert rt.judge_demand_fit() == 0  # same UTC day: nothing more
    clock.at = now + timedelta(days=1)
    assert rt.judge_demand_fit() == 7 and len(calls) == 2
