"""Deterministic feature engineering.

Features are separate signals (FIT, EVIDENCE, CONFIDENCE, MOMENTUM, NOVELTY,
CURRENTNESS), never one magic percentage.

Doctrine: MASTER §19 (no single magic percentage), §14.
"""

from __future__ import annotations

from pipeline.features.model import DerivedFeatures

__all__ = ["DerivedFeatures"]
