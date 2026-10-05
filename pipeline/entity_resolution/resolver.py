"""Deterministic canonical entity resolution.

The resolver may establish identity only from explicit governed signals:
verified external identifiers first, then unique exact canonical/alias names.
Ambiguity never becomes a winner and subscriber context is deliberately absent.

Doctrine: MASTER §14, §35, §36, §46.6, §46.11-13; FR-23.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.identity import GovernedIdentityName, IdentityBindingAuthority, identity_name_key
from domain.identity_binding import (
    GovernedIdentityBinding,
    IdentityBindingAdmission,
    IdentityBindingRequest,
)
from domain.representation import RepresentationSpan, TextRepresentation


class ResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, order=True)
class VerifiedIdentifier:
    scheme: str
    value: str
    authority: str

    def __post_init__(self) -> None:
        if not self.scheme.strip() or not self.value.strip() or not self.authority.strip():
            raise ValueError("verified identifier requires scheme, value and authority")

    @property
    def key(self) -> tuple[str, str, str]:
        return (
            unicodedata.normalize("NFC", self.scheme.strip().upper()),
            (
                self.value.strip().upper()
                if self.scheme.strip().upper() == "LEI"
                else unicodedata.normalize("NFC", self.value.strip())
            ),
            unicodedata.normalize("NFC", self.authority.strip().upper()),
        )


@dataclass(frozen=True)
class ResolutionCandidate:
    """A canonical organization candidate and its governed identity signals."""

    organization_id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    verified_identifiers: tuple[VerifiedIdentifier, ...] = ()
    name_history: tuple[GovernedIdentityName, ...] = ()

    def __post_init__(self) -> None:
        if not self.organization_id.strip() or not self.canonical_name.strip():
            raise ValueError("resolution candidate identity is required")
        if any(not alias.strip() for alias in self.aliases):
            raise ValueError("resolution candidate aliases must be non-empty")
        if len(self.verified_identifiers) != len(set(self.verified_identifiers)):
            raise ValueError("resolution candidate identifiers must be unique")
        if any(record.entity_id != self.organization_id for record in self.name_history):
            raise ValueError("identity name history cannot cross organizations")
        if len({record.decision_id for record in self.name_history}) != len(self.name_history):
            raise ValueError("identity name history decisions must be unique")


@dataclass(frozen=True)
class ResolutionResult:
    status: ResolutionStatus
    reason_code: str
    candidate: ResolutionCandidate | None = None
    candidates: tuple[ResolutionCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not self.reason_code.strip():
            raise ValueError("resolution result reason code is required")
        if self.status is ResolutionStatus.RESOLVED:
            if self.candidate is None or self.candidates != (self.candidate,):
                raise ValueError("resolved identity requires exactly one candidate")
        elif self.candidate is not None:
            raise ValueError("non-resolved identity cannot expose a selected candidate")
        if self.status is ResolutionStatus.AMBIGUOUS and len(self.candidates) < 2:
            raise ValueError("ambiguous identity requires at least two candidates")
        if self.status is ResolutionStatus.UNRESOLVED and self.candidates:
            raise ValueError("unresolved identity cannot expose candidates")


class ExactNameResolver:
    """Deterministic resolver with explicit ambiguity preservation.

    The historical class name is retained for compatibility. resolve() remains
    a conservative convenience API: it returns a candidate only when
    resolve_identity() reaches RESOLVED. New code should consume the richer
    result directly.
    """

    def __init__(self, candidates: Iterable[ResolutionCandidate]) -> None:
        by_name: dict[str, list[ResolutionCandidate]] = {}
        by_identifier: dict[tuple[str, str, str], list[ResolutionCandidate]] = {}
        seen_organizations: set[str] = set()
        history: dict[str, list[tuple[ResolutionCandidate, GovernedIdentityName]]] = {}

        for candidate in candidates:
            if candidate.organization_id in seen_organizations:
                raise ValueError("duplicate organization id in resolution authority")
            seen_organizations.add(candidate.organization_id)

            for raw_name in (candidate.canonical_name, *candidate.aliases):
                key = identity_name_key(raw_name)
                if not key:
                    continue
                bucket = by_name.setdefault(key, [])
                if candidate not in bucket:
                    bucket.append(candidate)

            for record in candidate.name_history:
                history.setdefault(identity_name_key(record.name), []).append((candidate, record))

            for identifier in candidate.verified_identifiers:
                bucket = by_identifier.setdefault(identifier.key, [])
                if candidate not in bucket:
                    bucket.append(candidate)

        self._by_name = {
            key: tuple(sorted(value, key=lambda item: item.organization_id))
            for key, value in by_name.items()
        }
        self._by_identifier = {
            key: tuple(sorted(value, key=lambda item: item.organization_id))
            for key, value in by_identifier.items()
        }
        self._history = history

    def resolve_identity(
        self,
        name: str,
        *,
        verified_identifiers: tuple[VerifiedIdentifier, ...] = (),
        as_of: datetime | None = None,
    ) -> ResolutionResult:
        if as_of is not None and as_of.tzinfo is None:
            raise ValueError("identity resolution as-of must be timezone-aware")
        if not name.strip() and not verified_identifiers:
            return ResolutionResult(
                ResolutionStatus.UNRESOLVED,
                "NO_IDENTITY_SIGNAL",
            )

        if verified_identifiers:
            matches: dict[str, ResolutionCandidate] = {}
            collision = False
            missing = False
            for identifier in verified_identifiers:
                candidates = self._by_identifier.get(identifier.key, ())
                missing = missing or not candidates
                if len(candidates) > 1:
                    collision = True
                for candidate in candidates:
                    matches[candidate.organization_id] = candidate

            ordered = tuple(sorted(matches.values(), key=lambda item: item.organization_id))
            if collision or len(ordered) > 1:
                return ResolutionResult(
                    ResolutionStatus.AMBIGUOUS,
                    "VERIFIED_IDENTIFIER_COLLISION",
                    candidates=ordered,
                )
            if len(ordered) == 1:
                if missing:
                    return ResolutionResult(
                        ResolutionStatus.UNRESOLVED, "VERIFIED_IDENTIFIER_NOT_FOUND"
                    )
                return ResolutionResult(
                    ResolutionStatus.RESOLVED,
                    "VERIFIED_IDENTIFIER_EXACT",
                    candidate=ordered[0],
                    candidates=ordered,
                )
            return ResolutionResult(
                ResolutionStatus.UNRESOLVED,
                "VERIFIED_IDENTIFIER_NOT_FOUND",
            )

        key = identity_name_key(name)
        matching = {item.organization_id: item for item in self._by_name.get(key, ())}
        history = self._history.get(key, ())
        if history and as_of is None:
            return ResolutionResult(ResolutionStatus.UNRESOLVED, "NAME_HISTORY_REQUIRES_AS_OF")
        for candidate, record in history:
            if as_of is not None and record.applies_at(as_of):
                matching[candidate.organization_id] = candidate
        candidates = tuple(sorted(matching.values(), key=lambda item: item.organization_id))
        if len(candidates) == 1:
            candidate = candidates[0]
            return ResolutionResult(
                ResolutionStatus.RESOLVED,
                "UNIQUE_CANONICAL_OR_ALIAS_NAME",
                candidate=candidate,
                candidates=(candidate,),
            )
        if len(candidates) > 1:
            return ResolutionResult(
                ResolutionStatus.AMBIGUOUS,
                "NAME_OR_ALIAS_COLLISION",
                candidates=candidates,
            )
        return ResolutionResult(
            ResolutionStatus.UNRESOLVED,
            "NO_GOVERNED_MATCH",
        )

    def resolve(self, name: str) -> ResolutionCandidate | None:
        result = self.resolve_identity(name)
        return result.candidate if result.status is ResolutionStatus.RESOLVED else None

    def bind_mention(
        self,
        *,
        representation: TextRepresentation,
        mention_span: RepresentationSpan,
        decision_id: str,
        evidence_refs: tuple[str, ...],
        authority: IdentityBindingAuthority,
        decided_by: str,
        decided_at: datetime,
        as_of: datetime,
        verified_identifiers: tuple[VerifiedIdentifier, ...] = (),
    ) -> GovernedIdentityBinding:
        """Bind only a resolved governed identity; a collision cannot issue a receipt."""
        mention = mention_span.extract(representation)
        result = self.resolve_identity(
            mention, as_of=as_of, verified_identifiers=verified_identifiers
        )
        if result.status is not ResolutionStatus.RESOLVED or result.candidate is None:
            raise ValueError(f"identity binding requires RESOLVED identity: {result.reason_code}")
        history_refs = tuple(
            ref
            for record in result.candidate.name_history
            if identity_name_key(record.name) == identity_name_key(mention)
            and record.applies_at(as_of)
            for ref in (record.decision_id, *record.evidence_refs)
        )
        return IdentityBindingAdmission.bind(
            IdentityBindingRequest(
                entity_id=result.candidate.organization_id,
                mention=mention,
                mention_span=mention_span,
                decision_id=decision_id,
                evidence_refs=tuple(dict.fromkeys((*evidence_refs, *history_refs))),
                authority=authority,
                decided_by=decided_by,
                decided_at=decided_at,
                policy_version="exact-identity-binding:v1",
            ),
            representation,
        )
