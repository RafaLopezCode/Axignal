from datetime import UTC, datetime

import pytest

from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.prime_execution import PrimeExecutionTrace
from application.subscriber_projection import (
    EvidenceNarrative,
    EvidenceNarrativeKind,
    EvidenceNarrativeStep,
    project_explainable_xignal,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination import (
    BootstrapDimensionGap,
    BootstrapDisposition,
    BootstrapPlan,
    apply_bootstrap_plan,
    apply_first_xignal,
    apply_prime_trace,
    apply_readiness_decision,
    begin_resolution,
    mark_runtime_blocked,
    mark_runtime_failed,
    plant_xeed_runtime,
)
from domain.evidence import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed import Xeed, XeedGerminationError, XeedGerminationStatus
from domain.xignal import XignalEpistemicState, XignalKind
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 9, 30, 19, 30, tzinfo=UTC)


class _Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


class _LearningMemory:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> bool:
        self.events.append(event)
        return True


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


def _bootstrap(disposition: BootstrapDisposition) -> BootstrapPlan:
    missing = ("document.home.visible_text",)
    gaps = (BootstrapDimensionGap("market-mode", missing),)
    return BootstrapPlan(
        xeed_id="xeed:1",
        subject_id="org:acme",
        policy_id="bootstrap",
        policy_version="1",
        state_fingerprint="state:0",
        disposition=disposition,
        reused_observation_count=0,
        available_state_fields=frozenset(),
        missing_requirements=missing,
        dimension_gaps=gaps,
        source_candidates=(),
        prime_plan=None,
        plan_fingerprint=f"plan:{disposition.value}",
    )


def _prime_trace(*, budget_stop_reason: str | None = None) -> PrimeExecutionTrace:
    return PrimeExecutionTrace(
        trace_id="prime-trace:1",
        subject_id="org:acme",
        xeed_id="xeed:1",
        source_request_id="request:1",
        source_observation_fingerprint="obs-fingerprint:1",
        source_artifact_ref="cas:sha256:" + "a" * 64,
        representation_id="representation:1",
        representation_fingerprint="representation-fingerprint:1",
        rich_state_fingerprint="rich-state:1",
        semantic_extraction_id=None,
        semantic_result_fingerprint=None,
        prime_plan=None,
        budget_stop_reason=budget_stop_reason,
        learning_event_ids=("learn:1",),
    )


def _xignal():
    basis = ExplainableBasis(
        basis_id="basis:first-xignal",
        subject_id="org:acme",
        candidate_id="candidate:first",
        semantic_target="FIRST_SIGNAL",
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
        interpretation="Industrial pump supply is economically relevant.",
        uncertainty="Geographic availability is unresolved.",
    )
    return project_explainable_xignal(
        organization_context=_seed(),
        candidate_id="candidate:first",
        kind=XignalKind.SUPPLY,
        epistemic_state=XignalEpistemicState.POTENTIAL,
        title="Industrial pump supply may be relevant",
        why_attention="Observed product semantics warrant attention.",
        basis=basis,
        emitted_at=NOW,
        policy_version="xignal-v1",
        currentness=Currentness.UNKNOWN,
        unknowns=("Geographic availability is UNKNOWN.",),
    )


def _narrative(xignal_id: str, *, verified: bool = True) -> EvidenceNarrative:
    root = f"narrative:xignal:{xignal_id}"
    return EvidenceNarrative(
        xignal_id=xignal_id,
        focus_step_id=root,
        return_focus_step_id=root,
        steps=(
            EvidenceNarrativeStep(
                step_id=root,
                kind=EvidenceNarrativeKind.XIGNAL,
                label="Observed product semantics warrant attention.",
                parent_step_id=None,
            ),
            EvidenceNarrativeStep(
                step_id="narrative:observation:1",
                kind=EvidenceNarrativeKind.OBSERVATION,
                label="ACME manufactures industrial pumps.",
                parent_step_id=root,
                observed_at=NOW,
                artifact_verified=verified,
            ),
        ),
    )


def _readiness(state, *, ready: bool, reasons: tuple[str, ...]):
    from application.xeed_germination import FirstXeedReadinessDecision

    assert state.first_xignal_id is not None
    return FirstXeedReadinessDecision(
        xeed_id=state.xeed_id,
        first_xignal_id=state.first_xignal_id,
        observation_depth=state.observation_depth,
        lifecycle_revision=len(state.transitions),
        ready=ready,
        policy_id="first-map-readiness",
        policy_version="future-fr08-v1",
        reason_codes=reasons,
    )


def test_authorized_xeed_can_traverse_first_runtime_to_live() -> None:
    seed = _seed()
    state = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    assert state.status is XeedGerminationStatus.PLANTED

    begin_resolution(seed=seed, state=state, occurred_at=NOW)
    assert state.status is XeedGerminationStatus.RESOLVING

    apply_bootstrap_plan(
        seed=seed,
        state=state,
        plan=_bootstrap(BootstrapDisposition.ADAPTIVE_RESEARCH),
        occurred_at=NOW,
        learning_memory=_LearningMemory(),
        execution_id="run:first-xeed",
        code_sha="abc123",
    )
    assert state.status is XeedGerminationStatus.OBSERVING

    apply_prime_trace(seed=seed, state=state, trace=_prime_trace(), occurred_at=NOW)
    assert state.status is XeedGerminationStatus.PARTIAL_READY
    assert state.observation_depth == 1

    projection = _xignal()
    apply_first_xignal(seed=seed, state=state, projection=projection, occurred_at=NOW)
    assert state.status is XeedGerminationStatus.FIRST_XIGNAL_READY
    assert state.first_xignal_id == projection.xignal.xignal_id

    decision = _readiness(
        state,
        ready=True,
        reasons=("MAP_READINESS_SATISFIED",),
    )

    apply_readiness_decision(seed=seed, state=state, decision=decision, occurred_at=NOW)
    assert state.status is XeedGerminationStatus.LIVE
    assert state.is_live is True
    assert "DONE" not in XeedGerminationStatus.__members__


def test_partial_ready_is_valid_and_can_later_recover_to_live() -> None:
    seed = _seed()
    state = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    begin_resolution(seed=seed, state=state, occurred_at=NOW)
    apply_bootstrap_plan(
        seed=seed,
        state=state,
        plan=_bootstrap(BootstrapDisposition.ADAPTIVE_RESEARCH),
        occurred_at=NOW,
        learning_memory=_LearningMemory(),
        execution_id="run:first-xeed",
        code_sha="abc123",
    )
    apply_prime_trace(
        seed=seed,
        state=state,
        trace=_prime_trace(budget_stop_reason="LOOP_LIMIT_REACHED"),
        occurred_at=NOW,
    )
    projection = _xignal()
    apply_first_xignal(seed=seed, state=state, projection=projection, occurred_at=NOW)

    not_ready = _readiness(
        state,
        ready=False,
        reasons=("EVIDENCE_NARRATIVE_MISSING",),
    )
    apply_readiness_decision(seed=seed, state=state, decision=not_ready, occurred_at=NOW)
    assert state.status is XeedGerminationStatus.PARTIAL_READY

    ready = _readiness(
        state,
        ready=True,
        reasons=("MAP_READINESS_SATISFIED",),
    )
    apply_readiness_decision(seed=seed, state=state, decision=ready, occurred_at=NOW)
    assert state.status is XeedGerminationStatus.LIVE


@pytest.mark.parametrize(
    "disposition",
    (BootstrapDisposition.RETAIN_UNKNOWN, BootstrapDisposition.DEFER),
)
def test_insufficient_evidence_is_honest_non_failure(
    disposition: BootstrapDisposition,
) -> None:
    seed = _seed()
    state = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    begin_resolution(seed=seed, state=state, occurred_at=NOW)
    apply_bootstrap_plan(
        seed=seed,
        state=state,
        plan=_bootstrap(disposition),
        occurred_at=NOW,
        learning_memory=_LearningMemory(),
        execution_id="run:first-xeed",
        code_sha="abc123",
    )

    assert state.status is XeedGerminationStatus.INSUFFICIENT_EVIDENCE
    assert state.status is not XeedGerminationStatus.FAILED
    assert state.first_xignal_id is None


def test_blocked_and_failed_are_explicit_runtime_states() -> None:
    seed = _seed()
    blocked = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    begin_resolution(seed=seed, state=blocked, occurred_at=NOW)
    apply_bootstrap_plan(
        seed=seed,
        state=blocked,
        plan=_bootstrap(BootstrapDisposition.BLOCKED_BY_BUDGET_OR_RIGHTS),
        occurred_at=NOW,
        learning_memory=_LearningMemory(),
        execution_id="run:first-xeed",
        code_sha="abc123",
    )
    assert blocked.status is XeedGerminationStatus.BLOCKED

    failed = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    mark_runtime_failed(
        seed=seed,
        state=failed,
        occurred_at=NOW,
        reason_code="IDENTITY_RESOLUTION_FAILED",
    )
    assert failed.status is XeedGerminationStatus.FAILED

    retry = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    mark_runtime_blocked(
        seed=seed,
        state=retry,
        occurred_at=NOW,
        reason_code="RIGHTS_UNAVAILABLE",
    )
    assert retry.status is XeedGerminationStatus.BLOCKED


def test_planted_xeed_cannot_jump_directly_to_live() -> None:
    state = plant_xeed_runtime(seed=_seed(), initiated_by="principal:1", created_at=NOW)

    with pytest.raises(XeedGerminationError, match="illegal Xeed germination transition"):
        state.transition(
            XeedGerminationStatus.LIVE,
            occurred_at=NOW,
            reason_code="FAKE_PROGRESS",
        )


def test_stale_readiness_decision_cannot_promote_changed_lifecycle() -> None:
    seed = _seed()
    state = plant_xeed_runtime(seed=seed, initiated_by="principal:1", created_at=NOW)
    begin_resolution(seed=seed, state=state, occurred_at=NOW)
    apply_bootstrap_plan(
        seed=seed,
        state=state,
        plan=_bootstrap(BootstrapDisposition.ADAPTIVE_RESEARCH),
        occurred_at=NOW,
        learning_memory=_LearningMemory(),
        execution_id="run:first-xeed",
        code_sha="abc123",
    )
    apply_prime_trace(seed=seed, state=state, trace=_prime_trace(), occurred_at=NOW)
    projection = _xignal()
    apply_first_xignal(seed=seed, state=state, projection=projection, occurred_at=NOW)
    stale = _readiness(
        state,
        ready=True,
        reasons=("MAP_READINESS_SATISFIED",),
    )

    state.note_observation(observed_at=NOW)

    with pytest.raises(ValueError, match="does not match current Xeed lifecycle state"):
        apply_readiness_decision(
            seed=seed,
            state=state,
            decision=stale,
            occurred_at=NOW,
        )
