"""Deterministic entity resolution.

Companies, aliases, groups, subsidiaries, brands and legal entities.

Doctrine: MASTER §9.3, §14, §36 (Organization).
"""

from __future__ import annotations

from pipeline.entity_resolution.resolver import (
    ExactNameResolver,
    ResolutionCandidate,
)

__all__ = ["ExactNameResolver", "ResolutionCandidate"]
