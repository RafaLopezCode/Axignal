"""Explicit synthetic representation fixtures; never use this in runtime code."""

from dataclasses import replace
from datetime import UTC

from domain.evidence.admission import Evidence
from domain.identity import IdentityBindingAuthority, identity_name_key
from domain.identity_binding import IdentityBindingAdmission, IdentityBindingRequest
from domain.representation import TextRepresentation, TextSurface, text_fingerprint


def with_synthetic_representation(evidence: Evidence) -> Evidence:
    """Give existing hand-authored admission tests an immutable synthetic artifact.

    This deliberately models the test's independently stipulated subject
    identity. It does not grant provider output identity or admission authority.
    """
    grounded = evidence.grounded_claim
    if grounded is None:
        raise ValueError("synthetic grounding fixture requires a grounded claim")
    artifact_ref = "synthetic:" + text_fingerprint(evidence.extracted_claim)
    representation = TextRepresentation(
        representation_id=f"synthetic-representation:{evidence.id}",
        observation_id=f"synthetic-observation:{evidence.id}",
        subject_id=evidence.observation_subject_id or grounded.subject_id,
        source_ref=evidence.reference,
        source_type=evidence.source_type,
        observed_at=evidence.observed_at,
        text=evidence.extracted_claim,
        surface=TextSurface.EXTRACTED_TEXT,
        representation_version="synthetic-text-fixture:v1",
        normalization_version="exact:v1",
        source_content_fingerprint=text_fingerprint(evidence.extracted_claim),
        source_observation_fingerprint=text_fingerprint(
            evidence.extracted_claim + evidence.observed_at.isoformat()
        ),
        source_artifact_ref=artifact_ref,
        source_observation_artifact_ref=artifact_ref,
        artifact_ref=artifact_ref,
        document_fingerprint=text_fingerprint(evidence.extracted_claim),
    )
    span = representation.span(0, len(representation.text))
    subject_binding = None
    if identity_name_key(grounded.subject_id) != identity_name_key(grounded.subject_mention):
        subject_binding = IdentityBindingAdmission.bind(
            IdentityBindingRequest(
                entity_id=grounded.subject_id,
                mention=grounded.subject_mention,
                mention_span=representation.unique_span(grounded.subject_mention),
                decision_id=f"synthetic-identity:{evidence.id}",
                evidence_refs=(f"synthetic-identity-evidence:{evidence.id}",),
                authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
                decided_by="synthetic-fixture",
                decided_at=evidence.observed_at.replace(tzinfo=UTC)
                if evidence.observed_at.tzinfo is None
                else evidence.observed_at,
                policy_version="synthetic-fixture:v1",
            ),
            representation,
        )
    return replace(
        evidence,
        representation=representation,
        grounded_claim=replace(
            grounded,
            grounding_version="grounded-claim:v2",
            supporting_span=span,
            subject_binding=subject_binding,
        ),
    )
