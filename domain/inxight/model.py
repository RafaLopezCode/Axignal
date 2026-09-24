"""INXIGHT model.

Derived knowledge that must remain explainable down to the FAXTs, relationships
and PATHX that support it, and must degrade when its evidence goes stale.

Doctrine: MASTER §4.6, §18.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.evidence.epistemics import Currentness


class InxightError(Exception):
    """Raised for invalid INXIGHT state."""


@dataclass(frozen=True)
class INXIGHT:
    """A derived, explainable interpretation (MASTER §4.6).

    This is intentionally not a ``FAXT`` subclass and does not carry a
    predicate/object pair. It references the canonical units that support it.
    """

    id: str
    subject_scope: str
    statement: str
    supporting_faxt_refs: tuple[str, ...]
    derived_at: datetime
    relationship_refs: tuple[str, ...] = ()
    pathx_refs: tuple[str, ...] = ()
    currentness: Currentness = Currentness.UNKNOWN

    def __post_init__(self) -> None:
        if not self.supporting_faxt_refs:
            raise InxightError("an INXIGHT must reference supporting FAXTs")
        if not self.statement.strip():
            raise InxightError("an INXIGHT requires a statement")

    @property
    def is_explainable(self) -> bool:
        return bool(self.supporting_faxt_refs)
