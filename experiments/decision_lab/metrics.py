"""Scoped descriptive metrics; no aggregate quality leaderboard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from typing import Any


def confusion_matrix(
    expected: Sequence[str], predicted: Sequence[str]
) -> dict[str, dict[str, int]]:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted lengths differ")
    labels = sorted(set(expected) | set(predicted))
    counts: Counter[tuple[str, str]] = Counter(zip(expected, predicted, strict=True))
    return {actual: {guess: counts[(actual, guess)] for guess in labels} for actual in labels}


def classification_metrics(expected: Sequence[str], predicted: Sequence[str]) -> dict[str, Any]:
    matrix = confusion_matrix(expected, predicted)
    total = len(expected)
    correct = sum(matrix[label][label] for label in matrix)
    return {
        "n": total,
        "accuracy": correct / total if total else None,
        "confusion_matrix": matrix,
        "calibration_status": "NOT_VALIDATED",
        "interpretation": "descriptive synthetic/experimental metric only",
    }


def calibration_metrics(
    probabilities: Sequence[float], outcomes: Sequence[bool], bins: int = 5
) -> dict[str, Any]:
    """Describe binary probability errors; small datasets remain unvalidated."""
    if len(probabilities) != len(outcomes):
        raise ValueError("probabilities and outcomes lengths differ")
    if bins < 1 or any(not 0 <= value <= 1 for value in probabilities):
        raise ValueError("probabilities must be in [0, 1] and bins positive")
    groups: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for probability, outcome in zip(probabilities, outcomes, strict=True):
        groups[min(int(probability * bins), bins - 1)].append((probability, outcome))
    reliability = [
        {
            "bin": index,
            "n": len(group),
            "mean_probability": sum(item[0] for item in group) / len(group),
            "observed_rate": sum(item[1] for item in group) / len(group),
        }
        for index, group in enumerate(groups)
        if group
    ]
    brier = sum(
        (probability - float(outcome)) ** 2
        for probability, outcome in zip(probabilities, outcomes, strict=True)
    )
    count = len(probabilities)
    return {
        "n": count,
        "brier_score": brier / count if count else None,
        "reliability_bins": reliability,
        "status": "INFRASTRUCTURE_ONLY_NOT_VALIDATED",
    }


def detect_critical_regressions(
    baseline: dict[str, str | None], candidate: dict[str, str | None], critical: set[str]
) -> list[str]:
    return sorted(
        case_id for case_id in critical if baseline.get(case_id) != candidate.get(case_id)
    )
