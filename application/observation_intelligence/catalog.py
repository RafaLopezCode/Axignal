"""Versioned catalogs: capability lexicon, economic questions, concrete sources.

These are governed data, not code paths. A new family, market, classification
scheme or jurisdiction is a catalog entry; routing logic never names a sector,
country or portal. Source facts are only what official documentation states;
anything unverified keeps the source CANDIDATE with explicit adoption blockers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from application.observation_intelligence.contracts import (
    AccessMethod,
    AdoptionStatus,
    Band,
    BuyerLevel,
    EconomicQuestion,
    MarketRole,
    OpportunityFamily,
    RightsStatus,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    geo,
)

CATALOG_VERSION = "eoil-catalog-2026-10-06.4"

#: Path depth that counts as a "region" inside each jurisdiction tree.
REGIONAL_DEPTH: dict[str, int] = {"EU": 4, "US": 2}


def cpv(code: str) -> TaxonomyCode:
    return TaxonomyCode("CPV", code)


def naics(code: str) -> TaxonomyCode:
    return TaxonomyCode("NAICS", code)


def psc(code: str) -> TaxonomyCode:
    return TaxonomyCode("PSC", code)


def eu_nuts(code: str) -> TaxonomyCode:
    """NUTS code → jurisdiction path: ES522 → EU/ES/ES5/ES52/ES522."""

    return geo("/".join(["EU", code[:2], *(code[:i] for i in range(3, len(code) + 1))]))


@dataclass(frozen=True, slots=True)
class CapabilityLexiconEntry:
    """Deterministic surface terms for one capability and how buyers classify it."""

    capability_id: str
    label: str
    terms: tuple[str, ...]
    demand_codes: tuple[TaxonomyCode, ...]
    families: tuple[str, ...]
    buyer_jobs: tuple[str, ...]


CAPABILITY_LEXICON: tuple[CapabilityLexiconEntry, ...] = (
    CapabilityLexiconEntry(
        capability_id="solar-pv-installation",
        label="Solar photovoltaic installation",
        terms=("fotovoltaic", "photovoltaï", "photovoltaic", "paneles solares", "autoconsumo"),
        demand_codes=(
            cpv("09331200"), cpv("09332000"), cpv("45261215"), naics("221114"), naics("238210"),
        ),
        families=("energy", "construction"),
        buyer_jobs=("self-consumption on public buildings", "solar roofs for industrial sites"),
    ),
    CapabilityLexiconEntry(
        capability_id="electrical-installation",
        label="Electrical installation work",
        terms=("instalaciones eléctricas", "electrical installation", "installation électrique"),
        demand_codes=(cpv("45311000"), cpv("45317000"), naics("238210")),
        families=("construction",),
        buyer_jobs=("electrical works in public facilities",),
    ),
    CapabilityLexiconEntry(
        capability_id="industrial-hvac",
        label="Industrial HVAC installation and maintenance",
        terms=("climatización industrial", "industrial hvac", "climatisation industrielle"),
        demand_codes=(
            cpv("45331000"), cpv("42510000"), naics("238220"), psc("4120"), psc("J041"),
        ),
        families=("industrial-maintenance", "construction"),
        buyer_jobs=(
            "HVAC renewal in hospitals and public buildings",
            "climate control for new logistics centres and plants",
        ),
    ),
    CapabilityLexiconEntry(
        capability_id="industrial-refrigeration",
        label="Industrial refrigeration installation and maintenance",
        terms=("refrigeración industrial", "froid industriel", "industrial refrigeration"),
        demand_codes=(
            cpv("42513000"), cpv("50730000"), naics("238220"), naics("333415"),
            psc("4110"), psc("J041"),
        ),
        families=("industrial-maintenance", "construction"),
        buyer_jobs=(
            "cold rooms for new food manufacturing plants",
            "refrigeration maintenance for hospitals and logistics centres",
        ),
    ),
    CapabilityLexiconEntry(
        capability_id="consumer-mobile-app",
        label="Consumer mobile ordering app",
        terms=("descarga nuestra app", "mobile app", "app móvil"),
        demand_codes=(),
        families=("consumer-software",),
        buyer_jobs=("consumers ordering from local shops",),
    ),
)  # fmt: skip


#: The Brain's root question. It is never routed itself; each opportunity family
#: contributes sub-questions that require that family's source capabilities.
ROOT_QUESTION = (
    "Where is there economically plausible demand for this Xeed's observed capabilities, "
    "and what public evidence supports it?"
)

_F = OpportunityFamily
_ALL_BUYERS = frozenset({MarketRole.PUBLIC_BUYERS, MarketRole.PRIVATE_BUSINESSES})

QUESTIONS: tuple[EconomicQuestion, ...] = (
    EconomicQuestion(
        question_id="what-does-it-offer",
        version="1",
        text="What does this organization actually offer?",
        requires=frozenset({SourceCapability.CAPABILITY_DECLARATION}),
        market_roles=frozenset(MarketRole),
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
    ),
    EconomicQuestion(
        question_id="compatible-public-tenders",
        version="1",
        text="Which open public tenders ask for its observed capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PUBLIC_PROCUREMENT,
    ),
    EconomicQuestion(
        question_id="revealed-public-demand",
        version="1",
        text="Which recent awards reveal buyers and recurring demand for these capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_PROCUREMENT_AWARDS}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.MEDIUM,
        opportunity_family=_F.PUBLIC_PROCUREMENT,
    ),
    EconomicQuestion(
        question_id="public-investment-pipeline",
        version="1",
        text="Which planned public investments will need these capabilities?",
        requires=frozenset({SourceCapability.PUBLIC_INVESTMENT_PLANS}),
        market_roles=frozenset({MarketRole.PUBLIC_BUYERS}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PUBLIC_INVESTMENT,
    ),
    EconomicQuestion(
        question_id="funding-driven-demand",
        version="1",
        text="Which grants or subsidies are funding work these capabilities can deliver?",
        requires=frozenset({SourceCapability.PUBLIC_FUNDING}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.MEDIUM,
        opportunity_family=_F.GRANTS_AND_SUBSIDIES,
    ),
    EconomicQuestion(
        question_id="projects-needing-capability",
        version="1",
        text="Which permitted or planned projects will need this capability?",
        requires=frozenset({SourceCapability.PLANNING_AND_PERMITS}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.HIGH,
        opportunity_family=_F.PLANNING_AND_PERMITS,
    ),
    EconomicQuestion(
        question_id="private-project-announcements",
        version="1",
        text="Which announced private projects (plants, logistics, hospitality) need it?",
        requires=frozenset({SourceCapability.PRIVATE_PROJECT_ANNOUNCEMENTS}),
        market_roles=frozenset({MarketRole.PRIVATE_BUSINESSES}),
        economic_value=Band.HIGH,
        opportunity_family=_F.PRIVATE_PROJECT_SIGNALS,
    ),
    EconomicQuestion(
        question_id="regulation-driven-demand",
        version="1",
        text="Which regulatory changes oblige buyers to purchase what it offers?",
        requires=frozenset({SourceCapability.REGULATORY_CHANGE}),
        market_roles=_ALL_BUYERS,
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
        opportunity_family=_F.REGULATION_DRIVEN_DEMAND,
    ),
    EconomicQuestion(
        question_id="buyer-expansion",
        version="1",
        text="Which potential buyers show expansion through hiring or investment?",
        requires=frozenset(
            {SourceCapability.HIRING_DEMAND, SourceCapability.BUYER_INVESTMENT_SIGNALS}
        ),
        market_roles=frozenset({MarketRole.PRIVATE_BUSINESSES}),
        economic_value=Band.LOW,
        opportunity_family=_F.BUYER_EXPANSION_SIGNALS,
    ),
    EconomicQuestion(
        question_id="consumer-representation",
        version="1",
        text="How is it represented where consumers look for it?",
        requires=frozenset({SourceCapability.DIGITAL_REPRESENTATION}),
        market_roles=frozenset({MarketRole.CONSUMERS}),
        economic_value=Band.MEDIUM,
        uses_capability_codes=False,
    ),
)

_PROCUREMENT = frozenset(
    {
        SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES,
        SourceCapability.PUBLIC_PROCUREMENT_AWARDS,
    }
)


def _candidate(
    *,
    source_id: str,
    name: str,
    owner: str,
    capabilities: frozenset[SourceCapability],
    jurisdictions: tuple[TaxonomyCode, ...],
    classification_systems: frozenset[str],
    buyer_levels: frozenset[BuyerLevel],
    record_types: tuple[str, ...],
    access_method: AccessMethod,
    authentication_required: bool,
    expected_change_interval: timedelta,
    reference: str,
    blockers: tuple[str, ...],
    scope_limitations: tuple[str, ...] = (),
    alternatives: tuple[str, ...] = (),
) -> SourceDescriptor:
    """A source known to exist but not yet through the adoption gate: UNKNOWNs stay UNKNOWN."""

    return SourceDescriptor(
        source_id=source_id,
        version="0",
        name=name,
        owner=owner,
        capabilities=capabilities,
        jurisdictions=jurisdictions,
        classification_systems=classification_systems,
        buyer_levels=buyer_levels,
        record_types=record_types,
        access_method=access_method,
        authentication_required=authentication_required,
        rights=RightsStatus.UNKNOWN,
        reliability=Band.UNKNOWN,
        precision=Band.UNKNOWN,
        coverage=Band.UNKNOWN,
        provenance_quality=Band.UNKNOWN,
        structured=True,
        expected_change_interval=expected_change_interval,
        historical_depth="TO_VERIFY",
        cost_per_request_microunits=None,
        computational_cost=Band.MEDIUM,
        expected_latency_ms=None,
        failure_modes=("TO_VERIFY",),
        alternatives=alternatives,
        adoption=AdoptionStatus.CANDIDATE,
        reference=reference,
        scope_limitations=scope_limitations,
        adoption_blockers=blockers,
    )


SOURCES: tuple[SourceDescriptor, ...] = (
    SourceDescriptor(
        source_id="official-public-website",
        version="1",
        name="Organization's own public website",
        owner="The observed organization",
        capabilities=frozenset(
            {SourceCapability.CAPABILITY_DECLARATION, SourceCapability.DIGITAL_REPRESENTATION}
        ),
        jurisdictions=(TaxonomyCode("GLOBAL", "ANY"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(),
        record_types=("public web page",),
        access_method=AccessMethod.CRAWL,
        authentication_required=False,
        rights=RightsStatus.REUSE_DOCUMENTED,
        reliability=Band.MEDIUM,
        precision=Band.LOW,
        coverage=Band.LOW,
        provenance_quality=Band.HIGH,
        structured=False,
        expected_change_interval=timedelta(days=30),
        historical_depth="current page only",
        cost_per_request_microunits=0,
        computational_cost=Band.LOW,
        expected_latency_ms=1_500,
        failure_modes=("unreachable host", "script-only rendering", "self-declared claims"),
        alternatives=("corporate registries",),
        adoption=AdoptionStatus.ADOPTED,
        reference="registered public homepage policy (FR-30 FirstProof)",
        scope_limitations=("A declaration is evidence of the claim, not of the capability.",),
    ),
    SourceDescriptor(
        source_id="ted-search-v3",
        version="1",
        name="Tenders Electronic Daily — Search API v3",
        owner="Publications Office of the European Union",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("EU"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(BuyerLevel),
        record_types=("cn-standard", "cn-social", "can-standard", "can-social"),
        access_method=AccessMethod.API,
        authentication_required=False,
        rights=RightsStatus.REUSE_DOCUMENTED,
        reliability=Band.HIGH,
        precision=Band.HIGH,
        coverage=Band.MEDIUM,
        provenance_quality=Band.HIGH,
        structured=True,
        expected_change_interval=timedelta(days=1),
        historical_depth="published notices, eForms and legacy archives",
        cost_per_request_microunits=0,
        computational_cost=Band.LOW,
        expected_latency_ms=2_000,
        failure_modes=(
            "timeout on broad queries",
            "multilingual free-text fields",
            "award data missing or partial per lot",
        ),
        alternatives=("es-placsp", "fr-boamp"),
        adoption=AdoptionStatus.ADOPTED,
        reference="https://docs.ted.europa.eu/api/latest/search.html",
        scope_limitations=(
            "Notices published on TED, mostly above EU thresholds; national and regional "
            "below-threshold tenders are outside its scope.",
        ),
    ),
    _candidate(
        source_id="es-placsp",
        name="Plataforma de Contratación del Sector Público (open data)",
        owner="Ministerio de Hacienda, Spain",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("EU/ES"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("TO_VERIFY",),
        access_method=AccessMethod.FEED,
        authentication_required=False,
        expected_change_interval=timedelta(days=1),
        reference="https://contrataciondelestado.es (open data section)",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT", "COVERAGE_TO_VERIFY"),
        scope_limitations=("Expected to add below-EU-threshold Spanish tenders; unverified.",),
        alternatives=("ted-search-v3",),
    ),
    _candidate(
        source_id="fr-boamp",
        name="BOAMP open data",
        owner="Direction de l'information légale et administrative, France",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("EU/FR"),),
        classification_systems=frozenset({"CPV"}),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("TO_VERIFY",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=1),
        reference="https://www.boamp.fr (open data)",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        alternatives=("ted-search-v3",),
    ),
    _candidate(
        source_id="us-sam-opportunities",
        name="SAM.gov Get Opportunities Public API v2",
        owner="U.S. General Services Administration",
        capabilities=_PROCUREMENT,
        jurisdictions=(geo("US"),),
        classification_systems=frozenset({"NAICS", "PSC"}),
        buyer_levels=frozenset({BuyerLevel.NATIONAL_OR_FEDERAL}),
        record_types=(
            "o solicitation",
            "k combined synopsis",
            "p presolicitation",
            "a award notice",
        ),
        access_method=AccessMethod.API,
        authentication_required=True,
        expected_change_interval=timedelta(days=1),
        reference="https://open.gsa.gov/api/get-opportunities-public-api/",
        blockers=("API_KEY_NOT_PROVISIONED", "RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=(
            "Federal opportunities only; state and local procurement is outside its scope.",
        ),
        alternatives=("us-usaspending-awards",),
    ),
    _candidate(
        source_id="us-usaspending-awards",
        name="USAspending API v2 (award search)",
        owner="U.S. Department of the Treasury",
        capabilities=frozenset({SourceCapability.PUBLIC_PROCUREMENT_AWARDS}),
        jurisdictions=(geo("US"),),
        classification_systems=frozenset({"NAICS", "PSC"}),
        buyer_levels=frozenset({BuyerLevel.NATIONAL_OR_FEDERAL}),
        record_types=("contract awards",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="https://api.usaspending.gov/docs/endpoints",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("Federal spending; reveals buyers and history, not open calls.",),
        alternatives=("us-sam-opportunities",),
    ),
    _candidate(
        source_id="fr-installations-classees",
        name="Installations classées (ICPE) public register",
        owner="Ministère de la Transition écologique, France",
        capabilities=frozenset({SourceCapability.PLANNING_AND_PERMITS}),
        jurisdictions=(geo("EU/FR"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(),
        record_types=("regulated industrial installation",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="Géorisques ICPE data",
        blockers=("RIGHTS_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("Permits reveal regulated sites, not purchasing intent.",),
    ),
    _candidate(
        source_id="eu-funding-tenders-portal",
        name="EU Funding & Tenders Portal",
        owner="European Commission",
        capabilities=frozenset({SourceCapability.PUBLIC_FUNDING}),
        jurisdictions=(geo("EU"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset({BuyerLevel.SUPRANATIONAL}),
        record_types=("calls for proposals",),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=7),
        reference="https://ec.europa.eu/info/funding-tenders/opportunities/portal",
        blockers=("RIGHTS_TO_VERIFY", "ACCESS_METHOD_TO_VERIFY", "ADAPTER_NOT_BUILT"),
        scope_limitations=("EU-managed programmes; national and regional schemes are outside.",),
    ),
    _candidate(
        source_id="es-bdns",
        name="Base de Datos Nacional de Subvenciones",
        owner="Intervención General de la Administración del Estado, Spain",
        capabilities=frozenset({SourceCapability.PUBLIC_FUNDING}),
        jurisdictions=(geo("EU/ES"),),
        classification_systems=frozenset(),
        buyer_levels=frozenset(
            {BuyerLevel.NATIONAL_OR_FEDERAL, BuyerLevel.REGIONAL_OR_STATE, BuyerLevel.LOCAL}
        ),
        record_types=("calls", "concessions of grants"),
        access_method=AccessMethod.API,
        authentication_required=False,
        expected_change_interval=timedelta(days=1),
        reference="https://www.infosubvenciones.es (TO_VERIFY)",
        blockers=("RIGHTS_TO_VERIFY", "ACCESS_METHOD_TO_VERIFY", "ADAPTER_NOT_BUILT"),
    ),
)
