"""The provider interface.

Adapters implement this protocol. It depends only on cognition job models, so
the domain can remain provider-agnostic.

Doctrine: MASTER §13.1, §13.2 (model swap test).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognition.jobs.model import CognitiveJob, StructuredResult


@runtime_checkable
class CognitiveProvider(Protocol):
    """A replaceable cognitive backend."""

    @property
    def name(self) -> str:
        """Stable provider name used by the router."""
        ...

    def complete(self, job: CognitiveJob) -> StructuredResult:
        """Execute a cognitive job and return structured, non-canonical output."""
        ...
