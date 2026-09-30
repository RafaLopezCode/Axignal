"""Cognitive jobs and structured results.

Doctrine: MASTER §12, §13.1 (CognitiveJob), §14.
"""

from __future__ import annotations

from cognition.jobs.model import CognitiveJob, JobKind, StructuredResult
from cognition.jobs.semantic_extraction import (
    build_semantic_extraction_job,
    normalize_semantic_extraction_result,
)

__all__ = [
    "CognitiveJob",
    "JobKind",
    "StructuredResult",
    "build_semantic_extraction_job",
    "normalize_semantic_extraction_result",
]
