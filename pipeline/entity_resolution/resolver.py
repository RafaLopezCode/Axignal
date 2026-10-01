"""Deterministic canonical entity resolution.

The resolver may establish identity only from explicit governed signals:
verified external identifiers first, then unique exact canonical/alias names.
Ambiguity never becomes a winner and subscriber context is deliberately absent.

Doctrine: MASTER §14, §35, §36, §46.6, §46.11-13; FR-23.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from pipeline.normalization.text import normalize_name


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
            self.scheme.strip().upper(),
            self.value.strip().upper(),
            self.authority.strip().upper(),
        )


@dataclass(frozen=True)
class ResolutionCandidate:
    """A canonical organization candidate and its governed identity signals."""

    organization_id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    verified_identifiers: tuple[VerifiedIdentifier, ...] = ()

    def __post_init__(self) -> None:
        if not self.organization_id.strip() or not self.canonical_name.strip():
            raise ValueError("resolution candidate identity is required")
        if any(not alias.strip() for alias in self.aliases):
            raise ValueError("resolution candidate aliases must be non-empty")
        if len(self.verified_identifiers) != len(set(self.verified_identifiers)):
            raise ValueError("resolution candidate identifiers must be unique")


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

        for candidate in candidates:
            if candidate.organization_id in seen_organizations:
                raise ValueError("duplicate organization id in resolution authority")
            seen_organizations.add(candidate.organization_id)

            for raw_name in (candidate.canonical_name, *candidate.aliases):
                key = normalize_name(raw_name)
                if not key:
                    continue
                bucket = by_name.setdefault(key, [])
                if candidate not in bucket:
                    bucket.append(candidate)

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

    def resolve_identity(
        self,
        name: str,
        *,
        verified_identifiers: tuple[VerifiedIdentifier, ...] = (),
    ) -> ResolutionResult:
        if not name.strip() and not verified_identifiers:
            return ResolutionResult(
                ResolutionStatus.UNRESOLVED,
                "NO_IDENTITY_SIGNAL",
            )

        if verified_identifiers:
            matches: dict[str, ResolutionCandidate] = {}
            collision = False
            for identifier in verified_identifiers:
                candidates = self._by_identifier.get(identifier.key, ())
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

        candidates = self._by_name.get(normalize_name(name), ())
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
