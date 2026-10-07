"""Global legal-name identities materialized only from admitted registry evidence."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol

from application.identity_resolution.governance import IdentitySubjectState
from application.organization_admission.locator import LocatorError, public_domain
from application.organization_admission.service import (
    AdmittedProposition,
    IdentityConflictError,
    organization_id_for,
    parse_registration,
    registration_value,
)
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
from domain.identity import FaxtId, OrganizationId, identity_name_key
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
            # Verified registry identifiers and registry-recorded websites. Primary keys
            # make "one key, two Organizations" impossible, also under concurrency.
            connection.execute("""CREATE TABLE IF NOT EXISTS canonical_identifiers (
                scheme TEXT NOT NULL, authority TEXT NOT NULL, value TEXT NOT NULL,
                organization_id TEXT NOT NULL, evidence_ref TEXT NOT NULL,
                evidence_digest TEXT NOT NULL, proposition_digest TEXT NOT NULL,
                policy_id TEXT NOT NULL, observed_at TEXT NOT NULL,
                PRIMARY KEY (scheme, authority, value))""")
            connection.execute("""CREATE TABLE IF NOT EXISTS canonical_websites (
                domain TEXT PRIMARY KEY, organization_id TEXT NOT NULL,
                evidence_ref TEXT NOT NULL, evidence_digest TEXT NOT NULL,
                proposition_digest TEXT NOT NULL, policy_id TEXT NOT NULL,
                observed_at TEXT NOT NULL)""")

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

    def _verified(self, proposition: AdmittedProposition, predicate: str) -> None:
        request, decision = proposition.request, proposition.decision
        if (
            request.predicate != predicate
            or request.evidence.authority is not SourceAuthority.REGISTRY
        ):
            raise OrganizationMaterializationError("registry admission required")
        EvidenceAdmission.require_claim(decision, request)
        representation = request.evidence.representation
        if representation is None:
            raise OrganizationMaterializationError("representation required")
        references = {
            representation.source_artifact_ref,
            representation.source_observation_artifact_ref,
            representation.artifact_ref,
        }
        if any(self._integrity.verify(reference) is not True for reference in references):
            raise OrganizationMaterializationError("identity artifact integrity unconfirmed")

    def admit(
        self,
        legal_name: AdmittedProposition,
        registrations: tuple[AdmittedProposition, ...],
        official_websites: tuple[AdmittedProposition, ...],
    ) -> tuple[OrganizationId, bool]:
        """Admit one registry-attested identity with its keys, atomically.

        Called by the organization admission service with EvidenceAdmission decisions.
        An identity already admitted is reused, never rewritten; a key held by another
        Organization, or a different admitted legal name, is a conflict.
        """

        subject = OrganizationId(legal_name.request.subject_id)
        propositions = (legal_name, *registrations, *official_websites)
        if any(item.request.subject_id != subject for item in propositions):
            raise OrganizationMaterializationError("one subject per admission")
        if not registrations:
            raise OrganizationMaterializationError("a verified registry identifier is required")
        try:
            identifiers = [
                (parse_registration(item.request.object_or_value), item) for item in registrations
            ]
            websites = [
                (public_domain(item.request.object_or_value), item) for item in official_websites
            ]
        except (ValueError, LocatorError) as exc:
            raise OrganizationMaterializationError("invalid identity key") from exc
        if subject != organization_id_for(*min(key for key, _ in identifiers)):
            raise OrganizationMaterializationError("subject is not derived from its identifier")
        if len({key for key, _ in identifiers}) != len(identifiers) or len(
            {key for key, _ in websites}
        ) != len(websites):
            raise OrganizationMaterializationError("duplicate identity key")
        self._verified(legal_name, "legal_identity")
        for item in registrations:
            self._verified(item, "registration")
        for item in official_websites:
            self._verified(item, "official_website")
        FAXT.create(
            faxt_id=FaxtId(
                "faxt:identity:"
                + hashlib.sha256(legal_name.request.evidence.id.encode()).hexdigest()
            ),
            subject_id=subject,
            predicate=legal_name.request.predicate,
            object_or_value=legal_name.request.object_or_value,
            evidence=legal_name.request.evidence,
            decision=legal_name.decision,
            claim_proposition=legal_name.request.claim_proposition,
            epistemic_state=EpistemicState.OBSERVED,
            currentness=Currentness.UNKNOWN,
        )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for (scheme, authority, value), _ in identifiers:
                row = connection.execute(
                    """SELECT organization_id FROM canonical_identifiers
                       WHERE scheme = ? AND authority = ? AND value = ?""",
                    (scheme, authority, value),
                ).fetchone()
                if row is not None and row[0] != subject:
                    raise IdentityConflictError("IDENTIFIER_HELD_BY_ANOTHER_ORGANIZATION")
            for domain, _ in websites:
                row = connection.execute(
                    "SELECT organization_id FROM canonical_websites WHERE domain = ?", (domain,)
                ).fetchone()
                if row is not None and row[0] != subject:
                    raise IdentityConflictError("WEBSITE_HELD_BY_ANOTHER_ORGANIZATION")
            existing = connection.execute(
                "SELECT canonical_name FROM canonical_legal_identities WHERE organization_id = ?",
                (subject,),
            ).fetchone()
            created = existing is None
            if existing is not None and identity_name_key(str(existing[0])) != identity_name_key(
                legal_name.request.object_or_value
            ):
                # Never silently replace an admitted identity: reevaluation is governed.
                raise IdentityConflictError("ADMITTED_LEGAL_NAME_DIFFERS")
            if created:
                connection.execute(
                    "INSERT INTO canonical_legal_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    self._legal_receipt(legal_name),
                )
            for (scheme, authority, value), item in identifiers:
                connection.execute(
                    "INSERT OR IGNORE INTO canonical_identifiers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (scheme, authority, value, *self._key_provenance(subject, item)),
                )
            for domain, item in websites:
                connection.execute(
                    "INSERT OR IGNORE INTO canonical_websites VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (domain, *self._key_provenance(subject, item)),
                )
        # Seeding is idempotent; a crash before it is healed by the next replay.
        self._governance.seed_subject(subject)
        return subject, created

    @staticmethod
    def _key_provenance(
        subject: OrganizationId, item: AdmittedProposition
    ) -> tuple[str, str, str, str, str, str]:
        decision = item.decision
        return (
            str(subject),
            item.request.evidence.id,
            str(decision.evidence_digest),
            str(decision.proposition_digest),
            str(decision.policy_id),
            item.request.evidence.observed_at.isoformat(),
        )

    @staticmethod
    def _legal_receipt(legal_name: AdmittedProposition) -> tuple[str, ...]:
        request, decision = legal_name.request, legal_name.decision
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
        receipt = {
            "organization_id": request.subject_id,
            "canonical_name": request.object_or_value,
            "evidence_ref": request.evidence.id,
            "evidence_digest": decision.evidence_digest,
            "proposition_digest": decision.proposition_digest,
            "policy_id": decision.policy_id,
            "observed_at": request.evidence.observed_at.isoformat(),
            "artifact_refs": json.dumps(references),
        }
        fingerprint = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
        return (*(str(value) for value in receipt.values()), fingerprint)

    def organization_by_identifier(
        self, scheme: str, authority: str, value: str
    ) -> OrganizationId | None:
        key = parse_registration(registration_value(scheme, authority, value))
        with self._connect() as connection:
            row = connection.execute(
                """SELECT organization_id FROM canonical_identifiers
                   WHERE scheme = ? AND authority = ? AND value = ?""",
                key,
            ).fetchone()
        return None if row is None else OrganizationId(str(row[0]))

    def organization_by_domain(self, domain: str) -> OrganizationId | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT organization_id FROM canonical_websites WHERE domain = ?", (domain,)
            ).fetchone()
        return None if row is None else OrganizationId(str(row[0]))

    def organizations_by_name(self, name: str) -> tuple[OrganizationId, ...]:
        """Every live identity whose exact admitted legal name equals ``name``."""
        key = identity_name_key(name)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT organization_id, canonical_name FROM canonical_legal_identities"
            ).fetchall()
        return tuple(
            sorted(
                OrganizationId(str(row[0]))
                for row in rows
                if identity_name_key(str(row[1])) == key
                and self.get_organization(OrganizationId(str(row[0]))) is not None
            )
        )

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
