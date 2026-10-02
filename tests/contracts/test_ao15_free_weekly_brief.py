from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_acquisition.lifecycle_service import AdminBriefLifecycleService
from application.admin_acquisition.projection import project_admin_acquisition
from application.admin_acquisition.public_service import PublicBriefRequestService
from application.admin_acquisition.review_service import AdminBriefReviewService
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_acquisition import (
    BriefReviewState,
    CoverageState,
    NewsletterConsentState,
)
from pipeline.admin_acquisition import AcquisitionStoreConflict, SqliteAdminAcquisitionStore

NOW = datetime(2026, 10, 2, 12, 30, tzinfo=UTC)


def _grant(
    role: AdminRole = AdminRole.FOUNDER,
    *,
    assurance: AdminAssurance = AdminAssurance.STEP_UP,
) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=assurance,
    )


def _submit(store: SqliteAdminAcquisitionStore, *, consent: bool = False):
    service = PublicBriefRequestService(store)
    return service.submit(
        request_id="brief:1",
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="contact@acme.example",
        purpose="Evaluate the observation newsletter.",
        request_notice_version="brief-request-v1",
        newsletter_consent=consent,
        newsletter_notice_version="newsletter-v1" if consent else None,
        now=NOW,
    )


def test_request_and_newsletter_consent_are_separate_states(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    snapshot = _submit(store)
    assert snapshot.review_state is BriefReviewState.REQUESTED
    assert snapshot.coverage_state is CoverageState.UNKNOWN
    assert snapshot.consent_state is NewsletterConsentState.NOT_GRANTED
    assert snapshot.delivery_eligible is False
    assert len(store.events_for_request("brief:1")) == 1


def test_affirmative_consent_is_explicit_and_versioned(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    snapshot = _submit(store, consent=True)
    assert snapshot.consent_state is NewsletterConsentState.GRANTED
    assert snapshot.newsletter_notice_version == "newsletter-v1"
    assert snapshot.consented_at == NOW
    assert snapshot.delivery_eligible is False
    assert len(store.events_for_request("brief:1")) == 2


def test_coverage_acceptance_does_not_replace_consent(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store)
    accepted = AdminBriefReviewService(store).accept(
        grant=_grant(),
        request_id="brief:1",
        subject_reference="organization:acme",
        reason="Resolvable entity with sufficient public coverage.",
        now=NOW + timedelta(seconds=1),
    )
    assert accepted.review_state is BriefReviewState.ACCEPTED
    assert accepted.coverage_state is CoverageState.SUFFICIENT
    assert accepted.consent_state is NewsletterConsentState.NOT_GRANTED
    assert accepted.delivery_eligible is False


def test_delivery_requires_accepted_coverage_and_consent(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store, consent=True)
    accepted = AdminBriefReviewService(store).accept(
        grant=_grant(),
        request_id="brief:1",
        subject_reference="organization:acme",
        reason="Public evidence coverage is sufficient for the pilot.",
        now=NOW + timedelta(seconds=1),
    )
    assert accepted.delivery_eligible is True

    withdrawn = PublicBriefRequestService(store).withdraw_consent(
        request_id="brief:1",
        now=NOW + timedelta(seconds=2),
    )
    assert withdrawn.consent_state is NewsletterConsentState.WITHDRAWN
    assert withdrawn.delivery_eligible is False


def test_admin_projection_excludes_email_and_free_text(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store, consent=True)
    projection = project_admin_acquisition(
        store=store,
        grant=_grant(),
        generated_at=NOW + timedelta(seconds=1),
    )
    assert projection.request_count == 1
    assert projection.pii_visible is False
    assert projection.requests[0].company_domain == "acme.example"
    rendered = repr(projection)
    assert "contact@acme.example" not in rendered
    assert "Evaluate the observation newsletter." not in rendered


def test_acquisition_projection_requires_acquisition_scope(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store)
    with pytest.raises(PermissionError, match="admin:acquisition:read"):
        project_admin_acquisition(
            store=store,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_event_replay_is_idempotent_and_conflict_is_rejected(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    service = PublicBriefRequestService(store)
    first = _submit(store)
    replay = service.submit(
        request_id="brief:1",
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="contact@acme.example",
        purpose="Evaluate the observation newsletter.",
        request_notice_version="brief-request-v1",
        now=NOW,
    )
    assert replay == first
    assert len(store.events_for_request("brief:1")) == 1

    with pytest.raises(AcquisitionStoreConflict):
        service.submit(
            request_id="brief:1",
            company_name="Different Company",
            company_domain="other.example",
            professional_email="other@other.example",
            purpose="Different request.",
            request_notice_version="brief-request-v1",
            now=NOW,
        )


def test_lifecycle_is_monotonic_and_admin_can_block_delivery(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store, consent=True)
    lifecycle = AdminBriefLifecycleService(store)
    blocked = lifecycle.block_delivery(
        grant=_grant(),
        request_id="brief:1",
        reason="Recipient requested permanent suppression.",
        now=NOW + timedelta(seconds=2),
    )
    assert blocked.consent_state is NewsletterConsentState.SUPPRESSED
    assert blocked.delivery_eligible is False

    with pytest.raises(ValueError, match="backward"):
        lifecycle.require_clarification(
            grant=_grant(),
            request_id="brief:1",
            reason="Late operator event.",
            now=NOW + timedelta(seconds=1),
        )


def test_acquisition_mutations_require_step_up_assurance(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    _submit(store, consent=True)
    with pytest.raises(PermissionError, match="STEP_UP"):
        AdminBriefReviewService(store).accept(
            grant=_grant(AdminRole.BUSINESS, assurance=AdminAssurance.PRIMARY),
            request_id="brief:1",
            subject_reference="organization:acme",
            reason="Coverage is sufficient.",
            now=NOW + timedelta(seconds=1),
        )
