"""Fail-closed FAXT lookup through an authorized Xeed reference."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.xeed_access.reader import AuthorizedXeed
from domain.faxt.model import FAXT
from domain.identity import FaxtId, XeedId
from domain.xeed.knowledge_reference import XeedFaxtReference


class KnowledgeReadFailure(StrEnum):
    """Internal outcomes for authorized contextual FAXT reads."""

    MISSING_AUTHORIZED_XEED = "MISSING_AUTHORIZED_XEED"
    INVALID_FAXT_ID = "INVALID_FAXT_ID"
    REFERENCE_NOT_FOUND = "REFERENCE_NOT_FOUND"
    FAXT_NOT_FOUND = "FAXT_NOT_FOUND"
    INVALID_REFERENCE_COLLECTION = "INVALID_REFERENCE_COLLECTION"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    DUPLICATE_REFERENCE = "DUPLICATE_REFERENCE"


class KnowledgeReadError(Exception):
    """A contextual FAXT could not be released."""

    def __init__(self, failure: KnowledgeReadFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


class XeedFaxtReferenceReader(Protocol):
    """Reads explicit private references for one Xeed identity."""

    def get_reference(self, xeed_id: XeedId, faxt_id: FaxtId) -> XeedFaxtReference | None: ...


class XeedFaxtReferenceCollectionReader(Protocol):
    """Lists references scoped to exactly one already-authorized Xeed."""

    def list_for_xeed(self, xeed_id: XeedId) -> tuple[XeedFaxtReference, ...]: ...


class CanonicalFaxtReader(Protocol):
    """Resolves the shared canonical FAXT object by its global identity."""

    def get_faxt(self, faxt_id: FaxtId) -> FAXT | None: ...


_AUTHORIZED_XEED_FAXT_TOKEN = object()


@dataclass(frozen=True, init=False)
class AuthorizedXeedFaxt:
    """A global FAXT released through an explicit authorized Xeed reference."""

    _authorized_xeed: AuthorizedXeed
    _reference: XeedFaxtReference
    _faxt: FAXT

    def __init__(
        self,
        authorized_xeed: AuthorizedXeed,
        reference: XeedFaxtReference,
        faxt: FAXT,
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _AUTHORIZED_XEED_FAXT_TOKEN:
            raise TypeError("AuthorizedXeedFaxt can only be created by its reader")
        object.__setattr__(self, "_authorized_xeed", authorized_xeed)
        object.__setattr__(self, "_reference", reference)
        object.__setattr__(self, "_faxt", faxt)

    @property
    def authorized_xeed(self) -> AuthorizedXeed:
        return self._authorized_xeed

    @property
    def reference(self) -> XeedFaxtReference:
        return self._reference

    @property
    def faxt(self) -> FAXT:
        """The original global object; its canonical state is not copied."""

        return self._faxt


class AuthorizedXeedKnowledgeReader:
    """Checks private contextual reference before resolving global FAXT."""

    def __init__(
        self,
        references: XeedFaxtReferenceReader,
        faxts: CanonicalFaxtReader,
    ) -> None:
        self._references = references
        self._faxts = faxts

    def read(self, authorized_xeed: AuthorizedXeed, faxt_id: FaxtId) -> AuthorizedXeedFaxt:
        """Release a FAXT only after an authorized context and explicit reference."""

        if not isinstance(authorized_xeed, AuthorizedXeed):
            raise KnowledgeReadError(KnowledgeReadFailure.MISSING_AUTHORIZED_XEED)
        if not isinstance(faxt_id, str) or not faxt_id.strip():
            raise KnowledgeReadError(KnowledgeReadFailure.INVALID_FAXT_ID)

        xeed_id = authorized_xeed.xeed.id
        reference = self._references.get_reference(xeed_id, faxt_id)
        if (
            not isinstance(reference, XeedFaxtReference)
            or reference.xeed_id != xeed_id
            or reference.faxt_id != faxt_id
        ):
            raise KnowledgeReadError(KnowledgeReadFailure.REFERENCE_NOT_FOUND)

        faxt = self._faxts.get_faxt(faxt_id)
        if not isinstance(faxt, FAXT) or faxt.id != faxt_id:
            raise KnowledgeReadError(KnowledgeReadFailure.FAXT_NOT_FOUND)

        return AuthorizedXeedFaxt(
            authorized_xeed,
            reference,
            faxt,
            _token=_AUTHORIZED_XEED_FAXT_TOKEN,
        )


class AuthorizedXeedFaxtCollectionReader:
    """Reads only explicitly referenced global FAXTs for one AuthorizedXeed."""

    def __init__(
        self,
        references: XeedFaxtReferenceCollectionReader,
        faxts: CanonicalFaxtReader,
    ) -> None:
        self._references = references
        self._faxts = faxts

    def read(self, authorized_xeed: AuthorizedXeed) -> tuple[AuthorizedXeedFaxt, ...]:
        """Return an immutable collection after private selection and validation."""

        if not isinstance(authorized_xeed, AuthorizedXeed):
            raise KnowledgeReadError(KnowledgeReadFailure.MISSING_AUTHORIZED_XEED)

        xeed_id = authorized_xeed.xeed.id
        references = self._references.list_for_xeed(xeed_id)
        if not isinstance(references, tuple):
            raise KnowledgeReadError(KnowledgeReadFailure.INVALID_REFERENCE_COLLECTION)

        references_by_id: dict[FaxtId, XeedFaxtReference] = {}
        for reference in references:
            if (
                not isinstance(reference, XeedFaxtReference)
                or reference.xeed_id != xeed_id
                or not isinstance(reference.faxt_id, str)
                or not reference.faxt_id.strip()
            ):
                raise KnowledgeReadError(KnowledgeReadFailure.INVALID_REFERENCE)
            if reference.faxt_id in references_by_id:
                raise KnowledgeReadError(KnowledgeReadFailure.DUPLICATE_REFERENCE)
            references_by_id[reference.faxt_id] = reference

        # Stable identity order is for deterministic output only, never ranking.
        result: list[AuthorizedXeedFaxt] = []
        for faxt_id in sorted(references_by_id):
            reference = references_by_id[faxt_id]
            faxt = self._faxts.get_faxt(faxt_id)
            if not isinstance(faxt, FAXT) or faxt.id != faxt_id:
                raise KnowledgeReadError(KnowledgeReadFailure.FAXT_NOT_FOUND)
            result.append(
                AuthorizedXeedFaxt(
                    authorized_xeed,
                    reference,
                    faxt,
                    _token=_AUTHORIZED_XEED_FAXT_TOKEN,
                )
            )

        return tuple(result)
