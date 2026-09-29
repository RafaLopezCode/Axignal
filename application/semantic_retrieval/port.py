"""Application port for disposable semantic candidate retrieval."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SemanticRepresentation:
    representation_id: str
    vector: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    representation_id: str
    similarity: float


class SemanticIndex(Protocol):
    """Retrieval proposes candidates; it never grants epistemic authority."""

    def rebuild(self, representations: Sequence[SemanticRepresentation]) -> None: ...

    def search(self, vector: Sequence[float], *, k: int) -> tuple[SemanticCandidate, ...]: ...

    @property
    def size(self) -> int: ...
