"""Evidence admission: the only gate into canonical AXIGNAL state.

Canonical business propositions require proposition-bound admission. Evidence-only
admission remains available for legacy/non-FAXT boundaries that are hardened
separately, but it cannot authorize FAXT creation.

Doctrine: MASTER §2.3, §15.1-15.3, §23, §33; Constitution VI and VIII.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Final

__all__ = [
    "AdmissionDecision",
    "AdmissionRequest",
    "Evidence",
    "EvidenceAdmission",
    "EvidenceAdmissionError",
    "EvidenceAdmissionRequired",
    "SourceAuthority",
]


class EvidenceAdmissionError(Exception):
    """Base error for evidence admission failures."""


class EvidenceAdmissionRequired(EvidenceAdmissionError):
    """Raised when canonical state is requested without valid admission."""


class SourceAuthority(StrEnum):
    """Source authority classes (MASTER §15.3)."""

    OFFICIAL_WEB = "OFFICIAL_WEB"
    REGISTRY = "REGISTRY"
    CERTIFIER = "CERTIFIER"
    CORPORATE_DOCUMENT = "CORPORATE_DOCUMENT"
    COUNTERPARTY = "COUNTERPARTY"
    SPECIALIST = "SPECIALIST"

    USER_SIGNAL = "USER_SIGNAL"
    AGENCY_SIGNAL = "AGENCY_SIGNAL"
    SUBSCRIBER_SIGNAL = "SUBSCRIBER_SIGNAL"


_CANONICAL_AUTHORITIES: Final[frozenset[SourceAuthority]] = frozenset(
    {
        SourceAuthority.OFFICIAL_WEB,
        SourceAuthority.REGISTRY,
        SourceAuthority.CERTIFIER,
        SourceAuthority.CORPORATE_DOCUMENT,
        SourceAuthority.COUNTERPARTY,
        SourceAuthority.SPECIALIST,
    }
)
_ATTENTION_ONLY_AUTHORITIES: Final[frozenset[SourceAuthority]] = frozenset(
    {
        SourceAuthority.USER_SIGNAL,
        SourceAuthority.AGENCY_SIGNAL,
        SourceAuthority.SUBSCRIBER_SIGNAL,
    }
)
_CANONICAL_TOKEN: Final[object] = object()
_EVIDENCE_ONLY_POLICY: Final[str] = "evidence-only:v1"

_PREDICATE_AUTHORITY_POLICY: Final[
    tuple[tuple[frozenset[str], frozenset[SourceAuthority], str], ...]
] = (
    (
        frozenset(
            {
                "capability",
                "manufactures",
                "product",
                "products",
                "has_product",
                "develops_capability",
                "serves_market",
                "operates_in_region",
                "recent_activity",
            }
        ),
        frozenset({SourceAuthority.OFFICIAL_WEB}),
        "predicate-capability:v1",
    ),
    (
        frozenset({"identity", "legal_identity", "registration"}),
        frozenset({SourceAuthority.REGISTRY}),
        "predicate-legal-identity:v1",
    ),
    (
        frozenset({"certification", "certified", "maintains_standard", "supports_standard"}),
        frozenset({SourceAuthority.CERTIFIER}),
        "predicate-certification:v1",
    ),
    (
        frozenset({"structure", "results", "revenue"}),
        frozenset({SourceAuthority.CORPORATE_DOCUMENT}),
        "predicate-corporate:v1",
    ),
    (
        frozenset({"supplier", "customer", "supplies", "relationship"}),
        frozenset({SourceAuthority.COUNTERPARTY}),
        "predicate-counterparty:v1",
    ),
)


def _predicate_policy(
    predicate: str,
) -> tuple[frozenset[SourceAuthority], str] | None:
    normalized = predicate.strip().lower()
    for predicates, authorities, policy_id in _PREDICATE_AUTHORITY_POLICY:
        if normalized in predicates:
            return authorities, policy_id
    return None


@dataclass(frozen=True)
class Evidence:
    """A public, observable source observation (MASTER §36, Evidence)."""

    id: str
    source: str
    source_type: str
    reference: str
    extracted_claim: str
    observed_at: datetime
    authority: SourceAuthority


@dataclass(frozen=True)
class AdmissionRequest:
    """Immutable proposition that a caller asks EvidenceAdmission to authorize."""

    evidence: Evidence
    subject_id: str
    predicate: str
    object_or_value: str
    claim_proposition: str
    policy_id: str = "predicate-authority:auto"

    def __post_init__(self) -> None:
        for value, name in (
            (self.subject_id, "subject_id"),
            (self.predicate, "predicate"),
            (self.object_or_value, "object_or_value"),
            (self.claim_proposition, "claim_proposition"),
            (self.policy_id, "policy_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise EvidenceAdmissionError(f"admission request requires {name}")


@dataclass(frozen=True)
class AdmissionDecision:
    """Cryptographic binding issued only by EvidenceAdmission."""

    admitted: bool
    evidence_id: str
    reason: str
    evidence_digest: str | None = None
    proposition_digest: str | None = None
    policy_id: str | None = None
    _token: object | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    @property
    def is_canonical(self) -> bool:
        return self.admitted and self._token is _CANONICAL_TOKEN

    @property
    def is_proposition_bound(self) -> bool:
        return (
            self.is_canonical
            and self.evidence_digest is not None
            and self.proposition_digest is not None
            and self.policy_id is not None
            and self.policy_id != _EVIDENCE_ONLY_POLICY
        )


def _datetime_text(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise EvidenceAdmissionError("evidence observed_at must be a datetime")
    return value.isoformat(timespec="microseconds")


def _evidence_payload(evidence: Evidence) -> dict[str, str]:
    authority = evidence.authority
    if not isinstance(authority, SourceAuthority):
        raise EvidenceAdmissionError("evidence authority must be a known SourceAuthority")
    return {
        "id": evidence.id,
        "source": evidence.source,
        "source_type": evidence.source_type,
        "reference": evidence.reference,
        "extracted_claim": evidence.extracted_claim,
        "observed_at": _datetime_text(evidence.observed_at),
        "authority": authority.value,
    }


def _digest(payload: dict[str, str]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _evidence_digest(evidence: Evidence) -> str:
    return _digest(_evidence_payload(evidence))


def _proposition_digest(request: AdmissionRequest) -> str:
    return _digest(
        {
            "evidence_digest": _evidence_digest(request.evidence),
            "subject_id": request.subject_id,
            "predicate": request.predicate,
            "object_or_value": request.object_or_value,
            "claim_proposition": request.claim_proposition,
            "policy_id": request.policy_id,
        }
    )


def _canonical_decision(
    *,
    evidence_id: str,
    reason: str,
    evidence_digest: str,
    proposition_digest: str | None,
    policy_id: str,
) -> AdmissionDecision:
    decision = AdmissionDecision(
        admitted=True,
        evidence_id=evidence_id,
        reason=reason,
        evidence_digest=evidence_digest,
        proposition_digest=proposition_digest,
        policy_id=policy_id,
    )
    object.__setattr__(decision, "_token", _CANONICAL_TOKEN)
    return decision


class EvidenceAdmission:
    """Deterministic admission gate for canonical state."""

    @staticmethod
    def _validate_evidence(evidence: Evidence) -> str | None:
        if not isinstance(evidence, Evidence):
            raise EvidenceAdmissionError("admission requires an Evidence instance")
        if not evidence.id.strip():
            return "evidence has no id"
        if not evidence.source.strip():
            return "evidence has no source"
        if not evidence.source_type.strip():
            return "evidence has no source type"
        if not isinstance(evidence.authority, SourceAuthority):
            return "evidence has unknown source authority"
        if evidence.authority in _ATTENTION_ONLY_AUTHORITIES:
            return "attention signals cannot establish canonical truth"
        if evidence.authority not in _CANONICAL_AUTHORITIES:
            return "source authority is not authorized for canonical admission"
        if not evidence.reference.strip():
            return "evidence has no reference"
        if not evidence.extracted_claim.strip():
            return "evidence has no extracted claim"
        if not isinstance(evidence.observed_at, datetime):
            return "evidence has invalid observed_at"
        return None

    @staticmethod
    def admit(evidence: Evidence) -> AdmissionDecision:
        """Admit evidence identity/content only; cannot authorize a FAXT."""

        reason = EvidenceAdmission._validate_evidence(evidence)
        if reason is not None:
            evidence_id = evidence.id if isinstance(evidence, Evidence) else ""
            return AdmissionDecision(False, evidence_id, reason)
        return _canonical_decision(
            evidence_id=evidence.id,
            reason="evidence admitted; proposition binding required for canonical FAXT",
            evidence_digest=_evidence_digest(evidence),
            proposition_digest=None,
            policy_id=_EVIDENCE_ONLY_POLICY,
        )

    @staticmethod
    def admit_claim(request: AdmissionRequest) -> AdmissionDecision:
        """Admit one exact proposition over one exact Evidence value."""

        if not isinstance(request, AdmissionRequest):
            raise EvidenceAdmissionError("claim admission requires an AdmissionRequest")
        evidence = request.evidence
        reason = EvidenceAdmission._validate_evidence(evidence)
        if reason is not None:
            return AdmissionDecision(False, evidence.id, reason)
        if request.claim_proposition.strip() != evidence.extracted_claim.strip():
            return AdmissionDecision(
                False,
                evidence.id,
                "claim proposition does not exactly match extracted evidence claim",
            )
        policy = _predicate_policy(request.predicate)
        if policy is None:
            return AdmissionDecision(
                False,
                evidence.id,
                "predicate has no explicit source-authority admission policy",
            )
        allowed_authorities, policy_id = policy
        if evidence.authority not in allowed_authorities:
            return AdmissionDecision(
                False,
                evidence.id,
                "source authority is not authorized for this predicate",
            )
        effective_request = AdmissionRequest(
            evidence=request.evidence,
            subject_id=request.subject_id,
            predicate=request.predicate,
            object_or_value=request.object_or_value,
            claim_proposition=request.claim_proposition,
            policy_id=policy_id,
        )
        return _canonical_decision(
            evidence_id=evidence.id,
            reason="proposition admitted",
            evidence_digest=_evidence_digest(evidence),
            proposition_digest=_proposition_digest(effective_request),
            policy_id=policy_id,
        )

    @staticmethod
    def require(decision: AdmissionDecision) -> None:
        """Raise unless decision is an authentic EvidenceAdmission decision."""

        if not isinstance(decision, AdmissionDecision):
            raise EvidenceAdmissionRequired("canonical state requires an AdmissionDecision")
        if not decision.is_canonical:
            raise EvidenceAdmissionRequired(
                "canonical state requires evidence admitted by EvidenceAdmission"
            )

    @staticmethod
    def require_claim(decision: AdmissionDecision, request: AdmissionRequest) -> None:
        """Require an exact proposition-bound admission decision."""

        EvidenceAdmission.require(decision)
        if not isinstance(request, AdmissionRequest):
            raise EvidenceAdmissionRequired("canonical FAXT requires an AdmissionRequest")
        if not decision.is_proposition_bound:
            raise EvidenceAdmissionRequired(
                "canonical FAXT requires proposition-bound evidence admission"
            )
        policy = _predicate_policy(request.predicate)
        if policy is None:
            raise EvidenceAdmissionRequired(
                "canonical FAXT predicate has no admission authority policy"
            )
        allowed_authorities, policy_id = policy
        if request.evidence.authority not in allowed_authorities:
            raise EvidenceAdmissionRequired(
                "canonical FAXT source authority does not match predicate policy"
            )
        effective_request = AdmissionRequest(
            evidence=request.evidence,
            subject_id=request.subject_id,
            predicate=request.predicate,
            object_or_value=request.object_or_value,
            claim_proposition=request.claim_proposition,
            policy_id=policy_id,
        )
        expected_evidence_digest = _evidence_digest(request.evidence)
        expected_proposition_digest = _proposition_digest(effective_request)
        if decision.evidence_id != request.evidence.id:
            raise EvidenceAdmissionRequired("admission evidence identity does not match request")
        if decision.evidence_digest != expected_evidence_digest:
            raise EvidenceAdmissionRequired("admission evidence content does not match request")
        if decision.policy_id != policy_id:
            raise EvidenceAdmissionRequired("admission policy does not match predicate policy")
        if decision.proposition_digest != expected_proposition_digest:
            raise EvidenceAdmissionRequired("admission proposition does not match request")
