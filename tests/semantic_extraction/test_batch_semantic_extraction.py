from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.semantic_extraction import SemanticExtractionContract, SemanticTarget
from application.source_representation import DocumentRepresentation
from cognition.batch import BatchSemanticExtractionAdapter, SemanticExtractionWork
from cognition.jobs.model import CognitiveJob, StructuredResult
from domain.representation import text_fingerprint

NOW = datetime(2026, 10, 6, 4, 30, tzinfo=UTC)


def _representation(subject: str) -> DocumentRepresentation:
    text = f"{subject} manufactures industrial pumps in Spain."
    return DocumentRepresentation(
        representation_id=f"document:{subject}",
        observation_id=f"observation:{subject}",
        subject_id=f"org:{subject}",
        source_ref=f"https://{subject}.example.test",
        source_type="OFFICIAL_WEB",
        observed_at=NOW,
        source_observation_fingerprint=f"observation-fp:{subject}",
        source_content_fingerprint=f"content-fp:{subject}",
        media_type="text/html",
        charset="utf-8",
        title=subject,
        language="en",
        description=None,
        canonical_uri=f"https://{subject}.example.test",
        visible_text=text,
        visible_text_fingerprint=text_fingerprint(text),
        structured_data=(),
        representation_version="html-document/0.1",
        normalization_version="visible-text/0.1",
        artifact_ref=f"cas:{subject}",
        source_artifact_ref=f"source:{subject}",
        source_observation_artifact_ref=f"source-observation:{subject}",
    )


def _contract() -> SemanticExtractionContract:
    return SemanticExtractionContract(
        contract_id="batch-claims",
        version="1",
        targets=(SemanticTarget("capability", "declared capability"),),
        max_candidates=4,
    )


def _result(job: CognitiveJob, *, excerpt: str = "industrial pumps") -> StructuredResult:
    return StructuredResult(
        job_id=job.id,
        provider="batch-fixture",
        payload={
            "provider_version": "fixture/1",
            "candidates": [
                {
                    "semantic_target": "capability",
                    "statement": "The source declares industrial pump manufacturing.",
                    "excerpt": excerpt,
                    "grounding_surface": "VISIBLE_TEXT",
                }
            ],
        },
    )


class _Provider:
    name = "batch-fixture"

    def __init__(self, behavior="normal") -> None:
        self.behavior = behavior
        self.calls: list[tuple[CognitiveJob, ...]] = []

    def complete_batch(self, jobs):
        jobs = tuple(jobs)
        self.calls.append(jobs)
        if self.behavior == "raise":
            raise RuntimeError("batch unavailable")
        results = [_result(job) for job in jobs]
        if self.behavior == "reverse":
            return tuple(reversed(results))
        if self.behavior == "duplicate":
            return (results[0], results[0])
        if self.behavior == "missing":
            return tuple(results[:-1])
        if self.behavior == "foreign":
            return (
                *results,
                StructuredResult(job_id="foreign", provider="batch-fixture", payload={}),
            )
        if self.behavior == "ungrounded":
            return tuple(_result(job, excerpt="spacecraft") for job in jobs)
        return tuple(results)


def _work(*subjects: str) -> tuple[SemanticExtractionWork, ...]:
    contract = _contract()
    return tuple(SemanticExtractionWork(_representation(subject), contract) for subject in subjects)


def test_batch_preserves_input_order_when_provider_reorders() -> None:
    provider = _Provider("reverse")
    result = BatchSemanticExtractionAdapter(provider).extract_batch(_work("a", "b"))
    assert tuple(item.subject_id for item in result) == ("org:a", "org:b")


def test_batch_size_is_bounded() -> None:
    provider = _Provider()
    result = BatchSemanticExtractionAdapter(provider, max_batch_size=2).extract_batch(
        _work("a", "b", "c")
    )
    assert len(result) == 3
    assert tuple(len(call) for call in provider.calls) == (2, 1)


@pytest.mark.parametrize("behavior", ["duplicate", "missing", "foreign"])
def test_invalid_result_population_fails_closed(behavior) -> None:
    with pytest.raises(ValueError):
        BatchSemanticExtractionAdapter(_Provider(behavior)).extract_batch(_work("a", "b"))


def test_ungrounded_batch_claim_fails_closed() -> None:
    with pytest.raises(ValueError, match="not grounded"):
        BatchSemanticExtractionAdapter(_Provider("ungrounded")).extract_batch(_work("a"))


def test_batch_failure_propagates_without_single_fallback() -> None:
    provider = _Provider("raise")
    with pytest.raises(RuntimeError, match="batch unavailable"):
        BatchSemanticExtractionAdapter(provider).extract_batch(_work("a", "b"))
    assert len(provider.calls) == 1


def test_duplicate_job_identity_fails_before_provider_call() -> None:
    provider = _Provider()
    same = _work("a")[0]
    with pytest.raises(ValueError, match="unique job identities"):
        BatchSemanticExtractionAdapter(provider).extract_batch((same, same))
    assert provider.calls == []
