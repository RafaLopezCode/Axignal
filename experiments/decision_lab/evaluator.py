"""Provider-neutral evaluation contracts and recorded fixture support."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from experiments.decision_lab.models import NormalizedJudgment, OperationalFailure


class StructuredEvaluator(Protocol):
    def evaluate(
        self, state: dict[str, Any], questions: dict[str, Any], model: str
    ) -> list[NormalizedJudgment]: ...


class RecordedEvaluator:
    """Replay contract fixtures. These outputs are not observations from Jev."""

    def __init__(self, records: Mapping[str, Any]) -> None:
        self._records = records

    def evaluate(
        self, state: dict[str, Any], questions: dict[str, Any], model: str
    ) -> list[NormalizedJudgment]:
        del state, model
        from experiments.decision_lab.judgments import normalize_judgment

        judgments: list[NormalizedJudgment] = []
        for question_id, primitive in questions.items():
            record = self._records.get(question_id)
            if record is None:
                judgments.append(
                    normalize_judgment(question_id, primitive, {}, evaluator="recorded-fixture")
                )
            else:
                judgments.append(
                    normalize_judgment(
                        question_id,
                        primitive,
                        record,
                        evaluator="recorded-fixture",
                        requested_model="fixture-only",
                        resolved_model=None,
                        usage=None,
                    )
                )
        return judgments


def failure_for_exception(exc: Exception) -> OperationalFailure:
    """Map known SDK exception classes to safe categories, excluding text/body."""
    name = type(exc).__name__.lower()
    if "auth" in name:
        category = "AUTHENTICATION"
    elif "permission" in name:
        category = "PERMISSION"
    elif "invalid" in name or "validation" in name:
        category = "INVALID_REQUEST"
    elif "rate" in name:
        category = "RATE_LIMIT"
    elif "timeout" in name:
        category = "TIMEOUT"
    elif "connection" in name:
        category = "CONNECTION"
    elif "server" in name or "apierror" in name:
        category = "SERVER"
    else:
        category = "UNKNOWN"
    return OperationalFailure(category, retryable=False)  # type: ignore[arg-type]
