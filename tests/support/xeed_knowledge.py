"""In-memory Xeed/FAXT authority for deterministic tests only."""

from __future__ import annotations

from application.xeed_knowledge.reader import (
    CanonicalFaxtReader,
    XeedFaxtReferenceCollectionReader,
    XeedFaxtReferenceReader,
)
from domain.faxt.model import FAXT
from domain.identity import FaxtId, XeedId
from domain.xeed.knowledge_reference import XeedFaxtReference


class InMemoryXeedKnowledgeAuthority(
    CanonicalFaxtReader,
    XeedFaxtReferenceCollectionReader,
    XeedFaxtReferenceReader,
):
    """Separate global FAXTs from explicit private Xeed references."""

    def __init__(self) -> None:
        self.faxts: dict[FaxtId, FAXT] = {}
        self.references: dict[tuple[XeedId, FaxtId], XeedFaxtReference] = {}
        self.calls: list[str] = []
        self.listed_xeeds: list[XeedId] = []

    def add_faxt(self, faxt: FAXT) -> None:
        if faxt.id in self.faxts:
            raise ValueError("duplicate canonical FAXT identity")
        self.faxts[faxt.id] = faxt

    def add_reference(self, reference: XeedFaxtReference) -> None:
        key = (reference.xeed_id, reference.faxt_id)
        if key in self.references:
            raise ValueError("duplicate Xeed FAXT reference")
        self.references[key] = reference

    def get_reference(self, xeed_id: XeedId, faxt_id: FaxtId) -> XeedFaxtReference | None:
        self.calls.append("reference")
        return self.references.get((xeed_id, faxt_id))

    def list_for_xeed(self, xeed_id: XeedId) -> tuple[XeedFaxtReference, ...]:
        self.calls.append("references")
        self.listed_xeeds.append(xeed_id)
        return tuple(
            reference
            for (reference_xeed_id, _), reference in self.references.items()
            if reference_xeed_id == xeed_id
        )

    def get_faxt(self, faxt_id: FaxtId) -> FAXT | None:
        self.calls.append("faxt")
        return self.faxts.get(faxt_id)
