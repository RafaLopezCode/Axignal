"""Distinct static identity types using AXIGNAL's string ID representation."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

OrganizationId = NewType("OrganizationId", str)
FaxtId = NewType("FaxtId", str)
PrincipalId = NewType("PrincipalId", str)
TenantId = NewType("TenantId", str)
XeedId = NewType("XeedId", str)


def identity_name_key(value: str) -> str:
    """Exact Unicode key; preserve scripts, accents and punctuation (MASTER §14)."""
    return unicodedata.normalize(
        "NFC", " ".join(unicodedata.normalize("NFC", value).casefold().split())
    )


class IdentityBindingAuthority(StrEnum):
    GOVERNED_HUMAN = "GOVERNED_HUMAN"
    DETERMINISTIC_POLICY = "DETERMINISTIC_POLICY"


class IdentityNameKind(StrEnum):
    ALIAS = "ALIAS"
    REBRAND = "REBRAND"


@dataclass(frozen=True, slots=True)
class GovernedIdentityName:
    """An immutable naming decision; never a canonical identity overwrite."""

    entity_id: str
    name: str
    kind: IdentityNameKind
    decision_id: str
    evidence_refs: tuple[str, ...]
    authority: IdentityBindingAuthority
    decided_by: str
    decided_at: datetime
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (self.entity_id, self.name, self.decision_id, self.decided_by)
        ):
            raise ValueError("identity name requires identity and decision provenance")
        if not isinstance(self.authority, IdentityBindingAuthority) or not isinstance(
            self.kind, IdentityNameKind
        ):
            raise ValueError("identity name requires governed authority and kind")
        if not self.evidence_refs or any(not value.strip() for value in self.evidence_refs):
            raise ValueError("identity name requires evidence references")
        for time in (self.decided_at, self.valid_from, self.valid_until):
            if time is not None and time.tzinfo is None:
                raise ValueError("identity name times must be timezone-aware")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from >= self.valid_until
        ):
            raise ValueError("identity name validity interval must be non-empty")

    def applies_at(self, as_of: datetime) -> bool:
        if as_of.tzinfo is None:
            raise ValueError("identity resolution as-of must be timezone-aware")
        return (
            self.decided_at <= as_of
            and (self.valid_from is None or self.valid_from <= as_of)
            and (self.valid_until is None or as_of < self.valid_until)
        )
