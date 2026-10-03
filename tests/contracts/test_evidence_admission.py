"""Evidence admission invariants (MASTER §15.1, §23, §33)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pytest

from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    SourceAuthority,
)


def _evidence(authority: SourceAuthority) -> Evidence:
    return Evidence(
        id="ev-1",
        source="https://example.com",
        source_type="web",
        reference="https://example.com/about",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=datetime(2026, 1, 1, 12, 0, 0),
        authority=authority,
    )


def test_official_evidence_is_admitted_as_canonical() -> None:
    decision = EvidenceAdmission.admit(_evidence(SourceAuthority.OFFICIAL_WEB))
    assert decision.admitted is True
    assert decision.is_canonical is True


def test_attention_only_signals_are_never_canonical() -> None:
    for authority in (
        SourceAuthority.USER_SIGNAL,
        SourceAuthority.AGENCY_SIGNAL,
        SourceAuthority.SUBSCRIBER_SIGNAL,
    ):
        decision = EvidenceAdmission.admit(_evidence(authority))
        assert decision.admitted is False
        assert decision.is_canonical is False


def test_hand_built_decision_is_not_canonical() -> None:
    forged = AdmissionDecision(admitted=True, evidence_id="ev-1", reason="trust me")
    assert forged.is_canonical is False
    try:
        EvidenceAdmission.require(forged)
    except EvidenceAdmissionRequired:
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError("forged admission decision was accepted")


def test_evidence_without_reference_is_not_admitted() -> None:
    evidence = Evidence(
        id="ev-x",
        source="s",
        source_type="t",
        reference="   ",
        extracted_claim="claim",
        observed_at=datetime(2026, 1, 1),
        authority=SourceAuthority.OFFICIAL_WEB,
    )
    decision = EvidenceAdmission.admit(evidence)
    assert decision.admitted is False


@pytest.mark.parametrize(
    ("field", "reason"),
    (("id", "id"), ("source", "source"), ("source_type", "source type")),
)
def test_incomplete_evidence_identity_is_never_admitted(field: str, reason: str) -> None:
    values = {
        "id": "ev-complete",
        "source": "official",
        "source_type": "web",
    }
    values[field] = " "
    evidence = Evidence(
        id=values["id"],
        source=values["source"],
        source_type=values["source_type"],
        reference="https://example.test/evidence",
        extracted_claim="Observed claim",
        observed_at=datetime(2026, 9, 30),
        authority=SourceAuthority.OFFICIAL_WEB,
    )

    decision = EvidenceAdmission.admit(evidence)

    assert decision.is_canonical is False
    assert reason in decision.reason


def test_unknown_runtime_authority_fails_closed() -> None:
    evidence = _evidence(SourceAuthority.OFFICIAL_WEB)
    object.__setattr__(evidence, "authority", "UNKNOWN_PROVIDER_AUTHORITY")
    decision = EvidenceAdmission.admit(evidence)
    assert decision.is_canonical is False
    assert "unknown source authority" in decision.reason


def test_claim_admission_is_bound_to_evidence_and_proposition_digests() -> None:
    evidence = _evidence(SourceAuthority.OFFICIAL_WEB)
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    assert decision.is_canonical is True
    assert decision.is_proposition_bound is True
    assert decision.evidence_digest is not None
    assert decision.proposition_digest is not None
    EvidenceAdmission.require_claim(decision, request)


def test_claim_admission_rejects_proposition_not_equal_to_extracted_claim() -> None:
    evidence = _evidence(SourceAuthority.OFFICIAL_WEB)
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition="ACME does not manufacture industrial pumps.",
    )
    decision = EvidenceAdmission.admit_claim(request)
    assert decision.is_canonical is False
    assert "does not exactly match" in decision.reason


def test_dataclass_replace_of_canonical_decision_loses_authority() -> None:
    evidence = _evidence(SourceAuthority.OFFICIAL_WEB)
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    copied = replace(decision, evidence_id="ev-forged")
    assert decision.is_canonical is True
    assert copied.is_canonical is False


def test_predicate_specific_authority_fails_closed() -> None:
    evidence = _evidence(SourceAuthority.REGISTRY)
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    assert decision.is_canonical is False
    assert "not authorized for this predicate" in decision.reason


def test_unknown_predicate_has_no_implicit_authority() -> None:
    evidence = _evidence(SourceAuthority.OFFICIAL_WEB)
    request = AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="UNDECLARED_PREDICATE",
        object_or_value="value",
        claim_proposition=evidence.extracted_claim,
    )
    decision = EvidenceAdmission.admit_claim(request)
    assert decision.is_canonical is False
    assert "no explicit source-authority" in decision.reason
