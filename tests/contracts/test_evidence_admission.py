"""Evidence admission invariants (MASTER §15.1, §23, §33)."""

from __future__ import annotations

from datetime import datetime

from domain.evidence.admission import (
    AdmissionDecision,
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
