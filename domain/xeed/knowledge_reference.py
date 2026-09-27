"""Private contextual references from a Xeed to global canonical FAXTs."""

from __future__ import annotations

from dataclasses import dataclass

from domain.identity import FaxtId, XeedId


@dataclass(frozen=True)
class XeedFaxtReference:
    """An explicit private-context reference, not ownership or world truth."""

    xeed_id: XeedId
    faxt_id: FaxtId

    def __post_init__(self) -> None:
        if not isinstance(self.xeed_id, str) or not self.xeed_id.strip():
            raise ValueError("a Xeed FAXT reference requires a Xeed id")
        if not isinstance(self.faxt_id, str) or not self.faxt_id.strip():
            raise ValueError("a Xeed FAXT reference requires a FAXT id")
