from datetime import UTC, datetime

import pytest

from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.subscriber_projection import ExplanationStepKind, project_explainable_xignal
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from domain.evidence import Currentness
from domain.evidence.admission import Evidence, EvidenceAdmission, SourceAuthority
from domain.faxt.model import FAXT
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from domain.xignal import XignalEpistemicState, XignalKind
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 9, 30, 18, 45, tzinfo=UTC)


class _Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


def _seed():
    authority = InMemoryXeedAuthority()
    authority.add_principal(Principal(PrincipalId("principal:1")))
    authority.add_tenant(Tenant(TenantId("tenant:1")))
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal:1"), TenantId("tenant:1"))
    )
    authority.add_xeed(Xeed(XeedId("xeed:1"), TenantId("tenant:1"), OrganizationId("org:acme")))
    authorized = AuthorizedXeedReader(authority, authority, authority).read(
        TrustedRequestContext(PrincipalId("principal:1"), TenantId("tenant:1")),
        XeedId("xeed:1"),
    )
    organization = Organization(OrganizationId("org:acme"), "ACME")
    return AuthorizedXeedOrganizationReader(_Organizations(organization)).read(authorized)


def _evidence() -> Evidence:
    return Evidence(
        id="evidence:web:1",
        source="ACME corporate website",
        source_type="OFFICIAL_WEB",
        reference="https://example.test/company",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=NOW,
        authority=SourceAuthority.OFFICIAL_WEB,
    )


def _faxt() -> FAXT:
    evidence = _evidence()
    return FAXT.create(
        faxt_id="faxt:manufactures-pumps",
        subject_id="org:acme",
        predicate="manufactures",
        object_or_value="industrial pumps",
        evidence=evidence,
        decision=EvidenceAdmission.admit(evidence),
        observed_at=NOW,
        currentness=Currentness.CURRENT,
    )


def _basis(*, with_evidence: bool = True, contradiction: bool = True) -> ExplainableBasis:
    data = [
        BasisDatum(
            datum_id="datum:web:1",
            observation_id="obs:web:1",
            source_ref="https://example.test/company",
            source_type="OFFICIAL_WEB",
            observed_at=NOW,
            excerpt_or_summary="ACME manufactures industrial pumps.",
            contribution=BasisContribution.SUPPORTS,
            evidence_ref="evidence:web:1" if with_evidence else None,
        )
    ]
    if contradiction:
        data.append(
            BasisDatum(
                datum_id="datum:registry:1",
                observation_id="obs:registry:1",
                source_ref="registry:acme",
                source_type="PUBLIC_REGISTRY",
                observed_at=NOW,
                excerpt_or_summary="Registry scope does not explicitly mention pump manufacturing.",
                contribution=BasisContribution.CONTRADICTS,
            )
        )
    return ExplainableBasis(
        basis_id="basis:market-signal:1",
        subject_id="org:acme",
        candidate_id="candidate:industrial-pumps",
        semantic_target="CAPABILITY_SIGNAL",
        state_fingerprint="state:1",
        contract_fingerprint="contract:1",
        evaluated_at=NOW,
        data=tuple(data),
        interpretation="Pump manufacturing is directly observed and economically relevant.",
        uncertainty="Registry wording is broader than the website claim.",
    )


def test_observed_xignal_requires_admitted_canonical_support() -> None:
    with pytest.raises(ValueError, match="requires admitted canonical support"):
        project_explainable_xignal(
            organization_context=_seed(),
            candidate_id="candidate:industrial-pumps",
            kind=XignalKind.SUPPLY,
            epistemic_state=XignalEpistemicState.OBSERVED,
            title="Industrial pump manufacturing observed",
            why_attention="This capability changes the observable supply map.",
            basis=_basis(),
            emitted_at=NOW,
            policy_version="xignal-v1",
        )


def test_observed_xignal_traces_admitted_faxt_and_sources_deterministically() -> None:
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:industrial-pumps",
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="This capability changes the observable supply map.",
        basis=_basis(),
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
        unknowns=("Whether the capability is available in all geographies is unknown.",),
    )
    assert projection.xignal.is_canonical_truth is False
    assert projection.xignal.epistemic_state is XignalEpistemicState.OBSERVED
    assert projection.xignal.currentness is Currentness.CURRENT
    assert projection.xignal.canonical_support_refs == ("faxt:manufactures-pumps",)
    assert projection.xignal.contradictions == (
        "Registry scope does not explicitly mention pump manufacturing.",
    )
    assert [step.kind for step in projection.trail.steps] == [
        ExplanationStepKind.XIGNAL,
        ExplanationStepKind.CANONICAL_SUPPORT,
        ExplanationStepKind.SUPPORTS,
        ExplanationStepKind.CONTRADICTS,
        ExplanationStepKind.UNKNOWN,
    ]
    assert projection.trail.steps[2].ref == "evidence:web:1"
    assert projection.source_refs == ("https://example.test/company", "registry:acme")


def test_observed_xignal_rejects_basis_not_bound_to_admitted_evidence() -> None:
    with pytest.raises(ValueError, match="must reference admitted FAXT evidence"):
        project_explainable_xignal(
            organization_context=_seed(),
            candidate_id="candidate:industrial-pumps",
            kind=XignalKind.SUPPLY,
            epistemic_state=XignalEpistemicState.OBSERVED,
            title="Industrial pump manufacturing observed",
            why_attention="This capability changes the observable supply map.",
            basis=_basis(with_evidence=False),
            emitted_at=NOW,
            policy_version="xignal-v1",
            canonical_faxt=_faxt(),
        )


def test_potential_xignal_remains_potential_without_canonical_support() -> None:
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:food-factories",
        kind=XignalKind.DEMAND,
        epistemic_state=XignalEpistemicState.POTENTIAL,
        title="Food-factory demand may be relevant",
        why_attention="Observed product semantics make this market worth testing.",
        basis=ExplainableBasis(
            basis_id="basis:potential:1",
            subject_id="org:acme",
            candidate_id="candidate:food-factories",
            semantic_target="POTENTIAL_DEMAND",
            state_fingerprint="state:2",
            contract_fingerprint="contract:2",
            evaluated_at=NOW,
            data=(
                BasisDatum(
                    datum_id="datum:context:1",
                    observation_id="obs:web:2",
                    source_ref="https://example.test/company",
                    source_type="OFFICIAL_WEB",
                    observed_at=NOW,
                    excerpt_or_summary="ACME markets pumps suitable for food-process environments.",
                    contribution=BasisContribution.SUPPORTS,
                ),
            ),
            interpretation="Food factories are a plausible demand segment.",
            uncertainty="No customer relationship has been observed.",
        ),
        emitted_at=NOW,
        policy_version="xignal-v1",
        unknowns=("No observed buyer relationship yet.",),
    )
    assert projection.xignal.epistemic_state is XignalEpistemicState.POTENTIAL
    assert projection.xignal.canonical_support_refs == ()
    assert projection.xignal.currentness is Currentness.UNKNOWN


def test_unknown_xignal_requires_and_preserves_explicit_unknowns() -> None:
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:export-currentness",
        kind=XignalKind.KNOWLEDGE_GAP,
        epistemic_state=XignalEpistemicState.UNKNOWN,
        title="Export currentness unresolved",
        why_attention="The gap affects market interpretation.",
        basis=ExplainableBasis(
            basis_id="basis:unknown:1",
            subject_id="org:acme",
            candidate_id="candidate:export-currentness",
            semantic_target="EXPORT_CURRENTNESS",
            state_fingerprint="state:3",
            contract_fingerprint="contract:3",
            evaluated_at=NOW,
            data=(
                BasisDatum(
                    datum_id="datum:historical:1",
                    observation_id="obs:historical:1",
                    source_ref="https://example.test/archive",
                    source_type="OFFICIAL_WEB",
                    observed_at=NOW,
                    excerpt_or_summary="Historical export wording exists but current status is unresolved.",
                    contribution=BasisContribution.SUPPORTS,
                ),
            ),
            interpretation="Export activity cannot currently be established.",
            uncertainty="Fresh evidence is missing.",
        ),
        emitted_at=NOW,
        policy_version="xignal-v1",
        unknowns=("Current export activity is UNKNOWN.",),
    )
    assert projection.xignal.epistemic_state is XignalEpistemicState.UNKNOWN
    assert projection.xignal.unknowns == ("Current export activity is UNKNOWN.",)
    assert projection.trail.steps[-1].kind is ExplanationStepKind.UNKNOWN
