"""Normalization and deterministic composition of typed judgments."""

from __future__ import annotations

import json
import math
from pathlib import Path
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


def compose_relationship_decomposition(
    judgments: list[NormalizedJudgment],
) -> dict[str, Any]:
    """Map the declared four-question relation strategy to compound labels.

    The 0.5 cut is an experimental comparison rule only. Raw judgments remain
    separately persisted and the result is never canonical truth.
    """
    required = {
        "REL.PRESENCE.v1": "NOUL",
        "REL.TYPE.v1": "CHOICE",
        "REL.TIME.v1": "CHOICE",
        "REL.CONTRADICTION.v1": "NOUL",
    }
    by_id = {item.question_id: item for item in judgments}
    if len(by_id) != len(judgments) or set(by_id) != set(required):
        return {
            "status": "UNRESOLVED",
            "outcome": "UNRESOLVED",
            "resolution_state": "INCOMPLETE_ATOMIC_SET",
            "policy_version": "relationship-decomposition.v0.1",
        }
    if any(
        by_id[question_id].primitive != primitive or by_id[question_id].status != "ANSWERED"
        for question_id, primitive in required.items()
    ):
        return {
            "status": "UNRESOLVED",
            "outcome": "UNRESOLVED",
            "resolution_state": "MISSING_OR_MALFORMED_ATOMIC_JUDGMENT",
            "policy_version": "relationship-decomposition.v0.1",
        }

    presence = float(by_id["REL.PRESENCE.v1"].value)
    contradiction = float(by_id["REL.CONTRADICTION.v1"].value)
    policy = json.loads(
        (Path(__file__).parent / "policies/v0.1/relationship-decomposition.json").read_text(
            encoding="utf-8"
        )
    )
    thresholds = {
        "presence_positive_at": policy["presence_positive_at"],
        "contradiction_at": policy["contradiction_signal_at"],
    }
    time_status_mapping = policy.get("time_status_mapping", {})
    raw_time_status = str(by_id["REL.TIME.v1"].value)
    time_status = time_status_mapping.get(raw_time_status)
    if time_status not in {"CURRENT", "HISTORICAL", "NONE", "UNRESOLVED"}:
        time_status = "UNRESOLVED"
    if contradiction >= thresholds["contradiction_at"]:
        outcome = policy["contradictory_comparable_outcome"]
        resolution = "CONTRADICTORY"
    elif time_status == "UNRESOLVED":
        outcome = "UNRESOLVED"
        resolution = "UNRESOLVED"
    elif time_status == "NONE":
        if presence >= thresholds["presence_positive_at"]:
            outcome = "UNRESOLVED"
            resolution = "CONTRADICTORY_ATOMIC_SIGNALS"
        else:
            outcome = "NONE"
            resolution = "RESOLVED"
    elif time_status in {"CURRENT", "HISTORICAL"}:
        if presence >= thresholds["presence_positive_at"]:
            outcome = time_status
            resolution = "RESOLVED"
        else:
            outcome = "UNRESOLVED"
            resolution = "CONTRADICTORY_ATOMIC_SIGNALS"
    else:
        outcome = "UNRESOLVED"
        resolution = "UNRESOLVED"
    return {
        "status": "COMPOSED_EXPERIMENTAL",
        "outcome": outcome,
        "resolution_state": resolution,
        "signals": {
            "presence_probability": presence,
            "relationship_type": by_id["REL.TYPE.v1"].value,
            "time_status": time_status,
            "contradiction_probability": contradiction,
        },
        "composition_thresholds": thresholds,
        "policy_version": policy["policy_version"],
        "canonical_authority": policy["canonical_authority"],
    }
