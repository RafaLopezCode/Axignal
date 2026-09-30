"""Deterministic source-representation adapters."""

from pipeline.source_representation.adapter import HtmlDocumentRepresentationAdapter
from pipeline.source_representation.html_document import (
    DocumentRepresentationError,
    represent_html_observation,
)

__all__ = [
    "DocumentRepresentationError",
    "HtmlDocumentRepresentationAdapter",
    "represent_html_observation",
]
