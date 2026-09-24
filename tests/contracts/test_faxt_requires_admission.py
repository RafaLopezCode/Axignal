"""Canonical FAXT creation requires evidence admission (MASTER §15.1, §46.9)."""

from __future__ import annotations

from datetime import datetime

import pytest

from domain.evidence.admission import (
    AdmissionDecision,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    SourceAuthority,
)
from domain.evidence.epistemics import EpistemicState
from domain.faxt.model import FAXT, FAXTCreationError


def _evidence(identifier: str = "ev-1") -> Evidence:
    return Evidence(
        id=identifier,
        source="https://example.com",
        source_type="web",
        reference="https://example.com/about",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=datetime(2026, 1, 1),
        authority=SourceAuthority.OFFICIAL_WEB,
    )


def test_faxt_can_be_created_with_admitted_evidence() -> None:
    evidence = _evidence()
    decision = EvidenceAdmission.admit(evidence)
    faxt = FAXT.create(
        faxt_id="faxt-1",
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        evidence=evidence,
        decision=decision,
    )
    assert faxt.epistemic_state is EpistemicState.OBSERVED
    assert faxt.evidence_refs == ("ev-1",)


def test_faxt_creation_without_admission_fails_closed() -> None:
    evidence = _evidence()
    forged = AdmissionDecision(admitted=True, evidence_id="ev-1", reason="forged")
    with pytest.raises(EvidenceAdmissionRequired):
        FAXT.create(
            faxt_id="faxt-2",
            subject_id="org-acme",
            predicate="MANUFACTURES",
            object_or_value="industrial pumps",
            evidence=evidence,
            decision=forged,
        )


def test_faxt_rejects_decision_for_different_evidence() -> None:
    evidence = _evidence("ev-1")
    decision = EvidenceAdmission.admit(_evidence("ev-2"))
    with pytest.raises(FAXTCreationError):
        FAXT.create(
            faxt_id="faxt-3",
            subject_id="org-acme",
            predicate="MANUFACTURES",
            object_or_value="pumps",
            evidence=evidence,
            decision=decision,
        )
