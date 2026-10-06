"""Opt-in Luna batch binding kept inside the approved provider boundary."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from cognition.jobs.model import CognitiveJob, StructuredResult


class LunaBatchTransport(Protocol):
    """Infrastructure transport capable of executing an authorized Luna batch."""

    def complete_batch(
        self,
        *,
        model: str,
        jobs: Sequence[CognitiveJob],
    ) -> Sequence[StructuredResult]: ...


class LunaBatchProvider:
    """Bind generic cognitive jobs to an explicitly authorized Luna model."""

    name = "luna-batch"

    def __init__(self, transport: LunaBatchTransport, *, authorized_model: str) -> None:
        if not authorized_model.strip():
            raise ValueError("authorized Luna model binding is required")
        self._transport = transport
        self._authorized_model = authorized_model

    @property
    def authorized_model(self) -> str:
        return self._authorized_model

    def complete_batch(self, jobs: Sequence[CognitiveJob]) -> Sequence[StructuredResult]:
        """Delegate transport only; result truth remains governed downstream."""

        if not jobs:
            return ()
        return tuple(
            self._transport.complete_batch(
                model=self._authorized_model,
                jobs=tuple(jobs),
            )
        )
