"""PATHX: explainable economic paths.

A relationship and an economic path are different objects. A PATHX must not be
collapsed into a single direct relationship.

Doctrine: MASTER §4.7, §17, §46.20.
"""

from __future__ import annotations

from domain.pathx.model import PATHX, PathxEdge, PathxError, PathxType

__all__ = ["PATHX", "PathxEdge", "PathxError", "PathxType"]
