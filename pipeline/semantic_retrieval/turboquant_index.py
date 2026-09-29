"""TurboQuant adapter for non-authoritative semantic candidate retrieval."""

from collections.abc import Sequence

import numpy as np
from turboquant import TurboQuantIndex  # type: ignore[import-untyped]

from application.semantic_retrieval import (
    SemanticCandidate,
    SemanticIndexStats,
    SemanticRepresentation,
)


class TurboQuantSemanticIndex:
    """Disposable index. Representation IDs map positions back to governed objects."""

    def __init__(self, *, dimension: int, num_bits: int = 8, seed: int = 42) -> None:
        if dimension < 1:
            raise ValueError("dimension must be positive")
        if num_bits not in {4, 6, 8}:
            raise ValueError("AXIGNAL validation permits only 4, 6, or 8 bits")
        self._dimension = dimension
        self._num_bits = num_bits
        self._seed = seed
        self._ids: tuple[str, ...] = ()
        self._representations: dict[str, SemanticRepresentation] = {}
        self._index = self._new_index()

    def _new_index(self) -> TurboQuantIndex:
        return TurboQuantIndex(
            dimension=self._dimension,
            num_bits=self._num_bits,
            metric="cosine",
            use_qjl=True,
            seed=self._seed,
            memory_efficient=True,
        )

    @property
    def size(self) -> int:
        return len(self._ids)

    @property
    def stats(self) -> SemanticIndexStats:
        return SemanticIndexStats(size=self.size, dimension=self._dimension)

    def rebuild(self, representations: Sequence[SemanticRepresentation]) -> None:
        ids = tuple(item.representation_id for item in representations)
        if len(ids) != len(set(ids)):
            raise ValueError("representation IDs must be unique")
        index = self._new_index()
        if representations:
            vectors = np.asarray([item.vector for item in representations], dtype=np.float32)
            if vectors.ndim != 2 or vectors.shape[1] != self._dimension:
                raise ValueError(f"all vectors must have dimension {self._dimension}")
            if not np.isfinite(vectors).all():
                raise ValueError("representation vectors must contain only finite values")
            if np.any(np.linalg.norm(vectors, axis=1) == 0):
                raise ValueError("representation vectors must be non-zero")
            index.add(vectors)
        self._index = index
        self._ids = ids
        self._representations = {item.representation_id: item for item in representations}

    def upsert(self, representation: SemanticRepresentation) -> None:
        if not isinstance(representation, SemanticRepresentation):
            raise TypeError("upsert requires a SemanticRepresentation")
        updated = dict(self._representations)
        updated[representation.representation_id] = representation
        self.rebuild(tuple(updated.values()))

    def remove(self, representation_id: str) -> bool:
        if representation_id not in self._representations:
            return False
        updated = dict(self._representations)
        del updated[representation_id]
        self.rebuild(tuple(updated.values()))
        return True

    def search(self, vector: Sequence[float], *, k: int) -> tuple[SemanticCandidate, ...]:
        if k < 1:
            raise ValueError("k must be positive")
        if not self._ids:
            return ()
        query = np.asarray(tuple(vector), dtype=np.float32)
        if query.shape != (self._dimension,):
            raise ValueError(f"query vector must have dimension {self._dimension}")
        if not np.isfinite(query).all() or np.linalg.norm(query) == 0:
            raise ValueError("query vector must be finite and non-zero")
        effective_k = min(k, len(self._ids))
        similarities, positions = self._index.search(query[np.newaxis, :], k=effective_k)
        return tuple(
            SemanticCandidate(
                representation_id=self._ids[int(position)],
                similarity=float(similarity),
            )
            for similarity, position in zip(similarities[0], positions[0], strict=True)
        )
