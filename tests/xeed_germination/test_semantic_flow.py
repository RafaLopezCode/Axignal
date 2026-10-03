from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.semantic_retrieval import SemanticCandidate
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
from domain.evidence.admission import Evidence, SourceAuthority
from domain.evidence.epistemics import Currentness
from domain.faxt.model import FAXT
from domain.identity import FaxtId, OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from pipeline.evidence import EvidenceLedger
from tests.support.xeed_authority import InMemoryXeedAuthority


class Encoder:
    def encode(self, text: str) -> tuple[float, ...]:
        assert "ColdChain Seed" in text
        return (1.0, 0.0, 0.0)


class Index:
    size = 6

    def rebuild(self, representations: object) -> None:
        raise AssertionError("run must not rebuild the index")

    def search(self, vector: object, *, k: int) -> tuple[SemanticCandidate, ...]:
        assert k == 6
        return (
            SemanticCandidate("self", 1.0),
            SemanticCandidate("stale", 0.99),
            SemanticCandidate("wrong-locale", 0.98),
            SemanticCandidate("duplicate-a", 0.97),
            SemanticCandidate("candidate-a", 0.96),
            SemanticCandidate("candidate-b", 0.95),
        )


class Catalog:
    def __init__(self) -> None:
        self.items = {
            "self": candidate("self", "org-seed"),
            "stale": candidate("stale", "org-stale", currentness=Currentness.STALE),
            "wrong-locale": candidate("wrong-locale", "org-fr", locale="fr"),
            "duplicate-a": candidate("duplicate-a", "org-a"),
            "candidate-a": candidate("candidate-a", "org-a"),
            "candidate-b": candidate("candidate-b", "org-b"),
        }

    def get(self, representation_id: str) -> GerminationCandidate | None:
        return self.items.get(representation_id)


def candidate(
    representation_id: str,
    organization_id: str,
    *,
    locale: str = "en",
    currentness: Currentness = Currentness.CURRENT,
) -> GerminationCandidate:
    return GerminationCandidate(
        representation_id=representation_id,
        organization_id=OrganizationId(organization_id),
        locale=locale,
        geographies=("ES",),
        currentness=currentness,
        query_family=GerminationQueryFamily.CAPABILITY_ADJACENCY,
    )


class Investigator:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.calls: list[str] = []
        self.mismatch = mismatch

    def investigate(self, *, seed: object, candidate: GerminationCandidate) -> InvestigationFinding:
        self.calls.append(candidate.representation_id)
        subject = "org-wrong" if self.mismatch else candidate.organization_id
        authority = (
            SourceAuthority.AGENCY_SIGNAL
            if candidate.organization_id == OrganizationId("org-b")
            else SourceAuthority.OFFICIAL_WEB
        )
        return InvestigationFinding(
            faxt_id=FaxtId(f"faxt-{candidate.organization_id}"),
            subject_id=OrganizationId(str(subject)),
            predicate="capability",
            object_or_value="cold-chain logistics",
            claim_proposition="The organization provides cold-chain logistics.",
            evidence=Evidence(
                id=f"ev-{candidate.organization_id}",
                source="fixture",
                source_type="web",
                reference=f"https://example.test/{candidate.organization_id}",
                extracted_claim="The organization provides cold-chain logistics.",
                observed_at=datetime(2026, 9, 30, tzinfo=UTC),
                authority=authority,
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


class Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


def authorized_seed() -> AuthorizedXeedOrganization:
    authority = InMemoryXeedAuthority()
    authority.add_principal(Principal(PrincipalId("principal")))
    authority.add_tenant(Tenant(TenantId("tenant")))
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal"), TenantId("tenant"))
    )
    authority.add_xeed(
        Xeed(XeedId("xeed"), TenantId("tenant"), OrganizationId("org-seed"), "ColdChain Seed")
    )
    authorized_xeed = AuthorizedXeedReader(authority, authority, authority).read(
        TrustedRequestContext(PrincipalId("principal"), TenantId("tenant")),
        XeedId("xeed"),
    )
    organization = Organization(
        OrganizationId("org-seed"),
        "ColdChain Seed",
        capabilities=("industrial refrigeration",),
        markets=("food logistics",),
        locations=("ES",),
    )
    return AuthorizedXeedOrganizationReader(Organizations(organization)).read(authorized_xeed)


def test_flow_filters_before_investigation_and_only_writes_admitted_evidence() -> None:
    investigator = Investigator()
    writer = Writer()
    judgments = JudgmentWriter()
    evidence = EvidenceLedger()
    flow = XeedSemanticGermination(
        encoder=Encoder(),
        index=Index(),
        catalog=Catalog(),
        judgment_writer=judgments,
        support_judge=SupportJudge(),
        investigator=investigator,
        evidence_writer=evidence,
        faxt_writer=writer,
    )

    result = flow.run(
        authorized_seed(),
        budget=GerminationBudget(retrieval_k=6, max_investigations=2, locale="en", geography="ES"),
    )

    assert result.retrieved_count == 6
    assert result.eligible_count == 2
    assert result.investigated_count == 2
    assert result.rejected_evidence_count == 1
    assert investigator.calls == ["duplicate-a", "candidate-b"]
    assert [item.faxt.id for item in result.admitted] == [FaxtId("faxt-org-a")]
    assert writer.written == [result.admitted[0].faxt]
    assert tuple(item.id for item in evidence.entries) == ("ev-org-a",)
    assert len(judgments.items) == 2


def test_subject_mismatch_fails_closed_before_canonical_write() -> None:
    writer = Writer()
    judgments = JudgmentWriter()
    evidence = EvidenceLedger()
    flow = XeedSemanticGermination(
        encoder=Encoder(),
        index=Index(),
        catalog=Catalog(),
        judgment_writer=judgments,
        support_judge=SupportJudge(),
        investigator=Investigator(mismatch=True),
        evidence_writer=evidence,
        faxt_writer=writer,
    )

    with pytest.raises(ValueError, match="subject"):
        flow.run(
            authorized_seed(),
            budget=GerminationBudget(retrieval_k=6, max_investigations=1, locale="en"),
        )

    assert writer.written == []
    assert evidence.entries == ()
    assert judgments.items == []


class RejectingSupportJudge:
    def judge(self, finding: InvestigationFinding) -> EvidenceSupportJudgment:
        return EvidenceSupportJudgment(
            EvidenceSupportClass.NO_EVIDENCE,
            "deterministic-test-judge",
            "test.v1",
        )


def test_semantic_non_support_never_reaches_evidence_admission_or_writer() -> None:
    writer = Writer()
    judgments = JudgmentWriter()
    evidence = EvidenceLedger()
    flow = XeedSemanticGermination(
        encoder=Encoder(),
        index=Index(),
        catalog=Catalog(),
        investigator=Investigator(),
        judgment_writer=judgments,
        support_judge=RejectingSupportJudge(),
        evidence_writer=evidence,
        faxt_writer=writer,
    )

    result = flow.run(
        authorized_seed(),
        budget=GerminationBudget(retrieval_k=6, max_investigations=1, locale="en"),
    )

    assert result.rejected_semantic_count == 1
    assert result.rejected_evidence_count == 0
    assert result.admitted == ()
    assert evidence.entries == ()
    assert writer.written == []
    assert len(judgments.items) == 1
    assert judgments.items[0][1].support is EvidenceSupportClass.NO_EVIDENCE


def test_semantic_judgment_rejects_invalid_provider_probability_data() -> None:
    with pytest.raises(ValueError, match="distribution"):
        EvidenceSupportJudgment(
            EvidenceSupportClass.SUPPORTED,
            "provider",
            "contract.v1",
            distribution=(("SUPPORTED", 1.2),),
        )
    with pytest.raises(ValueError, match="confidence"):
        EvidenceSupportJudgment(
            EvidenceSupportClass.SUPPORTED,
            "provider",
            "contract.v1",
            confidence=float("nan"),
        )


class ContradictingInvestigator(Investigator):
    def investigate(
        self,
        *,
        seed: object,
        candidate: GerminationCandidate,
    ) -> InvestigationFinding:
        finding = super().investigate(seed=seed, candidate=candidate)
        return InvestigationFinding(
            faxt_id=finding.faxt_id,
            subject_id=finding.subject_id,
            predicate=finding.predicate,
            object_or_value=finding.object_or_value,
            claim_proposition=finding.claim_proposition,
            evidence=Evidence(
                id=finding.evidence.id,
                source=finding.evidence.source,
                source_type=finding.evidence.source_type,
                reference=finding.evidence.reference,
                extracted_claim="The organization does not provide cold-chain logistics.",
                observed_at=finding.evidence.observed_at,
                authority=finding.evidence.authority,
            ),
            epistemic_state=finding.epistemic_state,
            currentness=finding.currentness,
        )


def test_supported_judgment_cannot_override_contradictory_evidence_claim() -> None:
    writer = Writer()
    judgments = JudgmentWriter()
    evidence = EvidenceLedger()
    flow = XeedSemanticGermination(
        encoder=Encoder(),
        index=Index(),
        catalog=Catalog(),
        investigator=ContradictingInvestigator(),
        judgment_writer=judgments,
        support_judge=SupportJudge(),
        evidence_writer=evidence,
        faxt_writer=writer,
    )

    result = flow.run(
        authorized_seed(),
        budget=GerminationBudget(
            retrieval_k=6,
            max_investigations=1,
            locale="en",
            geography="ES",
        ),
    )

    assert result.rejected_semantic_count == 0
    assert result.rejected_evidence_count == 1
    assert result.admitted == ()
    assert evidence.entries == ()
    assert writer.written == []
    assert len(judgments.items) == 1
    assert judgments.items[0][1].support is EvidenceSupportClass.SUPPORTED
