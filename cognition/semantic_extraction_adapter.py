"""Cognition adapter implementing the application semantic-extraction port."""

from __future__ import annotations

from application.semantic_extraction import (
    SemanticCandidateSet,
    SemanticExtractionContract,
)
from application.source_representation import DocumentRepresentation
from cognition.jobs.semantic_extraction import (
    build_semantic_extraction_job,
    normalize_semantic_extraction_result,
)
from cognition.router.router import ModelRouter


class CognitiveSemanticExtractionAdapter:
    def __init__(
        self,
        router: ModelRouter,
        *,
        provider_name: str | None = None,
    ) -> None:
        self._router = router
        self._provider_name = provider_name

    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet:
        job = build_semantic_extraction_job(representation, contract)
        result = self._router.route(job, provider_name=self._provider_name)
        return normalize_semantic_extraction_result(
            job=job,
            result=result,
            representation=representation,
            contract=contract,
        )
