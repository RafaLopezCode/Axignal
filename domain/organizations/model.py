"""Canonical Organization model.

The canonical organization is a property of AXIGLAND, shared by all observers.
It deliberately carries no subscriber, account, tenant, owner, claiming or
Xignal scope. Perspective and private classification live outside this model.

Doctrine: MASTER §6.1 (perspective is a query, not a permission), §6.3 (private
context), §7.3 (one organization, many Xignals), §36 (conceptual data model).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class OrganizationError(Exception):
    """Error raised for invalid canonical organization state."""


@dataclass(frozen=True)
class Organization:
    """A canonical economic entity in AXIGLAND.

    There is no ``account_id``, ``tenant_id``, ``owner_id``, ``xignal_id``,
    ``claimed_by`` or ``profile_owner`` field, by design. Adding one would turn
    AXIGNAL into a claiming/social product (MASTER §32, §46.35).
    """

    id: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    markets: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    products: tuple[str, ...] = ()
    corporate_links: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    discovered_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise OrganizationError("organization id is required")
        if not self.canonical_name.strip():
            raise OrganizationError("organization canonical_name is required")

    @property
    def identity_key(self) -> str:
        """Stable identity key. Independent of any observer."""

        return self.id
