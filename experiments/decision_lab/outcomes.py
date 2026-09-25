"""Deterministic experiment outcome evaluation from predeclared criteria."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from experiments.decision_lab.experiment import manifest_digest

OUTCOMES = {"SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE"}


def evaluate_experiment_outcome(
    definition: Mapping[str, Any],
    metrics_by_variant: Mapping[str, Mapping[str, Any]],
    *,
    operational_failures: int = 0,
    critical_regressions: Sequence[str] = (),
    incompatible_output_semantics: bool = False,
) -> dict[str, Any]:
    """Apply only predeclared evidence, invalidation and effect criteria."""
    criteria = definition["evaluation_criteria"]
    reasons: list[str] = []
    if incompatible_output_semantics:
        reasons.append("INCOMPATIBLE_OUTPUT_SEMANTICS")
    if operational_failures and "OPERATIONAL_FAILURE" in criteria["invalidation_conditions"]:
        reasons.append("OPERATIONAL_FAILURE")
    if critical_regressions and criteria["critical_regression_policy"] == "BLOCK":
        reasons.append("CRITICAL_REGRESSION")

    variant_metrics = list(metrics_by_variant.values())
    answered = [int(metric.get("unique_answered_cases", 0)) for metric in variant_metrics]
    if not answered or min(answered) < criteria["minimum_answered_cases"]:
        reasons.append("INSUFFICIENT_ANSWERED_CASES")
    if reasons:
        return {"outcome": "INCONCLUSIVE", "reasons": reasons}

    effect = criteria.get("minimum_effect")
    if effect is None:
        return {
            "outcome": "INCONCLUSIVE",
            "reasons": ["NO_PREDECLARED_MINIMUM_EFFECT"],
        }
    if len(variant_metrics) != 2:
        return {"outcome": "INCONCLUSIVE", "reasons": ["CRITERIA_REQUIRE_TWO_VARIANTS"]}
    scores = [metric.get(criteria["primary_metric"]) for metric in variant_metrics]
    if any(not isinstance(score, (int, float)) for score in scores):
        return {"outcome": "INCONCLUSIVE", "reasons": ["PRIMARY_METRIC_UNAVAILABLE"]}
    delta = float(scores[1]) - float(scores[0])
    if criteria["direction"] == "LOWER_IS_BETTER":
        delta = -delta
    if delta >= effect:
        outcome = "SUPPORTED"
        reason = "PREDECLARED_EFFECT_MET"
    elif delta <= -effect:
        outcome = "NOT_SUPPORTED"
        reason = "PREDECLARED_EFFECT_NOT_MET"
    else:
        outcome = "INCONCLUSIVE"
        reason = "EFFECT_WITHIN_PREDECLARED_INCONCLUSIVE_BAND"
    return {"outcome": outcome, "reasons": [reason], "oriented_effect": delta}


def object_digest(value: Mapping[str, Any]) -> str:
    return manifest_digest(dict(value))
