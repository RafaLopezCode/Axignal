"""Evidence admission: the only gate into canonical AXIGNAL state.

A claim does not become canonical automatically. Canonical FAXT and OBSERVED
Relationship state may only be produced after an ``AdmissionDecision`` issued by
``EvidenceAdmission``. User, agency and subscriber signals define attention,
never canonical truth.

Doctrine: MASTER §2.3 (the mirror does not edit the storefront), §15.1 (CLAIM !=
WRITE), §23 (anti-poisoning), §33 (agencies cannot configure canonical truth).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Final

__all__ = [
    "AdmissionDecision",
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
    """Source authority classes (MASTER §15.3).

    The first block can support canonical state. The second block only ever
    directs attention and can never establish canonical truth.
    """

    OFFICIAL_WEB = "OFFICIAL_WEB"
    REGISTRY = "REGISTRY"
    CERTIFIER = "CERTIFIER"
    CORPORATE_DOCUMENT = "CORPORATE_DOCUMENT"
    COUNTERPARTY = "COUNTERPARTY"
    SPECIALIST = "SPECIALIST"

    # Attention-only signals. Non-canonical by construction.
    USER_SIGNAL = "USER_SIGNAL"
    AGENCY_SIGNAL = "AGENCY_SIGNAL"
    SUBSCRIBER_SIGNAL = "SUBSCRIBER_SIGNAL"


_ATTENTION_ONLY_AUTHORITIES: Final[frozenset[SourceAuthority]] = frozenset(
    {
        SourceAuthority.USER_SIGNAL,
        SourceAuthority.AGENCY_SIGNAL,
        SourceAuthority.SUBSCRIBER_SIGNAL,
    }
)

_CANONICAL_TOKEN: Final[object] = object()


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
class AdmissionDecision:
    """Proof that a piece of evidence was admitted.

    A decision is canonical only when its private token is the module sentinel,
    which only ``EvidenceAdmission`` can supply. Hand-built decisions are
    therefore never canonical.
    """

    admitted: bool
    evidence_id: str
    reason: str
    _token: object | None = field(default=None, repr=False, compare=False)

    @property
    def is_canonical(self) -> bool:
        return self.admitted and self._token is _CANONICAL_TOKEN


class EvidenceAdmission:
    """Deterministic admission gate for canonical state."""

    @staticmethod
    def admit(evidence: Evidence) -> AdmissionDecision:
        if not isinstance(evidence, Evidence):
            raise EvidenceAdmissionError("admission requires an Evidence instance")
        if evidence.authority in _ATTENTION_ONLY_AUTHORITIES:
            return AdmissionDecision(
                admitted=False,
                evidence_id=evidence.id,
                reason="attention signals cannot establish canonical truth",
            )
        if not evidence.reference.strip():
            return AdmissionDecision(
                admitted=False,
                evidence_id=evidence.id,
                reason="evidence has no reference",
            )
        if not evidence.extracted_claim.strip():
            return AdmissionDecision(
                admitted=False,
                evidence_id=evidence.id,
                reason="evidence has no extracted claim",
            )
        return AdmissionDecision(
            admitted=True,
            evidence_id=evidence.id,
            reason="admitted",
            _token=_CANONICAL_TOKEN,
        )

    @staticmethod
    def require(decision: AdmissionDecision) -> None:
        """Raise unless ``decision`` is a canonical admission."""

        if not isinstance(decision, AdmissionDecision):
            raise EvidenceAdmissionRequired("canonical state requires an AdmissionDecision")
        if not decision.is_canonical:
            raise EvidenceAdmissionRequired(
                "canonical state requires evidence admitted by EvidenceAdmission"
            )
