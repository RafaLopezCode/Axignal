from __future__ import annotations

from pathlib import Path

from tests.observation_runtime.benchmark import PUBLISH_DAY, benchmark


def test_runtime_beats_naive_daily_observation_without_losing_findings(tmp_path: Path) -> None:
    result = benchmark(tmp_path)
    naive, runtime = result["before_naive_daily"], result["after_autonomous_runtime"]
    assert runtime["candidates_total"] == naive["candidates_total"]
    assert runtime["new_demand_found_on_day"] - PUBLISH_DAY <= 3
    assert runtime["http_requests"] * 4 <= naive["http_requests"]
    assert runtime["semantic_extraction_calls"] * 10 <= naive["semantic_extraction_calls"]
    assert runtime["structured_evaluator_calls"] * 10 <= naive["structured_evaluator_calls"]
    assert runtime["scheduler_model_calls"] == naive["scheduler_model_calls"] == 0
    assert runtime["idle_days"] > 0 and runtime["stop_reasons"]
