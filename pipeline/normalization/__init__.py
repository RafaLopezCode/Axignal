"""Deterministic normalization.

Doctrine: MASTER §14 (Python owns normalization), §35 (deterministic candidate
generation).
"""

from __future__ import annotations

from pipeline.normalization.text import normalize_name, normalize_whitespace

__all__ = ["normalize_name", "normalize_whitespace"]
