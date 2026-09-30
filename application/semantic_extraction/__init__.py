"""Grounded semantic extraction proposals; never canonical truth."""

from application.semantic_extraction.contracts import (
    EconomicClaimCandidate,
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticTarget,
)
from application.semantic_extraction.runtime import (
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)

__all__ = [
    "EconomicClaimCandidate",
    "GroundingSurface",
    "SemanticCandidateSet",
    "SemanticExtractionContract",
    "SemanticTarget",
    "build_semantic_extraction_request",
    "normalize_semantic_extraction_payload",
]
