from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.economic_discovery import (
    DimensionDisposition,
    ObservationIngress,
    ObservationMode,
    SemanticPrimitive,
    TypingDimensionContract,
    build_work_plan,
)
from application.source_acquisition import SourceObservation, SourceRequest
from application.source_representation import (
    compile_rich_subject_state,
    representation_state_data,
    rich_state_change,
)
from domain.representation import TextSurface
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_representation import (
    DocumentRepresentationError,
    represent_html_observation,
)

NOW = datetime(2026, 9, 30, 15, 0, tzinfo=UTC)


def _request() -> SourceRequest:
    return SourceRequest(
        request_id="request:acme:web:1",
        subject_id="org:acme",
        observation_slot="website",
        target_uri="https://example.test/company",
        source_type="OFFICIAL_WEB",
        policy_id="policy:web:v1",
        policy_fingerprint="policy-fingerprint",
    )


def _observation(
    store: ContentAddressedArtifactStore, body: bytes, content_type: str
) -> SourceObservation:
    body_ref = store.put_bytes(body)
    import hashlib

    body_fingerprint = f"sha256:{hashlib.sha256(body).hexdigest()}"
    return SourceObservation(
        request_id="request:acme:web:1",
        subject_id="org:acme",
        observation_slot="website",
        requested_uri="https://example.test/company",
        final_uri="https://example.test/company",
        retrieved_at=NOW,
        http_status=200,
        content_type=content_type,
        body_fingerprint=body_fingerprint,
        body_artifact_ref=body_ref,
        raw_observation_ref=store.put_json({"kind": "source-observation"}),
        observation_fingerprint="sha256:source-observation",
        instrument_ref="test-http/1",
        policy_id="policy:web:v1",
        policy_fingerprint="policy-fingerprint",
        redirect_chain=("https://example.test/company",),
        peer_ips=("8.8.8.8",),
        failure_state=None,
    )


def test_html_representation_extracts_only_deterministic_document_semantics(tmp_path: Path) -> None:
    html = b"""<!doctype html>
<html lang="EN">
<head>
<title> ACME   Industrial Pumps </title>
<meta name="description" content=" Pumps for food and chemical plants. ">
<link rel="canonical" href="/about">
<script>window.secret = "not visible";</script>
<script type="application/ld+json">
{"@type":"Organization","name":"ACME Pumps"}
</script>
<style>.hidden { display:none }</style>
</head>
<body><h1>Industrial pumps</h1><p>Serving Spain and France.</p></body>
</html>"""
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    representation = represent_html_observation(
        request=_request(),
        observation=_observation(store, html, "text/html; charset=utf-8"),
        artifacts=store,
    )

    assert representation.title == "ACME Industrial Pumps"
    assert representation.language == "en"
    assert representation.description == "Pumps for food and chemical plants."
    assert representation.canonical_uri == "https://example.test/about"
    assert representation.visible_text == "Industrial pumps Serving Spain and France."
    assert "window.secret" not in representation.visible_text
    assert ".hidden" not in representation.visible_text
    assert representation.structured_data == ('{"@type":"Organization","name":"ACME Pumps"}',)
    artifact = store.read(representation.artifact_ref)
    assert b'"visible_text":"Industrial pumps Serving Spain and France."' in artifact


def test_external_stylesheet_preserves_extracted_text_without_claiming_visibility(
    tmp_path: Path,
) -> None:
    html = b"""<!doctype html>
<html>
<head><link rel="stylesheet" href="/assets/site.css"></head>
<body><main><h1>Industrial pumps</h1><p>Serving Spain.</p></main></body>
</html>"""
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    representation = represent_html_observation(
        request=_request(),
        observation=_observation(store, html, "text/html; charset=utf-8"),
        artifacts=store,
    )

    assert representation.visibility_resolved is False
    assert representation.document_text == "Industrial pumps Serving Spain."
    assert representation.text_representation().surface is TextSurface.EXTRACTED_TEXT
    state = representation_state_data(representation, observation_slot="website")
    names = {item.name for item in state}
    assert "document.website.extracted_text" in names
    assert "document.website.visible_text" not in names


def test_representation_is_deterministic_for_same_source_bytes(tmp_path: Path) -> None:
    body = b"<html><body><p>Same document</p></body></html>"
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    observation = _observation(store, body, "text/html")

    first = represent_html_observation(request=_request(), observation=observation, artifacts=store)
    second = represent_html_observation(
        request=_request(), observation=observation, artifacts=store
    )

    assert first == second
    assert first.artifact_ref == second.artifact_ref
    assert first.fingerprint == second.fingerprint


def test_non_html_body_is_not_silently_represented(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    observation = _observation(store, b'{"name":"ACME"}', "application/json")

    with pytest.raises(DocumentRepresentationError, match="unsupported document media type"):
        represent_html_observation(request=_request(), observation=observation, artifacts=store)


def test_representation_change_drives_dependency_aware_answerability(tmp_path: Path) -> None:
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    representation = represent_html_observation(
        request=_request(),
        observation=_observation(
            store,
            b"<html><body><p>Industrial pumps for food plants</p></body></html>",
            "text/html; charset=utf-8",
        ),
        artifacts=store,
    )
    empty = compile_rich_subject_state(subject_id="org:acme", contributions=())
    data = representation_state_data(representation, observation_slot="website")
    current = compile_rich_subject_state(subject_id="org:acme", contributions=data)
    change = rich_state_change(empty, current)
    assert change is not None
    assert "document.website.visible_text" in change.changed_fields

    contract = TypingDimensionContract(
        dimension_id="capability-language",
        version="1",
        semantic_target="declared capability language",
        primitive=SemanticPrimitive.CHOICE,
        question="What capability language is present in the represented document?",
        state_requirements=("document.website.visible_text",),
        dependencies=("document.website.visible_text",),
        mutually_exclusive=True,
        abstention_policy="abstain when represented visible text is unavailable",
    )
    plan = build_work_plan(
        ingress=ObservationIngress(
            observation_id=representation.observation_id,
            mode=ObservationMode.DETERMINISTIC_SENSOR,
            bound_subject_id="org:acme",
            requires_universe_discovery=False,
        ),
        change=change,
        contracts=(contract,),
        available_state_fields=current.available_fields,
    )

    assert plan.retrieval_required is False
    assert plan.research_dimensions == ()
    assert len(plan.evaluation) == 1
    assert plan.evaluation[0].disposition is DimensionDisposition.ANSWERABLE


def test_missing_document_semantics_preserve_not_answerable() -> None:
    previous = compile_rich_subject_state(subject_id="org:acme", contributions=())
    assert previous.available_fields == frozenset()
