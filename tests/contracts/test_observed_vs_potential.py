"""Observed vs Potential and canonical relationship materialization invariants."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness
from domain.relationships.model import (
    ObservedRelationship,
    PotentialRelationship,
    RelationshipEpistemicClass,
    RelationshipError,
    deserialize_relationship,
)

NOW = datetime(2026, 1, 15, tzinfo=UTC)


def _evidence(
    *,
    identifier: str = "ev-rel",
    claim: str = "ACME supplies org-beta.",
) -> Evidence:
    return Evidence(
        id=identifier,
        source="Beta official counterparty confirmation",
        source_type="counterparty",
        reference="https://beta.example.test/suppliers/acme",
        extracted_claim=claim,
        observed_at=NOW,
        authority=SourceAuthority.COUNTERPARTY,
        observation_subject_id="org-acme",
        grounded_claim=GroundedClaim(
            subject_id="org-acme",
            predicate="SUPPLIES",
            object_or_value="org-beta",
            subject_mention="ACME",
            predicate_mention="supplies",
            object_mention="org-beta",
            supporting_excerpt=claim,
        ),
    )


def _decision(
    evidence: Evidence,
    *,
    source_org: str = "org-acme",
    target_org: str = "org-beta",
    relationship_type: str = "SUPPLIES",
):
    return EvidenceAdmission.admit_claim(
        AdmissionRequest(
            evidence=evidence,
            subject_id=source_org,
            predicate=relationship_type,
            object_or_value=target_org,
            claim_proposition=evidence.extracted_claim,
        )
    )


def _observed_payload(*, evidence_id: str = "ev-rel") -> dict[str, object]:
    return {
        "epistemic_class": "OBSERVED",
        "id": "rel-1",
        "source_org": "org-acme",
        "target_org": "org-beta",
        "relationship_type": "SUPPLIES",
        "evidence_refs": [evidence_id],
        "first_observed_at": NOW - timedelta(days=1),
        "last_observed_at": NOW + timedelta(days=1),
        "currentness": Currentness.CURRENT.value,
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
    assert relationship.epistemic_class is RelationshipEpistemicClass.POTENTIAL


def test_direct_observed_relationship_construction_is_blocked() -> None:
    with pytest.raises(TypeError, match="materialized"):
        ObservedRelationship(
            id="rel-forged",
            source_org="org-acme",
            target_org="org-beta",
            relationship_type="SUPPLIES",
            evidence_refs=("ev-rel",),
            first_observed_at=NOW,
            last_observed_at=NOW,
        )


def test_observed_replay_requires_exact_evidence_and_admission() -> None:
    evidence = _evidence()
    with pytest.raises(EvidenceAdmissionRequired):
        deserialize_relationship(_observed_payload())
    with pytest.raises(EvidenceAdmissionRequired):
        deserialize_relationship(_observed_payload(), evidence=evidence)


def test_observed_replay_rejects_empty_or_unrelated_evidence_refs() -> None:
    evidence = _evidence()
    decision = _decision(evidence)

    empty = _observed_payload()
    empty["evidence_refs"] = []
    with pytest.raises(RelationshipError, match="evidence"):
        deserialize_relationship(empty, evidence=evidence, decision=decision)

    with pytest.raises(RelationshipError, match="exactly match"):
        deserialize_relationship(
            _observed_payload(evidence_id="ev-other"),
            evidence=evidence,
            decision=decision,
        )


def test_observed_relationship_rejects_decision_for_different_relation() -> None:
    evidence = _evidence()
    unrelated = _decision(
        evidence,
        source_org="org-acme",
        target_org="org-other",
        relationship_type="CUSTOMER",
    )
    with pytest.raises(EvidenceAdmissionRequired):
        ObservedRelationship.create(
            relationship_id="rel-1",
            source_org="org-acme",
            target_org="org-beta",
            relationship_type="SUPPLIES",
            evidence=evidence,
            decision=unrelated,
            first_observed_at=NOW - timedelta(days=1),
            last_observed_at=NOW + timedelta(days=1),
        )


def test_observed_relationship_validates_endpoints_and_interval() -> None:
    evidence = _evidence()
    decision = _decision(evidence)
    with pytest.raises(RelationshipError, match="distinct endpoints"):
        ObservedRelationship.create(
            relationship_id="rel-self",
            source_org="org-acme",
            target_org="org-acme",
            relationship_type="SUPPLIES",
            evidence=evidence,
            decision=decision,
            first_observed_at=NOW,
            last_observed_at=NOW,
        )
    with pytest.raises(RelationshipError, match="interval"):
        ObservedRelationship.create(
            relationship_id="rel-time",
            source_org="org-acme",
            target_org="org-beta",
            relationship_type="SUPPLIES",
            evidence=evidence,
            decision=decision,
            first_observed_at=NOW + timedelta(days=2),
            last_observed_at=NOW + timedelta(days=1),
        )


def test_accredited_relationship_replay_remains_valid() -> None:
    evidence = _evidence()
    decision = _decision(evidence)
    relationship = deserialize_relationship(
        _observed_payload(),
        evidence=evidence,
        decision=decision,
    )
    assert isinstance(relationship, ObservedRelationship)
    assert relationship.evidence_refs == ("ev-rel",)
    assert relationship.currentness is Currentness.CURRENT
