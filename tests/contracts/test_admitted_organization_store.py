import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.subscriber_portfolio.models import OrganizationIdentityPending
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    GroundedClaim,
    SourceAuthority,
)
from domain.identity import OrganizationId
from domain.representation import TextRepresentation, TextSurface, text_fingerprint
from pipeline.entity_resolution.organization_store import (
    OrganizationMaterializationError,
    SqliteCanonicalOrganizationStore,
)
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)


def admitted_identity(
    artifacts: ContentAddressedArtifactStore,
    identity: str = "org:registry:one",
    name: str = "Registered Example SLU",
) -> AdmissionRequest:
    now = datetime(2026, 10, 6, 10, tzinfo=UTC)
    text = f"{identity} legal_identity {name}"
    source_ref = "https://registry.example.invalid/records/one"
    body = artifacts.put_bytes(text.encode())
    observation = artifacts.put_json(
        {"source": source_ref, "body": body, "observed_at": now.isoformat()}
    )
    surface = artifacts.put_json({"text": text, "body": body, "observation": observation})
    representation = TextRepresentation(
        representation_id="repr:" + identity,
        representation_version="controlled-registry:v1",
        subject_id=identity,
        source_ref=source_ref,
        source_type="REGISTRY_RECORD",
        observation_id="observation:" + identity,
        observed_at=now,
        surface=TextSurface.STRUCTURED_DATA,
        text=text,
        normalization_version="controlled-test:v1",
        source_content_fingerprint=text_fingerprint(text),
        source_observation_fingerprint=observation,
        source_artifact_ref=body,
        source_observation_artifact_ref=observation,
        artifact_ref=surface,
        document_fingerprint=text_fingerprint(text),
    )
    claim = GroundedClaim(
        identity,
        "legal_identity",
        name,
        identity,
        "legal_identity",
        name,
        text,
        supporting_span=representation.span(0, len(text)),
    )
    evidence = Evidence(
        "evidence:" + identity,
        "Controlled registry contract test",
        "REGISTRY_RECORD",
        source_ref,
        text,
        now,
        SourceAuthority.REGISTRY,
        observation_subject_id=identity,
        grounded_claim=claim,
        representation=representation,
    )
    return AdmissionRequest(evidence, identity, "legal_identity", name, text)


def make_store(
    tmp_path: Path,
) -> tuple[SqliteCanonicalOrganizationStore, ContentAddressedArtifactStore]:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    store = SqliteCanonicalOrganizationStore(
        tmp_path / "global.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        governance=SqliteIdentityGovernanceStore(tmp_path / "identity-governance.sqlite3"),
    )
    return store, artifacts


def test_exact_registry_identity_survives_restart_and_cannot_be_edited(tmp_path: Path) -> None:
    store, artifacts = make_store(tmp_path)
    request = admitted_identity(artifacts)
    decision = EvidenceAdmission.admit_claim(request)
    assert store.register(request, decision)
    restarted, _ = make_store(tmp_path)
    assert not restarted.register(request, decision)
    resolved = restarted.resolve("registered example slu")
    assert not isinstance(resolved, OrganizationIdentityPending)
    assert resolved.id == "org:registry:one"
    assert resolved.capabilities == () and resolved.markets == ()
    changed = admitted_identity(artifacts, name="Subscriber Preferred Name")
    with pytest.raises(OrganizationMaterializationError, match="reevaluation"):
        restarted.register(changed, EvidenceAdmission.admit_claim(changed))
    assert restarted.get_organization(OrganizationId("org:registry:one")) == resolved


def test_url_and_name_ambiguity_remain_pending(tmp_path: Path) -> None:
    store, artifacts = make_store(tmp_path)
    for identifier in ("org:one", "org:two"):
        request = admitted_identity(artifacts, identifier)
        assert store.register(request, EvidenceAdmission.admit_claim(request))
    assert isinstance(store.resolve("Registered Example SLU"), OrganizationIdentityPending)
    assert isinstance(
        store.resolve("https://registry.example.invalid/records/one"), OrganizationIdentityPending
    )


def test_nonregistry_or_evidence_only_admission_never_registers(tmp_path: Path) -> None:
    store, artifacts = make_store(tmp_path)
    request = admitted_identity(artifacts)
    with pytest.raises(EvidenceAdmissionRequired):
        store.register(request, EvidenceAdmission.admit(request.evidence))
    for authority in (
        SourceAuthority.OFFICIAL_WEB,
        SourceAuthority.USER_SIGNAL,
        SourceAuthority.SUBSCRIBER_SIGNAL,
    ):
        invalid = replace(request, evidence=replace(request.evidence, authority=authority))
        with pytest.raises(OrganizationMaterializationError):
            store.register(invalid, EvidenceAdmission.admit_claim(invalid))
    assert store.get_organization(OrganizationId(request.subject_id)) is None


def test_artifact_and_receipt_integrity_are_checked_again_on_read(tmp_path: Path) -> None:
    store, artifacts = make_store(tmp_path)
    request = admitted_identity(artifacts)
    assert store.register(request, EvidenceAdmission.admit_claim(request))
    with sqlite3.connect(store.path) as connection:
        connection.execute("UPDATE canonical_legal_identities SET canonical_name = 'forged'")
    with pytest.raises(OrganizationMaterializationError, match="integrity"):
        store.get_organization(OrganizationId(request.subject_id))


def test_identity_topology_revalidation_blocks_stale_identity(tmp_path: Path) -> None:
    store, artifacts = make_store(tmp_path)
    request = admitted_identity(artifacts)
    assert store.register(request, EvidenceAdmission.admit_claim(request))
    with sqlite3.connect(tmp_path / "identity-governance.sqlite3") as connection:
        connection.execute("UPDATE identity_subjects SET requires_revalidation = 1")
    assert store.get_organization(OrganizationId(request.subject_id)) is None
    assert isinstance(store.resolve(request.object_or_value), OrganizationIdentityPending)
