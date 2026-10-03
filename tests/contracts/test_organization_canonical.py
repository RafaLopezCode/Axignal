"""Organization identity is canonical, never subscriber-scoped (MASTER §6, §7.3)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from domain.evidence.admission import AdmissionRequest, Evidence, EvidenceAdmission, SourceAuthority
from domain.evidence.epistemics import EpistemicState
from domain.faxt.model import FAXT
from domain.identity import OrganizationId
from domain.organizations.model import Organization, OrganizationError

FORBIDDEN_SCOPE_FIELDS = {
    "account_id",
    "subscriber_id",
    "tenant_id",
    "owner_id",
    "user_id",
    "claimed_by",
    "profile_owner",
    "xignal_id",
    "subscription_id",
}


def test_organization_has_no_subscriber_scope_fields() -> None:
    field_names = {field.name for field in dataclasses.fields(Organization)}
    assert field_names & FORBIDDEN_SCOPE_FIELDS == set()


def test_organization_identity_is_observer_independent() -> None:
    organization = Organization(id=OrganizationId("org-acme"), canonical_name="ACME")
    assert organization.identity_key == OrganizationId("org-acme")


def test_organization_business_profile_requires_admitted_faxt() -> None:
    with pytest.raises(OrganizationError, match="admitted FAXT"):
        Organization(
            id=OrganizationId("org-acme"),
            canonical_name="ACME",
            capabilities=("industrial pumps",),
        )


def test_organization_profile_materializes_from_observed_faxt() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    evidence = Evidence(
        id="ev-capability",
        source="ACME official website",
        source_type="web",
        reference="https://acme.example/capabilities",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=now,
        authority=SourceAuthority.OFFICIAL_WEB,
    )
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )
    faxt = FAXT.create(
        faxt_id="faxt-capability",
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        evidence=evidence,
        decision=EvidenceAdmission.admit_claim(request),
        epistemic_state=EpistemicState.OBSERVED,
    )
    organization = Organization.from_admitted_faxts(
        organization_id=OrganizationId("org-acme"),
        canonical_name="ACME",
        faxts=(faxt,),
    )
    assert organization.capabilities == ("industrial pumps",)
    assert organization.evidence_refs == ("ev-capability",)


def test_organization_profile_rejects_inferred_faxt_promotion() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    evidence = Evidence(
        id="ev-inferred",
        source="ACME official website",
        source_type="web",
        reference="https://acme.example/capabilities",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=now,
        authority=SourceAuthority.OFFICIAL_WEB,
    )
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )
    faxt = FAXT.create(
        faxt_id="faxt-inferred",
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        evidence=evidence,
        decision=EvidenceAdmission.admit_claim(request),
        epistemic_state=EpistemicState.INFERRED,
    )
    with pytest.raises(OrganizationError, match="non-observed"):
        Organization.from_admitted_faxts(
            organization_id=OrganizationId("org-acme"),
            canonical_name="ACME",
            faxts=(faxt,),
        )
