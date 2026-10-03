from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.observation_memory import GovernedObservation
from application.subscriber_projection import (
    EvidenceNarrativeKind,
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
            ),
            BasisDatum(
                datum_id="datum:registry",
                observation_id="obs:registry",
                source_ref="registry:acme",
                source_type="PUBLIC_REGISTRY",
                observed_at=NOW,
                excerpt_or_summary="Registry wording does not explicitly mention pump manufacturing.",
                contribution=BasisContribution.CONTRADICTS,
            ),
        ),
        interpretation="Pump manufacturing is observed but registry wording is broader.",
        uncertainty="Geographic availability remains unresolved.",
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
        canonical_faxts=(_faxt(),),
    )

    assert after == before
