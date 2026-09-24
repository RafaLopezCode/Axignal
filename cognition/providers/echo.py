"""Deterministic echo provider.

A no-network adapter used to exercise the router and the boundary contracts. It
is deliberately not a real foundation-model integration and demonstrates the
adapter boundary without binding AXIGNAL to any vendor.

Doctrine: MASTER §13.2 (AXIGNAL must survive a provider swap).
"""

from __future__ import annotations

from cognition.jobs.model import CognitiveJob, StructuredResult


class EchoProvider:
    """Returns the job instruction unchanged. Deterministic, offline."""

    name = "echo"

    def complete(self, job: CognitiveJob) -> StructuredResult:
        return StructuredResult(
            job_id=job.id,
            provider=self.name,
            payload={"echo": job.instruction, "kind": job.kind.value},
        )
