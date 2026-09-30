"""Port-compatible deterministic document representation adapter."""

from __future__ import annotations

from application.source_acquisition import SourceObservation, SourceRequest
from application.source_representation import DocumentRepresentation
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_representation.html_document import represent_html_observation


class HtmlDocumentRepresentationAdapter:
    def __init__(self, artifacts: ContentAddressedArtifactStore) -> None:
        self._artifacts = artifacts

    def represent(
        self,
        *,
        request: SourceRequest,
        observation: SourceObservation,
    ) -> DocumentRepresentation:
        return represent_html_observation(
            request=request,
            observation=observation,
            artifacts=self._artifacts,
        )
