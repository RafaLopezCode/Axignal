"""Global legal-name identities materialized only from admitted registry evidence."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol

from application.identity_resolution.governance import IdentitySubjectState
from application.subscriber_portfolio.models import (
    OrganizationIdentityPending,
    OrganizationResolution,
)
from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    EvidenceAdmission,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId, OrganizationId
from domain.organizations.model import Organization
from pipeline.entity_resolution.resolver import (
    ExactNameResolver,
    ResolutionCandidate,
    ResolutionStatus,
)
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore


class IdentityArtifactIntegrity(Protocol):
    def verify(self, reference: str) -> bool | None: ...


class OrganizationMaterializationError(ValueError):
    """Safe conflict/authority error; contains no submitted locator or evidence body."""


class SqliteCanonicalOrganizationStore:
    """No Tenant column, no caller-supplied canonical-name mutation operation."""

    def __init__(
        self,
        path: Path,
        *,
        integrity: IdentityArtifactIntegrity,
        governance: SqliteIdentityGovernanceStore,
    ) -> None:
        self.path = path
        self._integrity = integrity
        self._governance = governance
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS canonical_legal_identities (
                organization_id TEXT PRIMARY KEY, canonical_name TEXT NOT NULL,
                evidence_ref TEXT NOT NULL, evidence_digest TEXT NOT NULL,
                proposition_digest TEXT NOT NULL, policy_id TEXT NOT NULL,
                observed_at TEXT NOT NULL, artifact_refs TEXT NOT NULL,
                receipt_fingerprint TEXT NOT NULL)""")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def register(self, request: AdmissionRequest, decision: AdmissionDecision) -> bool:
        """Called by a governed registry intake after independent identity binding."""
        if (
            request.predicate != "legal_identity"
            or request.evidence.authority is not SourceAuthority.REGISTRY
        ):
            raise OrganizationMaterializationError("exact registry legal-name admission required")
        EvidenceAdmission.require_claim(decision, request)
        representation = request.evidence.representation
        if representation is None:
            raise OrganizationMaterializationError("representation required")
        references = tuple(
            dict.fromkeys(
                (
                    representation.source_artifact_ref,
                    representation.source_observation_artifact_ref,
                    representation.artifact_ref,
                )
            )
        )
        if any(self._integrity.verify(reference) is not True for reference in references):
            raise OrganizationMaterializationError("identity artifact integrity unconfirmed")
        faxt = FAXT.create(
            faxt_id=FaxtId(
                "faxt:identity:" + hashlib.sha256(request.evidence.id.encode()).hexdigest()
            ),
            subject_id=request.subject_id,
            predicate=request.predicate,
            object_or_value=request.object_or_value,
            evidence=request.evidence,
            decision=decision,
            claim_proposition=request.claim_proposition,
            epistemic_state=EpistemicState.OBSERVED,
            currentness=Currentness.UNKNOWN,
        )
        receipt = {
            "organization_id": faxt.subject_id,
            "canonical_name": faxt.object_or_value,
            "evidence_ref": request.evidence.id,
            "evidence_digest": decision.evidence_digest,
            "proposition_digest": decision.proposition_digest,
            "policy_id": decision.policy_id,
            "observed_at": faxt.observed_at.isoformat(),
            "artifact_refs": json.dumps(references),
        }
        fingerprint = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        inserted = False
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT receipt_fingerprint FROM canonical_legal_identities WHERE organization_id = ?",
                (faxt.subject_id,),
            ).fetchone()
            if existing is not None:
                if existing["receipt_fingerprint"] != fingerprint:
                    raise OrganizationMaterializationError(
                        "identity requires governed reevaluation"
                    )
            else:
                connection.execute(
                    """INSERT INTO canonical_legal_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (*receipt.values(), fingerprint),
                )
                inserted = True
        self._governance.seed_subject(OrganizationId(faxt.subject_id))
        return inserted

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        pointer = self._governance.current(organization_id)
        if (
            pointer is None
            or pointer.state is not IdentitySubjectState.ACTIVE
            or pointer.requires_revalidation
        ):
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM canonical_legal_identities WHERE organization_id = ?",
                (organization_id,),
            ).fetchone()
        if row is None:
            return None
        receipt = {
            key: row[key]
            for key in (
                "organization_id",
                "canonical_name",
                "evidence_ref",
                "evidence_digest",
                "proposition_digest",
                "policy_id",
                "observed_at",
                "artifact_refs",
            )
        }
        fingerprint = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        if fingerprint != row["receipt_fingerprint"]:
            raise OrganizationMaterializationError("identity receipt integrity failure")
        references = json.loads(str(row["artifact_refs"]))
        if (
            not isinstance(references, list)
            or not references
            or any(
                not isinstance(reference, str) or self._integrity.verify(reference) is not True
                for reference in references
            )
        ):
            return None
        return Organization(
            organization_id,
            str(row["canonical_name"]),
            discovered_at=datetime.fromisoformat(str(row["observed_at"])),
        )

    def resolve(self, locator: str) -> OrganizationResolution:
        """Exact existing canonical identity only; no inference from a submitted URL."""
        with self._connect() as connection:
            ids = tuple(
                OrganizationId(str(row[0]))
                for row in connection.execute(
                    "SELECT organization_id FROM canonical_legal_identities ORDER BY organization_id"
                )
            )
        organizations = tuple(
            item
            for organization_id in ids
            if (item := self.get_organization(organization_id)) is not None
        )
        resolver = ExactNameResolver(
            ResolutionCandidate(item.id, item.canonical_name) for item in organizations
        )
        resolution = resolver.resolve_identity(locator)
        if resolution.status is not ResolutionStatus.RESOLVED or resolution.candidate is None:
            return OrganizationIdentityPending(resolution.reason_code)
        organization = self.get_organization(OrganizationId(resolution.candidate.organization_id))
        return (
            organization
            if organization is not None
            else OrganizationIdentityPending("IDENTITY_REVALIDATION_REQUIRED")
        )
