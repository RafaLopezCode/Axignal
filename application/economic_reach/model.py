"""Economic Operating Model: the evidence-derived "garden" of one Organization (Spec 059).

The garden is not an Organization property and not a profile anyone edits. It is a
temporal projection of public evidence about how each capability is delivered:

* a *delivery channel* is a capability delivered through a mode; reach belongs to the
  channel, not to the Organization, its headquarters or its country;
* OPERATING reach — where a channel is evidenced to serve now;
* EXPANSION reach — where the Organization's own preparatory acts (a new facility,
  regional hiring) make serving plausible; always POTENTIAL;
* EXPOSURE — drivers that reach the business through a transmission channel (energy,
  transport, freight, regulation, platform, supply) wherever they happen. Exposure is a
  dependency path, not a wider geographic circle, and never an opportunity.

Absence of evidence is UNKNOWN. A claim is an observation's statement, never a FAXT.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from application.observation_intelligence.contracts import EvidenceRef, TaxonomyCode
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState


class DeliveryMode(StrEnum):
    """How a capability reaches its customer; it decides which feasibility binds."""

    #: The customer comes to the provider (school, salon, restaurant, shop).
    PROVIDER_PREMISES = "PROVIDER_PREMISES"
    #: The provider goes to the customer (installation, field service, onsite work).
    CUSTOMER_SITE = "CUSTOMER_SITE"
    #: Physical goods travel to the customer.
    SHIPPED = "SHIPPED"
    #: A person delivers live but at a distance (online classes, remote consulting).
    REMOTE = "REMOTE"
    #: Self-served software or digital product.
    DIGITAL = "DIGITAL"


LOCATION_BOUND = frozenset({DeliveryMode.PROVIDER_PREMISES, DeliveryMode.CUSTOMER_SITE})
DISTANCE_INDEPENDENT = frozenset({DeliveryMode.REMOTE, DeliveryMode.DIGITAL})


class ReachBasis(StrEnum):
    #: The Organization states where it serves ("damos servicio en Madrid y Toledo").
    STATED_SERVICE_AREA = "STATED_SERVICE_AREA"
    #: Where its premises are; reach only for channels whose customers come to them.
    PREMISES = "PREMISES"
    #: Its own preparatory act in a place: a facility being opened, regional hiring.
    EXPANSION_SIGNAL = "EXPANSION_SIGNAL"


class ClaimBinding(StrEnum):
    #: The statement names the capability: it speaks about that channel.
    CAPABILITY = "CAPABILITY"
    #: A site-wide statement: it cannot prove any single capability's reach.
    ORGANIZATION = "ORGANIZATION"


class Polarity(StrEnum):
    INCLUDED = "INCLUDED"
    #: Explicitly excluded by the Organization ("no enviamos a Canarias").
    EXCLUDED = "EXCLUDED"


@dataclass(frozen=True, slots=True)
class ReachClaim:
    geography: TaxonomyCode
    basis: ReachBasis
    binding: ClaimBinding
    evidence: EvidenceRef
    currentness: Currentness
    mode: DeliveryMode | None = None
    polarity: Polarity = Polarity.INCLUDED
    #: "solo/únicamente/only": the stated area is exhaustive for this channel.
    exclusive: bool = False
    #: For expansion: FACILITY or HIRING; independent kinds corroborate each other.
    signal: str | None = None

    def identity(self) -> list[object]:
        return [
            self.geography.code,
            self.basis.value,
            self.binding.value,
            None if self.mode is None else self.mode.value,
            self.polarity.value,
            self.exclusive,
            self.signal,
            self.evidence.observation_id,
            self.evidence.excerpt,
        ]


@dataclass(frozen=True, slots=True)
class ModeClaim:
    mode: DeliveryMode
    binding: ClaimBinding
    evidence: EvidenceRef

    @property
    def state(self) -> XignalEpistemicState:
        # A site-wide mode statement cannot prove how one capability is delivered.
        return (
            XignalEpistemicState.OBSERVED
            if self.binding is ClaimBinding.CAPABILITY
            else XignalEpistemicState.POTENTIAL
        )


class ConstraintKind(StrEnum):
    CERTIFICATION = "CERTIFICATION"


@dataclass(frozen=True, slots=True)
class ConstraintClaim:
    kind: ConstraintKind
    value: str
    binding: ClaimBinding
    evidence: EvidenceRef
    #: True only for an explicit governed withdrawal (EB-06 WITHDRAWN field state).
    withdrawn: bool = False


class ExposureChannel(StrEnum):
    PREMISES_ENERGY = "PREMISES_ENERGY"
    FUEL_AND_TRAVEL = "FUEL_AND_TRAVEL"
    FREIGHT_AND_CUSTOMS = "FREIGHT_AND_CUSTOMS"
    LOCAL_REGULATION = "LOCAL_REGULATION"
    DIGITAL_PLATFORM = "DIGITAL_PLATFORM"
    SUPPLY_INPUTS = "SUPPLY_INPUTS"


#: Governed derivation: what a delivery mode depends on to operate. A path, not a fact.
CHANNELS_BY_MODE: dict[DeliveryMode, tuple[ExposureChannel, ...]] = {
    DeliveryMode.PROVIDER_PREMISES: (
        ExposureChannel.PREMISES_ENERGY,
        ExposureChannel.LOCAL_REGULATION,
    ),
    DeliveryMode.CUSTOMER_SITE: (ExposureChannel.FUEL_AND_TRAVEL, ExposureChannel.LOCAL_REGULATION),
    DeliveryMode.SHIPPED: (ExposureChannel.FREIGHT_AND_CUSTOMS, ExposureChannel.PREMISES_ENERGY),
    DeliveryMode.REMOTE: (ExposureChannel.DIGITAL_PLATFORM,),
    DeliveryMode.DIGITAL: (ExposureChannel.DIGITAL_PLATFORM, ExposureChannel.LOCAL_REGULATION),
}


@dataclass(frozen=True, slots=True)
class ExposurePath:
    channel: ExposureChannel
    capability_id: str | None
    via: str  # DeliveryMode value or the evidence kind that created the path
    evidence: tuple[EvidenceRef, ...]


@dataclass(frozen=True, slots=True)
class CapabilityReach:
    capability_id: str
    label: str
    modes: tuple[ModeClaim, ...]
    claims: tuple[ReachClaim, ...]
    constraints: tuple[ConstraintClaim, ...]

    def mode_values(self) -> frozenset[DeliveryMode]:
        return frozenset(item.mode for item in self.modes)


@dataclass(frozen=True, slots=True)
class EconomicOperatingModel:
    organization_id: str
    capabilities: tuple[CapabilityReach, ...]
    exposure: tuple[ExposurePath, ...]
    #: Observations the model was derived from (declared continuity dependencies).
    evidence_ids: tuple[str, ...]

    def reach_for(self, capability_id: str) -> CapabilityReach | None:
        return next((c for c in self.capabilities if c.capability_id == capability_id), None)

    @property
    def has_reach_evidence(self) -> bool:
        return any(c.claims for c in self.capabilities)

    @property
    def fingerprint(self) -> str:
        """Semantic identity: the same evidence always derives the same garden."""
        payload = {
            "organization": self.organization_id,
            "capabilities": [
                {
                    "id": c.capability_id,
                    "modes": sorted(
                        [m.mode.value, m.binding.value, m.evidence.observation_id] for m in c.modes
                    ),
                    "claims": sorted(claim.identity() for claim in c.claims),
                    "constraints": sorted(
                        [k.kind.value, k.value, k.binding.value, k.withdrawn] for k in c.constraints
                    ),
                }
                for c in sorted(self.capabilities, key=lambda item: item.capability_id)
            ],
            "exposure": sorted(
                [p.channel.value, p.capability_id or "", p.via] for p in self.exposure
            ),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
