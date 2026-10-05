"""E2E contract: authorized Xeed -> TurboQuant -> evidence admission -> FAXT write."""

from __future__ import annotations

from datetime import UTC, datetime

from application.semantic_retrieval import SemanticRepresentation
from application.xeed_access.organization_reader import (
    AuthorizedXeedOrganization,
    AuthorizedXeedOrganizationReader,
)
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination import (
    EvidenceSupportClass,
    EvidenceSupportJudgment,
    GerminationBudget,
    GerminationCandidate,
    GerminationQueryFamily,
    InvestigationFinding,
    XeedSemanticGermination,
)
from domain.evidence.admission import Evidence, GroundedClaim, SourceAuthority
from domain.evidence.epistemics import Currentness
from domain.faxt.model import FAXT
from domain.identity import FaxtId, OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from pipeline.evidence import EvidenceLedger
from pipeline.semantic_judgment import SemanticJudgmentLedger
from pipeline.semantic_retrieval import TurboQuantSemanticIndex
from tests.support.grounding import with_synthetic_representation
from tests.support.xeed_authority import InMemoryXeedAuthority


class Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


class Encoder:
    def encode(self, text: str) -> tuple[float, ...]:
        return (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)


class Catalog:
    def __init__(self) -> None:
        self.items = {
            "rep-cold": GerminationCandidate(
                "rep-cold",
                OrganizationId("org-cold"),
                "es",
                ("ES",),
                Currentness.CURRENT,
                GerminationQueryFamily.CAPABILITY_ADJACENCY,
            ),
            "rep-pumps": GerminationCandidate(
                "rep-pumps",
                OrganizationId("org-pumps"),
                "es",
                ("ES",),
                Currentness.CURRENT,
                GerminationQueryFamily.CAPABILITY_ADJACENCY,
            ),
        }

    def get(self, representation_id: str) -> GerminationCandidate | None:
        return self.items.get(representation_id)


class Investigator:
    def investigate(
        self, *, seed: object, candidate: GerminationCandidate
    ) -> InvestigationFinding | None:
        if candidate.organization_id != OrganizationId("org-cold"):
            return None
        claim = "org-cold capability industrial refrigeration."
        return InvestigationFinding(
            FaxtId("faxt-cold-capability"),
            candidate.organization_id,
            "capability",
            "industrial refrigeration",
            claim,
            with_synthetic_representation(
                Evidence(
                    "ev-cold-capability",
                    "fixture",
                    "official_web",
                    "https://cold.example.test/capabilities",
                    claim,
                    datetime(2026, 9, 30, tzinfo=UTC),
                    SourceAuthority.OFFICIAL_WEB,
                    observation_subject_id="org-cold",
                    grounded_claim=GroundedClaim(
                        subject_id="org-cold",
                        predicate="capability",
                        object_or_value="industrial refrigeration",
                        subject_mention="org-cold",
                        predicate_mention="capability",
                        object_mention="industrial refrigeration",
                        supporting_excerpt=claim,
                    ),
                )
            ),
            currentness=Currentness.CURRENT,
        )


class SupportJudge:
    def judge(self, finding: InvestigationFinding) -> EvidenceSupportJudgment:
        return EvidenceSupportJudgment(
            EvidenceSupportClass.SUPPORTED,
            "deterministic-test-judge",
            "test.v1",
        )


class JudgmentWriter:
    def __init__(self) -> None:
        self.items: list[tuple[InvestigationFinding, EvidenceSupportJudgment]] = []

    def append(
        self,
        finding: InvestigationFinding,
        judgment: EvidenceSupportJudgment,
    ) -> None:
        self.items.append((finding, judgment))


class Writer:
    def __init__(self) -> None:
        self.written: list[FAXT] = []

    def write(self, faxt: FAXT) -> None:
        self.written.append(faxt)


def seed() -> AuthorizedXeedOrganization:
    authority = InMemoryXeedAuthority()
    authority.add_principal(Principal(PrincipalId("principal")))
    authority.add_tenant(Tenant(TenantId("tenant")))
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal"), TenantId("tenant"))
    )
    authority.add_xeed(
        Xeed(XeedId("xeed"), TenantId("tenant"), OrganizationId("org-seed"), "Food Producer")
    )
    authorized = AuthorizedXeedReader(authority, authority, authority).read(
        TrustedRequestContext(PrincipalId("principal"), TenantId("tenant")), XeedId("xeed")
    )
    organization = Organization(
        OrganizationId("org-seed"),
        "Food Producer",
        locations=("ES",),
    )
    return AuthorizedXeedOrganizationReader(Organizations(organization)).read(authorized)


def test_authorized_xeed_reaches_canonical_writer_only_through_evidence_admission() -> None:
    index = TurboQuantSemanticIndex(dimension=8, num_bits=8, seed=7)
    index.rebuild(
        (
            SemanticRepresentation("rep-cold", (1.0, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
            SemanticRepresentation("rep-pumps", (0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        )
    )
    writer = Writer()
    judgments = SemanticJudgmentLedger()
    evidence = EvidenceLedger()
    flow = XeedSemanticGermination(
        encoder=Encoder(),
        index=index,
        catalog=Catalog(),
        judgment_writer=judgments,
        support_judge=SupportJudge(),
        investigator=Investigator(),
        evidence_writer=evidence,
        faxt_writer=writer,
    )

    result = flow.run(
        seed(),
        budget=GerminationBudget(retrieval_k=2, max_investigations=2, locale="es", geography="ES"),
    )

    assert len(result.admitted) == 1
    assert result.admitted[0].representation_id == "rep-cold"
    assert writer.written[0].id == FaxtId("faxt-cold-capability")
    assert writer.written[0].evidence_refs == ("ev-cold-capability",)
    assert tuple(item.id for item in evidence.entries) == ("ev-cold-capability",)
    assert len(judgments.entries) == 1
    assert judgments.entries[0].judgment.support is EvidenceSupportClass.SUPPORTED
