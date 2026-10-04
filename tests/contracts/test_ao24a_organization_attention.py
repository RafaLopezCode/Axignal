"""Controlled canonical targets are test-only; no economic/profile input path."""

from __future__ import annotations

import json
import sqlite3
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
