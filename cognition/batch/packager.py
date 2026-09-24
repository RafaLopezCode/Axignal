"""Deterministic batch packager.

Doctrine: MASTER §12, §35.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from cognition.jobs.model import CognitiveJob


@dataclass(frozen=True)
class Batch:
    """An immutable group of jobs dispatched together."""

    jobs: tuple[CognitiveJob, ...]


class BatchPackager:
    """Packs jobs into bounded batches, preserving input order."""

    def __init__(self, max_batch_size: int = 10) -> None:
        if max_batch_size < 1:
            raise ValueError("max_batch_size must be >= 1")
        self._max_batch_size = max_batch_size

    def pack(self, jobs: Sequence[CognitiveJob]) -> tuple[Batch, ...]:
        size = self._max_batch_size
        return tuple(
            Batch(jobs=tuple(jobs[index : index + size])) for index in range(0, len(jobs), size)
        )
