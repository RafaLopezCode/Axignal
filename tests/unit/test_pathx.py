"""PATHX must remain an explainable path, not a collapsed edge (MASTER §17)."""

from __future__ import annotations

from datetime import datetime

import pytest

from domain.pathx.model import PATHX, PathxEdge, PathxError, PathxType


def test_pathx_requires_contiguous_edges() -> None:
    with pytest.raises(PathxError):
        PATHX(
            id="path-1",
            origin="org-acme",
            destination="org-xiaomi",
            edges=(
                PathxEdge("org-acme", "SUPPLIES", "org-beta"),
                PathxEdge("org-gamma", "SUPPLIES", "org-xiaomi"),
            ),
            path_type=PathxType.INDIRECT,
            computed_at=datetime(2026, 1, 1),
        )


def test_pathx_preserves_multiple_hops() -> None:
    path = PATHX(
        id="path-2",
        origin="org-repsol",
        destination="org-xiaomi",
        edges=(
            PathxEdge("org-repsol", "PARENT_OF", "org-sub-a"),
            PathxEdge("org-sub-a", "SUPPLIES", "org-b"),
            PathxEdge("org-b", "SUPPLIES", "org-xiaomi"),
        ),
        path_type=PathxType.INDIRECT,
        computed_at=datetime(2026, 1, 1),
    )
    assert path.is_direct is False
    assert len(path.edges) == 3
