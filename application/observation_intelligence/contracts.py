"""Contracts for the Economic Observation Intelligence Layer.

Routing chain: Xeed capability + economic question + jurisdiction + buyer/job
→ abstract SourceCapability → concrete SourceDescriptor (an implementation of
that capability for some jurisdiction) → adapter. No sector, country or portal
appears in routing logic. Everything here is control-plane vocabulary: none of
it is canonical truth and nothing here may write AXIGLAND.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum, StrEnum

from domain.xignal import XignalEpistemicState


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("observation intelligence identity and values must be non-empty")


class Band(IntEnum):
    """Ordinal estimate; UNKNOWN is a value, never silently LOW or HIGH."""

    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class SourceCapability(StrEnum):
    """Abstract observation capability; concrete sources implement it per jurisdiction."""

    # Understanding the Xeed itself.
    CAPABILITY_DECLARATION = "CAPABILITY_DECLARATION"
    DIGITAL_REPRESENTATION = "DIGITAL_REPRESENTATION"
    CORPORATE_REGISTRATION = "CORPORATE_REGISTRATION"
    # Where demand for its capabilities may exist.
    PUBLIC_PROCUREMENT_OPPORTUNITIES = "PUBLIC_PROCUREMENT_OPPORTUNITIES"
    PUBLIC_PROCUREMENT_AWARDS = "PUBLIC_PROCUREMENT_AWARDS"
    PUBLIC_CONCESSIONS = "PUBLIC_CONCESSIONS"
    PUBLIC_INVESTMENT_PLANS = "PUBLIC_INVESTMENT_PLANS"
    PUBLIC_FUNDING = "PUBLIC_FUNDING"
    PLANNING_AND_PERMITS = "PLANNING_AND_PERMITS"
    PRIVATE_PROJECT_ANNOUNCEMENTS = "PRIVATE_PROJECT_ANNOUNCEMENTS"
    REGULATORY_CHANGE = "REGULATORY_CHANGE"
    HIRING_DEMAND = "HIRING_DEMAND"
    BUYER_INVESTMENT_SIGNALS = "BUYER_INVESTMENT_SIGNALS"


class OpportunityFamily(StrEnum):
    """Ways AXIGNAL can discover plausible demand; procurement is only one of them."""

    PUBLIC_PROCUREMENT = "PUBLIC_PROCUREMENT"
    PUBLIC_INVESTMENT = "PUBLIC_INVESTMENT"
    GRANTS_AND_SUBSIDIES = "GRANTS_AND_SUBSIDIES"
    PLANNING_AND_PERMITS = "PLANNING_AND_PERMITS"
    PRIVATE_PROJECT_SIGNALS = "PRIVATE_PROJECT_SIGNALS"
    REGULATION_DRIVEN_DEMAND = "REGULATION_DRIVEN_DEMAND"
    BUYER_EXPANSION_SIGNALS = "BUYER_EXPANSION_SIGNALS"


#: OPPORTUNITY_INTELLIGENCE: each family resolves to abstract source capabilities,
#: which resolve per jurisdiction to concrete sources and their adapters.
OPPORTUNITY_INTELLIGENCE: dict[OpportunityFamily, frozenset[SourceCapability]] = {
    OpportunityFamily.PUBLIC_PROCUREMENT: frozenset(
        {
            SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
            SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
            SourceCapability.PUBLIC_CONCESSIONS,
        }
    ),
    OpportunityFamily.PUBLIC_INVESTMENT: frozenset({SourceCapability.PUBLIC_INVESTMENT_PLANS}),
    OpportunityFamily.GRANTS_AND_SUBSIDIES: frozenset({SourceCapability.PUBLIC_FUNDING}),
    OpportunityFamily.PLANNING_AND_PERMITS: frozenset({SourceCapability.PLANNING_AND_PERMITS}),
    OpportunityFamily.PRIVATE_PROJECT_SIGNALS: frozenset(
        {SourceCapability.PRIVATE_PROJECT_ANNOUNCEMENTS}
    ),
    OpportunityFamily.REGULATION_DRIVEN_DEMAND: frozenset({SourceCapability.REGULATORY_CHANGE}),
    OpportunityFamily.BUYER_EXPANSION_SIGNALS: frozenset(
        {SourceCapability.HIRING_DEMAND, SourceCapability.BUYER_INVESTMENT_SIGNALS}
    ),
}


@dataclass(frozen=True, slots=True, order=True)
class TaxonomyCode:
    """A code kept in its own scheme (CPV, NAICS, PSC, GEO...); never coerced across."""

    scheme: str
    code: str

    def __post_init__(self) -> None:
        _required(self.scheme, self.code)

    def within(self, other: TaxonomyCode) -> bool:
        """Hierarchical containment inside one scheme.

        ``GEO`` codes are jurisdiction paths (``EU/ES/ES5/ES52``, ``US/US-CA``) and
        nest by path segment; other schemes nest by code prefix.
        """
        if self.scheme != other.scheme:
            return False
        if self.scheme == "GEO":
            return self.code == other.code or self.code.startswith(other.code + "/")
        return self.code.startswith(other.code)


def geo(path: str) -> TaxonomyCode:
    return TaxonomyCode("GEO", path)


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Pointer to the evidence behind a hypothesis: observation, excerpt and time."""

    observation_id: str
    source_ref: str
    excerpt: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _required(self.observation_id, self.source_ref, self.excerpt)
        if self.observed_at.tzinfo is None:
            raise ValueError("evidence reference time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class CapabilityHypothesis:
    """What the Xeed can do, as declared or inferred; POTENTIAL until admitted.

    ``demand_codes`` say how buyers classify demand for it, in every scheme known
    (CPV, NAICS, PSC...); each source uses only the schemes it supports.
    """

    capability_id: str
    label: str
    state: XignalEpistemicState
    basis: tuple[EvidenceRef, ...]
    demand_codes: tuple[TaxonomyCode, ...]
    buyer_jobs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.capability_id, self.label)
        if self.state is not XignalEpistemicState.UNKNOWN and not self.basis:
            raise ValueError("a capability hypothesis needs evidence unless it is UNKNOWN")
        if self.state is XignalEpistemicState.OBSERVED:
            raise ValueError("capability hypotheses are never OBSERVED without admission")


@dataclass(frozen=True, slots=True)
class BusinessFamilyHypothesis:
    """Membership in an economic family; many may hold at once."""

    family_id: str
    state: XignalEpistemicState
    strength: Band
    stability: Band
    capability_ids: tuple[str, ...]
    basis: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        _required(self.family_id)
        if self.state is XignalEpistemicState.OBSERVED:
            raise ValueError("a business family is a governed hypothesis, never OBSERVED")
        if self.state is XignalEpistemicState.POTENTIAL and not self.basis:
            raise ValueError("a POTENTIAL family requires evidence")


class MarketRole(StrEnum):
    PUBLIC_BUYERS = "PUBLIC_BUYERS"
    PRIVATE_BUSINESSES = "PRIVATE_BUSINESSES"
    CONSUMERS = "CONSUMERS"


@dataclass(frozen=True, slots=True)
class MarketScope:
    """A market the Xeed participates in or could enter, per capability reach."""

    geography: TaxonomyCode
    roles: frozenset[MarketRole]
    state: XignalEpistemicState
    buyer_segments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.geography.scheme != "GEO":
            raise ValueError("market geography must be a jurisdiction path")
        if not self.roles:
            raise ValueError("a market scope requires at least one buyer role")


@dataclass(frozen=True, slots=True)
class EconomicQuestion:
    """A question worth answering and the abstract capabilities that can answer it.

    Opportunity questions belong to one family and decompose the Brain's root
    question: where is there plausible demand for the observed capabilities?
    """

    question_id: str
    version: str
    text: str
    requires: frozenset[SourceCapability]
    market_roles: frozenset[MarketRole]
    economic_value: Band
    uses_capability_codes: bool = True
    opportunity_family: OpportunityFamily | None = None

    def __post_init__(self) -> None:
        _required(self.question_id, self.version, self.text)
        if not self.requires or not self.market_roles:
            raise ValueError("an economic question requires capabilities and market roles")
        if (
            self.opportunity_family is not None
            and not self.requires <= (OPPORTUNITY_INTELLIGENCE[self.opportunity_family])
        ):
            raise ValueError("an opportunity question can only require its family's capabilities")


class AccessMethod(StrEnum):
    API = "API"
    FEED = "FEED"
    FILE = "FILE"
    CRAWL = "CRAWL"
    SEARCH = "SEARCH"


class RightsStatus(StrEnum):
    REUSE_DOCUMENTED = "REUSE_DOCUMENTED"
    UNKNOWN = "UNKNOWN"
    RESTRICTED = "RESTRICTED"


class AdoptionStatus(StrEnum):
    ADOPTED = "ADOPTED"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"


class BuyerLevel(StrEnum):
    SUPRANATIONAL = "SUPRANATIONAL"
    NATIONAL_OR_FEDERAL = "NATIONAL_OR_FEDERAL"
    REGIONAL_OR_STATE = "REGIONAL_OR_STATE"
    LOCAL = "LOCAL"
    PUBLIC_UNDERTAKING = "PUBLIC_UNDERTAKING"


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    """A concrete source: which abstract capabilities it implements, where, and how well."""

    source_id: str
    version: str
    name: str
    owner: str
    capabilities: frozenset[SourceCapability]
    jurisdictions: tuple[TaxonomyCode, ...]
    classification_systems: frozenset[str]
    buyer_levels: frozenset[BuyerLevel]
    record_types: tuple[str, ...]
    access_method: AccessMethod
    authentication_required: bool
    rights: RightsStatus
    reliability: Band
    precision: Band
    coverage: Band
    provenance_quality: Band
    structured: bool
    expected_change_interval: timedelta
    historical_depth: str
    cost_per_request_microunits: int | None
    computational_cost: Band
    expected_latency_ms: int | None
    failure_modes: tuple[str, ...]
    alternatives: tuple[str, ...]
    adoption: AdoptionStatus
    reference: str
    scope_limitations: tuple[str, ...] = ()
    adoption_blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.source_id, self.version, self.name, self.owner, self.reference)
        if not self.capabilities or not self.jurisdictions:
            raise ValueError("a source must declare capabilities and jurisdictions")
        if any(item.scheme not in {"GEO", "GLOBAL"} for item in self.jurisdictions):
            raise ValueError("source jurisdictions must be jurisdiction paths")
        if self.expected_change_interval <= timedelta(0):
            raise ValueError("expected change interval must be positive")
        if self.cost_per_request_microunits is not None and self.cost_per_request_microunits < 0:
            raise ValueError("source cost cannot be negative")
        if self.adoption is AdoptionStatus.ADOPTED and self.adoption_blockers:
            raise ValueError("an adopted source cannot carry open adoption blockers")

    def covers(self, geography: TaxonomyCode) -> bool:
        """True when the market is inside a declared jurisdiction or contains one."""
        return any(
            scope.scheme == "GLOBAL" or geography.within(scope) or scope.within(geography)
            for scope in self.jurisdictions
        )

    @property
    def routable(self) -> bool:
        # Unknown rights or unknown cost make a source ineligible, never "cheap".
        return (
            self.adoption is AdoptionStatus.ADOPTED
            and self.rights is RightsStatus.REUSE_DOCUMENTED
            and self.cost_per_request_microunits is not None
        )

    @property
    def eligibility(self) -> tuple[str, ...]:
        """Why this source cannot be routed now; empty when it can."""
        if self.routable:
            return ()
        reasons = [f"ADOPTION_{self.adoption.value}"]
        if self.rights is not RightsStatus.REUSE_DOCUMENTED:
            reasons.append(f"RIGHTS_{self.rights.value}")
        if self.cost_per_request_microunits is None:
            reasons.append("COST_UNKNOWN")
        return (*reasons, *self.adoption_blockers)


@dataclass(frozen=True, slots=True)
class QuerySpec:
    """The concrete ask to a source, derived from capability codes and market."""

    demand_codes: tuple[TaxonomyCode, ...]
    geographies: tuple[TaxonomyCode, ...]
    capabilities: frozenset[SourceCapability]
    published_since: datetime | None = None
    # For calls for tender: only those still open for submission on this date.
    open_on: datetime | None = None

    @property
    def key(self) -> tuple[object, ...]:
        return (
            tuple(sorted(self.demand_codes)),
            tuple(sorted(self.geographies)),
            tuple(sorted(self.capabilities)),
        )


@dataclass(frozen=True, slots=True)
class ObservationBudget:
    max_requests: int
    max_amount_microunits: int | None
    max_depth: int
    max_actions: int

    def __post_init__(self) -> None:
        if min(self.max_requests, self.max_depth, self.max_actions) < 0:
            raise ValueError("observation budget limits cannot be negative")


@dataclass(frozen=True, slots=True)
class XeedObservationContext:
    """Everything routing may consider about one Xeed at one time."""

    xeed_id: str
    as_of: datetime
    capabilities: tuple[CapabilityHypothesis, ...]
    families: tuple[BusinessFamilyHypothesis, ...]
    markets: tuple[MarketScope, ...]
    evidence_seen: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        _required(self.xeed_id)
        if self.as_of.tzinfo is None:
            raise ValueError("observation context time must be timezone-aware")
