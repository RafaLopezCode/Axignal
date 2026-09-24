"""Observed vs Potential must not collapse (MASTER §16.2, §16.5, §46.19)."""

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
from domain.relationships.model import (
    ObservedRelationship,
    PotentialRelationship,
    RelationshipEpistemicClass,
    deserialize_relationship,
)


def _decision() -> AdmissionDecision:
    evidence = Evidence(
        id="ev-rel",
        source="registry",
        source_type="registry",
        reference="https://registry.example/acme",
        extracted_claim="ACME supplies Beta.",
        observed_at=datetime(2026, 1, 1),
        authority=SourceAuthority.REGISTRY,
    )
    return EvidenceAdmission.admit(evidence)


def _observed_payload() -> dict[str, object]:
    return {
        "epistemic_class": "OBSERVED",
        "id": "rel-1",
        "source_org": "org-acme",
        "target_org": "org-beta",
        "relationship_type": "SUPPLIES",
        "evidence_refs": ["ev-rel"],
        "first_observed_at": datetime(2026, 1, 1),
        "last_observed_at": datetime(2026, 2, 1),
    }


def _potential_payload() -> dict[str, object]:
    return {
        "epistemic_class": "POTENTIAL",
        "id": "rel-2",
        "source_org": "org-acme",
        "target_org": "org-gamma",
        "relationship_type": "POTENTIAL_CUSTOMER",
        "rationale": "compatible product and market",
    }


def test_potential_deserializes_as_potential() -> None:
    relationship = deserialize_relationship(_potential_payload())
    assert isinstance(relationship, PotentialRelationship)
    assert not isinstance(relationship, ObservedRelationship)
    assert relationship.epistemic_class is RelationshipEpistemicClass.POTENTIAL


def test_observed_cannot_materialize_without_admission() -> None:
    with pytest.raises(EvidenceAdmissionRequired):
        deserialize_relationship(_observed_payload())
    forged = AdmissionDecision(admitted=True, evidence_id="ev-rel", reason="forged")
    with pytest.raises(EvidenceAdmissionRequired):
        deserialize_relationship(_observed_payload(), decision=forged)


def test_observed_deserializes_with_admitted_decision() -> None:
    relationship = deserialize_relationship(_observed_payload(), decision=_decision())
    assert isinstance(relationship, ObservedRelationship)
    assert relationship.epistemic_class is RelationshipEpistemicClass.OBSERVED


def test_observed_relationship_creation_requires_admission() -> None:
    forged = AdmissionDecision(admitted=True, evidence_id="ev-rel", reason="forged")
    with pytest.raises(EvidenceAdmissionRequired):
        ObservedRelationship.create(
            relationship_id="rel-3",
            source_org="org-acme",
            target_org="org-delta",
            relationship_type="SUPPLIES",
            evidence_ids=("ev-rel",),
            decision=forged,
            first_observed_at=datetime(2026, 1, 1),
            last_observed_at=datetime(2026, 2, 1),
        )
