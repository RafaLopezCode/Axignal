from datetime import UTC, datetime

import pytest

from application.admin_commercial import (
    AdminCommercialService,
    export_admin_commercial,
    project_admin_commercial,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_commercial import (
    CommercialOrigin,
    ConsentBasis,
    DealStage,
    OpportunityStage,
    ProspectStage,
    TaskState,
)
from pipeline.admin_commercial import SqliteAdminCommercialStore

NOW = datetime(2026, 10, 2, 0, 30, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def test_internal_company_and_observed_org_mapping_are_separate_authorities(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    company = service.create_company(
        grant=_grant(),
        company_id="company:1",
        display_name="Acme Prospect",
        acquisition_source="frontier-brief",
        consent_basis=ConsentBasis.LEGITIMATE_INTEREST,
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="qualified inbound prospect",
    )
    assert company.observed_organization_id is None

    mapped = service.map_observed_organization(
        grant=_grant(),
        company_id="company:1",
        organization_id="org:canonical:77",
        mapping_reason="explicit operator mapping after independent identity review",
        now=NOW,
    )

    assert mapped.observed_organization_id == "org:canonical:77"
    assert mapped.observed_mapping_reason
    audits = store.audits()
    assert audits[-1].origin is CommercialOrigin.PUBLIC_OBSERVATION_REFERENCE
    assert audits[-1].action == "MAP_OBSERVED_ORGANIZATION_ID"


def test_contact_consent_and_origin_are_persisted_and_pii_stays_out_of_projection(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    service.create_company(
        grant=_grant(),
        company_id="company:1",
        display_name="Acme",
        acquisition_source="referral",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="self-submitted",
    )
    service.create_contact(
        grant=_grant(),
        contact_id="contact:1",
        company_id="company:1",
        display_name="Primary contact",
        email="private@example.test",
        phone="+34000000000",
        acquisition_source="referral",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="contact submitted details",
    )

    stored = store.contacts()[0]
    assert stored.email == "private@example.test"
    projection = project_admin_commercial(store=store, grant=_grant(), generated_at=NOW)
    assert projection.contact_count == 1
    assert projection.pii_visible is False
    assert not hasattr(projection.companies[0], "email")

    exported = export_admin_commercial(store=store, grant=_grant(), generated_at=NOW)
    assert exported["piiIncluded"] is False
    assert "private@example.test" not in str(exported)


def test_opportunity_deal_note_task_are_axignal_commercial_state_only(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    service.create_company(
        grant=_grant(),
        company_id="company:1",
        display_name="Acme",
        acquisition_source="direct",
        consent_basis=ConsentBasis.LEGITIMATE_INTEREST,
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="prospecting",
    )
    service.create_opportunity(
        grant=_grant(),
        opportunity_id="opp:1",
        company_id="company:1",
        title="AXIGNAL subscription",
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="commercial qualification",
    )
    service.set_opportunity_stage(
        grant=_grant(),
        opportunity_id="opp:1",
        stage=OpportunityStage.PROPOSAL,
        now=NOW,
        reason="proposal sent",
    )
    service.create_deal(
        grant=_grant(),
        deal_id="deal:1",
        opportunity_id="opp:1",
        now=NOW,
        reason="proposal accepted for negotiation",
    )
    service.set_deal_stage(
        grant=_grant(),
        deal_id="deal:1",
        stage=DealStage.WON,
        now=NOW,
        reason="subscription agreed",
        account_id="account:future-ao09:1",
    )
    service.add_note(
        grant=_grant(),
        note_id="note:1",
        company_id="company:1",
        body="Asked about agency portfolio pricing.",
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="commercial conversation",
    )
    service.add_task(
        grant=_grant(),
        task_id="task:1",
        company_id="company:1",
        title="Follow up on pricing",
        due_at=None,
        now=NOW,
        reason="commercial follow-up",
    )
    service.set_task_state(
        grant=_grant(),
        task_id="task:1",
        state=TaskState.DONE,
        now=NOW,
        reason="follow-up completed",
    )

    projection = project_admin_commercial(store=store, grant=_grant(), generated_at=NOW)
    assert projection.company_count == 1
    assert projection.opportunity_count == 1
    assert projection.deal_count == 1
    assert projection.note_count == 1
    assert projection.open_task_count == 0
    assert store.deals()[0].stage is DealStage.WON
    assert store.deals()[0].account_id == "account:future-ao09:1"
    assert store.tasks()[0].state is TaskState.DONE
    assert projection.companies[0].opportunity_count == 1


def test_support_customer_read_does_not_gain_commercial_pipeline_or_note_visibility(
    tmp_path,
) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    founder = _grant()
    service.create_company(
        grant=founder,
        company_id="company:1",
        display_name="Acme",
        acquisition_source="direct",
        consent_basis=ConsentBasis.UNKNOWN,
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="prospect",
    )
    service.create_opportunity(
        grant=founder,
        opportunity_id="opp:1",
        company_id="company:1",
        title="Private opportunity",
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="private commercial state",
    )
    service.add_note(
        grant=founder,
        note_id="note:1",
        company_id="company:1",
        body="Private negotiation note.",
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="commercial note",
    )

    support = project_admin_commercial(
        store=store, grant=_grant(AdminRole.SUPPORT), generated_at=NOW
    )
    assert support.company_count == 1
    assert support.opportunity_count == 0
    assert support.note_count == 0
    assert support.origin_counts == ()
    assert support.companies[0].opportunity_count == 0


def test_commercial_write_requires_commercial_scope(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    with pytest.raises(PermissionError, match="admin:commercial:write"):
        service.create_company(
            grant=_grant(AdminRole.SUPPORT),
            company_id="company:1",
            display_name="Acme",
            acquisition_source="direct",
            consent_basis=ConsentBasis.UNKNOWN,
            origin=CommercialOrigin.COMMERCIAL_CLAIM,
            now=NOW,
            reason="should be denied",
        )
    assert store.companies() == ()


def test_account_link_is_reference_only_and_requires_customer_write(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    founder = _grant()
    service.create_company(
        grant=founder,
        company_id="company:1",
        display_name="Acme",
        acquisition_source="direct",
        consent_basis=ConsentBasis.CONTRACT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="converted prospect",
    )
    linked = service.link_account(
        grant=founder,
        company_id="company:1",
        account_id="account:future-ao09:1",
        now=NOW,
        reason="explicit post-conversion account reference",
    )
    assert linked.account_id == "account:future-ao09:1"
    assert store.audits()[-1].action == "LINK_AXIGNAL_ACCOUNT_REFERENCE"


def test_prospect_lifecycle_is_separate_from_company_and_conversion_is_explicit(tmp_path) -> None:
    store = SqliteAdminCommercialStore(tmp_path / "commercial.sqlite3")
    service = AdminCommercialService(store)
    prospect = service.create_prospect(
        grant=_grant(),
        prospect_id="prospect:1",
        display_name="Potential customer",
        acquisition_source="newsletter",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="newsletter conversion",
    )
    assert prospect.stage is ProspectStage.NEW
    assert prospect.company_id is None

    service.create_company(
        grant=_grant(),
        company_id="company:converted",
        display_name="Converted company",
        acquisition_source="newsletter",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="qualified prospect",
    )
    converted = service.set_prospect_stage(
        grant=_grant(),
        prospect_id="prospect:1",
        stage=ProspectStage.CONVERTED,
        company_id="company:converted",
        now=NOW,
        reason="commercial conversion",
    )
    assert converted.company_id == "company:converted"
    assert store.audits()[-1].before_ref == "prospect-stage:NEW"
    assert store.audits()[-1].after_ref == "prospect-stage:CONVERTED"
