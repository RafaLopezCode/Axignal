"""Governed mention-to-entity binding, independent of canonical truth admission."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Final

from domain.identity import IdentityBindingAuthority
from domain.representation import RepresentationSpan, TextRepresentation

_BINDING_TOKEN: Final[object] = object()


@dataclass(frozen=True, slots=True)
class IdentityBindingRequest:
    entity_id: str
    mention: str
    mention_span: RepresentationSpan
    decision_id: str
    evidence_refs: tuple[str, ...]
    authority: IdentityBindingAuthority
    decided_by: str
    decided_at: datetime
    policy_version: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.entity_id,
                self.mention,
                self.decision_id,
                self.decided_by,
                self.policy_version,
            )
        ):
            raise ValueError("identity binding requires explicit identity and decision provenance")
        if not isinstance(self.authority, IdentityBindingAuthority):
            raise ValueError("identity binding authority must be governed")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("identity binding requires evidence references")
        if self.decided_at.tzinfo is None:
            raise ValueError("identity binding decision time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class GovernedIdentityBinding:
    request: IdentityBindingRequest
    _token: object | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def is_governed(self) -> bool:
        return self._token is _BINDING_TOKEN

    @property
    def is_canonical_truth(self) -> bool:
        return False


class IdentityBindingAdmission:
    """Accept only an explicit governed decision over an exact source mention.

    The caller is the governed identity control plane, never a provider-payload
    parser. This has the same language-level integrity posture as admission.
    """

    @staticmethod
    def bind(
        request: IdentityBindingRequest, representation: TextRepresentation
    ) -> GovernedIdentityBinding:
        if request.mention_span.extract(representation) != request.mention:
            raise ValueError("identity binding mention does not match exact span")
        binding = GovernedIdentityBinding(request)
        object.__setattr__(binding, "_token", _BINDING_TOKEN)
        return binding

    @staticmethod
    def matches(
        binding: GovernedIdentityBinding,
        *,
        entity_id: str,
        mention: str,
        support: RepresentationSpan,
        representation: TextRepresentation,
    ) -> bool:
        if not isinstance(binding, GovernedIdentityBinding) or not binding.is_governed:
            return False
        request = binding.request
        try:
            actual = request.mention_span.extract(representation)
            support.extract(representation)
        except ValueError:
            return False
        return (
            request.entity_id == entity_id
            and request.mention == mention == actual
            and support.start
            <= request.mention_span.start
            < request.mention_span.end
            <= support.end
        )
