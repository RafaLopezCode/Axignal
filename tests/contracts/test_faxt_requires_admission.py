"""Canonical FAXT creation requires exact proposition-bound evidence admission."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    SourceAuthority,
)
from domain.evidence.epistemics import EpistemicState
from domain.faxt.model import FAXT, FAXTCreationError
from domain.identity import FaxtId

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _evidence(identifier: str = "ev-1") -> Evidence:
    return Evidence(
        id=identifier,
        source="https://example.com",
        source_type="web",
        reference="https://example.com/about",
        extracted_claim="ACME manufactures industrial pumps.",
        observed_at=NOW,
        authority=SourceAuthority.OFFICIAL_WEB,
    )


def _request(evidence: Evidence) -> AdmissionRequest:
    return AdmissionRequest(
        evidence=evidence,
        subject_id="org-acme",
        predicate="MANUFACTURES",
        object_or_value="industrial pumps",
        claim_proposition=evidence.extracted_claim,
    )


def _decision(evidence: Evidence) -> AdmissionDecision:
    return EvidenceAdmission.admit_claim(_request(evidence))


def _create(evidence: Evidence, decision: AdmissionDecision, **overrides: object) -> FAXT:
    values = {
        "faxt_id": FaxtId("faxt-1"),
        "subject_id": "org-acme",
        "predicate": "MANUFACTURES",
        "object_or_value": "industrial pumps",
        "evidence": evidence,
        "decision": decision,
        "claim_proposition": evidence.extracted_claim,
    }
    values.update(overrides)
    return FAXT.create(**values)  # type: ignore[arg-type]


def test_faxt_can_be_created_with_exact_proposition_admission() -> None:
    evidence = _evidence()
    faxt = _create(evidence, _decision(evidence))
    assert faxt.epistemic_state is EpistemicState.OBSERVED
    assert faxt.id == FaxtId("faxt-1")
    assert faxt.evidence_refs == ("ev-1",)


def test_evidence_only_admission_cannot_create_faxt() -> None:
    evidence = _evidence()
    with pytest.raises(EvidenceAdmissionRequired, match="proposition-bound"):
        _create(evidence, EvidenceAdmission.admit(evidence))


def test_hand_built_admission_cannot_create_faxt() -> None:
    evidence = _evidence()
    forged = AdmissionDecision(admitted=True, evidence_id="ev-1", reason="forged")
    with pytest.raises(EvidenceAdmissionRequired):
        _create(evidence, forged)


@pytest.mark.parametrize(
    "changed",
    [
        lambda e: replace(e, extracted_claim="ACME does not manufacture pumps."),
        lambda e: replace(e, authority=SourceAuthority.SPECIALIST),
        lambda e: replace(e, observed_at=e.observed_at + timedelta(days=1)),
        lambda e: replace(e, reference="https://example.com/changed"),
        lambda e: replace(e, source_type="registry"),
    ],
)
def test_mutated_evidence_with_same_id_rejects_prior_decision(changed) -> None:  # type: ignore[no-untyped-def]
    original = _evidence()
    decision = _decision(original)
    mutated = changed(original)
    with pytest.raises(EvidenceAdmissionRequired):
        _create(mutated, decision, claim_proposition=mutated.extracted_claim)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subject_id", "org-victim"),
        ("predicate", "EXCLUSIVE_CUSTOMER"),
        ("object_or_value", "org-customer"),
        ("claim_proposition", "ACME is an exclusive customer."),
    ],
)
def test_mutated_proposition_rejects_prior_decision(field: str, value: str) -> None:
    evidence = _evidence()
    decision = _decision(evidence)
    with pytest.raises(EvidenceAdmissionRequired):
        _create(evidence, decision, **{field: value})


def test_decision_for_different_evidence_identity_is_rejected() -> None:
    evidence = _evidence("ev-1")
    decision = _decision(_evidence("ev-2"))
    with pytest.raises(EvidenceAdmissionRequired, match="identity"):
        _create(evidence, decision)


def test_faxt_rejects_empty_subject_and_value_before_admission_check() -> None:
    evidence = _evidence()
    decision = _decision(evidence)
    with pytest.raises(FAXTCreationError, match="subject"):
        _create(evidence, decision, subject_id=" ")
    with pytest.raises(FAXTCreationError, match="object or value"):
        _create(evidence, decision, object_or_value=" ")


def test_canonical_observed_at_cannot_diverge_from_admitted_evidence() -> None:
    evidence = _evidence()
    decision = _decision(evidence)
    with pytest.raises(FAXTCreationError, match="observed_at"):
        _create(
            evidence,
            decision,
            observed_at=evidence.observed_at + timedelta(seconds=1),
        )


def test_direct_faxt_constructor_is_blocked() -> None:
    with pytest.raises(TypeError, match=r"FAXT\.create"):
        FAXT(
            id=FaxtId("faxt-forged"),
            subject_id="org-acme",
            predicate="MANUFACTURES",
            object_or_value="industrial pumps",
            evidence_refs=(),
            observed_at=NOW,
            epistemic_state=EpistemicState.OBSERVED,
        )


def test_dataclass_replace_cannot_relabel_canonical_faxt() -> None:
    evidence = _evidence()
    faxt = _create(evidence, _decision(evidence))
    with pytest.raises(TypeError, match=r"FAXT\.create"):
        replace(faxt, epistemic_state=EpistemicState.INFERRED)
