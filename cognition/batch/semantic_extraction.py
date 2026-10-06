"""Governed semantic extraction batch boundary for BE-06."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from application.semantic_extraction import SemanticCandidateSet, SemanticExtractionContract
from application.source_representation import DocumentRepresentation
from cognition.batch.packager import BatchPackager
from cognition.jobs.model import CognitiveJob, StructuredResult
from cognition.jobs.semantic_extraction import (
    build_semantic_extraction_job,
    normalize_semantic_extraction_result,
)


class BatchCognitiveProvider(Protocol):
    @property
    def name(self) -> str: ...

    def complete_batch(self, jobs: Sequence[CognitiveJob]) -> Sequence[StructuredResult]: ...


@dataclass(frozen=True, slots=True)
class SemanticExtractionWork:
    representation: DocumentRepresentation
    contract: SemanticExtractionContract


class BatchSemanticExtractionAdapter:
    """Batch transport with strict per-job identity and grounding reconciliation."""

    def __init__(self, provider: BatchCognitiveProvider, *, max_batch_size: int = 50) -> None:
        self._provider = provider
        self._packager = BatchPackager(max_batch_size=max_batch_size)

    def extract_batch(
        self, work: Sequence[SemanticExtractionWork]
    ) -> tuple[SemanticCandidateSet, ...]:
        if not work:
            return ()
        jobs = tuple(
            build_semantic_extraction_job(item.representation, item.contract) for item in work
        )
        if len({job.id for job in jobs}) != len(jobs):
            raise ValueError("batch semantic extraction requires unique job identities")
        work_by_id = {job.id: item for job, item in zip(jobs, work, strict=True)}
        normalized: dict[str, SemanticCandidateSet] = {}
        for batch in self._packager.pack(jobs):
            results = tuple(self._provider.complete_batch(batch.jobs))
            result_ids = tuple(result.job_id for result in results)
            expected_ids = {job.id for job in batch.jobs}
            if len(set(result_ids)) != len(result_ids):
                raise ValueError("batch provider returned duplicate job results")
            if set(result_ids) != expected_ids:
                raise ValueError("batch provider result population does not match submitted jobs")
            job_by_id = {job.id: job for job in batch.jobs}
            for result in results:
                item = work_by_id[result.job_id]
                normalized[result.job_id] = normalize_semantic_extraction_result(
                    job=job_by_id[result.job_id],
                    result=result,
                    representation=item.representation,
                    contract=item.contract,
                )
        return tuple(normalized[job.id] for job in jobs)
