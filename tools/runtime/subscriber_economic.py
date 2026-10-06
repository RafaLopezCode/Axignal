"""Factory for the authorized subscriber Economic Brain read runtime.

The factory receives host-owned identity authorities and the existing governed
Observation Memory. It adds no authentication, source acquisition or fixture
fallback of its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from application.economic_discovery.observation_memory import ObservationMemory
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_projection.subscriber_runtime import SubscriberEconomicRuntime
from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganizationReader,
    CanonicalOrganizationReader,
)
from application.xeed_access.reader import (
    AuthorizedXeedReader,
    MembershipReader,
    PrincipalReader,
    XeedReader,
)
from pipeline.subscriber_projection.sqlite_store import SqliteSubscriberEconomicOutputStore


class SubscriberIdentityStoreReader(PrincipalReader, MembershipReader, Protocol):
    """TASK-049 identity store exposed through both existing read authorities."""


def build_subscriber_economic_runtime(
    *,
    database_path: str | Path,
    identity_store: SubscriberIdentityStoreReader,
    portfolio_store: XeedReader,
    organizations: CanonicalOrganizationReader,
    observation_memory: ObservationMemory,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
    code_sha: str,
) -> SubscriberEconomicRuntime:
    """Build a runtime whose every read rechecks membership and canonical identity."""

    return SubscriberEconomicRuntime(
        authorized_xeeds=AuthorizedXeedReader(identity_store, identity_store, portfolio_store),
        organization_reader=AuthorizedXeedOrganizationReader(organizations),
        observation_memory=observation_memory,
        output_store=SqliteSubscriberEconomicOutputStore(database_path),
        reuse_policy=reuse_policy,
        temporal_policy=temporal_policy,
        code_sha=code_sha,
    )
