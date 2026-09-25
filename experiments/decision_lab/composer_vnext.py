"""Deterministic experimental composition that preserves primitive uncertainty."""

from __future__ import annotations

from typing import Any

from experiments.decision_lab.models import NormalizedJudgment


def compose_vnext(
    judgment: NormalizedJudgment,
    *,
    policy_version: str,
) -> dict[str, Any]:
    """Derive an experimental result while retaining the complete raw judgment."""
    if not policy_version.strip():
        raise ValueError("composition policy must be explicitly versioned")
    raw = {
        "question_id": judgment.question_id,
        "primitive": judgment.primitive,
        "value": judgment.value,
        "distribution": judgment.distribution,
        "confidence": judgment.confidence,
        "status": judgment.status,
        "evaluator": judgment.evaluator,
        "requested_model": judgment.requested_model,
        "resolved_model": judgment.resolved_model,
        "usage": judgment.usage,
    }
    if judgment.status != "ANSWERED":
        return {
            "status": judgment.status,
            "derived_result": None,
            "raw_judgment": raw,
            "composition_policy_version": policy_version,
            "canonical_authority": False,
        }
    if judgment.primitive == "CHOICE":
        derived: Any = {"selected_class": judgment.value}
    elif judgment.primitive == "SCORE":
        derived = {"ordinal_value": judgment.value, "score_distribution": judgment.distribution}
    else:
        derived = {"probability_yes": judgment.value}
    return {
        "status": "COMPOSED_EXPERIMENTAL",
        "derived_result": derived,
        "raw_judgment": raw,
        "composition_policy_version": policy_version,
        "canonical_authority": False,
    }
