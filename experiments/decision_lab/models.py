"""Small data contracts used by the experimental decision laboratory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Primitive = Literal["CHOICE", "SCORE", "NOUL"]


@dataclass(frozen=True)
class NormalizedJudgment:
    """A provider-independent preservation of one typed answer."""

    question_id: str
    primitive: Primitive
    value: str | float | bool | None
    distribution: dict[str, float] | None = None
    confidence: float | None = None
    evaluator: str = "unknown"
    requested_model: str | None = None
    resolved_model: str | None = None
    usage: dict[str, int] | None = None
    status: Literal["ANSWERED", "MISSING", "MALFORMED"] = "ANSWERED"
    legend: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperationalFailure:
    """A safe failure category; deliberately contains no exception text/body."""

    category: Literal[
        "AUTHENTICATION",
        "PERMISSION",
        "INVALID_REQUEST",
        "RATE_LIMIT",
        "TIMEOUT",
        "CONNECTION",
        "SERVER",
        "RESPONSE_SCHEMA",
        "UNKNOWN",
    ]
    retryable: bool = False


class LabError(ValueError):
    """Invalid lab input or a refused operation."""
