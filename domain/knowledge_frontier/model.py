"""KnowledgeFrontier model.

A projection describing what remains unknown or stale. It must not write
canonical truth.

Doctrine: MASTER §11, §36.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeFrontier:
    """Explicit boundary of knowledge for one organization (MASTER §11)."""

    id: str
    organization_id: str
    unresolved_questions: tuple[str, ...] = ()
    stale_claims: tuple[str, ...] = ()
    candidate_expansions: tuple[str, ...] = ()
    priority_state: str = "UNRANKED"
