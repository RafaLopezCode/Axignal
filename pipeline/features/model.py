"""Derived feature signals kept separate by design.

Doctrine: MASTER §19. There is deliberately no combined user-facing percentage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DerivedFeatures:
    """Separate internal signals. Never collapsed into a single truth score."""

    fit: float | None = None
    evidence: float | None = None
    confidence: float | None = None
    momentum: float | None = None
    novelty: float | None = None
    currentness: float | None = None
