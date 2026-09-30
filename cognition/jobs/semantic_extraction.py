"""Cognition-layer bridge for grounded document semantic extraction."""

from __future__ import annotations

from application.semantic_extraction import (
    SemanticCandidateSet,
    SemanticExtractionContract,
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)
from application.source_representation import DocumentRepresentation
from cognition.jobs.model import CognitiveJob, JobKind, StructuredResult


def build_semantic_extraction_job(
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
) -> CognitiveJob:
    """Bind one cognitive job exactly to a governed representation and contract."""

    request = build_semantic_extraction_request(representation, contract)
    return CognitiveJob(
        id=request.request_id,
        kind=JobKind.DOCUMENT_SEMANTIC_EXTRACTION,
        instruction=request.instruction,
        context=request.context,
    )


def normalize_semantic_extraction_result(
    *,
    job: CognitiveJob,
    result: StructuredResult,
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
) -> SemanticCandidateSet:
    """Accept provider output only for the exact extraction job AXIGNAL issued."""

    expected_job = build_semantic_extraction_job(representation, contract)
    if job != expected_job:
        raise ValueError("semantic extraction job does not match representation and contract")
    if result.job_id != job.id:
        raise ValueError("semantic extraction result job identity mismatch")

    request = build_semantic_extraction_request(representation, contract)
    return normalize_semantic_extraction_payload(
        request=request,
        provider=result.provider,
        payload=result.payload,
        representation=representation,
        contract=contract,
    )
