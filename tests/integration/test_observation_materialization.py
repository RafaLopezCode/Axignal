"""Real OIDC/locator/admission -> derived authority -> T12 -> Brain -> independent AXENT."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.observation_runtime.materialization import Readiness, derive_observation
from application.subscriber_access.pilot import PilotAccessService
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId
from pipeline.axent import SqliteResearchRequestLedger
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
from tests.axent.fixtures import ScriptedLuna
from tests.integration.test_autonomous_observation_brain import _Clock
from tests.integration.test_axent_grounded_e2e import _ask
from tests.integration.test_organization_admission_e2e import _add, _pilot, _registry
from tests.integration.test_subscriber_composition import (
    _append_opportunity_capability_source,
    _build,
)
from tests.observation_runtime.harness import CountingTed
from tools.runtime.observation_daily import (
    build_economic_runtime,
    load_enrollment,
    run_scheduled_tick,
)
from tools.runtime.observation_enrollment import (
    ATTENTION,
    ENROLLMENT,
    MANIFEST,
    SubscriberObservationAuthority,
    check,
    first_proof,
    reconcile,
    validate_manifest,
)

SERVICE = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Solar photovoltaic installation",
    "areaServed": {
        "@type": "Country",
        "identifier": {"@type": "PropertyValue", "propertyID": "NUTS", "value": "ES"},
    },
    "audience": {"@type": "Audience", "audienceType": "government"},
}


def setup_focus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, subjects=("proof:a",), scope=True
):
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_PILOT_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_ENV", "development")
    clock = _Clock(datetime.now(UTC))
    facade = _build(tmp_path, pilot=True, identity_source=_registry(tmp_path), clock=clock)
    observers = []
    for subject in subjects:
        token, tenant = _pilot(facade, tmp_path, subject)
        added = _add(facade, token, subject)
        assert added.status == 200
        member = facade.identity.authenticate(token)
        focus = XeedId(str(added.body["focusId"]))
        context = TrustedRequestContext(member.principal_id, member.tenant_id)
        org = (
            build_economic_runtime(tmp_path, code_sha="proof")
            .authorize(context, focus)
            .organization.id
        )
        observers.append((token, tenant, focus, context, org))
    _append_opportunity_capability_source(tmp_path)
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    original = memory.for_subject("org:registry:shared")[0]
    content = original.raw_content or ""
    if scope:
        content += '<script type="application/ld+json">' + json.dumps(SERVICE) + "</script>"
    org = observers[0][4]
    memory.append(
        replace(
            original,
            record=replace(
                original.record,
                observation_id="observation:proof:public-service",
                subject_id=str(org),
                observed_at=clock.now() - timedelta(minutes=5),
                source_ref="https://www.solartec.example.com/",
                content_fingerprint=hashlib.sha256(content.encode()).hexdigest(),
            ),
            raw_content=content,
            reuse_authority=replace(original.reuse_authority, applicable_subject_ids=(str(org),)),
        )
    )
    authority = SubscriberObservationAuthority(tmp_path, clock)
    return facade, clock, authority, observers


def payloads(root: Path):
    return {p.name: p.read_bytes() for p in root.iterdir() if p.name.endswith(".json")}


def test_no_focus_creates_nothing_and_check_has_zero_writes(tmp_path, monkeypatch):
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_ENABLED", "true")
    authority = SubscriberObservationAuthority(tmp_path / "data", _Clock(datetime.now(UTC)))
    root = tmp_path / "config"
    assert check(authority, root)["state"] == "NO_ELIGIBLE_FOCUS"
    assert reconcile(authority, root)["state"] == "NO_ELIGIBLE_FOCUS"
    assert first_proof(authority, root, code_sha="test")["manual_tick_status"] == "NOT_EXECUTED"
    assert not root.exists() and not authority.root.exists()


def test_oidc_locator_canonical_focus_materializes_without_live_session(tmp_path, monkeypatch):
    _facade, clock, authority, observers = setup_focus(tmp_path, monkeypatch)
    root = tmp_path / "config"
    desired = derive_observation(authority, now=clock.now())
    assert desired.state is Readiness.READY_FOR_MANUAL_TICK
    assert desired.entries[0].context == observers[0][3]
    with sqlite3.connect(tmp_path / "subscriber-runtime.sqlite3") as db:
        db.execute("UPDATE subscriber_sessions SET revoked_at=?", (clock.now().isoformat(),))
    before = {p: p.read_bytes() for p in tmp_path.glob("*.sqlite3")}
    assert check(authority, root)["state"] == "ENROLLMENT_NOT_MATERIALIZED"
    assert before == {p: p.read_bytes() for p in tmp_path.glob("*.sqlite3")}
    assert reconcile(authority, root)["changed"]
    assert check(authority, root)["state"] == "READY_FOR_MANUAL_TICK"
    persisted = payloads(root)
    assert not reconcile(SubscriberObservationAuthority(tmp_path, clock), root)["changed"]
    assert payloads(root) == persisted
    assert set(json.loads(persisted[ENROLLMENT])[0]) == {"tenantId", "principalId", "focusId"}
    assert validate_manifest(root / MANIFEST, root / ENROLLMENT, root / ATTENTION)
    assert not any(
        word in str(persisted).lower() for word in ("email", "token", "secret", "subject")
    )
    assert (
        build_economic_runtime(tmp_path, code_sha="proof")
        .authorize(observers[0][3], observers[0][2])
        .organization.id
        == desired.entries[0].organization_id
    )


def test_existing_pending_recompute_cannot_escape_empty_authorized_scope(tmp_path, monkeypatch):
    from application.observation_runtime import ObservationFamily, run_daily_tick
    from tests.observation_runtime.harness import DAY_1, world

    w = world(tmp_path)
    store = w.store()
    assert store.owe_recompute(
        xeed_id="focus:revoked",
        family=ObservationFamily.DEMAND.value,
        evidence_keys=("evidence:old",),
        now=DAY_1,
    )
    report = run_daily_tick(
        store=store, now=DAY_1, attention=(), acquirers=w.acquirers(), recompute=w.downstream
    )
    assert report.requests == 0 and not report.recomputations
    assert store.pending_recompute(), "revocation never erases unpaid continuity history"


def test_wrong_principal_and_forged_cross_tenant_snapshot_never_dispatch(tmp_path, monkeypatch):
    _, clock, authority, observers = setup_focus(
        tmp_path, monkeypatch, subjects=("proof:a", "proof:b")
    )
    root = tmp_path / "config"
    reconcile(authority, root)
    entries = json.loads((root / ENROLLMENT).read_text())
    entries[0]["principalId"] = str(observers[1][3].principal_id)
    (root / ENROLLMENT).write_text(json.dumps(entries))
    assert check(authority, root)["state"] == "INVALID_MATERIALIZATION"
    ted = CountingTed()
    assert (
        first_proof(
            authority,
            root,
            code_sha="test",
            source_ports={"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)},
        )["manual_tick_status"]
        == "NOT_EXECUTED"
    )
    assert not ted.bodies
    assert not authority.allows(
        TrustedRequestContext(observers[1][3].principal_id, observers[0][3].tenant_id),
        observers[0][2],
        clock.now(),
    )


def test_revocation_between_reservation_and_acquisition_zero_child_calls(tmp_path, monkeypatch):
    from application.observation_intelligence import SourceRegistry
    from application.observation_runtime.families import FAMILY_POLICIES, ObservationFamily
    from application.observation_runtime.ports import AcquisitionRequest
    from application.observation_runtime.tick import _entry_leads
    from tests.observation_runtime.harness import ATTENTION, DAY_1
    from tools.runtime.observation_daily import AuthorizedAcquisition

    facade, clock, authority, observers = setup_focus(tmp_path, monkeypatch)

    class NeverCalled:
        def acquisition_key(self, request):
            return "bounded"

        def worst_case_requests(self, request):
            return 1

        def acquire(self, request):
            raise AssertionError("unauthorized source call")

    attention = replace(ATTENTION[0], xeed_id=str(observers[0][2]))
    lead = _entry_leads(attention, FAMILY_POLICIES[ObservationFamily.DEMAND], DAY_1)[0]
    request = AcquisitionRequest(
        lead, SourceRegistry().get("ted-search-v3"), attention, DAY_1, 1, frozenset()
    )
    port = AuthorizedAcquisition(
        NeverCalled(), {str(observers[0][2]): observers[0][3]}, clock, authority.allows
    )
    assert port.worst_case_requests(request) == 1
    revoke(tmp_path, "grant", facade, clock, observers[0])
    result = port.acquire(request)
    assert result.blocked == "AUTHORIZATION_REVOKED" and result.requests == 0


def test_verified_billing_capacity_order_and_expiry_use_existing_policy(tmp_path, monkeypatch):
    from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
    from pipeline.source_acquisition import ContentAddressedArtifactStore
    from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore
    from tests.integration.test_subscriber_composition import _commit_verified_projection
    from tests.organization_admission.registry_fixture import entity, lei
    from tools.runtime.subscriber_provisioning import _ACCOUNT_REF, _ENVIRONMENT_REF

    facade, clock, authority, observers = setup_focus(tmp_path, monkeypatch)
    token, _, _, context, _ = observers[0]
    monkeypatch.setenv("AXIGNAL_STRIPE_LIVE_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", _ACCOUNT_REF)
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(
        billing, context.tenant_id, now=clock.now(), environment_ref=_ENVIRONMENT_REF, capacity=2
    )
    registry = _registry(tmp_path)
    registry.records.append(
        entity(
            ContentAddressedArtifactStore(tmp_path / "artifacts"),
            legal_name="Second Solar SL",
            lei_value=lei("SECONDSOLAR0000001"),
        )
    )
    # Recompose the real locator/admission facade against the same authoritative stores.
    facade = _build(
        tmp_path,
        pilot=True,
        identity_source=registry,
        clock=clock,
        environment_ref=_ENVIRONMENT_REF,
    )
    added = _add(facade, token, "proof:second", locator="Second Solar SL")
    assert added.status == 200
    authority = SubscriberObservationAuthority(tmp_path, clock)
    entries = derive_observation(authority, now=clock.now()).entries
    assert len(entries) == 2
    projection = billing.get_billing_projection(context.tenant_id)
    assert projection and projection.binding
    clock.current += timedelta(seconds=1)
    billing.commit_billing_projection(
        replace(
            projection,
            effective_capacity=1,
            provider_state_at=clock.now(),
            binding=replace(
                projection.binding, effective_capacity=1, provider_state_at=clock.now()
            ),
        )
    )
    active = SqliteSubscriberPortfolioStore(
        tmp_path / "subscriber-runtime.sqlite3"
    ).list_authorized(context)
    expected = min(active, key=lambda e: (e.created_at, e.focus_id)).focus_id
    assert [e.focus_id for e in derive_observation(authority, now=clock.now()).entries] == [
        expected
    ]
    revoke(tmp_path, "grant", facade, clock, observers[0])
    clock.current += timedelta(minutes=6)
    assert derive_observation(authority, now=clock.now()).state is Readiness.NO_ELIGIBLE_FOCUS


def test_two_tenants_separate_enrollment_shared_organization(tmp_path, monkeypatch):
    _, clock, authority, observers = setup_focus(
        tmp_path, monkeypatch, subjects=("proof:a", "proof:b")
    )
    root = tmp_path / "config"
    reconcile(authority, root)
    enrolled = load_enrollment(root / ENROLLMENT)
    assert len(enrolled) == 2 and len({e.context.tenant_id for e in enrolled}) == 2
    assert len(json.loads((root / ATTENTION).read_text())) == 1
    assert observers[0][4] == observers[1][4]
    assert len(derive_observation(authority, now=clock.now()).entries) == 2


@pytest.mark.parametrize("mode", ("no_scope", "hq", "stale", "no_canonical"))
def test_unknown_never_invents_market_or_canonical_identity(tmp_path, monkeypatch, mode):
    _, clock, authority, _observers = setup_focus(tmp_path, monkeypatch, scope=mode != "no_scope")
    if mode == "no_canonical":
        with sqlite3.connect(tmp_path / "subscriber-runtime.sqlite3") as db:
            db.execute("UPDATE subscriber_focuses SET organization_id='org:axignal'")
        assert derive_observation(authority, now=clock.now()).state is Readiness.NO_ELIGIBLE_FOCUS
        return
    if mode == "stale":
        clock.current += timedelta(days=31)
    if mode == "hq":
        with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
            # A public Organization address is not Service.areaServed.
            raw = json.dumps({"@type": "Organization", "address": {"addressCountry": "ES"}})
            db.execute(
                "UPDATE observations SET raw_content=?",
                ('photovoltaic<script type="application/ld+json">' + raw + "</script>",),
            )
    desired = derive_observation(authority, now=clock.now())
    assert desired.state is Readiness.ATTENTION_NOT_READY
    assert all(not entry.markets for entry in desired.entries)
    root = tmp_path / "config"
    reconcile(authority, root)
    assert json.loads((root / ATTENTION).read_text()) == []
    assert first_proof(authority, root, code_sha="test")["manual_tick_status"] == "NOT_EXECUTED"


def revoke(tmp_path, mode, facade, clock, observer):
    token, _tenant, focus, context, _ = observer
    if mode == "grant":
        service = PilotAccessService(SqlitePilotAccessStore(tmp_path / "subscriber-pilot.sqlite3"))
        grant = service.active_grant(context.tenant_id, now=clock.now())
        assert grant and service._store.revoke_grant(grant.grant_ref, revoked_at=clock.now())
    elif mode == "membership":
        assert SqliteSubscriberIdentityStore(
            tmp_path / "subscriber-runtime.sqlite3"
        ).remove_membership(context.principal_id, context.tenant_id)
    else:
        result = facade.handle(
            "POST",
            "/subscriber/portfolio",
            {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
            {"action": mode, "focusId": str(focus), "requestRef": "proof:" + mode},
        )
        assert result.status == 200


@pytest.mark.parametrize("mode", ("grant", "membership", "pause", "remove"))
def test_revoked_stale_files_and_pending_debt_execute_zero_work(tmp_path, monkeypatch, mode):
    facade, clock, authority, observers = setup_focus(tmp_path, monkeypatch)
    root = tmp_path / "config"
    reconcile(authority, root)
    enrolled = load_enrollment(root / ENROLLMENT)
    ted = CountingTed()
    ports = {"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)}
    assert first_proof(authority, root, code_sha="proof", source_ports=ports)["technical_execution"]
    revoke(tmp_path, mode, facade, clock, observers[0])
    clock.current += timedelta(days=1)
    calls = len(ted.bodies)
    summary = run_scheduled_tick(
        root=tmp_path,
        clock=clock,
        code_sha="proof",
        attention_file=root / ATTENTION,
        enrollment=enrolled,
        source_ports=ports,
    )
    assert summary["requests"] == 0 and summary["recomputations"] == 0
    assert len(ted.bodies) == calls
    assert (
        first_proof(authority, root, code_sha="proof", source_ports=ports)["manual_tick_status"]
        == "NOT_EXECUTED"
    )
    assert reconcile(authority, root)["changed"]
    assert json.loads((root / ENROLLMENT).read_text()) == []
    assert derive_observation(authority, now=clock.now()).state is Readiness.NO_ELIGIBLE_FOCUS


def test_atomic_staging_failure_and_corruption_repair_and_concurrent_restart(tmp_path, monkeypatch):
    _, _, authority, _ = setup_focus(tmp_path, monkeypatch)
    root = tmp_path / "config"
    reconcile(authority, root)
    original = payloads(root)
    (root / ENROLLMENT).write_text("{")
    assert check(authority, root)["state"] == "INVALID_MATERIALIZATION"
    real_fsync = os.fsync

    def fail(_):
        raise OSError("controlled disk failure")

    monkeypatch.setattr(os, "fsync", fail)
    with pytest.raises(OSError):
        reconcile(authority, root)
    assert (root / ATTENTION).read_bytes() == original[ATTENTION]
    monkeypatch.setattr(os, "fsync", real_fsync)
    assert reconcile(authority, root)["changed"]
    assert payloads(root) == original
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: reconcile(authority, root), range(2)))
    assert all(not result["changed"] for result in results)
    assert payloads(root) == original


def test_one_shot_real_brain_continuity_axent_and_research_feedback(tmp_path, monkeypatch):
    facade, clock, authority, observers = setup_focus(
        tmp_path, monkeypatch, subjects=("proof:a", "proof:b")
    )
    root = tmp_path / "config"
    reconcile(authority, root)
    luna = ScriptedLuna()
    facade.axent.service.reasoner = luna
    facade.axent.service.clock = clock.now
    for token, _, focus, *_ in observers:
        initial = _ask(facade, token, str(focus), "¿Qué oportunidades hay?")
        assert initial["grounding"]["research"] and initial["grounding"]["route"] == "ABSTAINED"
    assert not luna.requests
    ted = CountingTed()
    ports = {"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)}
    proof = first_proof(authority, root, code_sha="proof-e2e", source_ports=ports)
    assert (
        proof["technical_execution"]
        and proof["provider_calls"] > 0
        and proof["brain_recomputed"] >= 2
    )
    assert proof["economic_finding_produced"]
    assert not luna.requests, "observation never auto-requeries AXENT"
    economic = build_economic_runtime(tmp_path, code_sha="proof-e2e")
    ledger = SqliteResearchRequestLedger(
        tmp_path / "axent-research.sqlite3", runtime_path=tmp_path / "observation-runtime.sqlite3"
    )
    for token, tenant, focus, _context, _ in observers:
        lifecycle = ledger.states(tenant_id=tenant, xeed_id=str(focus))[0]
        assert lifecycle.status == "OBSERVATION_COMPLETED"
        assert economic.continuity.store.latest(tenant, str(focus))
        reading = _ask(facade, token, str(focus), "¿Qué oportunidades hay?")
        assert reading["grounding"]["claims"]
        assert all(c["epistemic"] == "POTENTIAL" for c in reading["grounding"]["claims"])
    calls = len(ted.bodies)
    replay = first_proof(authority, root, code_sha="proof-e2e", source_ports=ports)
    assert replay["manual_tick_status"] == "ALREADY_COMPLETED" and len(ted.bodies) == calls
    assert len(luna.requests) == 2
    assert SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3").evidence()


def test_read_only_adapters_reject_mutation_and_no_new_files(tmp_path, monkeypatch):
    _, _, authority, observers = setup_focus(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in tmp_path.glob("*.sqlite3")}
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        authority.identity.remove_membership(
            observers[0][3].principal_id, observers[0][3].tenant_id
        )
    with pytest.raises(PermissionError):
        authority.organizations._integrity._store.put_bytes(b"forbidden")
    assert before == {p: p.read_bytes() for p in tmp_path.glob("*.sqlite3")}


@pytest.mark.skipif(os.name != "posix", reason="production filesystem ownership is POSIX")
def test_production_files_root_www_data_0640(tmp_path, monkeypatch):
    if vars(os)["geteuid"]() != 0:
        pytest.skip("isolated production preflight runs as root:www-data")
    _, _, authority, _ = setup_focus(tmp_path, monkeypatch)
    monkeypatch.setenv("AXIGNAL_ENV", "production")
    root = tmp_path / "config"
    reconcile(authority, root)
    for name in (ENROLLMENT, ATTENTION, MANIFEST, ".reconcile.lock"):
        info = (root / name).stat()
        assert (info.st_uid, info.st_gid, info.st_mode & 0o777) == (0, 33, 0o640)
    assert check(authority, root)["state"] == "READY_FOR_MANUAL_TICK"
    (root / ATTENTION).chmod(0o644)
    assert check(authority, root)["state"] == "INVALID_MATERIALIZATION"
    assert reconcile(authority, root)["changed"]
    assert (root / ATTENTION).stat().st_mode & 0o777 == 0o640


def test_torn_generation_fails_closed_and_repairs(tmp_path, monkeypatch):
    _, _, authority, _ = setup_focus(tmp_path, monkeypatch)
    root = tmp_path / "config"
    reconcile(authority, root)
    (root / ATTENTION).write_text("[]", encoding="utf-8")
    assert not validate_manifest(root / MANIFEST, root / ENROLLMENT, root / ATTENTION)
    assert first_proof(authority, root, code_sha="torn")["manual_tick_status"] == "NOT_EXECUTED"
    assert reconcile(authority, root)["changed"]
    assert validate_manifest(root / MANIFEST, root / ENROLLMENT, root / ATTENTION)


def test_unwired_sources_cannot_make_attention_ready(tmp_path, monkeypatch):
    _, clock, authority, _ = setup_focus(tmp_path, monkeypatch)
    desired = derive_observation(authority, now=clock.now(), source_ids=frozenset())
    assert desired.state is Readiness.ATTENTION_NOT_READY
    assert desired.entries and all(not e.markets for e in desired.entries)
    assert dict(desired.reasons)["NO_ROUTABLE_SOURCE_OR_UNKNOWN_COST"] == 1
    assert desired.summary()["model_calls"] == desired.summary()["provider_calls"] == 0


def test_principal_selection_uses_pilot_redeemer_and_rejects_ambiguity(tmp_path, monkeypatch):
    _, clock, authority, observers = setup_focus(
        tmp_path, monkeypatch, subjects=("member:a", "member:b")
    )
    first, second = observers[0][3], observers[1][3]
    # Controlled existing identity-backed second membership, never an operator CLI context.
    with sqlite3.connect(tmp_path / "subscriber-runtime.sqlite3") as db:
        db.execute(
            "UPDATE subscriber_identity_bindings SET tenant_id=? WHERE principal_id=?",
            (first.tenant_id, second.principal_id),
        )
        db.execute(
            "INSERT INTO subscriber_memberships(principal_id, tenant_id, created_at) VALUES (?, ?, ?)",
            (second.principal_id, first.tenant_id, clock.now().isoformat()),
        )
    desired = derive_observation(authority, now=clock.now())
    assert len(desired.entries) == 1 and desired.entries[0].context == first
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_PILOT_ENABLED", "false")
    ambiguous = derive_observation(SubscriberObservationAuthority(tmp_path, clock), now=clock.now())
    assert ambiguous.state is Readiness.NO_ELIGIBLE_FOCUS
    assert dict(ambiguous.reasons)["PRINCIPAL_AUTHORITY_AMBIGUOUS_OR_REVOKED"] == 1
