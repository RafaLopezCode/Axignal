"""TurboQuant adapter for non-authoritative semantic candidate retrieval."""

from collections.abc import Sequence

import numpy as np
from turboquant import TurboQuantIndex  # type: ignore[import-untyped]

from application.semantic_retrieval import SemanticCandidate, SemanticRepresentation


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

    def rebuild(self, representations: Sequence[SemanticRepresentation]) -> None:
        ids = tuple(item.representation_id for item in representations)
        if len(ids) != len(set(ids)):
            raise ValueError("representation IDs must be unique")
        index = self._new_index()
        if representations:
            vectors = np.asarray([item.vector for item in representations], dtype=np.float32)
            if vectors.ndim != 2 or vectors.shape[1] != self._dimension:
                raise ValueError(f"all vectors must have dimension {self._dimension}")
            index.add(vectors)
        self._index = index
        self._ids = ids

    def search(self, vector: Sequence[float], *, k: int) -> tuple[SemanticCandidate, ...]:
        if k < 1:
            raise ValueError("k must be positive")
        if not self._ids:
            return ()
        query = np.asarray(tuple(vector), dtype=np.float32)
        if query.shape != (self._dimension,):
            raise ValueError(f"query vector must have dimension {self._dimension}")
        similarities, positions = self._index.search(query[np.newaxis, :], k=k)
        return tuple(
            SemanticCandidate(
                representation_id=self._ids[int(position)],
                similarity=float(similarity),
            )
            for similarity, position in zip(similarities[0], positions[0], strict=True)
        )
