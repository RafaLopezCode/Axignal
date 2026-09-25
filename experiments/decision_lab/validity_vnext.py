"""Offline preflight for experimental designs; never performs provider calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VALIDITY_GATES = (
    "QUESTION_CONTRACT_VALID",
    "STATE_CONTRACT_VALID",
    "ANSWER_SPACE_VALID",
    "PRIMITIVE_CONTRACT_VALID",
    "ANSWERABILITY_FIXTURES_PASS",
    "GOLDEN_PROVENANCE_VALID",
    "CONTROLLED_VARIABLES_DECLARED",
    "MODEL_PINNED",
    "SDK_PINNED",
    "BUDGET_DECLARED",
    "RETRIES_DECLARED",
    "COMPOSITION_POLICY_PINNED",
    "EVALUATION_CRITERIA_PREDECLARED",
    "HELD_OUT_POLICY_LOCKED",
    "AUTHORITY_ISOLATION_PASS",
    "SECRET_BOUNDARY_PASS",
)


@dataclass(frozen=True)
class ExperimentValidity:
    status: str
    failed_gates: tuple[str, ...]
    live_experiment_eligible: bool
    live_experiment_authorized: bool = False


def validate_experiment_validity(document: dict[str, Any]) -> ExperimentValidity:
    gates = document.get("gates")
    if not isinstance(gates, dict):
        gates = {}
    failed = tuple(name for name in VALIDITY_GATES if gates.get(name) is not True)
    return ExperimentValidity(
        "VALID" if not failed else "INVALID",
        failed,
        not failed,
        False,
    )


def quality_eligible_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only answerable, single-target cases can enter model-quality metrics."""
    return [
        case
        for case in cases
        if case.get("answerability", {}).get("status") == "ANSWERABLE"
        and case.get("expected_outcome") is not None
        and case.get("label_provenance")
        and case.get("raw_judgment", {}).get("status") == "ANSWERED"
    ]
