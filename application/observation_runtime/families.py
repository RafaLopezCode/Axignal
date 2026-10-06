"""Explicit observation policy for each of the ten canonical families.

A family policy says where observation starts, which economic questions it
serves, which abstract source capability each kind of research needs, which
follow-ups a finding may open, how deep and how expensive that may get, how
fast its evidence ages and how it backs off when it stops yielding. It is
control-plane vocabulary: no policy here can make anything OBSERVED.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.observation_intelligence.contracts import SourceCapability

FAMILY_POLICY_VERSION = "aor-family-policy-2026-10-07.1"

_C = SourceCapability


class ObservationFamily(StrEnum):
    """The ten canonical families; features never add new ones."""

    PRESENCE = "presence"
    REPUTATION = "reputation"
    VALUE = "value"
    MARKETS = "markets"
    RELATIONSHIPS = "relationships"
    DEMAND = "demand"
    ACTIVITY = "activity"
    ECONOMICS = "economics"
    ORGANIZATION = "organization"
    CONTEXT = "context"


class LeadKind(StrEnum):
    """What one research lead looks at. Each kind needs one abstract capability."""

    # Entry points.
    WEBSITE = "WEBSITE"
    OFFER_DECLARATION = "OFFER_DECLARATION"
    PUBLIC_MENTIONS = "PUBLIC_MENTIONS"
    MARKET_DEMAND = "MARKET_DEMAND"
    AWARD_COAPPEARANCE = "AWARD_COAPPEARANCE"
    OPEN_DEMAND = "OPEN_DEMAND"
    AWARD_ACTIVITY = "AWARD_ACTIVITY"
    HIRING = "HIRING"
    ECONOMIC_FILINGS = "ECONOMIC_FILINGS"
    REGISTRY_IDENTITY = "REGISTRY_IDENTITY"
    REGULATION = "REGULATION"
    # Follow-ups opened by findings.
    SITE_STRUCTURE = "SITE_STRUCTURE"
    SEARCH_VISIBILITY = "SEARCH_VISIBILITY"
    GENERATIVE_VISIBILITY = "GENERATIVE_VISIBILITY"
    MENTION_TOPIC = "MENTION_TOPIC"
    REGIONAL_DEMAND = "REGIONAL_DEMAND"
    RECURRING_BUYER = "RECURRING_BUYER"
    BUYER_OPEN_DEMAND = "BUYER_OPEN_DEMAND"
    FUNDING_DEMAND = "FUNDING_DEMAND"
    SECTOR_CONTEXT = "SECTOR_CONTEXT"


#: The single abstract capability each kind of lead needs; routing resolves it per
#: jurisdiction through the SourceRegistry, never through a named portal.
LEAD_CAPABILITY: dict[LeadKind, SourceCapability] = {
    LeadKind.WEBSITE: _C.DIGITAL_REPRESENTATION,
    LeadKind.OFFER_DECLARATION: _C.CAPABILITY_DECLARATION,
    LeadKind.PUBLIC_MENTIONS: _C.PUBLIC_REVIEWS_AND_MENTIONS,
    LeadKind.MARKET_DEMAND: _C.PUBLIC_PROCUREMENT_AWARDS,
    LeadKind.AWARD_COAPPEARANCE: _C.PUBLIC_PROCUREMENT_AWARDS,
    LeadKind.OPEN_DEMAND: _C.PUBLIC_PROCUREMENT_OPPORTUNITIES,
    LeadKind.AWARD_ACTIVITY: _C.PUBLIC_PROCUREMENT_AWARDS,
    LeadKind.HIRING: _C.HIRING_DEMAND,
    LeadKind.ECONOMIC_FILINGS: _C.ECONOMIC_FILINGS,
    LeadKind.REGISTRY_IDENTITY: _C.CORPORATE_REGISTRATION,
    LeadKind.REGULATION: _C.REGULATORY_CHANGE,
    LeadKind.SITE_STRUCTURE: _C.DIGITAL_REPRESENTATION,
    LeadKind.SEARCH_VISIBILITY: _C.PUBLIC_SEARCH_VISIBILITY,
    LeadKind.GENERATIVE_VISIBILITY: _C.GENERATIVE_ANSWER_SURFACES,
    LeadKind.MENTION_TOPIC: _C.PUBLIC_REVIEWS_AND_MENTIONS,
    LeadKind.REGIONAL_DEMAND: _C.PUBLIC_PROCUREMENT_OPPORTUNITIES,
    LeadKind.RECURRING_BUYER: _C.PUBLIC_PROCUREMENT_AWARDS,
    LeadKind.BUYER_OPEN_DEMAND: _C.PUBLIC_PROCUREMENT_OPPORTUNITIES,
    LeadKind.FUNDING_DEMAND: _C.PUBLIC_FUNDING,
    LeadKind.SECTOR_CONTEXT: _C.SECTOR_CONTEXT,
}


class EntryTarget(StrEnum):
    """What an entry lead is anchored to in the Xeed's attention."""

    WEBSITE = "WEBSITE"
    ORGANIZATION = "ORGANIZATION"
    MARKET = "MARKET"


@dataclass(frozen=True, slots=True)
class EntryPoint:
    kind: LeadKind
    target: EntryTarget
    question: str


@dataclass(frozen=True, slots=True)
class FollowUpRule:
    """A finding of ``from_kind`` may open a lead of ``to_kind``, and why that is worth asking."""

    from_kind: LeadKind
    to_kind: LeadKind
    question: str
    reduces_unknown: str


@dataclass(frozen=True, slots=True)
class FamilyObservationPolicy:
    family: ObservationFamily
    economic_questions: tuple[str, ...]
    entry_points: tuple[EntryPoint, ...]
    follow_ups: tuple[FollowUpRule, ...]
    max_depth: int
    max_leads_per_xeed: int
    max_actions_per_tick: int
    max_requests_per_tick: int
    #: How often a lead is looked at when it last produced material change.
    base_interval: timedelta
    #: Ceiling for no-gain and failure backoff.
    max_interval: timedelta
    failure_backoff: timedelta
    #: No-gain streak after which a lead drops to the low-yield tier.
    low_yield_after: int
    currentness: TemporalCurrentnessPolicy
    #: When no adopted source can answer, look again only after this long.
    blocked_recheck: timedelta
    stop_conditions: tuple[str, ...]
    #: Evidence of this family changes meaning when it ages (freshness-dependent).
    freshness_dependent: bool = True

    def __post_init__(self) -> None:
        if not self.economic_questions or not self.entry_points:
            raise ValueError("a family policy needs economic questions and entry points")
        if self.max_depth < 0 or min(self.max_leads_per_xeed, self.max_actions_per_tick) < 1:
            raise ValueError("family policy limits are invalid")
        if self.max_requests_per_tick < 0 or self.low_yield_after < 1:
            raise ValueError("family policy limits are invalid")
        if not timedelta(0) < self.base_interval <= self.max_interval:
            raise ValueError("family cadence bounds are invalid")
        if self.failure_backoff <= timedelta(0) or self.blocked_recheck <= timedelta(0):
            raise ValueError("family backoff must be positive")
        kinds = {entry.kind for entry in self.entry_points} | {
            rule.to_kind for rule in self.follow_ups
        }
        if any(kind not in LEAD_CAPABILITY for kind in kinds):
            raise ValueError("every lead kind must declare its source capability")

    def allows(self, from_kind: LeadKind, to_kind: LeadKind) -> FollowUpRule | None:
        return next(
            (r for r in self.follow_ups if r.from_kind is from_kind and r.to_kind is to_kind),
            None,
        )


def _currentness(
    family: ObservationFamily, stale: int, historical: int
) -> TemporalCurrentnessPolicy:
    return TemporalCurrentnessPolicy(
        policy_id=f"aor-currentness-{family.value}",
        version=FAMILY_POLICY_VERSION,
        stale_after=timedelta(days=stale),
        historical_after=timedelta(days=historical),
    )


_F = ObservationFamily
_K = LeadKind
_E = EntryTarget
_DAY = timedelta(days=1)


def _policy(
    family: ObservationFamily,
    *,
    questions: tuple[str, ...],
    entries: tuple[EntryPoint, ...],
    follow_ups: tuple[FollowUpRule, ...] = (),
    max_depth: int,
    base_days: int,
    max_days: int,
    stale_days: int,
    historical_days: int,
    stops: tuple[str, ...],
    max_leads: int = 12,
    max_actions: int = 4,
    max_requests: int = 12,
    freshness_dependent: bool = True,
) -> FamilyObservationPolicy:
    return FamilyObservationPolicy(
        family=family,
        economic_questions=questions,
        entry_points=entries,
        follow_ups=follow_ups,
        max_depth=max_depth,
        max_leads_per_xeed=max_leads,
        max_actions_per_tick=max_actions,
        max_requests_per_tick=max_requests,
        base_interval=_DAY * base_days,
        max_interval=_DAY * max_days,
        failure_backoff=_DAY,
        low_yield_after=2,
        currentness=_currentness(family, stale_days, historical_days),
        blocked_recheck=_DAY * 30,
        stop_conditions=stops,
        freshness_dependent=freshness_dependent,
    )


FAMILY_POLICIES: dict[ObservationFamily, FamilyObservationPolicy] = {
    _F.PRESENCE: _policy(
        _F.PRESENCE,
        questions=(
            "How is the organization represented on its own public web?",
            "Is that representation indexable and visible in search and generative surfaces?",
        ),
        entries=(EntryPoint(_K.WEBSITE, _E.WEBSITE, "presence.own-web"),),
        follow_ups=(
            FollowUpRule(_K.WEBSITE, _K.SITE_STRUCTURE, "presence.structure",
                         "sitemap, robots and structured data of the observed site"),
            FollowUpRule(_K.WEBSITE, _K.SEARCH_VISIBILITY, "presence.search",
                         "public search visibility of the observed site"),
            FollowUpRule(_K.WEBSITE, _K.GENERATIVE_VISIBILITY, "presence.generative",
                         "mention and citation in generative answer surfaces"),
        ),
        max_depth=1, base_days=7, max_days=28, stale_days=10, historical_days=90,
        stops=("own web current", "no adopted visibility source"),
    ),
    _F.REPUTATION: _policy(
        _F.REPUTATION,
        questions=("What do third parties publicly say about the organization, where and when?",),
        entries=(EntryPoint(_K.PUBLIC_MENTIONS, _E.ORGANIZATION, "reputation.mentions"),),
        follow_ups=(
            FollowUpRule(_K.PUBLIC_MENTIONS, _K.MENTION_TOPIC, "reputation.topic",
                         "which product, topic or geography a mention concerns"),
        ),
        max_depth=2, base_days=3, max_days=21, stale_days=30, historical_days=180,
        stops=("no new mentions", "no adopted review or mention source"),
    ),
    _F.VALUE: _policy(
        _F.VALUE,
        questions=("What does the organization offer, and with what observable evidence?",),
        entries=(EntryPoint(_K.OFFER_DECLARATION, _E.WEBSITE, "value.offer"),),
        max_depth=0, base_days=14, max_days=56, stale_days=45, historical_days=180,
        stops=("offer declaration current",),
    ),
    _F.MARKETS: _policy(
        _F.MARKETS,
        questions=("Where is there observable territorial demand for its capabilities?",),
        # Where awarded demand concentrates is followed up by Demand, not here.
        entries=(EntryPoint(_K.MARKET_DEMAND, _E.MARKET, "revealed-public-demand"),),
        max_depth=0, base_days=7, max_days=28, stale_days=60, historical_days=365,
        stops=("market demand characterized", "regions exhausted"),
    ),
    _F.RELATIONSHIPS: _policy(
        _F.RELATIONSHIPS,
        questions=("Which buyers, partners or suppliers co-appear with it in public records?",),
        entries=(EntryPoint(_K.AWARD_COAPPEARANCE, _E.MARKET, "revealed-public-demand"),),
        follow_ups=(
            FollowUpRule(_K.AWARD_COAPPEARANCE, _K.RECURRING_BUYER, "revealed-public-demand",
                         "whether a co-appearing buyer recurs (co-appearance is not a relationship)"),
        ),
        max_depth=1, base_days=14, max_days=56, stale_days=90, historical_days=365,
        stops=("no new co-appearances",),
    ),
    _F.DEMAND: _policy(
        _F.DEMAND,
        questions=(
            "Where is there economically plausible demand for the observed capabilities?",
        ),
        entries=(EntryPoint(_K.OPEN_DEMAND, _E.MARKET, "compatible-public-tenders"),),
        # Rules may start from another family's finding (awarded demand, recurring buyers).
        follow_ups=(
            FollowUpRule(_K.MARKET_DEMAND, _K.REGIONAL_DEMAND, "compatible-public-tenders",
                         "open calls in regions where awarded demand concentrates"),
            FollowUpRule(_K.RECURRING_BUYER, _K.BUYER_OPEN_DEMAND, "compatible-public-tenders",
                         "open demand from a buyer that awarded compatible work repeatedly"),
            FollowUpRule(_K.OPEN_DEMAND, _K.FUNDING_DEMAND, "funding-driven-demand",
                         "funding programmes that create demand for the capability"),
        ),
        max_depth=3, base_days=1, max_days=3, stale_days=7, historical_days=60,
        stops=("sufficient POTENTIAL candidates", "no marginal gain", "adopted sources exhausted"),
        max_leads=24, max_actions=6, max_requests=16,
    ),
    _F.ACTIVITY: _policy(
        _F.ACTIVITY,
        questions=("What has the organization done recently: awards, hiring, launches?",),
        entries=(
            EntryPoint(_K.AWARD_ACTIVITY, _E.MARKET, "revealed-public-demand"),
            EntryPoint(_K.HIRING, _E.ORGANIZATION, "buyer-expansion"),
        ),
        max_depth=0, base_days=7, max_days=28, stale_days=30, historical_days=180,
        stops=("no new activity",),
    ),
    _F.ECONOMICS: _policy(
        _F.ECONOMICS,
        questions=("Which economic magnitudes are publicly observable? Otherwise UNKNOWN.",),
        entries=(EntryPoint(_K.ECONOMIC_FILINGS, _E.ORGANIZATION, "economics.filings"),),
        max_depth=0, base_days=30, max_days=90, stale_days=365, historical_days=730,
        stops=("no adopted filings source: magnitudes stay UNKNOWN",),
        freshness_dependent=False,
    ),
    _F.ORGANIZATION: _policy(
        _F.ORGANIZATION,
        questions=("Who is it economically: identity, activity and public structure?",),
        entries=(
            EntryPoint(_K.REGISTRY_IDENTITY, _E.ORGANIZATION, "organization.registry"),
            EntryPoint(_K.OFFER_DECLARATION, _E.WEBSITE, "what-does-it-offer"),
        ),
        max_depth=0, base_days=30, max_days=90, stale_days=180, historical_days=730,
        stops=("identity current",),
        freshness_dependent=False,
    ),
    _F.CONTEXT: _policy(
        _F.CONTEXT,
        questions=("Which regulation, sector or external factors shape its demand?",),
        entries=(EntryPoint(_K.REGULATION, _E.MARKET, "regulation-driven-demand"),),
        follow_ups=(
            FollowUpRule(_K.REGULATION, _K.SECTOR_CONTEXT, "context.sector",
                         "sector conditions behind a regulatory change"),
        ),
        max_depth=1, base_days=14, max_days=56, stale_days=90, historical_days=365,
        stops=("no adopted regulation source",),
    ),
}  # fmt: skip

#: Canonical order, used only as a stable tie-breaker, never as importance.
FAMILY_ORDER: dict[ObservationFamily, int] = {family: i for i, family in enumerate(_F)}
