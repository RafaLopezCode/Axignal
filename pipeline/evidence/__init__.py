"""Evidence ledger ingestion.

The ledger stores raw observations in append order. It does NOT admit evidence;
admission is the domain layer's deterministic responsibility.

Doctrine: MASTER §15 (evidence), §46.9 (CLAIM != WRITE).
"""

from __future__ import annotations

from pipeline.evidence.ledger import EvidenceLedger

__all__ = ["EvidenceLedger"]
