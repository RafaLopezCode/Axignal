"""ModelRouter: routes cognitive jobs to registered providers.

The router depends on the provider interface only. Provider-specific logic stays
inside adapters under ``cognition/providers``. The domain layer is never
imported here.

Doctrine: MASTER §13.1, §13.2.
"""

from __future__ import annotations

from collections.abc import Iterable

from cognition.jobs.model import CognitiveJob, StructuredResult
from cognition.providers.base import CognitiveProvider


class NoProviderAvailable(Exception):
    """Raised when no provider is registered for a job."""


class ModelRouter:
    """Routes jobs to providers by explicit name or first-registered default."""

    def __init__(self, providers: Iterable[CognitiveProvider] = ()) -> None:
        self._providers: dict[str, CognitiveProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: CognitiveProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(f"provider already registered: {provider.name}")
        self._providers[provider.name] = provider

    def registered(self) -> tuple[str, ...]:
        return tuple(self._providers)

    def route(self, job: CognitiveJob, provider_name: str | None = None) -> StructuredResult:
        if provider_name is not None:
            provider = self._providers.get(provider_name)
            if provider is None:
                raise NoProviderAvailable(f"no provider named {provider_name!r}")
            return provider.complete(job)
        if not self._providers:
            raise NoProviderAvailable("no cognitive providers registered")
        first = next(iter(self._providers.values()))
        return first.complete(job)
