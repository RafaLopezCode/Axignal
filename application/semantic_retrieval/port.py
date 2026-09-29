"""Application port for disposable semantic candidate retrieval."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SemanticRepresentation:
    representation_id: str
    vector: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.representation_id.strip():
            raise ValueError("representation id is required")
        if not self.vector:
            raise ValueError("representation vector is required")


@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    representation_id: str
    similarity: float


@dataclass(frozen=True, slots=True)
class SemanticIndexStats:
    size: int
    dimension: int


class SemanticIndex(Protocol):
    """Retrieval proposes candidates; it never grants epistemic authority."""

    def rebuild(self, representations: Sequence[SemanticRepresentation]) -> None: ...

    def upsert(self, representation: SemanticRepresentation) -> None: ...

    def remove(self, representation_id: str) -> bool: ...

    def search(self, vector: Sequence[float], *, k: int) -> tuple[SemanticCandidate, ...]: ...

    @property
    def stats(self) -> SemanticIndexStats: ...

    @property
    def size(self) -> int: ...
