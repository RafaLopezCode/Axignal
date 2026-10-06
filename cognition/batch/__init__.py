"""Batch packaging for cognitive work.

Doctrine: MASTER §12 (batch packager), §29 (compute budget), §35 (never run
expensive cognition over the cartesian product).
"""

from __future__ import annotations

from cognition.batch.packager import Batch, BatchPackager
from cognition.batch.semantic_extraction import (
    BatchCognitiveProvider,
    BatchSemanticExtractionAdapter,
    SemanticExtractionWork,
)

__all__ = [
    "Batch",
    "BatchCognitiveProvider",
    "BatchPackager",
    "BatchSemanticExtractionAdapter",
    "SemanticExtractionWork",
]
