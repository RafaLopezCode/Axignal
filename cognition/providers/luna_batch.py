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
        submitted = tuple(jobs)
        job_ids = {job.id for job in submitted}
        if len(job_ids) != len(submitted):
            raise ValueError("Luna batch job identities must be unique")
        results = tuple(
            self._transport.complete_batch(
                model=self._authorized_model,
                jobs=submitted,
            )
        )
        # Missing results stay absent (not negative); foreign or repeated
        # identities cannot be attributed to a submitted job and are refused.
        seen: set[str] = set()
        for result in results:
            if result.job_id not in job_ids:
                raise ValueError(f"Luna batch returned unknown job identity: {result.job_id!r}")
            if result.job_id in seen:
                raise ValueError(f"Luna batch returned duplicate job identity: {result.job_id!r}")
            seen.add(result.job_id)
        return results
