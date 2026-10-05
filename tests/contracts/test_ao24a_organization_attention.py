"""Controlled canonical targets are test-only; no economic/profile input path."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

import pytest

from domain.identity import OrganizationId
from domain.organizations.model import Organization
from tests.contracts.test_fr30_production_first_proof import _install_source, _service
from tools.runtime.first_proof import FirstProofInsufficientEvidence
from tools.runtime.organization_attention import (
    CanonicalObservationTarget,
    OrganizationAttention,
    attention_target,
    load_observation_catalog,
)


def _attention(tmp_path: Path) -> OrganizationAttention:
    proof = _service(tmp_path)
    catalog = (
        *load_observation_catalog(None, "axignal.com"),
        CanonicalObservationTarget(
            Organization(OrganizationId("org:controlled-second"), "Controlled second"),
            "https://controlled.example/",
            "identity:controlled-test:second",
        ),
    )
    return OrganizationAttention(proof, catalog)


def test_resolved_add_duplicate_selection_reobserve_restart_and_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attention = _attention(tmp_path)
    _install_source(monkeypatch, attention.proof)
    first = attention.add("operator:a", "AXIGNAL", "https://axignal.com/")
    second = attention.add("operator:a", "Controlled second", "https://controlled.example/")
    assert second["organization"]["id"] == "org:controlled-second"
    assert first["organization"]["id"] == "org:axignal"
    inventory = attention.inventory("operator:a", can_observe=True)
    assert inventory["accessMode"] == "INTERNAL_ADMIN"
    assert len(inventory["organizations"]) == 2
    assert attention.projection("operator:a") == second
    duplicate = attention.add("operator:a", "Controlled second", "https://controlled.example/")
    assert duplicate == second
    assert len(attention.proof.observation_memory.for_subject("org:controlled-second")) == 1
    attention.select("operator:b", inventory["organizations"][0]["id"])
    assert attention.projection("operator:b") == first
    assert attention.projection("operator:a") == second
    repeated = attention.reobserve("operator:a", inventory["selectedId"])
    assert repeated["context"]["id"] != second["context"]["id"]
    history = repeated["temporalHistory"]
    assert history["disposition"] == "MULTIPLE_OBSERVATIONS"
    assert len(history["items"]) == 2
    assert history["items"][0]["normalizedStateChanged"] is None
    assert history["items"][1]["normalizedStateChanged"] is False
    assert history["items"][0]["sourceRef"] == "https://controlled.example/"
    assert history["items"][1]["sourceRef"] == "https://controlled.example/"
    assert attention.proof.store.get(second["context"]["id"]) == second
    restarted = OrganizationAttention(_service(tmp_path), attention.catalog)
    assert restarted.projection("operator:a") == repeated
    assert restarted.projection("operator:b") == first
    signal = repeated["nodes"][0]
    assert signal["sourceRefs"] == ["https://controlled.example/"]
    assert signal["observationSupportRefs"]
    assert signal["uncertainty"]
    assert signal["evidenceNarrative"]["steps"]
    assert signal["currentness"] == "CURRENT"
    assert not {"billing", "checkout", "privateRevenue", "session"} & inventory.keys()


def test_unresolved_attention_persists_without_organization_or_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attention = _attention(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("unresolved attention must not acquire or create truth")

    monkeypatch.setattr(type(attention.proof), "observe_resolved", forbidden)
    result = attention.add("operator:a", "Unverified name", "https://unverified.example/")
    assert result["state"] == "IDENTITY_UNRESOLVED"
    restarted = OrganizationAttention(_service(tmp_path), attention.catalog)
    assert (
        restarted.inventory("operator:a", can_observe=True)["organizations"][0]["state"]
        == "IDENTITY_UNRESOLVED"
    )
    assert restarted.projection("operator:a") is None
    assert attention.proof.store.latest() is None
    assert attention.proof.observation_memory.for_subject("org:controlled-second") == ()
    with pytest.raises(ValueError, match="FOCUS_NOT_AVAILABLE"):
        attention.select("operator:a", result["attentionId"])


def test_failure_does_not_replace_selected_evidence_and_retries_use_new_run_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attention = _attention(tmp_path)
    _install_source(monkeypatch, attention.proof)
    first = attention.add("operator:a", "AXIGNAL", "https://axignal.com/")
    original = attention.proof.observe_resolved

    def insufficient(**kwargs):
        attention.proof.store.next_sequence()
        raise FirstProofInsufficientEvidence("CONTROLLED_SOURCE_FAILURE")

    monkeypatch.setattr(
        type(attention.proof), "observe_resolved", lambda self, **kwargs: insufficient(**kwargs)
    )
    with pytest.raises(FirstProofInsufficientEvidence):
        attention.add("operator:a", "Controlled second", "https://controlled.example/")
    assert attention.projection("operator:a") == first
    assert (
        attention.inventory("operator:a", can_observe=True)["organizations"][-1]["state"]
        == "INSUFFICIENT_EVIDENCE"
    )
    monkeypatch.setattr(
        type(attention.proof), "observe_resolved", lambda self, **kwargs: original(**kwargs)
    )
    second = attention.add("operator:a", "Controlled second", "https://controlled.example/")
    assert second["context"]["id"].endswith(":3")


def test_catalog_revocation_and_identity_mismatch_cannot_retarget_old_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attention = _attention(tmp_path)
    _install_source(monkeypatch, attention.proof)
    projection = attention.add("operator:a", "Controlled second", "https://controlled.example/")
    identifier = attention.inventory("operator:a", can_observe=True)["selectedId"]
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        attention.add("operator:a", "AXIGNAL", "https://controlled.example/")
    assert attention.projection("operator:a") == projection
    revoked = OrganizationAttention(attention.proof, attention.catalog[:1])
    assert revoked.projection("operator:a") is None
    for action in (revoked.select, revoked.reobserve):
        with pytest.raises(ValueError, match="FOCUS_NOT_AVAILABLE"):
            action("operator:a", identifier)
    with pytest.raises(ValueError, match="FOCUS_NOT_AVAILABLE"):
        attention.select("operator:a", "xeed:foreign")


@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_or_interrupted_acquisition_survives_restart_without_false_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interrupted: bool
) -> None:
    attention = _attention(tmp_path)
    _install_source(monkeypatch, attention.proof)
    first = attention.add("operator:a", "AXIGNAL", "https://axignal.com/")

    def fail(self, **kwargs):
        del self, kwargs
        if interrupted:
            raise KeyboardInterrupt("CONTROLLED_PROCESS_INTERRUPTION")
        raise RuntimeError("CONTROLLED_RUNTIME_FAILURE")

    monkeypatch.setattr(type(attention.proof), "observe_resolved", fail)
    with pytest.raises(KeyboardInterrupt if interrupted else RuntimeError):
        attention.add("operator:a", "Controlled second", "https://controlled.example/")
    restarted = OrganizationAttention(_service(tmp_path), attention.catalog)
    assert restarted.projection("operator:a") == first
    entry = restarted.inventory("operator:a", can_observe=True)["organizations"][-1]
    assert entry["state"] == ("RUN_INTERRUPTED" if interrupted else "RUNTIME_FAILURE")
    assert entry["projectionContextId"] is None
    assert restarted.proof.observation_memory.for_subject("org:controlled-second") == ()


def test_network_work_runs_outside_attention_lock_and_same_intent_is_leased(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attention = _attention(tmp_path)
    _install_source(monkeypatch, attention.proof)
    original = attention.proof.observe_resolved
    started = threading.Event()
    release = threading.Event()
    inventory_completed = threading.Event()
    calls = 0
    result_box: dict[str, object] = {}
    error_box: list[BaseException] = []

    def blocking_observe(self, **kwargs):
        nonlocal calls
        del self
        calls += 1
        started.set()
        if not release.wait(timeout=2):
            raise RuntimeError("fixture observation release timeout")
        return original(**kwargs)

    monkeypatch.setattr(type(attention.proof), "observe_resolved", blocking_observe)

    def run_add() -> None:
        try:
            result_box["projection"] = attention.add(
                "operator:a",
                "Controlled second",
                "https://controlled.example/",
            )
        except BaseException as exc:  # capture thread failure for assertion below
            error_box.append(exc)

    worker = threading.Thread(target=run_add, daemon=True)
    worker.start()
    assert started.wait(timeout=1)

    inventory_box: dict[str, object] = {}

    def read_inventory() -> None:
        inventory_box["value"] = attention.inventory("operator:b", can_observe=True)
        inventory_completed.set()

    reader = threading.Thread(target=read_inventory, daemon=True)
    reader.start()
    if not inventory_completed.wait(timeout=0.5):
        release.set()
        worker.join(timeout=2)
        reader.join(timeout=2)
        pytest.fail("attention inventory blocked behind network acquisition")

    inventory = inventory_box["value"]
    assert isinstance(inventory, dict)
    active = next(
        item
        for item in inventory["organizations"]
        if item["organizationId"] == "org:controlled-second"
    )
    assert active["state"] == "PLANTING"

    duplicate = attention.add(
        "operator:b",
        "Controlled second",
        "https://controlled.example/",
    )
    assert duplicate["state"] == "PLANTING"
    assert calls == 1

    release.set()
    worker.join(timeout=2)
    reader.join(timeout=2)
    assert not worker.is_alive()
    assert not error_box
    projection = result_box["projection"]
    assert isinstance(projection, dict)
    assert projection["organization"]["id"] == "org:controlled-second"
    assert calls == 1


def test_expired_lease_can_be_reclaimed_and_old_token_is_fenced(tmp_path: Path) -> None:
    attention = _attention(tmp_path)
    identifier = attention._id("https://controlled.example/")
    first = attention._claim_lease(identifier, "observe")
    assert first is not None
    assert attention._owns_lease(identifier, first)

    with sqlite3.connect(attention.proof.store.path) as db:
        db.execute(
            "UPDATE organization_attention_leases SET expires_at=? WHERE attention_id=?",
            ("2000-01-01T00:00:00+00:00", identifier),
        )

    second = attention._claim_lease(identifier, "observe")
    assert second is not None
    assert second != first
    assert not attention._owns_lease(identifier, first)
    assert attention._owns_lease(identifier, second)

    attention._release_lease(identifier, first)
    assert attention._owns_lease(identifier, second)
    attention._release_lease(identifier, second)
    assert not attention._owns_lease(identifier, second)


@pytest.mark.parametrize(
    "uri",
    [
        "http://example.com/",
        "https://127.0.0.1/",
        "https://localhost/",
        "https://user:password@example.com/",
        "https://example.com/?token=secret",
        "https://example.com/path",
        "https://example.com/#secret",
        "https://example.com:8443/",
        "https://host.internal/",
    ],
)
def test_public_attention_rejects_private_and_non_root_locators(uri: str) -> None:
    with pytest.raises(ValueError):
        attention_target(uri)


def test_catalog_requires_authority_and_ambiguity_stays_unresolved(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            [
                {
                    "organizationId": "org:other",
                    "canonicalName": "Other",
                    "targetUri": "https://other.example/",
                    "identityAuthorityRef": "",
                }
            ]
        )
    )
    with pytest.raises(ValueError):
        load_observation_catalog(path, "axignal.com")
    attention = _attention(tmp_path)
    ambiguous = CanonicalObservationTarget(
        Organization(OrganizationId("org:ambiguous"), "Controlled second"),
        "https://ambiguous.example/",
        "identity:controlled:ambiguous",
    )
    attention = OrganizationAttention(attention.proof, (*attention.catalog, ambiguous))
    assert (
        attention.add("operator:a", "Controlled second", "https://controlled.example/")["state"]
        == "IDENTITY_UNRESOLVED"
    )
    with sqlite3.connect(attention.proof.store.path) as db:
        assert db.execute("SELECT COUNT(*) FROM first_proof_sessions").fetchone()[0] == 0
