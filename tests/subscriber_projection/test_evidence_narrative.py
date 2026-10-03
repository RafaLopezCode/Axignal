from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import (
    ObservationReusePolicy,
    ReusePurpose,
    ReuseTargetScope,
)
from application.subscriber_projection import (
    EvidenceNarrativeKind,
    NarrativeAccessContext,
    NarrativeEvidenceScope,
    NarrativeGraphKind,
    NarrativeGraphMapResolver,
    NarrativeGraphReference,
    NarrativeMaterial,
    NarrativeMaterialContribution,
    NarrativeMaterialMapResolver,
    build_evidence_narrative,
    project_explainable_xignal,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from domain.evidence import Currentness
from domain.evidence.admission import AdmissionRequest, Evidence, EvidenceAdmission, SourceAuthority
from domain.faxt.model import FAXT
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from domain.xignal import XignalEpistemicState, XignalKind
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 9, 30, 19, 0, tzinfo=UTC)


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
    return AuthorizedXeedOrganizationReader(
        _Organizations(Organization(OrganizationId("org:acme"), "ACME"))
    ).read(authorized)


def _faxt() -> FAXT:
    evidence = Evidence(
        id="evidence:web:1",
        source="ACME corporate website",
        source_type="OFFICIAL_WEB",
        reference="https://example.test/company",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=NOW,
        authority=SourceAuthority.OFFICIAL_WEB,
    )
    return FAXT.create(
        faxt_id="faxt:manufactures-pumps",
        subject_id="org:acme",
        predicate="manufactures",
        object_or_value="industrial pumps",
        evidence=evidence,
        decision=EvidenceAdmission.admit_claim(
            AdmissionRequest(
                evidence=evidence,
                subject_id="org:acme",
                predicate="manufactures",
                object_or_value="industrial pumps",
                claim_proposition=evidence.extracted_claim,
            )
        ),
        observed_at=NOW,
        currentness=Currentness.CURRENT,
    )


def _observation(
    *,
    observation_id: str,
    source_ref: str,
    source_type: str,
    artifact_ref: str,
    fingerprint: str,
    authority: ObservationReuseAuthority | None = None,
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id="org:acme",
            source_ref=source_ref,
            source_type=source_type,
            observed_at=NOW,
            content_fingerprint=fingerprint,
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_artifact_ref=artifact_ref,
        reuse_authority=(
            ObservationReuseAuthority(
                rights_status=ObservationRightsStatus.PERMITTED,
                access_status=ObservationAccessStatus.ACCESSIBLE,
                scope=ObservationReuseScope.GLOBAL_PUBLIC,
                provenance_ref="policy:public-test",
                currentness=Currentness.CURRENT,
                applicable_subject_ids=("org:acme",),
                applicable_purposes=(ReusePurpose.CURRENT_STATE.value,),
            )
            if authority is None
            else authority
        ),
    )


def _basis() -> ExplainableBasis:
    return ExplainableBasis(
        basis_id="basis:fr06:1",
        subject_id="org:acme",
        candidate_id="candidate:industrial-pumps",
        semantic_target="CAPABILITY_SIGNAL",
        state_fingerprint="state:fr06",
        contract_fingerprint="contract:fr06",
        evaluated_at=NOW,
        data=(
            BasisDatum(
                datum_id="datum:web",
                observation_id="obs:web",
                source_ref="https://example.test/company",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="ACME manufactures industrial pumps.",
                contribution=BasisContribution.SUPPORTS,
                evidence_ref="evidence:web:1",
                representation_fingerprint="repr:web:v1",
                extraction_fingerprint="extract:web:v1",
            ),
            BasisDatum(
                datum_id="datum:registry",
                observation_id="obs:registry",
                source_ref="registry:acme",
                source_type="PUBLIC_REGISTRY",
                observed_at=NOW,
                excerpt_or_summary="Registry wording does not explicitly mention pump manufacturing.",
                contribution=BasisContribution.CONTRADICTS,
                representation_fingerprint="repr:registry:v1",
                extraction_fingerprint="extract:registry:v1",
            ),
        ),
        interpretation="Pump manufacturing is observed but registry wording is broader.",
        uncertainty="Geographic availability remains unresolved.",
    )


NARRATIVE_POLICY = ObservationReusePolicy("subscriber-evidence-narrative", "1")


def _access_context(
    *,
    tenant_id: str = "tenant:1",
    target_scope: ReuseTargetScope = ReuseTargetScope.TENANT_PRIVATE,
    purpose: ReusePurpose = ReusePurpose.CURRENT_STATE,
) -> NarrativeAccessContext:
    return NarrativeAccessContext(
        subject_id="org:acme",
        xeed_id="xeed:1",
        tenant_id=tenant_id,
        target_scope=target_scope,
        purpose=purpose,
        as_of=NOW,
    )


def _material_resolver() -> NarrativeMaterialMapResolver:
    return NarrativeMaterialMapResolver(
        (
            NarrativeMaterial(
                observation_id="obs:web",
                subject_id="org:acme",
                candidate_id="candidate:industrial-pumps",
                source_ref="https://example.test/company",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="ACME manufactures industrial pumps.",
                contribution=NarrativeMaterialContribution.SUPPORTS,
                representation_fingerprint="repr:web:v1",
                extraction_fingerprint="extract:web:v1",
            ),
            NarrativeMaterial(
                observation_id="obs:registry",
                subject_id="org:acme",
                candidate_id="candidate:industrial-pumps",
                source_ref="registry:acme",
                source_type="PUBLIC_REGISTRY",
                observed_at=NOW,
                excerpt_or_summary="Registry wording does not explicitly mention pump manufacturing.",
                contribution=NarrativeMaterialContribution.CONTRADICTS,
                representation_fingerprint="repr:registry:v1",
                extraction_fingerprint="extract:registry:v1",
            ),
        )
    )


def _graph_resolver() -> NarrativeGraphMapResolver:
    return NarrativeGraphMapResolver(
        (
            NarrativeGraphReference(
                ref="relationship:supply:1",
                kind=NarrativeGraphKind.RELATIONSHIP,
                label="ACME supplies industrial pumps",
                subject_ids=("org:acme", "org:buyer"),
            ),
            NarrativeGraphReference(
                ref="pathx:supply:1",
                kind=NarrativeGraphKind.PATHX,
                label="ACME to buyer supply path",
                subject_ids=("org:acme", "org:buyer"),
            ),
        )
    )


def _runtime(tmp_path: Path):
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    web_ref = artifacts.put_json({"source": "web", "claim": "industrial pumps"})
    registry_ref = artifacts.put_json({"source": "registry", "scope": "manufacturing"})
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    web = _observation(
        observation_id="obs:web",
        source_ref="https://example.test/company",
        source_type="OFFICIAL_WEB",
        artifact_ref=web_ref,
        fingerprint="fingerprint:web",
    )
    registry = _observation(
        observation_id="obs:registry",
        source_ref="registry:acme",
        source_type="PUBLIC_REGISTRY",
        artifact_ref=registry_ref,
        fingerprint="fingerprint:registry",
    )
    assert memory.append(web)
    assert memory.append(registry)
    return artifacts, memory, web, registry


def test_complete_evidence_narrative_resolves_runtime_lineage_and_is_ui_safe(
    tmp_path: Path,
) -> None:
    artifacts, memory, _web, _registry = _runtime(tmp_path)
    basis = _basis()
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:industrial-pumps",
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
        relationship_ref="relationship:supply:1",
        pathx_ref="pathx:supply:1",
        unknowns=("Geographic availability remains UNKNOWN.",),
    )

    narrative = build_evidence_narrative(
        organization_context=_seed(),
        projection=projection,
        basis=basis,
        observation_memory=memory,
        artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        material_resolver=_material_resolver(),
        access_context=_access_context(),
        reuse_policy=NARRATIVE_POLICY,
        graph_resolver=_graph_resolver(),
        canonical_faxts=(_faxt(),),
    )

    assert narrative.focus_step_id == narrative.return_focus_step_id
    assert [step.kind for step in narrative.steps] == [
        EvidenceNarrativeKind.XIGNAL,
        EvidenceNarrativeKind.CLAIM,
        EvidenceNarrativeKind.RELATIONSHIP,
        EvidenceNarrativeKind.PATHX,
        EvidenceNarrativeKind.OBSERVATION,
        EvidenceNarrativeKind.SOURCE,
        EvidenceNarrativeKind.CONTRADICTION,
        EvidenceNarrativeKind.SOURCE,
        EvidenceNarrativeKind.UNKNOWN,
    ]
    source_steps = [step for step in narrative.steps if step.kind is EvidenceNarrativeKind.SOURCE]
    assert all(step.artifact_verified is True for step in source_steps)
    assert source_steps[0].source_ref == "https://example.test/company"
    assert source_steps[0].observed_at == NOW
    assert all(step.evidence_scope is NarrativeEvidenceScope.GLOBAL_PUBLIC for step in source_steps)
    assert narrative.steps[1].currentness == Currentness.CURRENT.value

    rendered = json.dumps(asdict(narrative), default=str, sort_keys=True)
    assert "cas:sha256:" not in rendered
    assert str(tmp_path) not in rendered
    assert "peer_ip" not in rendered
    assert "raw_artifact_ref" not in rendered


def test_evidence_narrative_survives_exact_observation_replay(tmp_path: Path) -> None:
    artifacts, memory, web, registry = _runtime(tmp_path)
    basis = _basis()
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:industrial-pumps",
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
        unknowns=("Geographic availability remains UNKNOWN.",),
    )
    adapter = ContentAddressedArtifactIntegrityAdapter(artifacts)

    before = build_evidence_narrative(
        organization_context=_seed(),
        projection=projection,
        basis=basis,
        observation_memory=memory,
        artifact_integrity=adapter,
        material_resolver=_material_resolver(),
        access_context=_access_context(),
        reuse_policy=NARRATIVE_POLICY,
        canonical_faxts=(_faxt(),),
    )

    assert memory.append(web) is False
    assert memory.append(registry) is False

    after = build_evidence_narrative(
        organization_context=_seed(),
        projection=projection,
        basis=basis,
        observation_memory=memory,
        artifact_integrity=adapter,
        material_resolver=_material_resolver(),
        access_context=_access_context(),
        reuse_policy=NARRATIVE_POLICY,
        canonical_faxts=(_faxt(),),
    )

    assert after == before


def test_narrative_rejects_altered_summary_with_same_ids(tmp_path: Path) -> None:
    artifacts, memory, _web, _registry = _runtime(tmp_path)
    basis = _basis()
    altered = replace(
        basis,
        data=(
            replace(basis.data[0], excerpt_or_summary="ACME is the market leader in pumps."),
            basis.data[1],
        ),
    )
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=altered.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=altered,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
    )
    with pytest.raises(ValueError, match="summary"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=projection,
            basis=altered,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


def test_narrative_rejects_altered_type_or_version_with_same_ids(tmp_path: Path) -> None:
    artifacts, memory, _web, _registry = _runtime(tmp_path)
    basis = _basis()
    altered_type = replace(
        basis,
        data=(replace(basis.data[0], source_type="BLOG"), basis.data[1]),
    )
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=altered_type.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=altered_type,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
    )
    with pytest.raises(ValueError, match="source type"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=projection,
            basis=altered_type,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )

    altered_version = replace(
        basis,
        data=(replace(basis.data[0], representation_fingerprint="repr:web:forged"), basis.data[1]),
    )
    projection2 = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=altered_version.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=altered_version,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
    )
    with pytest.raises(ValueError, match="representation fingerprint"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=projection2,
            basis=altered_version,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


def test_narrative_cannot_omit_material_contradiction(tmp_path: Path) -> None:
    artifacts, memory, _web, _registry = _runtime(tmp_path)
    basis = _basis()
    omitted = replace(basis, data=(basis.data[0],))
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=omitted.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=omitted,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
    )
    with pytest.raises(ValueError, match="omits material contradiction"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=projection,
            basis=omitted,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


def test_narrative_rejects_unresolved_graph_reference(tmp_path: Path) -> None:
    artifacts, memory, _web, _registry = _runtime(tmp_path)
    basis = _basis()
    projection = project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=basis.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Industrial pump manufacturing observed",
        why_attention="Observed supply capability warrants attention.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-v1",
        canonical_faxt=_faxt(),
        relationship_ref="relationship:missing",
    )
    with pytest.raises(ValueError, match="unresolved or unauthorized"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=projection,
            basis=basis,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            graph_resolver=_graph_resolver(),
            canonical_faxts=(_faxt(),),
        )


def _private_authority(
    *,
    owner: str = "tenant:1",
    rights: ObservationRightsStatus = ObservationRightsStatus.PERMITTED,
    scope: ObservationReuseScope = ObservationReuseScope.TENANT_PRIVATE,
    purposes: tuple[str, ...] = (ReusePurpose.CURRENT_STATE.value,),
) -> ObservationReuseAuthority:
    return ObservationReuseAuthority(
        rights_status=rights,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        scope=scope,
        scope_owner_id=owner if scope is ObservationReuseScope.TENANT_PRIVATE else None,
        provenance_ref="policy:private-test",
        currentness=Currentness.CURRENT,
        applicable_subject_ids=("org:acme",),
        applicable_purposes=purposes,
    )


def _private_runtime(tmp_path: Path, authority: ObservationReuseAuthority):
    artifacts = ContentAddressedArtifactStore(tmp_path / "private-artifacts")
    ref = artifacts.put_json({"private": "billing note", "amount": "secret"})
    memory = SqliteObservationMemory(tmp_path / "private-observations.sqlite3")
    private = _observation(
        observation_id="obs:web",
        source_ref="private://tenant-note",
        source_type="PRIVATE_BILLING",
        artifact_ref=ref,
        fingerprint="fingerprint:private",
        authority=authority,
    )
    assert memory.append(private)
    return artifacts, memory


def _private_basis() -> ExplainableBasis:
    basis = _basis()
    return replace(
        basis,
        data=(
            replace(
                basis.data[0],
                source_ref="private://tenant-note",
                source_type="PRIVATE_BILLING",
                excerpt_or_summary="Private tenant billing note.",
                representation_fingerprint="repr:private:v1",
                extraction_fingerprint="extract:private:v1",
            ),
        ),
    )


def _private_material_resolver() -> NarrativeMaterialMapResolver:
    return NarrativeMaterialMapResolver(
        (
            NarrativeMaterial(
                observation_id="obs:web",
                subject_id="org:acme",
                candidate_id="candidate:industrial-pumps",
                source_ref="private://tenant-note",
                source_type="PRIVATE_BILLING",
                observed_at=NOW,
                excerpt_or_summary="Private tenant billing note.",
                contribution=NarrativeMaterialContribution.SUPPORTS,
                representation_fingerprint="repr:private:v1",
                extraction_fingerprint="extract:private:v1",
            ),
        )
    )


def _private_projection(basis: ExplainableBasis):
    return project_explainable_xignal(
        organization_context=_seed(),
        candidate_id=basis.candidate_id,
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.OBSERVED,
        title="Private tenant-supported view",
        why_attention="Private context may inform this tenant-only presentation.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-private-v1",
        canonical_faxt=_faxt(),
    )


def test_private_evidence_from_different_owner_is_rejected_before_material_resolution(
    tmp_path: Path,
) -> None:
    artifacts, memory = _private_runtime(
        tmp_path,
        _private_authority(owner="tenant:other"),
    )
    basis = _private_basis()
    with pytest.raises(ValueError, match="PRIVATE_SCOPE_MISMATCH"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=_private_projection(basis),
            basis=basis,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_private_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


@pytest.mark.parametrize(
    "authority",
    [
        _private_authority(rights=ObservationRightsStatus.PROHIBITED),
        ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.UNKNOWN,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.TENANT_PRIVATE,
            scope_owner_id="tenant:1",
            provenance_ref="policy:private-test",
            currentness=Currentness.CURRENT,
            applicable_subject_ids=("org:acme",),
            applicable_purposes=(ReusePurpose.CURRENT_STATE.value,),
        ),
        ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.PERMITTED,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.RESTRICTED,
            provenance_ref="policy:restricted-test",
            currentness=Currentness.CURRENT,
            applicable_subject_ids=("org:acme",),
            applicable_purposes=(ReusePurpose.CURRENT_STATE.value,),
        ),
    ],
)
def test_prohibited_unknown_or_restricted_private_material_is_rejected(
    tmp_path: Path,
    authority: ObservationReuseAuthority,
) -> None:
    artifacts, memory = _private_runtime(tmp_path, authority)
    basis = _private_basis()
    with pytest.raises(ValueError, match="narrative observation access rejected"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=_private_projection(basis),
            basis=basis,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_private_material_resolver(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


def test_correct_private_owner_gets_explicit_private_projection_without_cas_leak(
    tmp_path: Path,
) -> None:
    artifacts, memory = _private_runtime(tmp_path, _private_authority())
    basis = _private_basis()
    narrative = build_evidence_narrative(
        organization_context=_seed(),
        projection=_private_projection(basis),
        basis=basis,
        observation_memory=memory,
        artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        material_resolver=_private_material_resolver(),
        access_context=_access_context(),
        reuse_policy=NARRATIVE_POLICY,
        canonical_faxts=(_faxt(),),
    )
    evidence_steps = [
        step
        for step in narrative.steps
        if step.kind in (EvidenceNarrativeKind.OBSERVATION, EvidenceNarrativeKind.SOURCE)
    ]
    assert evidence_steps
    assert all(
        step.evidence_scope is NarrativeEvidenceScope.TENANT_PRIVATE for step in evidence_steps
    )
    rendered = json.dumps(asdict(narrative), default=str, sort_keys=True)
    assert "cas:sha256:" not in rendered
    assert "raw_artifact_ref" not in rendered
    assert str(tmp_path) not in rendered


def test_private_evidence_cannot_be_projected_to_global_world(tmp_path: Path) -> None:
    artifacts, memory = _private_runtime(tmp_path, _private_authority())
    basis = _private_basis()
    with pytest.raises(ValueError, match="PRIVATE_SCOPE_GLOBAL_LEAK"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=_private_projection(basis),
            basis=basis,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_private_material_resolver(),
            access_context=_access_context(target_scope=ReuseTargetScope.GLOBAL_WORLD),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )


class _ResolverMustNotReadPrivateMaterial:
    def considered_observation_ids(
        self,
        *,
        subject_id: str,
        candidate_id: str,
    ) -> tuple[str, ...]:
        assert subject_id == "org:acme"
        assert candidate_id == "candidate:industrial-pumps"
        return ("obs:web",)

    def resolve(self, observation_id: str):
        raise AssertionError("material resolver must not run before authorization")


def test_private_material_is_not_resolved_before_owner_authorization(tmp_path: Path) -> None:
    artifacts, memory = _private_runtime(
        tmp_path,
        _private_authority(owner="tenant:other"),
    )
    basis = _private_basis()
    with pytest.raises(ValueError, match="PRIVATE_SCOPE_MISMATCH"):
        build_evidence_narrative(
            organization_context=_seed(),
            projection=_private_projection(basis),
            basis=basis,
            observation_memory=memory,
            artifact_integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
            material_resolver=_ResolverMustNotReadPrivateMaterial(),
            access_context=_access_context(),
            reuse_policy=NARRATIVE_POLICY,
            canonical_faxts=(_faxt(),),
        )
