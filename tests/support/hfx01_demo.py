"""Synthetic in-memory AXIGLAND context assembled through canonical contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from application.subscriber_projection.axigland import (
    SubscriberAxiglandProjection,
    project_axigland,
)
from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganizationReader,
)
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_knowledge.reader import AuthorizedXeedFaxtCollectionReader
from domain.evidence.admission import Evidence, EvidenceAdmission, SourceAuthority
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import (
    FaxtId,
    OrganizationId,
    PrincipalId,
    TenantId,
    XeedId,
)
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.knowledge_reference import XeedFaxtReference
from domain.xeed.model import Xeed
from tests.support.xeed_authority import InMemoryXeedAuthority
from tests.support.xeed_knowledge import InMemoryXeedKnowledgeAuthority


class _Organizations:
    """Global Organization authority used only by tests and the loopback demo."""

    def __init__(self) -> None:
        self.items: dict[OrganizationId, Organization] = {}

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.items.get(organization_id)


class Hfx01Demo:
    """A local-only pair of tenant contexts over one global Organization."""

    def __init__(self, organization_name: str = "Northwind Materials (synthetic demo)") -> None:
        self.identities = InMemoryXeedAuthority()
        self.knowledge = InMemoryXeedKnowledgeAuthority()
        self.organizations = _Organizations()
        self.xeed_reader = AuthorizedXeedReader(self.identities, self.identities, self.identities)
        self.organization_reader = AuthorizedXeedOrganizationReader(self.organizations)
        self.faxt_reader = AuthorizedXeedFaxtCollectionReader(self.knowledge, self.knowledge)

        shared_org = Organization(
            OrganizationId("org-demo-shared"),
            organization_name,
            capabilities=("Industrial materials manufacturing",),
            markets=("Northern Europe",),
        )
        self.organizations.items[shared_org.id] = shared_org

        for principal_id, tenant_id, xeed_id, label in (
            ("principal-demo-a", "tenant-demo-a", "xeed-demo-a", "Demo context"),
            ("principal-demo-b", "tenant-demo-b", "xeed-demo-b", "Isolated demo context"),
        ):
            principal = Principal(PrincipalId(principal_id))
            tenant = Tenant(TenantId(tenant_id))
            self.identities.add_principal(principal)
            self.identities.add_tenant(tenant)
            self.identities.add_membership(PrincipalTenantMembership(principal.id, tenant.id))
            self.identities.add_xeed(Xeed(XeedId(xeed_id), tenant.id, shared_org.id, label))

        self.identities.add_xeed(
            Xeed(
                XeedId("xeed-demo-empty"),
                TenantId("tenant-demo-a"),
                shared_org.id,
                "Empty demo context",
            )
        )

        for faxt_id, subject_id, predicate, value, epistemic_state in (
            (
                "faxt-demo-a",
                "subject-demo-a-unknown-kind",
                "MANUFACTURES",
                "precision components",
                EpistemicState.OBSERVED,
            ),
            (
                "faxt-demo-b",
                "subject-demo-b-unknown-kind",
                "SERVES_MARKET",
                "specialty industrial buyers",
                EpistemicState.STALE,
            ),
            (
                "faxt-demo-a2",
                "subject-demo-a2-unknown-kind",
                "MAINTAINS_STANDARD",
                "ISO 9001",
                EpistemicState.STALE,
            ),
        ):
            evidence = Evidence(
                id=f"evidence-{faxt_id}",
                source="synthetic://hfx01-test-fixture",
                source_type="test",
                reference=f"synthetic://{faxt_id}",
                extracted_claim=f"Synthetic demo field for {faxt_id}",
                observed_at=datetime(2026, 9, 1, tzinfo=UTC),
                authority=SourceAuthority.OFFICIAL_WEB,
            )
            faxt = FAXT.create(
                faxt_id=FaxtId(faxt_id),
                subject_id=subject_id,
                predicate=predicate,
                object_or_value=value,
                evidence=evidence,
                decision=EvidenceAdmission.admit(evidence),
                epistemic_state=epistemic_state,
                currentness=Currentness.UNKNOWN,
            )
            self.knowledge.add_faxt(faxt)

        self.knowledge.add_reference(
            XeedFaxtReference(XeedId("xeed-demo-a"), FaxtId("faxt-demo-a"))
        )
        self.knowledge.add_reference(
            XeedFaxtReference(XeedId("xeed-demo-a"), FaxtId("faxt-demo-a2"))
        )
        self.knowledge.add_reference(
            XeedFaxtReference(XeedId("xeed-demo-b"), FaxtId("faxt-demo-b"))
        )

    def project_for(
        self, principal_id: str, tenant_id: str, xeed_id: str
    ) -> SubscriberAxiglandProjection:
        """Run authorization, canonical reads, and the subscriber projection."""

        authorized = self.xeed_reader.read(
            TrustedRequestContext(PrincipalId(principal_id), TenantId(tenant_id)),
            XeedId(xeed_id),
        )
        organization = self.organization_reader.read(authorized)
        faxts = self.faxt_reader.read(authorized)
        return project_axigland(organization, faxts)

    def selected_demo_projection(self) -> SubscriberAxiglandProjection:
        """Return only the primary explicitly authorized synthetic demo context."""

        return self.project_for("principal-demo-a", "tenant-demo-a", "xeed-demo-a")

    def empty_demo_projection(self) -> SubscriberAxiglandProjection:
        """Read a genuinely empty, explicitly authorized synthetic Xeed."""

        return self.project_for("principal-demo-a", "tenant-demo-a", "xeed-demo-empty")
