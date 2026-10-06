"""Cognitive adapter from durable PB-07 research work to governed batch providers."""

from __future__ import annotations

import hashlib
import json
from typing import Protocol

from application.economic_discovery.batch_research import ClaimedResearchWork
from application.economic_discovery.batch_research_runtime import ResearchBatchItemResult
from cognition.batch.semantic_extraction import BatchCognitiveProvider
from cognition.jobs.model import CognitiveJob, JobKind, StructuredResult


class ResearchResultAdmissionPort(Protocol):
    """Decide whether provider output actually resolves the governed objective."""

    def admit(
        self,
        *,
        work: ClaimedResearchWork,
        result: StructuredResult,
    ) -> bool: ...


def build_research_job(work: ClaimedResearchWork) -> CognitiveJob:
    intent = work.work.intent
    return CognitiveJob(
        id=f"research:{work.lease.work_key}",
        kind=JobKind.GAP_ENRICHMENT,
        instruction=(
            "Investigate only the governed missing requirements. Return evidence candidates "
            "with source provenance; do not assert canonical truth."
        ),
        context={
            "subject_id": intent.subject_id,
            "state_fingerprint": intent.state_fingerprint,
            "dimension_id": intent.dimension_id,
            "missing_requirements": intent.missing_requirements,
            "research_policy_id": intent.research_policy_id,
            "research_policy_version": intent.research_policy_version,
            "research_context_fingerprint": intent.research_context_fingerprint,
        },
    )


def _fingerprint(result: StructuredResult) -> str:
    encoded = json.dumps(
        {
            "job_id": result.job_id,
            "provider": result.provider,
            "payload": result.payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class CognitiveResearchBatchExecutor:
    """Batch provider output remains unresolved until the admission port accepts it."""

    def __init__(
        self,
        provider: BatchCognitiveProvider,
        admission: ResearchResultAdmissionPort,
    ) -> None:
        self._provider = provider
        self._admission = admission

    def execute_batch(
        self,
        claimed: tuple[ClaimedResearchWork, ...],
    ) -> tuple[ResearchBatchItemResult, ...]:
        if not claimed:
            return ()
        jobs = tuple(build_research_job(item) for item in claimed)
        results = tuple(self._provider.complete_batch(jobs))
        result_ids = tuple(result.job_id for result in results)
        expected_ids = {job.id for job in jobs}
        if len(set(result_ids)) != len(result_ids) or set(result_ids) != expected_ids:
            raise ValueError("cognitive research result population does not match claimed work")

        work_by_job = {
            job.id: item for job, item in zip(jobs, claimed, strict=True)
        }
        result_by_job = {result.job_id: result for result in results}
        settled: list[ResearchBatchItemResult] = []
        for job in jobs:
            work = work_by_job[job.id]
            result = result_by_job[job.id]
            provider_version = result.payload.get("provider_version")
            if not isinstance(provider_version, str) or not provider_version.strip():
                raise ValueError("cognitive research result requires provider version")
            settled.append(
                ResearchBatchItemResult(
                    work_key=work.lease.work_key,
                    output_fingerprint=_fingerprint(result),
                    objective_resolved=self._admission.admit(work=work, result=result),
                    provider=result.provider,
                    provider_version=provider_version,
                )
            )
        return tuple(settled)
