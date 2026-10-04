"""Append-only evidence ledger.

Doctrine: MASTER §15, §20 (temporal), §46.9.
"""

from __future__ import annotations

from domain.evidence.admission import Evidence, evidence_fingerprint


class EvidenceLedgerConflict(ValueError):
    """An existing evidence identity was reused for different immutable content."""


class EvidenceLedger:
    """Append-only evidence identity ledger with exact-replay idempotency."""

    def __init__(self) -> None:
        self._entries: list[Evidence] = []
        self._by_id: dict[str, tuple[str, Evidence]] = {}

    def append(self, evidence: Evidence) -> bool:
        if not isinstance(evidence, Evidence):
            raise TypeError("EvidenceLedger accepts Evidence instances only")

        fingerprint = evidence_fingerprint(evidence)
        existing = self._by_id.get(evidence.id)
        if existing is not None:
            existing_fingerprint, _ = existing
            if existing_fingerprint == fingerprint:
                return False
            raise EvidenceLedgerConflict("evidence id reused with different immutable content")

        self._entries.append(evidence)
        self._by_id[evidence.id] = (fingerprint, evidence)
        return True

    def get(self, evidence_id: str) -> Evidence | None:
        existing = self._by_id.get(evidence_id)
        return None if existing is None else existing[1]

    @property
    def entries(self) -> tuple[Evidence, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
