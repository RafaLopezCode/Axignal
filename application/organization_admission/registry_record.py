"""Build a registry record's propositions from one immutable registry document.

The document bytes and observation are stored content-addressed; each proposition
(legal name, registration identifier, registry-recorded website) is grounded in one
exact, unique excerpt of that document. Nothing here admits anything: the result is
handed to EvidenceAdmission, which re-checks grounding, authority and digests.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.organization_admission.service import (
    RegistryIdentityRecord,
    organization_id_for,
    registration_value,
)
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    GroundedClaim,
    SourceAuthority,
)
from domain.representation import TextRepresentation, TextSurface, text_fingerprint

_PREDICATES = ("legal_identity", "registration", "official_website")


class ArtifactWriter(Protocol):
    def put_bytes(self, data: bytes) -> str: ...
    def put_json(self, value: object) -> str: ...


@dataclass(frozen=True, slots=True)
class RegistryAttestation:
    """One registry statement: the exact excerpt and the mentions it contains."""

    predicate: str
    value: str
    excerpt: str
    subject_mention: str
    predicate_mention: str
    object_mention: str

    def __post_init__(self) -> None:
        if self.predicate not in _PREDICATES:
            raise ValueError("unsupported registry predicate")


def registry_record(
    *,
    document: str,
    source_ref: str,
    observed_at: datetime,
    artifacts: ArtifactWriter,
    identifier: tuple[str, str, str],
    attestations: Sequence[RegistryAttestation],
) -> RegistryIdentityRecord:
    if observed_at.tzinfo is None:
        raise ValueError("registry observation time must be timezone-aware")
    subject = organization_id_for(*identifier)
    body = artifacts.put_bytes(document.encode("utf-8"))
    observation = artifacts.put_json(
        {"source": source_ref, "body": body, "observed_at": observed_at.isoformat()}
    )
    surface = artifacts.put_json({"text": document, "body": body, "observation": observation})
    representation = TextRepresentation(
        representation_id=f"repr:registry:{body}",
        representation_version="registry-document:v1",
        subject_id=subject,
        source_ref=source_ref,
        source_type="REGISTRY_RECORD",
        observation_id=f"observation:registry:{observation}",
        observed_at=observed_at,
        surface=TextSurface.STRUCTURED_DATA,
        text=document,
        normalization_version="registry-document:v1",
        source_content_fingerprint=text_fingerprint(document),
        source_observation_fingerprint=observation,
        source_artifact_ref=body,
        source_observation_artifact_ref=observation,
        artifact_ref=surface,
        document_fingerprint=text_fingerprint(document),
    )
    requests: dict[str, list[AdmissionRequest]] = {name: [] for name in _PREDICATES}
    for item in attestations:
        # unique_span refuses a missing or repeated excerpt: no ambiguous grounding.
        span = representation.unique_span(item.excerpt)
        value = (
            registration_value(*_split(item.value))
            if item.predicate == "registration"
            else item.value
        )
        digest = hashlib.sha256(
            "|".join((body, item.predicate, value, item.excerpt)).encode("utf-8")
        ).hexdigest()[:32]
        evidence = Evidence(
            f"evidence:registry:{digest}",
            "Registry record",
            "REGISTRY_RECORD",
            source_ref,
            item.excerpt,
            observed_at,
            SourceAuthority.REGISTRY,
            observation_subject_id=subject,
            grounded_claim=GroundedClaim(
                subject,
                item.predicate,
                value,
                item.subject_mention,
                item.predicate_mention,
                item.object_mention,
                item.excerpt,
                supporting_span=span,
            ),
            representation=representation,
        )
        requests[item.predicate].append(
            AdmissionRequest(evidence, subject, item.predicate, value, item.excerpt)
        )
    if len(requests["legal_identity"]) != 1:
        raise ValueError("a registry record states exactly one legal name")
    return RegistryIdentityRecord(
        requests["legal_identity"][0],
        tuple(requests["registration"]),
        tuple(requests["official_website"]),
    )


def _split(value: str) -> tuple[str, str, str]:
    parts = value.split("|")
    if len(parts) != 3:
        raise ValueError("registration must be SCHEME|AUTHORITY|VALUE")
    return parts[0], parts[1], parts[2]
