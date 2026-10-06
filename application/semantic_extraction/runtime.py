"""Build grounded extraction requests and validate provider-neutral proposal payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict

from application.semantic_extraction.contracts import (
    EconomicClaimCandidate,
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticExtractionRequest,
    fingerprint,
)
from application.source_representation import DocumentRepresentation
from domain.representation import RepresentationSpan, TextRepresentation

_JOB_INSTRUCTION = (
    "Extract only candidate economic statements grounded in the supplied document. "
    "Return provider_version and candidates. Each candidate must contain semantic_target, "
    "statement, excerpt and grounding_surface. Prefer an exact span with representation_id, "
    "representation_fingerprint, start and end (half-open Unicode code-point offsets). "
    "Structured spans also require structured_index. Do not assert canonical truth."
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
        "visible_text": representation.visible_text if representation.visibility_resolved else None,
        "extracted_text": representation.document_text,
        "structured_data": representation.structured_data,
        "grounding_surfaces": tuple(
            {
                "representation_id": item.representation_id,
                "representation_fingerprint": item.fingerprint,
                "text": item.text,
                "surface": item.surface.value,
            }
            for item in (
                representation.text_representation(),
                *(
                    representation.text_representation(index)
                    for index in range(len(representation.structured_data))
                ),
            )
        ),
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


def _required_string(value: object, name: str, *, strip: bool = True) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"semantic extraction result requires non-empty {name}")
    return value.strip() if strip else value


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
    raw_span: object,
) -> tuple[TextRepresentation, RepresentationSpan]:
    surfaces = (
        tuple(
            representation.text_representation(index)
            for index in range(len(representation.structured_data))
        )
        if surface is GroundingSurface.STRUCTURED_DATA
        else (representation.text_representation(),)
    )
    if raw_span is not None:
        if not isinstance(raw_span, Mapping):
            raise ValueError("candidate span must be an object")
        start, end = raw_span.get("start"), raw_span.get("end")
        if type(start) is not int or type(end) is not int:
            raise ValueError("candidate span offsets must be integers")
        span = RepresentationSpan(
            _required_string(raw_span.get("representation_id"), "span representation_id"),
            _required_string(
                raw_span.get("representation_fingerprint"), "span representation_fingerprint"
            ),
            start,
            end,
        )
        if surface is GroundingSurface.STRUCTURED_DATA:
            index = raw_span.get("structured_index")
            if type(index) is not int:
                raise ValueError("structured span requires integer structured_index")
            selected = representation.text_representation(index)
        else:
            if "structured_index" in raw_span:
                raise ValueError("document-text span cannot select structured data")
            selected = surfaces[0]
            if selected.surface.value != surface.value:
                raise ValueError("candidate grounding surface does not match representation")
        if span.extract(selected) != excerpt:
            raise ValueError("candidate excerpt does not match exact span")
        return selected, span
    matches = tuple(item for item in surfaces if excerpt in item.text)
    if not matches:
        raise ValueError("candidate excerpt is not grounded in represented surface")
    if len(matches) != 1:
        raise ValueError("ambiguous excerpt requires explicit offsets")
    selected = matches[0]
    if selected.surface.value != surface.value:
        raise ValueError("candidate grounding surface does not match representation")
    return selected, selected.unique_span(excerpt)


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
        excerpt = _required_string(row.get("excerpt"), "excerpt", strip=False)
        raw_surface = _required_string(row.get("grounding_surface"), "grounding_surface")
        try:
            surface = GroundingSurface(raw_surface)
        except ValueError as exc:
            raise ValueError("semantic extraction grounding surface is invalid") from exc
        if "span" in row and row["span"] is None:
            raise ValueError("candidate span cannot be null")
        supporting_representation, supporting_span = _grounded_excerpt(
            excerpt=excerpt,
            surface=surface,
            representation=representation,
            raw_span=row.get("span"),
        )

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
                "supporting_span": asdict(supporting_span),
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
                supporting_span=supporting_span,
                supporting_representation=supporting_representation,
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
