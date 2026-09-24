"""Deterministic exact-name entity resolution.

No fuzzy or model-based matching here: those belong behind explicit, tested
layers. This baseline resolver is fully deterministic and offline.

Doctrine: MASTER §14, §35.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pipeline.normalization.text import normalize_name


@dataclass(frozen=True)
class ResolutionCandidate:
    """A canonical organization candidate."""

    organization_id: str
    canonical_name: str


class ExactNameResolver:
    """Resolves a name to a candidate using normalized exact matching."""

    def __init__(self, candidates: Iterable[ResolutionCandidate]) -> None:
        index: dict[str, ResolutionCandidate] = {}
        for candidate in candidates:
            index.setdefault(normalize_name(candidate.canonical_name), candidate)
        self._index = index

    def resolve(self, name: str) -> ResolutionCandidate | None:
        return self._index.get(normalize_name(name))
