"""Canonical Organization identity and admitted economic profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.evidence.epistemics import EpistemicState
from domain.faxt.model import FAXT
from domain.identity import OrganizationId


class OrganizationError(Exception):
    """Error raised for invalid canonical organization state."""


_PROFILE_TOKEN = object()


@dataclass(frozen=True)
class Organization:
    """One canonical economic entity; business profile requires admitted FAXTs."""

    id: OrganizationId
    canonical_name: str
    aliases: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    markets: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    products: tuple[str, ...] = ()
    corporate_links: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    discovered_at: datetime | None = None
    _profile_token: object | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise OrganizationError("organization id is required")
        if not self.canonical_name.strip():
            raise OrganizationError("organization canonical_name is required")
        business_profile = (
            self.markets,
            self.capabilities,
            self.products,
            self.corporate_links,
            self.evidence_refs,
        )
        if any(business_profile) and self._profile_token is not _PROFILE_TOKEN:
            raise OrganizationError(
                "canonical Organization business fields require admitted FAXT materialization"
            )

    @classmethod
    def from_admitted_faxts(
        cls,
        *,
        organization_id: OrganizationId,
        canonical_name: str,
        faxts: tuple[FAXT, ...],
        aliases: tuple[str, ...] = (),
        locations: tuple[str, ...] = (),
        discovered_at: datetime | None = None,
    ) -> Organization:
        """Materialize business profile fields only from canonical FAXTs."""

        if not faxts:
            raise OrganizationError("admitted Organization profile requires FAXTs")
        capabilities: list[str] = []
        products: list[str] = []
        markets: list[str] = []
        links: list[str] = []
        evidence_refs: list[str] = []
        for faxt in faxts:
            if not isinstance(faxt, FAXT):
                raise OrganizationError("Organization profile requires canonical FAXT values")
            if faxt.subject_id != organization_id:
                raise OrganizationError("Organization profile FAXT subject mismatch")
            if faxt.epistemic_state not in (
                EpistemicState.OBSERVED,
                EpistemicState.CORROBORATED,
            ):
                raise OrganizationError(
                    "Organization profile cannot promote non-observed FAXT state"
                )
            predicate = faxt.predicate.strip().lower()
            if predicate in {"capability", "manufactures", "develops_capability"}:
                capabilities.append(faxt.object_or_value)
            elif predicate in {"product", "products", "has_product"}:
                products.append(faxt.object_or_value)
            elif predicate in {"market", "serves_market"}:
                markets.append(faxt.object_or_value)
            elif predicate in {"corporate_link", "official_link"}:
                links.append(faxt.object_or_value)
            else:
                continue
            evidence_refs.extend(faxt.evidence_refs)

        value = cls(
            id=organization_id,
            canonical_name=canonical_name,
            aliases=aliases,
            locations=locations,
            discovered_at=discovered_at,
        )
        object.__setattr__(value, "markets", tuple(dict.fromkeys(markets)))
        object.__setattr__(value, "capabilities", tuple(dict.fromkeys(capabilities)))
        object.__setattr__(value, "products", tuple(dict.fromkeys(products)))
        object.__setattr__(value, "corporate_links", tuple(dict.fromkeys(links)))
        object.__setattr__(value, "evidence_refs", tuple(dict.fromkeys(evidence_refs)))
        object.__setattr__(value, "_profile_token", _PROFILE_TOKEN)
        return value

    @property
    def identity_key(self) -> OrganizationId:
        return self.id
