"""Durable Batch API transport primitives for PB-10."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from cognition.jobs.model import CognitiveJob, StructuredResult


class BatchState(StrEnum):
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class BatchReceipt:
    batch_id: str
    state: BatchState


@dataclass(frozen=True, slots=True)
class BatchPoll:
    batch_id: str
    state: BatchState
    results: tuple[StructuredResult, ...] = ()
    error_code: str | None = None


class BatchApiClient(Protocol):
    def submit(self, *, model: str, jobs: Sequence[CognitiveJob]) -> str: ...
    def poll(self, batch_id: str) -> BatchPoll: ...


class DurableBatchTransport:
    """Submit/poll only; never blocks waiting for asynchronous completion."""

    def __init__(self, client: BatchApiClient) -> None:
        self._client = client

    def submit(self, *, model: str, jobs: Sequence[CognitiveJob]) -> BatchReceipt:
        if not model.strip() or not jobs:
            raise ValueError("model and non-empty jobs are required")
        batch_id = self._client.submit(model=model, jobs=tuple(jobs))
        if not batch_id.strip():
            raise ValueError("batch client returned blank identity")
        return BatchReceipt(batch_id=batch_id, state=BatchState.SUBMITTED)

    def poll(self, batch_id: str) -> BatchPoll:
        if not batch_id.strip():
            raise ValueError("batch identity is required")
        return self._client.poll(batch_id)
