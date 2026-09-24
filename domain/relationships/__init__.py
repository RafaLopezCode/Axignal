"""Economic relationships: observed, potential and historical.

Observed and Potential are distinct epistemic classes. A potential relationship
must never be presented or materialized as a real relationship.

Doctrine: MASTER §16 (Observed Graph / Potential Graph / Organisational /
Historical), §16.5 (Observed != Potential), §46.19.
"""

from __future__ import annotations

from domain.relationships.model import (
    ObservedRelationship,
    PotentialRelationship,
    RelationshipEpistemicClass,
    RelationshipError,
    deserialize_relationship,
)

__all__ = [
    "ObservedRelationship",
    "PotentialRelationship",
    "RelationshipEpistemicClass",
    "RelationshipError",
    "deserialize_relationship",
]
