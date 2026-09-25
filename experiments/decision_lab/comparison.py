"""Descriptive comparison and critical regression reporting."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from experiments.decision_lab.metrics import detect_critical_regressions


def compare_records(
    baseline: Mapping[str, Any], candidate: Mapping[str, Any], critical_case_ids: set[str]
) -> dict[str, Any]:
    def outcomes(result: Mapping[str, Any]) -> dict[str, Any]:
        rows = result.get("records", [])
        return {
            f"{row['case_id']}::{row.get('variant_id', 'default')}::{row.get('repetition', 1)}": json.dumps(
                row.get("compositions"), sort_keys=True
            )
            for row in rows
            if isinstance(row, Mapping) and "case_id" in row
        }

    old, new = outcomes(baseline), outcomes(candidate)
    return {
        "baseline_result_id": baseline.get("result_id"),
        "candidate_result_id": candidate.get("result_id"),
        "changed_case_ids": sorted(
            case_id for case_id in old.keys() | new.keys() if old.get(case_id) != new.get(case_id)
        ),
        "missing_candidate_case_ids": sorted(old.keys() - new.keys()),
        "critical_regressions": detect_critical_regressions(
            old,
            new,
            {
                key
                for key in old.keys() | new.keys()
                if any(key.startswith(f"{case_id}::") for case_id in critical_case_ids)
            },
        ),
        "interpretation": "DESCRIPTIVE_ONLY; no policy or grammar promotion",
    }
