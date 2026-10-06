"""Economic Observation Intelligence Layer: where to look, why, how much, when to stop.

A deterministic control plane between observed context and governed acquisition.
It plans and explains observation; it never admits evidence or writes AXIGLAND.
"""

from application.observation_intelligence.catalog import (
    CAPABILITY_LEXICON,
    CATALOG_VERSION,
    QUESTIONS,
    REGIONAL_DEPTH,
    ROOT_QUESTION,
    SOURCES,
    eu_nuts,
)
from application.observation_intelligence.contracts import (
    OPPORTUNITY_INTELLIGENCE,
    AdoptionStatus,
    Band,
    BusinessFamilyHypothesis,
    BuyerLevel,
    CapabilityHypothesis,
    EconomicQuestion,
    EvidenceRef,
    MarketRole,
    MarketScope,
    ObservationBudget,
    OpportunityFamily,
    QuerySpec,
    SourceCapability,
    SourceDescriptor,
    TaxonomyCode,
    XeedObservationContext,
    geo,
)
from application.observation_intelligence.coverage import CoverageState, EvidenceCoverageMap
from application.observation_intelligence.findings import ProcurementRecord, SourceFindings
from application.observation_intelligence.human import HumanObservationBrief, build_brief
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.loop import (
    LoopResult,
    OpportunityCandidate,
    SourceObservationPort,
    StopReason,
    code_within,
    region_of,
    run_observation_loop,
)
from application.observation_intelligence.registry import (
    AdoptionEvidence,
    AdoptionRejected,
    SourceDiscoveryRequest,
    SourceRegistry,
    SourceResolution,
)
from application.observation_intelligence.strategy import (
    ObservationAction,
    ObservationStrategy,
    RoutingDecision,
    StopPolicy,
    build_strategy,
)
from application.observation_intelligence.understanding import (
    derive_families,
    detect_capabilities,
)

__all__ = [
    "CAPABILITY_LEXICON",
    "CATALOG_VERSION",
    "OPPORTUNITY_INTELLIGENCE",
    "QUESTIONS",
    "REGIONAL_DEPTH",
    "ROOT_QUESTION",
    "SOURCES",
    "AdoptionEvidence",
    "AdoptionRejected",
    "AdoptionStatus",
    "Band",
    "BusinessFamilyHypothesis",
    "BuyerLevel",
    "CapabilityHypothesis",
    "CoverageState",
    "EconomicQuestion",
    "EvidenceCoverageMap",
    "EvidenceRef",
    "HumanObservationBrief",
    "LoopResult",
    "MarketRole",
    "MarketScope",
    "ObservationAction",
    "ObservationBudget",
    "ObservationStrategy",
    "OperationalLearning",
    "OpportunityCandidate",
    "OpportunityFamily",
    "ProcurementRecord",
    "QuerySpec",
    "RoutingDecision",
    "SourceCapability",
    "SourceDescriptor",
    "SourceDiscoveryRequest",
    "SourceFindings",
    "SourceObservationPort",
    "SourceRegistry",
    "SourceResolution",
    "StopPolicy",
    "StopReason",
    "TaxonomyCode",
    "XeedObservationContext",
    "build_brief",
    "build_strategy",
    "code_within",
    "derive_families",
    "detect_capabilities",
    "eu_nuts",
    "geo",
    "region_of",
    "run_observation_loop",
]
