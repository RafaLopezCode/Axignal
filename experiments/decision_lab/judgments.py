"""Normalization and deterministic composition of typed judgments."""

from __future__ import annotations

import math
from typing import Any

from experiments.decision_lab.models import NormalizedJudgment


def normalize_judgment(
    question_id: str,
    primitive: str,
    answer: dict[str, Any],
    *,
    evaluator: str,
    requested_model: str | None = None,
    resolved_model: str | None = None,
    usage: dict[str, int] | None = None,
) -> NormalizedJudgment:
    if primitive not in {"CHOICE", "SCORE", "NOUL"}:
        return NormalizedJudgment(
            question_id,
            "NOUL",
            None,
            evaluator=evaluator,
            requested_model=requested_model,
            resolved_model=resolved_model,
            usage=usage,
            status="MALFORMED",
        )
    raw_value = answer.get("selected") if primitive == "CHOICE" else answer.get("value")
    if primitive == "NOUL" and raw_value is None:
        raw_value = answer.get("probability_yes")
    distribution = answer.get("distribution")
    confidence = answer.get("confidence")
    valid_distribution = None
    distribution_valid = distribution is None or (
        isinstance(distribution, dict)
        and all(
            isinstance(key, (str, int)) and isinstance(value, (float, int)) and 0 <= value <= 1
            for key, value in distribution.items()
        )
    )
    confidence_valid = confidence is None or (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(confidence)
        and 0 <= confidence <= 1
    )
    usage_valid = usage is None or all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in usage.values()
    )
    distribution_valid = distribution_valid and (
        valid_distribution is None or abs(sum(valid_distribution.values()) - 1.0) <= 0.05
    )
    if isinstance(distribution, dict) and distribution_valid:
        valid_distribution = {str(key): float(value) for key, value in distribution.items()}
    if raw_value is None:
        status = "MISSING"
    elif (
        not distribution_valid
        or not confidence_valid
        or not usage_valid
        or (
            (
                primitive == "NOUL"
                and (
                    not isinstance(raw_value, (int, float))
                    or isinstance(raw_value, bool)
                    or not math.isfinite(raw_value)
                    or not 0 <= raw_value <= 1
                )
            )
            or (
                primitive == "SCORE"
                and (
                    not isinstance(raw_value, (int, float))
                    or isinstance(raw_value, bool)
                    or not math.isfinite(raw_value)
                )
            )
            or (primitive == "CHOICE" and not isinstance(raw_value, str))
        )
    ):
        status = "MALFORMED"
    else:
        status = "ANSWERED"
    return NormalizedJudgment(
        question_id,
        primitive,
        raw_value,
        valid_distribution,
        float(confidence)
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1
        else None,
        evaluator,
        requested_model,
        resolved_model,
        usage,
        status,
        {str(key): value for key, value in answer["legend"].items()}
        if isinstance(answer.get("legend"), dict)
        else None,
    )


def compose_support(judgment: NormalizedJudgment) -> dict[str, Any]:
    """Compose one experimental support judgment without thresholding Noul."""
    if judgment.status != "ANSWERED":
        return {"status": judgment.status, "outcome": None, "policy_version": "support.v0.1"}
    value = judgment.value
    outcome = value if judgment.primitive == "CHOICE" else None
    if judgment.primitive == "NOUL":
        outcome = {"probability_yes": value}
    if judgment.primitive == "SCORE":
        outcome = {"score": value, "distribution": judgment.distribution}
    return {"status": "COMPOSED", "outcome": outcome, "policy_version": "support.v0.1"}
