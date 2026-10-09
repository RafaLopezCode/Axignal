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

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from urllib.parse import urlsplit

from application.economic_discovery.observation_memory import (
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.source_registry import SourceRegistryEntry
from domain.evidence.epistemics import Currentness

RIGHTS_POLICY_VERSION = "first-observation-content-rights.v1"
#: Tenant-private citations kept in a First Proof when no rights decision exists.
PRIVATE_CITATION_DAYS = 30


@dataclass(frozen=True, slots=True)
class ContentRights:
    """What may be done with one website's content, as decided now."""

    entry: SourceRegistryEntry | None = None
    provider_input: bool = False
    decided_at: datetime | None = None
    #: Explicit permission for reviewed offering excerpts, distinct from routing vocabulary.
    public_offer_input: bool = False

    @property
    def reuse_permitted(self) -> bool:
        entry = self.entry
        return (
            entry is not None
            and entry.rights_status is ObservationRightsStatus.PERMITTED
            and entry.access_status is ObservationAccessStatus.ACCESSIBLE
            and entry.reuse_scope is ObservationReuseScope.GLOBAL_PUBLIC
            and entry.currentness is Currentness.CURRENT
            and ReusePurpose.CURRENT_STATE in entry.allowed_purposes
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
            "publicOfferInput": self.public_offer_input,
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
        public_offer_input: frozenset[str] = frozenset(),
    ) -> None:
        self._entries = tuple(e for e in entries if e.source_type == "PUBLIC_WEBSITE")
        self._provider_input = provider_input
        self._public_offer_input = public_offer_input

    def rights_for(self, website: str, *, now: datetime) -> ContentRights:
        parts = urlsplit(website if "://" in website else "https://" + website)
        host = (parts.hostname or "").lower()
        path = parts.path or "/"
        scheme = parts.scheme or "https"
        matches = (
            entry
            for entry in self._entries
            if any(
                host == target.host.rstrip(".").lower()
                and scheme in target.schemes
                and (
                    target.path_prefix == "/"
                    or path == target.path_prefix.rstrip("/")
                    or path.startswith(target.path_prefix.rstrip("/") + "/")
                )
                for target in entry.targets
            )
        )
        entry = next(matches, None)
        if entry is None:
            return ContentRights(decided_at=now)
        rights = ContentRights(entry=entry, decided_at=now)
        return ContentRights(
            entry=entry,
            provider_input=rights.reuse_permitted and entry.source_id in self._provider_input,
            public_offer_input=rights.reuse_permitted
            and entry.source_id in self._public_offer_input,
            decided_at=now,
        )
