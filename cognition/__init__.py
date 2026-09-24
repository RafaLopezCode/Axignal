"""Cognition layer: AXENT's cognitive work orchestration.

Handles jobs, model routing, provider adapters and batching. The foundation
model is a replaceable component. Cognition MUST NOT be the canonical truth
authority and must not write canonical state.

Doctrine: MASTER §13 (AXENT and model abstraction), §14 (responsibilities),
§30 (moat), §46.28-§46.31.
"""

from __future__ import annotations

__all__: list[str] = []
