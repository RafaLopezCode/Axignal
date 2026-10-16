"""Identity verification is an optional upgrade, not a gate to observe (ADR-0087 amendment).

Wraps the registry-based resolution of a subscriber's locator. When no registry can attest the
organization (not found, or no source covers it) and the locator names a public website, the
Focus is created on a web-anchored subject: observation of everything public, legal-identity
predicates UNKNOWN, nothing canonical. Ambiguous or conflicting identities stay pending and
invalid input stays rejected: only the absence of a registry answer is anchored to the web.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from application.organization_admission.locator import LocatorError, parse_locator
from application.subscriber_portfolio.models import (
    OrganizationIdentityPending,
    OrganizationResolution,
)
from domain.organizations.model import Organization

#: Pending reasons that mean "no registry answered", never "the registry disagreed".
ANCHORABLE = frozenset({"IDENTITY_SOURCE_UNAVAILABLE", "NOT_FOUND_IN_IDENTITY_SOURCE"})


class OrganizationResolutionPort(Protocol):
    def resolve(self, locator: str) -> OrganizationResolution: ...


class WebSubjectPort(Protocol):
    def ensure(self, domain: str, locator: str, now: datetime) -> Organization: ...


class WebAnchoredResolution:
    def __init__(
        self,
        inner: OrganizationResolutionPort,
        subjects: WebSubjectPort,
        clock: Callable[[], datetime],
    ) -> None:
        self._inner, self._subjects, self._clock = inner, subjects, clock

    def resolve(self, locator: str) -> OrganizationResolution:
        resolved = self._inner.resolve(locator)
        if not isinstance(resolved, OrganizationIdentityPending):
            return resolved
        if resolved.reason_code not in ANCHORABLE:
            return resolved
        try:
            domain = parse_locator(locator).domain
        except LocatorError:
            return resolved
        if not domain:
            return resolved  # a bare name has no website to anchor observation to
        return self._subjects.ensure(domain, locator, self._clock())
