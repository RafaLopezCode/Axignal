"""Append-only evidence ledger.

Doctrine: MASTER §15, §20 (temporal), §46.9.
"""

from __future__ import annotations

from domain.evidence.admission import Evidence


class EvidenceLedger:
    """An append-only collection of raw evidence observations."""

    def __init__(self) -> None:
        self._entries: list[Evidence] = []

    def append(self, evidence: Evidence) -> None:
        if not isinstance(evidence, Evidence):
            raise TypeError("EvidenceLedger accepts Evidence instances only")
        self._entries.append(evidence)

    @property
    def entries(self) -> tuple[Evidence, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
