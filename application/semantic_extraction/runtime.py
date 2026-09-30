"""Build grounded extraction requests and validate provider-neutral proposal payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from application.semantic_extraction.contracts import (
    EconomicClaimCandidate,
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticExtractionRequest,
    fingerprint,
)
from application.source_representation import DocumentRepresentation

_JOB_INSTRUCTION = (
    "Extract only candidate economic statements grounded in the supplied document. "
    "Return provider_version and candidates. Each candidate must contain semantic_target, "
    "statement, excerpt and grounding_surface. Do not assert canonical truth."
)


def build_semantic_extraction_request(
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
) -> SemanticExtractionRequest:
    """Create a provider-neutral extraction request from governed representation."""

    context: dict[str, object] = {
        "subject_id": representation.subject_id,
        "observation_id": representation.observation_id,
        "representation_id": representation.representation_id,
        "representation_fingerprint": representation.fingerprint,
        "source_ref": representation.source_ref,
        "source_type": representation.source_type,
        "observed_at": representation.observed_at.isoformat(),
        "title": representation.title,
        "language": representation.language,
        "description": representation.description,
        "visible_text": representation.visible_text,
        "structured_data": representation.structured_data,
        "semantic_targets": tuple(
            {"target_id": target.target_id, "meaning": target.meaning}
            for target in contract.targets
        ),
        "contract_id": contract.contract_id,
        "contract_version": contract.version,
        "contract_fingerprint": contract.fingerprint,
        "max_candidates": contract.max_candidates,
    }
    request_fingerprint = fingerprint(
        {
            "representation_fingerprint": representation.fingerprint,
            "contract_fingerprint": contract.fingerprint,
            "instruction": _JOB_INSTRUCTION,
        }
    )
    return SemanticExtractionRequest(
        request_id=f"semantic-extraction:{request_fingerprint[:32]}",
        representation_id=representation.representation_id,
        contract_fingerprint=contract.fingerprint,
        instruction=_JOB_INSTRUCTION,
        context=context,
    )


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"semantic extraction result requires non-empty {name}")
    return value.strip()


def _candidate_rows(payload: Mapping[str, object]) -> Sequence[object]:
    rows = payload.get("candidates")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("semantic extraction result candidates must be a sequence")
    return rows


def _grounded_excerpt(
    *,
    excerpt: str,
    surface: GroundingSurface,
    representation: DocumentRepresentation,
) -> None:
    if surface is GroundingSurface.VISIBLE_TEXT:
        if excerpt not in representation.visible_text:
            raise ValueError("candidate excerpt is not grounded in represented visible text")
        return
    if not any(excerpt in item for item in representation.structured_data):
        raise ValueError("candidate excerpt is not grounded in represented structured data")


def normalize_semantic_extraction_payload(
    *,
    request: SemanticExtractionRequest,
    provider: str,
    payload: Mapping[str, object],
    representation: DocumentRepresentation,
    contract: SemanticExtractionContract,
) -> SemanticCandidateSet:
    """Fail closed on ungrounded or out-of-contract provider proposals."""

    expected = build_semantic_extraction_request(representation, contract)
    if request != expected:
        raise ValueError("semantic extraction request does not match representation and contract")
    provider = _required_string(provider, "provider")
    provider_version = _required_string(payload.get("provider_version"), "provider_version")
    rows = _candidate_rows(payload)
    if len(rows) > contract.max_candidates:
        raise ValueError("semantic extraction result exceeds candidate budget")

    result_fingerprint = fingerprint(
        {
            "request_id": request.request_id,
            "provider": provider,
            "payload": payload,
        }
    )
    candidates: list[EconomicClaimCandidate] = []
    semantic_keys: set[tuple[str, str, str, GroundingSurface]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("semantic extraction candidate must be an object")
        semantic_target = _required_string(row.get("semantic_target"), "semantic_target")
        if semantic_target not in contract.target_ids:
            raise ValueError("semantic extraction candidate target is outside contract")
        statement = _required_string(row.get("statement"), "statement")
        excerpt = _required_string(row.get("excerpt"), "excerpt")
        raw_surface = _required_string(row.get("grounding_surface"), "grounding_surface")
        try:
            surface = GroundingSurface(raw_surface)
        except ValueError as exc:
            raise ValueError("semantic extraction grounding surface is invalid") from exc
        _grounded_excerpt(excerpt=excerpt, surface=surface, representation=representation)

        key = (semantic_target, statement, excerpt, surface)
        if key in semantic_keys:
            raise ValueError("semantic extraction result contains duplicate candidates")
        semantic_keys.add(key)
        candidate_digest = fingerprint(
            {
                "representation_id": representation.representation_id,
                "semantic_target": semantic_target,
                "statement": statement,
                "excerpt": excerpt,
                "grounding_surface": surface.value,
                "contract_fingerprint": contract.fingerprint,
            }
        )
        candidates.append(
            EconomicClaimCandidate(
                candidate_id=f"claim:{candidate_digest[:32]}",
                subject_id=representation.subject_id,
                observation_id=representation.observation_id,
                representation_id=representation.representation_id,
                semantic_target=semantic_target,
                statement=statement,
                excerpt=excerpt,
                grounding_surface=surface,
                source_ref=representation.source_ref,
                source_type=representation.source_type,
                observed_at=representation.observed_at,
                extractor=provider,
                extractor_version=provider_version,
                contract_fingerprint=contract.fingerprint,
                result_fingerprint=result_fingerprint,
            )
        )

    extraction_digest = fingerprint(
        {
            "representation_id": representation.representation_id,
            "contract_fingerprint": contract.fingerprint,
            "result_fingerprint": result_fingerprint,
            "candidate_ids": [candidate.candidate_id for candidate in candidates],
        }
    )
    return SemanticCandidateSet(
        extraction_id=f"extraction:{extraction_digest[:32]}",
        subject_id=representation.subject_id,
        representation_id=representation.representation_id,
        contract_fingerprint=contract.fingerprint,
        provider=provider,
        provider_version=provider_version,
        result_fingerprint=result_fingerprint,
        candidates=tuple(candidates),
    )
