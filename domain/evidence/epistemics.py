"""Epistemic states and truth semantics.

UNKNOWN is not FALSE. A state that cannot decide a boolean returns ``None``
rather than a default ``False``.

Doctrine: MASTER §15.4 (UNKNOWN != FALSE), §19, §21.
"""

from __future__ import annotations

from enum import StrEnum


class EpistemicState(StrEnum):
    """Epistemic state of a canonical claim (MASTER §15.4)."""

    OBSERVED = "OBSERVED"
    DECLARED = "DECLARED"
    INFERRED = "INFERRED"
    CORROBORATED = "CORROBORATED"
    CONTRADICTED = "CONTRADICTED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class Currentness(StrEnum):
    """Temporal validity of knowledge (MASTER §20)."""

    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class Observability(StrEnum):
    """Economic observability grading (MASTER §21)."""

    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    LIMITED = "LIMITED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"
    STALE = "STALE"


class UnknownIsNotFalseError(Exception):
    """Raised when UNKNOWN would be coerced into FALSE."""


def truth_value(state: EpistemicState) -> bool | None:
    """Return a justified boolean, or ``None`` when the state cannot decide.

    Only OBSERVED and CORROBORATED justify ``True``. Everything else, including
    UNKNOWN, returns ``None`` and must never be silently coerced to ``False``
    (MASTER §15.4).
    """

    if state in (EpistemicState.OBSERVED, EpistemicState.CORROBORATED):
        return True
    return None


def require_boolean(state: EpistemicState) -> bool:
    """Boolean coercion that refuses to turn UNKNOWN into FALSE."""

    value = truth_value(state)
    if value is None:
        raise UnknownIsNotFalseError(f"{state.value} cannot be coerced to a boolean")
    return value
