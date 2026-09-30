from datetime import UTC, datetime

from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.subscriber_projection import (
    EvidenceNarrative,
    EvidenceNarrativeKind,
    EvidenceNarrativeStep,
    project_explainable_xignal,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination import (
    FirstMapReadinessDisposition,
    FirstMapReadinessPolicy,
    FirstMapReadinessReason,
    apply_readiness_decision,
    evaluate_first_map_readiness,
    plant_xeed_runtime,
)
from domain.evidence import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed import Xeed, XeedGerminationStatus
from domain.xignal import XignalEpistemicState, XignalKind
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 9, 30, 20, 0, tzinfo=UTC)


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


def _projection(*, state: XignalEpistemicState = XignalEpistemicState.POTENTIAL):
    basis = ExplainableBasis(
        basis_id=f"basis:{state.value.lower()}",
        subject_id="org:acme",
        candidate_id="candidate:first-map",
        semantic_target="FIRST_MAP_SIGNAL",
        state_fingerprint="state:1",
        contract_fingerprint="contract:1",
        evaluated_at=NOW,
        data=(
            BasisDatum(
                datum_id="datum:1",
                observation_id="obs:1",
                source_ref="https://example.test/company",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="ACME manufactures industrial pumps.",
                contribution=BasisContribution.SUPPORTS,
            ),
        ),
        interpretation="Industrial-pump supply is economically relevant.",
        uncertainty="Geographic reach remains unresolved.",
    )
    unknowns = (
        ("Current economic meaning is still unresolved.",)
        if state is XignalEpistemicState.UNKNOWN
        else ("Geographic reach remains UNKNOWN.",)
    )
    return project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:first-map",
        kind=XignalKind.SUPPLY,
        epistemic_state=state,
        title="Industrial pump supply",
        why_attention="This supply capability warrants attention.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-v1",
        currentness=Currentness.UNKNOWN,
        unknowns=unknowns,
    )


def _narrative(
    xignal_id: str,
    *,
    grounded: bool = True,
    contradiction: bool = False,
) -> EvidenceNarrative:
    root = f"narrative:xignal:{xignal_id}"
    steps = [
        EvidenceNarrativeStep(
            step_id=root,
            kind=EvidenceNarrativeKind.XIGNAL,
            label="This supply capability warrants attention.",
            parent_step_id=None,
        )
    ]
    if grounded:
        steps.append(
            EvidenceNarrativeStep(
                step_id="narrative:observation:1",
                kind=EvidenceNarrativeKind.OBSERVATION,
                label="ACME manufactures industrial pumps.",
                parent_step_id=root,
                observed_at=NOW,
                artifact_verified=True,
            )
        )
    if contradiction:
        steps.append(
            EvidenceNarrativeStep(
                step_id="narrative:contradiction:1",
                kind=EvidenceNarrativeKind.CONTRADICTION,
                label="Registry wording is broader than the website claim.",
                parent_step_id=root,
                observed_at=NOW,
                artifact_verified=True,
            )
        )
    return EvidenceNarrative(
        xignal_id=xignal_id,
        focus_step_id=root,
        return_focus_step_id=root,
        steps=tuple(steps),
    )


def _state_with_observation(*, projection=None):
    state = plant_xeed_runtime(
        seed=_seed(),
        initiated_by="principal:1",
        created_at=NOW,
    )
    state.transition(
        XeedGerminationStatus.RESOLVING,
        occurred_at=NOW,
        reason_code="TEST_RESOLUTION",
    )
    state.transition(
        XeedGerminationStatus.OBSERVING,
        occurred_at=NOW,
        reason_code="TEST_OBSERVATION",
    )
    state.note_observation(observed_at=NOW)
    state.transition(
        XeedGerminationStatus.PARTIAL_READY,
        occurred_at=NOW,
        reason_code="TEST_PARTIAL",
    )
    if projection is not None:
        state.note_first_xignal(projection.xignal.xignal_id)
        state.transition(
            XeedGerminationStatus.FIRST_XIGNAL_READY,
            occurred_at=NOW,
            reason_code="TEST_FIRST_XIGNAL",
        )
    return state


def _policy() -> FirstMapReadinessPolicy:
    return FirstMapReadinessPolicy(
        policy_id="first-map-readiness",
        version="1",
    )


def test_empty_world_is_insufficient_evidence_without_fake_promotion_decision() -> None:
    state = plant_xeed_runtime(seed=_seed(), initiated_by="principal:1", created_at=NOW)

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=None,
        narrative=None,
    )

    assert assessment.disposition is FirstMapReadinessDisposition.INSUFFICIENT_EVIDENCE
    assert assessment.decision is None
    assert assessment.reason_codes == (FirstMapReadinessReason.NO_OBSERVATIONS,)


def test_observed_but_no_xignal_is_honest_sparse_map() -> None:
    state = _state_with_observation()

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=None,
        narrative=None,
    )

    assert assessment.disposition is FirstMapReadinessDisposition.SPARSE_MAP
    assert assessment.decision is None
    assert assessment.reason_codes == (FirstMapReadinessReason.FIRST_XIGNAL_MISSING,)


def test_first_xignal_without_narrative_is_useful_partial_not_ready() -> None:
    projection = _projection()
    state = _state_with_observation(projection=projection)

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=projection,
        narrative=None,
    )

    assert assessment.disposition is FirstMapReadinessDisposition.PARTIAL_MAP
    assert assessment.decision is not None
    assert assessment.decision.ready is False
    assert assessment.reason_codes == (FirstMapReadinessReason.EVIDENCE_NARRATIVE_MISSING,)


def test_one_grounded_explainable_potential_xignal_is_enough_for_first_map_ready() -> None:
    projection = _projection(state=XignalEpistemicState.POTENTIAL)
    state = _state_with_observation(projection=projection)

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=projection,
        narrative=_narrative(projection.xignal.xignal_id),
    )

    assert assessment.disposition is FirstMapReadinessDisposition.FIRST_MAP_READY
    assert assessment.decision is not None
    assert assessment.decision.ready is True
    assert assessment.reason_codes[:2] == (
        FirstMapReadinessReason.READY_EXPLAINABLE_XIGNAL,
        FirstMapReadinessReason.VERIFIED_RUNTIME_LINEAGE_PRESENT,
    )

    apply_readiness_decision(
        seed=_seed(),
        state=state,
        decision=assessment.decision,
        occurred_at=NOW,
    )
    assert state.status is XeedGerminationStatus.LIVE


def test_unknown_only_xignal_does_not_make_first_map_ready() -> None:
    projection = _projection(state=XignalEpistemicState.UNKNOWN)
    state = _state_with_observation(projection=projection)

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=projection,
        narrative=_narrative(projection.xignal.xignal_id),
    )

    assert assessment.disposition is FirstMapReadinessDisposition.PARTIAL_MAP
    assert assessment.decision is not None
    assert assessment.decision.ready is False
    assert FirstMapReadinessReason.XIGNAL_IS_UNKNOWN in assessment.reason_codes


def test_explicit_contradiction_does_not_block_ready_map() -> None:
    projection = _projection()
    state = _state_with_observation(projection=projection)

    assessment = evaluate_first_map_readiness(
        seed=_seed(),
        state=state,
        policy=_policy(),
        projection=projection,
        narrative=_narrative(projection.xignal.xignal_id, contradiction=True),
    )

    assert assessment.disposition is FirstMapReadinessDisposition.FIRST_MAP_READY
    assert FirstMapReadinessReason.EXPLICIT_CONTRADICTIONS_PRESERVED in assessment.reason_codes
    assert FirstMapReadinessReason.EXPLICIT_UNKNOWNS_PRESERVED in assessment.reason_codes


def test_node_count_is_not_a_readiness_policy_or_assessment_dimension() -> None:
    policy_fields = FirstMapReadinessPolicy.__dataclass_fields__
    assessment_fields = FirstMapReadinessDisposition.__members__

    assert "node_count" not in policy_fields
    assert "MIN_NODE_COUNT" not in assessment_fields
