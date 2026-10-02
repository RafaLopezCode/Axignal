from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_acquisition.public_service import PublicBriefRequestService
from application.admin_acquisition.review_service import AdminBriefReviewService
from application.admin_integrations.service import AdminIntegrationService
from application.admin_weekly_brief import (
    InterpretationDraft,
    MaterialObservationCandidate,
    append_correction,
    apply_interpretation_draft,
    approve_issue,
    compose_issue,
    deliver_issue,
    reconstruct_issue,
)
from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
    ObservedField,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
    IntegrationHealth,
    IntegrationHealthState,
)
from domain.admin_weekly_brief import WeeklyBriefIssueKind
from domain.evidence.epistemics import Currentness
from pipeline.admin_acquisition import SqliteAdminAcquisitionStore
from pipeline.admin_weekly_brief import SqliteWeeklyBriefStore, WeeklyBriefStoreConflict
from pipeline.observation_memory import SqliteObservationMemory

NOW = datetime(2026, 10, 2, 15, 0, tzinfo=UTC)
POLICY = TemporalCurrentnessPolicy(
    policy_id="weekly-currentness",
    version="v1",
    stale_after=timedelta(days=14),
    historical_after=timedelta(days=90),
)


def _grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("session:founder"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _eligible_request(store: SqliteAdminAcquisitionStore, request_id: str = "brief:1") -> None:
    PublicBriefRequestService(store).submit(
        request_id=request_id,
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="contact@acme.example",
        purpose="Observe material public changes.",
        request_notice_version="brief-request-v1",
        newsletter_consent=True,
        newsletter_notice_version="newsletter-v1",
        now=NOW - timedelta(days=1),
    )
    AdminBriefReviewService(store).accept(
        grant=_grant(),
        request_id=request_id,
        subject_reference="organization:acme",
        reason="Resolvable entity with sufficient public evidence.",
        now=NOW - timedelta(hours=23),
    )


def _observation(
    observation_id: str,
    *,
    fingerprint: str | None = None,
    observed_at: datetime = NOW - timedelta(days=1),
    currentness: Currentness = Currentness.CURRENT,
    value: str | None = None,
) -> GovernedObservation:
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=observation_id,
            subject_id="organization:acme",
            source_ref=f"https://example.com/{observation_id}",
            source_type="PUBLIC_WEB",
            observed_at=observed_at,
            content_fingerprint=fingerprint or f"sha256:{observation_id}",
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_content=f"raw {observation_id}",
        fields=(ObservedField("public.change", value or observation_id),),
        reuse_authority=ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.PERMITTED,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.GLOBAL_PUBLIC,
            currentness=currentness,
            applicable_subject_ids=("organization:acme",),
            applicable_purposes=("weekly-brief",),
        ),
    )


def _candidate(observation_id: str) -> MaterialObservationCandidate:
    return MaterialObservationCandidate(
        observation_id=observation_id,
        why_may_matter="This may alter the external context worth reviewing.",
        unknowns=("Commercial impact remains UNKNOWN.",),
    )


def _stores(tmp_path: Path):
    acquisition = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    brief = SqliteWeeklyBriefStore(tmp_path / "weekly-brief.sqlite3")
    observations = SqliteObservationMemory(tmp_path / "observation.sqlite3")
    _eligible_request(acquisition)
    return acquisition, brief, observations


def test_composition_caps_three_and_deduplicates_evidence(tmp_path: Path) -> None:
    acquisition, brief, observations = _stores(tmp_path)
    for idx in range(1, 5):
        observations.append(_observation(f"obs:{idx}"))
    observations.append(_observation("obs:dup", fingerprint="sha256:obs:1"))

    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:1",
        issue_version="2026-W40-v1",
        candidates=(*(_candidate(f"obs:{idx}") for idx in range(1, 5)), _candidate("obs:dup")),
        currentness_policy=POLICY,
        now=NOW,
    )

    assert issue.kind is WeeklyBriefIssueKind.MATERIAL_CHANGES
    assert len(issue.items) == 3
    assert [item.observation_id for item in issue.items] == ["obs:1", "obs:2", "obs:3"]


def test_stale_unknown_or_unbacked_candidates_create_no_material_change_not_filler(
    tmp_path: Path,
) -> None:
    acquisition, brief, observations = _stores(tmp_path)
    observations.append(_observation("obs:stale", observed_at=NOW - timedelta(days=30)))
    observations.append(_observation("obs:unknown", currentness=Currentness.UNKNOWN))

    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:none",
        issue_version="2026-W40-v1",
        candidates=(
            _candidate("obs:stale"),
            _candidate("obs:unknown"),
            _candidate("obs:not-present"),
        ),
        currentness_policy=POLICY,
        now=NOW,
    )

    assert issue.kind is WeeklyBriefIssueKind.NO_MATERIAL_CHANGE
    assert issue.items == ()


def test_restricted_or_nonreusable_evidence_is_not_leaked_into_free_brief(
    tmp_path: Path,
) -> None:
    acquisition, brief, observations = _stores(tmp_path)
    restricted = _observation("obs:restricted")
    restricted = GovernedObservation(
        record=restricted.record,
        raw_content=restricted.raw_content,
        fields=restricted.fields,
        reuse_authority=ObservationReuseAuthority(
            rights_status=ObservationRightsStatus.PERMITTED,
            access_status=ObservationAccessStatus.ACCESSIBLE,
            scope=ObservationReuseScope.RESTRICTED,
            currentness=Currentness.CURRENT,
            applicable_subject_ids=("organization:acme",),
            applicable_purposes=("weekly-brief",),
        ),
    )
    observations.append(restricted)

    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:restricted",
        issue_version="2026-W40-v1",
        candidates=(_candidate("obs:restricted"),),
        currentness_policy=POLICY,
        now=NOW,
    )

    assert issue.kind is WeeklyBriefIssueKind.NO_MATERIAL_CHANGE
    assert issue.items == ()


def test_model_draft_cannot_add_or_rewrite_observed_development(tmp_path: Path) -> None:
    acquisition, brief, observations = _stores(tmp_path)
    observations.append(_observation("obs:1", value="new distributor page"))

    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:model",
        issue_version="2026-W40-v1",
        candidates=(_candidate("obs:1"),),
        currentness_policy=POLICY,
        now=NOW,
    )
    original_summary = issue.items[0].observation_summary

    drafted = apply_interpretation_draft(
        issue,
        (InterpretationDraft("obs:1", "This may warrant a channel review."),),
    )
    assert drafted.items[0].observation_summary == original_summary
    assert drafted.items[0].source_ref == issue.items[0].source_ref
    assert drafted.items[0].observed_at == issue.items[0].observed_at
    assert drafted.evidence_fingerprint == issue.evidence_fingerprint

    with pytest.raises(ValueError, match="cannot introduce evidence"):
        apply_interpretation_draft(
            issue,
            (InterpretationDraft("obs:invented", "A model invented a development."),),
        )

    frozen = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:model-frozen",
        issue_version="2026-W40-v1",
        candidates=(_candidate("obs:1"),),
        currentness_policy=POLICY,
        now=NOW,
        drafts=(InterpretationDraft("obs:1", "Drafted before the immutable snapshot."),),
    )
    assert frozen.items[0].why_may_matter == "Drafted before the immutable snapshot."
    assert brief.get_issue("issue:model-frozen") == frozen
    assert frozen.evidence_fingerprint == issue.evidence_fingerprint


class _Registry:
    def __init__(self) -> None:
        self.definition = IntegrationDefinition(
            integration_id="weekly-email",
            provider="test-mail",
            purpose="Weekly brief delivery",
            owner="AXIGNAL",
            environment=IntegrationEnvironment.PRODUCTION,
            enabled=True,
            credential=CredentialLifecycle(
                reference="secret://weekly-email/api",
                state=CredentialState.CONFIGURED,
            ),
            scopes=("email:send",),
            direction=IntegrationDirection.OUTBOUND,
            authority_boundary="Delivery only; never economic truth.",
            webhook_capable=False,
            webhook_endpoint=None,
            rate_limit_posture=None,
            health_freshness_seconds=3600,
        )
        self.health = IntegrationHealth(
            integration_id="weekly-email",
            state=IntegrationHealthState.HEALTHY,
            observed_at=NOW - timedelta(minutes=5),
            last_success_at=NOW - timedelta(minutes=5),
        )

    def all_definitions(self):
        return (self.definition,)

    def latest_health(self, integration_id: str, *, as_of: datetime):
        return self.health if integration_id == self.definition.integration_id else None


class _Audit:
    def append(self, record) -> bool:
        return True


class _Resolver:
    def is_resolvable(self, *, reference: str, environment: IntegrationEnvironment) -> bool:
        return reference == "secret://weekly-email/api"


class _Provider:
    def __init__(self) -> None:
        self.calls = 0

    def send(self, *, recipient_email: str, issue, delivery_id: str) -> str:
        self.calls += 1
        assert delivery_id.startswith("delivery:")
        assert recipient_email == "contact@acme.example"
        return "message:1"


def _issue_ready(tmp_path: Path):
    acquisition, brief, observations = _stores(tmp_path)
    observations.append(_observation("obs:1"))
    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:delivery",
        issue_version="2026-W40-v1",
        candidates=(_candidate("obs:1"),),
        currentness_policy=POLICY,
        now=NOW,
    )
    return acquisition, brief, issue


def test_delivery_requires_human_approval_and_rechecks_consent(tmp_path: Path) -> None:
    acquisition, brief, issue = _issue_ready(tmp_path)
    integration = AdminIntegrationService(_Registry(), _Audit())
    provider = _Provider()

    with pytest.raises(PermissionError, match="human approval"):
        deliver_issue(
            store=brief,
            acquisition_store=acquisition,
            integration_service=integration,
            credential_resolver=_Resolver(),
            provider=provider,
            issue_id=issue.issue_id,
            delivery_id="delivery:no-approval",
            integration_id="weekly-email",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW + timedelta(minutes=1),
        )
    assert provider.calls == 0

    approve_issue(store=brief, grant=_grant(), issue_id=issue.issue_id, now=NOW)
    PublicBriefRequestService(acquisition).withdraw_consent(
        request_id="brief:1",
        now=NOW + timedelta(minutes=1),
    )
    with pytest.raises(PermissionError, match="no longer delivery eligible"):
        deliver_issue(
            store=brief,
            acquisition_store=acquisition,
            integration_service=integration,
            credential_resolver=_Resolver(),
            provider=provider,
            issue_id=issue.issue_id,
            delivery_id="delivery:withdrawn",
            integration_id="weekly-email",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW + timedelta(minutes=2),
        )
    assert provider.calls == 0


def test_sent_issue_reconstructs_and_correction_is_append_only(tmp_path: Path) -> None:
    acquisition, brief, issue = _issue_ready(tmp_path)
    approve_issue(store=brief, grant=_grant(), issue_id=issue.issue_id, now=NOW)
    provider = _Provider()

    delivery = deliver_issue(
        store=brief,
        acquisition_store=acquisition,
        integration_service=AdminIntegrationService(_Registry(), _Audit()),
        credential_resolver=_Resolver(),
        provider=provider,
        issue_id=issue.issue_id,
        delivery_id="delivery:1",
        integration_id="weekly-email",
        environment=IntegrationEnvironment.PRODUCTION,
        now=NOW + timedelta(minutes=1),
    )
    correction = append_correction(
        store=brief,
        grant=_grant(),
        correction_id="correction:1",
        issue_id=issue.issue_id,
        reason="Source wording was later clarified.",
        note="Interpretive note corrected; original sent issue remains immutable.",
        now=NOW + timedelta(minutes=2),
    )
    reconstructed = reconstruct_issue(store=brief, issue_id=issue.issue_id)

    assert provider.calls == 1
    assert reconstructed.issue == issue
    assert reconstructed.deliveries == (delivery,)
    assert reconstructed.corrections == (correction,)
    assert brief.get_issue(issue.issue_id) == issue

    replay = deliver_issue(
        store=brief,
        acquisition_store=acquisition,
        integration_service=AdminIntegrationService(_Registry(), _Audit()),
        credential_resolver=_Resolver(),
        provider=provider,
        issue_id=issue.issue_id,
        delivery_id="delivery:1",
        integration_id="weekly-email",
        environment=IntegrationEnvironment.PRODUCTION,
        now=NOW + timedelta(minutes=3),
    )
    assert replay == delivery
    assert provider.calls == 1


def test_store_replay_is_idempotent_and_conflicting_issue_is_rejected(tmp_path: Path) -> None:
    acquisition, brief, observations = _stores(tmp_path)
    observations.append(_observation("obs:1"))
    issue = compose_issue(
        store=brief,
        acquisition_store=acquisition,
        observation_memory=observations,
        request_id="brief:1",
        issue_id="issue:replay",
        issue_version="2026-W40-v1",
        candidates=(_candidate("obs:1"),),
        currentness_policy=POLICY,
        now=NOW,
    )
    assert brief.put_issue(issue) is False

    altered = apply_interpretation_draft(
        issue,
        (InterpretationDraft("obs:1", "Different interpretation."),),
    )
    with pytest.raises(WeeklyBriefStoreConflict):
        brief.put_issue(altered)
