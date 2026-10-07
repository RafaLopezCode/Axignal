"""Real EB-04 result + real authorization + real stores, with a controlled clock."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
)
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_continuity.service import ContinuityService
from application.subscriber_projection.subscriber_runtime import SubscriberEconomicRuntime
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal
from domain.xeed.model import Xeed
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.subscriber_projection.continuity_store import SqliteSubscriberContinuityStore
from pipeline.subscriber_projection.opportunity_store import (
    SqliteSubscriberOpportunityProjectionStore,
)
from pipeline.subscriber_projection.sqlite_store import SqliteSubscriberEconomicOutputStore

POLICY = TemporalCurrentnessPolicy(
    "subscriber-currentness", "1", timedelta(days=7), timedelta(days=30)
)
REUSE = ObservationReusePolicy("subscriber-read", "1")


@dataclass
class Auth:
    principals: dict[str, Principal] = field(default_factory=dict)
    xeeds: dict[str, Xeed] = field(default_factory=dict)
    memberships: set[tuple[str, str]] = field(default_factory=set)
    organizations: dict[str, Organization] = field(default_factory=dict)

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        return self.principals.get(principal_id)

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        return (principal_id, tenant_id) in self.memberships

    def get_xeed(self, xeed_id: XeedId) -> Xeed | None:
        return self.xeeds.get(xeed_id)

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organizations.get(organization_id)

    def focus(self, n: int, organization: Organization) -> tuple[TrustedRequestContext, Xeed]:
        """Principal n, Tenant n, Focus n on ``organization`` (one membership each)."""
        principal, tenant = PrincipalId(f"principal:{n}"), TenantId(f"tenant:{n}")
        xeed = Xeed(XeedId(f"focus_{n:032x}"), tenant, organization.id, organization.canonical_name)
        self.principals[principal] = Principal(principal)
        self.memberships.add((principal, tenant))
        self.xeeds[xeed.id] = xeed
        self.organizations[organization.id] = organization
        return TrustedRequestContext(principal, tenant), xeed


def public(subject_id: str, observation_id: str, **overrides: Any) -> ObservationReuseAuthority:
    values: dict[str, Any] = {
        "rights_status": ObservationRightsStatus.PERMITTED,
        "access_status": ObservationAccessStatus.ACCESSIBLE,
        "scope": ObservationReuseScope.GLOBAL_PUBLIC,
        "provenance_ref": f"provenance:{observation_id}",
        "currentness": Currentness.CURRENT,
        "applicable_subject_ids": (subject_id,),
        "applicable_purposes": ("CURRENT_STATE", "HISTORICAL_REFERENCE"),
        "authority_id": "test-source-policy",
        "authority_version": "1",
    }
    values.update(overrides)
    return ObservationReuseAuthority(**values)


def observation(
    subject_id: str,
    observation_id: str,
    *,
    source_ref: str,
    observed_at: datetime,
    content: str,
    fields: tuple[ObservedField, ...] = (),
    authority: ObservationReuseAuthority | None = None,
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id=subject_id,
            source_ref=source_ref,
            source_type="PUBLIC_WEBSITE",
            observed_at=observed_at,
            content_fingerprint="fp:" + content,
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=content,
        fields=fields,
        reuse_authority=authority or public(subject_id, observation_id),
    )


def runtime(
    root: Path, auth: Auth, memory: SqliteObservationMemory | None = None
) -> tuple[SubscriberEconomicRuntime, SqliteSubscriberContinuityStore]:
    database = root / "subscriber-economic-output.sqlite3"
    economic = SubscriberEconomicRuntime(
        authorized_xeeds=AuthorizedXeedReader(auth, auth, auth),
        organization_reader=AuthorizedXeedOrganizationReader(auth),
        observation_memory=memory or SqliteObservationMemory(root / "observation-memory.sqlite3"),
        output_store=SqliteSubscriberEconomicOutputStore(database),
        opportunity_store=SqliteSubscriberOpportunityProjectionStore(database),
        reuse_policy=REUSE,
        temporal_policy=POLICY,
        code_sha="test-sha",
    )
    store = SqliteSubscriberContinuityStore(database)
    economic.continuity = ContinuityService(economic, store)
    return economic, store


def seed_eb04_evidence(result: Any, memory: SqliteObservationMemory) -> tuple[str, str]:
    """Persist the EB-04 result's evidence as governed public observations."""

    wire = result.human_output.to_wire()
    organization_id, activity_id = str(wire["subject_ref"]), str(wire["activity_subject_ref"])
    subject_refs = {
        str(item.datum.observation_id) for item in result.subject_source.state.observations
    }
    seen: set[str] = set()
    for item in wire["evidence"]:
        observation_id = str(item["observation_ref"])
        if observation_id in seen:
            continue
        seen.add(observation_id)
        subject_id = organization_id if observation_id in subject_refs else activity_id
        memory.append(
            observation(
                subject_id,
                observation_id,
                source_ref=str(item["source_ref"]),
                observed_at=datetime.fromisoformat(str(item["observed_at"])),
                content=f"content:{observation_id}",
            )
        )
    return organization_id, activity_id
