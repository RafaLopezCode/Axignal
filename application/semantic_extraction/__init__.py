"""Grounded semantic extraction proposals; never canonical truth."""

from application.semantic_extraction.contracts import (
    EconomicClaimCandidate,
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticTarget,
)
from application.semantic_extraction.reuse import (
    ContentAddressedSemanticExtractor,
    InMemorySemanticExtractionRecordStore,
    ReusableCandidate,
    SemanticExtractionRecord,
    SemanticExtractionRecordStore,
    extraction_content_key,
)
from application.semantic_extraction.runtime import (
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)

__all__ = [
    "ContentAddressedSemanticExtractor",
    "EconomicClaimCandidate",
    "GroundingSurface",
    "InMemorySemanticExtractionRecordStore",
    "ReusableCandidate",
    "SemanticCandidateSet",
    "SemanticExtractionContract",
    "SemanticExtractionRecord",
    "SemanticExtractionRecordStore",
    "SemanticTarget",
    "build_semantic_extraction_request",
    "extraction_content_key",
    "normalize_semantic_extraction_payload",
]
