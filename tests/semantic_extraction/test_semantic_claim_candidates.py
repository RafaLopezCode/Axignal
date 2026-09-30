from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.semantic_extraction import (
    GroundingSurface,
    SemanticExtractionContract,
    SemanticTarget,
)
from application.source_representation import DocumentRepresentation
from cognition.jobs import (
    CognitiveJob,
    StructuredResult,
    build_semantic_extraction_job,
    normalize_semantic_extraction_result,
)
from cognition.router import ModelRouter

NOW = datetime(2026, 9, 30, 15, 20, tzinfo=UTC)


def _representation() -> DocumentRepresentation:
    return DocumentRepresentation(
        representation_id="document:source:acme:abc",
        observation_id="source:request:acme:web:abc",
        subject_id="org:acme",
        source_ref="https://example.test/company",
        source_type="OFFICIAL_WEB",
        observed_at=NOW,
        source_observation_fingerprint="sha256:observation",
        source_content_fingerprint="sha256:content",
        media_type="text/html",
        charset="utf-8",
        title="ACME Pumps",
        language="en",
        description="Industrial pumps",
        canonical_uri="https://example.test/company",
        visible_text="ACME manufactures industrial pumps for food processing plants in Spain.",
        visible_text_fingerprint="sha256:text",
        structured_data=('{"@type":"Organization","name":"ACME Pumps"}',),
        representation_version="html-document/0.1",
        normalization_version="visible-text/0.1",
        artifact_ref="cas:sha256:representation",
    )


def _contract(max_candidates: int = 24) -> SemanticExtractionContract:
    return SemanticExtractionContract(
        contract_id="economic-document-claims",
        version="1",
        targets=(
            SemanticTarget("capability", "declared products, services or operational capabilities"),
            SemanticTarget("market", "declared market or customer geography"),
        ),
        max_candidates=max_candidates,
    )


def _result(job: CognitiveJob) -> StructuredResult:
    return StructuredResult(
        job_id=job.id,
        provider="fixture-provider",
        payload={
            "provider_version": "fixture/1",
            "candidates": [
                {
                    "candidate_id": "provider-must-not-own-this",
                    "semantic_target": "capability",
                    "statement": "ACME manufactures industrial pumps.",
                    "excerpt": "manufactures industrial pumps",
                    "grounding_surface": "VISIBLE_TEXT",
                },
                {
                    "semantic_target": "market",
                    "statement": "ACME declares activity in Spain.",
                    "excerpt": "Spain",
                    "grounding_surface": "VISIBLE_TEXT",
                },
            ],
        },
    )


def test_job_is_bound_to_exact_representation_and_contract() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)

    assert job.kind.value == "DOCUMENT_SEMANTIC_EXTRACTION"
    assert job.context["representation_id"] == representation.representation_id
    assert job.context["representation_fingerprint"] == representation.fingerprint
    assert job.context["contract_fingerprint"] == contract.fingerprint
    assert job.context["visible_text"] == representation.visible_text
    assert "canonical truth" in job.instruction


def test_grounded_provider_result_becomes_noncanonical_candidates() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)

    candidate_set = normalize_semantic_extraction_result(
        job=job,
        result=_result(job),
        representation=representation,
        contract=contract,
    )

    assert len(candidate_set.candidates) == 2
    assert candidate_set.is_canonical_truth is False
    first = candidate_set.candidates[0]
    assert first.is_canonical_truth is False
    assert first.semantic_target == "capability"
    assert first.grounding_surface is GroundingSurface.VISIBLE_TEXT
    assert first.source_type == "OFFICIAL_WEB"
    assert first.candidate_id.startswith("claim:")
    assert first.candidate_id != "provider-must-not-own-this"


def test_structured_data_grounding_is_accepted() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    result = StructuredResult(
        job_id=job.id,
        provider="fixture-provider",
        payload={
            "provider_version": "fixture/1",
            "candidates": [
                {
                    "semantic_target": "capability",
                    "statement": "The source declares an Organization named ACME Pumps.",
                    "excerpt": '"name":"ACME Pumps"',
                    "grounding_surface": "STRUCTURED_DATA",
                }
            ],
        },
    )

    candidate_set = normalize_semantic_extraction_result(
        job=job, result=result, representation=representation, contract=contract
    )
    assert candidate_set.candidates[0].grounding_surface is GroundingSurface.STRUCTURED_DATA


def test_ungrounded_claim_fails_closed() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    result = StructuredResult(
        job_id=job.id,
        provider="fixture-provider",
        payload={
            "provider_version": "fixture/1",
            "candidates": [
                {
                    "semantic_target": "capability",
                    "statement": "ACME manufactures spacecraft.",
                    "excerpt": "spacecraft",
                    "grounding_surface": "VISIBLE_TEXT",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="not grounded"):
        normalize_semantic_extraction_result(
            job=job, result=result, representation=representation, contract=contract
        )


def test_out_of_contract_target_fails_closed() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    result = StructuredResult(
        job_id=job.id,
        provider="fixture-provider",
        payload={
            "provider_version": "fixture/1",
            "candidates": [
                {
                    "semantic_target": "sale_probability",
                    "statement": "Likely buyer.",
                    "excerpt": "food processing plants",
                    "grounding_surface": "VISIBLE_TEXT",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="outside contract"):
        normalize_semantic_extraction_result(
            job=job, result=result, representation=representation, contract=contract
        )


def test_result_from_another_job_fails_closed() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    result = _result(job)
    replayed = StructuredResult(
        job_id="semantic-extraction:another-job",
        provider=result.provider,
        payload=result.payload,
    )

    with pytest.raises(ValueError, match="job identity mismatch"):
        normalize_semantic_extraction_result(
            job=job,
            result=replayed,
            representation=representation,
            contract=contract,
        )


def test_mutated_job_context_fails_closed() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    mutated = CognitiveJob(
        id=job.id,
        kind=job.kind,
        instruction=job.instruction,
        context={**job.context, "subject_id": "org:other"},
    )

    with pytest.raises(ValueError, match="does not match representation and contract"):
        normalize_semantic_extraction_result(
            job=mutated,
            result=_result(mutated),
            representation=representation,
            contract=contract,
        )


def test_candidate_budget_fails_closed() -> None:
    representation = _representation()
    contract = _contract(max_candidates=1)
    job = build_semantic_extraction_job(representation, contract)
    with pytest.raises(ValueError, match="exceeds candidate budget"):
        normalize_semantic_extraction_result(
            job=job,
            result=_result(job),
            representation=representation,
            contract=contract,
        )


class _GroundedFixtureProvider:
    name = "fixture-provider"

    def complete(self, job: CognitiveJob) -> StructuredResult:
        return _result(job)


def test_model_router_can_execute_extraction_without_owning_truth() -> None:
    representation = _representation()
    contract = _contract()
    job = build_semantic_extraction_job(representation, contract)
    routed = ModelRouter([_GroundedFixtureProvider()]).route(job)
    candidate_set = normalize_semantic_extraction_result(
        job=job,
        result=routed,
        representation=representation,
        contract=contract,
    )

    assert candidate_set.provider == "fixture-provider"
    assert all(candidate.is_canonical_truth is False for candidate in candidate_set.candidates)
