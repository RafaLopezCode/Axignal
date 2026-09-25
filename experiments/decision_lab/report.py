"""Human-inspectable research report for one immutable result."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any


def render_report(result: Mapping[str, Any]) -> str:
    records = result.get("records", [])
    failures = Counter(str(row.get("failure")) for row in records if row.get("failure"))
    judgments = [judgment for row in records for judgment in row.get("judgments", [])]
    latencies = [
        float(row["metadata"]["latency_seconds"])
        for row in records
        if isinstance(row.get("metadata", {}).get("latency_seconds"), (float, int))
    ]
    return "\n".join(
        [
            f"# Decision Lab Result {result.get('result_id', 'unknown')}",
            "",
            f"- Experiment: {result.get('experiment_id', 'recorded fixture')}",
            f"- Data mode: {result.get('data_mode', 'unknown')}",
            f"- Cases/records: {len(records) if records else len(result.get('judgments', []))}",
            f"- Judgments: {len(judgments) if records else len(result.get('judgments', []))}",
            f"- Failure taxonomy: {dict(sorted(failures.items()))}",
            f"- Metrics by variant: {result.get('metrics_by_variant', 'NOT AVAILABLE')}",
            f"- Usage: {result.get('actual_usage', result.get('usage'))}",
            f"- Mean request latency seconds: {sum(latencies) / len(latencies) if latencies else 'UNKNOWN'}",
            f"- Cost: {result.get('actual_cost', result.get('cost', 'UNKNOWN'))}",
            "- Result: INCONCLUSIVE unless a predeclared, adequately powered live analysis supports another classification.",
            "- Calibration: NOT VALIDATED.",
            "- Authority: experimental only; no canonical admission, grammar promotion, or production policy.",
            "",
            "## Limitations",
            "",
            *[
                f"- {item}"
                for item in result.get(
                    "limitations", ["Fixture/replay output is not model quality evidence."]
                )
            ],
            "",
        ]
    )
