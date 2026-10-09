"""Content rights of a website for First Observation (ADR-0015, ADR-0090 §5, ADR-0091).

Public visibility and robots.txt are not authority to reuse, retain or transmit content
(ADR-0015: "public visibility alone is insufficient authority"; "raw text retention is
not automatic"). The authority is a governed ``SourceRegistryEntry`` for the website,
registered by the operator with its rights basis and retention policy, plus an explicit
input-rights decision for evaluator transmission. Without one, everything fails closed
except the legitimate private observation for the requesting tenant: fetch under robots,
derive in memory, keep only bounded citations in its private First Proof for a bounded
time, retain no raw body, share no content across tenants, send nothing to a provider.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

from application.economic_discovery.observation_memory import (
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.source_registry import SourceRegistryEntry

RIGHTS_POLICY_VERSION = "first-observation-content-rights.v1"
#: Tenant-private citations kept in a First Proof when no rights decision exists.
PRIVATE_CITATION_DAYS = 30


@dataclass(frozen=True, slots=True)
class ContentRights:
    """What may be done with one website's content, as decided now."""

    entry: SourceRegistryEntry | None = None
    provider_input: bool = False
    decided_at: datetime | None = None

    @property
    def reuse_permitted(self) -> bool:
        entry = self.entry
        return (
            entry is not None
            and entry.rights_status is ObservationRightsStatus.PERMITTED
            and entry.access_status is ObservationAccessStatus.ACCESSIBLE
            and entry.reuse_scope is ObservationReuseScope.GLOBAL_PUBLIC
        )

    @property
    def raw_retention_days(self) -> int:
        return (
            0
            if not self.reuse_permitted or self.entry is None
            else (self.entry.retention_policy.raw_retention_days)
        )

    @property
    def basis_ref(self) -> str | None:
        if self.entry is None:
            return None
        return (
            f"source-registry:{self.entry.source_id}@{self.entry.version}:{self.entry.fingerprint}"
        )

    def shared_until(self, now: datetime) -> datetime | None:
        """Until when world-level content (site reading text) may be kept and reused."""
        days = self.raw_retention_days
        return None if days <= 0 else now + timedelta(days=days)

    def private_until(self, now: datetime) -> datetime:
        """Until when a tenant-private First Proof may keep its citations."""
        return now + timedelta(days=max(self.raw_retention_days, PRIVATE_CITATION_DAYS))

    def to_wire(self) -> dict[str, object]:
        return {
            "policyVersion": RIGHTS_POLICY_VERSION,
            "basisRef": self.basis_ref,
            "reusePermitted": self.reuse_permitted,
            "rawRetentionDays": self.raw_retention_days,
            "providerInput": self.provider_input,
        }


NO_RIGHTS = ContentRights()


class ContentRightsPolicy(Protocol):
    def rights_for(self, website: str, *, now: datetime) -> ContentRights: ...


class NoContentRights:
    """Default: no governed decision exists, so nothing beyond private observation."""

    def rights_for(self, website: str, *, now: datetime) -> ContentRights:
        del website
        return ContentRights(decided_at=now)


def _host(website: str) -> str:
    parts = urlsplit(website if "://" in website else "https://" + website)
    return (parts.hostname or "").lower()


class RegisteredContentRights:
    """Rights from governed registry entries matched by exact host (bare or ``www.``)."""

    def __init__(
        self,
        entries: tuple[SourceRegistryEntry, ...],
        *,
        provider_input: frozenset[str] = frozenset(),
    ) -> None:
        self._by_host: Mapping[str, SourceRegistryEntry] = {
            target.host.lower().removeprefix("www."): entry
            for entry in entries
            if entry.source_type == "PUBLIC_WEBSITE"
            for target in entry.targets
        }
        self._provider_input = provider_input

    def rights_for(self, website: str, *, now: datetime) -> ContentRights:
        host = _host(website).removeprefix("www.")
        entry = self._by_host.get(host)
        if entry is None:
            return ContentRights(decided_at=now)
        return ContentRights(
            entry=entry,
            provider_input=entry.source_id in self._provider_input,
            decided_at=now,
        )
