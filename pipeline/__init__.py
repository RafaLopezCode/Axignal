"""Pipeline layer: deterministic discovery, normalization and feature work.

Python/deterministic code owns normalization, canonicalization, entity
resolution, temporal validity, hard filters, candidate generation and feature
engineering. The pipeline feeds evidence admission but never bypasses it.

Doctrine: MASTER §14 (AI/Python/JEV division), §35 (candidate generation), §37
(infrastructure/repository).
"""

from __future__ import annotations

__all__: list[str] = []
